from __future__ import annotations

from typing import Any, Dict, List

from agent_core import AgentCore

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider
from timestamp_extension.timestamp_extension import TimestampExtension


class SyntheticSystemMessageFeature:
    """Minimal stand-in for SystemMessageFeature.

    TimestampExtension tests need a feature that injects a synthetic system
    message into provider-native history during request initialization.
    """

    name: str = "synthetic_system_message_feature"
    version: str = "0.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - not needed in tests
        return {}

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        cfg = state.get("config") or {}
        system_message = cfg.get("system_message")
        if not isinstance(system_message, str) or not system_message:
            return list(native_messages), state

        if native_messages and isinstance(native_messages[0], dict) and native_messages[0].get("role") == "system":
            return list(native_messages), state

        injected = {"role": "system", "content": system_message, "_metadata": {}}
        return [injected, *list(native_messages)], state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state


def _make_core(*, with_system_message: bool) -> AgentCore:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider)
    if with_system_message:
        core.register_feature(SyntheticSystemMessageFeature)
    core.register_feature(TimestampExtension)
    return core


def test_assistant_timestamp_persisted_in_native_history_and_survives_rebuild() -> None:
    core = _make_core(with_system_message=False)
    config: Dict[str, Any] = {"model": "test-model"}

    session = core.create_session()
    session = core.add_message(session, "user", "hi", config=config)

    native_0 = session.metadata.get("native_messages") or []
    assert native_0
    assert native_0[0].get("_metadata", {}).get("timestamp")

    session_1, finals = core.send_request(session, config)
    assert finals
    assistant_ts = finals[-1].get("metadata", {}).get("timestamp")
    assert isinstance(assistant_ts, str) and assistant_ts

    native_1 = session_1.metadata.get("native_messages") or []
    assert native_1
    assert native_1[-1].get("role") == "assistant"
    assert native_1[-1].get("_metadata", {}).get("timestamp") == assistant_ts

    # Appending a new message rebuilds core history from native history.
    session_2 = core.add_message(session_1, "user", "next", config=config)

    assistant_msgs = [msg for msg in session_2.messages if msg.role == "assistant"]
    assert assistant_msgs
    assert assistant_msgs[-1].metadata
    assert assistant_msgs[-1].metadata.get("timestamp") == assistant_ts


def test_does_not_timestamp_synthetic_system_messages_during_request_prep() -> None:
    core = _make_core(with_system_message=True)
    config: Dict[str, Any] = {
        "model": "test-model",
        "system_message": "template system message",
    }

    session = core.create_session()
    session = core.add_message(session, "user", "hi", config=config)

    user_messages = [m for m in session.messages if m.role == "user"]
    assert user_messages
    user_ts = (
        user_messages[0].metadata.get("timestamp") if user_messages[0].metadata else None
    )
    assert isinstance(user_ts, str) and user_ts

    session_1, _finals_1 = core.send_request(session, config)
    native_1: List[Dict[str, Any]] = session_1.metadata.get("native_messages") or []
    sys_1 = [m for m in native_1 if m.get("role") == "system"]
    assert len(sys_1) == 1
    assert not sys_1[0].get("_metadata", {}).get("timestamp")

    # Trigger a second request without appending a new message. This exercises
    # the retained-native-history path where core and native histories can be
    # temporarily misaligned.
    session_2, _finals_2 = core.send_request(session_1, config)
    native_2: List[Dict[str, Any]] = session_2.metadata.get("native_messages") or []
    sys_2 = [m for m in native_2 if m.get("role") == "system"]
    assert len(sys_2) == 1
    assert not sys_2[0].get("_metadata", {}).get("timestamp")

    user_2 = [m for m in native_2 if m.get("role") == "user"]
    assert user_2
    assert user_2[0].get("_metadata", {}).get("timestamp") == user_ts
