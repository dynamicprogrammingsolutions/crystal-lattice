from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication, SessionConflictError
from agent_app.events import InMemoryEventStore
from plugins.controllable_openai_test_provider import (
    release_controllable_openai_test_provider_call,
    reset_controllable_openai_test_provider_state,
    wait_for_controllable_openai_test_provider_call,
)


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "controlled": {
                "provider": "controllable_openai_test_provider",
                "model": "test-model",
                "response_text": (
                    "<state_snapshot><overall_goal>Keep going</overall_goal></state_snapshot>"
                ),
                "block_until_released": True,
                "block_wait_timeout": 5.0,
            },
        },
        "plugins": [
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
        "agents": {
            "default": {
                "provider": "controlled",
                "compaction": {
                    "enabled": True,
                    "type": "gemini",
                    "verification_pass": False,
                },
            },
        },
    }

    path = tmp_path / "config_gemini_compaction_app.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_compact_range_conflicts_when_session_changes_mid_action(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    for role, content in [
        ("user", "u0"),
        ("assistant", "a0"),
        ("user", "u1"),
        ("assistant", "a1"),
    ]:
        session = core.add_message(session, role, content, None, base_config)

    app.save_session(session)

    outcome: Dict[str, Any] = {}

    def _run_action() -> None:
        try:
            outcome["result"] = app.execute_application_action(
                "gemini_compaction",
                "compact_range",
                {"session_id": session_id},
            )
        except Exception as exc:  # pragma: no cover - asserted below
            outcome["exception"] = exc

    thread = threading.Thread(target=_run_action)
    thread.start()

    try:
        assert wait_for_controllable_openai_test_provider_call(2.0)
        ctx = app.load_session(session_id)
        assert ctx is not None
        core_live, base_live, live_session = ctx
        advanced = core_live.add_message(
            live_session,
            "user",
            "concurrent edit",
            None,
            base_live,
        )
        app.save_session(advanced)
    finally:
        release_controllable_openai_test_provider_call()

    thread.join(timeout=2.0)
    assert not thread.is_alive()

    exc = outcome.get("exception")
    assert isinstance(exc, SessionConflictError)
    assert "Concurrent session modification detected while compacting messages" in str(exc)

    stored = app.load_session_record(session_id)
    assert stored is not None
    assert [msg.content for msg in stored.messages] == [
        "u0",
        "a0",
        "u1",
        "a1",
        "concurrent edit",
    ]