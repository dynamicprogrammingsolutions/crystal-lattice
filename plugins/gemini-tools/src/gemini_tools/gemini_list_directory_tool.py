from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_gemini_list_result,
    format_tool_result_text,
    list_directory_entries,
    resolve_path,
    validate_path_within_directories,
)


class GeminiListDirectoryTool(ToolPlugin):
    name = "gemini_list_directory_tool"
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
                    "name": "list_directory",
                    "description": "Lists the names of files and subdirectories directly within a specified directory path. Can optionally ignore entries matching provided glob patterns.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "The path to the directory to list"},
                            "ignore": {
                                "type": "array",
                                "description": "List of glob patterns to ignore",
                                "items": {"type": "string"},
                            },
                            "file_filtering_options": {
                                "type": "object",
                                "description": "Optional: Whether to respect ignore patterns from .gitignore or .geminiignore",
                                "properties": {
                                    "respect_git_ignore": {
                                        "type": "boolean",
                                        "description": "Optional: Whether to respect .gitignore patterns when listing files. Only available in git repositories. Defaults to true.",
                                    },
                                    "respect_gemini_ignore": {
                                        "type": "boolean",
                                        "description": "Optional: Whether to respect .geminiignore patterns when listing files. Defaults to true.",
                                    },
                                },
                            },
                        },
                        "required": ["dir_path"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "list_directory":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        dir_path = arguments.get("dir_path")
        if not isinstance(dir_path, str) or not dir_path.strip():
            return {"success": False, "error": "The 'dir_path' parameter must be non-empty."}

        working_directory = state["working_directory"]
        resolved = resolve_path(dir_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            return {"success": False, "error": f"Path not in workspace: {resolved}"}

        filtering_options = arguments.get("file_filtering_options") if isinstance(arguments.get("file_filtering_options"), dict) else {}
        ignore = arguments.get("ignore") if isinstance(arguments.get("ignore"), list) else None
        outcome = list_directory_entries(
            resolved,
            display_root=working_directory,
            ignore_patterns=[item for item in ignore if isinstance(item, str)] if ignore else None,
            vendor_ignore_filename=".geminiignore",
            respect_git_ignore=bool(filtering_options.get("respect_git_ignore", True)),
            respect_vendor_ignore=bool(filtering_options.get("respect_gemini_ignore", True)),
        )
        if not outcome["ok"]:
            return {"success": False, "error": str(outcome["error"])}
        return format_gemini_list_result(outcome)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
