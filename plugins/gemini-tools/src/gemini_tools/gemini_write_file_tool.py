from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_tool_result_text,
    is_path_ignored,
    resolve_path,
    validate_path_within_directories,
    write_text_file,
)


class GeminiWriteFileTool(ToolPlugin):
    name = "gemini_write_file_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        return {
            "working_directory": working_directory,
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
        }

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Writes the complete content to a file, automatically creating missing parent directories. Overwrites existing files. The user has the ability to modify 'content' before it is saved. Best for new or small files; use 'replace' for targeted edits to large files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file."},
                            "content": {
                                "type": "string",
                                "description": "The complete content to write. Provide the full file; do not use placeholders like '// ... rest of code'.",
                            },
                        },
                        "required": ["file_path", "content"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "write_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        file_path = arguments.get("file_path")
        content = arguments.get("content")
        if not isinstance(file_path, str) or not file_path.strip():
            return {"success": False, "error": "The 'file_path' parameter must be non-empty."}
        if not isinstance(content, str):
            return {"success": False, "error": "The 'content' parameter must be a string."}

        working_directory = state["working_directory"]
        resolved = resolve_path(file_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            return {"success": False, "error": f"Path not in workspace: {resolved}"}
        if is_path_ignored(resolved, root=working_directory, ignore_filename=".geminiignore"):
            return {"success": False, "error": f"File path '{resolved}' is ignored by configured ignore patterns."}

        outcome = write_text_file(resolved, content)
        if not outcome["ok"]:
            return {"success": False, "error": str(outcome["error"])}
        message = (
            f"Successfully created and wrote to new file: {resolved}."
            if outcome["created"]
            else f"Successfully overwrote file: {resolved}."
        )
        return {"success": True, "result": message, "kind": "text", "return_display": message}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}