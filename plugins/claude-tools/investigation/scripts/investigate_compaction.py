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

"""Run deterministic Claude Code investigations for manual compaction."""

from __future__ import annotations

import argparse
from collections import Counter
import json
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
RAW_ROOT = PLUGIN_ROOT / "investigation" / "raw" / "compaction"
FIXTURE_ROOT = PLUGIN_ROOT / "investigation" / "fixtures" / "compaction"
DEFAULT_MODEL = "qwen3-coder-next:cloud"


@dataclass(frozen=True)
class StepSpec:
    prompt: str
    continue_session: bool = False


@dataclass(frozen=True)
class CaseSpec:
    name: str
    steps: tuple[StepSpec, ...]
    prepare_workspace: str | None = None


CASES: dict[str, CaseSpec] = {
    "error-no-messages": CaseSpec(
        name="error-no-messages",
        steps=(StepSpec(prompt="/compact"),),
    ),
    "error-not-enough-messages": CaseSpec(
        name="error-not-enough-messages",
        steps=(
            StepSpec(prompt="Answer exactly READY."),
            StepSpec(prompt="/compact", continue_session=True),
        ),
    ),
    "success-basic": CaseSpec(
        name="success-basic",
        steps=(
            StepSpec(prompt="Answer exactly ONE."),
            StepSpec(prompt="Answer exactly TWO.", continue_session=True),
            StepSpec(prompt="Answer exactly THREE.", continue_session=True),
            StepSpec(prompt="/compact", continue_session=True),
        ),
    ),
    "success-tool-history": CaseSpec(
        name="success-tool-history",
        prepare_workspace="tool_history",
        steps=(
            StepSpec(
                prompt=(
                    "Use the Read tool to read README.md. "
                    "Then answer exactly PROBE1."
                )
            ),
            StepSpec(prompt="Answer exactly PROBE2.", continue_session=True),
            StepSpec(prompt="Answer exactly PROBE3.", continue_session=True),
            StepSpec(prompt="/compact", continue_session=True),
        ),
    ),
    "success-prior-summary": CaseSpec(
        name="success-prior-summary",
        steps=(
            StepSpec(prompt="Answer exactly FIRST."),
            StepSpec(prompt="Answer exactly SECOND.", continue_session=True),
            StepSpec(prompt="Answer exactly THIRD.", continue_session=True),
            StepSpec(prompt="/compact", continue_session=True),
            StepSpec(prompt="Answer exactly FOURTH.", continue_session=True),
            StepSpec(prompt="Answer exactly FIFTH.", continue_session=True),
            StepSpec(prompt="Answer exactly SIXTH.", continue_session=True),
            StepSpec(prompt="/compact", continue_session=True),
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


def _run(
    command: list[str], *, cwd: Path, timeout: int = 30
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
            ["curl", "-sS", f"http://localhost:{port}/health"], cwd=REPO_ROOT, timeout=5
        )
        if proc.returncode == 0:
            return
        time.sleep(0.2)
    raise RuntimeError(f"proxy did not become ready on port {port}")


def _prepare_workspace(workspace: Path, mode: str | None) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    if mode == "tool_history":
        (workspace / "README.md").write_text(
            "# Probe Heading\n\nBody\n", encoding="utf-8"
        )


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


def _session_file_for_id(session_id: str) -> Path:
    projects_root = Path.home() / ".claude" / "projects"
    candidates = sorted(
        projects_root.glob("*/*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if session_id in text:
            return candidate
    raise FileNotFoundError(f"no session transcript found for session_id={session_id}")


def _replace_all(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        for source, target in replacements.items():
            value = value.replace(source, target)
        return value
    if isinstance(value, list):
        return [_replace_all(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_all(item, replacements) for key, item in value.items()}
    return value


def _compact_summary_events(
    project_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for event in project_events:
        if event.get("isCompactSummary") is True:
            found.append(event)
    return found


def _attachment_events(project_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in project_events if event.get("type") == "attachment"]


def _project_transcript_type_counts(
    project_events: list[dict[str, Any]],
) -> dict[str, int]:
    counts = Counter(str(event.get("type")) for event in project_events)
    return dict(sorted(counts.items()))


def _collect_uuid_placeholders(value: Any, *, excluded: set[str]) -> dict[str, str]:
    replacements: dict[str, str] = {}

    def visit(item: Any) -> None:
        if isinstance(item, str):
            for match in re.finditer(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                item,
                flags=re.IGNORECASE,
            ):
                uuid_text = match.group(0)
                if uuid_text in excluded or uuid_text in replacements:
                    continue
                replacements[uuid_text] = f"<UUID_{len(replacements) + 1:03d}>"
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for child in item.values():
                visit(child)

    visit(value)
    return replacements


def _collect_prompt_id_placeholders(
    project_events: list[dict[str, Any]],
    *,
    excluded: set[str],
) -> dict[str, str]:
    replacements: dict[str, str] = {}
    for event in project_events:
        prompt_id = event.get("promptId")
        if not isinstance(prompt_id, str):
            continue
        if prompt_id in excluded or prompt_id in replacements:
            continue
        replacements[prompt_id] = f"<PROMPT_ID_{len(replacements) + 1:03d}>"
    return replacements


def _collect_regex_placeholders(
    value: Any,
    *,
    pattern: str,
    prefix: str,
    excluded: set[str],
) -> dict[str, str]:
    replacements: dict[str, str] = {}
    compiled = re.compile(pattern)

    def visit(item: Any) -> None:
        if isinstance(item, str):
            for match in compiled.finditer(item):
                text = match.group(0)
                if text in excluded or text in replacements:
                    continue
                replacements[text] = f"<{prefix}_{len(replacements) + 1:03d}>"
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for child in item.values():
                visit(child)

    visit(value)
    return replacements


def _collect_transcript_string_placeholders(
    project_events: list[dict[str, Any]],
    *,
    excluded: set[str],
) -> dict[str, str]:
    placeholders: dict[str, str] = {}
    placeholders.update(
        _collect_prompt_id_placeholders(project_events, excluded=excluded)
    )
    excluded_with_prompt_ids = excluded | set(placeholders)
    placeholders.update(
        _collect_uuid_placeholders(
            project_events,
            excluded=excluded_with_prompt_ids,
        )
    )
    excluded_with_uuids = excluded_with_prompt_ids | set(placeholders)
    placeholders.update(
        _collect_regex_placeholders(
            project_events,
            pattern=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z",
            prefix="TIMESTAMP",
            excluded=excluded_with_uuids,
        )
    )
    excluded_with_timestamps = excluded_with_uuids | set(placeholders)
    placeholders.update(
        _collect_regex_placeholders(
            project_events,
            pattern=r"\bmsg_[A-Za-z0-9]+\b",
            prefix="MESSAGE_ID",
            excluded=excluded_with_timestamps,
        )
    )
    return placeholders


def _normalize_project_event(
    event: dict[str, Any],
    replacements: dict[str, str],
) -> dict[str, Any]:
    normalized = _replace_all(event, replacements)
    return normalize_value(normalized, {})


def _project_transcript_message_events_before_latest_compaction(
    project_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    compact_indexes = [
        index
        for index, event in enumerate(project_events)
        if event.get("isCompactSummary") is True
    ]
    if not compact_indexes:
        return []
    latest_summary_index = compact_indexes[-1]
    return [
        event
        for event in project_events[:latest_summary_index]
        if event.get("type") in {"user", "assistant"}
    ]


def _latest_project_compact_boundary_event(
    project_events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    compact_indexes = [
        index
        for index, event in enumerate(project_events)
        if event.get("isCompactSummary") is True
    ]
    if not compact_indexes:
        return None
    latest_summary_index = compact_indexes[-1]
    for event in reversed(project_events[:latest_summary_index]):
        if event.get("type") == "system" and event.get("subtype") == "compact_boundary":
            return event
    return None


def _latest_project_local_command_events(
    project_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    compact_indexes = [
        index
        for index, event in enumerate(project_events)
        if event.get("isCompactSummary") is True
    ]
    if not compact_indexes:
        return []
    latest_summary_index = compact_indexes[-1]
    command_events: list[dict[str, Any]] = []
    for event in project_events[latest_summary_index + 1 :]:
        if event.get("type") != "user":
            break
        message = event.get("message")
        if not isinstance(message, dict):
            break
        content = message.get("content")
        if not isinstance(content, str):
            break
        if not (
            "<local-command-" in content
            or "<command-name>/compact</command-name>" in content
        ):
            break
        command_events.append(event)
    return command_events


def _latest_project_no_response_event(
    project_events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    compact_indexes = [
        index
        for index, event in enumerate(project_events)
        if event.get("isCompactSummary") is True
    ]
    if not compact_indexes:
        return None
    latest_summary_index = compact_indexes[-1]
    for event in project_events[latest_summary_index + 1 :]:
        if event.get("type") == "assistant" and "No response requested." in json.dumps(
            event.get("message"),
            ensure_ascii=False,
        ):
            return event
        if event.get("type") == "user":
            message = event.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str) and (
                "<local-command-" in content
                or "<command-name>/compact</command-name>" in content
            ):
                continue
        if event.get("type") in {"last-prompt", "ai-title", "mode", "queue-operation"}:
            continue
        break
    return None


def _collect_memory_dirs(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        found.update(
            match.group(0) for match in re.finditer(r"/[^`\n\"']+?/memory/", value)
        )
        return found
    if isinstance(value, list):
        for item in value:
            found.update(_collect_memory_dirs(item))
        return found
    if isinstance(value, dict):
        for item in value.values():
            found.update(_collect_memory_dirs(item))
    return found


def _find_latest_compact_request(
    requests: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not requests:
        return None
    for request in reversed(requests):
        body = request.get("body")
        if not isinstance(body, dict):
            continue
        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            continue
        last_message = messages[-1]
        if not isinstance(last_message, dict):
            continue
        content = last_message.get("content")
        if not isinstance(content, list):
            continue
        joined_text = "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        )
        if "<analysis>" in joined_text and "<summary>" in joined_text:
            return request
    return requests[-1]


def _extract_compact_prompt_text(compact_request: dict[str, Any] | None) -> str | None:
    if not isinstance(compact_request, dict):
        return None
    body = compact_request.get("body")
    if not isinstance(body, dict):
        return None
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    last_message = messages[-1]
    if not isinstance(last_message, dict):
        return None
    content = last_message.get("content")
    if not isinstance(content, list):
        return None
    for block in reversed(content):
        if not isinstance(block, dict):
            continue
        text = block.get("text")
        if isinstance(text, str) and "CRITICAL: Respond with TEXT ONLY." in text:
            return text
    return None


def _extract_compact_prompt_sections(prompt_text: str | None) -> list[str]:
    if not isinstance(prompt_text, str):
        return []
    sections: list[str] = []
    for line in prompt_text.splitlines():
        stripped = line.strip()
        if re.match(r"^\d+\.\s+\S", stripped):
            sections.append(stripped)
    return sections


def _build_fixture(
    *,
    case_name: str,
    workspace: Path,
    compact_stdout_events: list[dict[str, Any]],
    project_events: list[dict[str, Any]],
    session_file: Path | None,
    executed_steps: list[dict[str, Any]],
    proxy_requests: list[dict[str, Any]],
) -> dict[str, Any]:
    session_id = next(
        (
            event.get("session_id")
            for event in compact_stdout_events
            if isinstance(event.get("session_id"), str)
        ),
        None,
    )
    compact_boundary = next(
        (
            event
            for event in compact_stdout_events
            if event.get("type") == "system"
            and event.get("subtype") == "compact_boundary"
        ),
        None,
    )
    compact_statuses = [
        event
        for event in compact_stdout_events
        if event.get("type") == "system" and event.get("subtype") == "status"
    ]
    compact_summaries = _compact_summary_events(project_events)
    latest_summary = compact_summaries[-1] if compact_summaries else None
    latest_summary_text = None
    if isinstance(latest_summary, dict):
        message = latest_summary.get("message")
        if isinstance(message, dict):
            latest_summary_text = message.get("content")

    replacements = {str(workspace.resolve()): "<WORKSPACE>"}
    if session_file is not None:
        replacements[str(session_file)] = "<PROJECT_TRANSCRIPT>"
    if isinstance(session_id, str):
        replacements[session_id] = "<SESSION_ID>"
    for memory_dir in sorted(
        _collect_memory_dirs(executed_steps)
        | _collect_memory_dirs(project_events)
        | _collect_memory_dirs(proxy_requests)
    ):
        replacements[memory_dir] = "<MEMORY_DIR>"
    replacements.update(
        _collect_transcript_string_placeholders(
            project_events,
            excluded={session_id} if isinstance(session_id, str) else set(),
        )
    )

    normalized_steps = _replace_all(executed_steps, replacements)
    normalized_statuses = _replace_all(compact_statuses, replacements)
    normalized_boundary = _replace_all(compact_boundary, replacements)
    normalized_summary_text = _replace_all(latest_summary_text, replacements)
    normalized_project_pre_compaction_message_events = [
        _normalize_project_event(event, replacements)
        for event in _project_transcript_message_events_before_latest_compaction(
            project_events
        )
    ]
    project_compact_boundary = _latest_project_compact_boundary_event(project_events)
    normalized_project_compact_boundary = (
        _normalize_project_event(project_compact_boundary, replacements)
        if project_compact_boundary is not None
        else None
    )
    normalized_project_compact_summary = (
        _normalize_project_event(latest_summary, replacements)
        if isinstance(latest_summary, dict)
        else None
    )
    normalized_project_local_command_events = [
        _normalize_project_event(event, replacements)
        for event in _latest_project_local_command_events(project_events)
    ]
    latest_no_response_event = _latest_project_no_response_event(project_events)
    normalized_project_no_response_event = (
        _normalize_project_event(latest_no_response_event, replacements)
        if latest_no_response_event is not None
        else None
    )
    compact_request = _find_latest_compact_request(proxy_requests)
    normalized_compact_request = normalize_value(compact_request, replacements)
    compact_prompt_text = _extract_compact_prompt_text(normalized_compact_request)
    compact_system_text = None
    if isinstance(normalized_compact_request, dict):
        body = normalized_compact_request.get("body")
        if isinstance(body, dict):
            system = body.get("system")
            if (
                isinstance(system, list)
                and len(system) >= 3
                and isinstance(system[2], dict)
                and isinstance(system[2].get("text"), str)
            ):
                compact_system_text = system[2]["text"]

    summary_text = (
        normalized_summary_text if isinstance(normalized_summary_text, str) else ""
    )
    summary_sections: list[str] = []
    for line in summary_text.splitlines():
        stripped = line.strip()
        if re.match(r"^\d+\.\s", stripped):
            summary_sections.append(stripped)

    return {
        "case": case_name,
        "session_id": "<SESSION_ID>" if isinstance(session_id, str) else None,
        "step_count": len(executed_steps),
        "steps": normalized_steps,
        "compact_request": normalized_compact_request,
        "compact_request_message_count": (
            len(normalized_compact_request.get("body", {}).get("messages", []))
            if isinstance(normalized_compact_request, dict)
            else 0
        ),
        "compact_request_tool_count": (
            len(normalized_compact_request.get("body", {}).get("tools", []))
            if isinstance(normalized_compact_request, dict)
            else 0
        ),
        "compact_request_prompt_text": compact_prompt_text,
        "compact_request_prompt_sections": _extract_compact_prompt_sections(
            compact_prompt_text
        ),
        "compact_request_has_text_only_directive": (
            isinstance(compact_prompt_text, str)
            and "CRITICAL: Respond with TEXT ONLY." in compact_prompt_text
        ),
        "compact_request_has_no_tools_directive": (
            isinstance(compact_prompt_text, str)
            and "Do NOT use Read, Bash, Grep, Glob, Edit, Write, or ANY other tool."
            in compact_prompt_text
        ),
        "compact_request_has_resume_directive": (
            isinstance(compact_prompt_text, str)
            and "There may be additional summarization instructions provided in the included context."
            in compact_prompt_text
        ),
        "compact_request_system_prompt_text": compact_system_text,
        "compact_statuses": normalized_statuses,
        "compact_boundary": normalized_boundary,
        "compact_summary_count": len(compact_summaries),
        "compact_summary_text": normalized_summary_text,
        "compact_summary_sections": summary_sections,
        "summary_mentions_transcript_path": "<PROJECT_TRANSCRIPT>" in summary_text,
        "summary_has_resume_directive": "Resume directly" in summary_text,
        "summary_has_no_acknowledgement_directive": "do not acknowledge the summary"
        in summary_text,
        "summary_is_user_message": bool(
            latest_summary and latest_summary.get("type") == "user"
        ),
        "summary_is_visible_in_transcript_only": bool(
            latest_summary and latest_summary.get("isVisibleInTranscriptOnly") is True
        ),
        "summary_is_compact_summary": bool(
            latest_summary and latest_summary.get("isCompactSummary") is True
        ),
        "attachment_count": len(_attachment_events(project_events)),
        "has_local_command_caveat": any(
            "<local-command-caveat>" in json.dumps(event, ensure_ascii=True)
            for event in project_events
        ),
        "has_compact_command_message": any(
            "<command-name>/compact</command-name>"
            in json.dumps(event, ensure_ascii=True)
            for event in project_events
        ),
        "project_transcript_type_counts": _project_transcript_type_counts(
            project_events
        ),
        "project_transcript_pre_compaction_message_events": (
            normalized_project_pre_compaction_message_events
        ),
        "project_transcript_compact_boundary_event": (
            normalized_project_compact_boundary
        ),
        "project_transcript_compact_summary_event": normalized_project_compact_summary,
        "project_transcript_local_command_events": (
            normalized_project_local_command_events
        ),
        "project_transcript_no_response_event": normalized_project_no_response_event,
        "session_transcript_available": session_file is not None,
    }


def _run_case(case: CaseSpec, *, model: str, keep_raw: bool) -> dict[str, object]:
    run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{case.name}"
    if keep_raw:
        raw_dir = RAW_ROOT / run_id
        raw_dir.mkdir(parents=True, exist_ok=False)
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory(
            prefix=f"claude-compaction-{case.name}-"
        )
        raw_dir = Path(temp_context.name)

    try:
        workspace = raw_dir / "workspace"
        _prepare_workspace(workspace, case.prepare_workspace)

        proxy_log = raw_dir / "proxy.log"
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

            executed_steps: list[dict[str, Any]] = []
            compact_stdout_path: Path | None = None
            for index, step in enumerate(case.steps, start=1):
                stdout_path = raw_dir / f"step{index}.jsonl"
                stderr_path = raw_dir / f"step{index}.stderr.log"
                debug_path = raw_dir / f"step{index}.debug.log"
                command = [
                    "claude",
                    "-p",
                    "--verbose",
                    "--setting-sources",
                    "project",
                    "--settings",
                    settings,
                    "--debug-file",
                    str(debug_path),
                    "--model",
                    model,
                    "--tools",
                    "Read",
                    "--output-format",
                    "stream-json",
                ]
                if step.continue_session:
                    command.append("-c")
                command.append(step.prompt)

                proc = subprocess.run(
                    command,
                    cwd=str(workspace),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=180,
                    check=False,
                )
                stdout_path.write_text(proc.stdout, encoding="utf-8")
                stderr_path.write_text(proc.stderr, encoding="utf-8")
                events = _read_jsonl(stdout_path)
                executed_steps.append(
                    {
                        "index": index,
                        "prompt": step.prompt,
                        "continue_session": step.continue_session,
                        "stdout_events": events,
                        "stderr_text": proc.stderr,
                        "returncode": proc.returncode,
                    }
                )
                if step.prompt == "/compact":
                    compact_stdout_path = stdout_path

            if compact_stdout_path is None:
                raise RuntimeError("case did not include a /compact step")

            compact_stdout_events = _read_jsonl(compact_stdout_path)
            proxy_requests = parse_proxy_log(proxy_log)
            session_id = next(
                (
                    event.get("session_id")
                    for event in compact_stdout_events
                    if isinstance(event.get("session_id"), str)
                ),
                None,
            )
            try:
                session_path = (
                    _session_file_for_id(session_id)
                    if isinstance(session_id, str)
                    else None
                )
            except FileNotFoundError:
                session_path = None
            project_events = (
                _read_jsonl(session_path) if session_path is not None else []
            )
            fixture = _build_fixture(
                case_name=case.name,
                workspace=workspace,
                compact_stdout_events=compact_stdout_events,
                project_events=project_events,
                session_file=session_path,
                executed_steps=executed_steps,
                proxy_requests=proxy_requests,
            )
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
    args = parser.parse_args()

    _require_executable("claude")
    _require_executable("node")
    _require_executable("curl")

    selected = sorted(CASES) if args.case == "all" else [args.case]
    results = [
        _run_case(CASES[name], model=args.model, keep_raw=args.keep_raw)
        for name in selected
    ]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
