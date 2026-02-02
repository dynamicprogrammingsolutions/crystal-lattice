"""Unit tests for :mod:`plugins.generate_title_app` application plugin.

These tests exercise the GenerateTitleAppPlugin directly via the
application-layer ``AgentApplication.execute_application_action`` helper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

# Ensure provider plugin is importable for dotted-path loading.
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from plugins.generate_title_app import GenerateTitleAppPlugin  # noqa: F401


def _get_mutations(result: Dict[str, Any]) -> Dict[str, Any]:
    mutations = result.get("mutations")
    return mutations if isinstance(mutations, dict) else {}


def _get_ui_effects(result: Dict[str, Any]) -> Dict[str, Any]:
    ui_effects = result.get("ui_effects")
    return ui_effects if isinstance(ui_effects, dict) else {}


def _make_config_with_generate_title(tmp_path: Path) -> Path:
  
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_prompt_template": "Generate a concise title.",
            "generate_title_max_messages": 10,
        },
    }

    path = tmp_path / "config_generate_title.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    config_path = _make_config_with_generate_title(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _build_app_with_system_message(tmp_path: Path, system_message: str) -> AgentApplication:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_system_message": system_message,
        },
    }

    path = tmp_path / "config_generate_title_system_message.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    session_root = tmp_path / "sessions_system_message"
    events = InMemoryEventStore()
    return AgentApplication(str(path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def test_generate_title_for_session_sets_metadata_and_ids(tmp_path: Path) -> None:
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
    assert "title" in metadata
    assert isinstance(metadata["title"], str)
    assert metadata["title"].strip() != ""


def test_generate_title_respects_session_title_metadata_key(tmp_path: Path) -> None:
    # Configure a custom metadata key and ensure the plugin writes there.
    cfg_path = tmp_path / "config_generate_title_custom_key.json"
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "session_title_metadata_key": "custom_title",
        },
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    session_root = tmp_path / "sessions_custom"
    events = InMemoryEventStore()
    app = AgentApplication(str(cfg_path), str(session_root), event_store=events)

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
    assert "custom_title" in metadata
    assert isinstance(metadata["custom_title"], str)
    assert metadata["custom_title"].strip() != ""
    assert "title" not in metadata or metadata["title"] in (None, "")


def test_generate_title_plugin_error_status_when_no_assistant_reply(
    tmp_path: Path,
) -> None:
    """Guard that a failed title generation run returns plugin_error status.

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
        from agent_core import Session as CoreSession

        assert isinstance(session_arg, CoreSession)
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
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    assert result.get("status") == "error"
    assert result.get("error_type") == "plugin_error"

    # Session metadata should be unchanged on failure.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert "title" not in metadata


def test_generate_title_from_session_list_does_not_request_navigation(
    tmp_path: Path,
) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["alpha", "beta"])

    result = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id, "source": "session_list"},
    )

    assert _get_mutations(result).get("updated_session_ids") == [session_id]
    # For session-list invocations the plugin should not suggest navigation.
    assert not isinstance(_get_ui_effects(result).get("navigate_to_session_id"), str)


def test_generate_title_populates_description_when_enabled(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["hello", "world"])

    def _fake_send_request(
        core_arg: Any,
        session_arg: Session,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "request_started",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
            {
                "type": "final",
                "session_id": session_arg.session_id,
                "request_id": request_id,
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Project Title\nShort description here",
                    }
                ],
            },
            {
                "type": "request_completed",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
        ]

    app.send_request = _fake_send_request  # type: ignore[assignment]

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
    # Default description key should be "subtitle" when not overridden.
    assert metadata.get("subtitle") == "Short description here"


def test_generate_title_ignores_description_when_disabled(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config_generate_title_no_description.json"
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_enable_description": False,
        },
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    session_root = tmp_path / "sessions_no_desc"
    events = InMemoryEventStore()
    app = AgentApplication(str(cfg_path), str(session_root), event_store=events)

    session_id = _create_session_with_messages(app, ["one", "two"])

    def _fake_send_request(
        core_arg: Any,
        session_arg: Session,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "request_started",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
            {
                "type": "final",
                "session_id": session_arg.session_id,
                "request_id": request_id,
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Only Title\nAnd a second line that should be ignored",
                    }
                ],
            },
            {
                "type": "request_completed",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
        ]

    app.send_request = _fake_send_request  # type: ignore[assignment]

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
    cfg_path = tmp_path / "config_generate_title_custom_desc_key.json"
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_description_metadata_key": "custom_subtitle",
        },
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    session_root = tmp_path / "sessions_custom_desc_key"
    events = InMemoryEventStore()
    app = AgentApplication(str(cfg_path), str(session_root), event_store=events)

    session_id = _create_session_with_messages(app, ["alpha", "beta"])

    def _fake_send_request(
        core_arg: Any,
        session_arg: Session,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "request_started",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
            {
                "type": "final",
                "session_id": session_arg.session_id,
                "request_id": request_id,
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Custom Title\nCustom subtitle here",
                    }
                ],
            },
            {
                "type": "request_completed",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
        ]

    app.send_request = _fake_send_request  # type: ignore[assignment]

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
    system_message = (
        "You are a title generator. Respond with exactly two lines: "
        "first line is the title, second line is a one-sentence description."
    )
    app = _build_app_with_system_message(tmp_path, system_message)

    session_id = _create_session_with_messages(app, ["hello", "world"])

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
        # Capture the messages passed to the provider so we can assert on
        # the system message replacement behaviour.
        captured["messages"] = list(session_arg.messages)
        return [
            {
                "type": "request_started",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
            {
                "type": "final",
                "session_id": session_arg.session_id,
                "request_id": request_id,
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Title line\nDescription line",
                    }
                ],
            },
            {
                "type": "request_completed",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
        ]

    app.send_request = _fake_send_request  # type: ignore[assignment]

    _ = app.execute_application_action(
        plugin_id="generate_title",
        action_id="generate_title_for_session",
        params={"session_id": session_id},
    )

    msgs = captured.get("messages") or []
    assert msgs, "expected messages to be captured"
    # There should be at least one system message matching the configured
    # system message text.
    system_msgs = [m for m in msgs if getattr(m, "role", None) == "system"]
    assert system_msgs, "expected at least one system message"
    assert any(
        getattr(m, "content", "").startswith("You are a title generator")
        for m in system_msgs
    )
