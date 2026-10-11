"""Shell tool settings plugin package.

Exposes ``shell_tool_mode`` as a session-settable setting through a
minimal feature plugin. See ``shell_tool_settings_feature.py``.
"""

from .shell_tool_settings_feature import (
    SHELL_TOOL_MODE_DEFAULT,
    SHELL_TOOL_MODE_DESCRIPTION,
    SHELL_TOOL_MODE_LABEL,
    SHELL_TOOL_MODE_OPTIONS,
    ShellToolSettingsFeature,
)

__all__ = [
    "SHELL_TOOL_MODE_DEFAULT",
    "SHELL_TOOL_MODE_DESCRIPTION",
    "SHELL_TOOL_MODE_LABEL",
    "SHELL_TOOL_MODE_OPTIONS",
    "ShellToolSettingsFeature",
]
