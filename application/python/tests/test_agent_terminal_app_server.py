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

    # 3) Send a request asynchronously and verify echo provider behaviour.
    send_resp = server_mod.send_request(
        session_id,
        {"config_overrides": {}},
        app_instance=app,
    )

    # The /send endpoint now returns an immediate acknowledgement with
    # no session/messages/request_id payload.
    assert send_resp == {}

    # Wait for the background worker to finish and record a final event.
    deadline = time.time() + 30.0
    final_kinds: set[str] = set()
    while time.time() < deadline:
        events = app.get_event_store().list(session_id=session_id, limit=100)
        final_kinds = {ev.get("type") for ev in events}
        if "final" in final_kinds or "request_completed" in final_kinds:
            break
        time.sleep(0.1)

    assert ("final" in final_kinds) or ("request_completed" in final_kinds), (
        "timed out waiting for final/request_completed events",
    )

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


def test_get_session_ui_schema_includes_ui_types(tmp_path: Path) -> None:
    """GET /sessions/{session_id}/ui-schema exposes full UI entries.

    Uses the default config so that provider, extension, and feature
    plugins contribute both configuration and footer / status metadata
    to the schema.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "default_config.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    resp = server_mod.get_session_ui_schema(session_id, app_instance=app)
    elements = resp.get("elements")
    assert isinstance(elements, list)

    ui_types = {el.get("ui_type") for el in elements if isinstance(el, dict)}

    # Configuration entries (either explicit or defaulted) should be present.
    assert "config" in {t or "config" for t in ui_types}

    # The default config registers extensions that contribute message_footer
    # and status_bar elements (for example, timestamp_extension and
    # openrouter_usage_extension). We only require that such entries are
    # surfaced, not the exact count.
    assert "message_footer" in ui_types
    assert "status_bar" in ui_types


def test_get_session_config_schema_exposes_known_keys(tmp_path: Path) -> None:
  """GET /sessions/{id}/config/schema returns flattened config entries.

  Uses the OpenRouter application-layer config so that plugin config
  schema entries are present and can be queried by key.
  """

  from agent_terminal_app import server as server_mod

  base_dir = Path(server_mod.__file__).resolve().parent
  config_path = base_dir / "config_openrouter_app_layer.json"
  session_root = tmp_path / "sessions"

  events = InMemoryEventStore()
  app = AgentApplication(str(config_path), str(session_root), event_store=events)

  create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
  session_id = create_resp["session"]["session_id"]

  resp = server_mod.get_session_config_schema(session_id, app_instance=app)
  schema = resp.get("schema")
  assert isinstance(schema, list)

  keys = {entry.get("key") for entry in schema if isinstance(entry, dict)}
  # openrouter_reasoning_extension contributes these keys to the config schema.
  assert "reasoning_effort" in keys
  assert "enable_reasoning" in keys


def test_get_session_config_schema_exposes_known_keys(tmp_path: Path) -> None:
  """GET /sessions/{id}/config/schema exposes plugin config entries.

  Uses the OpenRouter application-layer config so that real plugin
  config schema entries are present.
  """

  from agent_terminal_app import server as server_mod

  base_dir = Path(server_mod.__file__).resolve().parent
  config_path = base_dir / "config_openrouter_app_layer.json"
  session_root = tmp_path / "sessions"

  events = InMemoryEventStore()
  app = AgentApplication(str(config_path), str(session_root), event_store=events)

  create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
  session_id = create_resp["session"]["session_id"]

  resp = server_mod.get_session_config_schema(session_id, app_instance=app)
  schema = resp.get("schema")
  assert isinstance(schema, list)

  keys = {entry.get("key") for entry in schema if isinstance(entry, dict)}
  assert "reasoning_effort" in keys
  assert "enable_reasoning" in keys


def test_get_session_base_config_returns_mapping(tmp_path: Path) -> None:
  """GET /sessions/{id}/config/base returns a config mapping."""

  from agent_terminal_app import server as server_mod

  base_dir = Path(server_mod.__file__).resolve().parent
  config_path = base_dir / "config_openrouter_app_layer.json"
  session_root = tmp_path / "sessions"

  events = InMemoryEventStore()
  app = AgentApplication(str(config_path), str(session_root), event_store=events)

  create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
  session_id = create_resp["session"]["session_id"]

  resp = server_mod.get_session_base_config(session_id, app_instance=app)
  cfg = resp.get("config")
  assert isinstance(cfg, dict)


def test_run_send_request_background_helper_sends_and_persists(tmp_path: Path) -> None:
    """Internal helper _run_send_request_background mirrors /send behaviour.

    This test calls the helper directly to ensure that it drives the
    send_request flow to completion and persists the final session.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the _run_send_request_background test"

    create_resp = server_mod.create_session(
        {"agent_id": "default", "system_message": system_message},
        app_instance=app,
    )
    session_dict = create_resp["session"]
    session_id = session_dict["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": user_message, "metadata": None},
        app_instance=app,
    )

    # Run the helper synchronously; it should process the request to
    # completion and save the final session.
    server_mod._run_send_request_background(app, session_id, {})

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, final_session = ctx
    session_dict = final_session.to_dict()
    history = session_dict.get("messages") or []
    assert history, "expected at least one message in the final session"

    evs = app.get_event_store().list(session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in evs}
    assert "request_started" in kinds
    assert "final" in kinds or "request_completed" in kinds

    # A checkpoint marker should also have been recorded for this session.
    checkpoint_events = [ev for ev in evs if ev.get("type") == "checkpoint"]
    assert checkpoint_events, "expected at least one checkpoint event for the session"


def test_session_overrides_get_and_patch_round_trip(tmp_path: Path) -> None:
    """GET/PATCH /sessions/{id}/overrides round-trips a single key.

    Verifies that overrides are persisted on the session metadata and
    exposed again via the GET endpoint.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Initially there should be no overrides.
    get_resp = server_mod.get_session_overrides(session_id, app_instance=app)
    assert get_resp == {"overrides": {}}

    # Patch a single override and verify it is persisted.
    server_mod.patch_session_overrides(
        session_id,
        {"key": "reasoning_effort", "value": "high"},
        app_instance=app,
    )

    get_resp2 = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = get_resp2.get("overrides") or {}
    assert overrides.get("reasoning_effort") == "high"

    # Confirm that the session metadata was updated on disk.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    md = session.metadata or {}
    stored = md.get("overrides") or {}
    assert stored.get("reasoning_effort") == "high"


def test_session_overrides_patch_bulk_merges_with_existing(tmp_path: Path) -> None:
    """PATCH /sessions/{id}/overrides merges bulk values with existing.

    Starts with an override for one key, then bulk-updates another and
    verifies that both remain in the mapping.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Seed a single-key override.
    server_mod.patch_session_overrides(
        session_id,
        {"key": "enable_reasoning", "value": True},
        app_instance=app,
    )

    # Bulk update another key.
    server_mod.patch_session_overrides(
        session_id,
        {"values": {"reasoning_effort": "medium"}},
        app_instance=app,
    )

    get_resp = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = get_resp.get("overrides") or {}
    assert overrides.get("enable_reasoning") is True
    assert overrides.get("reasoning_effort") == "medium"


def test_delete_session_override_removes_key_and_preserves_others(tmp_path: Path) -> None:
    """DELETE /sessions/{id}/overrides/{key} removes a single override key."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Seed two overrides.
    server_mod.patch_session_overrides(
        session_id,
        {"values": {"enable_reasoning": True, "reasoning_effort": "high"}},
        app_instance=app,
    )

    # Delete only reasoning_effort.
    server_mod.delete_session_override(session_id, "reasoning_effort", app_instance=app)

    resp = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = resp.get("overrides") or {}
    assert overrides.get("enable_reasoning") is True
    assert "reasoning_effort" not in overrides


def test_delete_session_override_is_idempotent_for_missing_key(tmp_path: Path) -> None:
    """Deleting a non-existent override key is a no-op."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # No overrides set; deleting a key should be a no-op.
    before = server_mod.get_session_overrides(session_id, app_instance=app)
    server_mod.delete_session_override(session_id, "nonexistent", app_instance=app)
    after = server_mod.get_session_overrides(session_id, app_instance=app)
    assert before == after


def test_get_session_base_config_returns_mapping(tmp_path: Path) -> None:
    """GET /sessions/{id}/config/base exposes base agent config as mapping."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    resp = server_mod.get_session_base_config(session_id, app_instance=app)
    cfg = resp.get("config")
    assert isinstance(cfg, dict)


def test_delete_session_override_removes_key_and_preserves_others(tmp_path: Path) -> None:
    """DELETE /sessions/{id}/overrides/{key} drops only the requested key."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.patch_session_overrides(
        session_id,
        {"values": {"enable_reasoning": True, "reasoning_effort": "high"}},
        app_instance=app,
    )

    server_mod.delete_session_override(session_id, "reasoning_effort", app_instance=app)

    get_resp = server_mod.get_session_overrides(session_id, app_instance=app)
    overrides = get_resp.get("overrides") or {}
    assert overrides.get("enable_reasoning") is True
    assert "reasoning_effort" not in overrides


def test_delete_session_override_is_idempotent_when_key_missing(tmp_path: Path) -> None:
    """DELETE /sessions/{id}/overrides/{key} is idempotent for missing keys."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # No overrides set; deleting a non-existent key should not fail.
    resp = server_mod.delete_session_override(session_id, "nonexistent", app_instance=app)
    assert isinstance(resp.get("session"), dict)


def test_checkpoint_cursor_after_final_event(tmp_path: Path) -> None:
    """After a request, cursor_event_id is after the final event.

    The test runs a non-streaming request to completion via the
    background helper and verifies that the checkpoint marker recorded
    for the session has a higher ``event_id`` than the last ``final``
    event and that ``cursor_event_id`` from the messages endpoint
    matches that marker.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello from final", "metadata": None},
        app_instance=app,
    )

    # Run the helper synchronously to drive the non-streaming request.
    server_mod._run_send_request_background(app, session_id, {})

    evs = app.get_event_store().list(session_id=session_id, limit=200)
    final_events = [ev for ev in evs if ev.get("type") == "final"]
    checkpoint_events = [ev for ev in evs if ev.get("type") == "checkpoint"]

    assert final_events, "expected at least one final event for the session"
    assert checkpoint_events, "expected at least one checkpoint event for the session"

    last_final = final_events[-1]
    last_checkpoint = checkpoint_events[-1]

    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except Exception:
            return -1

    assert _to_int(last_checkpoint.get("event_id")) > _to_int(
        last_final.get("event_id")
    )

    resp = server_mod.list_session_messages(session_id, app_instance=app)
    assert resp["cursor_event_id"] == last_checkpoint.get("event_id")


def test_run_send_request_background_merges_session_and_http_overrides(tmp_path: Path) -> None:
    """Background send merges metadata overrides with HTTP overrides.

    The per-session overrides stored in session.metadata["overrides"]
    must be merged with any config_overrides passed via HTTP, with the
    HTTP-provided values taking precedence on conflicts.
    """

    from agent_terminal_app import server as server_mod
    from agent_core import Session

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Attach some per-session overrides directly to the stored session.
    ctx = app.load_session(session_id)
    assert ctx is not None
    core, base_config, session = ctx
    existing_md = session.metadata or {}
    new_md = {
        **existing_md,
        "overrides": {"foo": "session", "both": "session"},
    }
    session_with_overrides = Session(
        session_id=session.session_id,
        messages=session.messages,
        metadata=new_md,
    )
    app.save_session(session_with_overrides)

    captured: dict[str, Any] = {}

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        stream: bool = True,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        captured["overrides"] = overrides_arg
        return []

    # Monkeypatch AgentApplication.send_request.
    app.send_request = _fake_send_request  # type: ignore[assignment]

    # HTTP-provided overrides should be merged on top.
    http_overrides = {"bar": "http", "both": "http"}
    server_mod._run_send_request_background(app, session_id, http_overrides)

    merged = captured.get("overrides") or {}
    assert merged == {"foo": "session", "both": "http", "bar": "http"}


def test_run_send_request_background_uses_session_overrides_when_http_empty(tmp_path: Path) -> None:
    """Background send uses only session overrides when HTTP none provided."""

    from agent_terminal_app import server as server_mod
    from agent_core import Session

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    ctx = app.load_session(session_id)
    assert ctx is not None
    core, base_config, session = ctx
    existing_md = session.metadata or {}
    new_md = {
        **existing_md,
        "overrides": {"alpha": 1, "beta": 2},
    }
    session_with_overrides = Session(
        session_id=session.session_id,
        messages=session.messages,
        metadata=new_md,
    )
    app.save_session(session_with_overrides)

    captured: dict[str, Any] = {}

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        stream: bool = True,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        captured["overrides"] = overrides_arg
        return []

    app.send_request = _fake_send_request  # type: ignore[assignment]

    server_mod._run_send_request_background(app, session_id, {})

    merged = captured.get("overrides") or {}
    assert merged == {"alpha": 1, "beta": 2}


def test_list_session_messages_includes_cursor_event_id_after_request(tmp_path: Path) -> None:
    """GET /sessions/{session_id}/messages returns cursor_event_id.

    The test runs a request to completion using the background helper
    and then verifies that the messages endpoint exposes the
    event_id of the latest checkpoint marker for that session.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_dict = create_resp["session"]
    session_id = session_dict["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello", "metadata": None},
        app_instance=app,
    )

    server_mod._run_send_request_background(app, session_id, {})

    evs = app.get_event_store().list(session_id=session_id, limit=100)
    checkpoint_events = [ev for ev in evs if ev.get("type") == "checkpoint"]
    assert checkpoint_events, "expected at least one checkpoint event for the session"
    last_id = checkpoint_events[-1].get("event_id")
    assert isinstance(last_id, str) and last_id

    resp = server_mod.list_session_messages(session_id, app_instance=app)
    assert resp["cursor_event_id"] == last_id


def test_events_endpoint_bootstrap_returns_latest_event_id(tmp_path: Path) -> None:
    """GET /events with no filters returns only latest_event_id.

    When called without since_id, session_id, or request_id, the
    events endpoint should not replay the entire history. Instead it
    returns an empty events list plus the latest event_id so that
    clients can start polling from "now".
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Publish a couple of events for distinct sessions.
    s1_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    s1 = s1_resp["session"]["session_id"]
    server_mod.add_message(
        s1,
        {"role": "user", "content": "one", "metadata": None},
        app_instance=app,
    )

    s2_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    s2 = s2_resp["session"]["session_id"]
    server_mod.add_message(
        s2,
        {"role": "user", "content": "two", "metadata": None},
        app_instance=app,
    )

    # Directly call the route function with no filters.
    resp = server_mod.list_events(app_instance=app)
    events_payload = resp.get("events")
    latest_event_id = resp.get("latest_event_id")

    assert isinstance(events_payload, list) and events_payload == []
    # The latest event id should correspond to the last event published
    # in the store.
    assert isinstance(latest_event_id, str) and latest_event_id


def test_events_endpoint_uses_session_cursor_as_default_since_id(tmp_path: Path) -> None:
    """GET /events?session_id=... uses cursor when since_id omitted.

    After a checkpoint is recorded for a session, polling /events for
    that session without an explicit since_id should return only
    events after the cursor.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Add a user message and run a request to completion so that a
    # checkpoint is recorded for this session.
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "before", "metadata": None},
        app_instance=app,
    )
    server_mod._run_send_request_background(app, session_id, {})

    # Capture the cursor and then publish an additional synthetic event
    # for the same session after the checkpoint.
    cursor_id = app.get_session_cursor_event_id(session_id)
    assert isinstance(cursor_id, str) and cursor_id

    extra = app.publish_event({"type": "debug_marker", "session_id": session_id})
    extra_id = extra.get("event_id")
    assert isinstance(extra_id, str) and extra_id

    # Calling /events with only session_id should start from the
    # cursor, returning only the extra event for this session.
    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    returned_ids = {ev.get("event_id") for ev in payload}
    assert extra_id in returned_ids
    # Older events (including the checkpoint itself) should not be
    # included in this batch.
    assert cursor_id not in returned_ids


def test_events_endpoint_compacts_partials(tmp_path: Path) -> None:
    """GET /events omits redundant partials when a final is present.

    When a batch contains both partial and final events for the same
    request, only the final should be returned for that request.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Publish a sequence of partial events followed by a final for the
    # same (session_id, request_id) pair.
    request_id = "req-1"
    app.publish_event(
        {"type": "partial", "session_id": session_id, "request_id": request_id}
    )
    app.publish_event(
        {"type": "partial", "session_id": session_id, "request_id": request_id}
    )
    app.publish_event(
        {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [
                {"role": "assistant", "content": "done", "metadata": {}},
            ],
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    types = [ev.get("type") for ev in payload if ev.get("session_id") == session_id]
    # Final must be present.
    assert "final" in types
    # All partials for this request should have been compacted away.
    assert "partial" not in [
        ev.get("type")
        for ev in payload
        if ev.get("session_id") == session_id and ev.get("request_id") == request_id
    ]


def test_events_endpoint_merges_consecutive_partials(tmp_path: Path) -> None:
    """GET /events merges consecutive partials for the same request.

    When a batch contains only partial events for a request (no
    final yet), consecutive partials should be merged so that callers
    receive a single event with concatenated content/reasoning.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    request_id = "req-merge"
    # Two partials with both reasoning and content pieces.
    app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {
                "role": "assistant",
                "content": "Hello, ",
                "metadata": {"reasoning": "think1 "},
            },
        }
    )
    app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {
                "role": "assistant",
                "content": "world",
                "metadata": {"reasoning": "think2"},
            },
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    # For this request we should see a single merged partial.
    partials = [
        ev
        for ev in payload
        if ev.get("type") == "partial" and ev.get("session_id") == session_id
    ]
    assert len(partials) == 1

    msg = partials[0].get("message") or {}
    md = msg.get("metadata") or {}
    assert msg.get("content") == "Hello, world"
    assert md.get("reasoning") == "think1 think2"


def test_events_endpoint_respects_compaction_flags(tmp_path: Path) -> None:
    """Disabling compaction flags leaves event batches unchanged.

    This test toggles the AgentApplication compaction flags to verify
    that they can be used to disable dropping and merging behavior for
    debugging and tests.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]
    request_id = "req-flags"

    # Publish two partials and a final.
    ev1 = app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {"role": "assistant", "content": "a", "metadata": {}},
        }
    )
    ev2 = app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {"role": "assistant", "content": "b", "metadata": {}},
        }
    )
    ev3 = app.publish_event(
        {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [
                {"role": "assistant", "content": "ab", "metadata": {}},
            ],
        }
    )

    # Disable all compaction.
    app._enable_event_compaction = False

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    ids = [ev.get("event_id") for ev in payload]
    assert ids[:3] == [ev1.get("event_id"), ev2.get("event_id"), ev3.get("event_id")]


def test_events_endpoint_compacts_tool_partials(tmp_path: Path) -> None:
    """GET /events drops tool_partial events once tool_results is present."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]
    request_id = "req-tools"
    tool_call_id = "call-1"

    # Two streaming tool_partial chunks followed by a final tool_results.
    app.publish_event(
        {
            "type": "tool_partial",
            "session_id": session_id,
            "request_id": request_id,
            "tool_call_id": tool_call_id,
            "phase": "stream",
            "payload": {"part": "alpha "},
        }
    )
    app.publish_event(
        {
            "type": "tool_partial",
            "session_id": session_id,
            "request_id": request_id,
            "tool_call_id": tool_call_id,
            "phase": "stream",
            "payload": {"part": "beta"},
        }
    )
    app.publish_event(
        {
            "type": "tool_results",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [
                {
                    "role": "tool",
                    "content": "final",
                    "metadata": {"tool_call_id": tool_call_id},
                }
            ],
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    types = [
        ev.get("type")
        for ev in payload
        if ev.get("session_id") == session_id and ev.get("request_id") == request_id
    ]
    assert "tool_results" in types
    assert "tool_partial" not in types


def test_events_endpoint_preserves_inflight_partials(tmp_path: Path) -> None:
    """GET /events keeps in-flight partials when no final/results exist.

    For requests that have not yet produced a final or tool_results
    event, partial and tool_partial events should not be dropped by the
    compaction pass.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events_store)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]
    request_id = "req-inflight"

    app.publish_event(
        {
            "type": "partial",
            "session_id": session_id,
            "request_id": request_id,
            "message": {"role": "assistant", "content": "a", "metadata": {}},
        }
    )
    app.publish_event(
        {
            "type": "tool_partial",
            "session_id": session_id,
            "request_id": request_id,
            "tool_call_id": "tc1",
            "phase": "stream",
            "payload": {"part": "x"},
        }
    )

    resp = server_mod.list_events(session_id=session_id, app_instance=app)
    payload = resp.get("events") or []

    types = [
        ev.get("type")
        for ev in payload
        if ev.get("session_id") == session_id and ev.get("request_id") == request_id
    ]
    # Both partial and tool_partial should still be present (they may
    # be merged with any additional partials, but not dropped).
    assert "partial" in types
    assert "tool_partial" in types


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
    previews and metadata.
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

    # Metadata should also be included for each session (at minimum the
    # agent_id stored by the application layer).
    metadata_by_id = {entry["session_id"]: entry.get("metadata") for entry in sessions}
    assert isinstance(metadata_by_id[session_id1], dict)
    assert isinstance(metadata_by_id[session_id2], dict)


def test_checkpoint_cursor_after_message_appended(tmp_path: Path) -> None:
    """After appending a message, cursor_event_id is after the event.

    The test appends a single user message via the HTTP-style route
    functions, then verifies that:

    * A ``message_appended`` event exists for the session.
    * A subsequent ``checkpoint`` event exists with a higher
      ``event_id``.
    * ``GET /sessions/{id}/messages`` exposes ``cursor_event_id``
      equal to that checkpoint's ``event_id``.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "user", "content": "hello", "metadata": None},
        app_instance=app,
    )

    # Inspect raw events for this session.
    evs = app.get_event_store().list(session_id=session_id, limit=100)
    appended = [ev for ev in evs if ev.get("type") == "message_appended"]
    checkpoints = [ev for ev in evs if ev.get("type") == "checkpoint"]

    assert appended, "expected message_appended event"
    assert checkpoints, "expected checkpoint event after append"

    last_appended = appended[-1]
    last_checkpoint = checkpoints[-1]

    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except Exception:
            return -1

    assert _to_int(last_checkpoint.get("event_id")) > _to_int(
        last_appended.get("event_id")
    )

    # The messages endpoint should expose the same cursor_event_id.
    resp = server_mod.list_session_messages(session_id, app_instance=app)
    assert resp["cursor_event_id"] == last_checkpoint.get("event_id")


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

    # cursor_event_id is present (may be null if no cursor yet)
    assert "cursor_event_id" in full

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


def test_get_api_data_returns_initial_state() -> None:
    """GET /api/data returns the initial DataStore contents.

    This exercises the FastAPI layer end-to-end via TestClient while
    resetting the module-level ``_bonjour_data_store`` to a known
    starting value.
    """

    from agent_terminal_app import server as server_mod
    from agent_terminal_app.server import app as fastapi_app

    # Reset the global store to a predictable state for this test.
    server_mod._bonjour_data_store = server_mod.DataStore({"message": "Initial data", "count": 0})

    client = TestClient(fastapi_app)
    resp = client.get("/api/data")
    assert resp.status_code == 200

    body = resp.json()
    assert body["success"] is True
    assert body["data"] == {"message": "Initial data", "count": 0}
    ts = body.get("timestamp")
    assert isinstance(ts, str) and ts.endswith("Z")


def test_put_api_data_updates_store() -> None:
    """PUT /api/data merges into the store and subsequent GET reflects it."""

    from agent_terminal_app import server as server_mod
    from agent_terminal_app.server import app as fastapi_app

    server_mod._bonjour_data_store = server_mod.DataStore({"message": "Initial data", "count": 0})

    client = TestClient(fastapi_app)

    update = {"count": 5, "extra": "value"}
    resp = client.put("/api/data", json=update)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    updated = body["updated"]
    assert updated["message"] == "Initial data"
    assert updated["count"] == 5
    assert updated["extra"] == "value"

    # A subsequent GET should return the same updated mapping.
    resp2 = client.get("/api/data")
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["data"] == updated


def test_get_api_hello_matches_python_bonjour_shape() -> None:
    """GET /api/hello exposes the expected greeting shape."""

    from agent_terminal_app.server import app as fastapi_app

    client = TestClient(fastapi_app)
    resp = client.get("/api/hello")
    assert resp.status_code == 200

    body = resp.json()
    assert body["message"] == "Hello from Bonjour Server!"
    assert body["method"] == "GET"
    ts = body.get("timestamp")
    assert isinstance(ts, str) and ts.endswith("Z")


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


def test_update_message_endpoint_modifies_content_and_emits_event(tmp_path: Path) -> None:
    """PATCH /sessions/{session_id}/messages/{index} updates message content.

    The test creates a session with a system and two user messages,
    modifies the last message via the endpoint, and verifies both the
    stored session and the emitted ``message_modified`` event.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Create a session and add a system plus two user messages.
    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "system", "content": "system", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "one", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "two", "metadata": None},
        app_instance=app,
    )

    # Modify the last message using a negative index.
    resp = server_mod.update_message(
        session_id,
        -1,
        {"content": "two modified"},
        app_instance=app,
    )
    session_dict = resp["session"]
    contents = [m["content"] for m in session_dict["messages"]]
    assert contents == ["system", "one", "two modified"]

    # Check that a message_modified event was recorded with the expected index.
    evs = app.get_event_store().list(session_id=session_id, limit=100)
    modified = [ev for ev in evs if ev.get("type") == "message_modified"]
    assert modified, "expected at least one message_modified event"
    last_ev = modified[-1]
    assert last_ev["index"] == 2
    assert last_ev["content"] == "two modified"


def test_delete_messages_endpoint_supports_indices_range_and_last(tmp_path: Path) -> None:
    """DELETE /sessions/{session_id}/messages handles all deletion modes.

    The test exercises the ``indices``, ``range``, and ``last`` shapes
    and verifies both the resulting history and the reported indices.
    """

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Session with a system message and three user messages.
    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    server_mod.add_message(
        session_id,
        {"role": "system", "content": "system", "metadata": None},
        app_instance=app,
    )
    for content in ["one", "two", "three"]:
        server_mod.add_message(
            session_id,
            {"role": "user", "content": content, "metadata": None},
            app_instance=app,
        )

    # 1) Delete a single message by explicit index (remove "two").
    resp_indices = server_mod.delete_messages(
        session_id,
        {"indices": [2]},
        app_instance=app,
    )
    session_after_indices = resp_indices["session"]
    contents_indices = [m["content"] for m in session_after_indices["messages"]]
    assert contents_indices == ["system", "one", "three"]
    assert resp_indices["deleted_indices"] == [2]

    # 2) Delete specific indices (remove "one" and "three").
    resp_range = server_mod.delete_messages(
        session_id,
        {"indices": [1, 2]},
        app_instance=app,
    )
    session_after_range = resp_range["session"]
    contents_range = [m["content"] for m in session_after_range["messages"]]
    assert contents_range == ["system"]
    assert sorted(resp_range["deleted_indices"]) == [1, 2]

    # 3) Recreate messages and exercise range + last forms together.
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "one", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "two", "metadata": None},
        app_instance=app,
    )
    server_mod.add_message(
        session_id,
        {"role": "user", "content": "three", "metadata": None},
        app_instance=app,
    )

    # Delete a slice [1:3) -> "one", "two".
    resp_slice = server_mod.delete_messages(
        session_id,
        {"range": {"start": 1, "end": 3}},
        app_instance=app,
    )
    contents_slice = [m["content"] for m in resp_slice["session"]["messages"]]
    assert contents_slice == ["system", "three"]
    assert resp_slice["deleted_indices"] == [1, 2]

    # Delete the last remaining user message via ``last``.
    resp_last = server_mod.delete_messages(
        session_id,
        {"last": 1},
        app_instance=app,
    )
    contents_last = [m["content"] for m in resp_last["session"]["messages"]]
    assert contents_last == ["system"]
    assert resp_last["deleted_indices"] == [1]


def test_fork_session_endpoint_creates_truncated_copy(tmp_path: Path) -> None:
    """POST /sessions/{session_id}/fork creates a new session with sliced history."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    source_session = create["session"]
    source_id = source_session["session_id"]

    # Add a system message and three user messages to the source session.
    server_mod.add_message(
        source_id,
        {"role": "system", "content": "system", "metadata": None},
        app_instance=app,
    )
    for content in ["one", "two", "three"]:
        server_mod.add_message(
            source_id,
            {"role": "user", "content": content, "metadata": None},
            app_instance=app,
        )

    # Fork up to and including index 2 ("two").
    fork_resp = server_mod.fork_session(
        source_id,
        {"index": 2},
        app_instance=app,
    )
    forked = fork_resp["session"]
    forked_id = forked["session_id"]

    assert forked_id != source_id
    assert fork_resp["source_session_id"] == source_id

    forked_contents = [m["content"] for m in forked["messages"]]
    assert forked_contents == ["system", "one", "two"]

    # A session_created event for the fork should be present.
    evs = app.get_event_store().list(session_id=forked_id, limit=20)
    created = [ev for ev in evs if ev.get("type") == "session_created"]
    assert created, "expected a session_created event for forked session"
    assert created[-1].get("source_session_id") == source_id


def test_agent_endpoints_list_and_switch_agents(tmp_path: Path) -> None:
    """GET /agents and /sessions/{id}/agent + PATCH switching behaviour."""

    from agent_terminal_app import server as server_mod

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # List configured agents.
    agents_resp = server_mod.list_agents(app_instance=app)
    agents = agents_resp["agents"]
    assert "default" in agents
    assert "alt" in agents

    # Create a session using the default agent.
    create = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create["session"]["session_id"]

    # The session's agent endpoint should report "default".
    agent_resp = server_mod.get_session_agent(session_id, app_instance=app)
    assert agent_resp["agent_id"] == "default"

    # Switch to the "alt" agent.
    switch_resp = server_mod.update_session_agent(
        session_id,
        {"agent_id": "alt"},
        app_instance=app,
    )
    assert switch_resp["agent_id"] == "alt"

    # The session metadata should reflect the new agent id.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, session = ctx
    md = session.metadata or {}
    assert md.get("agent_id") == "alt"




