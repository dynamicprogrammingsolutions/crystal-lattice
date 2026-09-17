from __future__ import annotations

import shlex
import time
from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import read_text_file, resolve_workspace_root

from .command_result import CommandResultMixin, command_error, command_result


SED_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "sed",
        "description": (
            "Read a bounded line range from one workspace text file. Equivalent "
            "to `sed -n '<from_line>,<to_line>p' <path>`. Set "
            "show_line_numbers for output equivalent to numbering the input first."
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Workspace-relative input file path",
                },
                "from_line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "First 1-based line to print",
                },
                "to_line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Last 1-based line to print, inclusive",
                },
                "show_line_numbers": {
                    "type": "boolean",
                    "description": "Prefix output with 1-based line numbers",
                },
            },
            "required": ["path", "from_line", "to_line"],
        },
    },
}


class CodexLikeSedTool(CommandResultMixin, ToolPlugin):
    name = "embedded_codex_sed"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [SED_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "sed"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        started = time.monotonic()
        if tool_name != "sed" or not isinstance(payload, dict):
            return command_error("sed", "sed: input must be an object", started=started)
        path = payload.get("path")
        from_line = payload.get("from_line")
        to_line = payload.get("to_line")
        command = (
            f"sed -n '{from_line},{to_line}p' "
            f"{shlex.quote(path) if isinstance(path, str) else '<path>'}"
        )
        if (
            not isinstance(path, str)
            or not path
            or not isinstance(from_line, int)
            or not isinstance(to_line, int)
            or from_line < 1
            or to_line < from_line
        ):
            return command_error(
                command,
                "sed: path and a valid 1-based line range are required",
                started=started,
            )
        effective_to = min(to_line, from_line + 1999)
        try:
            result = read_text_file(
                state["workspace_root"],
                path,
                offset=from_line - 1,
                limit=effective_to - from_line + 1,
                number_lines=bool(payload.get("show_line_numbers", False)),
            )
            return command_result(
                (
                    f"sed -n '{from_line},{effective_to}p' "
                    f"{shlex.quote(path)}"
                ),
                result.text,
                started=started,
                truncated=effective_to != to_line,
            )
        except (OSError, UnicodeError, ValueError) as error:
            return command_error(command, f"sed: {error}", started=started)