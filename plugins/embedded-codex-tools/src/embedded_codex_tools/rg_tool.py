from __future__ import annotations

import shlex
import time
from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import resolve_workspace_root, search_workspace_text

from .command_result import CommandResultMixin, command_error, command_result


RG_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "rg",
        "description": (
            "Search workspace text recursively with ripgrep-like output. Equivalent "
            "to `rg -n --no-heading --color=never <pattern> <path>`, with safe "
            "options for fixed strings, case, hidden files, globs, context, and limits."
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression or fixed search text",
                },
                "path": {
                    "type": "string",
                    "description": "Workspace-relative file or directory; defaults to .",
                },
                "fixed_strings": {
                    "type": "boolean",
                    "description": "Treat pattern literally, equivalent to `rg -F`",
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Use case-sensitive matching; defaults true",
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files, equivalent to `rg --hidden`",
                },
                "glob": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File globs, equivalent to repeated `rg -g`",
                },
                "context_lines": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 20,
                    "description": "Context before and after matches, equivalent to -C",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Requested result cap; app limits remain authoritative",
                },
            },
            "required": ["pattern"],
        },
    },
}


def _render_matches(result: Any) -> str:
    lines: list[str] = []
    for match in result.matches:
        for number, text in match.before:
            lines.append(f"{match.path}-{number}-{text}")
        lines.append(f"{match.path}:{match.line_number}:{match.line}")
        for number, text in match.after:
            lines.append(f"{match.path}-{number}-{text}")
    return "\n".join(lines)


class CodexLikeRgTool(CommandResultMixin, ToolPlugin):
    name = "embedded_codex_rg"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [RG_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "rg"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        started = time.monotonic()
        if tool_name != "rg" or not isinstance(payload, dict):
            return command_error("rg", "rg: input must be an object", started=started)
        pattern = payload.get("pattern")
        path = payload.get("path")
        path = path if isinstance(path, str) and path else "."
        command = f"rg -n --no-heading --color=never {shlex.quote(str(pattern))} {shlex.quote(path)}"
        if not isinstance(pattern, str) or not pattern:
            return command_error(
                command,
                "rg: pattern must be a non-empty string",
                started=started,
            )
        globs = payload.get("glob")
        globs = (
            [item for item in globs if isinstance(item, str) and item]
            if isinstance(globs, list)
            else None
        )
        context = payload.get("context_lines")
        context = context if isinstance(context, int) and context >= 0 else 0
        requested_limit = payload.get("max_results")
        requested_limit = (
            requested_limit
            if isinstance(requested_limit, int) and requested_limit > 0
            else 500
        )
        try:
            result = search_workspace_text(
                state["workspace_root"],
                pattern,
                start_path=path,
                fixed_strings=bool(payload.get("fixed_strings", False)),
                case_sensitive=bool(payload.get("case_sensitive", True)),
                include_hidden=bool(payload.get("include_hidden", False)),
                path_globs=globs,
                context_before=context,
                context_after=context,
                max_results=requested_limit,
            )
            output = _render_matches(result)
            return command_result(
                command,
                output,
                exit_code=0 if result.matches else 1,
                started=started,
                truncated=result.truncated,
            )
        except (OSError, UnicodeError, ValueError) as error:
            return command_error(command, f"rg: {error}", started=started)