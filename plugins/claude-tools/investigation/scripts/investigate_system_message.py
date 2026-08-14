#!/usr/bin/env python3
# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run deterministic Claude Code investigations for system-message construction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from normalize_proxy_log import normalize_value, parse_proxy_log


REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
PROXY_JS = REPO_ROOT.parent / "openai-proxy" / "proxy.js"
RAW_ROOT = PLUGIN_ROOT / "investigation" / "raw" / "system-message"
FIXTURE_ROOT = PLUGIN_ROOT / "investigation" / "fixtures" / "system-message"
DEFAULT_MODEL = "qwen3-coder-next:cloud"
STANDARD_TOOLS = "Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch"


@dataclass(frozen=True)
class CaseSpec:
    name: str
    prompt: str
    tools: str
    expect_tool_use: bool = False


CASES = {
    "no-tools": CaseSpec(
        name="no-tools",
        tools="",
        prompt="Answer exactly: CLAUDE_SYSTEM_NO_TOOLS",
    ),
    "read-tool": CaseSpec(
        name="read-tool",
        tools="Read",
        prompt="Answer exactly: CLAUDE_SYSTEM_READ_TOOL",
    ),
    "read-relative-path": CaseSpec(
        name="read-relative-path",
        tools="Read",
        prompt=(
            "Use the Read tool to read README.md. "
            "Then answer with exactly the sentinel line from that file and nothing else."
        ),
        expect_tool_use=True,
    ),
    "standard-tools": CaseSpec(
        name="standard-tools",
        tools=STANDARD_TOOLS,
        prompt="Answer exactly: CLAUDE_SYSTEM_STANDARD_TOOLS",
    ),
}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required executable not found: {name}")


def _run(command: list[str], *, cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def _wait_for_proxy(port: int, timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        proc = _run(["curl", "-sS", f"http://localhost:{port}/health"], cwd=REPO_ROOT, timeout=5)
        if proc.returncode == 0:
            return
        time.sleep(0.2)
    raise RuntimeError(f"proxy did not become ready on port {port}")


def _prepare_workspace(root: Path) -> dict[str, Path]:
    workspace = root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "README.md").write_text(
        "# Claude System Message Probe\n\nCLAUDE_SYSTEM_READ_SENTINEL\n",
        encoding="utf-8",
    )
    (workspace / "notes.txt").write_text(
        "CLAUDE_SYSTEM_NOTES_SENTINEL\n",
        encoding="utf-8",
    )
    return {"workspace": workspace, "readme": workspace / "README.md"}


def _system_texts(body: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for block in body.get("system") or []:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            texts.append(block["text"])
    return texts


def _user_texts(body: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for message in body.get("messages") or []:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    texts.append(block["text"])
    return texts


def _assistant_tool_uses(body: dict[str, Any]) -> list[dict[str, Any]]:
    uses: list[dict[str, Any]] = []
    for message in body.get("messages") or []:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                uses.append(block)
    return uses


def _primary_request(requests: list[dict[str, Any]]) -> dict[str, Any] | None:
    for request in requests:
        body = request.get("body") or {}
        if any(len(text) > 1000 for text in _system_texts(body)):
            return request
    return requests[-1] if requests else None


def _extract_headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if re.match(r"^#{1,4}\s+\S", line)]


def _extract_environment_section(text: str) -> str | None:
    match = re.search(r"(?ms)^# Environment\n.*?(?=^# |\Z)", text)
    return match.group(0).rstrip() if match else None


def _path_related_lines(text: str) -> list[str]:
    needles = ("absolute path", "relative path", "working directory", "primary working directory", "file_path")
    lines: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if any(needle in lower for needle in needles):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
    return lines


def _tool_path_guidance(tools: list[dict[str, Any]]) -> dict[str, list[str]]:
    guidance: dict[str, list[str]] = {}
    for tool in tools:
        name = tool.get("name")
        if not isinstance(name, str):
            continue
        lines: list[str] = []
        description = tool.get("description")
        if isinstance(description, str):
            lines.extend(_path_related_lines(description))
        schema = tool.get("input_schema")
        if isinstance(schema, dict):
            for prop_name, prop in (schema.get("properties") or {}).items():
                if isinstance(prop, dict) and isinstance(prop.get("description"), str):
                    description_line = f"{prop_name}: {prop['description']}"
                    if _path_related_lines(description_line):
                        lines.append(description_line)
        if lines:
            guidance[name] = lines
    return guidance


def _read_stdout_events(stdout_jsonl: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not stdout_jsonl.exists():
        return events
    for line in stdout_jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def build_system_fixture(
    *,
    case_name: str,
    proxy_log: Path,
    stdout_jsonl: Path,
    replacements: dict[str, str],
) -> dict[str, Any]:
    requests = normalize_value(parse_proxy_log(proxy_log), replacements)
    primary = _primary_request(requests)
    primary_body = primary.get("body") if primary else {}
    system_texts = _system_texts(primary_body)
    stdout_events = normalize_value(_read_stdout_events(stdout_jsonl), replacements)
    assistant_tool_uses = []
    for request in requests:
        assistant_tool_uses.extend(_assistant_tool_uses(request.get("body") or {}))

    final_result = None
    init_event = None
    for event in stdout_events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            init_event = event
        if event.get("type") == "result":
            final_result = event.get("result")

    return {
        "case": case_name,
        "request_count": len(requests),
        "request_urls": [request.get("url") for request in requests],
        "primary_request_index": requests.index(primary) if primary in requests else None,
        "model": primary_body.get("model"),
        "system_block_count": len(system_texts),
        "system_block_summaries": [
            {
                "index": index,
                "length": len(text),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "first_line": next((line for line in text.splitlines() if line.strip()), ""),
                "headings": _extract_headings(text),
                "environment_section": _extract_environment_section(text),
                "path_related_lines": _path_related_lines(text),
            }
            for index, text in enumerate(system_texts)
        ],
        "first_user_texts": _user_texts(primary_body),
        "tool_names": [tool.get("name") for tool in primary_body.get("tools") or []],
        "tool_schemas": primary_body.get("tools") or [],
        "tool_path_guidance": _tool_path_guidance(primary_body.get("tools") or []),
        "assistant_tool_uses": assistant_tool_uses,
        "stdout_init": init_event,
        "final_result": final_result,
    }


def _run_case(case: CaseSpec, *, model: str, keep_raw: bool) -> dict[str, object]:
    run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{case.name}"
    if keep_raw:
        raw_dir = RAW_ROOT / run_id
        raw_dir.mkdir(parents=True, exist_ok=False)
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory(prefix=f"claude-system-{case.name}-")
        raw_dir = Path(temp_context.name)

    try:
        paths = _prepare_workspace(raw_dir)
        proxy_log = raw_dir / "proxy.log"
        stdout_jsonl = raw_dir / "claude_stdout.jsonl"
        stderr_log = raw_dir / "claude_stderr.log"
        debug_log = raw_dir / "claude_debug.log"
        port = _free_port()

        with proxy_log.open("w", encoding="utf-8") as proxy_out:
            proxy = subprocess.Popen(
                ["node", str(PROXY_JS), "http://localhost:11434/v1", str(port)],
                cwd=str(PROXY_JS.parent),
                stdout=proxy_out,
                stderr=subprocess.STDOUT,
                text=True,
            )
        try:
            _wait_for_proxy(port)
            base_url = f"http://localhost:{port}/api"
            env_settings = {
                "ANTHROPIC_BASE_URL": base_url,
                "ANTHROPIC_API_KEY": "ollama",
                "ANTHROPIC_AUTH_TOKEN": "ollama",
                "ANTHROPIC_SMALL_FAST_MODEL": model,
                "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
                "DISABLE_TELEMETRY": "1",
                "OTEL_METRICS_EXPORTER": "none",
                "OTEL_TRACES_EXPORTER": "none",
                "OTEL_LOGS_EXPORTER": "none",
            }
            command = [
                "claude",
                "-p",
                "--verbose",
                "--debug-file",
                str(debug_log),
                "--setting-sources",
                "project",
                "--settings",
                json.dumps({"env": env_settings}, separators=(",", ":")),
                "--no-session-persistence",
                "--model",
                model,
                "--tools",
                case.tools,
                "--permission-mode",
                "bypassPermissions",
                "--output-format",
                "stream-json",
                case.prompt,
            ]
            env = {**os.environ, **env_settings}
            with stdout_jsonl.open("w", encoding="utf-8") as stdout_out, stderr_log.open(
                "w", encoding="utf-8"
            ) as stderr_out:
                completed = subprocess.run(
                    command,
                    cwd=str(paths["workspace"]),
                    env=env,
                    stdout=stdout_out,
                    stderr=stderr_out,
                    text=True,
                    timeout=150,
                    check=False,
                )
        finally:
            proxy.terminate()
            try:
                proxy.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy.kill()
                proxy.wait(timeout=5)

        replacements = {
            str(paths["workspace"].resolve()): "<WORKSPACE>",
            str(paths["workspace"]): "<WORKSPACE>",
            str(REPO_ROOT.resolve()): "<REPO_ROOT>",
            str(raw_dir.resolve()): "<RAW_DIR>",
            str(raw_dir): "<RAW_DIR>",
        }
        fixture = build_system_fixture(
            case_name=case.name,
            proxy_log=proxy_log,
            stdout_jsonl=stdout_jsonl,
            replacements=replacements,
        )
        fixture["raw_artifact_dir"] = "<RAW_DIR>" if keep_raw else None
        fixture["claude_returncode"] = completed.returncode
        fixture_path = FIXTURE_ROOT / f"{case.name}.json"
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        tool_use_found = bool(fixture.get("assistant_tool_uses"))
        return {
            "case": case.name,
            "returncode": completed.returncode,
            "fixture": str(fixture_path),
            "raw": str(raw_dir) if keep_raw else None,
            "system_found": bool(fixture.get("system_block_count")),
            "tool_names": fixture.get("tool_names"),
            "tool_use_found": tool_use_found,
            "expected_tool_use": case.expect_tool_use,
            "final_result": fixture.get("final_result"),
        }
    finally:
        if temp_context is not None:
            temp_context.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=[*CASES.keys(), "all"],
        default="read-relative-path",
        help="System-message investigation case to run.",
    )
    parser.add_argument("--model", default=os.environ.get("CLAUDE_INVESTIGATION_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--discard-raw",
        action="store_true",
        help="Use a temporary raw directory and keep only normalized fixtures.",
    )
    args = parser.parse_args()

    _require_executable("claude")
    _require_executable("node")
    _require_executable("curl")
    if not PROXY_JS.exists():
        raise SystemExit(f"proxy not found: {PROXY_JS}")
    ollama = _run(["curl", "-sS", "http://localhost:11434/api/tags"], cwd=REPO_ROOT, timeout=10)
    if ollama.returncode != 0:
        raise SystemExit("Ollama is not reachable at http://localhost:11434")

    selected = CASES.values() if args.case == "all" else [CASES[args.case]]
    summaries = [_run_case(case, model=args.model, keep_raw=not args.discard_raw) for case in selected]
    print(json.dumps(summaries, indent=2, sort_keys=True))
    failed = [
        item
        for item in summaries
        if not item["system_found"] or (item["expected_tool_use"] and not item["tool_use_found"])
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())