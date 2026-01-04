"""Unit tests for :mod:`plugins.session_timestamp_meta_app`.

These tests exercise the SessionTimestampMetaAppPlugin UI schema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from plugins.session_timestamp_meta_app import (  # noqa: F401
    SessionTimestampMetaAppPlugin,
)


def _make_config_with_timestamp_meta(tmp_path: Path) -> Path:
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
            "plugins.session_timestamp_meta_app.SessionTimestampMetaAppPlugin",
        ],
        "application": {},
    }

    path = tmp_path / "config_session_timestamp_meta.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config_with_timestamp_meta(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_session_timestamp_meta_ui_schema_includes_modified_field(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    elements = app.get_application_ui_schema()
    fields = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "session_timestamp_meta"
        and el.get("ui_type") == "session_list_field"
        and el.get("role") == "meta"
        and el.get("data") == "modified"
    ]

    assert fields, "expected a session_list_field for modified timestamp"
    field = fields[0]
    md = field.get("metadata") or {}
    assert md.get("format") == "datetime"
