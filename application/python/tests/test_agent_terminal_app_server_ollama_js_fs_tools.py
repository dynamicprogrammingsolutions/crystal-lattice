"""Application-level regression test for Node (JS/TS) tool plugins.

This test covers the user-facing surface area where Node tools must appear:

- Terminal: plugin listing (used by `/help config` and `/plugins`)
- HTTP server: session plugins endpoint (used by desktop/mobile clients)

It also exercises tool execution end-to-end by injecting pending tool calls
into the session history and running the server send loop.

The test is marked `@pytest.mark.ollama` and skips when Ollama/Node
prerequisites are not available.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_terminal_app import server as server_mod
from agent_terminal_app.terminal_app import TerminalApplication


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _run(cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


@pytest.fixture(scope="module")
def ensure_node_ollama_and_model() -> None:
    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping JS tool integration test")
    if _which("node") is None:
        pytest.skip("node is not installed; skipping JS tool integration test")

    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    config_path = (
        Path(server_mod.__file__).resolve().parent / "config_ollama_js_fs_tools.json"
    )
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    model = ((cfg.get("providers") or {}).get("ollama_tools") or {}).get("model")
    model_name = model if isinstance(model, str) and model.strip() else "qwen3:0.6b"

    try:
        cp = _run(["ollama", "pull", model_name], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {model_name}: {msg}")
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"could not pull model {model_name}: {exc}")


def _tool_results(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for ev in events:
        if ev.get("type") != "tool_results":
            continue
        msgs = ev.get("messages")
        if isinstance(msgs, list):
            results.extend([m for m in msgs if isinstance(m, dict)])
    return results


@pytest.mark.ollama
def test_server_and_terminal_list_js_fs_tools_and_can_execute(
    tmp_path: Path,
    ensure_node_ollama_and_model: None,
) -> None:
    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_ollama_js_fs_tools.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)
    term_app = TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=app,
    )

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]
    term_app.switch_session(session_id)

    terminal_plugins = term_app.list_plugins_for_session()
    assert any(p.get("id") == "js_fs_tools" for p in terminal_plugins)

    server_plugins = server_mod.get_session_plugins(session_id, app_instance=app)[
        "plugins"
    ]
    assert any(p.get("id") == "js_fs_tools" for p in server_plugins)

    desired = "HELLO_FROM_JS_FS_TOOLS"
    file_path = tmp_path / "js_fs_tools.txt"

    tool_calls = [
        {
            "id": "call_write",
            "type": "function",
            "function": {
                "name": "write_file",
                "arguments": json.dumps(
                    {"file_path": str(file_path), "content": desired}
                ),
            },
        },
        {
            "id": "call_read",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": json.dumps({"file_path": str(file_path)}),
            },
        },
    ]

    system_message = (
        "You are a helpful assistant. You will be given tool results. "
        "After tools finish, reply with the file contents only."
    )

    server_mod.add_message(
        session_id,
        {"role": "system", "content": system_message, "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "Run the pending tool calls.", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {
            "role": "assistant",
            "content": "Running tools.",
            "metadata": {"tool_calls": tool_calls},
        },
        app_instance=app,
    )

    overrides = {
        "allowed_paths": [str(tmp_path)],
        "working_directory": str(tmp_path),
    }
    server_mod._run_send_request_background(app, session_id, overrides)

    stored_events = app.get_event_store().list(session_id=session_id, limit=5000)
    kinds = {ev.get("type") for ev in stored_events}
    assert "tool_calls" in kinds
    assert "tool_results" in kinds
    assert "final" in kinds
    assert "request_completed" in kinds

    tool_msgs = _tool_results(stored_events)
    tool_names = {
        (m.get("metadata") or {}).get("tool_name")
        for m in tool_msgs
        if isinstance(m.get("metadata"), dict)
    }
    assert "write_file" in tool_names
    assert "read_file" in tool_names

    read_texts = [
        m.get("content")
        for m in tool_msgs
        if (m.get("metadata") or {}).get("tool_name") == "read_file"
    ]
    assert any(isinstance(text, str) and desired in text for text in read_texts)

    assert file_path.read_text(encoding="utf-8") == desired
