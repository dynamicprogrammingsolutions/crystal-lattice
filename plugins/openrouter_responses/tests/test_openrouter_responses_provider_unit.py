from __future__ import annotations

from typing import Any, Dict, List

from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider


def _apply_events(
    provider: OpenRouterResponsesProvider,
    events: List[Dict[str, Any]],
    *,
    state: Dict[str, Any] | None = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    native_messages: List[Dict[str, Any]] = []
    state = state or {"config": {"model": "test", "api_key": "x"}}

    partials_out: List[Dict[str, Any]] = []
    finals_out: List[Dict[str, Any]] = []

    for ev in events:
        partials, finals, native_messages, state = provider.process_chunk(ev, native_messages, state)
        partials_out.extend(partials)
        finals_out.extend(finals)

    return partials_out, finals_out, native_messages, state


def test_responses_streaming_accumulates_text_and_tool_calls() -> None:
    provider = OpenRouterResponsesProvider()

    events = [
        {"type": "response.created", "response": {"id": "resp_123"}},
        {
            "type": "response.output_item.added",
            "item": {"id": "fc_1", "type": "function_call", "call_id": "call_1", "name": "add"},
        },
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": "{\"a\": 1,",
        },
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": " \"b\": 2}",
        },
        {
            "type": "response.function_call_arguments.done",
            "item_id": "fc_1",
            "name": "add",
            "arguments": "{\"a\": 1, \"b\": 2}",
        },
        {"type": "response.output_text.delta", "delta": "OK"},
        {
            "type": "response.completed",
            "response": {
                "id": "resp_123",
                "usage": {"input_tokens": 1, "output_tokens": 2},
                "output": [
                    {"type": "function_call", "call_id": "call_1", "name": "add", "arguments": "{\"a\": 1, \"b\": 2}"},
                    {"type": "message", "content": [{"type": "output_text", "text": "OK"}]},
                ],
            },
        },
    ]

    partials, finals, native_messages, _state = _apply_events(provider, events)

    # text deltas are forwarded as partials
    assert any(p.get("role") == "assistant" and p.get("content") == "OK" for p in partials)

    # completed response yields native output items unchanged
    assert finals and isinstance(finals[-1], dict)
    assert finals[0].get("type") == "function_call"
    assert finals[0].get("call_id") == "call_1"
    assert finals[0].get("name") == "add"
    assert finals[0].get("arguments") == "{\"a\": 1, \"b\": 2}"

    last = finals[-1]
    assert last.get("type") == "message"
    content = last.get("content")
    assert isinstance(content, list)
    assert any(isinstance(p, dict) and p.get("type") == "output_text" and p.get("text") == "OK" for p in content)

    md = last.get("_metadata")
    assert isinstance(md, dict)
    assert md.get("response_id") == "resp_123"
    assert isinstance(md.get("usage"), dict)

    core = provider.from_native_messages(finals, {})
    assert any(
        m.get("role") == "assistant"
        and isinstance((m.get("metadata") or {}).get("usage"), dict)
        and (m.get("metadata") or {}).get("response_id") == "resp_123"
        for m in core
    )

    assert native_messages and native_messages[-2:] == finals


def test_responses_streaming_emits_reasoning_summary_partials() -> None:
    provider = OpenRouterResponsesProvider()
    state: Dict[str, Any] = {"config": {"model": "test", "api_key": "x"}}

    partials, _finals, _native, state = provider.process_chunk(
        {"type": "response.reasoning_summary_text.delta", "delta": " hello"},
        [],
        state,
    )
    assert partials
    last = partials[-1]
    assert last.get("role") == "assistant"
    assert last.get("content") == ""
    md = last.get("_metadata")
    assert isinstance(md, dict)
    assert md.get("reasoning") == " hello"


def test_completed_output_phase_final_answer_preferred() -> None:
    provider = OpenRouterResponsesProvider()
    obj: Dict[str, Any] = {
        "id": "resp_1",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "phase": "commentary",
                "content": [{"type": "output_text", "text": "COMMENT"}],
            },
            {
                "type": "message",
                "role": "assistant",
                "phase": "final_answer",
                "content": [{"type": "output_text", "text": "FINAL"}],
            },
        ],
    }
    _partials, finals, native_messages, _state = provider.process_chunk(
        {"type": "response.completed", "response": obj},
        [],
        {"config": {"model": "test", "api_key": "x"}},
    )

    assert finals and isinstance(finals[-1], dict)
    # Provider attaches response-level metadata (response_id) to the assistant
    # final_answer message item. Phase summaries are derived from the native
    # items in from_native_messages.
    annotated = next(
        (
            item
            for item in finals
            if isinstance(item, dict)
            and item.get("type") == "message"
            and item.get("phase") == "final_answer"
        ),
        None,
    )
    assert isinstance(annotated, dict)
    md_native = annotated.get("_metadata")
    assert isinstance(md_native, dict)
    assert md_native.get("response_id") == "resp_1"

    core = provider.from_native_messages(finals, {})
    assert any(
        isinstance(m, dict)
        and m.get("role") == "assistant"
        and m.get("content") == "COMMENT"
        and isinstance(m.get("metadata"), dict)
        and (m.get("metadata") or {}).get("phase") == "commentary"
        for m in core
    )
    assert any(
        isinstance(m, dict)
        and m.get("role") == "assistant"
        and m.get("content") == "FINAL"
        and isinstance(m.get("metadata"), dict)
        and (m.get("metadata") or {}).get("phase") == "final_answer"
        for m in core
    )

    assert native_messages == finals
