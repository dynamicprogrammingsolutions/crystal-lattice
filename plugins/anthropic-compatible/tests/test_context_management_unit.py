from __future__ import annotations

from typing import Any

import pytest

from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicCompactionExtension,
    AnthropicContextEditingExtension,
    AnthropicProvider,
    AnthropicUsageExtension,
)
from anthropic_plugins.content_blocks import reduce_event
from anthropic_plugins.context_management import (
    COMPACTION_BETA,
    CONTEXT_EDITING_BETA,
    REQUEST_REQUIRED_BETAS_KEY,
)


def _state(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "config": config,
        "request": {"payload": {"model": "m", "messages": []}},
    }


def _model(
    model_id: str,
    *,
    compaction: bool,
    clear_thinking: bool,
    clear_tools: bool,
) -> dict[str, Any]:
    return {
        "id": model_id,
        "capabilities": {
            "context_management": {
                "supported": compaction or clear_thinking or clear_tools,
                "compact_20260112": {"supported": compaction},
                "clear_thinking_20251015": {"supported": clear_thinking},
                "clear_tool_uses_20250919": {"supported": clear_tools},
            }
        },
    }


def test_provider_context_management_tags_follow_selected_model_capabilities() -> None:
    provider = AnthropicProvider()
    models = [
        _model(
            "claude-sonnet-5",
            compaction=True,
            clear_thinking=True,
            clear_tools=True,
        ),
        _model(
            "claude-haiku-4-5-20251001",
            compaction=False,
            clear_thinking=True,
            clear_tools=True,
        ),
    ]

    sonnet = provider.get_tags({"model": "claude-sonnet-5"}, models)
    haiku = provider.get_tags({"model": "claude-haiku-4-5-20251001"}, models)

    assert "supports_anthropic_compaction" in sonnet
    assert "supports_anthropic_context_editing" in sonnet
    assert "supports_anthropic_compaction" not in haiku
    assert "supports_anthropic_context_editing" in haiku


def test_explicit_context_capabilities_override_model_descriptors() -> None:
    provider = AnthropicProvider()
    models = [
        _model(
            "claude-sonnet-5",
            compaction=True,
            clear_thinking=True,
            clear_tools=True,
        )
    ]

    disabled = provider.get_tags(
        {
            "model": "claude-sonnet-5",
            "capabilities": {
                "anthropic_compaction": False,
                "anthropic_context_editing": False,
            },
        },
        models,
    )
    enabled = provider.get_tags(
        {
            "model": "compatible",
            "capabilities": {
                "anthropic_compaction": True,
                "anthropic_context_editing": True,
            },
        },
        [],
    )

    assert "supports_anthropic_compaction" not in disabled
    assert "supports_anthropic_context_editing" not in disabled
    assert "supports_anthropic_compaction" in enabled
    assert "supports_anthropic_context_editing" in enabled


def test_extensions_expose_independent_config_ui_and_required_tags() -> None:
    compaction = AnthropicCompactionExtension()
    editing = AnthropicContextEditingExtension()

    compaction_schema = compaction.get_config_schema()
    editing_schema = editing.get_config_schema()
    compaction_ui = {
        item["key"]: item
        for item in compaction.get_ui_elements({})
        if isinstance(item.get("key"), str)
    }
    editing_ui = {
        item["key"]: item
        for item in editing.get_ui_elements({})
        if isinstance(item.get("key"), str)
    }

    assert compaction_schema["enable_anthropic_compaction"]["default"] is False
    assert compaction_schema["anthropic_compaction_trigger_tokens"]["minimum"] == 50000
    assert compaction_ui["enable_anthropic_compaction"]["type"] == "checkbox"
    assert compaction_ui["anthropic_compaction_trigger_tokens"]["type"] == "number"
    assert "anthropic_compaction_instructions" not in compaction_ui
    assert "supports_anthropic_compaction" in compaction.required_tags()
    assert editing_schema["anthropic_thinking_retention"]["enum"] == [
        "provider_default",
        "all",
        "turns",
    ]
    assert editing_ui["anthropic_thinking_retention"]["type"] == "select"
    assert editing_ui["enable_anthropic_tool_use_clearing"]["type"] == "checkbox"
    assert editing_ui["anthropic_tool_use_clear_trigger_tokens"]["type"] == "number"
    assert editing_ui["anthropic_tool_uses_to_keep"]["type"] == "number"
    assert "anthropic_thinking_turns_to_keep" not in editing_ui
    assert "anthropic_clear_tool_inputs" not in editing_ui
    assert "supports_anthropic_context_editing" in editing.required_tags()


def test_context_editing_ui_describes_configured_recent_turn_count() -> None:
    editing = AnthropicContextEditingExtension()

    latest = editing.get_ui_elements({"anthropic_thinking_turns_to_keep": 1})
    latest_retention = next(
        item for item in latest if item.get("key") == "anthropic_thinking_retention"
    )
    assert latest_retention["options"][-1] == {
        "value": "turns",
        "label": "Keep latest turn",
    }

    recent = editing.get_ui_elements({"anthropic_thinking_turns_to_keep": 3})
    recent_retention = next(
        item for item in recent if item.get("key") == "anthropic_thinking_retention"
    )
    assert recent_retention["options"][-1] == {
        "value": "turns",
        "label": "Keep latest 3 turns",
    }


def test_context_editing_then_compaction_compose_ordered_edits_and_betas() -> None:
    config = {
        "anthropic_thinking_retention": "turns",
        "anthropic_thinking_turns_to_keep": 2,
        "enable_anthropic_tool_use_clearing": True,
        "anthropic_tool_use_clear_trigger_tokens": 12000,
        "anthropic_tool_uses_to_keep": 4,
        "anthropic_tool_use_clear_at_least_tokens": 2500,
        "anthropic_clear_tool_inputs": True,
        "anthropic_tool_use_excluded_tools": ["read_file"],
        "enable_anthropic_compaction": True,
        "anthropic_compaction_trigger_tokens": 50000,
        "anthropic_compaction_instructions": "Keep decisions.",
    }
    state = _state(config)

    _native, state = AnthropicContextEditingExtension().initialize_request([], state)
    _native, state = AnthropicCompactionExtension().initialize_request([], state)

    assert state["request"]["payload"]["context_management"]["edits"] == [
        {
            "type": "clear_thinking_20251015",
            "keep": {"type": "thinking_turns", "value": 2},
        },
        {
            "type": "clear_tool_uses_20250919",
            "trigger": {"type": "input_tokens", "value": 12000},
            "keep": {"type": "tool_uses", "value": 4},
            "clear_tool_inputs": True,
            "clear_at_least": {"type": "input_tokens", "value": 2500},
            "exclude_tools": ["read_file"],
        },
        {
            "type": "compact_20260112",
            "trigger": {"type": "input_tokens", "value": 50000},
            "pause_after_compaction": False,
            "instructions": "Keep decisions.",
        },
    ]
    assert state["request"][REQUEST_REQUIRED_BETAS_KEY] == [
        CONTEXT_EDITING_BETA,
        COMPACTION_BETA,
    ]


def test_provider_composes_required_betas_and_validates_final_edit_types() -> None:
    provider = AnthropicProvider()
    payload = {
        "model": "m",
        "max_tokens": 8,
        "messages": [{"role": "user", "content": "hi"}],
        "context_management": {
            "edits": [
                {"type": "clear_thinking_20251015", "keep": "all"},
                {
                    "type": "compact_20260112",
                    "trigger": {"type": "input_tokens", "value": 50000},
                    "pause_after_compaction": False,
                },
            ]
        },
    }

    kwargs, use_beta = provider._request_kwargs(
        {},
        payload,
        stream=False,
        required_betas=[CONTEXT_EDITING_BETA, COMPACTION_BETA],
    )

    assert use_beta is True
    assert kwargs["betas"] == [CONTEXT_EDITING_BETA, COMPACTION_BETA]

    with pytest.raises(RuntimeError, match=COMPACTION_BETA):
        provider._request_kwargs(
            {"betas": [CONTEXT_EDITING_BETA]},
            payload,
            stream=False,
        )


def test_explicit_beta_header_remains_authoritative_and_is_validated() -> None:
    provider = AnthropicProvider()
    payload = {
        "model": "m",
        "max_tokens": 8,
        "messages": [{"role": "user", "content": "hi"}],
        "context_management": {
            "edits": [
                {
                    "type": "compact_20260112",
                    "trigger": {"type": "input_tokens", "value": 50000},
                    "pause_after_compaction": False,
                }
            ]
        },
        "extra_headers": {"anthropic-beta": CONTEXT_EDITING_BETA},
    }

    with pytest.raises(RuntimeError, match=COMPACTION_BETA):
        provider._request_kwargs(
            {},
            payload,
            stream=False,
            required_betas=[COMPACTION_BETA],
        )


def test_raw_request_options_replace_extension_context_management() -> None:
    config = {
        "anthropic_thinking_retention": "all",
        "enable_anthropic_compaction": True,
        "request_options": {
            "context_management": {
                "edits": [
                    {
                        "type": "compact_20260112",
                        "trigger": {"type": "input_tokens", "value": 70000},
                        "pause_after_compaction": False,
                    }
                ]
            }
        },
    }
    state = _state(config)

    _native, state = AnthropicContextEditingExtension().initialize_request([], state)
    _native, state = AnthropicCompactionExtension().initialize_request([], state)
    feature = RequestOptionsFeature()
    state = feature.init(config, state)
    _native, state = feature.initialize_request([], state)

    assert (
        state["request"]["payload"]["context_management"]
        == config["request_options"]["context_management"]
    )


def test_compaction_metadata_is_public_but_encrypted_content_is_not_copied() -> None:
    native = {
        "role": "assistant",
        "content": [
            {
                "type": "compaction",
                "content": "Summary",
                "encrypted_content": "opaque-secret",
            },
            {"type": "text", "text": "Answer"},
        ],
    }
    core = {"role": "assistant", "content": "Answer", "metadata": {}}

    rebuilt = AnthropicCompactionExtension().from_native_messages([native], [core])

    metadata = rebuilt[0]["metadata"]
    assert metadata["anthropic_compaction"] == {
        "occurred": True,
        "block_count": 1,
        "readable_summary_count": 1,
    }
    assert "opaque-secret" not in repr(metadata)


def test_context_editing_metadata_sums_applied_edits() -> None:
    native = {
        "role": "assistant",
        "content": [{"type": "text", "text": "Answer"}],
        "_metadata": {
            "anthropic": {
                "context_management": {
                    "applied_edits": [
                        {
                            "type": "clear_thinking_20251015",
                            "cleared_input_tokens": 100,
                            "cleared_thinking_turns": 2,
                        },
                        {
                            "type": "clear_tool_uses_20250919",
                            "cleared_input_tokens": 300,
                            "cleared_tool_uses": 4,
                        },
                    ]
                }
            }
        },
    }
    core = {"role": "assistant", "content": "Answer", "metadata": {}}

    rebuilt = AnthropicContextEditingExtension().from_native_messages([native], [core])

    assert rebuilt[0]["metadata"]["anthropic_context_editing"] == {
        "applied_edit_count": 2,
        "cleared_input_tokens": 400,
        "cleared_thinking_turns": 2,
        "cleared_tool_uses": 4,
    }


def test_stream_reducer_preserves_compaction_delta_and_applied_edits() -> None:
    accumulator = None
    events = [
        {
            "type": "message_start",
            "message": {"id": "msg", "model": "m", "content": []},
        },
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "compaction"},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "compaction_delta",
                "content": "Summary",
                "encrypted_content": "opaque",
            },
        },
        {"type": "content_block_stop", "index": 0},
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn"},
            "usage": {"output_tokens": 2},
            "context_management": {
                "applied_edits": [
                    {
                        "type": "clear_tool_uses_20250919",
                        "cleared_input_tokens": 50,
                        "cleared_tool_uses": 1,
                    }
                ]
            },
        },
        {"type": "message_stop"},
    ]

    completed = False
    for event in events:
        _partial, accumulator, completed = reduce_event(accumulator, event)

    assert completed is True
    assert accumulator is not None
    assert accumulator["content"][0] == {
        "type": "compaction",
        "content": "Summary",
        "encrypted_content": "opaque",
    }
    assert (
        accumulator["_metadata"]["anthropic"]["context_management"]["applied_edits"][0][
            "cleared_tool_uses"
        ]
        == 1
    )


def test_incomplete_compaction_stream_is_not_finalized_into_history() -> None:
    provider = AnthropicProvider()
    state = provider.init({"model": "m", "api_key": "test"})
    baseline = [{"role": "user", "content": "hello"}]

    _partials, _finals, history, state = provider.process_chunk(
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "compaction"},
        },
        baseline,
        state,
    )
    _partials, _finals, history, state = provider.process_chunk(
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "compaction_delta",
                "content": "partial",
                "encrypted_content": "partial-opaque",
            },
        },
        history,
        state,
    )

    finals, completed_history, _state = provider.finalize(history, state)

    assert finals == []
    assert completed_history == baseline


def test_usage_iterations_are_authoritative_and_compaction_is_not_double_counted() -> (
    None
):
    extension = AnthropicUsageExtension()
    final = {
        "role": "assistant",
        "content": [{"type": "text", "text": "Answer"}],
        "_metadata": {
            "anthropic_usage": {
                "input_tokens": 999,
                "output_tokens": 999,
                "cache_read_input_tokens": 999,
                "output_tokens_details": {"thinking_tokens": 4},
                "iterations": [
                    {
                        "type": "compaction",
                        "input_tokens": 50,
                        "output_tokens": 5,
                        "cache_read_input_tokens": 2,
                        "cache_creation_input_tokens": 3,
                        "cache_creation": {
                            "ephemeral_5m_input_tokens": 1,
                            "ephemeral_1h_input_tokens": 2,
                        },
                    },
                    {
                        "type": "message",
                        "input_tokens": 7,
                        "output_tokens": 11,
                        "cache_read_input_tokens": 1,
                        "cache_creation_input_tokens": 0,
                    },
                ],
            }
        },
    }
    state = extension.init({}, _state({}))

    finals, _history, _state_out = extension.finalize([final], [final], state)
    metadata = finals[0]["_metadata"]

    assert metadata["usage_prompt_tokens"] == 57
    assert metadata["usage_completion_tokens"] == 16
    assert metadata["usage_cached_tokens"] == 3
    assert metadata["usage_cache_write_tokens"] == 3
    assert metadata["usage_reasoning_tokens"] == 4
    assert metadata["usage_compaction_iterations"] == 1
    assert metadata["usage_compaction_input_tokens"] == 50
    assert metadata["usage_compaction_output_tokens"] == 5
    assert metadata["usage_compaction_total_tokens"] == 55
    assert metadata["usage_compaction_cache_write_5m_tokens"] == 1
    assert metadata["usage_compaction_cache_write_1h_tokens"] == 2
