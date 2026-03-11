from __future__ import annotations

from typing import Any, Dict, List

from agent_core import AgentCore

from openai_responses_plugins.openai_responses_native_compaction_extension import (
    OpenAIResponsesNativeCompactionExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


class _ScriptedResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _ScriptedResponsesResource:
    def __init__(
        self,
        create_payloads: List[Dict[str, Any]],
        compact_payload: Dict[str, Any],
    ) -> None:
        self._create_payloads = list(create_payloads)
        self._compact_payload = compact_payload
        self.create_calls: List[Dict[str, Any]] = []
        self.compact_calls: List[Dict[str, Any]] = []
        self._create_cursor = 0

    def create(self, **kwargs: Any) -> _ScriptedResponse:
        self.create_calls.append(kwargs)
        if self._create_cursor >= len(self._create_payloads):
            raise RuntimeError("no scripted create payload remaining")
        payload = self._create_payloads[self._create_cursor]
        self._create_cursor += 1
        return _ScriptedResponse(payload)

    def compact(self, **kwargs: Any) -> _ScriptedResponse:
        self.compact_calls.append(kwargs)
        return _ScriptedResponse(self._compact_payload)


class _ScriptedClient:
    def __init__(
        self,
        create_payloads: List[Dict[str, Any]],
        compact_payload: Dict[str, Any],
    ) -> None:
        self.responses = _ScriptedResponsesResource(create_payloads, compact_payload)


class _ScriptedCompactionProvider(OpenAIResponsesProvider):
    scripted_client: _ScriptedClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        if type(self).scripted_client is None:
            raise RuntimeError("scripted_client must be configured before init")
        state["client"] = type(self).scripted_client
        return state


def _config() -> Dict[str, Any]:
    return {
        "provider": "openai_responses",
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _ScriptedCompactionProvider,
        [OpenAIResponsesNativeCompactionExtension],
    )
    return core


def test_compaction_action_uses_sdk_and_sanitizes_input() -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[],
        compact_payload={
            "id": "cmp_1",
            "created_at": 1,
            "object": "response.compaction",
            "output": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hello"}],
                },
                {
                    "id": "comp_1",
                    "type": "compaction",
                    "encrypted_content": "opaque",
                    "created_by": "openai",
                },
            ],
            "usage": {"total_tokens": 10},
        },
    )

    extension = OpenAIResponsesNativeCompactionExtension()
    state = {
        "config": _config(),
        "client": _ScriptedCompactionProvider.scripted_client,
    }
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "id": "msg_1",
            "status": "completed",
            "content": [{"type": "output_text", "text": "hello"}],
            "_metadata": {"response_id": "resp_1"},
        }
    ]

    result = extension.execute_action(
        "compact_native_history",
        session=AgentCore().create_session(),
        native_messages=native_messages,
        params={"instructions": "Compact this session"},
        state=state,
    )

    assert result["rebuild_messages_from_native"] is False
    assert result["message"] == "Compacted provider-native history."

    calls = _ScriptedCompactionProvider.scripted_client.responses.compact_calls
    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-5-mini"
    assert calls[0]["instructions"] == "Compact this session"
    assert calls[0]["timeout"] == 30.0
    assert calls[0]["input"] == [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello"}],
        }
    ]


def test_core_session_action_preserves_transcript_and_keeps_future_turns_working() -> None:
    _ScriptedCompactionProvider.scripted_client = _ScriptedClient(
        create_payloads=[
            {
                "id": "resp_1",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "First answer"}],
                    }
                ],
            },
            {
                "id": "resp_2",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "Second answer"}],
                    }
                ],
            },
        ],
        compact_payload={
            "id": "cmp_2",
            "created_at": 2,
            "object": "response.compaction",
            "output": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "first turn"}],
                },
                {
                    "id": "comp_2",
                    "type": "compaction",
                    "encrypted_content": "opaque-compacted",
                    "created_by": "openai",
                },
            ],
            "usage": {"total_tokens": 12},
        },
    )

    core = _build_core()
    config = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "first turn", config=config)
    session, first_finals = core.send_request(session, config)
    assert first_finals[-1]["content"] == "First answer"

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={},
    )

    assert result["message"] == "Compacted provider-native history."
    assert [message.content for message in compacted_session.messages] == [
        "first turn",
        "First answer",
    ]
    assert all(
        "native_indices" not in ((message.metadata or {})) for message in compacted_session.messages
    )
    compacted_native = (compacted_session.metadata or {}).get("native_messages")
    assert isinstance(compacted_native, list)
    assert compacted_native[-1]["type"] == "compaction"

    compacted_session = core.add_message(compacted_session, "user", "second turn", config=config)
    _session_after_second, second_finals = core.send_request(compacted_session, config)

    assert second_finals[-1]["content"] == "Second answer"
    create_calls = _ScriptedCompactionProvider.scripted_client.responses.create_calls
    assert len(create_calls) == 2
    second_input = create_calls[1]["input"]
    assert any(item.get("type") == "compaction" for item in second_input if isinstance(item, dict))