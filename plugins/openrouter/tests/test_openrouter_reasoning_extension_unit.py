"""Unit tests for OpenRouter reasoning extension."""

from __future__ import annotations

from agent_core import AgentCore, Session, Message
from openrouter_plugins.openrouter_provider import OpenRouterProvider
from openrouter_plugins.openrouter_reasoning_extension import OpenRouterReasoningExtension



def test_extension_name_and_version():
    """Extension has correct name and version."""
    ext = OpenRouterReasoningExtension()
    assert ext.name == "openrouter_reasoning"
    assert ext.version == "0.2.0"


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
    }
    state = {"config": config}

    new_state = ext.init(config, state)

    assert "openrouter_reasoning" in new_state
    reasoning_config = new_state["openrouter_reasoning"]
    assert reasoning_config["reasoning"]["enabled"] is True


def test_initialize_request_when_disabled():
    """Initialize request returns unchanged state when reasoning is disabled."""
    ext = OpenRouterReasoningExtension()
    state = {"request": {"payload": {"model": "test"}}}

    new_state = ext.initialize_request([], state)

    assert new_state == state


def test_initialize_request_adds_reasoning_parameters():
    """Initialize request adds reasoning parameters to payload."""
    ext = OpenRouterReasoningExtension()

    config = {
        "enable_reasoning": True,
        "reasoning_effort": "high"
    }
    state = {"config": config}

    state = ext.init(config, state)

    state = ext.initialize_request([], state)

    payload = state["request"]["payload"]
    assert payload["reasoning"]["effort"] == "high"
    assert payload["reasoning"]["enabled"] is True


def test_initialize_request_without_effort():
    """Initialize request works without reasoning_effort."""
    ext = OpenRouterReasoningExtension()
    config = {
        "enable_reasoning": True
    }
    state = {"config": config}

    state = ext.init(config, state)

    state = ext.initialize_request([], state)

    payload = state["request"]["payload"]
    assert "effort" not in payload["reasoning"]
    assert payload["reasoning"]["enabled"] is True


def test_to_native_messages_is_identity():
    """to_native_messages leaves native messages unchanged."""
    ext = OpenRouterReasoningExtension()
    messages = [
        {
            "role": "assistant",
            "content": "Answer",
            "metadata": {"reasoning": "Thought process"},
        }
    ]
    native_messages = [{"role": "assistant", "content": "Answer"}]

    enhanced = ext.to_native_messages(messages, list(native_messages))

    assert enhanced == native_messages
    assert "reasoning" not in enhanced[0]



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
    current_partial = {"role": "assistant", "content": "Answer", "reasoning": "Step 1: "}
    accumulated = {}

    partial, new_accumulated = ext.process_delta(
        delta, current_partial=current_partial, accumulated=accumulated
    )

    print("partial:", partial, "\nacc:", new_accumulated)

    assert partial["reasoning"] == "Step 1: "
    assert new_accumulated["reasoning"] == "Step 1: "


def test_process_delta_accumulates_reasoning_details():
    """Process delta accumulates reasoning fragments."""
    ext = OpenRouterReasoningExtension()
    delta = {"delta": {"role": "assistant", "content": "Answer", "reasoning": "Step 1: ", "reasoning_details": [{ "data": "ENCRYPTED" }]}}
    current_partial = {"role": "assistant", "content": "Answer", "reasoning": "Step 1: ", "reasoning_details": [{ "data": "ENCRYPTED" }]}
    accumulated = {"role": "assistant", "content": "Answer"}

    partial, new_accumulated = ext.process_delta(
        delta, current_partial=current_partial, accumulated=accumulated
    )

    print("partial:", partial, "\nacc:", new_accumulated)

    assert new_accumulated["reasoning"] == "Step 1: "
    assert new_accumulated["reasoning_details"][0]["data"] == "ENCRYPTED"
    assert partial["reasoning"] == "Step 1: "
    assert new_accumulated["reasoning"] == "Step 1: "


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
    partial, accumulated = ext.process_delta(
        delta, current_partial={}, accumulated={}
    )

    assert accumulated["reasoning"] == "Complete reasoning"

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


def test_accumulate_reasoning_details_different_id_same_index_does_not_merge():
    """Do not merge details with different ids even if (type, index) match."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {
            "type": "reasoning.encrypted",
            "data": "chunk1_",
            "id": "rs_111",
            "format": "openai-responses-v1",
            "index": 0,
        }
    ]

    delta_details = [
        {
            "type": "reasoning.encrypted",
            "data": "chunk2_",
            "id": "rs_222",
            "format": "openai-responses-v1",
            "index": 0,
        }
    ]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 2
    assert result[0]["id"] == "rs_111"
    assert result[0]["data"] == "chunk1_"
    assert result[1]["id"] == "rs_222"
    assert result[1]["data"] == "chunk2_"


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


def test_accumulate_reasoning_details_content_field_multiple_chunks():
    """Accumulate generic 'content' field across chunks (example scenario)."""
    ext = OpenRouterReasoningExtension()

    current_details = [
        {"type": "reasoning.test", "content": "A", "format": "unit-test", "index": 0}
    ]
    delta_details = [
        {"type": "reasoning.test", "content": "B", "format": "unit-test", "index": 0}
    ]

    result = ext._accumulate_reasoning_details(current_details, delta_details)

    assert len(result) == 1
    assert result[0]["content"] == "AB"



def test_retained_native_reasoning_details_preserved_in_pre_request():
    """Native reasoning_details from prior turn are preserved for next request."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])
    config = {
        "model": "openai/gpt-5-mini",
        "api_key": "sk-test",
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 5,
        "enable_reasoning": True,
    }

    messages = [
        Message(role="user", content="Hello", metadata={}),
        Message(role="assistant", content="World", metadata={}),
    ]

    reasoning_details = [
        {"type": "reasoning.test", "content": "AB", "format": "unit-test", "index": 0}
    ]
    native_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "World", "reasoning_details": reasoning_details},
    ]

    integrity = core._compute_native_integrity(messages)
    session = Session(
        session_id="test-session",
        messages=messages,
        metadata={
            "native_messages": native_messages,
            "native_messages_integrity": integrity,
        },
    )

    provider, exts, features, tools, tags = core._resolve_plugins_for_config(config)
    messages_out, native_out, state = core._pre_request(
        session,
        config,
        provider,
        features,
        tools,
    )

    assert native_out[-1].get("reasoning_details") == reasoning_details


class _DummyResponse:
    def __init__(self, obj):
        self._obj = obj
        self.status_code = 200
        self.reason = "OK"

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._obj


def test_reasoning_details_round_trip_non_streaming(monkeypatch):
    """End-to-end: reasoning_details from first turn appear in next payload."""
    calls = []

    def fake_post(url, json=None, headers=None, timeout=None, stream=False):
        call_index = len(calls)
        calls.append(json)
        if call_index == 0:
            response_obj = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "First",
                            "reasoning_details": [
                                {
                                    "type": "reasoning.test",
                                    "content": "AB",
                                    "format": "unit-test",
                                    "index": 0,
                                }
                            ],
                        }
                    }
                ]
            }
        else:
            response_obj = {
                "choices": [
                    {"message": {"role": "assistant", "content": "Second"}}
                ]
            }
        return _DummyResponse(response_obj)

    monkeypatch.setattr("openrouter_plugins.openrouter_provider.requests.post", fake_post)

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])
    config = {
        "model": "openai/gpt-5-mini",
        "api_key": "sk-test",
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 5,
        "enable_reasoning": True,
        "reasoning_effort": "low",
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    # First turn: provider returns reasoning_details "AB" which are stored in native history
    session, responses = core.send_request(session, config)
    assert responses[-1]["metadata"].get("reasoning_details")

    # Second turn: payload should include the same reasoning_details in messages
    session, responses2 = core.send_request(session, config)

    assert len(calls) == 2
    second_payload = calls[1]
    messages_payload = second_payload["messages"]
    last_native = messages_payload[-1]
    details = last_native.get("reasoning_details")
    assert details
    assert details[0].get("content") == "AB"

