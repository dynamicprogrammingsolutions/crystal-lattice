"""Syntax parsing for the terminal ``/session`` command."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import shlex
from typing import Any, Dict, List, Sequence


MAX_SESSION_FILTER_ASSIGNMENTS = 64
MAX_SESSION_FILTER_ASSIGNMENT_LENGTH = 4096


@dataclass(frozen=True)
class ParsedSessionQuery:
    search_text: str
    filter_inputs: Dict[str, str]


def parse_session_query(text: str) -> ParsedSessionQuery:
    try:
        tokens = shlex.split(text or "", posix=True)
    except ValueError as exc:
        raise ValueError(f"invalid /session quoting: {exc}") from exc

    filter_inputs: Dict[str, str] = {}
    search_parts: List[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--filter":
            index += 1
            if index >= len(tokens):
                raise ValueError("--filter requires <filter-id>=<value>")
            assignment = tokens[index]
            filter_id, separator, raw_value = assignment.partition("=")
            if not separator or not filter_id:
                raise ValueError("--filter requires <filter-id>=<value>")
            if filter_id in filter_inputs:
                raise ValueError(f"filter {filter_id!r} was supplied more than once")
            filter_inputs[filter_id] = raw_value
        elif token.startswith("--"):
            raise ValueError(f"unknown /session option {token!r}")
        else:
            search_parts.append(token)
        index += 1

    return ParsedSessionQuery(
        search_text=" ".join(search_parts),
        filter_inputs=filter_inputs,
    )


def parse_multi_select_csv(raw_value: str) -> List[str]:
    try:
        values = next(csv.reader([raw_value], strict=True))
    except (csv.Error, StopIteration) as exc:
        raise ValueError(f"invalid comma-separated filter value: {exc}") from exc
    if not values or any(value == "" for value in values):
        raise ValueError(
            "multi-select filter values must be 'any' or a comma-separated list"
        )
    return values


def coerce_session_filter_assignments(
    application: Any,
    assignments: Sequence[str],
) -> Dict[str, object]:
    """Validate ``id=value`` assignments through the active plugin schema."""

    if len(assignments) > MAX_SESSION_FILTER_ASSIGNMENTS:
        raise ValueError(
            "session queries accept at most "
            f"{MAX_SESSION_FILTER_ASSIGNMENTS} filter assignments"
        )
    schema = application.get_session_list_filter_schema()
    declarations = {
        declaration["id"]: declaration
        for declaration in schema.get("filters", [])
        if isinstance(declaration, dict) and isinstance(declaration.get("id"), str)
    }
    values: Dict[str, object] = {}
    for assignment in assignments:
        if (
            not isinstance(assignment, str)
            or len(assignment) > MAX_SESSION_FILTER_ASSIGNMENT_LENGTH
        ):
            raise ValueError(
                "session filter assignments must be strings no longer than "
                f"{MAX_SESSION_FILTER_ASSIGNMENT_LENGTH} characters"
            )
        filter_id, separator, raw_value = assignment.partition("=")
        if not separator or not filter_id:
            raise ValueError("filter requires <filter-id>=<value>")
        if filter_id in values:
            raise ValueError(f"filter {filter_id!r} was supplied more than once")
        declaration = declarations.get(filter_id)
        if declaration is None:
            raise ValueError(f"unknown session filter: {filter_id!r}")
        if declaration.get("type") == "select" and declaration.get("multiple") is True:
            input_value: str | List[str] = parse_multi_select_csv(raw_value)
        else:
            input_value = raw_value
        try:
            values[filter_id] = application.coerce_session_list_filter_input(
                filter_id,
                input_value,
            )
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
    return values


__all__ = [
    "MAX_SESSION_FILTER_ASSIGNMENTS",
    "MAX_SESSION_FILTER_ASSIGNMENT_LENGTH",
    "ParsedSessionQuery",
    "coerce_session_filter_assignments",
    "parse_multi_select_csv",
    "parse_session_query",
]
