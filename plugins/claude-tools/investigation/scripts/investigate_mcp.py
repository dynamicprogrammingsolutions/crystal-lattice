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

"""Run deterministic Claude Code investigations for MCP-backed tools."""

from __future__ import annotations

import argparse
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
RAW_ROOT = PLUGIN_ROOT / "investigation" / "raw" / "mcp"
FIXTURE_ROOT = PLUGIN_ROOT / "investigation" / "fixtures" / "mcp"
DEFAULT_MODEL = "qwen3-coder-next:cloud"


@dataclass(frozen=True)
class CaseSpec:
    name: str
    prompt: str
    expected_fragment: str


CASES: dict[str, CaseSpec] = {
    "filesystem-read-file": CaseSpec(
        name="filesystem-read-file",
        prompt=(
            "Use the MCP filesystem tool to read note.txt. "
            "Reply with exactly the first line and nothing else."
        ),
        expected_fragment="CLAUDE_MCP_SENTINEL first line",
    ),
    "filesystem-read-nested-file": CaseSpec(
        name="filesystem-read-nested-file",
        prompt=(
            "Use the MCP filesystem tool to read nested/facts.md. "
            "Reply with exactly the value after 'Answer:' and nothing else."
        ),
        expected_fragment="CLAUDE_MCP_NESTED_VALUE",
    ),
    "filesystem-missing-file": CaseSpec(
        name="filesystem-missing-file",
        prompt=(
            "Use the MCP filesystem tool to read missing.txt. "
            "Briefly report the tool error."
        ),
        expected_fragment="",
    ),
}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required executable not found: {name}")


def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
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
        proc = _run(
            ["curl", "-sS", f"http://localhost:{port}/health"],
            cwd=REPO_ROOT,
            timeout=5,
        )
        if proc.returncode == 0:
            return
        time.sleep(0.2)
    raise RuntimeError(f"proxy did not become ready on port {port}")


def _proxy_js_path() -> Path:
    env_path = os.getenv("CLAUDE_INVESTIGATION_PROXY_JS")
    candidates = []
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.extend(
        [
            REPO_ROOT.parent / "openai-proxy" / "proxy.js",
            REPO_ROOT.parent.parent / "openai-proxy" / "proxy.js",
            REPO_ROOT.parent.parent / "AI-setup" / "openai-proxy" / "proxy.js",
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise SystemExit(
        "could not find openai-proxy/proxy.js; set CLAUDE_INVESTIGATION_PROXY_JS"
    )


def _prepare_workspace(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "note.txt").write_text(
        "CLAUDE_MCP_SENTINEL first line\nsecond line\n",
        encoding="utf-8",
    )
    nested = workspace / "nested"
    nested.mkdir()
    (nested / "facts.md").write_text(
        "# Facts\n\nAnswer: CLAUDE_MCP_NESTED_VALUE\n",
        encoding="utf-8",
    )


def _write_mcp_config(path: Path, workspace: Path) -> None:
    payload = {
        "mcpServers": {
            "filesystem": {
                "type": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(workspace),
                ],
            }
        }
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _replace_all(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        for source, target in replacements.items():
            if source:
                value = value.replace(source, target)
        return value
    if isinstance(value, list):
        return [_replace_all(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_all(item, replacements) for key, item in value.items()}
    return value


def _mcp_tools_from_request(request: dict[str, Any]) -> list[dict[str, Any]]:
    body = request.get("body")
    if not isinstance(body, dict):
        return []
    tools = body.get("tools")
    if not isinstance(tools, list):
        return []
    return [
        tool
        for tool in tools
        if isinstance(tool, dict) and _looks_like_mcp_tool_name(tool.get("name"))
    ]


def _looks_like_mcp_tool_name(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.startswith("mcp__") or value.startswith("filesystem__")


def _extract_tool_uses(request: dict[str, Any]) -> list[dict[str, Any]]:
    body = request.get("body")
    if not isinstance(body, dict):
        return []
    messages = body.get("messages")
    if not isinstance(messages, list):
        return []
    found: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and _looks_like_mcp_tool_name(block.get("name"))
            ):
                found.append(block)
    return found


def _extract_tool_results(request: dict[str, Any]) -> list[dict[str, Any]]:
    body = request.get("body")
    if not isinstance(body, dict):
        return []
    messages = body.get("messages")
    if not isinstance(messages, list):
        return []
    found: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                found.append(block)
    return found


def _extract_mcp_prompt_parts(request: dict[str, Any]) -> list[str]:
    body = request.get("body")
    if not isinstance(body, dict):
        return []
    text = json.dumps(body, ensure_ascii=False)
    return sorted(set(re.findall(r"mcp__[A-Za-z0-9_]+__[A-Za-z0-9_]+", text)))


def _extract_stdout_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "event_types": [event.get("type") for event in events],
        "system_subtypes": [
            event.get("subtype") for event in events if event.get("type") == "system"
        ],
        "tool_uses": [],
        "tool_results": [],
        "final_result": None,
    }
    for event in events:
        if event.get("type") == "assistant":
            message = event.get("message")
            if isinstance(message, dict):
                for block in message.get("content") or []:
                    if (
                        isinstance(block, dict)
                        and block.get("type") == "tool_use"
                        and _looks_like_mcp_tool_name(block.get("name"))
                    ):
                        summary["tool_uses"].append(block)
        if event.get("type") == "user":
            message = event.get("message")
            if isinstance(message, dict):
                for block in message.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        summary["tool_results"].append(block)
        if event.get("type") == "result":
            summary["final_result"] = event.get("result")
    return summary


def _dedupe_by_json(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(item, sort_keys=True, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _dedupe_tools_by_name(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for item in items:
        name = item.get("name")
        if isinstance(name, str) and name not in by_name:
            by_name[name] = item
    return [by_name[name] for name in sorted(by_name.keys())]


def _build_fixture(
    *,
    case_name: str,
    workspace: Path,
    mcp_config: Path,
    proxy_log: Path,
    stdout_jsonl: Path,
    stderr_log: Path,
    debug_log: Path,
) -> dict[str, Any]:
    requests = parse_proxy_log(proxy_log)
    events = _read_jsonl(stdout_jsonl)
    replacements = {
        str(workspace.resolve()): "<WORKSPACE>",
        str(workspace): "<WORKSPACE>",
        str(mcp_config.resolve()): "<MCP_CONFIG>",
        str(mcp_config): "<MCP_CONFIG>",
        str(stdout_jsonl.resolve()): "<STDOUT_JSONL>",
        str(stdout_jsonl): "<STDOUT_JSONL>",
        str(stderr_log.resolve()): "<STDERR_LOG>",
        str(stderr_log): "<STDERR_LOG>",
        str(debug_log.resolve()): "<DEBUG_LOG>",
        str(debug_log): "<DEBUG_LOG>",
    }
    normalized_requests = normalize_value(
        _replace_all(requests, replacements),
        replacements,
    )
    normalized_events = normalize_value(
        _replace_all(events, replacements),
        replacements,
    )

    mcp_tools: list[dict[str, Any]] = []
    tool_uses: list[dict[str, Any]] = []
    tool_results: list[dict[str, Any]] = []
    prompt_tool_names: list[str] = []
    for request in normalized_requests:
        mcp_tools.extend(_mcp_tools_from_request(request))
        tool_uses.extend(_extract_tool_uses(request))
        tool_results.extend(_extract_tool_results(request))
        prompt_tool_names.extend(_extract_mcp_prompt_parts(request))

    mcp_tools = _dedupe_tools_by_name(mcp_tools)
    tool_uses = _dedupe_by_json(tool_uses)
    tool_results = _dedupe_by_json(tool_results)
    stdout_summary = _extract_stdout_summary(normalized_events)
    stderr_text = stderr_log.read_text(encoding="utf-8", errors="replace")
    debug_text = debug_log.read_text(encoding="utf-8", errors="replace")
    stderr_text = normalize_value(_replace_all(stderr_text, replacements), replacements)
    debug_text = normalize_value(_replace_all(debug_text, replacements), replacements)

    return {
        "case": case_name,
        "request_count": len(normalized_requests),
        "request_urls": [request.get("url") for request in normalized_requests],
        "mcp_tool_names": sorted(
            {
                str(tool.get("name"))
                for tool in mcp_tools
                if isinstance(tool.get("name"), str)
            }
        ),
        "mcp_tools": mcp_tools,
        "assistant_tool_uses": tool_uses,
        "tool_results": tool_results,
        "prompt_mcp_tool_names": sorted(set(prompt_tool_names)),
        "stdout_summary": stdout_summary,
        "stderr_excerpt": str(stderr_text)[-4000:],
        "debug_mcp_lines": [
            line
            for line in str(debug_text).splitlines()
            if "mcp" in line.lower() or "filesystem" in line.lower()
        ][-80:],
    }


def _run_case(
    case: CaseSpec,
    *,
    model: str,
    keep_raw: bool,
    timeout: int,
) -> dict[str, str]:
    run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{case.name}"
    if keep_raw:
        raw_dir = RAW_ROOT / run_id
        raw_dir.mkdir(parents=True, exist_ok=False)
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory(prefix=f"claude-mcp-{case.name}-")
        raw_dir = Path(temp_context.name)

    proxy_js = _proxy_js_path()
    try:
        workspace = raw_dir / "workspace"
        _prepare_workspace(workspace)
        mcp_config = raw_dir / "mcp.json"
        _write_mcp_config(mcp_config, workspace)

        proxy_log = raw_dir / "proxy.log"
        stdout_path = raw_dir / "stdout.jsonl"
        stderr_path = raw_dir / "stderr.log"
        debug_path = raw_dir / "debug.log"
        port = _free_port()

        with proxy_log.open("w", encoding="utf-8") as proxy_out:
            proxy = subprocess.Popen(
                ["node", str(proxy_js), "http://localhost:11434/v1", str(port)],
                cwd=str(proxy_js.parent),
                stdout=proxy_out,
                stderr=subprocess.STDOUT,
                text=True,
            )
        try:
            _wait_for_proxy(port)
            base_url = f"http://localhost:{port}/api"
            settings = json.dumps(
                {
                    "env": {
                        "ANTHROPIC_BASE_URL": base_url,
                        "ANTHROPIC_API_KEY": "ollama",
                        "ANTHROPIC_AUTH_TOKEN": "ollama",
                        "ANTHROPIC_SMALL_FAST_MODEL": model,
                        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
                    }
                }
            )

            command = [
                "claude",
                "-p",
                "--verbose",
                "--bare",
                "--setting-sources",
                "project",
                "--settings",
                settings,
                "--debug-file",
                str(debug_path),
                "--model",
                model,
                "--permission-mode",
                "bypassPermissions",
                "--strict-mcp-config",
                "--mcp-config",
                str(mcp_config),
                "--output-format",
                "stream-json",
                case.prompt,
            ]
            proc = subprocess.run(
                command,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
            )
            stdout_path.write_text(proc.stdout, encoding="utf-8")
            stderr_path.write_text(proc.stderr, encoding="utf-8")
            fixture = _build_fixture(
                case_name=case.name,
                workspace=workspace,
                mcp_config=mcp_config,
                proxy_log=proxy_log,
                stdout_jsonl=stdout_path,
                stderr_log=stderr_path,
                debug_log=debug_path,
            )
            fixture["returncode"] = proc.returncode
            fixture["expected_fragment"] = case.expected_fragment
            fixture["expected_fragment_seen"] = bool(
                case.expected_fragment
            ) and case.expected_fragment in json.dumps(fixture, ensure_ascii=False)
            output_path = FIXTURE_ROOT / f"{case.name}.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(fixture, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return {
                "case": case.name,
                "fixture": str(output_path),
                "raw_dir": str(raw_dir),
                "returncode": str(proc.returncode),
            }
        finally:
            proxy.terminate()
            try:
                proxy.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proxy.kill()
                proxy.wait(timeout=2)
    finally:
        if temp_context is not None:
            temp_context.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=["all", *sorted(CASES)],
        default="all",
        help="Case to run (default: all)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--keep-raw", action="store_true")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    _require_executable("claude")
    _require_executable("node")
    _require_executable("curl")
    _require_executable("npx")

    selected = sorted(CASES) if args.case == "all" else [args.case]
    results = [
        _run_case(
            CASES[name], model=args.model, keep_raw=args.keep_raw, timeout=args.timeout
        )
        for name in selected
    ]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
