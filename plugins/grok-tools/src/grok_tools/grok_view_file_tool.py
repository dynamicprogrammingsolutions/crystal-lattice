from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_tool_result_payload,
    format_tool_result_text,
    grok_directory_listing,
    read_gemini_style_file,
    resolve_path,
    validate_path_within_directories,
)


class GrokViewFileTool(ToolPlugin):
    name = "grok_view_file_tool"
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
                    "name": "view_file",
                    "description": "View contents of a file or list directory contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to file or directory to view"},
                            "start_line": {
                                "type": "number",
                                "description": "Starting line number for partial file view (optional)",
                            },
                            "end_line": {
                                "type": "number",
                                "description": "Ending line number for partial file view (optional)",
                            },
                        },
                        "required": ["path"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "view_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        raw_path = arguments.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "The 'path' parameter must be non-empty."}

        start_line = arguments.get("start_line")
        end_line = arguments.get("end_line")
        if start_line is not None and start_line < 1:
            return {"success": False, "error": "start_line must be at least 1"}
        if end_line is not None and end_line < 1:
            return {"success": False, "error": "end_line must be at least 1"}
        if start_line is not None and end_line is not None and start_line > end_line:
            return {"success": False, "error": "start_line cannot be greater than end_line"}

        working_directory = state["working_directory"]
        resolved = resolve_path(raw_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            return {
                "success": False,
                "error": f"Path not in workspace: {resolved}",
            }

        target = Path(resolved)
        if target.is_dir():
            return format_tool_result_payload(grok_directory_listing(resolved, display_root=working_directory))

        outcome = read_gemini_style_file(
            resolved,
            display_root=working_directory,
            start_line=int(start_line) if start_line is not None else None,
            end_line=int(end_line) if end_line is not None else None,
        )
        return format_tool_result_payload(outcome)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}