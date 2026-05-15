from __future__ import annotations

from .base import CodeComparisonResult
from .cpp_compare import compare_cpp
from .go_compare import compare_go
from .java_compare import compare_java
from .python_compare import compare_python
from .rust_compare import compare_rust
from .tree_sitter_utils import normalize_text
from .typescript_compare import compare_typescript


def compare_code(language: str, left: str, right: str) -> CodeComparisonResult:
    normalized_language = language.strip().lower()
    if normalized_language == "python":
        return compare_python(left, right)
    if normalized_language == "cpp":
        return compare_cpp(left, right)
    if normalized_language == "java":
        return compare_java(left, right)
    if normalized_language == "go":
        return compare_go(left, right)
    if normalized_language == "rust":
        return compare_rust(left, right)
    if normalized_language == "typescript":
        return compare_typescript(left, right)
    return CodeComparisonResult(
        matched=normalize_text(left) == normalize_text(right),
        method="normalized_text_fallback",
        left_parse_ok=False,
        right_parse_ok=False,
        normalized_left=normalize_text(left),
        normalized_right=normalize_text(right),
    )