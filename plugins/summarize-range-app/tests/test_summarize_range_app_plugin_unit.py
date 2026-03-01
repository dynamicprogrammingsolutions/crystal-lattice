"""Unit tests for :mod:`summarize_range_app` application plugin.

These tests exercise the SummarizeRangeAppPlugin directly via the
application-layer ``AgentApplication.execute_application_action`` helper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session

# Ensure provider + app plugin are importable for dotted-path loading.
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from summarize_range_app import SummarizeRangeAppPlugin  # noqa: F401


def _get_mutations(result: Dict[str, Any]) -> Dict[str, Any]:
    mutations = result.get("mutations")
    return mutations if isinstance(mutations, dict) else {}


def _make_config_with_summarize_range(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
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

    path = tmp_path / "config_summarize_range.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    config_path = _make_config_with_summarize_range(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def test_summarize_range_replaces_range_with_single_message(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="summarize_range",
        params={"session_id": session_id, "start": 1, "end": 3},
    )

    updated = _get_mutations(result).get("updated_session_ids") or []
    assert updated == [session_id]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx

    # Expect exactly one message in the original [1:3] range to have been
    # replaced by a single assistant summary message.
    assert len(session.messages) == 3
    assert [m.content for m in session.messages] == [
        "m0",
        session.messages[1].content,
        "m3",
    ]
    assert session.messages[1].role == "assistant"
    assert isinstance(session.messages[1].content, str)
    assert session.messages[1].content != ""


def test_prompt_input_overrides_config_default(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["hello", "world"])

    # The echo-like provider will echo the last user message, so by providing
    # an explicit prompt we can assert that the summary text matches it.
    custom_prompt = "Custom summarization prompt"  # echoed back verbatim

    result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="summarize_range",
        params={
            "session_id": session_id,
            "start": 0,
            "end": 2,
            "prompt": custom_prompt,
        },
    )

    updated = _get_mutations(result).get("updated_session_ids") or []
    assert updated == [session_id]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx

    # With the echo provider wired up, the assistant summary should equal the
    # last user message content (our custom prompt). In this test the entire
    # range is summarized, so only a single assistant message remains.
    assert len(session.messages) == 1
    summary_msg = session.messages[0]
    assert summary_msg.role == "assistant"
    assert isinstance(summary_msg.content, str)
    assert custom_prompt in summary_msg.content


def test_plugin_error_status_when_no_assistant_reply(tmp_path: Path) -> None:
    """Guard that a failed summarization run returns plugin_error status.

    This test monkeypatches AgentApplication.send_request to simulate a
    provider failure that yields no final assistant reply.
    """

    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["one", "two"])

    captured: Dict[str, Any] = {}

    def _fake_send_request(
        core_arg: Any,
        session_arg: Session,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        # Record arguments for sanity and yield no final event.
        captured["session_id"] = session_arg.session_id
        captured["overrides"] = overrides_arg
        return [
            {
                "type": "request_started",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
            {
                "type": "request_completed",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
        ]

    # Monkeypatch AgentApplication.send_request on this instance.
    app.send_request = _fake_send_request  # type: ignore[assignment]

    result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="summarize_range",
        params={"session_id": session_id, "start": 0, "end": 2},
    )

    assert result.get("status") == "error"
    assert result.get("error_type") == "plugin_error"

    # Session history should be unchanged on failure.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    assert [m.content for m in session.messages] == ["one", "two"]
