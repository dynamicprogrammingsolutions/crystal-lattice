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


def test_reasoning_extension_from_native_aliases_reasoning_content_to_reasoning():
    ext = OpenAICompatibleReasoningExtension()

    rebuilt = ext.from_native_messages(
        [{"role": "assistant", "content": "done", "reasoning_content": "alpha beta"}],
        [{"role": "assistant", "content": "done", "metadata": {}}],
    )

    # Only canonical "reasoning" field in metadata
    assert rebuilt[0]["metadata"]["reasoning"] == "alpha beta"
    assert "reasoning_content" not in rebuilt[0]["metadata"]


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
    # Core messages store reasoning in canonical "reasoning" metadata field
    messages = [
        {
            "role": "assistant",
            "content": "done",
            "metadata": {
                "reasoning": "chain",
            },
        }
    ]
    native_messages = [{"role": "assistant", "content": "done"}]

    # to_native_messages reads from canonical "reasoning" and writes to all native fields
    native_out = ext.to_native_messages(messages, native_messages)
    assert native_out == [
        {
            "role": "assistant",
            "content": "done",
            "reasoning": "chain",
            "reasoning_content": "chain",
        }
    ]

    # from_native_messages reads from native fields and writes to canonical "reasoning"
    rebuilt = ext.from_native_messages(
        native_out, [{"role": "assistant", "content": "done"}]
    )
    assert rebuilt[0]["metadata"] == {
        "reasoning": "chain",
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


def test_reasoning_extension_process_chunk_updates_accumulator_without_emitting_partial():
    ext = OpenAICompatibleReasoningExtension()

    partials, _finals, _native, new_state = ext.process_chunk(
        {"choices": [{"delta": {"reasoning_content": "alpha"}}]},
        [],
        [],
        [],
        {"partial": {"role": "assistant", "content": ""}},
    )

    assert partials == []
    assert new_state["partial"]["reasoning_content"] == "alpha"


# Tests for reasoning_field config functionality


def test_reasoning_extension_init_stores_reasoning_field_in_state():
    ext = OpenAICompatibleReasoningExtension()

    # When reasoning_field is set in config
    state = ext.init({"reasoning_field": "custom_reasoning"}, {})
    assert state["reasoning_field"] == "custom_reasoning"

    # When reasoning_field is not set
    state = ext.init({}, {})
    assert "reasoning_field" not in state


def test_reasoning_extension_to_native_messages_uses_configured_field():
    ext = OpenAICompatibleReasoningExtension()
    state = ext.init({"reasoning_field": "custom_reasoning"}, {})

    # Core messages have canonical "reasoning" in metadata
    messages = [
        {
            "role": "assistant",
            "content": "done",
            "metadata": {
                "reasoning": "my reasoning",
            },
        }
    ]
    native_messages = [{"role": "assistant", "content": "done"}]

    native_out = ext.to_native_messages(messages, native_messages, state)

    # Reads from canonical "reasoning" and writes to configured native field
    assert native_out == [
        {
            "role": "assistant",
            "content": "done",
            "custom_reasoning": "my reasoning",
        }
    ]


def test_reasoning_extension_to_native_messages_uses_all_fields_when_not_configured():
    ext = OpenAICompatibleReasoningExtension()
    state = ext.init({}, {})

    # Core messages have canonical "reasoning" in metadata
    messages = [
        {
            "role": "assistant",
            "content": "done",
            "metadata": {
                "reasoning": "chain",
            },
        }
    ]
    native_messages = [{"role": "assistant", "content": "done"}]

    native_out = ext.to_native_messages(messages, native_messages, state)

    # Reads from canonical "reasoning" and writes to all native fields
    assert native_out == [
        {
            "role": "assistant",
            "content": "done",
            "reasoning": "chain",
            "reasoning_content": "chain",
        }
    ]


def test_reasoning_extension_from_native_messages_uses_configured_field():
    ext = OpenAICompatibleReasoningExtension()
    state = ext.init({"reasoning_field": "custom_reasoning"}, {})

    native_messages = [
        {
            "role": "assistant",
            "content": "done",
            "custom_reasoning": "only this",
            "reasoning": "should be ignored",
        }
    ]
    messages = [{"role": "assistant", "content": "done", "metadata": {}}]

    rebuilt = ext.from_native_messages(native_messages, messages, state)

    # Only custom_reasoning should be extracted, stored in canonical "reasoning"
    assert rebuilt[0]["metadata"]["reasoning"] == "only this"
    assert "custom_reasoning" not in rebuilt[0]["metadata"]
    assert "reasoning_content" not in rebuilt[0]["metadata"]


def test_reasoning_extension_process_delta_uses_configured_field():
    ext = OpenAICompatibleReasoningExtension()
    state = ext.init({"reasoning_field": "custom_reasoning"}, {})

    # Process delta with custom_reasoning field
    patch, acc = ext.process_delta(
        {"delta": {"custom_reasoning": "step 1"}},
        {},
        state,
    )

    assert patch == {"reasoning": "step 1"}
    assert acc["custom_reasoning"] == "step 1"

    # Process delta with reasoning field (should be ignored when custom_reasoning is configured)
    patch2, acc2 = ext.process_delta(
        {"delta": {"reasoning": "should be ignored"}},
        acc,
        state,
    )

    assert patch2 is None  # No patch because custom_reasoning wasn't in this delta


def test_reasoning_extension_process_chunk_uses_configured_field():
    ext = OpenAICompatibleReasoningExtension()
    state = ext.init({"reasoning_field": "custom_reasoning"}, {})

    partials, _finals, _native, new_state = ext.process_chunk(
        {"choices": [{"delta": {"custom_reasoning": "alpha"}}]},
        [],
        [],
        [],
        {"partial": {"role": "assistant", "content": ""}, **state},
    )

    assert partials == []
    assert new_state["partial"]["custom_reasoning"] == "alpha"


def test_reasoning_extension_round_trip_with_configured_field():
    """Test full round trip with a configured reasoning_field."""
    ext = OpenAICompatibleReasoningExtension()
    state = ext.init({"reasoning_field": "thinking"}, {})

    # Native messages with thinking field
    native_messages = [
        {"role": "assistant", "content": "done", "thinking": "my thought process"}
    ]

    # Convert to core messages - stores in canonical "reasoning"
    core_messages = [{"role": "assistant", "content": "done", "metadata": {}}]
    rebuilt = ext.from_native_messages(native_messages, core_messages, state)

    assert rebuilt[0]["metadata"]["reasoning"] == "my thought process"
    assert "thinking" not in rebuilt[0]["metadata"]

    # Convert back to native - reads from canonical "reasoning", writes to "thinking"
    native_out = ext.to_native_messages(rebuilt, [{"role": "assistant", "content": "done"}], state)

    # Only thinking field should be present in native
    assert native_out == [
        {
            "role": "assistant",
            "content": "done",
            "thinking": "my thought process",
        }
    ]