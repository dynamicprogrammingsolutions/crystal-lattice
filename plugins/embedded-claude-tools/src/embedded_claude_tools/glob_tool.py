from __future__ import annotations

from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import (
    enumerate_workspace_paths,
    resolve_workspace_root,
)


GLOB_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "Glob",
        "description": (
            "Find workspace files by glob pattern. Supports patterns such as "
            "`**/*.md` and returns sorted workspace-relative paths."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern matched relative to the search path",
                },
                "path": {
                    "type": "string",
                    "description": "Optional workspace-relative directory",
                },
            },
            "required": ["pattern"],
        },
    },
}


class ClaudeLikeGlobTool(ToolPlugin):
    name = "embedded_claude_glob"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [GLOB_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "Glob"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "Glob" or not isinstance(payload, dict):
            return {"success": False, "error": "Glob input must be an object"}
        pattern = payload.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            return {"success": False, "error": "pattern must be a non-empty string"}
        start_path = payload.get("path")
        start_path = start_path if isinstance(start_path, str) and start_path else "."
        try:
            result = enumerate_workspace_paths(
                state["workspace_root"],
                start_path=start_path,
                path_globs=[pattern],
                kind="file",
                max_results=100,
            )
            paths = [entry.path for entry in result.paths]
            text = "\n".join(paths) if paths else "No files found"
            if result.truncated:
                text += (
                    "\n(Results are truncated. Use a more specific path or pattern.)"
                )
            return {
                "success": True,
                "result": text,
                "count": len(paths),
                "truncated": result.truncated,
            }
        except (OSError, ValueError) as error:
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
            "single_line": f"Glob: {result.get('count', 0)} files",
        }