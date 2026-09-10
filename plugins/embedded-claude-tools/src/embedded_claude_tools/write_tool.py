from __future__ import annotations

from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import resolve_workspace_root, write_text_file


WRITE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "Write",
        "description": (
            "Create or replace a UTF-8 text file inside the configured workspace. "
            "Use workspace-relative paths only."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Workspace-relative path to write",
                },
                "content": {
                    "type": "string",
                    "description": "Complete text content",
                },
            },
            "required": ["file_path", "content"],
        },
    },
}


class ClaudeLikeWriteTool(ToolPlugin):
    name = "embedded_claude_write"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [WRITE_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "Write"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "Write" or not isinstance(payload, dict):
            return {"success": False, "error": "Write input must be an object"}
        content = payload.get("content")
        if not isinstance(content, str):
            return {"success": False, "error": "content must be a string"}
        try:
            result = write_text_file(
                state["workspace_root"],
                payload.get("file_path"),
                content,
            )
            return {
                "success": True,
                "result": f"Wrote {result.bytes_written} bytes to {result.path}",
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
            f"Write {payload.get('file_path')}"
            if isinstance(payload, dict)
            else "Write workspace file"
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
            "single_line": f"Write: {path}",
        }