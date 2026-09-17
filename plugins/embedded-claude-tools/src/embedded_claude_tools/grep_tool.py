from __future__ import annotations

from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import resolve_workspace_root, search_workspace_text


GREP_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "Grep",
        "description": (
            "Search workspace text files with a regular expression. Results can "
            "contain matching lines, matching file paths, or per-file counts."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression to search for",
                },
                "path": {
                    "type": "string",
                    "description": "Optional workspace-relative file or directory",
                },
                "glob": {
                    "type": "string",
                    "description": "Optional file glob such as `**/*.py`",
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                    "description": "Result shape; defaults to files_with_matches",
                },
                "-i": {
                    "type": "boolean",
                    "description": "Case-insensitive matching",
                },
                "-n": {
                    "type": "boolean",
                    "description": "Show line numbers in content mode; defaults true",
                },
                "context": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 20,
                    "description": "Lines before and after content matches",
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Skip initial results",
                },
                "head_limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum returned results; defaults to 250",
                },
            },
            "required": ["pattern"],
        },
    },
}


def _content_lines(result: Any, *, show_line_numbers: bool) -> list[str]:
    lines: list[str] = []
    for match in result.matches:
        for line_number, line in match.before:
            prefix = f"{match.path}-{line_number}-" if show_line_numbers else ""
            lines.append(f"{prefix}{line}")
        prefix = f"{match.path}:{match.line_number}:" if show_line_numbers else ""
        lines.append(f"{prefix}{match.line}")
        for line_number, line in match.after:
            prefix = f"{match.path}-{line_number}-" if show_line_numbers else ""
            lines.append(f"{prefix}{line}")
    return lines


class ClaudeLikeGrepTool(ToolPlugin):
    name = "embedded_claude_grep"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [GREP_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "Grep"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "Grep" or not isinstance(payload, dict):
            return {"success": False, "error": "Grep input must be an object"}
        pattern = payload.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            return {"success": False, "error": "pattern must be a non-empty string"}

        mode = payload.get("output_mode")
        mode = (
            mode
            if mode in {"content", "files_with_matches", "count"}
            else "files_with_matches"
        )
        offset = payload.get("offset")
        offset = offset if isinstance(offset, int) and offset >= 0 else 0
        head_limit = payload.get("head_limit")
        head_limit = (
            head_limit
            if isinstance(head_limit, int) and 0 < head_limit <= 500
            else 250
        )
        context = payload.get("context")
        context = context if isinstance(context, int) and context >= 0 else 0
        start_path = payload.get("path")
        start_path = start_path if isinstance(start_path, str) and start_path else "."
        glob = payload.get("glob")
        globs = [glob] if isinstance(glob, str) and glob else None
        try:
            result = search_workspace_text(
                state["workspace_root"],
                pattern,
                start_path=start_path,
                case_sensitive=not bool(payload.get("-i", False)),
                path_globs=globs,
                context_before=context if mode == "content" else 0,
                context_after=context if mode == "content" else 0,
                max_results=min(500, offset + head_limit),
            )
            if mode == "files_with_matches":
                items = list(result.files)
            elif mode == "count":
                items = [f"{path}:{count}" for path, count in result.counts]
            else:
                items = _content_lines(
                    result,
                    show_line_numbers=bool(payload.get("-n", True)),
                )
            visible = items[offset : offset + head_limit]
            text = "\n".join(visible)
            return {
                "success": True,
                "result": text,
                "count": len(visible),
                "truncated": result.truncated or len(items) > offset + head_limit,
            }
        except (OSError, UnicodeError, ValueError) as error:
            return {"success": False, "error": str(error)}

    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        _ = state
        if result.get("success"):
            return str(result.get("result") or "")
        return f"Error: {result.get('error')}"

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = state
        return {
            "type": "text",
            "content": text,
            "single_line": f"Grep: {result.get('count', 0)} results",
        }