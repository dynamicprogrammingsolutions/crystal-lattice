"""Feature plugin exposing ``shell_tool_mode`` as a session-settable setting."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


SHELL_TOOL_MODE_OPTIONS = [
    {"value": "auto", "label": "Auto (unified exec)"},
    {"value": "exec_command", "label": "exec_command (unified exec)"},
    {"value": "shell_command", "label": "shell_command (legacy string)"},
    {"value": "shell", "label": "shell (legacy array)"},
]

SHELL_TOOL_MODE_LABEL = "Shell tool"

SHELL_TOOL_MODE_DESCRIPTION = (
    "Shell tool used by this agent/session: unified exec "
    "(exec_command + write_stdin) by default, or the legacy "
    "shell_command / shell tools."
)

SHELL_TOOL_MODE_DEFAULT = "auto"


class ShellToolSettingsFeature(FeaturePlugin):
    """Expose ``shell_tool_mode`` as a session-settable setting.

    Purely a settings surface: the codex-tools shell tools consume the key
    from the merged agent/session config. Registering this plugin makes the
    setting visible in the session settings (terminal ``/set`` and the
    settings UI rendered from the UI schema); setting it for a session
    stores a session override that takes effect on the next request, and
    resetting it returns the session to the agent default.
    """

    name: str = "shell_tool_settings"
    version: str = "1.0.0"
    default_enabled: bool = True

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "select",
                "key": "shell_tool_mode",
                "label": SHELL_TOOL_MODE_LABEL,
                "description": SHELL_TOOL_MODE_DESCRIPTION,
                "default": SHELL_TOOL_MODE_DEFAULT,
                "options": [dict(option) for option in SHELL_TOOL_MODE_OPTIONS],
            }
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        return []

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state


__all__ = [
    "SHELL_TOOL_MODE_DEFAULT",
    "SHELL_TOOL_MODE_DESCRIPTION",
    "SHELL_TOOL_MODE_LABEL",
    "SHELL_TOOL_MODE_OPTIONS",
    "ShellToolSettingsFeature",
]
