from __future__ import annotations

from typing import Any, Dict

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_reasoning_extension import (
    OpenAIResponsesReasoningExtension,
)
from plugins.request_options_feature import RequestOptionsFeature


def _base_state() -> Dict[str, Any]:
    return {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
        }
    }


def test_initialize_request_merges_reasoning_request_options() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "enable_reasoning": True,
        "reasoning_effort": "high",
        "reasoning_summary": "concise",
        "reasoning_max_tokens": 256,
        "request_options": {"temperature": 0.2, "reasoning": {"summary": "auto"}},
    }

    state = ext.init(config, {"config": config})
    native_messages, new_state = ext.initialize_request([], state)

    assert native_messages == []
    request_options = new_state["config"]["request_options"]
    assert request_options["temperature"] == 0.2
    assert request_options["reasoning"] == {
        "effort": "high",
        "summary": "concise",
        "max_tokens": 256,
    }


def test_process_chunk_accumulates_reasoning_deltas_into_partial_metadata() -> None:
    ext = OpenAIResponsesReasoningExtension()
    state = ext.init(_base_state()["config"], _base_state())

    partials, finals, native_messages, state = ext.process_chunk(
        {"type": "response.reasoning_summary_text.delta", "delta": "Plan: "},
        [{"role": "assistant", "content": "STREAM"}],
        [],
        [],
        state,
    )

    assert finals == []
    assert native_messages == []
    assert partials[-1]["metadata"]["reasoning"] == "Plan: "
    raw_reasoning = partials[-1]["metadata"]["openai_responses_reasoning"]
    assert raw_reasoning["summary_text"] == "Plan: "

    partials, _finals, _native_messages, state = ext.process_chunk(
        {"type": "response.reasoning_summary_text.delta", "delta": "step 1"},
        partials,
        [],
        [],
        state,
    )

    assert partials[-1]["metadata"]["reasoning"] == "Plan: step 1"
    raw_reasoning = partials[-1]["metadata"]["openai_responses_reasoning"]
    assert raw_reasoning["summary_text"] == "Plan: step 1"


def test_from_native_messages_extracts_reasoning_metadata_from_native_indices() -> None:
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesReasoningExtension()

    native_messages = [
        {
            "type": "reasoning",
            "id": "rs_123",
            "summary": [{"type": "summary_text", "text": "Used internal reasoning."}],
            "content": None,
            "encrypted_content": None,
            "status": None,
            "_metadata": {"response_id": "resp_123"},
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Done."}],
            "_metadata": {"response_id": "resp_123"},
        },
    ]

    core_messages = provider.from_native_messages(native_messages, {})
    enriched = ext.from_native_messages(native_messages, core_messages)

    assert enriched[-1]["role"] == "assistant"
    metadata = enriched[-1]["metadata"]
    assert metadata["reasoning"] == "Used internal reasoning."
    raw_reasoning = metadata["openai_responses_reasoning"]
    assert raw_reasoning["summary_text"] == "Used internal reasoning."
    assert isinstance(raw_reasoning["items"], list)
    assert raw_reasoning["items"][0]["type"] == "reasoning"


def test_from_native_messages_prefers_summary_then_falls_back_to_raw_reasoning_text() -> None:
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesReasoningExtension()

    native_messages = [
        {
            "type": "reasoning",
            "id": "rs_456",
            "summary": [],
            "content": [{"type": "reasoning_text", "text": "Detailed chain of thought."}],
            "encrypted_content": None,
            "status": None,
            "_metadata": {"response_id": "resp_456"},
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Done."}],
            "_metadata": {"response_id": "resp_456"},
        },
    ]

    core_messages = provider.from_native_messages(native_messages, {})
    enriched = ext.from_native_messages(native_messages, core_messages)

    metadata = enriched[-1]["metadata"]
    assert metadata["reasoning"] == "Detailed chain of thought."
    raw_reasoning = metadata["openai_responses_reasoning"]
    assert raw_reasoning["content_text"] == "Detailed chain of thought."


def test_streaming_send_request_integration_with_scripted_reasoning_events() -> None:
    class _ReasoningFixtureStream:
        def __iter__(self):
            yield {"type": "response.reasoning_summary_text.delta", "delta": "Considering options. "}
            yield {"type": "response.output_text.delta", "delta": "STREAM_REASONING_OK"}
            yield {
                "type": "response.completed",
                "response": {
                    "id": "resp_reasoning_stream",
                    "output": [
                        {
                            "type": "reasoning",
                            "id": "rs_reasoning_stream",
                            "summary": [
                                {"type": "summary_text", "text": "Considering options."}
                            ],
                            "content": None,
                            "encrypted_content": None,
                            "status": None,
                        },
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {"type": "output_text", "text": "STREAM_REASONING_OK"}
                            ],
                        },
                    ],
                },
            }

    class _ReasoningFixtureResponses:
        def create(self, **kwargs: Any):
            assert kwargs["stream"] is True
            return _ReasoningFixtureStream()

    class _ReasoningFixtureProvider(OpenAIResponsesProvider):
        def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
            state = super().init(config)
            state["client"] = type("_Client", (), {"responses": _ReasoningFixtureResponses()})()
            return state

    core = AgentCore()
    core.register_provider(
        _ReasoningFixtureProvider,
        extensions=[OpenAIResponsesReasoningExtension],
    )
    core.register_feature(RequestOptionsFeature)

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: STREAM_REASONING_OK")

    config = {
        **_base_state()["config"],
        "enable_reasoning": True,
        "reasoning_summary": "concise",
    }

    final_message = None
    saw_reasoning_partial = False
    for event in core.send_request_stream(session, config):
        if event["type"] == "partial":
            metadata = (event.get("message") or {}).get("metadata") or {}
            if metadata.get("reasoning"):
                saw_reasoning_partial = True
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert saw_reasoning_partial is True
    assert final_message is not None
    assert final_message["content"] == "STREAM_REASONING_OK"
    metadata = final_message["metadata"]
    assert metadata["reasoning"] == "Considering options."
    raw_reasoning = metadata["openai_responses_reasoning"]
    assert raw_reasoning["summary_text"] == "Considering options."
    assert raw_reasoning["items"][0]["type"] == "reasoning"