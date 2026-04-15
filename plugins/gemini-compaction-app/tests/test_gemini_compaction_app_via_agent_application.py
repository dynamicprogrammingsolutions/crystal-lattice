from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication, SessionConflictError
from agent_app.events import InMemoryEventStore
from agent_core import Session


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "gemini_compaction_app.GeminiCompactionAppPlugin",
        ],
        "agents": {
            "default": {
                "provider": "echo",
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

    class _FakeCore:
        def send_request(
            self,
            session_arg: Session,
            config_arg: Dict[str, Any],
            *,
            request_id: str | None = None,
            cancellation: Any | None = None,
        ) -> tuple[Session, List[Dict[str, Any]]]:
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
            return session_arg, [
                {
                    "role": "assistant",
                    "content": "<state_snapshot><overall_goal>Keep going</overall_goal></state_snapshot>",
                }
            ]

    def _fake_prepare_tools_for_session(
        core_arg: Any,
        session_arg: Session,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        request_id: str | None = None,
    ) -> tuple[Any, Dict[str, Any], Session, Dict[str, Any], str]:
        return _FakeCore(), base_config_arg, session_arg, dict(base_config_arg), "fake-rid"

    app.prepare_tools_for_session = _fake_prepare_tools_for_session  # type: ignore[assignment]

    with pytest.raises(
        SessionConflictError,
        match="Concurrent session modification detected while compacting messages",
    ):
        app.execute_application_action(
            "gemini_compaction",
            "compact_range",
            {"session_id": session_id},
        )

    stored = app.load_session_record(session_id)
    assert stored is not None
    assert [msg.content for msg in stored.messages] == [
        "u0",
        "a0",
        "u1",
        "a1",
        "concurrent edit",
    ]