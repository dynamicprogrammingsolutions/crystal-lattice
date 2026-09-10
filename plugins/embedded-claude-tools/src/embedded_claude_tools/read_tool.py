from __future__ import annotations

from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import (
    DEFAULT_MAX_READ_LINES,
    read_text_file,
    resolve_workspace_path,
    resolve_workspace_root,
)

from .activity import record_read_path


READ_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "Read",
        "description": (
            "Read a UTF-8 text file inside the configured workspace. "
            "Use workspace-relative paths only."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Workspace-relative path to read",
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Optional zero-based starting line",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": DEFAULT_MAX_READ_LINES,
                    "description": "Optional maximum number of lines",
                },
            },
            "required": ["file_path"],
        },
    },
}


class ClaudeLikeReadTool(ToolPlugin):
    name = "embedded_claude_read"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [READ_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "Read"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "Read" or not isinstance(payload, dict):
            return {"success": False, "error": "Read input must be an object"}
        offset = payload.get("offset")
        limit = payload.get("limit")
        safe_offset = offset if isinstance(offset, int) and offset >= 0 else 0
        safe_limit = (
            limit
            if isinstance(limit, int) and 0 < limit <= DEFAULT_MAX_READ_LINES
            else DEFAULT_MAX_READ_LINES
        )
        try:
            resolved = resolve_workspace_path(
                state["workspace_root"],
                payload.get("file_path"),
            )
            result = read_text_file(
                state["workspace_root"],
                payload.get("file_path"),
                offset=safe_offset,
                limit=safe_limit,
            )
            record_read_path(
                resolved.path,
                context=context,
                workspace_root=state["workspace_root"],
            )
            return {
                "success": True,
                "result": result.text,
                "path": result.path,
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

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> str:
        _ = tool_name, state
        return (
            f"Read {payload.get('file_path')}"
            if isinstance(payload, dict)
            else "Read workspace file"
        )

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = state
        path = str(result.get("path") or "file")
        return {
            "type": "text",
            "content": text,
            "single_line": f"Read: {path}",
        }