"""Maintainer-owned agent-guidance source and compilation."""

from .compiler import (
    CompilationResult,
    bundle_section_path,
    compile_guidance,
    write_compilation,
)

__all__ = [
    "CompilationResult",
    "bundle_section_path",
    "compile_guidance",
    "write_compilation",
]