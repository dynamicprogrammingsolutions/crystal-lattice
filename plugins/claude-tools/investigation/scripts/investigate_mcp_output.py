#!/usr/bin/env python3
# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");

"""Investigate Claude Code formatting/truncation of large MCP outputs."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from normalize_proxy_log import normalize_value, parse_proxy_log


REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SERVER_SRC = REPO_ROOT / "plugins" / "dummy-mcp-output-server" / "src"
RAW_ROOT = PLUGIN_ROOT / "investigation" / "raw" / "mcp-output"
FIXTURE_ROOT = PLUGIN_ROOT / "investigation" / "fixtures" / "mcp-output"
DEFAULT_MODEL = "qwen3-coder-next:cloud"


@dataclass(frozen=True)
class CaseSpec:
    name: str
    tool: str
    arguments: dict[str, Any]


CASES: dict[str, CaseSpec] = {
    "success-8k": CaseSpec(
        name="success-8k",
        tool="large_text_output",
        arguments={"size_chars": 8192, "line_length": 80},
    ),
    "success-16k": CaseSpec(
        name="success-16k",
        tool="large_text_output",
        arguments={"size_chars": 16384, "line_length": 80},
    ),
    "success-32k": CaseSpec(
        name="success-32k",
        tool="large_text_output",
        arguments={"size_chars": 32768, "line_length": 80},
    ),
    "success-64k": CaseSpec(
        name="success-64k",
        tool="large_text_output",
        arguments={"size_chars": 65536, "line_length": 80},
    ),
    "success-256k": CaseSpec(
        name="success-256k",
        tool="large_text_output",
        arguments={"size_chars": 262144, "line_length": 80},
    ),
    "error-64k": CaseSpec(
        name="error-64k",
        tool="large_error_output",
        arguments={"size_chars": 65536, "line_length": 80},
    ),
}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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


def _require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required executable not found: {name}")


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


def _write_mcp_config(path: Path) -> None:
    pythonpath = str(SERVER_SRC)
    if os.environ.get("PYTHONPATH"):
        pythonpath = pythonpath + os.pathsep + str(os.environ["PYTHONPATH"])
    payload = {
        "mcpServers": {
            "dummy_output": {
                "type": "stdio",
                "command": sys.executable,
                "args": [
                    "-m",
                    "dummy_mcp_output_server",
                    "--transport",
                    "stdio",
                ],
                "env": {
                    "PYTHONPATH": pythonpath,
                },
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


def _looks_like_dummy_tool_name(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("mcp__dummy_output__")


def _extract_dummy_tools(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}
    for request in requests:
        for tool in request.get("body", {}).get("tools", []) or []:
            if isinstance(tool, dict) and _looks_like_dummy_tool_name(tool.get("name")):
                name = str(tool["name"])
                if name not in by_name:
                    by_name[name] = tool
    for name in sorted(by_name):
        tools.append(by_name[name])
    return tools


def _extract_tool_uses(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for request in requests:
        for message in request.get("body", {}).get("messages", []) or []:
            for block in message.get("content", []) or []:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and _looks_like_dummy_tool_name(block.get("name"))
                ):
                    key = json.dumps(block, sort_keys=True)
                    if key not in seen:
                        seen.add(key)
                        found.append(block)
    return found


def _extract_tool_results(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for request in requests:
        for message in request.get("body", {}).get("messages", []) or []:
            for block in message.get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    key = json.dumps(block, sort_keys=True)
                    if key not in seen:
                        seen.add(key)
                        found.append(block)
    return found


def _tool_result_content_text(block: dict[str, Any]) -> str:
    content = block.get("content")
    if not isinstance(content, str):
        return ""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return content
    if isinstance(parsed, dict) and isinstance(parsed.get("content"), str):
        return parsed["content"]
    return content


def _summarize_tool_result(block: dict[str, Any]) -> dict[str, Any]:
    text = _tool_result_content_text(block)
    return {
        "content_chars": len(text),
        "is_error": bool(block.get("is_error")),
        "has_begin_sentinel": "BEGIN_SENTINEL" in text,
        "has_middle_sentinel": "MIDDLE_SENTINEL" in text,
        "has_end_sentinel": "END_SENTINEL" in text,
        "has_truncated_marker": "truncated" in text.lower(),
        "prefix": text[:500],
        "suffix": text[-500:],
    }


def _shorten_log_line(line: str, *, max_chars: int = 500) -> str:
    if len(line) <= max_chars:
        return line
    omitted = len(line) - max_chars
    head_chars = max_chars // 2
    tail_chars = max_chars - head_chars
    return f"{line[:head_chars]}... [{omitted} chars omitted] ...{line[-tail_chars:]}"


def _extract_stdout_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "event_types": [event.get("type") for event in events],
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
                        and _looks_like_dummy_tool_name(block.get("name"))
                    ):
                        summary["tool_uses"].append(block)
        if event.get("type") == "user":
            message = event.get("message")
            if isinstance(message, dict):
                for block in message.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        summary["tool_results"].append(_summarize_tool_result(block))
        if event.get("type") == "result":
            summary["final_result"] = event.get("result")
    return summary


def _build_fixture(
    *,
    case: CaseSpec,
    raw_dir: Path,
    mcp_config: Path,
    proxy_log: Path,
    stdout_jsonl: Path,
    stderr_log: Path,
    debug_log: Path,
) -> dict[str, Any]:
    requests = parse_proxy_log(proxy_log)
    events = _read_jsonl(stdout_jsonl)
    replacements = {
        str(raw_dir.resolve()): "<RAW_DIR>",
        str(raw_dir): "<RAW_DIR>",
        str(mcp_config.resolve()): "<MCP_CONFIG>",
        str(mcp_config): "<MCP_CONFIG>",
        str(SERVER_SRC.resolve()): "<DUMMY_MCP_OUTPUT_SERVER_SRC>",
    }
    normalized_requests = normalize_value(
        _replace_all(requests, replacements), replacements
    )
    normalized_events = normalize_value(
        _replace_all(events, replacements), replacements
    )
    tool_results = _extract_tool_results(normalized_requests)
    stderr_text = normalize_value(
        _replace_all(
            stderr_log.read_text(encoding="utf-8", errors="replace"), replacements
        ),
        replacements,
    )
    debug_text = normalize_value(
        _replace_all(
            debug_log.read_text(encoding="utf-8", errors="replace"), replacements
        ),
        replacements,
    )
    return {
        "case": case.name,
        "requested_tool": case.tool,
        "requested_arguments": case.arguments,
        "request_count": len(normalized_requests),
        "request_urls": [request.get("url") for request in normalized_requests],
        "mcp_tools": _extract_dummy_tools(normalized_requests),
        "assistant_tool_uses": _extract_tool_uses(normalized_requests),
        "tool_results": tool_results,
        "tool_result_summaries": [
            _summarize_tool_result(block) for block in tool_results
        ],
        "stdout_summary": _extract_stdout_summary(normalized_events),
        "stderr_excerpt": str(stderr_text)[-4000:],
        "debug_mcp_lines": [
            _shorten_log_line(line)
            for line in str(debug_text).splitlines()
            if "mcp" in line.lower() or "dummy_output" in line.lower()
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
        temp_context = tempfile.TemporaryDirectory(
            prefix=f"claude-mcp-output-{case.name}-"
        )
        raw_dir = Path(temp_context.name)

    proxy_js = _proxy_js_path()
    try:
        workspace = raw_dir / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        mcp_config = raw_dir / "mcp.json"
        _write_mcp_config(mcp_config)
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
            settings = json.dumps(
                {
                    "env": {
                        "ANTHROPIC_BASE_URL": f"http://localhost:{port}/api",
                        "ANTHROPIC_API_KEY": "ollama",
                        "ANTHROPIC_AUTH_TOKEN": "ollama",
                        "ANTHROPIC_SMALL_FAST_MODEL": model,
                        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
                    }
                }
            )
            prompt = (
                f"Use the MCP dummy_output tool {case.tool} with exactly these JSON "
                f"arguments: {json.dumps(case.arguments, sort_keys=True)}. "
                "After the tool finishes, reply with exactly OK and nothing else."
            )
            proc = subprocess.run(
                [
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
                    prompt,
                ],
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
                case=case,
                raw_dir=raw_dir,
                mcp_config=mcp_config,
                proxy_log=proxy_log,
                stdout_jsonl=stdout_path,
                stderr_log=stderr_path,
                debug_log=debug_path,
            )
            fixture["returncode"] = proc.returncode
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
    parser.add_argument("--case", choices=["all", *sorted(CASES)], default="all")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--keep-raw", action="store_true")
    parser.add_argument(
        "--from-raw-dir",
        type=Path,
        help="Normalize an existing raw run directory instead of running Claude Code.",
    )
    parser.add_argument("--timeout", type=int, default=360)
    args = parser.parse_args()

    if args.from_raw_dir is not None:
        if args.case == "all":
            raise SystemExit("--from-raw-dir requires a specific --case")
        case = CASES[args.case]
        fixture = _build_fixture(
            case=case,
            raw_dir=args.from_raw_dir,
            mcp_config=args.from_raw_dir / "mcp.json",
            proxy_log=args.from_raw_dir / "proxy.log",
            stdout_jsonl=args.from_raw_dir / "stdout.jsonl",
            stderr_log=args.from_raw_dir / "stderr.log",
            debug_log=args.from_raw_dir / "debug.log",
        )
        output_path = FIXTURE_ROOT / f"{case.name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(fixture, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"case": case.name, "fixture": str(output_path)}, indent=2))
        return 0

    _require_executable("claude")
    _require_executable("node")
    _require_executable("curl")

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
