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
        "reasoning_effort": "high",
        "reasoning_summary": "concise",
        "request_options": {
            "temperature": 0.2,
            "include": ["message.input_image.image_url"],
            "reasoning": {"summary": "auto"},
        },
    }

    state = ext.init(config, {"config": config})
    native_messages, new_state = ext.initialize_request([], state)

    assert native_messages == []
    request_options = new_state["config"]["request_options"]
    assert request_options["temperature"] == 0.2
    assert request_options["include"] == [
        "message.input_image.image_url",
        "reasoning.encrypted_content",
    ]
    assert request_options["reasoning"] == {
        "effort": "high",
        "summary": "concise",
    }


def test_initialize_request_adds_encrypted_reasoning_include_without_reasoning_config() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    state = ext.init(_base_state()["config"], _base_state())

    native_messages, new_state = ext.initialize_request([], state)

    assert native_messages == []
    assert new_state["config"]["request_options"]["include"] == [
        "reasoning.encrypted_content"
    ]


def test_get_config_schema_exposes_current_reasoning_keys_only() -> None:
    ext = OpenAIResponsesReasoningExtension()

    schema = ext.get_config_schema()

    assert "reasoning_effort" in schema
    assert "reasoning_summary" in schema
    assert "enable_reasoning" not in schema
    assert "reasoning_max_tokens" not in schema


def test_get_ui_elements_uses_model_specific_effort_values() -> None:
    ext = OpenAIResponsesReasoningExtension()

    gpt5 = ext.get_ui_elements(
        config={"model": "gpt-5-mini"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5-mini"}],
    )
    gpt51 = ext.get_ui_elements(
        config={"model": "gpt-5.1-mini"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.1-mini"}],
    )
    gpt54 = ext.get_ui_elements(
        config={"model": "gpt-5.4"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.4"}],
    )
    gpt5pro = ext.get_ui_elements(
        config={"model": "gpt-5-pro"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5-pro"}],
    )
    unknown = ext.get_ui_elements(
        config={"model": "o3-mini"},
        tags=["supports_reasoning"],
        models=[{"id": "o3-mini"}],
    )

    def _options(elements: list[dict[str, Any]]) -> list[str]:
        effort = next(
            element for element in elements if element.get("key") == "reasoning_effort"
        )
        return [option["value"] for option in effort["options"]]

    assert _options(gpt5) == ["minimal", "low", "medium", "high"]
    assert _options(gpt51) == ["none", "low", "medium", "high"]
    assert _options(gpt54) == ["none", "low", "medium", "high", "xhigh"]
    assert _options(gpt5pro) == ["high"]
    assert _options(unknown) == ["none", "minimal", "low", "medium", "high", "xhigh"]


def test_init_ignores_effort_not_supported_by_selected_model() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.1-mini",
        "reasoning_effort": "minimal",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


def test_process_chunk_leaves_streaming_chunks_unchanged() -> None:
    ext = OpenAIResponsesReasoningExtension()
    state = ext.init(_base_state()["config"], _base_state())
    partial_input = [
        {"role": "assistant", "content": "", "_metadata": {"reasoning": "Plan: "}}
    ]

    partials, finals, native_messages, state = ext.process_chunk(
        {"type": "response.reasoning_summary_text.delta", "delta": "Plan: "},
        partial_input,
        [],
        [],
        state,
    )

    assert finals == []
    assert native_messages == []
    assert partials == partial_input


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


def test_from_native_messages_prefers_summary_then_falls_back_to_raw_reasoning_text() -> (
    None
):
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesReasoningExtension()

    native_messages = [
        {
            "type": "reasoning",
            "id": "rs_456",
            "summary": [],
            "content": [
                {"type": "reasoning_text", "text": "Detailed chain of thought."}
            ],
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
            yield {
                "type": "response.reasoning_summary_text.delta",
                "delta": "Considering options. ",
            }
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
            state["client"] = type(
                "_Client", (), {"responses": _ReasoningFixtureResponses()}
            )()
            return state

    core = AgentCore()
    core.register_provider(
        _ReasoningFixtureProvider,
        extensions=[OpenAIResponsesReasoningExtension],
    )
    core.register_feature(RequestOptionsFeature)

    session = core.create_session()
    session = core.add_message(
        session, "user", "Reply with exactly: STREAM_REASONING_OK"
    )

    config = {
        **_base_state()["config"],
        "reasoning_effort": "minimal",
        "reasoning_summary": "concise",
    }

    final_message = None
    reasoning_partials: list[str] = []
    text_partials: list[str] = []
    for event in core.send_request_stream(session, config):
        if event["type"] == "partial":
            metadata = (event.get("message") or {}).get("metadata") or {}
            reasoning = metadata.get("reasoning")
            if isinstance(reasoning, str) and reasoning:
                reasoning_partials.append(reasoning)
            text = (event.get("message") or {}).get("content")
            if isinstance(text, str) and text:
                text_partials.append(text)
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert reasoning_partials == ["Considering options. "]
    assert text_partials == ["STREAM_REASONING_OK"]
    assert final_message is not None
    assert final_message["content"] == "STREAM_REASONING_OK"
    metadata = final_message["metadata"]
    assert metadata["reasoning"] == "Considering options."
    raw_reasoning = metadata["openai_responses_reasoning"]
    assert raw_reasoning["summary_text"] == "Considering options."
    assert raw_reasoning["items"][0]["type"] == "reasoning"


def _effort_options(elements: list[dict[str, Any]]) -> list[str]:
    effort = next(
        element for element in elements if element.get("key") == "reasoning_effort"
    )
    return [option["value"] for option in effort["options"]]


def test_get_config_schema_includes_max_and_ultra() -> None:
    ext = OpenAIResponsesReasoningExtension()

    schema = ext.get_config_schema()
    effort_enum = schema["reasoning_effort"]["enum"]

    assert "max" in effort_enum
    assert "ultra" in effort_enum
    assert effort_enum == [
        "none",
        "minimal",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    ]


def test_get_ui_elements_gpt_5_6_sol_options() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    assert _effort_options(elements) == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    ]


def test_get_ui_elements_gpt_5_6_terra_options() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-terra"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-terra"}],
    )

    assert _effort_options(elements) == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    ]


def test_get_ui_elements_gpt_5_6_luna_options_exclude_ultra() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-luna"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-luna"}],
    )

    assert _effort_options(elements) == ["low", "medium", "high", "xhigh", "max"]


def test_get_ui_elements_bare_gpt_5_6_alias_maps_to_sol_options() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6"}],
    )

    assert _effort_options(elements) == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    ]


def test_get_ui_elements_older_models_unchanged() -> None:
    ext = OpenAIResponsesReasoningExtension()

    gpt5 = ext.get_ui_elements(
        config={"model": "gpt-5-mini"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5-mini"}],
    )
    gpt51 = ext.get_ui_elements(
        config={"model": "gpt-5.1-mini"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.1-mini"}],
    )
    gpt52 = ext.get_ui_elements(
        config={"model": "gpt-5.2"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.2"}],
    )
    gpt54 = ext.get_ui_elements(
        config={"model": "gpt-5.4"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.4"}],
    )
    gpt5pro = ext.get_ui_elements(
        config={"model": "gpt-5-pro"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5-pro"}],
    )
    unknown = ext.get_ui_elements(
        config={"model": "o3-mini"},
        tags=["supports_reasoning"],
        models=[{"id": "o3-mini"}],
    )

    assert _effort_options(gpt5) == ["minimal", "low", "medium", "high"]
    assert _effort_options(gpt51) == ["none", "low", "medium", "high"]
    assert _effort_options(gpt52) == ["none", "low", "medium", "high", "xhigh"]
    assert _effort_options(gpt54) == ["none", "low", "medium", "high", "xhigh"]
    assert _effort_options(gpt5pro) == ["high"]
    assert _effort_options(unknown) == [
        "none",
        "minimal",
        "low",
        "medium",
        "high",
        "xhigh",
    ]


def test_init_drops_ultra_for_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


def test_init_drops_max_for_unknown_model() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "o3-mini",
        "reasoning_effort": "max",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


def test_initialize_request_injects_max_for_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_effort": "max",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "max"}


def test_initialize_request_injects_ultra_for_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "ultra"}


def test_initialize_request_injects_ultra_for_terra() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-terra",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "ultra"}


def test_initialize_request_injects_ultra_for_bare_gpt_5_6_alias() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "ultra"}


def test_initialize_request_preserves_unrelated_existing_reasoning_fields() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_effort": "max",
        "reasoning_summary": "concise",
        "request_options": {
            "reasoning": {
                "summary": "auto",
                "generate_summary": True,
            },
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["effort"] == "max"
    assert reasoning["summary"] == "concise"
    assert reasoning["generate_summary"] is True


def test_initialize_request_config_effort_overrides_request_options_effort() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_effort": "max",
        "request_options": {
            "reasoning": {"effort": "low"},
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["effort"] == "max"
