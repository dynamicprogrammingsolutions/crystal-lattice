from __future__ import annotations

from reference_openai_compatible_provider._extension_accumulator import (
    _merge_delta_content,
)
from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.tools_extension import _merge_tool_calls


def test_merge_delta_content_preserves_unknown_keys_and_accumulates_strings():
    current = {"keep": 123, "reasoning": "a"}
    delta = {"reasoning": "b"}
    out = _merge_delta_content(current, delta, accumulate=("reasoning",))
    assert out["keep"] == 123
    assert out["reasoning"] == "ab"


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
