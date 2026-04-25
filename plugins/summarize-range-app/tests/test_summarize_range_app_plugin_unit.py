"""Unit tests for :mod:`summarize_range_app` application plugin."""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Any, Dict, List

import json
import pytest

from agent_app.application_future import AgentApplication, SessionConflictError
from agent_app.events import InMemoryEventStore

from plugins.controllable_openai_test_provider import (
    get_controllable_openai_test_provider_state,
    release_controllable_openai_test_provider_call,
    reset_controllable_openai_test_provider_state,
    wait_for_controllable_openai_test_provider_call,
)

from summarize_range_app import SummarizeRangeAppPlugin  # noqa: F401


def _get_mutations(result: Dict[str, Any]) -> Dict[str, Any]:
    mutations = result.get("mutations")
    return mutations if isinstance(mutations, dict) else {}


def _make_config_with_summarize_range(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
    extra_plugins: List[str] | None = None,
    filename: str = "config_summarize_range.json",
) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "controlled": {
                "provider": "controllable_openai_test_provider",
                "model": "test-model",
                **dict(provider_config or {}),
            }
        },
        "plugins": [
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
            *(extra_plugins or []),
            "summarize_range_app.SummarizeRangeAppPlugin",
        ],
        "agents": {
            "default": {"provider": "controlled"},
        },
        "application": {
            "summarize_range_agent_id": "default",
            "summarize_range_prompt": "Summarize this range succinctly.",
            **dict(application_config or {}),
        },
    }

    path = tmp_path / filename
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
    extra_plugins: List[str] | None = None,
    filename: str = "config_summarize_range.json",
    session_dir: str = "sessions",
) -> AgentApplication:
    config_path = _make_config_with_summarize_range(
        tmp_path,
        provider_config=provider_config,
        application_config=application_config,
        extra_plugins=extra_plugins,
        filename=filename,
    )
    session_root = tmp_path / session_dir
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    core, base_config, session = app.create_session("default")

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def test_summarize_range_replaces_range_with_single_message(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Range summary"},
    )

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

    assert len(session.messages) == 3
    assert [m.content for m in session.messages] == [
        "m0",
        "Range summary",
        "m3",
    ]
    assert session.messages[1].role == "assistant"


def test_summarize_before_message_ui_action_is_inclusive() -> None:
    plugin = SummarizeRangeAppPlugin()
    plugin.init({"application": {}})

    elements = plugin.get_ui_elements(plugin._state)
    action = next(el for el in elements if el.get("id") == "summarize_before_message")

    assert action["ui_type"] == "message_action"
    assert action["fixed_params"]["start"] == 0
    assert action["fixed_params"]["end_inclusive"] is True
    assert action["param_map"]["end"] == "$message.index"


def test_end_inclusive_replaces_selected_message_too(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Inclusive summary"},
        filename="config_summarize_range_inclusive.json",
        session_dir="sessions_inclusive",
    )

    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="summarize_range",
        params={
            "session_id": session_id,
            "start": 0,
            "end": 2,
            "end_inclusive": True,
        },
    )

    assert _get_mutations(result).get("updated_session_ids") == [session_id]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    assert [m.content for m in session.messages] == [
        "Inclusive summary",
        "m3",
    ]
    assert session.messages[0].role == "assistant"


def test_prompt_input_overrides_config_default(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_mode": "echo_last_user"},
        filename="config_summarize_range_echo.json",
        session_dir="sessions_echo",
    )

    session_id = _create_session_with_messages(app, ["hello", "world"])
    custom_prompt = "Custom summarization prompt"

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
    assert len(session.messages) == 1
    assert session.messages[0].role == "assistant"
    assert custom_prompt in str(session.messages[0].content)


def test_summarize_range_internal_request_disables_tools_with_real_app(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Condensed summary"},
        application_config={
            "summarize_range_settings_overrides": {
                "request_options": {"temperature": 0.4},
            }
        },
        extra_plugins=[
            "plugins.openai_tools_extension.OpenAIToolsExtension",
            "plugins.request_options_feature.RequestOptionsFeature",
            "plugins.tool_gating_feature.ToolGatingFeature",
            "plugins.math_tools.MathTools",
        ],
        filename="config_summarize_range_tools.json",
        session_dir="sessions_tools",
    )

    session_id = _create_session_with_messages(app, ["First message", "Second message"])

    result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="summarize_range",
        params={
            "session_id": session_id,
            "start": 0,
            "end": 2,
            "prompt": "Use this custom summarize prompt.",
        },
    )

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    provider_state = get_controllable_openai_test_provider_state()

    assert _get_mutations(result).get("updated_session_ids") == [session_id]
    assert len(session.messages) == 1
    assert session.messages[0].content == "Condensed summary"
    assert provider_state["payload"] == {
        "model": "test-model",
        "temperature": 0.4,
    }
    assert provider_state["last_user_message"] == "Use this custom summarize prompt."


def test_plugin_error_status_when_no_assistant_reply(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_mode": "none"},
        filename="config_summarize_range_no_reply.json",
        session_dir="sessions_no_reply",
    )

    session_id = _create_session_with_messages(app, ["one", "two"])

    result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="summarize_range",
        params={"session_id": session_id, "start": 0, "end": 2},
    )

    assert result.get("status") == "error"
    assert result.get("error_type") == "plugin_error"

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    assert [m.content for m in session.messages] == ["one", "two"]


def test_summarize_range_conflicts_when_session_changes_mid_action(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={
            "response_text": "summary output",
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        filename="config_summarize_range_conflict.json",
        session_dir="sessions_conflict",
    )
    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    outcome: Dict[str, Any] = {}

    def _run_action() -> None:
        try:
            outcome["result"] = app.execute_application_action(
                plugin_id="summarize_range",
                action_id="summarize_range",
                params={"session_id": session_id, "start": 1, "end": 3},
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
    assert "Concurrent session modification detected while summarizing messages" in str(exc)

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    assert [msg.content for msg in session.messages] == [
        "m0",
        "m1",
        "m2",
        "m3",
        "concurrent edit",
    ]