from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core import AgentCore
from plugins.deterministic_stream_provider import DeterministicStreamProvider


class SyntheticTemplateSystemFeature:
    name = "synthetic_template_system"

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        has_system = any(
            isinstance(message, dict) and message.get("role") == "system"
            for message in native_messages
        )
        if has_system:
            return native_messages, state

        synthetic = {
            "role": "system",
            "content": "Template {{NAME}}",
            "_metadata": {"source": "synthetic"},
        }
        return [synthetic, *native_messages], state


def _make_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(DeterministicStreamProvider)
    core.register_feature(SyntheticTemplateSystemFeature)
    return core


def _system_messages(session) -> list:
    return [message for message in session.messages if message.role == "system"]


def _native_system_messages(session) -> list:
    native_messages = (session.metadata or {}).get("native_messages") or []
    return [message for message in native_messages if message.get("role") == "system"]


def test_send_request_rebuilds_session_messages_when_initialize_request_changes_native_history() -> None:
    core = _make_core()
    config: Dict[str, Any] = {
        "provider": DeterministicStreamProvider.name,
        "model": "deterministic-test",
    }

    session = core.create_session()
    session = core.add_message(session, "user", "hello")

    new_session, final_messages = core.send_request(session, config)

    assert [message["role"] for message in final_messages] == ["assistant"]
    assert [message.role for message in new_session.messages] == [
        "system",
        "user",
        "assistant",
    ]
    assert _system_messages(new_session)[0].content == "Template {{NAME}}"
    assert _system_messages(new_session)[0].metadata == {"source": "synthetic", "native_indices": [0]}

    native_system = _native_system_messages(new_session)
    assert len(native_system) == 1
    assert native_system[0]["content"] == "Template {{NAME}}"

    session2 = core.add_message(new_session, "user", "again", config=config)
    newer_session, _final_messages = core.send_request(session2, config)

    assert len(_system_messages(newer_session)) == 1
    assert _system_messages(newer_session)[0].content == "Template {{NAME}}"


def test_send_request_stream_rebuilds_session_messages_when_initialize_request_changes_native_history() -> None:
    core = _make_core()
    config: Dict[str, Any] = {
        "provider": DeterministicStreamProvider.name,
        "model": "deterministic-test",
        "stream": True,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "hello")

    events = list(core.send_request_stream(session, config))
    final_event = events[-1]

    assert final_event["type"] == "final"
    assert [message["role"] for message in final_event["messages"]] == ["assistant"]

    new_session = final_event["session"]
    assert [message.role for message in new_session.messages] == [
        "system",
        "user",
        "assistant",
    ]
    assert _system_messages(new_session)[0].content == "Template {{NAME}}"

    native_system = _native_system_messages(new_session)
    assert len(native_system) == 1
    assert native_system[0]["content"] == "Template {{NAME}}"