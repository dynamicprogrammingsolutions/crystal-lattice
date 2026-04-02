from __future__ import annotations

from typing import Any

from reference_openai_compatible_provider._extension_accumulator import (
    AccumulatorExtensionMixin,
    _merge_delta_content,
)
from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.tools_extension import _merge_tool_calls


class _DummyAccumulatorExtension(AccumulatorExtensionMixin):
    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        return native_chunk

    def process_delta(
        self,
        delta: dict[str, Any],
        accumulated: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        base = dict(accumulated or {})
        patch = delta.get("patch")
        new_acc = {**base, **dict(delta.get("accumulated") or {})}
        return patch, new_acc


def test_merge_delta_content_preserves_unknown_keys_and_accumulates_strings():
    current = {"keep": 123, "reasoning": "a"}
    delta = {"reasoning": "b"}
    out = _merge_delta_content(current, delta, accumulate=("reasoning",))
    assert out["keep"] == 123
    assert out["reasoning"] == "ab"


def test_merge_delta_content_preserves_existing_override_when_new_value_is_null():
    current = {"name": "read_file"}
    delta = {"name": None}
    out = _merge_delta_content(current, delta, override=("name",))
    assert out["name"] == "read_file"


def test_merge_tool_calls_merges_by_index_and_concatenates_arguments_fragments():
    existing = [
        {
            "index": 0,
            "id": "call_1",
            "type": "function",
            "function": {"name": "read_file", "arguments": '{"file_path":'},
        }
    ]
    deltas = [
        {
            "index": 0,
            "function": {"arguments": ' "README.md"}'},
        }
    ]
    merged = _merge_tool_calls(existing=existing, deltas=deltas)
    assert merged[0]["function"]["name"] == "read_file"
    assert "README.md" in merged[0]["function"]["arguments"]


def test_merge_tool_calls_preserves_function_name_when_later_delta_sets_null():
    existing = [
        {
            "index": 0,
            "id": "call_1",
            "type": "function",
            "function": {"name": "read_file", "arguments": '{"file_path": '},
        }
    ]
    deltas = [
        {
            "index": 0,
            "name": None,
            "function": {"name": None, "arguments": '"bank0.json"}'},
        }
    ]
    merged = _merge_tool_calls(existing=existing, deltas=deltas)
    assert merged[0]["function"]["name"] == "read_file"
    assert merged[0].get("name") is None
    assert merged[0]["function"]["arguments"] == '{"file_path": "bank0.json"}'


def test_provider_accumulator_preserves_extension_keys():
    provider = OpenAICompatibleProvider()
    base = {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1"}]}
    patch, new_acc = provider.process_delta(
        {"delta": {"content": "hi"}},
        base,
    )
    assert patch and patch["content"] == "hi"
    assert new_acc["content"] == "hi"
    assert new_acc["tool_calls"] == [{"id": "call_1"}]


def test_extension_accumulator_does_not_emit_new_partial_from_accumulated_state():
    ext = _DummyAccumulatorExtension()

    partials, finals, native, new_state = ext.process_chunk(
        {
            "patch": {"reasoning": "next"},
            "accumulated": {"role": "assistant", "content": "Hello", "reasoning": "next"},
        },
        partial_messages=[],
        final_messages=[],
        native_messages=[],
        state={"partial": {"role": "assistant", "content": "Hello"}},
    )

    assert partials == []
    assert finals == []
    assert native == []
    assert new_state["partial"] == {
        "role": "assistant",
        "content": "Hello",
        "reasoning": "next",
    }


def test_extension_accumulator_merges_patch_into_existing_current_chunk_partial():
    ext = _DummyAccumulatorExtension()

    partials, _finals, _native, new_state = ext.process_chunk(
        {
            "patch": {"reasoning": "step"},
            "accumulated": {"reasoning": "step"},
        },
        partial_messages=[{"role": "assistant", "content": "Hel"}],
        final_messages=[],
        native_messages=[],
        state={"partial": {"role": "assistant", "content": "Hello"}},
    )

    assert partials == [{"role": "assistant", "content": "Hel", "reasoning": "step"}]
    assert new_state["partial"] == {
        "role": "assistant",
        "content": "Hello",
        "reasoning": "step",
    }
