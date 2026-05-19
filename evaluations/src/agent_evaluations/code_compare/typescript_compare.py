from __future__ import annotations

from .base import CodeComparisonResult
from .tree_sitter_utils import compare_tree_sitter_language


def _strip_stray_comment_closer(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and lines[0].strip() in {"*/", "*"}:
        lines.pop(0)
    return "\n".join(lines)


def compare_typescript(left: str, right: str) -> CodeComparisonResult:
    return compare_tree_sitter_language(
        "typescript",
        _strip_stray_comment_closer(left),
        _strip_stray_comment_closer(right),
        method="typescript_tree_sitter",
    )