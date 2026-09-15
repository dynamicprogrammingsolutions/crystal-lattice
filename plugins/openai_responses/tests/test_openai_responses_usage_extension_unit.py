from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from openai_responses_plugins.openai_responses_usage_extension import (
    OpenAIResponsesUsageExtension,
)

RAW_USAGE_KEY = "_openai_responses_usage_raw"


def test_usage_config_schema_exposes_footer_visibility_controls() -> None:
    schema = OpenAIResponsesUsageExtension().get_config_schema()

    assert schema["show_usage"]["default"] is True
    assert schema["show_usage_status_total"]["default"] is True
    assert schema["usage_message_footer_fields"]["items"]["enum"] == [
        "input",
        "cached",
        "cache_write",
        "estimated_cached",
        "completion",
        "auth",
        "tier",
        "mode",
        "cost",
        "turn_cost",
        "turn_reasoning",
        "turn_input",
        "turn_cached",
        "turn_output",
    ]


def _assistant_output_item(
    text: str,
    *,
    response_id: str = "resp",
    extra_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    metadata = {"response_id": response_id}
    if isinstance(extra_metadata, dict):
        metadata.update(extra_metadata)
    return {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": text}],
        "_metadata": metadata,
    }


def _user_item(text: str) -> Dict[str, Any]:
    return {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": text}],
    }


def _assistant_usage_item(
    text: str,
    *,
    input_tokens: int,
    output_tokens: int = 1,
    response_id: str = "resp",
) -> Dict[str, Any]:
    return _assistant_output_item(
        text,
        response_id=response_id,
        extra_metadata={
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        },
    )


def _tool_result_item(call_id: str = "call_1", output: str = "ok") -> Dict[str, Any]:
    return {
        "type": "function_call_output",
        "call_id": call_id,
        "output": output,
    }


def test_streaming_usage_attaches_openrouter_compatible_fields() -> None:
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 1234,
        "input_tokens_details": {"cached_tokens": 12},
        "output_tokens": 56,
        "output_tokens_details": {"reasoning_tokens": 7},
        "total_tokens": 1290,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_1")
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_1", "usage": usage},
    }

    _partials, finals, new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage") == usage
    assert md.get("usage_prompt_tokens_formatted") == "1,234"
    assert md.get("usage_cached_tokens_formatted") == "12"
    assert md.get("usage_completion_tokens_formatted") == "56"
    assert md.get("usage_total_cost") == pytest.approx(0.0004178, rel=1e-9)
    assert md.get("usage_total_cost_formatted") == "$0.000418"
    assert md.get("usage_total_cost_cumulative") == pytest.approx(0.0004178, rel=1e-9)
    assert md.get("usage_total_cost_cumulative_formatted") == "$0.000418"
    assert md.get("usage_turn_cost_cumulative") == pytest.approx(0.0004178, rel=1e-9)
    assert md.get("usage_turn_cost_cumulative_formatted") == "$0.000418"
    assert md.get("usage_turn_input_tokens_cumulative") == 1234
    assert md.get("usage_turn_input_tokens_cumulative_formatted") == "1,234"
    assert md.get("usage_turn_cached_tokens_cumulative") == 12
    assert md.get("usage_turn_cached_tokens_cumulative_formatted") == "12"
    assert md.get("usage_turn_output_tokens_cumulative") == 56
    assert md.get("usage_turn_output_tokens_cumulative_formatted") == "56"
    assert md.get("usage_turn_reasoning_tokens_cumulative") == 7
    assert md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "7"
    assert md.get("turn") == {"id": 1, "has_tool_calls": False, "is_terminal": True}
    assert md.get("has_tool_calls") is False
    assert "usage_estimated_cost" not in md
    assert "usage_cost_source" not in md
    assert "usage_pricing_model" not in md

    native_md = new_native[0].get("_metadata") or {}
    assert native_md.get("usage") == usage
    assert RAW_USAGE_KEY not in native_md
    assert md.get("usage_effective_auth_mode") == "api"
    assert md.get("usage_effective_auth_mode_label") == "API"


def test_usage_persistence_projects_supported_field_paths() -> None:
    ext = OpenAIResponsesUsageExtension()
    usage = {
        "input_tokens": 120,
        "input_tokens_details": {
            "cached_tokens": 20,
            "cache_write_tokens": 3,
            "future_nested_detail": "discarded",
        },
        "output_tokens": 30,
        "output_tokens_details": {
            "reasoning_tokens": 5,
            "future_output_detail": "discarded",
        },
        "completion_tokens_details": {
            "reasoning_tokens": 6,
            "future_completion_detail": "discarded",
        },
        "total_tokens": 150,
        "future_scalar": "discarded",
        "future_object": {"payload": "discarded"},
        "attribution": {
            "request_fields": {"model": "gpt-test"},
            "items": [
                {
                    "input_tokens": 120,
                    "output_tokens": 30,
                    "content": "repeated provider attribution",
                }
            ],
        },
    }
    final_messages = [_assistant_output_item("done", response_id="resp_attr")]

    _partials, finals, new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_attr", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=list(final_messages),
        state={"config": {"model": "gpt-5-mini"}},
    )

    expected_usage = {
        "input_tokens": 120,
        "input_tokens_details": {
            "cached_tokens": 20,
            "cache_write_tokens": 3,
        },
        "output_tokens": 30,
        "output_tokens_details": {"reasoning_tokens": 5},
        "completion_tokens_details": {"reasoning_tokens": 6},
        "total_tokens": 150,
    }
    persisted_metadata = finals[0]["_metadata"]
    assert persisted_metadata["usage"] == expected_usage
    assert new_native[0]["_metadata"]["usage"] == expected_usage
    assert persisted_metadata["usage_prompt_tokens_formatted"] == "120"
    assert persisted_metadata["usage_completion_tokens_formatted"] == "30"
    assert persisted_metadata["usage_turn_reasoning_tokens_cumulative"] == 5
    assert (
        "future_nested_detail"
        not in persisted_metadata["usage"]["input_tokens_details"]
    )
    assert (
        "future_output_detail"
        not in persisted_metadata["usage"]["output_tokens_details"]
    )
    assert (
        "future_completion_detail"
        not in persisted_metadata["usage"]["completion_tokens_details"]
    )
    assert "future_scalar" not in persisted_metadata["usage"]
    assert "future_object" not in persisted_metadata["usage"]
    assert "attribution" not in persisted_metadata["usage"]

    rebuilt = ext.from_native_messages(
        new_native,
        [
            {
                "role": "assistant",
                "content": "done",
                "metadata": {
                    "native_indices": [0],
                    "phase_messages": [
                        {
                            "phase": "final_answer",
                            "content": "done",
                            "metadata": {"usage": usage},
                        }
                    ],
                },
            }
        ],
    )
    rebuilt_metadata = rebuilt[0]["metadata"]
    assert rebuilt_metadata["usage"] == expected_usage
    assert rebuilt_metadata["phase_messages"][0]["metadata"]["usage"] == expected_usage


def test_streaming_usage_surfaces_flex_tier_and_uses_tier_pricing(
    tmp_path: Path,
) -> None:
    ext = OpenAIResponsesUsageExtension()

    snapshot_path = tmp_path / "pricing.json"
    snapshot_path.write_text(
        """
{
  "version": 2,
  "fetched_at": "2026-03-14T00:00:00+00:00",
  "source_base_url": "https://developers.openai.com/api/docs/pricing",
  "models": {
    "gpt-5-mini": {
      "model": "gpt-5-mini",
      "pricing": {
        "input_per_1m": 0.25,
        "cached_input_per_1m": 0.025,
        "output_per_1m": 2.0
      },
      "service_tiers": {
        "flex": {
          "input_per_1m": 0.125,
          "cached_input_per_1m": 0.0125,
          "output_per_1m": 1.0
        }
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item(
            "hi",
            response_id="resp_flex",
            extra_metadata={"_openai_responses_service_tier": "flex"},
        )
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_flex", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "pricing_snapshot_path": str(snapshot_path),
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_service_tier") == "flex"
    assert md.get("usage_total_cost") == pytest.approx(0.0002025, rel=1e-9)
    assert md.get("usage_total_cost_formatted") == "$0.000202"


def test_streaming_usage_uses_manual_model_pricing_when_snapshot_is_missing_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ext = OpenAIResponsesUsageExtension()

    # Use an empty snapshot and a synthetic manual fallback so the manual
    # pricing path is exercised without depending on the checked-in manual
    # models file (which no longer publishes any model).
    empty_snapshot_path = tmp_path / "empty_pricing.json"
    empty_snapshot_path.write_text(
        json.dumps(
            {
                "version": 2,
                "fetched_at": "2026-07-13T00:00:00+00:00",
                "source_base_url": "https://developers.openai.com/api/docs/pricing",
                "models": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "openai_responses_plugins.openai_responses_usage_extension"
        "._load_manual_chatgpt_model_pricing_shared",
        lambda path=None: {
            "gpt-5.5": {
                "model": "gpt-5.5",
                "pricing": {
                    "input_per_1m": 5.0,
                    "cached_input_per_1m": 0.5,
                    "output_per_1m": 30.0,
                },
            },
        },
    )

    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_manual")
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_manual", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5.5",
                "pricing_snapshot_path": str(empty_snapshot_path),
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_total_cost") == pytest.approx(0.0071, rel=1e-9)
    assert md.get("usage_total_cost_formatted") == "$0.007100"


def test_streaming_usage_uses_manual_fast_tier_pricing_when_snapshot_is_missing_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ext = OpenAIResponsesUsageExtension()

    # Use an empty snapshot and a synthetic manual fallback so the manual
    # fast-tier pricing path is exercised without depending on the checked-in
    # manual models file.
    empty_snapshot_path = tmp_path / "empty_pricing.json"
    empty_snapshot_path.write_text(
        json.dumps(
            {
                "version": 2,
                "fetched_at": "2026-07-13T00:00:00+00:00",
                "source_base_url": "https://developers.openai.com/api/docs/pricing",
                "models": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "openai_responses_plugins.openai_responses_usage_extension"
        "._load_manual_chatgpt_model_pricing_shared",
        lambda path=None: {
            "gpt-5.5": {
                "model": "gpt-5.5",
                "pricing": {
                    "input_per_1m": 5.0,
                    "cached_input_per_1m": 0.5,
                    "output_per_1m": 30.0,
                },
                "service_tiers": {
                    "fast": {
                        "input_per_1m": 5.0,
                        "cached_input_per_1m": 0.5,
                        "output_per_1m": 30.0,
                    }
                },
            },
        },
    )

    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item(
            "hi",
            response_id="resp_manual_fast",
            extra_metadata={"_openai_responses_service_tier": "fast"},
        )
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_manual_fast", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5.5",
                "pricing_snapshot_path": str(empty_snapshot_path),
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_service_tier") == "fast"
    assert md.get("usage_total_cost") == pytest.approx(0.0071, rel=1e-9)
    assert md.get("usage_total_cost_formatted") == "$0.007100"


def test_streaming_usage_surfaces_reasoning_mode_pro() -> None:
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item(
            "hi",
            response_id="resp_pro_mode",
            extra_metadata={"_openai_responses_reasoning_mode": "pro"},
        )
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_pro_mode", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5.6-sol"}},
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_reasoning_mode") == "pro"


def test_streaming_usage_omits_reasoning_mode_when_absent() -> None:
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_no_mode")
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_no_mode", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5.6-sol"}},
    )

    md = finals[0].get("_metadata") or {}
    assert "usage_reasoning_mode" not in md


def test_streaming_usage_surfaces_service_tier_priority_and_reasoning_mode_pro() -> (
    None
):
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens": 100,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item(
            "hi",
            response_id="resp_both",
            extra_metadata={
                "_openai_responses_service_tier": "priority",
                "_openai_responses_reasoning_mode": "pro",
            },
        )
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_both", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5.6-sol"}},
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_service_tier") == "priority"
    assert md.get("usage_reasoning_mode") == "pro"


def test_streaming_usage_marks_tool_call_turns_and_attaches_to_assistant_item() -> None:
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 20,
        "output_tokens": 10,
        "output_tokens_details": {"reasoning_tokens": 2},
    }
    final_messages: List[Dict[str, Any]] = [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": "{}",
            "_metadata": {"response_id": "resp_2"},
        },
        _assistant_output_item("calling tool", response_id="resp_2"),
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_2", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    assert "usage" not in ((finals[0].get("_metadata") or {}))
    assistant_md = finals[1].get("_metadata") or {}
    assert assistant_md.get("usage") == usage
    assert assistant_md.get("has_tool_calls") is True
    assert assistant_md.get("usage_total_cost") == pytest.approx(0.000025, rel=1e-9)
    assert assistant_md.get("usage_total_cost_formatted") == "$0.000025"
    assert assistant_md.get("usage_turn_cost_cumulative_formatted") == "$0.000025"
    assert assistant_md.get("usage_turn_input_tokens_cumulative_formatted") == "20"
    assert assistant_md.get("usage_turn_cached_tokens_cumulative_formatted") == "0"
    assert assistant_md.get("usage_turn_output_tokens_cumulative_formatted") == "10"
    assert assistant_md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "2"
    assert assistant_md.get("turn") == {
        "id": 1,
        "has_tool_calls": True,
        "is_terminal": False,
    }


def test_streaming_usage_marks_custom_tool_call_turns_correctly() -> None:
    """Ensure custom_tool_call items set has_tool_calls=True, not False.

    This prevents the turn separator logic from incorrectly resetting turn cost
    when responses contain custom_tool_call items (e.g., apply_patch tool).
    """
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 30,
        "output_tokens": 15,
        "output_tokens_details": {"reasoning_tokens": 3},
    }
    final_messages: List[Dict[str, Any]] = [
        {
            "type": "custom_tool_call",
            "call_id": "call_custom_1",
            "name": "apply_patch",
            "arguments": "{}",
            "_metadata": {"response_id": "resp_custom"},
        },
        _assistant_output_item("applying patch", response_id="resp_custom"),
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_custom", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    assistant_md = finals[1].get("_metadata") or {}
    assert assistant_md.get("usage") == usage
    assert (
        assistant_md.get("has_tool_calls") is True
    )  # Should be True for custom_tool_call
    assert assistant_md.get("usage_total_cost") == pytest.approx(0.0000375, rel=1e-9)


def test_streaming_usage_keeps_open_turn_id_when_preceding_history_is_retained() -> (
    None
):
    """A resumed tool turn keeps its ID when its preceding turns remain intact."""
    ext = OpenAIResponsesUsageExtension()

    usage = {"input_tokens": 30, "output_tokens": 10}
    final_messages = [_assistant_output_item("turn 3 complete", response_id="resp_3b")]
    native_messages = [
        _user_item("turn 1"),
        _assistant_output_item(
            "turn 1 complete",
            response_id="resp_1",
            extra_metadata={
                "usage": {"input_tokens": 10, "output_tokens": 2},
                "turn": {"id": 1, "has_tool_calls": False, "is_terminal": True},
            },
        ),
        _user_item("turn 2"),
        _assistant_output_item(
            "turn 2 complete",
            response_id="resp_2",
            extra_metadata={
                "usage": {"input_tokens": 20, "output_tokens": 4},
                "turn": {"id": 2, "has_tool_calls": False, "is_terminal": True},
            },
        ),
        _user_item("turn 3"),
        _assistant_output_item(
            "turn 3 requested tools",
            response_id="resp_3a",
            extra_metadata={
                "usage": {"input_tokens": 25, "output_tokens": 6},
                "turn": {"id": 3, "has_tool_calls": True, "is_terminal": False},
                "duration_ms": 170_257,
            },
        ),
        {"type": "function_call_output", "call_id": "call_3", "output": "ok"},
        *final_messages,
    ]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_3b", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    assert (finals[0].get("_metadata") or {}).get("turn") == {
        "id": 3,
        "has_tool_calls": False,
        "is_terminal": True,
    }


def test_streaming_usage_preserves_open_turn_id_after_partial_compaction() -> None:
    """Regression for turn 1 compacted, turn 2 retained, and turn 3 restarted.

    This mirrors the affected session shape:

    - turn 1 (messages 0-9) is replaced by compacted native history;
    - turn 2 (messages 10-19) remains a completed turn with ID 2;
    - turn 3 is suspended after a tool-call response with ID 3;
    - the restarted request must finish turn 3, retaining ID 3.

    The duration feature groups history solely by ``_metadata.turn.id``. If
    this continuation is stamped as ID 2, it loses turn 3's prior duration and
    can include duration from the retained completed turn 2 instead.
    """
    ext = OpenAIResponsesUsageExtension()

    continuation_usage = {"input_tokens": 30, "output_tokens": 10}
    final_messages = [_assistant_output_item("turn 3 complete", response_id="resp_3b")]
    native_messages = [
        {"type": "compaction_summary", "encrypted_content": "turn-1-summary"},
        _user_item("turn 2"),
        _assistant_output_item(
            "turn 2 complete",
            response_id="resp_2",
            extra_metadata={
                "usage": {"input_tokens": 20, "output_tokens": 4},
                "turn": {"id": 2, "has_tool_calls": False, "is_terminal": True},
                "duration_ms": 35_139,
            },
        ),
        _user_item("turn 3"),
        _assistant_output_item(
            "turn 3 requested tools",
            response_id="resp_3a",
            extra_metadata={
                "usage": {"input_tokens": 25, "output_tokens": 6},
                "turn": {"id": 3, "has_tool_calls": True, "is_terminal": False},
                "duration_ms": 170_257,
            },
        ),
        {"type": "function_call_output", "call_id": "call_3", "output": "ok"},
        *final_messages,
    ]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_3b", "usage": continuation_usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    assert (finals[0].get("_metadata") or {}).get("turn") == {
        "id": 3,
        "has_tool_calls": False,
        "is_terminal": True,
    }


def test_nonstreaming_finalize_extracts_raw_usage_and_computes_cumulative_totals() -> (
    None
):
    ext = OpenAIResponsesUsageExtension()

    native_messages: List[Dict[str, Any]] = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hi"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "tool reply"}],
            "_metadata": {
                "usage": {"completion_tokens_details": {"reasoning_tokens": 5}},
                "usage_total_cost": 0.0002,
                "has_tool_calls": True,
            },
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "reply"}],
            "_metadata": {
                "usage": {"completion_tokens_details": {"reasoning_tokens": 10}},
                "usage_total_cost": 0.0003,
                "has_tool_calls": False,
            },
        },
        _assistant_output_item(
            "new",
            response_id="resp_3",
            extra_metadata={
                RAW_USAGE_KEY: {
                    "input_tokens": 99,
                    "input_tokens_details": {"cached_tokens": 4},
                    "output_tokens": 15,
                    "output_tokens_details": {"reasoning_tokens": 3},
                }
            },
        ),
    ]

    finals, updated_native, _state = ext.finalize(
        [],
        native_messages,
        {"config": {"model": "gpt-5-mini"}},
    )

    assert finals == []
    md = updated_native[-1].get("_metadata") or {}
    assert md.get("usage") == {
        "input_tokens": 99,
        "input_tokens_details": {"cached_tokens": 4},
        "output_tokens": 15,
        "output_tokens_details": {"reasoning_tokens": 3},
    }
    assert md.get("usage_prompt_tokens_formatted") == "99"
    assert md.get("usage_cached_tokens_formatted") == "4"
    assert md.get("usage_completion_tokens_formatted") == "15"
    assert md.get("usage_total_cost") == pytest.approx(0.00005385, rel=1e-9)
    assert md.get("usage_total_cost_formatted") == "$0.000054"
    assert md.get("usage_total_cost_cumulative") == pytest.approx(0.00055385, rel=1e-9)
    assert md.get("usage_total_cost_cumulative_formatted") == "$0.000554"
    assert md.get("usage_turn_cost_cumulative") == pytest.approx(0.00005385, rel=1e-9)
    assert md.get("usage_turn_cost_cumulative_formatted") == "$0.000054"
    assert md.get("usage_turn_reasoning_tokens_cumulative") == 3
    assert md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "3"
    assert md.get("has_tool_calls") is False
    assert md.get("usage_effective_auth_mode") == "api"
    assert md.get("usage_effective_auth_mode_label") == "API"
    assert "usage_estimated_cost" not in md
    assert "usage_cost_source" not in md
    assert RAW_USAGE_KEY not in md


def test_from_native_messages_lifts_usage_from_tool_call_item_to_assistant_message() -> (
    None
):
    ext = OpenAIResponsesUsageExtension()

    native_messages: List[Dict[str, Any]] = [
        {
            "type": "reasoning",
            "id": "rs_1",
            "summary": [],
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": "{}",
            "_metadata": {
                "response_id": "resp_1",
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 10,
                    "output_tokens_details": {"reasoning_tokens": 2},
                },
                "has_tool_calls": True,
                "usage_total_cost": 0.000025,
                "usage_total_cost_formatted": "$0.000025",
                "usage_total_cost_cumulative": 0.000025,
                "usage_total_cost_cumulative_formatted": "$0.000025",
                "usage_turn_cost_cumulative": 0.000025,
                "usage_turn_cost_cumulative_formatted": "$0.000025",
                "usage_turn_reasoning_tokens_cumulative": 2,
                "usage_turn_reasoning_tokens_cumulative_formatted": "2",
                "usage_prompt_tokens_formatted": "20",
                "usage_completion_tokens_formatted": "10",
                "usage_service_tier": "default",
            },
        },
    ]
    messages = [
        {
            "role": "assistant",
            "content": "",
            "metadata": {
                "response_id": "resp_1",
                "native_indices": [0, 1],
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "lookup", "arguments": "{}"},
                    }
                ],
                "reasoning": "Reasoning present but not exposed by model.",
            },
        }
    ]

    out = ext.from_native_messages(native_messages, messages)

    md = out[0].get("metadata") or {}
    assert md.get("usage") == {
        "input_tokens": 20,
        "output_tokens": 10,
        "output_tokens_details": {"reasoning_tokens": 2},
    }
    assert md.get("has_tool_calls") is True
    assert md.get("usage_total_cost") == pytest.approx(0.000025, rel=1e-9)
    assert md.get("usage_total_cost_formatted") == "$0.000025"
    assert md.get("usage_turn_cost_cumulative_formatted") == "$0.000025"
    assert md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "2"


def test_usage_ui_elements_match_openrouter_usage_fields() -> None:
    ext = OpenAIResponsesUsageExtension()

    elements = ext.get_ui_elements(config={}, tags=["openai_responses"], models=[])
    data_paths = [element.get("data") for element in elements]

    assert data_paths == [
        "metadata.usage_prompt_tokens_formatted",
        "metadata.usage_cached_tokens_formatted",
        "metadata.usage_cache_write_tokens_formatted",
        "metadata.usage_completion_tokens_formatted",
        "metadata.usage_service_tier",
        "metadata.usage_reasoning_mode",
        "metadata.usage_total_cost_formatted",
        "metadata.usage_total_cost_formatted",
        "metadata.usage_turn_cost_cumulative_formatted",
        "metadata.usage_turn_cost_cumulative_formatted",
        "metadata.usage_turn_reasoning_tokens_cumulative_formatted",
        "metadata.usage_turn_input_tokens_cumulative_formatted",
        "metadata.usage_turn_cached_tokens_cumulative_formatted",
        "metadata.usage_turn_output_tokens_cumulative_formatted",
        "metadata.usage_total_cost_cumulative_formatted",
    ]
    assert elements[1]["condition"] == {
        "not": {
            "path": "metadata.usage_effective_auth_mode",
            "eq": "chatgpt",
        }
    }
    assert elements[2]["condition"] == {
        "path": "metadata.usage_cache_write_tokens_formatted",
        "exists": True,
    }
    assert elements[4]["condition"] == {
        "any": [
            {"path": "metadata.usage_service_tier", "eq": "flex"},
            {"path": "metadata.usage_service_tier", "eq": "fast"},
            # ``priority`` is the obsolete tier name; some backends may
            # still report it.
            {"path": "metadata.usage_service_tier", "eq": "priority"},
        ]
    }
    assert elements[5]["condition"] == {
        "path": "metadata.usage_reasoning_mode",
        "eq": "pro",
    }
    assert [
        (element["template"], element["condition"])
        for element in elements
        if element.get("data") == "metadata.usage_total_cost_formatted"
    ] == [
        (
            "estimated cost: {{data}}",
            {
                "path": "metadata.usage_effective_auth_mode",
                "eq": "chatgpt",
            },
        ),
        (
            "cost: {{data}}",
            {
                "not": {
                    "path": "metadata.usage_effective_auth_mode",
                    "eq": "chatgpt",
                }
            },
        ),
    ]
    assert [
        (element["template"], element["condition"])
        for element in elements
        if element.get("data") == "metadata.usage_turn_cost_cumulative_formatted"
    ] == [
        (
            "estimated turn: {{data}}",
            {
                "path": "metadata.usage_effective_auth_mode",
                "eq": "chatgpt",
            },
        ),
        (
            "turn: {{data}}",
            {
                "not": {
                    "path": "metadata.usage_effective_auth_mode",
                    "eq": "chatgpt",
                }
            },
        ),
    ]


def test_chatgpt_estimated_cached_tokens_follow_turn_algorithm() -> None:
    ext = OpenAIResponsesUsageExtension()

    history = [
        _user_item("u1"),
        _assistant_usage_item("a2", input_tokens=20, response_id="resp_2"),
        _assistant_usage_item("a3", input_tokens=30, response_id="resp_3"),
        _user_item("u4"),
    ]

    assert (
        ext._estimated_cached_tokens_for_current(history[:1], {"input_tokens": 20}) == 0
    )
    assert (
        ext._estimated_cached_tokens_for_current(history[:2], {"input_tokens": 30})
        == 20
    )
    assert ext._estimated_cached_tokens_for_current(history, {"input_tokens": 40}) == 30
    assert ext._estimated_cached_tokens_for_current(history, {"input_tokens": 30}) == 20
    assert ext._estimated_cached_tokens_for_current(history, {"input_tokens": 25}) == 20
    assert ext._estimated_cached_tokens_for_current(history, {"input_tokens": 19}) == 0


def test_chatgpt_estimated_cached_tokens_detect_same_turn_prefix_invalidation() -> None:
    ext = OpenAIResponsesUsageExtension()
    history = [
        _user_item("u1"),
        _assistant_usage_item("a2", input_tokens=371_326, response_id="resp_previous"),
    ]

    assert (
        ext._estimated_cached_tokens_for_current(history, {"input_tokens": 371_326})
        == 371_326
    )
    assert (
        ext._estimated_cached_tokens_for_current(history, {"input_tokens": 400_000})
        == 371_326
    )
    assert (
        ext._estimated_cached_tokens_for_current(history, {"input_tokens": 278_176})
        == 0
    )


def test_chatgpt_estimated_cached_tokens_ignore_tool_results() -> None:
    ext = OpenAIResponsesUsageExtension()

    history = [
        _user_item("u1"),
        _assistant_usage_item("a2", input_tokens=20, response_id="resp_2"),
        _tool_result_item("call_1"),
        _assistant_usage_item("a3", input_tokens=30, response_id="resp_3"),
        _user_item("u4"),
        _tool_result_item("call_2"),
    ]

    assert (
        ext._estimated_cached_tokens_for_current(history[:2], {"input_tokens": 30})
        == 20
    )
    assert ext._estimated_cached_tokens_for_current(history, {"input_tokens": 50}) == 30

    history.extend([_user_item("u5"), _user_item("u6")])
    assert ext._estimated_cached_tokens_for_current(history, {"input_tokens": 50}) == 30


def test_chatgpt_compaction_invalidation_flows_into_usage_cost_and_totals() -> None:
    ext = OpenAIResponsesUsageExtension()
    previous = {
        "type": "function_call",
        "call_id": "call_1",
        "name": "lookup",
        "arguments": "{}",
        "_metadata": {
            "usage": {"input_tokens": 371_326, "output_tokens": 10},
            "usage_estimated_cached_tokens": 100,
            "usage_total_cost": 0.1,
            "turn": {"id": 1, "has_tool_calls": True, "is_terminal": False},
        },
    }
    base_native = [_user_item("u1"), previous]
    final_messages = [_assistant_output_item("done", response_id="resp_current")]
    native_messages = [*base_native, *final_messages]
    usage = {"input_tokens": 278_176, "output_tokens": 190}

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_current", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "chatgpt",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    expected_current_cost = ((278_176 * 0.25) + (190 * 2.0)) / 1_000_000
    assert md.get("usage") == usage
    assert md.get("usage_estimated_cached_tokens") == 0
    assert md.get("usage_estimated_cached_tokens_formatted") == "0"
    assert md.get("usage_total_cost") == pytest.approx(expected_current_cost)
    assert md.get("usage_turn_cached_tokens_cumulative") == 100
    assert md.get("usage_turn_cached_tokens_cumulative_formatted") == "100"


def test_chatgpt_streaming_usage_keeps_raw_usage_separate_and_estimates_cost() -> None:
    ext = OpenAIResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        _user_item("u1"),
        _assistant_usage_item(
            "a2", input_tokens=20, output_tokens=4, response_id="resp_prev"
        ),
        _user_item("u3"),
    ]
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("a4", response_id="resp_4")
    ]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]
    usage = {
        "input_tokens": 50,
        "output_tokens": 10,
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_4", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "chatgpt",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage") == usage
    assert md.get("usage_estimated_cached_tokens") == 20
    assert md.get("usage_estimated_cached_tokens_formatted") == "20"
    assert "usage_cached_tokens_formatted" not in md
    assert md.get("usage_effective_auth_mode") == "chatgpt"
    assert md.get("usage_effective_auth_mode_label") == "ChatGPT"
    assert md.get("usage_total_cost") == pytest.approx(0.000028, rel=1e-9)


def test_chatgpt_usage_ignores_reported_cached_tokens_for_cost_and_uses_estimate() -> (
    None
):
    ext = OpenAIResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        _user_item("u1"),
        _assistant_usage_item(
            "a2", input_tokens=20, output_tokens=4, response_id="resp_prev"
        ),
        _user_item("u3"),
    ]
    usage = {
        "input_tokens": 100,
        "input_tokens_details": {"cached_tokens": 12},
        "output_tokens": 10,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_1")
    ]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_1", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "chatgpt",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    expected_cost = ((80 * 0.25) + (20 * 0.025) + (10 * 2.0)) / 1_000_000.0
    assert md.get("usage_total_cost") == pytest.approx(expected_cost, rel=1e-9)
    assert "usage_cached_tokens_formatted" not in md
    assert md.get("usage") == usage
    assert md.get("usage_estimated_cached_tokens") == 20
    assert md.get("usage_estimated_cached_tokens_formatted") == "20"
    assert md.get("usage_turn_cached_tokens_cumulative") == 20
    assert md.get("usage_turn_cached_tokens_cumulative_formatted") == "20"


def test_turn_cached_cumulative_prefers_estimated_cached_tokens_when_present() -> None:
    ext = OpenAIResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        _user_item("u1"),
        _assistant_output_item(
            "a2",
            response_id="resp_prev",
            extra_metadata={
                "usage": {
                    "input_tokens": 20,
                    "input_tokens_details": {"cached_tokens": 4},
                    "output_tokens": 3,
                },
                "usage_estimated_cached_tokens": 18,
                "turn": {"id": 1, "has_tool_calls": True, "is_terminal": False},
                "usage_total_cost": 0.00001,
            },
        ),
    ]
    usage = {
        "input_tokens": 100,
        "input_tokens_details": {"cached_tokens": 12},
        "output_tokens": 10,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_1")
    ]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_1", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "chatgpt",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_estimated_cached_tokens") == 20
    assert md.get("usage_turn_cached_tokens_cumulative") == 38
    assert md.get("usage_turn_cached_tokens_cumulative_formatted") == "38"


def test_chatgpt_estimated_cached_tokens_are_shown_as_zero_for_first_turn_message() -> (
    None
):
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 40,
        "output_tokens": 8,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_1")
    ]
    native_messages: List[Dict[str, Any]] = [
        _user_item("u1"),
        *final_messages,
    ]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_1", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "chatgpt",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_estimated_cached_tokens") == 0
    assert md.get("usage_estimated_cached_tokens_formatted") == "0"


def test_usage_ui_elements_can_show_estimated_cached_tokens_and_auth_mode() -> None:
    ext = OpenAIResponsesUsageExtension()

    elements = ext.get_ui_elements(
        config={"show_estimated_cached_tokens": True, "show_openai_auth_mode": True},
        tags=["openai_responses"],
        models=[],
    )
    data_paths = [element.get("data") for element in elements]

    assert "metadata.usage_estimated_cached_tokens_formatted" in data_paths
    assert "metadata.usage_effective_auth_mode_label" in data_paths


def test_usage_ui_elements_hide_optional_chatgpt_footers_by_default() -> None:
    ext = OpenAIResponsesUsageExtension()

    elements = ext.get_ui_elements(config={}, tags=["openai_responses"], models=[])
    data_paths = [element.get("data") for element in elements]

    assert "metadata.usage_estimated_cached_tokens_formatted" not in data_paths
    assert "metadata.usage_effective_auth_mode_label" not in data_paths


def test_usage_ui_elements_can_select_compact_turn_footer() -> None:
    ext = OpenAIResponsesUsageExtension()

    elements = ext.get_ui_elements(
        config={
            "usage_message_footer_fields": [
                "turn_input",
                "turn_output",
                "turn_cost",
            ]
        },
        tags=["openai_responses"],
        models=[],
    )
    footers = [
        element for element in elements if element.get("ui_type") == "message_footer"
    ]

    assert [element["template"] for element in footers] == [
        "estimated turn: {{data}}",
        "turn: {{data}}",
        "turn input: {{data}}",
        "turn output: {{data}}",
    ]
    assert [
        element["template"]
        for element in elements
        if element.get("ui_type") == "status_bar"
    ] == ["Total: {{data}}"]


def test_usage_ui_elements_can_hide_message_footer_or_status_total_independently() -> (
    None
):
    ext = OpenAIResponsesUsageExtension()

    status_only = ext.get_ui_elements(
        config={"usage_message_footer_fields": []},
        tags=["openai_responses"],
        models=[],
    )
    footer_only = ext.get_ui_elements(
        config={"show_usage_status_total": False},
        tags=["openai_responses"],
        models=[],
    )

    assert [element.get("ui_type") for element in status_only] == ["status_bar"]
    assert all(element.get("ui_type") == "message_footer" for element in footer_only)
    assert (
        ext.get_ui_elements(
            config={"show_usage": False},
            tags=["openai_responses"],
            models=[],
        )
        == []
    )


def test_api_mode_does_not_synthesize_estimated_cached_tokens() -> None:
    ext = OpenAIResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        _user_item("u1"),
        _assistant_usage_item(
            "a2", input_tokens=20, output_tokens=4, response_id="resp_prev"
        ),
        _user_item("u3"),
    ]
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("a4", response_id="resp_4")
    ]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]
    usage = {
        "input_tokens": 50,
        "output_tokens": 10,
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_4", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "api",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_effective_auth_mode") == "api"
    assert "usage_estimated_cached_tokens" not in md
    expected_cost = ((50 * 0.25) + (10 * 2.0)) / 1_000_000.0
    assert md.get("usage_total_cost") == pytest.approx(expected_cost, rel=1e-9)


# ---------------------------------------------------------------------------
# Cache-write token accounting tests (GPT-5.6 support).
# ---------------------------------------------------------------------------


def test_streaming_usage_exposes_cache_write_tokens_formatted() -> None:
    """API mode usage with cache_write_tokens emits the formatted footer."""
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 100, "cache_write_tokens": 42},
        "output_tokens": 50,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_cw")
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_cw", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_cache_write_tokens_formatted") == "42"
    assert md.get("usage_turn_cache_write_tokens_cumulative") == 42
    assert md.get("usage_turn_cache_write_tokens_cumulative_formatted") == "42"


def test_streaming_usage_includes_cache_write_in_cumulative_turn_totals() -> None:
    """Two assistant items in the same turn sum cache-write tokens."""
    ext = OpenAIResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        _user_item("u1"),
        _assistant_output_item(
            "a2",
            response_id="resp_prev",
            extra_metadata={
                "usage": {
                    "input_tokens": 100,
                    "input_tokens_details": {"cache_write_tokens": 30},
                    "output_tokens": 5,
                },
                "turn": {"id": 1, "has_tool_calls": True, "is_terminal": False},
                "usage_total_cost": 0.0001,
            },
        ),
    ]
    usage = {
        "input_tokens": 200,
        "input_tokens_details": {"cache_write_tokens": 25},
        "output_tokens": 10,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("a3", response_id="resp_3")
    ]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_3", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_turn_cache_write_tokens_cumulative") == 55
    assert md.get("usage_turn_cache_write_tokens_cumulative_formatted") == "55"


def test_streaming_usage_preserves_cache_write_in_provider_native_metadata() -> None:
    """metadata.usage.input_tokens_details.cache_write_tokens is preserved."""
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 500,
        "input_tokens_details": {"cached_tokens": 50, "cache_write_tokens": 75},
        "output_tokens": 20,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_preserve")
    ]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {
        "type": "response.completed",
        "response": {"id": "resp_preserve", "usage": usage},
    }

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={"config": {"model": "gpt-5-mini"}},
    )

    md = finals[0].get("_metadata") or {}
    public_usage = md.get("usage")
    assert isinstance(public_usage, dict)
    details = public_usage.get("input_tokens_details")
    assert isinstance(details, dict)
    assert details.get("cache_write_tokens") == 75


def test_chatgpt_usage_preserves_backend_reported_cache_write_tokens() -> None:
    """ChatGPT mode with backend-reported cache_write_tokens keeps it in effective_usage
    and the estimator prices it at the cache-write rate."""
    ext = OpenAIResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        _user_item("u1"),
        _assistant_usage_item(
            "a2", input_tokens=20, output_tokens=4, response_id="resp_prev"
        ),
        _user_item("u3"),
    ]
    usage = {
        "input_tokens": 100,
        "input_tokens_details": {"cache_write_tokens": 15},
        "output_tokens": 10,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_cw_chatgpt")
    ]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_cw_chatgpt", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "chatgpt",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    # The backend-reported cache_write_tokens should be preserved in the public usage
    public_usage = md.get("usage")
    assert isinstance(public_usage, dict)
    details = public_usage.get("input_tokens_details")
    assert isinstance(details, dict)
    assert details.get("cache_write_tokens") == 15
    # The formatted footer should be present
    assert md.get("usage_cache_write_tokens_formatted") == "15"
    # The cumulative should include the write tokens
    assert md.get("usage_turn_cache_write_tokens_cumulative") == 15
    # The estimated cached tokens should still be produced (estimate preserved)
    assert md.get("usage_estimated_cached_tokens") == 20


def test_chatgpt_usage_does_not_synthesize_cache_write_tokens_when_omitted() -> None:
    """ChatGPT mode with no cache_write_tokens field → write bucket is 0;
    no synthesis from the cached-read estimate."""
    ext = OpenAIResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        _user_item("u1"),
        _assistant_usage_item(
            "a2", input_tokens=20, output_tokens=4, response_id="resp_prev"
        ),
        _user_item("u3"),
    ]
    usage = {
        "input_tokens": 100,
        "output_tokens": 10,
    }
    final_messages: List[Dict[str, Any]] = [
        _assistant_output_item("hi", response_id="resp_no_cw")
    ]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk={
            "type": "response.completed",
            "response": {"id": "resp_no_cw", "usage": usage},
        },
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={
            "config": {
                "model": "gpt-5-mini",
                "_openai_responses_effective_auth_mode": "chatgpt",
            }
        },
    )

    md = finals[0].get("_metadata") or {}
    # No cache_write_tokens_formatted footer should be emitted
    assert "usage_cache_write_tokens_formatted" not in md
    # Cumulative cache-write should be 0
    assert md.get("usage_turn_cache_write_tokens_cumulative") == 0
    # The estimated cached tokens should still be produced (estimate preserved)
    assert md.get("usage_estimated_cached_tokens") == 20
    # The public usage should not have cache_write_tokens synthesized
    public_usage = md.get("usage")
    assert isinstance(public_usage, dict)
    details = public_usage.get("input_tokens_details")
    if isinstance(details, dict):
        assert "cache_write_tokens" not in details or details.get(
            "cache_write_tokens"
        ) in (None, 0)


def test_usage_ui_elements_include_cache_write_footer_when_present() -> None:
    """UI element list includes the cache-write footer with the right condition."""
    ext = OpenAIResponsesUsageExtension()

    elements = ext.get_ui_elements(config={}, tags=["openai_responses"], models=[])
    cache_write_elements = [
        el
        for el in elements
        if el.get("data") == "metadata.usage_cache_write_tokens_formatted"
    ]
    assert len(cache_write_elements) == 1
    assert cache_write_elements[0]["template"] == "cache write: {{data}}"
    assert cache_write_elements[0]["condition"] == {
        "path": "metadata.usage_cache_write_tokens_formatted",
        "exists": True,
    }
