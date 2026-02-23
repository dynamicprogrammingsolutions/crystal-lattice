"""Application-layer integration tests for Ollama + JS (Node) tools.

These mirror the structure of `core/python/tests/test_application_layer_integration.py`
but load tools via the application plugin manager's `node_tool` source.

Scenario:
- Use OpenAI-compatible provider pointing at Ollama /v1
- Enable OpenAI tools extension
- Enable a JS tool plugin exposing `write_file` and `read_file`
- Ask the assistant to write then read a file

Assertions:
- Tool calls + tool results occur
- In streaming mode, tool outputs actually stream via `tool_partial` events
- With streaming disabled in tool config, only `tool_partial` end events appear
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest

from agent_app.application_future import AgentApplication
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")

REPO_TMP_DIR = Path(__file__).resolve().parents[3] / "tmp"
REPO_TMP_DIR.mkdir(parents=True, exist_ok=True)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_model() -> None:
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping node tools integration tests")
    if _which("node") is None:
        pytest.skip("node is not installed; skipping node tools integration tests")

    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {exc}")


def _make_app_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / "plugin_cache"),
        "plugin_policy": {
            "base_dir": str(_repo_root()),
        },
        "providers": {
            "ollama_tools": {
                "provider": "openai_compatible",
                "model": MODEL_TOOLS,
                "base_url": OPENAI_BASE_URL,
                "timeout": 180,
                "allowed_paths": [".", str(REPO_TMP_DIR)],
                "working_directory": str(REPO_TMP_DIR),
            }
        },
        "plugins": [
            "plugins.openai_provider.OpenAICompatibleProvider",
            "plugins.openai_tools_extension.OpenAIToolsExtension",
            "plugins.ollama_thinking_extension.OllamaThinkingExtension",
            {"node_tool": {"path": "plugins/js-fs-tools"}},
        ],
        "agents": {
            "default": {"provider": "ollama_tools"},
        },
    }
    path = tmp_path / "config_node_tools_ollama.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _collect_events(
    app: AgentApplication,
    session_id: str,
    *,
    stream: bool,
    overrides: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    ctx = app.load_session(session_id)
    assert ctx is not None
    core, base_config, session = ctx

    events: List[Dict[str, Any]] = []
    for ev in app.send_request(core, session, base_config, overrides or {}, stream=stream):
        events.append(ev)
    return events


def _extract_tool_names_from_results(events: List[Dict[str, Any]]) -> Set[str]:
    tool_result_events = [ev for ev in events if ev.get("type") == "tool_results"]
    tool_msgs: List[Dict[str, Any]] = []
    for ev in tool_result_events:
        tool_msgs.extend(ev.get("messages") or [])
    return {
        str((m.get("metadata") or {}).get("tool_name"))
        for m in tool_msgs
        if isinstance(m, dict) and isinstance((m.get("metadata") or {}).get("tool_name"), str)
    }


def _extract_tool_call_ids(events: List[Dict[str, Any]], tool_name: str) -> List[str]:
    ids: List[str] = []
    for ev in events:
        if ev.get("type") != "tool_calls":
            continue
        tool_calls = ev.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            continue
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            func = call.get("function") or {}
            name = None
            if isinstance(func, dict):
                name = func.get("name")
            if not isinstance(name, str) or name != tool_name:
                continue
            call_id = call.get("id") or call.get("tool_call_id")
            if isinstance(call_id, str) and call_id:
                ids.append(call_id)
    return ids


def _last_assistant_text(events: List[Dict[str, Any]]) -> str:
    finals = [ev for ev in events if ev.get("type") == "final"]
    if not finals:
        return ""
    last_final = finals[-1]
    messages = last_final.get("messages") or []
    assistants = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]
    if not assistants:
        return ""
    return str(assistants[-1].get("content") or "")


def _tool_partial_phases(events: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    phases: Dict[str, Set[str]] = {}
    for ev in events:
        if ev.get("type") != "tool_partial":
            continue
        tool_call_id = ev.get("tool_call_id")
        phase = ev.get("phase")
        if not isinstance(tool_call_id, str) or not tool_call_id:
            continue
        if not isinstance(phase, str) or not phase:
            continue
        phases.setdefault(tool_call_id, set()).add(phase)
    return phases


@pytest.mark.ollama
def test_application_layer_ollama_js_fs_tools_streaming_emits_tool_partials(
    tmp_path: Path,
    ensure_model: None,
) -> None:
    config_path = _make_app_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root))

    write_path = str(REPO_TMP_DIR / f"node_tools_streaming_{os.getpid()}_{os.urandom(4).hex()}.txt")
    desired = "HELLO_FROM_JS_STREAMING"

    core, _base_config, session = app.create_session("default")
    session_id = session.session_id

    system_message = (
        "You are a helpful assistant. You will be given tool results. "
        "After the tool run completes, reply with the file contents only."
    )
    user_message = "Wait for tools to run, then reply with the file contents only."

    tool_calls = [
        {
            "id": "call_write",
            "type": "function",
            "function": {
                "name": "write_file",
                # OpenAI-native tool calls expect string arguments.
                "arguments": json.dumps({"file_path": write_path, "content": desired}),
            },
        },
        {
            "id": "call_read",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": json.dumps({"file_path": write_path}),
            },
        },
    ]

    session = core.add_message(session, "system", system_message)
    session = core.add_message(session, "user", user_message)
    session = core.add_message(session, "assistant", "", metadata={"tool_calls": tool_calls})
    app.save_session(session)

    events = _collect_events(app, session_id, stream=True, overrides=None)

    assert any(ev.get("type") == "tool_calls" for ev in events)
    assert any(ev.get("type") == "tool_results" for ev in events)
    assert any(ev.get("type") == "tool_partial" for ev in events)
    assert any(ev.get("type") == "final" for ev in events)
    assert any(ev.get("type") == "request_completed" for ev in events)

    tool_names = _extract_tool_names_from_results(events)
    assert "write_file" in tool_names
    assert "read_file" in tool_names

    phases_by_call = _tool_partial_phases(events)
    assert phases_by_call, "expected tool_partial events keyed by tool_call_id"

    write_call_ids = _extract_tool_call_ids(events, "write_file")
    read_call_ids = _extract_tool_call_ids(events, "read_file")
    assert write_call_ids, "expected at least one write_file tool call"
    assert read_call_ids, "expected at least one read_file tool call"

    for tool_call_id in write_call_ids + read_call_ids:
        phases = phases_by_call.get(tool_call_id) or set()
        assert "end" in phases, f"expected end phase for {tool_call_id}"
        assert "start" in phases, f"expected start phase for {tool_call_id}"
        assert "stream" in phases, f"expected stream phase for {tool_call_id}"

    text = _last_assistant_text(events)
    assert desired in text

    try:
        os.unlink(write_path)
    except Exception:
        pass


@pytest.mark.ollama
def test_application_layer_ollama_js_fs_tools_streaming_disabled_has_no_stream_phases(
    tmp_path: Path,
    ensure_model: None,
) -> None:
    config_path = _make_app_config(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root))

    write_path = str(REPO_TMP_DIR / f"node_tools_no_stream_{os.getpid()}_{os.urandom(4).hex()}.txt")
    desired = "HELLO_FROM_JS_NO_STREAM"

    core, _base_config, session = app.create_session("default")
    session_id = session.session_id

    system_message = (
        "You are a helpful assistant. You will be given tool results. "
        "After the tool run completes, reply with the file contents only."
    )
    user_message = "Wait for tools to run, then reply with the file contents only."

    tool_calls = [
        {
            "id": "call_write",
            "type": "function",
            "function": {
                "name": "write_file",
                "arguments": json.dumps({"file_path": write_path, "content": desired}),
            },
        },
        {
            "id": "call_read",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": json.dumps({"file_path": write_path}),
            },
        },
    ]

    session = core.add_message(session, "system", system_message)
    session = core.add_message(session, "user", user_message)
    session = core.add_message(session, "assistant", "", metadata={"tool_calls": tool_calls})
    app.save_session(session)

    overrides = {"node_tool_stream_parts": False}
    events = _collect_events(app, session_id, stream=True, overrides=overrides)

    assert any(ev.get("type") == "tool_calls" for ev in events)
    assert any(ev.get("type") == "tool_results" for ev in events)
    assert any(ev.get("type") == "tool_partial" for ev in events)
    assert any(ev.get("type") == "final" for ev in events)

    # Even when tools don't stream, the application tool loop emits one
    # tool_partial(end) event per tool call in streaming mode.
    assert not any(
        ev.get("type") == "tool_partial" and ev.get("phase") in {"start", "stream"}
        for ev in events
    )

    tool_names = _extract_tool_names_from_results(events)
    assert "write_file" in tool_names
    assert "read_file" in tool_names

    text = _last_assistant_text(events)
    assert desired in text

    try:
        os.unlink(write_path)
    except Exception:
        pass
