from __future__ import annotations

from typing import Any, Dict, List

from agent_core import AgentCore

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


class _ScriptedResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _ScriptedResponsesResource:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self._payloads = list(payloads)
        self.calls: List[Dict[str, Any]] = []
        self._cursor = 0

    def create(self, **kwargs: Any) -> _ScriptedResponse:
        self.calls.append(kwargs)
        if self._cursor >= len(self._payloads):
            raise RuntimeError("no scripted response remaining")
        payload = self._payloads[self._cursor]
        self._cursor += 1
        return _ScriptedResponse(payload)


class _ScriptedClient:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self.responses = _ScriptedResponsesResource(payloads)


class _ScriptedNativeHistoryProvider(OpenAIResponsesProvider):
    scripted_payloads: List[Dict[str, Any]] = []
    last_client: _ScriptedClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        if type(self).last_client is None:
            type(self).last_client = _ScriptedClient(list(type(self).scripted_payloads))
        state["client"] = type(self).last_client
        return state


def _config() -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
        "provider": "openai_responses",
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(_ScriptedNativeHistoryProvider)
    return core


def _response_ids(native_messages: List[Dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for item in native_messages:
        if not isinstance(item, dict):
            continue
        metadata = item.get("_metadata")
        if not isinstance(metadata, dict):
            continue
        response_id = metadata.get("response_id")
        if isinstance(response_id, str) and response_id:
            ids.add(response_id)
    return ids


def test_native_history_survives_across_core_instances() -> None:
    _ScriptedNativeHistoryProvider.last_client = None
    _ScriptedNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_1",
            "output": [
                {
                    "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": "first reasoning"}],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "First answer"}],
                },
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
    ]

    core1 = _build_core()
    config = _config()

    session = core1.create_session()
    session = core1.add_message(session, "user", "first turn")
    session_after_first, first_responses = core1.send_request(session, config)

    assert first_responses[-1]["content"] == "First answer"
    native_after_first = (session_after_first.metadata or {}).get("native_messages") or []
    assert any(isinstance(item, dict) and item.get("type") == "reasoning" for item in native_after_first)

    core2 = _build_core()
    session_after_first = core2.add_message(
        session_after_first,
        "user",
        "second turn",
        config=config,
    )
    _session_after_second, second_responses = core2.send_request(session_after_first, config)

    assert second_responses[-1]["content"] == "Second answer"

    client = _ScriptedNativeHistoryProvider.last_client
    assert client is not None
    assert len(client.responses.calls) == 2

    second_input = client.responses.calls[1]["input"]
    assert any(
        isinstance(item, dict)
        and item.get("type") == "reasoning"
        for item in second_input
    )


def test_slice_and_fork_keep_response_segments_coherent() -> None:
    _ScriptedNativeHistoryProvider.last_client = None
    _ScriptedNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_1",
            "output": [
                {
                    "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": "first reasoning"}],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "First answer"}],
                },
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
    ]

    core = _build_core()
    config = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "first turn", config=config)
    session, _ = core.send_request(session, config)
    session = core.add_message(session, "user", "second turn", config=config)
    session, _ = core.send_request(session, config)

    assert [message.content for message in session.messages] == [
        "first turn",
        "First answer",
        "second turn",
        "Second answer",
    ]

    first_assistant_md = session.messages[1].metadata or {}
    native_indices = first_assistant_md.get("native_indices") or []
    assert isinstance(native_indices, list)
    assert len(native_indices) > 1

    deleted = core.slice_session(session, config, remove_indices=[0, 1])
    deleted_native = (deleted.metadata or {}).get("native_messages") or []
    assert _response_ids(deleted_native) == {"resp_2"}
    assert [message.content for message in deleted.messages] == ["second turn", "Second answer"]

    forked = core.fork_session(session, config, upto_index=1, new_session_id="forked")
    forked_native = (forked.metadata or {}).get("native_messages") or []
    assert _response_ids(forked_native) == {"resp_1"}
    assert [message.content for message in forked.messages] == ["first turn", "First answer"]