from __future__ import annotations

from functools import lru_cache
import textwrap
from typing import Callable, Sequence

from tree_sitter import Language, Node, Parser, Query, QueryCursor
import tree_sitter_cpp
import tree_sitter_go
import tree_sitter_java
import tree_sitter_rust
import tree_sitter_typescript

from .base import CodeComparisonResult
from .queries import COMMENT_QUERIES, FUNCTION_QUERY


LanguageFactory = Callable[[], object]


def _typescript_language() -> object:
    return tree_sitter_typescript.language_typescript()


LANGUAGE_FACTORIES: dict[str, LanguageFactory] = {
    "cpp": tree_sitter_cpp.language,
    "java": tree_sitter_java.language,
    "go": tree_sitter_go.language,
    "rust": tree_sitter_rust.language,
    "typescript": _typescript_language,
}


def normalize_text(text: str) -> str:
    normalized = textwrap.dedent(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


@lru_cache(maxsize=None)
def language_for(language_name: str) -> Language:
    factory = LANGUAGE_FACTORIES[language_name]
    return Language(factory())


@lru_cache(maxsize=None)
def parser_for(language_name: str) -> Parser:
    return Parser(language_for(language_name))


@lru_cache(maxsize=None)
def function_query_for(language_name: str) -> Query:
    return Query(language_for(language_name), FUNCTION_QUERY[language_name])


@lru_cache(maxsize=None)
def comment_queries_for(language_name: str) -> tuple[Query, ...]:
    return tuple(Query(language_for(language_name), query) for query in COMMENT_QUERIES[language_name])


def _capture_nodes(query: Query, root_node: Node) -> list[Node]:
    captures = QueryCursor(query).captures(root_node)
    nodes: list[Node] = []
    for capture_nodes in captures.values():
        nodes.extend(capture_nodes)
    return nodes


def _select_primary_candidate(nodes: Sequence[Node], *, wrapper_parent_types: Sequence[str] = ()) -> Node | None:
    if not nodes:
        return None
    candidate = max(nodes, key=lambda node: (node.end_byte - node.start_byte, -node.start_byte))
    while candidate.parent is not None and candidate.parent.type in wrapper_parent_types:
        candidate = candidate.parent
    return candidate


def _remove_comment_nodes(source_bytes: bytes, comment_nodes: Sequence[Node]) -> bytes:
    output = source_bytes
    for node in sorted(comment_nodes, key=lambda item: item.start_byte, reverse=True):
        output = output[: node.start_byte] + output[node.end_byte :]
    return output


def extract_primary_function_source(
    language_name: str,
    text: str,
    *,
    wrapper_parent_types: Sequence[str] = (),
) -> tuple[str | None, bool, tuple[str, ...]]:
    normalized = normalize_text(text)
    if not normalized:
        return None, False, ("empty_input",)

    parser = parser_for(language_name)
    source_bytes = normalized.encode("utf-8")
    tree = parser.parse(source_bytes)
    function_nodes = _capture_nodes(function_query_for(language_name), tree.root_node)
    candidate = _select_primary_candidate(function_nodes, wrapper_parent_types=wrapper_parent_types)
    if candidate is None:
        return normalized, False, ("function_query_no_match",)

    snippet_bytes = source_bytes[candidate.start_byte : candidate.end_byte]
    snippet_tree = parser.parse(snippet_bytes)
    comment_nodes: list[Node] = []
    for query in comment_queries_for(language_name):
        comment_nodes.extend(_capture_nodes(query, snippet_tree.root_node))
    stripped_bytes = _remove_comment_nodes(snippet_bytes, comment_nodes)
    return normalize_text(stripped_bytes.decode("utf-8")), True, ()


def compare_tree_sitter_language(
    language_name: str,
    left: str,
    right: str,
    *,
    method: str,
    wrapper_parent_types: Sequence[str] = (),
) -> CodeComparisonResult:
    left_normalized, left_parse_ok, left_notes = extract_primary_function_source(
        language_name,
        left,
        wrapper_parent_types=wrapper_parent_types,
    )
    right_normalized, right_parse_ok, right_notes = extract_primary_function_source(
        language_name,
        right,
        wrapper_parent_types=wrapper_parent_types,
    )
    notes = tuple(left_notes + right_notes)
    matched = (left_normalized or "") == (right_normalized or "")
    actual_method = method
    if not left_parse_ok or not right_parse_ok:
        actual_method = f"{method}:fallback_normalized_text"
        matched = normalize_text(left) == normalize_text(right)
    return CodeComparisonResult(
        matched=matched,
        method=actual_method,
        left_parse_ok=left_parse_ok,
        right_parse_ok=right_parse_ok,
        notes=notes,
        normalized_left=left_normalized,
        normalized_right=right_normalized,
    )