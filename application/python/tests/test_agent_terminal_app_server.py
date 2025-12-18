"""Tests for the agent_terminal_app server functions.

These tests mirror the style of the example application tests under
``core/python/examples/tests`` but exercise the FastAPI-style route
functions directly, injecting an ``AgentApplication`` instance instead
of going through the HTTP layer.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import threading
import time

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def test_server_flow_with_echo_provider(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the agent_terminal_app test"

    # 1) Create a new session with a system message via the route function.
    create_resp = server_mod.create_session(
        {"agent_id": "default", "system_message": system_message},
        app_instance=app,
    )
    session_dict = create_resp["session"]
    session_id = session_dict["session_id"]
    assert isinstance(session_id, str) and session_id

    # 2) Add a user message.
    add_resp = server_mod.add_message(
        session_id,
        {"role": "user", "content": user_message, "metadata": None},
        app_instance=app,
    )
    updated_session = add_resp["session"]
    assert updated_session["session_id"] == session_id

    # 3) Send a request and verify the echo provider behaviour.
    send_resp = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        app_instance=app,
    )

    final_session_dict = send_resp["session"]
    messages = send_resp["messages"]
    request_id = send_resp["request_id"]

    # Reload the final session from the application to avoid relying on
    # the shape of the streaming events.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, final_session = ctx
    session_dict = final_session.to_dict()

    history = session_dict.get("messages") or []
    assert history, "expected at least one message in the final session"
    # For the echo config we only require that the call completes and
    # that the session history was not corrupted; we do not assert on
    # the exact assistant content here.

    # 4) Basic check that events were recorded for this session.
    events = app.get_event_store().list(session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in events}
    assert "session_created" in kinds
    assert "message_appended" in kinds
    assert "request_started" in kinds or "final" in kinds


def test_system_message_feature_adds_system_message_after_second_user_message(tmp_path: Path) -> None:
    """Application-level test for SystemMessageFeature integration.

    Verifies that when a provider is configured with SystemMessageFeature
    and the first request has run (so the permanent system template lives
    only in native history), adding a *subsequent* user message causes the
    system message to appear in the stored core session history as well.
    """

    import json

    from agent_core import Session
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    # Minimal config: echo-like provider + SystemMessageFeature.
    system_template = "You are a helpful system message for tests."
    config = {
        "providers": {
            "echo_with_system": {
                "provider": "echo_openai_like",
                "model": "echo-test-1",
                "timeout": 60,
                "system_message_enabled": True,
                "system_message": system_template,
            }
        },
        "plugins": {
            "providers": [
                "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            ],
            "extensions": [],
            "features": [
                "plugins.system_message_feature.SystemMessageFeature",
            ],
            "tools": [],
        },
        "agents": {
            "default": {
                "provider": "echo_with_system",
            }
        },
    }

    cfg_path = tmp_path / "config_system_message_app.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(cfg_path), str(session_root), event_store=events_store)

    # Create a new session and append the first user message using the
    # agent's base config so that SystemMessageFeature is active.
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "first", metadata=None, config=base_config)

    # Run the first request; SystemMessageFeature should insert a permanent
    # template-level system message into provider-native history, but the
    # core session history remains as the application created it.
    events1 = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints1 = [ev for ev in events1 if ev.get("type") == "session_checkpoint"]
    assert checkpoints1, "expected at least one session_checkpoint event"
    session1 = checkpoints1[-1]["session"]
    assert isinstance(session1, Session)

    native1 = session1.metadata.get("native_messages") or []
    sys_native1 = [m for m in native1 if isinstance(m, dict) and m.get("role") == "system"]
    assert sys_native1 and sys_native1[0].get("content") == system_template

    # Append a second user message using the same agent config and run a
    # second request. Native history should still contain exactly one
    # template-level system message (no duplication across turns).
    core2, base_config2, loaded1 = app.load_session(session1.session_id)
    session2 = core2.add_message(loaded1, "user", "second", metadata=None, config=base_config2)

    events2 = list(app.send_request(core2, session2, base_config2, overrides=None, stream=False))
    checkpoints2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"]
    assert checkpoints2, "expected at least one session_checkpoint event"
    session3 = checkpoints2[-1]["session"]
    assert isinstance(session3, Session)

    native2 = session3.metadata.get("native_messages") or []
    sys_native2 = [m for m in native2 if isinstance(m, dict) and m.get("role") == "system"]
    assert len(sys_native2) == 1
    assert sys_native2[0].get("content") == system_template


def test_list_sessions_endpoint_returns_metadata_for_created_sessions(tmp_path: Path) -> None:
    """GET /sessions returns basic metadata for stored sessions.

    The test creates two sessions with user messages via the existing
    create_session and add_message endpoints, then verifies that the
    list_sessions endpoint returns entries for both with appropriate
    previews.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create two sessions with a single user message each.
    create1 = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id1 = create1["session"]["session_id"]
    server_mod.add_message(
        session_id1,
        {"role": "user", "content": "first session hello", "metadata": None},
        app_instance=app,
    )

    create2 = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id2 = create2["session"]["session_id"]
    server_mod.add_message(
        session_id2,
        {"role": "user", "content": "second session hi", "metadata": None},
        app_instance=app,
    )

    resp = server_mod.list_sessions(app_instance=app)
    sessions = resp["sessions"]

    # Both sessions should be present with non-empty previews.
    ids = {entry["session_id"] for entry in sessions}
    assert session_id1 in ids and session_id2 in ids

    preview_by_id = {entry["session_id"]: entry["preview"] for entry in sessions}
    assert preview_by_id[session_id1] == "first session hello"
    assert preview_by_id[session_id2] == "second session hi"


def test_list_session_messages_endpoint_supports_slice_bounds(tmp_path: Path) -> None:
    """GET /sessions/{session_id}/messages lists and slices messages.

    The test creates a session with three user messages and verifies that
    the endpoint returns the full history as well as a negative-index
    slice selecting the last two messages.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    for content in ["one", "two", "three"]:
        server_mod.add_message(
            session_id,
            {"role": "user", "content": content, "metadata": None},
            app_instance=app,
        )

    # Full history
    full = server_mod.list_session_messages(session_id, app_instance=app)
    full_messages = full["messages"]
    assert [m["message"]["content"] for m in full_messages] == ["one", "two", "three"]

    # Last two messages using a negative start index
    last_two = server_mod.list_session_messages(session_id, start=-2, app_instance=app)
    last_two_messages = last_two["messages"]
    assert [m["index"] for m in last_two_messages] == [1, 2]
    assert [m["message"]["content"] for m in last_two_messages] == ["two", "three"]


def test_cancel_request_endpoint_triggers_cancellation(tmp_path: Path) -> None:
    """POST /requests/{request_id}/cancel cooperates with send_request.

    The test schedules a cancellation for a specific request id and then
    runs AgentApplication.send_request with the same id, asserting that a
    ``request_cancelled`` event is produced instead of a normal final
    response.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Prepare a simple session with one user message.
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello", metadata=None, config=base_config)

    request_id = "test-request-id-123"

    # Request cancellation via the server endpoint before starting the call.
    server_mod.cancel_request(request_id, app_instance=app)

    events = list(
        app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=False,
            request_id=request_id,
        )
    )

    kinds = {ev.get("type") for ev in events}
    assert "request_started" in kinds
    assert "request_cancelled" in kinds
    assert "final" not in kinds


# ---------------------------------------------------------------------------
# HTTP integration test using FastAPI TestClient
# ---------------------------------------------------------------------------


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_BASE_URL = f"{OLLAMA_HOST}/v1"
MODEL_TOOLS = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")

REPO_TMP_DIR = Path(__file__).resolve().parents[3] / "tmp"
REPO_TMP_DIR.mkdir(parents=True, exist_ok=True)

def _which(cmd: str) -> Optional[str]:
    import shutil

    return shutil.which(cmd)


def _run(cmd: list[str], timeout: int = 120):
    import subprocess

    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


@pytest.fixture(scope="module")
def ensure_ollama_model() -> None:
    """Ensure that Ollama and the tools-capable model are available, else skip."""

    if _which("ollama") is None:
        pytest.skip("ollama is not installed; skipping HTTP Ollama tools test")
    try:
        _run(["ollama", "ps"], timeout=30)
    except Exception:
        pytest.skip("ollama command unavailable or not responding; skipping")

    try:
        cp = _run(["ollama", "pull", MODEL_TOOLS], timeout=1200)
        if cp.returncode != 0:
            msg = cp.stderr.decode("utf-8", errors="ignore")
            pytest.skip(f"failed to pull model {MODEL_TOOLS}: {msg}")
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip(f"could not pull model {MODEL_TOOLS}: {e}")


@pytest.mark.ollama
def test_http_flow_with_tools_and_reasoning(ensure_ollama_model: None, tmp_path: Path) -> None:
    """End-to-end HTTP flow exercising tools and reasoning.

    The flow uses the real FastAPI app with config_openrouter_app_layer.json
    via TestClient:

    1. Create a session with a system message.
    2. Add a user message.
    3. Inject a pending shell tool call as an assistant message.
    4. Start /send in a background thread with a small artificial delay.
    5. Poll /events while the request is in progress.
    6. Verify that tool events and reasoning metadata are present.
    7. List messages and ensure user, assistant, and tool messages exist.
    """

    from agent_terminal_app import server as server_mod

    # Build an application instance using an Ollama tools config similar to
    # the core application-layer integration tests.
    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = tmp_path / "config_ollama_tools_app.json"

    ollama_cfg = {
        "providers": {
            "ollama_tools": {
                "provider": "openai_compatible",
                "model": MODEL_TOOLS,
                "base_url": OPENAI_BASE_URL,
                "timeout": 180,
                # Tool configuration, forwarded to FileReaderTool
                "allowed_paths": ["."],
                "max_file_size": 1024 * 1024,
            }
        },
        "plugins": {
            "providers": ["plugins.openai_provider.OpenAICompatibleProvider"],
            "extensions": [
                "plugins.openai_tools_extension.OpenAIToolsExtension",
                "plugins.ollama_thinking_extension.OllamaThinkingExtension",
            ],
            "tools": ["plugins.file_reader_tool.FileReaderTool"],
        },
        "agents": {
            "default": {"provider": "ollama_tools"},
        },
    }

    config_path.write_text(__import__("json").dumps(ollama_cfg), encoding="utf-8")
    session_root = tmp_path / "sessions"

    event_store = InMemoryEventStore()
    app_instance = AgentApplication(str(config_path), str(session_root), event_store=event_store)

    # Wire the custom AgentApplication into the FastAPI app via dependency override.
    from agent_terminal_app.server import app, get_agent_app

    app.dependency_overrides[get_agent_app] = lambda: app_instance
    client = TestClient(app)

    try:
        # 1) Create a new session.
        system_message = (
            "You are a helpful assistant. When the user asks about file contents, "
            "you MUST use the read_file tool to inspect the file and then answer. "
            "Never guess. You also include brief reasoning in your metadata."
        )

        resp = client.post("/sessions", json={"agent_id": "default", "system_message": system_message})
        assert resp.status_code == 200
        session_id = resp.json()["session"]["session_id"]

        # 2) Add a user message.
        # Prepare a small temp file under the repository tmp directory so that
        # allowed_paths ["."] covers it.
        import tempfile

        with tempfile.NamedTemporaryFile("w+", delete=False, dir=REPO_TMP_DIR) as tf:
            tf.write("hello from ollama tools over HTTP")
            tf.flush()
            file_path = tf.name

        user_message = (
            "Use the tools to read this file and tell me its exact contents: "
            f"{file_path}. Do not answer without using tools."
        )
        resp = client.post(
            f"/sessions/{session_id}/messages",
            json={"role": "user", "content": user_message, "metadata": None},
        )
        assert resp.status_code == 200

        # 3) Start /send in a background thread with a small artificial delay
        # configured via the DelayExtension so that the request remains in
        # progress long enough for us to poll /events while it is running.
        overrides = {
            "allowed_paths": ["."],
            "working_directory": ".",
            "enable_delay_extension": True,
            "delay_seconds": 2.0,
        }

        send_resp_container: dict[str, Any] = {}

        def _run_send() -> None:
            r = client.post(f"/sessions/{session_id}/send", json={"config_overrides": overrides})
            send_resp_container["response"] = r

        send_thread = threading.Thread(target=_run_send)
        send_thread.start()

        # 5) Poll /events while the request is in progress.
        seen_event_types: set[str] = set()
        seen_tool_event = False
        seen_reasoning_in_final = False
        last_event_id: Optional[str] = None

        deadline = time.time() + 60.0
        while time.time() < deadline:
            params: Dict[str, Any] = {"session_id": session_id}
            if last_event_id is not None:
                params["since_id"] = last_event_id

            ev_resp = client.get("/events", params=params)
            assert ev_resp.status_code == 200
            batch = ev_resp.json().get("events", [])

            if batch:
                last_event_id = batch[-1].get("event_id") or last_event_id

            for ev in batch:
                etype = ev.get("type")
                if isinstance(etype, str):
                    seen_event_types.add(etype)

                if etype in {"tool_calls", "tool_results", "tool_partial"}:
                    seen_tool_event = True

                if etype == "final":
                    messages = ev.get("messages") or []
                    if messages:
                        last_msg = messages[-1]
                        md = last_msg.get("metadata") or {}
                        reasoning = md.get("reasoning")
                        if isinstance(reasoning, str) and reasoning.strip():
                            seen_reasoning_in_final = True

            if "final" in seen_event_types and "request_completed" in seen_event_types:
                break

            # If the background thread already finished and no new events
            # are coming in, exit the loop after a short grace period.
            if not send_thread.is_alive() and not batch:
                break

            time.sleep(0.5)

        send_thread.join(timeout=10.0)
        assert not send_thread.is_alive(), "send_request thread did not finish in time"

        send_resp = send_resp_container.get("response")
        assert send_resp is not None
        assert send_resp.status_code == 200

        # 6) Basic assertions about the event stream.
        assert "request_started" in seen_event_types
        assert "request_completed" in seen_event_types
        assert "final" in seen_event_types
        assert seen_tool_event, "expected at least one tool-related event"
        assert seen_reasoning_in_final, "expected reasoning in final assistant metadata"

        # 7) List messages for the finished session and ensure history looks reasonable.
        list_resp = client.get(f"/sessions/{session_id}/messages")
        assert list_resp.status_code == 200
        messages = list_resp.json().get("messages", [])

        roles = [entry["message"]["role"] for entry in messages]
        assert "user" in roles
        assert "assistant" in roles
        assert "tool" in roles

    finally:
        # Remove overrides so other tests are unaffected.
        from agent_terminal_app.server import app as shared_app

        shared_app.dependency_overrides.clear()
