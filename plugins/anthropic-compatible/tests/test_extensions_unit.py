from __future__ import annotations

from anthropic_plugins.reasoning_extension import AnthropicReasoningExtension
from anthropic_plugins.tools_extension import AnthropicToolsExtension
from anthropic_plugins.usage_extension import AnthropicUsageExtension


def _base_state() -> dict:
    return {
        "config": {},
        "request": {"payload": {"model": "m", "messages": []}},
        "accumulator": None,
    }


def test_extensions_have_separate_identity_and_provider_requirements() -> None:
    assert AnthropicToolsExtension().name == "anthropic_tools"
    assert AnthropicReasoningExtension().name == "anthropic_reasoning"
    assert AnthropicUsageExtension().name == "anthropic_usage"
    assert "provider:anthropic" in AnthropicToolsExtension().required_tags()
    assert "provider:anthropic" in AnthropicReasoningExtension().required_tags()
    assert "provider:anthropic" in AnthropicUsageExtension().required_tags()


def test_tools_extension_injects_anthropic_schema() -> None:
    extension = AnthropicToolsExtension()
    state = extension.init(
        {
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "echo",
                        "description": "Echo",
                        "parameters": {
                            "type": "object",
                            "properties": {"value": {"type": "string"}},
                        },
                    },
                }
            ]
        },
        _base_state(),
    )

    _native, state = extension.initialize_request([], state)

    assert state["request"]["payload"]["tools"] == [
        {
            "name": "echo",
            "description": "Echo",
            "input_schema": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
            },
        }
    ]


def test_tools_extension_contributes_anthropic_call_accessor() -> None:
    contribution = AnthropicToolsExtension().get_tool_interop_contribution({})
    accessor = contribution.call_accessors[0]

    inspected = {
        "type": "tool_use",
        "id": "call_1",
        "name": "echo",
        "input": {"value": "x"},
    }

    assert accessor.can_handle(inspected)
    assert accessor.get_call_id(inspected) == "call_1"
    assert accessor.get_tool_name(inspected) == "echo"


def test_tools_extension_maps_calls_and_results() -> None:
    extension = AnthropicToolsExtension()
    assistant_native = {
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "call_1",
                "name": "echo",
                "input": {"value": "x"},
            }
        ],
    }
    assistant = {"role": "assistant", "content": "", "metadata": {}}

    rebuilt = extension.from_native_messages([assistant_native], [assistant])
    assert rebuilt[0]["metadata"]["tool_calls"][0]["id"] == "call_1"

    tool = {
        "role": "tool",
        "content": "x",
        "metadata": {"tool_call_id": "call_1", "display": {"type": "text"}},
    }
    native = extension.to_native_messages([tool], [{"role": "tool", "content": "x"}])
    assert native[0]["role"] == "user"
    assert native[0]["content"][0] == {
        "type": "tool_result",
        "tool_use_id": "call_1",
        "content": "x",
    }
    assert native[0]["_metadata"]["display"] == {"type": "text"}


def test_tools_extension_does_not_double_wrap_native_tool_result() -> None:
    extension = AnthropicToolsExtension()
    tool = {
        "role": "tool",
        "content": "x",
        "metadata": {"tool_call_id": "call_1"},
        "toolResult": {
            "type": "provider_native_tool_result",
            "format": "anthropic.messages",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "call_1",
                    "content": [{"type": "text", "text": "x"}],
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "text": "x",
        },
    }

    native = extension.to_native_messages(
        [tool],
        [{"role": "tool", "content": "x", "toolResult": tool["toolResult"]}],
    )

    assert native[0]["content"] == [
        {
            "type": "tool_result",
            "tool_use_id": "call_1",
            "content": [{"type": "text", "text": "x"}],
            "cache_control": {"type": "ephemeral"},
        }
    ]


def test_reasoning_extension_has_no_request_config_or_ui_and_round_trips() -> None:
    extension = AnthropicReasoningExtension()
    assert extension.get_config_schema() == {}
    assert extension.get_ui_elements({}) == []
    state = extension.init(
        {"request_options": {"thinking": {"type": "adaptive"}}}, _base_state()
    )

    _native, state = extension.initialize_request([], state)

    assert state["request"]["payload"] == {"model": "m", "messages": []}

    native = {
        "role": "assistant",
        "content": [
            {"type": "thinking", "thinking": "consider", "signature": "sig"},
            {"type": "redacted_thinking", "data": "hidden"},
            {"type": "text", "text": "answer"},
        ],
    }
    core = {"role": "assistant", "content": "answer", "metadata": {}}
    rebuilt = extension.from_native_messages([native], [core])
    assert rebuilt[0]["metadata"]["reasoning"] == "consider"
    assert (
        rebuilt[0]["metadata"]["anthropic_reasoning_blocks"][:2]
        == native["content"][:2]
    )


def test_reasoning_stream_delta_is_chunk_local() -> None:
    extension = AnthropicReasoningExtension()
    partials, _, _, _ = extension.process_chunk(
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "thinking_delta", "thinking": "new"},
        },
        [{"role": "assistant", "content": ""}],
        [],
        [],
        _base_state(),
    )
    assert partials[0]["_metadata"]["reasoning"] == "new"


def test_reasoning_always_surfaces_visible_text_and_preserves_native_blocks() -> None:
    extension = AnthropicReasoningExtension()
    native = {
        "role": "assistant",
        "content": [
            {"type": "thinking", "thinking": "private", "signature": "sig"},
            {"type": "text", "text": "answer"},
        ],
    }
    message = {"role": "assistant", "content": "answer", "metadata": {}}

    rebuilt = extension.from_native_messages([native], [message], _base_state())

    assert rebuilt[0]["metadata"]["reasoning"] == "private"
    assert rebuilt[0]["metadata"]["anthropic_reasoning_blocks"][0]["signature"] == "sig"


def test_usage_extension_formats_turn_and_session_totals() -> None:
    extension = AnthropicUsageExtension()
    prior = {
        "role": "assistant",
        "content": [{"type": "text", "text": "first"}],
        "_metadata": {"anthropic_usage": {"input_tokens": 10, "output_tokens": 4}},
    }
    tool_result = {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "c", "content": "ok"}],
        "_metadata": {"core_role": "tool"},
    }
    final = {
        "role": "assistant",
        "content": [{"type": "text", "text": "second"}],
        "_metadata": {
            "anthropic_usage": {
                "input_tokens": 20,
                "output_tokens": 5,
                "cache_read_input_tokens": 7,
                "cache_creation_input_tokens": 3,
                "output_tokens_details": {"thinking_tokens": 2},
            }
        },
    }
    state = extension.init({}, _base_state())

    finals, history, _state = extension.finalize(
        [final], [prior, tool_result, final], state
    )
    metadata = finals[0]["_metadata"]

    assert metadata["usage_prompt_tokens"] == 20
    assert metadata["usage_cached_tokens"] == 7
    assert metadata["usage_cache_write_tokens"] == 3
    assert metadata["usage_reasoning_tokens"] == 2
    assert metadata["usage_turn_input_tokens_cumulative"] == 30
    assert metadata["usage_turn_output_tokens_cumulative"] == 9
    assert metadata["usage_input_tokens_cumulative"] == 30
    assert history[-1]["_metadata"]["usage_prompt_tokens_formatted"] == "20"
    assert metadata["turn"] == {
        "id": 1,
        "has_tool_calls": False,
        "is_terminal": True,
    }


def test_usage_extension_keeps_one_turn_id_across_tool_generations() -> None:
    extension = AnthropicUsageExtension()
    user = {"role": "user", "content": "add"}
    tool_call = {
        "role": "assistant",
        "content": [{"type": "tool_use", "id": "tool_1", "name": "add", "input": {}}],
        "_metadata": {"anthropic_usage": {"input_tokens": 5, "output_tokens": 2}},
    }
    tool_result = {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "tool_1", "content": "5"}],
        "_metadata": {"core_role": "tool"},
    }
    final = {
        "role": "assistant",
        "content": [{"type": "text", "text": "5"}],
        "_metadata": {"anthropic_usage": {"input_tokens": 8, "output_tokens": 1}},
    }

    first_finals, first_history, _state = extension.finalize(
        [tool_call],
        [user, tool_call],
        {"anthropic_usage": {"raw": tool_call["_metadata"]["anthropic_usage"]}},
    )
    second_finals, _history, _state = extension.finalize(
        [final],
        [*first_history, tool_result, final],
        {"anthropic_usage": {"raw": final["_metadata"]["anthropic_usage"]}},
    )

    first_turn = first_finals[-1]["_metadata"]["turn"]
    second_metadata = second_finals[-1]["_metadata"]
    assert first_turn == {"id": 1, "has_tool_calls": True, "is_terminal": False}
    assert second_metadata["turn"] == {
        "id": 1,
        "has_tool_calls": False,
        "is_terminal": True,
    }
    assert second_metadata["usage_turn_input_tokens_cumulative"] == 13
    assert second_metadata["usage_turn_output_tokens_cumulative"] == 3


def test_usage_ui_can_be_hidden_without_disabling_accounting() -> None:
    extension = AnthropicUsageExtension()
    assert extension.get_ui_elements({"show_usage": False}) == []
