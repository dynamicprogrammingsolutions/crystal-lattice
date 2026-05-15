from __future__ import annotations

import ast
import textwrap

from .base import CodeComparisonResult
from .tree_sitter_utils import normalize_text


def _strip_docstrings(node: ast.AST) -> ast.AST:
    for child in ast.walk(node):
        body = getattr(child, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if not isinstance(first, ast.Expr):
            continue
        value = getattr(first, "value", None)
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            body.pop(0)
    return node


def _python_semantic_signature(text: str) -> str | None:
    normalized = textwrap.dedent(text).strip()
    if not normalized:
        return None
    try:
        tree = ast.parse(normalized)
    except SyntaxError:
        return None
    stripped = _strip_docstrings(tree)
    return ast.dump(stripped, annotate_fields=True, include_attributes=False)


def compare_python(left: str, right: str) -> CodeComparisonResult:
    left_sig = _python_semantic_signature(left)
    right_sig = _python_semantic_signature(right)
    if left_sig is not None and right_sig is not None:
        return CodeComparisonResult(
            matched=left_sig == right_sig,
            method="python_ast",
            left_parse_ok=True,
            right_parse_ok=True,
            normalized_left=left_sig,
            normalized_right=right_sig,
        )
    return CodeComparisonResult(
        matched=normalize_text(left) == normalize_text(right),
        method="python_ast:fallback_normalized_text",
        left_parse_ok=left_sig is not None,
        right_parse_ok=right_sig is not None,
        normalized_left=normalize_text(left),
        normalized_right=normalize_text(right),
    )