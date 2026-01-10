"""Unit tests for :mod:`plugins.session_ordering_buckets_app`.

These tests exercise the SessionOrderingBucketsAppPlugin action and its
``session_list_fields`` / ``session_list_order`` outputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from plugins.session_ordering_buckets_app import (  # noqa: F401
    SessionOrderingBucketsAppPlugin,
)


def _make_config_with_ordering_buckets(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {},
        "plugins": {
            "providers": [],
            "features": [],
            "tools": [],
            "extensions": [],
        },
        "agents": {},
        "application_plugins": [
            "plugins.session_ordering_buckets_app.SessionOrderingBucketsAppPlugin",
        ],
        "application": {
            "session_order_24h_window_seconds": 86400,
            "session_order_use_updated_at": True,
        },
    }

    path = tmp_path / "config_session_ordering_buckets.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config_with_ordering_buckets(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_session_ordering_buckets_action_computes_fields(monkeypatch, tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    # Fix "now" so 24h window decisions are deterministic.
    fake_now = 1_700_000_000.0

    import plugins.session_ordering_buckets_app as mod

    monkeypatch.setattr(mod.time, "time", lambda: fake_now)

    # Session updated 1 hour ago, pinned.
    summary_recent_pinned = {
        "session_updated_at": fake_now - 3600,
        "modified": fake_now - 3600,
        "pinned": True,
    }

    result = app.execute_application_action(
        "session_ordering_buckets",
        "compute_session_order_buckets",
        {"session_id": "s1", "session_summary": summary_recent_pinned},
    )

    fields = result.get("session_list_fields") or {}
    assert fields.get("updated_24h_rank") == 0
    assert fields.get("pinned_rank") == 0
    assert isinstance(fields.get("last_updated_sort_key"), (int, float))

    specs = result.get("session_list_order") or []
    assert isinstance(specs, list) and len(specs) == 3
    keys = [s.get("key") for s in specs]
    assert keys == [
        "updated_24h_rank",
        "pinned_rank",
        "last_updated_sort_key",
    ]
    for s in specs:
        assert s.get("direction") == "asc"
        assert "fallback" in s
        assert isinstance(s.get("priority"), int)


def test_session_ordering_buckets_falls_back_to_modified(monkeypatch, tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    fake_now = 1_700_000_000.0
    import plugins.session_ordering_buckets_app as mod

    monkeypatch.setattr(mod.time, "time", lambda: fake_now)

    # No session_updated_at; must use modified.
    summary = {
        "modified": fake_now - 7200,
        "pinned": False,
    }

    result = app.execute_application_action(
        "session_ordering_buckets",
        "compute_session_order_buckets",
        {"session_id": "s2", "session_summary": summary},
    )

    fields = result.get("session_list_fields") or {}
    assert fields.get("updated_24h_rank") == 0  # within 24h via modified
    assert fields.get("pinned_rank") == 1
    assert fields.get("last_updated_sort_key") == -(fake_now - 7200)
