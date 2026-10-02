from __future__ import annotations

import pytest

from agent_app.history_projection import (
    get_canonical_message,
    project_session_history,
)
from agent_core import Message, Session


def _session() -> Session:
    return Session(
        session_id="history-session",
        messages=[
            Message(
                role="system",
                content="System instructions",
                metadata={"native_indices": [0], "secret": "not projected"},
            ),
            Message(role="user", content="  First\nquestion  "),
            Message(
                role="assistant",
                content="I will inspect that.",
                metadata={
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "function": {
                                "name": "read_file",
                                "arguments": '{"path": "secret"}',
                            },
                        }
                    ]
                },
            ),
            Message(
                role="tool",
                content="very long raw output " * 100,
                metadata={
                    "tool_name": "read_file",
                    "tool_call_id": "call-1",
                    "success": True,
                    "display": {
                        "type": "text",
                        "content": "full display output " * 50,
                        "single_line": "Read: README.md",
                    },
                    "native_response": {"authorization": "secret"},
                },
                multipart_content=[
                    {
                        "type": "image",
                        "data": "base64-data-that-must-not-be-projected",
                    }
                ],
            ),
            Message(role="assistant", content="Final answer with details"),
        ],
        metadata={
            "native_messages": [{"authorization": "session-secret"}],
        },
    )


def test_compact_history_preserves_indices_and_uses_tool_display() -> None:
    session = _session()
    before = session.to_dict()

    result = project_session_history(session)

    assert [message.index for message in result.messages] == [0, 1, 2, 3, 4]
    tool = result.messages[3]
    assert tool.role == "tool"
    assert tool.content == "Read: README.md"
    assert tool.content_length == len(session.messages[3].content)
    assert tool.content_truncated is True
    assert tool.content_omitted is False
    assert tool.tool_name == "read_file"
    assert tool.tool_call_id == "call-1"
    assert tool.tool_status == "succeeded"
    serialized = result.to_dict()
    serialized_text = repr(serialized)
    assert "base64-data" not in serialized_text
    assert "authorization" not in serialized_text
    assert "native_response" not in serialized_text
    assert session.to_dict() == before


def test_compact_history_applies_range_before_role_filtering() -> None:
    result = project_session_history(
        _session(),
        start=1,
        end=4,
        roles={"assistant", "tool"},
    )

    assert [message.index for message in result.messages] == [2, 3]
    assert result.selected_message_count == 2
    assert result.omitted_message_count == 0


def test_compact_history_keeps_newest_rows_and_budgets_newest_content_first() -> None:
    result = project_session_history(
        _session(),
        max_messages=3,
        max_content_chars=10,
        max_total_content_chars=12,
    )

    assert [message.index for message in result.messages] == [2, 3, 4]
    assert result.selected_message_count == 5
    assert result.omitted_message_count == 2
    assert result.content_characters == 12
    assert result.messages[0].content == ""
    assert result.messages[0].content_omitted is True
    assert result.messages[1].content == "Re"
    assert result.messages[2].content == "Final answ"


def test_compact_history_normalizes_non_tool_text() -> None:
    result = project_session_history(_session(), start=1, end=2)

    assert result.messages[0].content == "First question"
    assert result.messages[0].content_length == len("  First\nquestion  ")


def test_compact_history_omits_non_text_content_without_serializing_it() -> None:
    session = Session(
        session_id="non-text",
        messages=[
            Message(
                role="user",
                content={"inline": "binary-like-value"},
            )
        ],
    )

    result = project_session_history(session)

    assert result.messages[0].content == ""
    assert result.messages[0].content_omitted is True
    assert result.messages[0].content_truncated is True
    assert "binary-like-value" not in repr(result.to_dict())


def test_full_message_lookup_supports_negative_index_and_keeps_full_fields() -> None:
    session = _session()

    result = get_canonical_message(session, -2)

    assert result["index"] == 3
    assert result["message"]["content"] == session.messages[3].content
    assert result["message"]["multipartContent"][0]["data"].startswith("base64")
    assert result["message"]["metadata"]["native_response"]["authorization"] == "secret"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_messages": 0}, "max_messages"),
        ({"max_content_chars": -1}, "max_content_chars"),
        ({"max_total_content_chars": -1}, "max_total_content_chars"),
        ({"roles": {"invalid"}}, "roles"),
        ({"roles": "tool"}, "roles"),
    ],
)
def test_compact_history_rejects_invalid_options(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        project_session_history(_session(), **kwargs)


@pytest.mark.parametrize("index", [5, -6, True, "1"])
def test_full_message_lookup_rejects_invalid_index(index: object) -> None:
    error = ValueError if isinstance(index, (bool, str)) else IndexError
    with pytest.raises(error):
        get_canonical_message(_session(), index)  # type: ignore[arg-type]
