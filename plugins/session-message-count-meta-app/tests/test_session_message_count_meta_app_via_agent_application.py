from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "session_message_count_meta_app.SessionMessageCountMetaAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }

    path = tmp_path / "config_session_message_count_meta.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    core, base_config, session = app.create_session("default")
    for text in contents:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)
    app.save_session(session)
    return session.session_id


def test_message_count_action_returns_expected_count(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id_1 = _create_session_with_messages(app, ["one", "two"])
    session_id_2 = _create_session_with_messages(app, ["alpha", "beta", "gamma"])

    out1 = app.execute_application_action(
        "session_message_count_meta",
        "compute_session_message_count_meta",
        {"session_id": session_id_1},
    )
    out2 = app.execute_application_action(
        "session_message_count_meta",
        "compute_session_message_count_meta",
        {"session_id": session_id_2},
    )

    assert (out1.get("session_list_fields") or {}).get("message_count") == 2
    assert (out2.get("session_list_fields") or {}).get("message_count") == 3
