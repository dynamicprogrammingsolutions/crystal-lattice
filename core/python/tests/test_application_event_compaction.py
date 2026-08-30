from __future__ import annotations

from typing import Any, Dict, List

from agent_app.application_future import AgentApplication


def _compactor() -> AgentApplication:
    app = AgentApplication.__new__(AgentApplication)
    app._enable_event_compaction = True
    app._enable_drop_redundant_partials = True
    app._enable_merge_consecutive_partials = True
    return app


def _tool_partial(
    *,
    request_id: str,
    call_id: str,
    phase: str,
    message_index: int | None = None,
) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "type": "tool_partial",
        "session_id": "session-1",
        "request_id": request_id,
        "tool_call_id": call_id,
        "phase": phase,
        "payload": (
            {
                "result": {
                    "role": "tool",
                    "content": f"{call_id}-result",
                    "metadata": {"tool_call_id": call_id, "tool_name": "demo"},
                }
            }
            if phase == "end"
            else {"part": {"type": "text", "content": f"{phase}\n"}}
        ),
    }
    if message_index is not None:
        event["message_index"] = message_index
    return event


def test_compact_events_preserves_tool_end_and_drops_redundant_stream_chunks() -> None:
    end_event = _tool_partial(
        request_id="request-1",
        call_id="call-1",
        phase="end",
        message_index=7,
    )
    end_event["event_id"] = "event-end"
    end_event["future_field"] = {"kept": True}

    events: List[Dict[str, Any]] = [
        _tool_partial(request_id="request-1", call_id="call-1", phase="start"),
        _tool_partial(request_id="request-1", call_id="call-1", phase="stream"),
        end_event,
        {
            "type": "tool_results",
            "session_id": "session-1",
            "request_id": "request-1",
            "messages": [],
        },
        {
            "type": "session_checkpoint",
            "session_id": "session-1",
            "request_id": "request-1",
        },
    ]

    compacted = _compactor().compact_events(events)

    assert [event["type"] for event in compacted] == [
        "tool_partial",
        "tool_results",
        "session_checkpoint",
    ]
    assert compacted[0] == end_event


def test_compact_events_preserves_each_tool_end_in_call_order() -> None:
    end_one = _tool_partial(
        request_id="request-1",
        call_id="call-1",
        phase="end",
        message_index=7,
    )
    end_two = _tool_partial(
        request_id="request-1",
        call_id="call-2",
        phase="end",
        message_index=8,
    )
    other_request_stream = _tool_partial(
        request_id="request-2",
        call_id="call-other",
        phase="stream",
    )

    compacted = _compactor().compact_events(
        [
            end_one,
            end_two,
            {
                "type": "tool_results",
                "session_id": "session-1",
                "request_id": "request-1",
                "messages": [],
            },
            other_request_stream,
        ]
    )

    assert compacted == [
        end_one,
        end_two,
        {
            "type": "tool_results",
            "session_id": "session-1",
            "request_id": "request-1",
            "messages": [],
        },
        other_request_stream,
    ]


def test_compact_events_keeps_legacy_tool_partial_dropping_behavior() -> None:
    legacy_partial = {
        "type": "tool_partial",
        "session_id": "session-1",
        "request_id": "request-1",
        "tool_call_id": "call-1",
        "payload": {"partial": {"type": "text", "content": "legacy"}},
    }

    compacted = _compactor().compact_events(
        [
            legacy_partial,
            {
                "type": "tool_results",
                "session_id": "session-1",
                "request_id": "request-1",
                "messages": [],
            },
        ]
    )

    assert [event["type"] for event in compacted] == ["tool_results"]
