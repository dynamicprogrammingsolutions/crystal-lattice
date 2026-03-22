from __future__ import annotations

from reference_openai_compatible_provider.reasoning_extension import (
    OpenAICompatibleReasoningExtension,
)


def test_reasoning_extension_does_not_expose_package_owned_think_config():
    ext = OpenAICompatibleReasoningExtension()
    assert ext.get_config_schema() == {}
    assert ext.get_ui_elements({}, [], []) == []


def test_reasoning_extension_extracts_reasoning_string_fragments():
    ext = OpenAICompatibleReasoningExtension()

    patch1, acc1 = ext.process_delta(
        {"delta": {"reasoning": "step 1"}},
        {},
    )
    patch2, acc2 = ext.process_delta(
        {"delta": {"reasoning": " + step 2"}},
        acc1,
    )

    assert patch1 == {"reasoning": "step 1"}
    assert patch2 == {"reasoning": " + step 2"}
    assert acc2["reasoning"] == "step 1 + step 2"


def test_reasoning_extension_extracts_reasoning_content_fragments():
    ext = OpenAICompatibleReasoningExtension()

    patch1, acc1 = ext.process_delta(
        {"delta": {"reasoning_content": "alpha"}},
        {},
    )
    patch2, acc2 = ext.process_delta(
        {"delta": {"reasoning_content": " beta"}},
        acc1,
    )

    assert patch1 == {"reasoning": "alpha"}
    assert patch2 == {"reasoning": " beta"}
    assert acc2["reasoning_content"] == "alpha beta"


def test_reasoning_extension_prioritizes_reasoning_for_patch_when_both_fields_exist():
    ext = OpenAICompatibleReasoningExtension()

    patch, acc = ext.process_delta(
        {"delta": {"reasoning": "summary", "reasoning_content": "raw details"}},
        {},
    )

    assert patch == {"reasoning": "summary"}
    assert acc["reasoning"] == "summary"
    assert acc["reasoning_content"] == "raw details"


def test_reasoning_extension_round_trips_native_reasoning_fields():
    ext = OpenAICompatibleReasoningExtension()
    messages = [
        {
            "role": "assistant",
            "content": "done",
            "metadata": {
                "reasoning": "chain",
                "reasoning_content": "raw chain",
            },
        }
    ]
    native_messages = [{"role": "assistant", "content": "done"}]

    native_out = ext.to_native_messages(messages, native_messages)
    assert native_out == [
        {
            "role": "assistant",
            "content": "done",
            "reasoning": "chain",
            "reasoning_content": "raw chain",
        }
    ]

    rebuilt = ext.from_native_messages(
        native_out, [{"role": "assistant", "content": "done"}]
    )
    assert rebuilt[0]["metadata"] == {
        "reasoning": "chain",
        "reasoning_content": "raw chain",
    }


def test_reasoning_extension_returns_messages_unchanged_on_length_mismatch():
    ext = OpenAICompatibleReasoningExtension()
    messages = [{"role": "assistant", "content": "done", "metadata": {}}]
    native_messages = [
        {"role": "assistant", "content": "ignored"},
        {"role": "assistant", "content": "done", "reasoning_content": "fallback"},
    ]

    rebuilt = ext.from_native_messages(native_messages, messages)
    assert rebuilt == messages
