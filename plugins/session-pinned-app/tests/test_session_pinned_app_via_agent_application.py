from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "session_pinned_app.SessionPinnedAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "session_pinned_metadata_key": "pinned",
        },
    }

    path = tmp_path / "config_session_pinned_app.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_toggle_session_pinned_updates_session_metadata(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")
    session_id = session.session_id

    out1 = app.execute_application_action(
        "session_pinned",
        "toggle_session_pinned",
        {"session_id": session_id},
    )
    assert (out1.get("mutations") or {}).get("updated_session_ids") == [session_id]

    s1 = app.load_session_record(session_id)
    assert s1 is not None
    assert bool((s1.metadata or {}).get("pinned")) is True

    out2 = app.execute_application_action(
        "session_pinned",
        "toggle_session_pinned",
        {"session_id": session_id},
    )
    assert (out2.get("mutations") or {}).get("updated_session_ids") == [session_id]

    s2 = app.load_session_record(session_id)
    assert s2 is not None
    assert bool((s2.metadata or {}).get("pinned")) is False
