"""Codex tools package.

Provides tools matching Codex CLI schemas:
- ShellArrayTool: Array-based shell command (for gpt-5 / gpt-5-mini style models) - tool name: "shell"
- ShellCommandTool: String-based shell command (for shell-command-family models) - tool name: "shell_command"
- ShellTool: Legacy shell tool (tool name: "shell_legacy", disabled by default)
- ApplyPatchTool: Apply unified diff patches
- ViewImageTool: Load local images for model-visible vision inputs

Features:
- CodexVariantFeature: Emits "codex-variant" tag for shell-command-family models

Shell tool selection is controlled by:
- shell_tool_mode config: "auto" (default) | "shell" | "shell_command"
- codex-variant tag: Added by CodexVariantFeature for shell-command-family models
- enabled_plugins config: To enable the legacy tool
"""

from .base_shell_tool import BaseCodexShellTool, DEFAULT_MAX_OUTPUT_TOKENS
from .shell_command_tool import ShellCommandTool
from .shell_tool import ShellArrayTool
from .shell_tool_legacy import ShellTool
from .apply_patch_tool import ApplyPatchTool
from .mcp_tool import CodexMCPTool
from .view_image_tool import ViewImageTool
from .codex_skills_feature import CodexSkillsFeature
from .codex_variant_feature import CodexVariantFeature

__all__ = [
    "BaseCodexShellTool",
    "DEFAULT_MAX_OUTPUT_TOKENS",
    "ShellCommandTool",
    "ShellArrayTool",
    "ShellTool",
    "ApplyPatchTool",
    "CodexMCPTool",
    "ViewImageTool",
    "CodexSkillsFeature",
    "CodexVariantFeature",
]