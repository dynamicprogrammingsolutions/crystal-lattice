"""Unit tests for OpenRouter reasoning extension."""

from __future__ import annotations

import pytest

from plugins.openrouter_reasoning_extension import OpenRouterReasoningExtension


def test_extension_name_and_version():
    """Extension has correct name and version."""
    ext = OpenRouterReasoningExtension()
    assert ext.name == "openrouter_reasoning"
    assert ext.version == "0.2.0"


def test_get_config_schema():
    """Config schema includes reasoning parameters."""
    ext = OpenRouterReasoningExtension()
    schema = ext.get_config_schema()

    assert "reasoning_effort" in schema
    assert schema["reasoning_effort"]["enum"] == ["low", "medium", "high"]

    assert "enable_reasoning" in schema
    assert schema["enable_reasoning"]["type"] == "boolean"

    assert "include_reasoning" in schema
    assert schema["include_reasoning"]["default"] is True


def test_get_tags():
    """Extension returns correct tags."""
    ext = OpenRouterReasoningExtension()
    config = {}
    models = []

    tags = ext.get_tags(config, models)

    assert "ext:openrouter_reasoning" in tags


def test_required_tags():
    """Extension requires openrouter provider and reasoning support."""
    ext = OpenRouterReasoningExtension()

    required = ext.required_tags()

    assert "openrouter" in required
    assert "supports_reasoning" in required


def test_init_when_disabled():
    """Init returns unchanged state when reasoning is disabled."""
    ext = OpenRouterReasoningExtension()
    config = {"enable_reasoning": False}
    state = {"config": config}

    new_state = ext.init(config, state)

    assert new_state == state
    assert "openrouter_reasoning" not in new_state


def test_init_when_enabled():
    """Init adds reasoning configuration to state."""
    ext = OpenRouterReasoningExtension()
    config = {
        "enable_reasoning": True,
        "reasoning_effort": "medium",
        "include_reasoning": True,
    }
    state = {"config": config}

    new_state = ext.init(config, state)

    assert "openrouter_reasoning" in new_state
    reasoning_config = new_state["openrouter_reasoning"]
    assert reasoning_config["enabled"] is True
    assert reasoning_config["effort"] == "medium"
    assert reasoning_config["include"] is True


def test_initialize_request_when_disabled():
    """Initialize request returns unchanged state when reasoning is disabled."""
    ext = OpenRouterReasoningExtension()
    state = {"request": {"payload": {"model": "test"}}}

    new_state = ext.initialize_request([], state)

    assert new_state == state


def test_initialize_request_adds_reasoning_parameters():
    """Initialize request adds reasoning parameters to payload."""
    ext = OpenRouterReasoningExtension()
    state = {
        "request": {"payload": {"model": "test"}},
        "openrouter_reasoning": {
            "enabled": True,
            "effort": "high",
            "include": True,
        },
    }

    new_state = ext.initialize_request([], state)

    payload = new_state["request"]["payload"]
    assert payload["reasoning_effort"] == "high"
    assert payload["include_reasoning"] is True


def test_initialize_request_without_effort():
    """Initialize request works without reasoning_effort."""
    ext = OpenRouterReasoningExtension()
    state = {
        "request": {"payload": {"model": "test"}},
        "openrouter_reasoning": {
            "enabled": True,
            "effort": None,
            "include": True,
        },
    }

    new_state = ext.initialize_request([], state)

    payload = new_state["request"]["payload"]
    assert "reasoning_effort" not in payload
    assert payload["include_reasoning"] is True


def test_to_native_messages_with_reasoning():
    """to_native_messages puts reasoning back into native format."""
    ext = OpenRouterReasoningExtension()
    messages = [
        {
            "role": "assistant",
            "content": "Answer",
            "metadata": {"reasoning": "Thought process"},
        }
    ]
    native_messages = [{"role": "assistant", "content": "Answer"}]

    enhanced = ext.to_native_messages(messages, native_messages)

    assert len(enhanced) == 1
    assert enhanced[0]["reasoning"] == "Thought process"


def test_from_native_messages_extracts_reasoning():
    """from_native_messages extracts reasoning into metadata."""
    ext = OpenRouterReasoningExtension()
    native_messages = [{"role": "assistant", "content": "Answer", "reasoning": "Thought process"}]
    messages = [{"role": "assistant", "content": "Answer", "metadata": {}}]

    enhanced = ext.from_native_messages(native_messages, messages)

    assert len(enhanced) == 1
    assert enhanced[0]["metadata"]["reasoning"] == "Thought process"


def test_extract_delta():
    """Extract delta from streaming chunk."""
    ext = OpenRouterReasoningExtension()
    chunk = {"choices": [{"delta": {"reasoning": "Step 1: "}}]}

    delta = ext.extract_delta(chunk)

    assert delta == {"delta": {"reasoning": "Step 1: "}}


def test_extract_delta_empty():
    """Extract delta returns empty dict for chunk without choices."""
    ext = OpenRouterReasoningExtension()
    chunk = {}

    delta = ext.extract_delta(chunk)

    assert delta == {}


def test_process_delta_accumulates_reasoning():
    """Process delta accumulates reasoning fragments."""
    ext = OpenRouterReasoningExtension()
    delta = {"delta": {"reasoning": "Step 1: "}}
    current_partial = {"role": "assistant", "content": "Answer"}
    accumulated = {}

    partial, final, new_accumulated = ext.process_delta(
        delta, current_partial=current_partial, accumulated=accumulated
    )

    assert partial["reasoning"] == "Step 1: "
    assert new_accumulated["reasoning"] == "Step 1: "
    assert final is None


def test_process_delta_full_message():
    """Process delta handles full message chunks with reasoning."""
    ext = OpenRouterReasoningExtension()
    delta = {
        "message": {
            "role": "assistant",
            "content": "Answer",
            "reasoning": "Complete reasoning",
        }
    }
    current_final = {"role": "assistant", "content": "Answer"}

    partial, final, accumulated = ext.process_delta(
        delta, current_final=current_final, accumulated={}
    )

    assert partial is None
    assert final["reasoning"] == "Complete reasoning"


def test_finalize_with_accumulated_reasoning():
    """Finalize attaches accumulated reasoning to final messages."""
    ext = OpenRouterReasoningExtension()
    final_messages = [{"role": "assistant", "content": "Answer"}]
    native_messages = [{"role": "assistant", "content": "Answer"}]
    state = {
        "openrouter_reasoning": {"enabled": True},
        "partial": {"reasoning": "Accumulated reasoning"},
    }

    finals, natives, new_state = ext.finalize(final_messages, native_messages, state)

    assert len(finals) == 1
    assert finals[0]["reasoning"] == "Accumulated reasoning"
    assert len(natives) == 1
    assert natives[0]["reasoning"] == "Accumulated reasoning"


def test_finalize_when_disabled():
    """Finalize returns unchanged when reasoning is disabled."""
    ext = OpenRouterReasoningExtension()
    final_messages = [{"role": "assistant", "content": "Answer"}]
    native_messages = [{"role": "assistant", "content": "Answer"}]
    state = {"partial": {"reasoning": "Should be ignored"}}

    finals, natives, new_state = ext.finalize(final_messages, native_messages, state)

    assert finals == final_messages
    assert natives == native_messages


def test_finalize_without_accumulated_reasoning():
    """Finalize returns unchanged when no reasoning accumulated."""
    ext = OpenRouterReasoningExtension()
    final_messages = [{"role": "assistant", "content": "Answer"}]
    native_messages = [{"role": "assistant", "content": "Answer"}]
    state = {
        "openrouter_reasoning": {"enabled": True},
        "partial": {},
    }

    finals, natives, new_state = ext.finalize(final_messages, native_messages, state)

    assert finals == final_messages
    assert natives == native_messages


def test_accumulate_reasoning_details_text_multiple_chunks():
    """Accumulate text field across multiple chunks."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {"type": "reasoning.text", "text": "Step 1: ", "format": "google-gemini-v1", "index": 0}
    ]

    delta_details = [
        {
            "type": "reasoning.text",
            "text": "Add the numbers. ",
            "format": "google-gemini-v1",
            "index": 0,
        }
    ]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 1
    assert result[0]["text"] == "Step 1: Add the numbers. "
    assert result[0]["type"] == "reasoning.text"


def test_accumulate_reasoning_details_signature_multiple_chunks():
    """Accumulate signature field across multiple chunks (Anthropic)."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {
            "type": "reasoning.text",
            "text": "Complete text",
            "signature": "abc123",
            "format": "anthropic-claude-v1",
            "index": 0,
        }
    ]

    delta_details = [
        {
            "type": "reasoning.text",
            "signature": "def456",
            "format": "anthropic-claude-v1",
            "index": 0,
        }
    ]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 1
    assert result[0]["signature"] == "abc123def456"  # Accumulated, not overridden!
    assert result[0]["text"] == "Complete text"


def test_accumulate_reasoning_details_data_multiple_chunks():
    """Accumulate encrypted data across multiple chunks (OpenAI/xAI)."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {
            "type": "reasoning.encrypted",
            "data": "chunk1_",
            "id": "rs_123",
            "format": "openai-responses-v1",
            "index": 0,
        }
    ]

    delta_details = [
        {
            "type": "reasoning.encrypted",
            "data": "chunk2_",
            "id": "rs_123",
            "format": "openai-responses-v1",
            "index": 0,
        }
    ]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 1
    assert result[0]["data"] == "chunk1_chunk2_"  # Accumulated
    assert result[0]["id"] == "rs_123"  # Preserved


def test_accumulate_reasoning_details_summary_multiple_chunks():
    """Accumulate summary field across multiple chunks (OpenAI)."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {
            "type": "reasoning.summary",
            "summary": "First part. ",
            "format": "openai-responses-v1",
            "index": 0,
        }
    ]

    delta_details = [
        {
            "type": "reasoning.summary",
            "summary": "Second part.",
            "format": "openai-responses-v1",
            "index": 0,
        }
    ]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 1
    assert result[0]["summary"] == "First part. Second part."  # Accumulated, not overridden!


def test_accumulate_reasoning_details_multiple_types():
    """Accumulate multiple reasoning detail types."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {
            "type": "reasoning.summary",
            "summary": "Sum: ",
            "format": "openai-responses-v1",
            "index": 0,
        },
        {
            "type": "reasoning.encrypted",
            "data": "enc1",
            "id": "rs_1",
            "format": "openai-responses-v1",
            "index": 1,
        },
    ]

    delta_details = [
        {
            "type": "reasoning.summary",
            "summary": "Complete.",
            "format": "openai-responses-v1",
            "index": 0,
        },
        {
            "type": "reasoning.encrypted",
            "data": "enc2",
            "id": "rs_1",
            "format": "openai-responses-v1",
            "index": 1,
        },
    ]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 2
    assert result[0]["summary"] == "Sum: Complete."
    assert result[1]["data"] == "enc1enc2"


def test_accumulate_reasoning_details_new_detail():
    """Add new detail when no matching detail exists."""
    ext = OpenRouterReasoningExtension()

    current_details = [{"type": "reasoning.summary", "summary": "Summary", "index": 0}]

    delta_details = [{"type": "reasoning.text", "text": "New text", "index": 1}]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 2
    assert result[0]["type"] == "reasoning.summary"
    assert result[1]["type"] == "reasoning.text"
    assert result[1]["text"] == "New text"


def test_accumulate_reasoning_details_match_by_id():
    """Match details by id when present."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {"type": "reasoning.encrypted", "data": "d1", "id": "rs_abc", "index": 0},
        {"type": "reasoning.encrypted", "data": "d2", "id": "rs_def", "index": 1},
    ]

    delta_details = [{"type": "reasoning.encrypted", "data": "_more", "id": "rs_def", "index": 1}]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 2
    assert result[0]["data"] == "d1"
    assert result[1]["data"] == "d2_more"  # Matched by id


def test_accumulate_reasoning_details_empty_current():
    """Return delta details when current is empty."""
    ext = OpenRouterReasoningExtension()

    delta_details = [{"type": "reasoning.text", "text": "First chunk", "index": 0}]

    result = ext._accumulate_reasoning_details(None, delta_details)

    assert len(result) == 1
    assert result[0]["text"] == "First chunk"


def test_accumulate_reasoning_details_empty_delta():
    """Return current details when delta is empty."""
    ext = OpenRouterReasoningExtension()

    current_details = [{"type": "reasoning.text", "text": "Existing", "index": 0}]

    result = ext._accumulate_reasoning_details(current_details, None)

    assert len(result) == 1
    assert result[0]["text"] == "Existing"
