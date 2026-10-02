from __future__ import annotations

from typing import Any, Dict

import pytest

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_fast_mode_extension import (
    OpenAIResponsesFastModeExtension,
)
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
    assert schema["show_reasoning_context_footer"]["default"] is True
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
        assert effort["icon"] == "sliders"
        assert effort["rich_ui"] == {
            "kind": "dropdown",
            "label": "Reasoning effort",
            "show_label": False,
            "show_icon": False,
            "options": effort["options"],
            "placements": ["composer"],
            "default_pinned": True,
        }
        assert all(option["label"] == option["value"] for option in effort["options"])
        assert all(
            "icon" not in option and "tone" not in option
            for option in effort["options"]
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


def test_get_ui_elements_gpt_6_astra_options() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-6-astra"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-6-astra"}],
    )

    assert _effort_options(elements) == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    ]


def test_get_ui_elements_gpt_61_sol_options() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-6.1-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-6.1-sol"}],
    )

    assert _effort_options(elements) == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    ]


def test_gpt_61_sol_offers_pro_mode_and_context() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-6.1-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-6.1-sol"}],
    )

    keys = [element.get("key") for element in elements]
    assert "reasoning_mode" in keys
    assert "reasoning_context" in keys


def test_initialize_request_injects_ultra_for_gpt_61_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-6.1-sol",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "ultra"}


def test_get_ui_elements_gpt_6_sol_options_match_astra() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-6-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-6-sol"}],
    )

    assert _effort_options(elements) == [
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
        "ultra",
    ]


def test_get_ui_elements_gpt_6_luna_options_exclude_ultra() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-6-luna"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-6-luna"}],
    )

    assert _effort_options(elements) == ["low", "medium", "high", "xhigh", "max"]


def test_gpt_6_sol_and_luna_offer_pro_mode_and_context() -> None:
    """The GPT-6 family shares the gated effort tuples, so Pro reasoning
    mode and reasoning context are offered for gpt-6-sol (and, through its
    low-through-max tuple, gpt-6-luna) as well."""
    ext = OpenAIResponsesReasoningExtension()

    for model in ("gpt-6-sol", "gpt-6-luna"):
        elements = ext.get_ui_elements(
            config={"model": model},
            tags=["supports_reasoning"],
            models=[{"id": model}],
        )

        keys = [element.get("key") for element in elements]
        assert "reasoning_mode" in keys, model
        assert "reasoning_context" in keys, model


def test_get_ui_elements_gpt_6_astra_offers_pro_mode_and_context() -> None:
    """gpt-6-astra shares the GPT-5.6 effort set, so Pro reasoning mode and
    reasoning context are offered for it as well."""
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-6-astra"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-6-astra"}],
    )

    keys = [element.get("key") for element in elements]
    assert "reasoning_mode" in keys
    assert "reasoning_context" in keys


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


def test_initialize_request_injects_ultra_for_gpt_6_astra() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-6-astra",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "ultra"}


def test_initialize_request_injects_ultra_for_gpt_6_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-6-sol",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "ultra"}


def test_init_drops_ultra_for_gpt_6_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-6-luna",
        "reasoning_effort": "ultra",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


def test_initialize_request_injects_max_for_gpt_6_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-6-luna",
        "reasoning_effort": "max",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["reasoning"] == {"effort": "max"}


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


# ---------------------------------------------------------------------------
# Pro reasoning mode (reasoning_mode / reasoning.mode) — task 030
# ---------------------------------------------------------------------------


def _reasoning_mode_elements(
    elements: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for element in elements:
        if element.get("key") == "reasoning_mode":
            return element
    return None


def test_get_config_schema_includes_reasoning_mode_pro_enum() -> None:
    ext = OpenAIResponsesReasoningExtension()

    schema = ext.get_config_schema()
    mode_entry = schema["reasoning_mode"]

    assert mode_entry["type"] == "string"
    assert mode_entry["required"] is False
    assert mode_entry["enum"] == ["pro"]


def test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    mode_element = _reasoning_mode_elements(elements)
    assert mode_element is not None
    assert mode_element["type"] == "select"
    assert mode_element["label"] == "Reasoning Mode"
    assert mode_element["options"] == [{"value": "pro", "label": "pro"}]


def test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-luna"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-luna"}],
    )

    mode_element = _reasoning_mode_elements(elements)
    assert mode_element is not None
    assert mode_element["options"] == [{"value": "pro", "label": "pro"}]


def test_get_ui_elements_shows_reasoning_mode_for_bare_gpt_5_6_alias() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6"}],
    )

    mode_element = _reasoning_mode_elements(elements)
    assert mode_element is not None
    assert mode_element["options"] == [{"value": "pro", "label": "pro"}]


def test_get_ui_elements_hides_reasoning_mode_for_older_models() -> None:
    ext = OpenAIResponsesReasoningExtension()

    for model in (
        "gpt-5-mini",
        "gpt-5.1-mini",
        "gpt-5.2",
        "gpt-5.4",
        "gpt-5-pro",
        "o3-mini",
    ):
        elements = ext.get_ui_elements(
            config={"model": model},
            tags=["supports_reasoning"],
            models=[{"id": model}],
        )
        assert (
            _reasoning_mode_elements(elements) is None
        ), f"reasoning_mode should not appear for {model}"


def test_get_ui_elements_hides_reasoning_mode_without_supports_reasoning_tag() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol"},
        tags=["openai_responses"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    assert elements == []
    assert _reasoning_mode_elements(elements) is None


def test_get_ui_elements_shows_reasoning_mode_for_api_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol", "auth_mode": "api"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    mode_element = _reasoning_mode_elements(elements)
    assert mode_element is not None
    assert mode_element["options"] == [{"value": "pro", "label": "pro"}]


def test_get_ui_elements_shows_reasoning_mode_for_auto_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol", "auth_mode": "auto"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    mode_element = _reasoning_mode_elements(elements)
    assert mode_element is not None
    assert mode_element["options"] == [{"value": "pro", "label": "pro"}]


def test_get_ui_elements_shows_reasoning_mode_for_default_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    mode_element = _reasoning_mode_elements(elements)
    assert mode_element is not None
    assert mode_element["options"] == [{"value": "pro", "label": "pro"}]


def test_get_ui_elements_shows_reasoning_mode_for_api_key_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol", "auth_mode": "api_key"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    mode_element = _reasoning_mode_elements(elements)
    assert mode_element is not None
    assert mode_element["options"] == [{"value": "pro", "label": "pro"}]


def test_get_ui_elements_hides_reasoning_mode_for_chatgpt_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol", "auth_mode": "chatgpt"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    assert _reasoning_mode_elements(elements) is None


def test_init_drops_reasoning_mode_pro_for_gpt_5_4() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.4",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


def test_init_drops_reasoning_mode_pro_for_unknown_model() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "o3-mini",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


def test_init_preserves_reasoning_mode_pro_for_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})

    reasoning = state["_openai_responses_reasoning"]
    assert reasoning["mode"] == "pro"


def test_init_drops_reasoning_mode_pro_for_chatgpt_effective_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "auth_mode": "chatgpt",
        "_openai_responses_effective_auth_mode": "chatgpt",
        "reasoning_mode": "pro",
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
    }

    state = ext.init(config, {"config": config})

    reasoning = state.get("_openai_responses_reasoning")
    assert isinstance(reasoning, dict)
    assert "mode" not in reasoning
    assert reasoning["effort"] == "medium"
    assert reasoning["summary"] == "concise"


def test_init_preserves_reasoning_mode_pro_for_api_effective_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "auth_mode": "api",
        "_openai_responses_effective_auth_mode": "api",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})

    reasoning = state["_openai_responses_reasoning"]
    assert reasoning["mode"] == "pro"


def test_init_drops_reasoning_mode_pro_for_auto_resolving_to_chatgpt() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "auth_mode": "auto",
        "_openai_responses_effective_auth_mode": "chatgpt",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})

    # When pro mode is the only reasoning config and it is dropped, the
    # reasoning state is absent entirely (normalize returns None).
    reasoning = state.get("_openai_responses_reasoning")
    if reasoning is not None:
        assert isinstance(reasoning, dict)
        assert "mode" not in reasoning
    else:
        assert "_openai_responses_reasoning" not in state


def test_init_preserves_reasoning_mode_pro_for_auto_resolving_to_api() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "auth_mode": "auto",
        "_openai_responses_effective_auth_mode": "api",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})

    reasoning = state["_openai_responses_reasoning"]
    assert reasoning["mode"] == "pro"


def test_init_preserves_effort_and_summary_for_chatgpt_auth() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "auth_mode": "chatgpt",
        "_openai_responses_effective_auth_mode": "chatgpt",
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})

    reasoning = state["_openai_responses_reasoning"]
    assert reasoning["effort"] == "medium"
    assert reasoning["summary"] == "concise"
    assert "mode" not in reasoning


def test_initialize_request_injects_pro_mode_for_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "pro"


def test_initialize_request_injects_pro_mode_for_terra() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-terra",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "pro"


def test_initialize_request_injects_pro_mode_for_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "pro"


def test_initialize_request_injects_pro_mode_for_bare_gpt_5_6_alias() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "pro"


def test_initialize_request_pro_mode_composes_with_effort_and_summary() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_mode": "pro",
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning == {
        "mode": "pro",
        "effort": "medium",
        "summary": "concise",
    }


def test_initialize_request_pro_mode_preserves_unrelated_existing_reasoning_fields() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_mode": "pro",
        "reasoning_summary": "concise",
        "request_options": {
            "reasoning": {
                "summary": "auto",
                "generate_summary": True,
                "mode": "standard",
            },
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "pro"
    assert reasoning["summary"] == "concise"
    assert reasoning["generate_summary"] is True


def test_initialize_request_omits_mode_when_reasoning_mode_unset() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning == {"effort": "medium"}
    assert "mode" not in reasoning


def test_initialize_request_does_not_send_standard_mode() -> None:
    ext = OpenAIResponsesReasoningExtension()

    for model in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.6"):
        for reasoning_mode in (None, "pro", "standard"):
            config = {
                **_base_state()["config"],
                "model": model,
            }
            if reasoning_mode is not None:
                config["reasoning_mode"] = reasoning_mode

            state = ext.init(config, {"config": config})
            if "_openai_responses_reasoning" not in state:
                continue
            _, new_state = ext.initialize_request([], state)
            reasoning = new_state["config"]["request_options"]["reasoning"]
            assert reasoning.get("mode") != "standard", (
                f"extension must never send mode=standard for {model} "
                f"with reasoning_mode={reasoning_mode!r}"
            )


def test_initialize_request_config_reasoning_mode_overrides_request_options_mode() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_mode": "pro",
        "request_options": {
            "reasoning": {"mode": "standard"},
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "pro"


def test_initialize_request_preserves_raw_request_options_mode_when_config_unset() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "request_options": {
            "reasoning": {"mode": "pro"},
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "pro"


def test_initialize_request_preserves_raw_request_options_standard_mode_when_config_unset() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "request_options": {
            "reasoning": {"mode": "standard"},
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["mode"] == "standard"


def test_initialize_request_pro_mode_and_fast_mode_coexist() -> None:
    reasoning_ext = OpenAIResponsesReasoningExtension()
    fast_mode_ext = OpenAIResponsesFastModeExtension()
    request_options_feature = RequestOptionsFeature()

    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "auth_mode": "api",
        "_openai_responses_effective_auth_mode": "api",
        "reasoning_mode": "pro",
        "reasoning_effort": "medium",
        "enable_fast_mode": True,
    }
    state: Dict[str, Any] = {
        "config": config,
        "request": {"payload": {"model": "gpt-5.6-sol"}, "headers": {}},
    }

    state = reasoning_ext.init(config, state)
    state = fast_mode_ext.init(config, state)

    _, state = reasoning_ext.initialize_request([], state)
    _, state = fast_mode_ext.initialize_request([], state)
    _, state = request_options_feature.initialize_request([], state)

    payload = state["request"]["payload"]
    assert payload["service_tier"] == "fast"
    assert isinstance(payload.get("reasoning"), dict)
    assert payload["reasoning"]["mode"] == "pro"
    assert payload["reasoning"]["effort"] == "medium"


def test_initialize_request_pro_mode_dropped_for_chatgpt_while_fast_mode_applies() -> (
    None
):
    reasoning_ext = OpenAIResponsesReasoningExtension()
    fast_mode_ext = OpenAIResponsesFastModeExtension()
    request_options_feature = RequestOptionsFeature()

    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "auth_mode": "chatgpt",
        "_openai_responses_effective_auth_mode": "chatgpt",
        "reasoning_mode": "pro",
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
        "enable_fast_mode": True,
    }
    state: Dict[str, Any] = {
        "config": config,
        "request": {"payload": {"model": "gpt-5.6-sol"}, "headers": {}},
    }

    state = reasoning_ext.init(config, state)
    state = fast_mode_ext.init(config, state)

    _, state = reasoning_ext.initialize_request([], state)
    _, state = fast_mode_ext.initialize_request([], state)
    _, state = request_options_feature.initialize_request([], state)

    payload = state["request"]["payload"]
    # Fast mode still applies for ChatGPT auth; the ChatGPT backend only
    # accepts the legacy ``priority`` tier name.
    assert payload["service_tier"] == "priority"
    # Pro mode is dropped for ChatGPT auth; effort and summary are preserved.
    assert isinstance(payload.get("reasoning"), dict)
    assert "mode" not in payload["reasoning"]
    assert payload["reasoning"]["effort"] == "medium"
    assert payload["reasoning"]["summary"] == "concise"


# ---------------------------------------------------------------------------
# Reasoning context (reasoning_context / reasoning.context) — task 040
# ---------------------------------------------------------------------------


def _reasoning_context_elements(
    elements: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for element in elements:
        if element.get("key") == "reasoning_context":
            return element
    return None


def _context_footer_element(
    elements: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for element in elements:
        if (
            element.get("ui_type") == "message_footer"
            and element.get("data") == "metadata.openai_responses_reasoning.context"
        ):
            return element
    return None


def test_get_config_schema_includes_reasoning_context_enum() -> None:
    ext = OpenAIResponsesReasoningExtension()

    schema = ext.get_config_schema()
    context_entry = schema["reasoning_context"]

    assert context_entry["type"] == "string"
    assert context_entry["required"] is False
    assert context_entry["enum"] == ["auto", "current_turn", "all_turns"]


def test_get_ui_elements_shows_reasoning_context_for_gpt_5_6_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    context_element = _reasoning_context_elements(elements)
    assert context_element is not None
    assert context_element["type"] == "select"
    assert context_element["label"] == "Reasoning retention"
    assert context_element["options"] == [
        {"value": "auto", "label": "Auto"},
        {"value": "current_turn", "label": "Current turn only"},
        {"value": "all_turns", "label": "All turns"},
    ]


def test_get_ui_elements_shows_reasoning_context_for_gpt_5_6_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-luna"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-luna"}],
    )

    context_element = _reasoning_context_elements(elements)
    assert context_element is not None
    assert context_element["options"] == [
        {"value": "auto", "label": "Auto"},
        {"value": "current_turn", "label": "Current turn only"},
        {"value": "all_turns", "label": "All turns"},
    ]


def test_get_ui_elements_shows_reasoning_context_for_bare_gpt_5_6_alias() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6"}],
    )

    context_element = _reasoning_context_elements(elements)
    assert context_element is not None


@pytest.mark.parametrize(
    "model",
    [
        "gpt-5.10-preview",
        "gpt-6-astra",
        "gpt-6.1-custom",
        "gpt-10-next",
    ],
)
def test_get_ui_elements_shows_reasoning_context_for_future_numeric_gpt_models(
    model: str,
) -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": model},
        tags=["supports_reasoning"],
        models=[{"id": model}],
    )

    context_element = _reasoning_context_elements(elements)
    assert context_element is not None
    assert context_element["label"] == "Reasoning retention"


def test_get_ui_elements_hides_reasoning_context_for_older_models() -> None:
    ext = OpenAIResponsesReasoningExtension()

    for model in (
        "gpt-5-mini",
        "gpt-5.1-mini",
        "gpt-5.2",
        "gpt-5.4",
        "gpt-5.5",
        "gpt-5-pro",
        "o3-mini",
    ):
        elements = ext.get_ui_elements(
            config={"model": model},
            tags=["supports_reasoning"],
            models=[{"id": model}],
        )
        assert (
            _reasoning_context_elements(elements) is None
        ), f"reasoning_context should not appear for {model}"


def test_get_ui_elements_includes_context_footer() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    footer = _context_footer_element(elements)
    assert footer is not None
    assert footer["ui_type"] == "message_footer"
    assert footer["data"] == "metadata.openai_responses_reasoning.context"
    assert footer["template"] == "context: {{data}}"
    assert footer["condition"] == {
        "path": "metadata.openai_responses_reasoning.context",
        "exists": True,
    }


def test_get_ui_elements_can_hide_context_footer() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={
            "model": "gpt-5.6-luna",
            "show_reasoning_context_footer": False,
        },
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-luna"}],
    )

    assert _reasoning_context_elements(elements) is not None
    assert _context_footer_element(elements) is None


def test_get_ui_elements_context_footer_present_for_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-luna"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-luna"}],
    )

    assert _context_footer_element(elements) is not None


def test_get_ui_elements_context_footer_present_for_older_models() -> None:
    ext = OpenAIResponsesReasoningExtension()

    # The footer element definition is unconditional (not model-gated) because
    # the ``condition`` handles per-message visibility. It should appear in the
    # element list for all models, but only render when the metadata path
    # exists.
    for model in ("gpt-5-mini", "o3-mini"):
        elements = ext.get_ui_elements(
            config={"model": model},
            tags=["supports_reasoning"],
            models=[{"id": model}],
        )
        assert (
            _context_footer_element(elements) is not None
        ), f"context footer should be defined for {model}"


def test_get_ui_elements_context_footer_distinct_from_config_selects() -> None:
    ext = OpenAIResponsesReasoningExtension()

    elements = ext.get_ui_elements(
        config={"model": "gpt-5.6-sol"},
        tags=["supports_reasoning"],
        models=[{"id": "gpt-5.6-sol"}],
    )

    context_select = _reasoning_context_elements(elements)
    footer = _context_footer_element(elements)
    assert context_select is not None
    assert footer is not None
    assert context_select.get("type") == "select"
    assert footer.get("ui_type") == "message_footer"
    # The select has no ui_type (defaults to "config"); the footer has no "type".
    assert "ui_type" not in context_select
    assert "type" not in footer


def test_init_drops_reasoning_context_for_gpt_5_4() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.4",
        "reasoning_context": "all_turns",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


def test_init_drops_reasoning_context_for_unknown_model() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "o3-mini",
        "reasoning_context": "all_turns",
    }

    state = ext.init(config, {"config": config})

    assert "_openai_responses_reasoning" not in state


@pytest.mark.parametrize("model", ["gpt-5.10-preview", "gpt-6-astra", "gpt-10-next"])
def test_init_preserves_reasoning_context_for_future_numeric_gpt_models(
    model: str,
) -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": model,
        "reasoning_context": "all_turns",
    }

    state = ext.init(config, {"config": config})

    assert state["_openai_responses_reasoning"]["context"] == "all_turns"


def test_init_normalizes_auto_to_omission() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "auto",
    }

    state = ext.init(config, {"config": config})

    # ``auto`` normalizes to omission: no ``context`` key in the reasoning
    # state. The state itself may be empty (no reasoning config at all) or
    # may contain other reasoning fields, but must not contain ``context``.
    reasoning = state.get("_openai_responses_reasoning")
    if reasoning is not None:
        assert "context" not in reasoning


def test_init_preserves_current_turn_for_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_context": "current_turn",
    }

    state = ext.init(config, {"config": config})

    reasoning = state["_openai_responses_reasoning"]
    assert reasoning["context"] == "current_turn"


def test_init_preserves_all_turns_for_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
    }

    state = ext.init(config, {"config": config})

    reasoning = state["_openai_responses_reasoning"]
    assert reasoning["context"] == "all_turns"


def test_init_drops_invalid_reasoning_context_value() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "later",
    }

    state = ext.init(config, {"config": config})

    reasoning = state.get("_openai_responses_reasoning")
    if reasoning is not None:
        assert "context" not in reasoning


def test_initialize_request_injects_context_all_turns_for_sol() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["context"] == "all_turns"


def test_initialize_request_injects_context_current_turn_for_luna() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-luna",
        "reasoning_context": "current_turn",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["context"] == "current_turn"


def test_initialize_request_context_composes_with_effort_summary_and_mode() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
        "reasoning_mode": "pro",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning == {
        "context": "all_turns",
        "effort": "medium",
        "summary": "concise",
        "mode": "pro",
    }


def test_initialize_request_auto_context_omits_wire_field() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "auto",
        "reasoning_effort": "medium",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning == {"effort": "medium"}
    assert "context" not in reasoning


def test_initialize_request_context_preserves_unrelated_existing_reasoning_fields() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
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
    assert reasoning["context"] == "all_turns"
    assert reasoning["summary"] == "concise"
    assert reasoning["generate_summary"] is True


def test_initialize_request_config_context_overrides_request_options_context() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
        "request_options": {
            "reasoning": {"context": "current_turn"},
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["context"] == "all_turns"


def test_initialize_request_preserves_raw_request_options_context_when_config_unset() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "request_options": {
            "reasoning": {"context": "all_turns"},
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    assert reasoning["context"] == "all_turns"


def test_initialize_request_auto_context_does_not_override_raw_context() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "auto",
        "request_options": {
            "reasoning": {"context": "all_turns"},
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    reasoning = new_state["config"]["request_options"]["reasoning"]
    # ``auto`` normalizes to omission, so the raw expert escape hatch is
    # preserved (config does not clobber raw when config normalizes to
    # omission).
    assert reasoning["context"] == "all_turns"


def test_initialize_request_context_all_turns_keeps_encrypted_content_include() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    include = new_state["config"]["request_options"]["include"]
    assert "reasoning.encrypted_content" in include
    assert include.count("reasoning.encrypted_content") == 1


def test_initialize_request_context_all_turns_preserves_raw_include_values() -> None:
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
        "request_options": {
            "include": ["message.input_image.image_url"],
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    include = new_state["config"]["request_options"]["include"]
    assert include == ["message.input_image.image_url", "reasoning.encrypted_content"]


def test_initialize_request_context_all_turns_preserves_unrelated_request_options() -> (
    None
):
    ext = OpenAIResponsesReasoningExtension()
    config = {
        **_base_state()["config"],
        "model": "gpt-5.6-sol",
        "reasoning_context": "all_turns",
        "request_options": {
            "temperature": 0.2,
            "top_p": 0.9,
        },
    }

    state = ext.init(config, {"config": config})
    _, new_state = ext.initialize_request([], state)

    request_options = new_state["config"]["request_options"]
    assert request_options["temperature"] == 0.2
    assert request_options["top_p"] == 0.9
    assert request_options["reasoning"]["context"] == "all_turns"


def test_from_native_messages_extracts_effective_context_from_reasoning_item_metadata() -> (
    None
):
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesReasoningExtension()

    native_messages = [
        {
            "type": "reasoning",
            "id": "rs_ctx_1",
            "summary": [{"type": "summary_text", "text": "Used internal reasoning."}],
            "content": None,
            "encrypted_content": "enc_blob_1",
            "status": None,
            "_metadata": {
                "response_id": "resp_ctx_1",
                "_openai_responses_reasoning_context": "all_turns",
            },
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Done."}],
            "_metadata": {
                "response_id": "resp_ctx_1",
                "_openai_responses_reasoning_context": "all_turns",
            },
        },
    ]

    core_messages = provider.from_native_messages(native_messages, {})
    enriched = ext.from_native_messages(native_messages, core_messages)

    metadata = enriched[-1]["metadata"]
    assert metadata["openai_responses_reasoning"]["context"] == "all_turns"


def test_from_native_messages_extracts_effective_context_from_message_item_metadata() -> (
    None
):
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesReasoningExtension()

    # Response with no reasoning items but an effective context reported on
    # the message item's internal metadata.
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Simple response."}],
            "_metadata": {
                "response_id": "resp_ctx_2",
                "_openai_responses_reasoning_context": "current_turn",
            },
        },
    ]

    core_messages = provider.from_native_messages(native_messages, {})
    enriched = ext.from_native_messages(native_messages, core_messages)

    metadata = enriched[-1].get("metadata") or {}
    raw_reasoning = metadata.get("openai_responses_reasoning") or {}
    assert raw_reasoning.get("context") == "current_turn"


def test_from_native_messages_omits_context_when_response_does_not_report_it() -> None:
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesReasoningExtension()

    native_messages = [
        {
            "type": "reasoning",
            "id": "rs_no_ctx",
            "summary": [{"type": "summary_text", "text": "No context reported."}],
            "content": None,
            "encrypted_content": "enc_blob_no_ctx",
            "status": None,
            "_metadata": {"response_id": "resp_no_ctx"},
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Done."}],
            "_metadata": {"response_id": "resp_no_ctx"},
        },
    ]

    core_messages = provider.from_native_messages(native_messages, {})
    enriched = ext.from_native_messages(native_messages, core_messages)

    metadata = enriched[-1]["metadata"]
    assert "context" not in metadata["openai_responses_reasoning"]


def test_from_native_messages_context_survives_merge_across_segments() -> None:
    provider = OpenAIResponsesProvider()
    ext = OpenAIResponsesReasoningExtension()

    # Two response segments with different effective contexts. The merge
    # should use the latest non-empty value.
    native_messages = [
        {
            "type": "reasoning",
            "id": "rs_seg_1",
            "summary": [{"type": "summary_text", "text": "First reasoning."}],
            "content": None,
            "encrypted_content": "enc_seg_1",
            "status": None,
            "_metadata": {
                "response_id": "resp_seg_1",
                "_openai_responses_reasoning_context": "current_turn",
            },
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "First answer."}],
            "_metadata": {
                "response_id": "resp_seg_1",
                "_openai_responses_reasoning_context": "current_turn",
            },
        },
        {
            "type": "reasoning",
            "id": "rs_seg_2",
            "summary": [{"type": "summary_text", "text": "Second reasoning."}],
            "content": None,
            "encrypted_content": "enc_seg_2",
            "status": None,
            "_metadata": {
                "response_id": "resp_seg_2",
                "_openai_responses_reasoning_context": "all_turns",
            },
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Second answer."}],
            "_metadata": {
                "response_id": "resp_seg_2",
                "_openai_responses_reasoning_context": "all_turns",
            },
        },
    ]

    core_messages = provider.from_native_messages(native_messages, {})
    enriched = ext.from_native_messages(native_messages, core_messages)

    # The last assistant message should have the latest non-empty context.
    last_assistant = [m for m in enriched if m.get("role") == "assistant"][-1]
    metadata = last_assistant["metadata"]
    assert metadata["openai_responses_reasoning"]["context"] == "all_turns"
