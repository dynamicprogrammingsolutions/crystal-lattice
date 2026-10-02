from __future__ import annotations

import csv
from io import StringIO
import json

from agent_terminal_app.query_rendering import (
    render_messages_document,
    render_sessions_document,
)


def test_session_id_projection_is_one_undecorated_value_per_text_line() -> None:
    document = {
        "sessions": [
            {"session_id": "session-a"},
            {"session_id": "session-b"},
        ]
    }

    assert render_sessions_document(document, "text") == "session-a\nsession-b\n"
    assert json.loads(render_sessions_document(document, "json")) == document


def test_message_text_is_grep_friendly_and_has_identity_context() -> None:
    document = {
        "messages": [
            {
                "index": 12,
                "message": {
                    "role": "assistant",
                    "content": "Crystal\n  Lattice result",
                    "metadata": {
                        "reasoning": "Inspect\tthe configuration",
                    },
                },
            }
        ]
    }

    assert render_messages_document(
        document,
        "text",
        session_id="session-a",
    ) == (
        "session-a [12] assistant content: Crystal Lattice result\n"
        "session-a [12] assistant metadata.reasoning: Inspect the configuration\n"
    )


def test_message_tsv_and_csv_keep_one_physical_record_per_leaf() -> None:
    document = {
        "messages": [
            {
                "index": 1,
                "message": {
                    "role": "future-role",
                    "content": "line one\nline two, still content",
                    "metadata": {"items": ["a", "b"]},
                },
            }
        ]
    }

    tsv = render_messages_document(document, "tsv", session_id="session")
    assert len(tsv.splitlines()) == 3
    assert "line one line two, still content" in tsv

    csv_text = render_messages_document(document, "csv", session_id="session")
    rows = list(csv.reader(StringIO(csv_text)))
    assert rows[0] == ["session_id", "index", "role", "path", "value"]
    assert rows[1] == [
        "session",
        "1",
        "future-role",
        "content",
        "line one line two, still content",
    ]
    assert rows[2] == [
        "session",
        "1",
        "future-role",
        "metadata.items",
        '["a","b"]',
    ]
    assert len(csv_text.splitlines()) == 3
