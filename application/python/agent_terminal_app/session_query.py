"""Syntax parsing for the terminal ``/session`` command."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import shlex
from typing import Dict, List


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


__all__ = [
    "ParsedSessionQuery",
    "parse_multi_select_csv",
    "parse_session_query",
]
