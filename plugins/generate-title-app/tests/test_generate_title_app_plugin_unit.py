"""Unit tests for :mod:`generate_title_app` application plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from plugins.controllable_openai_test_provider import (
    get_controllable_openai_test_provider_state,
    reset_controllable_openai_test_provider_state,
)

from generate_title_app import GenerateTitleAppPlugin  # noqa: F401


def _get_mutations(result: Dict[str, Any]) -> Dict[str, Any]:
    mutations = result.get("mutations")
    return mutations if isinstance(mutations, dict) else {}


def _get_ui_effects(result: Dict[str, Any]) -> Dict[str, Any]:
    ui_effects = result.get("ui_effects")
    return ui_effects if isinstance(ui_effects, dict) else {}


def _make_config_with_generate_title(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
    extra_plugins: List[str] | None = None,
    filename: str = "config_generate_title.json",
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
            "generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "controlled"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_prompt_template": "Generate a concise title.",
            "generate_title_max_messages": 10,
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
    filename: str = "config_generate_title.json",
    session_dir: str = "sessions",
) -> AgentApplication:
    config_path = _make_config_with_generate_title(
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


def test_generate_title_for_session_sets_metadata_and_ids(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["hello", "world"])

    result = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    updated = _get_mutations(result).get("updated_session_ids") or []
    assert updated == [session_id]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx

    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert metadata.get("title") == "Generated title"


def test_generate_title_respects_session_title_metadata_key(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        application_config={"session_title_metadata_key": "custom_title"},
        filename="config_generate_title_custom_key.json",
        session_dir="sessions_custom",
    )

    session_id = _create_session_with_messages(app, ["note one", "note two"])

    _ = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert metadata.get("custom_title") == "Generated title"
    assert "title" not in metadata or metadata["title"] in (None, "")


def test_generate_title_internal_request_disables_tools_with_real_app(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "A short title"},
        application_config={
            "generate_title_enable_description": False,
            "generate_title_settings_overrides": {
                "request_options": {"temperature": 0.3},
            },
        },
        extra_plugins=[
            "plugins.openai_tools_extension.OpenAIToolsExtension",
            "plugins.request_options_feature.RequestOptionsFeature",
            "plugins.tool_gating_feature.ToolGatingFeature",
            "plugins.math_tools.MathTools",
        ],
        filename="config_generate_title_tools.json",
        session_dir="sessions_tools",
    )

    session_id = _create_session_with_messages(
        app,
        ["We discussed release planning.", "We settled on a staged rollout."],
    )

    result = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    provider_state = get_controllable_openai_test_provider_state()

    assert _get_mutations(result).get("updated_session_ids") == [session_id]
    assert metadata.get("title") == "A short title"
    assert provider_state["payload"] == {
        "model": "test-model",
        "temperature": 0.3,
    }
    assert provider_state["last_user_message"] == "Generate a concise title."


def test_generate_title_plugin_error_status_when_no_assistant_reply(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_mode": "none"},
        filename="config_generate_title_no_reply.json",
        session_dir="sessions_no_reply",
    )

    session_id = _create_session_with_messages(app, ["one", "two"])

    result = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    assert result.get("status") == "error"
    assert result.get("error_type") == "plugin_error"

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert "title" not in metadata


def test_generate_title_from_session_list_does_not_request_navigation(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["alpha", "beta"])

    result = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id, "source": "session_list"},
    )

    assert _get_mutations(result).get("updated_session_ids") == [session_id]
    assert not isinstance(_get_ui_effects(result).get("navigate_to_session_id"), str)


def test_generate_title_populates_description_when_enabled(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Project Title\nShort description here"},
        filename="config_generate_title_with_desc.json",
        session_dir="sessions_with_desc",
    )

    session_id = _create_session_with_messages(app, ["hello", "world"])

    _ = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert metadata.get("title") == "Project Title"
    assert metadata.get("subtitle") == "Short description here"


def test_generate_title_ignores_description_when_disabled(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={
            "response_text": "Only Title\nAnd a second line that should be ignored"
        },
        application_config={"generate_title_enable_description": False},
        filename="config_generate_title_no_description.json",
        session_dir="sessions_no_desc",
    )

    session_id = _create_session_with_messages(app, ["one", "two"])

    _ = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert metadata.get("title") == "Only Title"
    assert "subtitle" not in metadata


def test_generate_title_uses_custom_description_metadata_key(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Custom Title\nCustom subtitle here"},
        application_config={"generate_title_description_metadata_key": "custom_subtitle"},
        filename="config_generate_title_custom_desc_key.json",
        session_dir="sessions_custom_desc_key",
    )

    session_id = _create_session_with_messages(app, ["alpha", "beta"])

    _ = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert metadata.get("title") == "Custom Title"
    assert metadata.get("custom_subtitle") == "Custom subtitle here"
    assert "subtitle" not in metadata


def test_generate_title_replaces_system_message_when_configured(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    system_message = (
        "You are a title generator. Respond with exactly two lines: "
        "first line is the title, second line is a one-sentence description."
    )
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Title line\nDescription line"},
        application_config={"generate_title_system_message": system_message},
        filename="config_generate_title_system_message.json",
        session_dir="sessions_system_message",
    )

    session_id = _create_session_with_messages(app, ["hello", "world"])

    _ = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    provider_state = get_controllable_openai_test_provider_state()
    system_messages = [
        message
        for message in provider_state["native_messages"]
        if message.get("role") == "system"
    ]
    assert system_messages
    assert any(
        str(message.get("content", "")).startswith("You are a title generator")
        for message in system_messages
    )