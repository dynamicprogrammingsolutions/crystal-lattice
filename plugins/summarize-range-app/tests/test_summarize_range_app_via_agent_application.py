from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "summarize_range_app.SummarizeRangeAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "summarize_range_agent_id": "default",
            "summarize_range_prompt": "Summarize this range succinctly.",
        },
    }

    path = tmp_path / "config_summarize_range_app.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_summarize_range_modifies_session_messages(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    for text in ["m0", "m1", "m2", "m3"]:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)

    app.save_session(session)

    result = app.execute_application_action(
        "summarize_range",
        "summarize_range",
        {"session_id": session_id, "start": 1, "end": 3},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    updated = app.load_session_record(session_id)
    assert updated is not None
    assert len(updated.messages) == 3
    assert updated.messages[0].role == "user"
    assert updated.messages[0].content == "m0"
    assert updated.messages[2].role == "user"
    assert updated.messages[2].content == "m3"
    assert updated.messages[1].role == "assistant"
    assert isinstance(updated.messages[1].content, str) and updated.messages[1].content


def test_summarize_range_validation_error_bubbles(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    for text in ["one", "two"]:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)

    app.save_session(session)

    with pytest.raises(Exception):
        app.execute_application_action(
            "summarize_range",
            "summarize_range",
            {"session_id": session_id, "start": 5, "end": 1},
        )
