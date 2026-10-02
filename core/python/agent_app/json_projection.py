"""Bounded RFC 9535 include/exclude projection for JSON-like documents."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Mapping, Sequence

from jsonpath import CompoundJSONPath, JSONPath, JSONPathEnvironment
from jsonpath.exceptions import JSONPathError


MAX_PROJECTION_SELECTORS = 64
MAX_PROJECTION_SELECTOR_LENGTH = 4096
MAX_PROJECTION_MATCHES = 100_000
MAX_PROJECTED_JSON_CHARACTERS = 20_000_000

_OMIT = object()
_PathSegment = str | int
_RFC9535_ENVIRONMENT = JSONPathEnvironment(strict=True)


class JsonProjectionError(ValueError):
    """Raised when a JSONPath projection request is invalid or too large."""


@dataclass
class _PathNode:
    selected: bool = False
    children: dict[_PathSegment, "_PathNode"] = field(default_factory=dict)

    def add(self, location: Sequence[_PathSegment]) -> None:
        node = self
        for segment in location:
            node = node.children.setdefault(segment, _PathNode())
        node.selected = True
        node.children.clear()


def _selector_values(
    name: str,
    selectors: Sequence[str] | None,
) -> tuple[str, ...]:
    if selectors is None:
        return ()
    if isinstance(selectors, (str, bytes)) or not isinstance(selectors, Sequence):
        raise JsonProjectionError(f"{name} must be a sequence of JSONPath strings")
    values = tuple(selectors)
    for selector in values:
        if not isinstance(selector, str) or not selector:
            raise JsonProjectionError(f"{name} must contain non-empty JSONPath strings")
        if len(selector) > MAX_PROJECTION_SELECTOR_LENGTH:
            raise JsonProjectionError(
                f"{name} selector exceeds {MAX_PROJECTION_SELECTOR_LENGTH} characters"
            )
        if not selector.startswith("$"):
            raise JsonProjectionError(
                f"{name} selector must start with '$': {selector!r}"
            )
    return values


def _compiled_selectors(
    *,
    name: str,
    selectors: Sequence[str],
) -> tuple[tuple[str, JSONPath | CompoundJSONPath], ...]:
    compiled: list[tuple[str, JSONPath | CompoundJSONPath]] = []
    for selector in selectors:
        try:
            compiled.append((selector, _RFC9535_ENVIRONMENT.compile(selector)))
        except JSONPathError as exc:
            raise JsonProjectionError(
                f"invalid {name} JSONPath {selector!r}: {exc}"
            ) from exc
    return tuple(compiled)


def _selected_paths(
    document: Any,
    *,
    name: str,
    selectors: Sequence[tuple[str, JSONPath | CompoundJSONPath]],
    remaining_matches: list[int],
) -> _PathNode:
    root = _PathNode()
    for selector, query in selectors:
        try:
            for node in query.finditer(document):
                remaining_matches[0] -= 1
                if remaining_matches[0] < 0:
                    raise JsonProjectionError(
                        f"projection exceeds {MAX_PROJECTION_MATCHES} matched nodes"
                    )
                root.add(node.parts)
        except JSONPathError as exc:
            raise JsonProjectionError(
                f"failed {name} JSONPath {selector!r}: {exc}"
            ) from exc
    return root


def _render(
    source: Any,
    *,
    include: _PathNode | None,
    include_all: bool,
    exclude: _PathNode | None,
) -> Any:
    if exclude is not None and exclude.selected:
        return _OMIT

    selected = include_all or (include is not None and include.selected)
    if not selected and include is None:
        return _OMIT

    child_include_all = selected
    if isinstance(source, Mapping):
        result: dict[str, Any] = {}
        for key, value in source.items():
            include_child = include.children.get(key) if include is not None else None
            if not child_include_all and include_child is None:
                continue
            exclude_child = exclude.children.get(key) if exclude is not None else None
            projected = _render(
                value,
                include=include_child,
                include_all=child_include_all,
                exclude=exclude_child,
            )
            if projected is not _OMIT:
                result[key] = projected
        return result

    if isinstance(source, list):
        result_list: list[Any] = []
        for index, value in enumerate(source):
            include_child = include.children.get(index) if include is not None else None
            if not child_include_all and include_child is None:
                continue
            exclude_child = exclude.children.get(index) if exclude is not None else None
            projected = _render(
                value,
                include=include_child,
                include_all=child_include_all,
                exclude=exclude_child,
            )
            if projected is not _OMIT:
                result_list.append(projected)
        return result_list

    return source if selected else _OMIT


def project_json_document(
    document: Any,
    *,
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> Any:
    """Project one JSON-like document without mutating the source.

    With no selectors, the original document is returned unchanged. Otherwise,
    all selectors are evaluated against the original document. Include matches
    are unioned with their structural ancestors and exclude matches then remove
    nodes or complete array entries.
    """

    include_values = _selector_values("include", include)
    exclude_values = _selector_values("exclude", exclude)
    selector_count = len(include_values) + len(exclude_values)
    if selector_count == 0:
        return document
    if selector_count > MAX_PROJECTION_SELECTORS:
        raise JsonProjectionError(
            f"projection accepts at most {MAX_PROJECTION_SELECTORS} selectors"
        )

    compiled_include = _compiled_selectors(
        name="include",
        selectors=include_values,
    )
    compiled_exclude = _compiled_selectors(
        name="exclude",
        selectors=exclude_values,
    )
    remaining_matches = [MAX_PROJECTION_MATCHES]
    include_root = (
        _selected_paths(
            document,
            name="include",
            selectors=compiled_include,
            remaining_matches=remaining_matches,
        )
        if compiled_include
        else None
    )
    exclude_root = (
        _selected_paths(
            document,
            name="exclude",
            selectors=compiled_exclude,
            remaining_matches=remaining_matches,
        )
        if compiled_exclude
        else None
    )
    result = _render(
        document,
        include=include_root,
        include_all=include_root is None,
        exclude=exclude_root,
    )
    projected = None if result is _OMIT else result
    rendered_size = len(
        json.dumps(
            projected,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    if rendered_size > MAX_PROJECTED_JSON_CHARACTERS:
        raise JsonProjectionError(
            "projected JSON exceeds " f"{MAX_PROJECTED_JSON_CHARACTERS} characters"
        )
    return projected


__all__ = [
    "JsonProjectionError",
    "MAX_PROJECTED_JSON_CHARACTERS",
    "MAX_PROJECTION_MATCHES",
    "MAX_PROJECTION_SELECTOR_LENGTH",
    "MAX_PROJECTION_SELECTORS",
    "project_json_document",
]
