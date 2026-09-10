from __future__ import annotations

from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import (
    edit_text_file,
    resolve_workspace_path,
    resolve_workspace_root,
)

from .activity import has_read_path, record_read_path


EDIT_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "Edit",
        "description": (
            "Perform an exact string replacement in a workspace text file. "
            "Read the file before editing it. By default old_string must be unique; "
            "set replace_all to replace every occurrence."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Workspace-relative file path to edit",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement text",
                },
                "replace_all": {
                    "type": "boolean",
                    "default": False,
                    "description": "Replace all occurrences instead of requiring one",
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        },
    },
}


class ClaudeLikeEditTool(ToolPlugin):
    name = "embedded_claude_edit"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [EDIT_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "Edit"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "Edit" or not isinstance(payload, dict):
            return {"success": False, "error": "Edit input must be an object"}
        try:
            resolved = resolve_workspace_path(
                state["workspace_root"],
                payload.get("file_path"),
            )
            if not has_read_path(
                resolved.path,
                context=context,
                workspace_root=state["workspace_root"],
            ):
                raise ValueError(
                    "File has not been read yet. Read it first before editing it."
                )
            result = edit_text_file(
                state["workspace_root"],
                payload.get("file_path"),
                payload.get("old_string"),
                payload.get("new_string"),
                replace_all=bool(payload.get("replace_all", False)),
            )
            record_read_path(
                resolved.path,
                context=context,
                workspace_root=state["workspace_root"],
            )
            return {
                "success": True,
                "result": (
                    f"Updated {result.path} with {result.replacements} replacement"
                    f"{'' if result.replacements == 1 else 's'}"
                ),
                "path": result.path,
                "replacements": result.replacements,
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
            f"Edit {payload.get('file_path')}"
            if isinstance(payload, dict)
            else "Edit workspace file"
        )

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
            "single_line": f"Edit: {result.get('path') or 'file'}",
        }