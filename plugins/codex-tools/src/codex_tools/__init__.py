"""Codex tools package.

Provides tools matching Codex CLI schemas:
- ShellArrayTool: Array-based shell command (for non-Codex-variant models) - tool name: "shell"
- ShellCommandTool: String-based shell command (for Codex-variant models) - tool name: "shell_command"
- ShellTool: Legacy shell tool (tool name: "shell_legacy", disabled by default)
- ApplyPatchTool: Apply unified diff patches

Features:
- CodexVariantFeature: Emits "codex-variant" tag for models ending with "-codex"

Shell tool selection is controlled by:
- shell_tool_mode config: "auto" (default) | "shell" | "shell_command"
- codex-variant tag: Added by CodexVariantFeature for Codex models
- enabled_plugins config: To enable the legacy tool
"""

from .base_shell_tool import BaseCodexShellTool, DEFAULT_MAX_OUTPUT_TOKENS
from .shell_command_tool import ShellCommandTool
from .shell_array_tool import ShellArrayTool
from .shell_tool import ShellTool
from .apply_patch_tool import ApplyPatchTool
from .codex_variant_feature import CodexVariantFeature

__all__ = [
    "BaseCodexShellTool",
    "DEFAULT_MAX_OUTPUT_TOKENS",
    "ShellCommandTool",
    "ShellArrayTool",
    "ShellTool",
    "ApplyPatchTool",
    "CodexVariantFeature",
]