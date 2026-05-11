from __future__ import annotations

from .base import CodeComparisonResult
from .tree_sitter_utils import compare_tree_sitter_language


def compare_cpp(left: str, right: str) -> CodeComparisonResult:
    return compare_tree_sitter_language(
        "cpp",
        left,
        right,
        method="cpp_tree_sitter",
        wrapper_parent_types=("template_declaration",),
    )