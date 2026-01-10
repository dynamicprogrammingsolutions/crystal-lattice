"""Server-level tests for plugin-driven session ordering.

These tests exercise the interaction between:

* SessionTimestampMetaAppPlugin (created/updated timestamps),
* SessionPinnedAppPlugin (pinned state), and
* SessionOrderingBucketsAppPlugin (24h / pinned / recency ordering),

as applied by the ``/sessions`` endpoint.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from agent_terminal_app import server as server_mod


def _make_config_with_time_and_ordering(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": {
            "providers": [
                "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            ],
            "features": [
                # Enable timestamp extension so message metadata carries timestamps.
                "plugins.timestamp_extension.TimestampExtension",
            ],
            "tools": [],
            "extensions": [],
        },
        "agents": {
            "default": {"provider": "echo"},
        },
        "application_plugins": [
            "plugins.session_timestamp_meta_app.SessionTimestampMetaAppPlugin",
            "plugins.session_pinned_app.SessionPinnedAppPlugin",
            "plugins.session_ordering_buckets_app.SessionOrderingBucketsAppPlugin",
        ],
        "application": {
            "session_pinned_metadata_key": "pinned",
            "session_order_24h_window_seconds": 86400,
            "session_order_use_updated_at": True,
        },
    }

    path = tmp_path / "config_server_sessions_ordering_buckets.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config_with_time_and_ordering(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def _create_session_with_label(app: AgentApplication, label: str) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)
    session = core.add_message(session, "user", label, None, base_config)
    app.save_session(session)
    return session.session_id


def _pin_session(client: TestClient, session_id: str) -> None:
    payload = {
        "plugin": "session_pinned",
        "action_id": "toggle_session_pinned",
        "inputs": {"session_id": session_id},
    }
    resp = client.post("/actions", json=payload)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_sessions_ordered_by_24h_pinned_and_recency(monkeypatch, tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    # Inject app into server module.
    server_mod._agent_app = app  # type: ignore[assignment]
    fastapi_app: FastAPI = server_mod.app
    client = TestClient(fastapi_app)

    # Fix "now" for deterministic 24h window decisions.
    fake_now = 1_700_000_000.0

    import plugins.session_ordering_buckets_app as ordering_mod

    monkeypatch.setattr(ordering_mod.time, "time", lambda: fake_now)

    # Create sessions.
    s_recent_pinned = _create_session_with_label(app, "recent_pinned")
    s_recent_unpinned = _create_session_with_label(app, "recent_unpinned")
    s_old_pinned = _create_session_with_label(app, "old_pinned")

    # Manually set message-level timestamps in the session JSON files so the
    # time meta plugin computes deterministic session_updated_at values.
    session_root = Path(server_mod._get_session_root(app))  # type: ignore[arg-type]

    def _write_timestamp(session_id: str, epoch: float) -> None:
        path = session_root / f"{session_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        iso = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        messages = raw.get("messages") or []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            md = msg.get("metadata") or {}
            if not isinstance(md, dict):
                md = {}
            md["timestamp"] = iso
            msg["metadata"] = md
        raw["messages"] = messages
        path.write_text(json.dumps(raw), encoding="utf-8")

    # Chosen so that the window (24h) clearly separates recent vs old.
    recent_1 = fake_now - 3600   # 1 hour ago
    recent_2 = fake_now - 7200   # 2 hours ago
    old_ts = fake_now - 3 * 86400  # 3 days ago

    _write_timestamp(s_recent_pinned, recent_1)
    _write_timestamp(s_recent_unpinned, recent_2)
    _write_timestamp(s_old_pinned, old_ts)

    # Pin two of the sessions.
    _pin_session(client, s_recent_pinned)
    _pin_session(client, s_old_pinned)

    # First load should trigger all session_list actions, including time
    # meta and ordering buckets.
    resp = client.get("/sessions")
    assert resp.status_code == 200
    sessions = resp.json().get("sessions") or []
    ids_in_order: List[str] = [s["session_id"] for s in sessions]

    # Expect ordering:
    #   1) recent_pinned (24h bucket 0, pinned)
    #   2) recent_unpinned (24h bucket 0, unpinned)
    #   3) old_pinned (24h bucket 1, pinned)
    assert ids_in_order[:3] == [s_recent_pinned, s_recent_unpinned, s_old_pinned]
