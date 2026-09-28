from __future__ import annotations

import pytest

from agent_app.json_projection import (
    JsonProjectionError,
    MAX_PROJECTION_SELECTOR_LENGTH,
    MAX_PROJECTION_SELECTORS,
    project_json_document,
)
from agent_app import json_projection


@pytest.fixture
def document() -> dict:
    return {
        "messages": [
            {
                "index": 0,
                "message": {
                    "role": "tool",
                    "content": "large tool result",
                    "metadata": {"tool_name": "shell"},
                },
            },
            {
                "index": 1,
                "message": {
                    "role": "assistant",
                    "content": "Crystal Lattice result",
                    "metadata": {
                        "reasoning": "Inspect the configuration",
                        "tool_calls": [{"id": "call-1"}],
                    },
                },
            },
            {
                "index": 2,
                "message": {
                    "role": "future-role",
                    "content": "Future content",
                    "metadata": {"kind": "custom-event"},
                },
            },
        ],
        "cursor_event_id": "event-1",
        "readonly": False,
    }


def test_no_selectors_returns_existing_document(document: dict) -> None:
    assert project_json_document(document) is document
    assert project_json_document(document, include=[], exclude=[]) is document


def test_include_union_reconstructs_ancestors_and_preserves_source_order(
    document: dict,
) -> None:
    projected = project_json_document(
        document,
        include=[
            "$.messages[*].message.metadata.reasoning",
            "$.messages[*].index",
            "$.messages[*].message.role",
            "$.messages[*].message.content",
        ],
    )

    assert projected == {
        "messages": [
            {
                "index": 0,
                "message": {
                    "role": "tool",
                    "content": "large tool result",
                },
            },
            {
                "index": 1,
                "message": {
                    "role": "assistant",
                    "content": "Crystal Lattice result",
                    "metadata": {"reasoning": "Inspect the configuration"},
                },
            },
            {
                "index": 2,
                "message": {
                    "role": "future-role",
                    "content": "Future content",
                },
            },
        ]
    }


def test_exclude_uses_original_discriminator_and_removes_array_entry(
    document: dict,
) -> None:
    projected = project_json_document(
        document,
        include=[
            "$.messages[*].index",
            "$.messages[*].message.content",
        ],
        exclude=['$.messages[?(@.message.role == "tool")]'],
    )

    assert projected == {
        "messages": [
            {
                "index": 1,
                "message": {"content": "Crystal Lattice result"},
            },
            {
                "index": 2,
                "message": {"content": "Future content"},
            },
        ]
    }
    assert [message["index"] for message in projected["messages"]] == [1, 2]


def test_selected_subtree_can_exclude_nested_heavy_data(document: dict) -> None:
    projected = project_json_document(
        document,
        include=["$.messages[1].message"],
        exclude=["$.messages[1].message.metadata.tool_calls"],
    )

    assert projected == {
        "messages": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Crystal Lattice result",
                    "metadata": {"reasoning": "Inspect the configuration"},
                }
            }
        ]
    }


def test_wildcards_and_future_discriminators_need_no_role_registry(
    document: dict,
) -> None:
    projected = project_json_document(
        document,
        include=[
            '$.messages[?(@.message.metadata.kind == "custom-event")].index',
            '$.messages[?(@.message.metadata.kind == "custom-event")].message.*',
        ],
    )

    assert projected == {
        "messages": [
            {
                "index": 2,
                "message": {
                    "role": "future-role",
                    "content": "Future content",
                    "metadata": {"kind": "custom-event"},
                },
            }
        ]
    }


def test_recursive_descent_and_root_selection_are_supported(document: dict) -> None:
    reasoning = project_json_document(
        document,
        include=["$..reasoning"],
    )
    assert reasoning == {
        "messages": [
            {"message": {"metadata": {"reasoning": "Inspect the configuration"}}}
        ]
    }

    complete = project_json_document(document, include=["$"])
    assert complete == document
    assert complete is not document


def test_valid_no_match_and_root_exclusion_are_deterministic(document: dict) -> None:
    assert (
        project_json_document(
            document,
            include=['$.messages[?(@.message.role == "missing")]'],
        )
        == {}
    )
    assert project_json_document(document, exclude=["$"]) is None


def test_projection_does_not_mutate_source(document: dict) -> None:
    original = {
        "messages": [
            {
                "index": message["index"],
                "message": {
                    key: (
                        value.copy()
                        if isinstance(value, dict)
                        else list(value) if isinstance(value, list) else value
                    )
                    for key, value in message["message"].items()
                },
            }
            for message in document["messages"]
        ],
        "cursor_event_id": "event-1",
        "readonly": False,
    }

    project_json_document(
        document,
        include=["$.messages[*].message"],
        exclude=["$.messages[*].message.metadata"],
    )

    assert document == original


def test_projected_json_size_is_bounded(
    document: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(json_projection, "MAX_PROJECTED_JSON_CHARACTERS", 20)

    with pytest.raises(JsonProjectionError, match="projected JSON exceeds 20"):
        project_json_document(
            document,
            include=["$.messages[*].message.content"],
        )


@pytest.mark.parametrize(
    ("include", "expected"),
    [
        ("$.messages[*]", "include must be a sequence"),
        (["messages[*]"], r"must start with '\$'"),
        (["$["], "invalid include JSONPath"),
        (["$" + ".x" * (MAX_PROJECTION_SELECTOR_LENGTH // 2 + 1)], "exceeds"),
        (["$"] * (MAX_PROJECTION_SELECTORS + 1), "at most"),
    ],
)
def test_projection_rejects_invalid_or_unbounded_selectors(
    document: dict,
    include: object,
    expected: str,
) -> None:
    with pytest.raises(JsonProjectionError, match=expected):
        project_json_document(document, include=include)  # type: ignore[arg-type]
