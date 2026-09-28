from __future__ import annotations

from typing import Any

import pytest

from agent_terminal_app.session_query import (
    MAX_SESSION_FILTER_ASSIGNMENTS,
    MAX_SESSION_FILTER_ASSIGNMENT_LENGTH,
    coerce_session_filter_assignments,
)


class _FilterApplication:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | list[str]]] = []

    def get_session_list_filter_schema(self) -> dict[str, Any]:
        return {
            "filters": [
                {
                    "id": "status",
                    "type": "select",
                    "multiple": True,
                },
                {
                    "id": "modified_after",
                    "type": "datetime",
                    "multiple": False,
                },
            ]
        }

    def coerce_session_list_filter_input(
        self,
        filter_id: str,
        raw_value: str | list[str],
    ) -> object:
        self.calls.append((filter_id, raw_value))
        return raw_value


def test_filter_assignments_parse_multi_select_csv_and_scalar_values() -> None:
    application = _FilterApplication()

    values = coerce_session_filter_assignments(
        application,
        [
            'status=todo,"needs, review"',
            "modified_after=2026-09-01T00:00:00Z",
        ],
    )

    assert values == {
        "status": ["todo", "needs, review"],
        "modified_after": "2026-09-01T00:00:00Z",
    }
    assert application.calls == list(values.items())


@pytest.mark.parametrize(
    ("assignments", "expected"),
    [
        (["missing=value"], "unknown session filter"),
        (["status=todo", "status=done"], "supplied more than once"),
        (
            ["x" * (MAX_SESSION_FILTER_ASSIGNMENT_LENGTH + 1)],
            "no longer than",
        ),
        (
            ["status=todo"] * (MAX_SESSION_FILTER_ASSIGNMENTS + 1),
            "at most",
        ),
    ],
)
def test_filter_assignments_reject_invalid_or_unbounded_input(
    assignments: list[str],
    expected: str,
) -> None:
    with pytest.raises(ValueError, match=expected):
        coerce_session_filter_assignments(
            _FilterApplication(),
            assignments,
        )
