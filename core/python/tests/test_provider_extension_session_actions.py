from __future__ import annotations

from agent_core import AgentCore

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider
from tests.dummy_provider_extension_session_action import DummySessionActionExtension


def _config() -> dict[str, object]:
    return {
        "provider": "echo_openai_like",
        "model": "test-model",
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider, [DummySessionActionExtension])
    return core


def test_get_session_actions_exposes_extension_actions() -> None:
    core = _build_core()

    actions = core.get_session_actions(_config())

    assert len(actions) == 1
    action = actions[0]
    assert action["plugin"] == "dummy_session_action"
    assert action["id"] == "append_native_marker"
    assert action["action_owner"] == "provider_extension"


def test_get_ui_schema_marks_extension_actions_with_owner() -> None:
    core = _build_core()

    elements = core.get_ui_schema(_config())

    session_actions = [el for el in elements if el.get("ui_type") == "session_action"]
    assert len(session_actions) == 1
    element = session_actions[0]
    assert element["plugin"] == "dummy_session_action"
    assert element["action_id"] == "append_native_marker"
    assert element["action_owner"] == "provider_extension"


def test_execute_session_action_rebuilds_messages_from_native_history() -> None:
    core = _build_core()
    config = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "hello", config=config)
    session, finals = core.send_request(session, config)

    assert finals[-1]["content"] == "SYS= | USER=hello"
    assert session.messages[-1].metadata is not None
    assert "native_indices" in (session.messages[-1].metadata or {})

    updated_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="dummy_session_action",
        action_id="append_native_marker",
        params={"marker": "after-send"},
    )

    assert result["message"] == "Appended marker after-send"
    assert [message.content for message in updated_session.messages] == [
        "hello",
        "SYS= | USER=hello",
        "MARKER=after-send",
    ]
    assert all(
        "native_indices" in ((message.metadata or {})) for message in updated_session.messages
    )

    native_history = (updated_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert native_history[-1] == {"role": "assistant", "content": "MARKER=after-send"}
    assert (updated_session.metadata or {}).get("native_messages_integrity") == {
        "message_count": 3,
        "total_chars": len("hello") + len("SYS= | USER=hello") + len("MARKER=after-send"),
    }


def test_execute_session_action_validates_inputs() -> None:
    core = _build_core()
    session = core.create_session()

    try:
        core.execute_session_action(
            session,
            _config(),
            plugin_id="dummy_session_action",
            action_id="append_native_marker",
            params={},
        )
    except AgentCore._SessionActionValidationError as exc:  # type: ignore[attr-defined]
        assert exc.details == {"missing_params": ["marker"]}
    else:  # pragma: no cover - defensive
        raise AssertionError("expected validation error")