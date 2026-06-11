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

"""Run deterministic Claude Code investigations for the TaskStop tool."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from normalize_proxy_log import (
    find_tool_schema,
    normalize_value,
    parse_proxy_log,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
PROXY_JS = REPO_ROOT.parent / "openai-proxy" / "proxy.js"
RAW_ROOT = PLUGIN_ROOT / "investigation" / "raw" / "task-stop"
FIXTURE_ROOT = PLUGIN_ROOT / "investigation" / "fixtures" / "task-stop"
DEFAULT_MODEL = "qwen3-coder-next:cloud"


@dataclass(frozen=True)
class CaseSpec:
    name: str
    prompt: str


CASES = {
    "success-stop-background-task": CaseSpec(
        name="success-stop-background-task",
        prompt=(
            "Using the available standard tools, start an infinite background process with Bash "
            "using the exact command while true; do sleep 60; done. "
            "If a dedicated task-management tool for stopping background tasks exists, prefer using that "
            "instead of a shell kill command. Then stop that same process before finishing. "
            "Do not retry with a different background command. "
            "After the process is stopped, answer with exactly STOPPED."
        ),
    ),
    "error-task-not-found": CaseSpec(
        name="error-task-not-found",
        prompt=(
            "Use the TaskStop tool exactly once with task_id set to does-not-exist. "
            "After that one tool call, answer with exactly DONE."
        ),
    ),
    "error-invalid-parameters": CaseSpec(
        name="error-invalid-parameters",
        prompt=(
            "Use the TaskStop tool exactly once with task_id set to does-not-exist, "
            'block set to "true", and timeout set to "10000". '
            "After that one tool call, answer with exactly DONE."
        ),
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


def _find_last_tool_use(
    requests: list[dict[str, Any]],
    *,
    tool_name: str,
) -> dict[str, Any] | None:
    found: dict[str, Any] | None = None
    for request in requests:
        for message in request.get("body", {}).get("messages", []) or []:
            for item in message.get("content", []) or []:
                if (
                    isinstance(item, dict)
                    and item.get("type") == "tool_use"
                    and item.get("name") == tool_name
                ):
                    found = item
    return found


def _find_last_tool_result_message(
    requests: list[dict[str, Any]],
    *,
    tool_use_id: str | None,
) -> dict[str, Any] | None:
    if not isinstance(tool_use_id, str):
        return None
    found: dict[str, Any] | None = None
    for request in requests:
        for message in request.get("body", {}).get("messages", []) or []:
            for item in message.get("content", []) or []:
                if (
                    isinstance(item, dict)
                    and item.get("type") == "tool_result"
                    and item.get("tool_use_id") == tool_use_id
                ):
                    found = {"role": "user", "content": [item]}
    return found


def _background_replacements(
    raw_tool_result_message: dict[str, Any] | None,
    raw_tool_use: dict[str, Any] | None,
) -> dict[str, str]:
    replacements: dict[str, str] = {}
    if not isinstance(raw_tool_use, dict):
        return replacements
    task_id = raw_tool_use.get("input", {}).get("task_id")
    if isinstance(task_id, str) and task_id and task_id != "does-not-exist":
        replacements[task_id] = "<BACKGROUND_ID>"
    if not isinstance(raw_tool_result_message, dict):
        return replacements
    content = raw_tool_result_message.get("content")
    if not isinstance(content, list):
        return replacements
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("content")
        if not isinstance(text, str):
            continue
        marker = 'Successfully stopped task: '
        if marker in text:
            start = text.index(marker) + len(marker)
            end = text.find(" ", start)
            if end > start:
                replacements[text[start:end]] = "<BACKGROUND_ID>"
    return replacements


def build_fixture(
    *,
    case_name: str,
    proxy_log: Path,
    stdout_jsonl: Path,
) -> dict[str, Any]:
    raw_requests = parse_proxy_log(proxy_log)
    raw_tool_schema = find_tool_schema(raw_requests, tool_name="TaskStop")
    raw_assistant_tool_use = _find_last_tool_use(raw_requests, tool_name="TaskStop")
    tool_use_id = (
        raw_assistant_tool_use.get("id")
        if isinstance(raw_assistant_tool_use, dict)
        and isinstance(raw_assistant_tool_use.get("id"), str)
        else None
    )
    raw_tool_result_message = _find_last_tool_result_message(
        raw_requests,
        tool_use_id=tool_use_id,
    )
    replacements = _background_replacements(
        raw_tool_result_message,
        raw_assistant_tool_use,
    )
    requests = normalize_value(raw_requests, replacements)
    fixture: dict[str, Any] = {
        "case": case_name,
        "request_count": len(requests),
        "request_urls": [request.get("url") for request in requests],
        "tool_schema": normalize_value(raw_tool_schema, replacements),
        "assistant_tool_use": normalize_value(raw_assistant_tool_use, replacements),
        "tool_result_message": normalize_value(raw_tool_result_message, replacements),
        "final_result": None,
    }

    for event in _read_stdout_events(stdout_jsonl):
        if event.get("type") == "result":
            fixture["final_result"] = normalize_value(event.get("result"), replacements)
            break

    return fixture


def _run_case(case: CaseSpec, *, model: str, keep_raw: bool) -> dict[str, object]:
    run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{case.name}"
    if keep_raw:
        raw_dir = RAW_ROOT / run_id
        raw_dir.mkdir(parents=True, exist_ok=False)
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory(prefix=f"claude-task-stop-{case.name}-")
        raw_dir = Path(temp_context.name)

    try:
        workspace = raw_dir / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
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
                    cwd=str(workspace),
                    env=env,
                    stdout=stdout_out,
                    stderr=stderr_out,
                    text=True,
                    timeout=180,
                    check=False,
                )
        finally:
            proxy.terminate()
            try:
                proxy.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy.kill()
                proxy.wait(timeout=5)

        fixture = build_fixture(
            case_name=case.name,
            proxy_log=proxy_log,
            stdout_jsonl=stdout_jsonl,
        )
        fixture["raw_artifact_dir"] = "<RAW_DIR>" if keep_raw else None
        fixture["claude_returncode"] = completed.returncode
        fixture_path = FIXTURE_ROOT / f"{case.name}.json"
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(
            json.dumps(fixture, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        return {
            "case": case.name,
            "returncode": completed.returncode,
            "fixture": str(fixture_path),
            "raw": str(raw_dir) if keep_raw else None,
            "schema_found": fixture.get("tool_schema") is not None,
            "tool_use_found": fixture.get("assistant_tool_use") is not None,
            "tool_result_found": fixture.get("tool_result_message") is not None,
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
        default="success-stop-background-task",
        help="TaskStop investigation case to run.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_INVESTIGATION_MODEL", DEFAULT_MODEL),
    )
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
    summaries = [
        _run_case(case, model=args.model, keep_raw=not args.discard_raw)
        for case in selected
    ]
    print(json.dumps(summaries, indent=2, sort_keys=True))
    failed = [
        item
        for item in summaries
        if not (
            item["schema_found"]
            and item["tool_use_found"]
            and item["tool_result_found"]
        )
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())