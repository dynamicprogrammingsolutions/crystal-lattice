from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from openai_responses_plugins.openai_responses_usage_extension import OpenAIResponsesUsageExtension


RAW_USAGE_KEY = "_openai_responses_usage_raw"


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


def test_streaming_usage_attaches_openrouter_compatible_fields() -> None:
    ext = OpenAIResponsesUsageExtension()

    usage = {
        "input_tokens": 1234,
        "input_tokens_details": {"cached_tokens": 12},
        "output_tokens": 56,
        "output_tokens_details": {"reasoning_tokens": 7},
        "total_tokens": 1290,
    }
    final_messages: List[Dict[str, Any]] = [_assistant_output_item("hi", response_id="resp_1")]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    native_chunk = {"type": "response.completed", "response": {"id": "resp_1", "usage": usage}}

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
    assert md.get("usage_turn_reasoning_tokens_cumulative") == 7
    assert md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "7"
    assert md.get("has_tool_calls") is False
    assert "usage_estimated_cost" not in md
    assert "usage_cost_source" not in md
    assert "usage_pricing_model" not in md

    native_md = new_native[0].get("_metadata") or {}
    assert native_md.get("usage") == usage
    assert RAW_USAGE_KEY not in native_md


def test_streaming_usage_surfaces_flex_tier_and_uses_tier_pricing(tmp_path: Path) -> None:
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
    native_chunk = {"type": "response.completed", "response": {"id": "resp_flex", "usage": usage}}

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
        native_chunk={"type": "response.completed", "response": {"id": "resp_2", "usage": usage}},
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
    assert assistant_md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "2"


def test_nonstreaming_finalize_extracts_raw_usage_and_computes_cumulative_totals() -> None:
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
    assert "usage_estimated_cost" not in md
    assert "usage_cost_source" not in md
    assert RAW_USAGE_KEY not in md


def test_usage_ui_elements_match_openrouter_usage_fields() -> None:
    ext = OpenAIResponsesUsageExtension()

    elements = ext.get_ui_elements(config={}, tags=["openai_responses"], models=[])
    data_paths = [element.get("data") for element in elements]

    assert data_paths == [
        "metadata.usage_prompt_tokens_formatted",
        "metadata.usage_cached_tokens_formatted",
        "metadata.usage_completion_tokens_formatted",
        "metadata.usage_service_tier",
        "metadata.usage_total_cost_formatted",
        "metadata.usage_turn_cost_cumulative_formatted",
        "metadata.usage_turn_reasoning_tokens_cumulative_formatted",
        "metadata.usage_total_cost_cumulative_formatted",
    ]
    assert elements[3]["condition"] == {"path": "metadata.usage_service_tier", "eq": "flex"}
