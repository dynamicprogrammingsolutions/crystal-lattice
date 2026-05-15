from __future__ import annotations

from .base import CodeComparisonResult
from .tree_sitter_utils import compare_tree_sitter_language


def compare_go(left: str, right: str) -> CodeComparisonResult:
    return compare_tree_sitter_language("go", left, right, method="go_tree_sitter")