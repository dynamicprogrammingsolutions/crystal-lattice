from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import format_qwen_list_result, format_tool_result_text, list_directory_entries, validate_path_within_directories


class QwenListDirectoryTool(ToolPlugin):
    name = "qwen_list_directory_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("workspace_dirs") or config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        global_temp_dir = str(config.get("global_temp_dir") or tempfile.gettempdir())
        user_skills_dir = str(config.get("user_skills_dir") or Path.home() / ".qwen" / "skills")
        return {
            "display_root": str(Path(working_directory).resolve()),
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
            "global_temp_dir": str(Path(global_temp_dir).resolve()),
            "user_skills_dir": str(Path(user_skills_dir).resolve()),
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
                            "path": {
                                "type": "string",
                                "description": "The absolute path to the directory to list (must be absolute, not relative)",
                            },
                            "ignore": {
                                "type": "array",
                                "description": "List of glob patterns to ignore",
                                "items": {"type": "string"},
                            },
                            "file_filtering_options": {
                                "type": "object",
                                "description": "Optional: Whether to respect ignore patterns from .gitignore or .qwenignore",
                                "properties": {
                                    "respect_git_ignore": {
                                        "type": "boolean",
                                        "description": "Optional: Whether to respect .gitignore patterns when listing files. Only available in git repositories. Defaults to true.",
                                    },
                                    "respect_qwen_ignore": {
                                        "type": "boolean",
                                        "description": "Optional: Whether to respect .qwenignore patterns when listing files. Defaults to true.",
                                    },
                                },
                            },
                        },
                        "required": ["path"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "list_directory":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        raw_path = arguments.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "The 'path' parameter must be non-empty."}
        if not os.path.isabs(raw_path):
            return {"success": False, "error": f"Path must be absolute: {raw_path}"}

        resolved = str(Path(raw_path).resolve())
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"], state["global_temp_dir"], state["user_skills_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            directories = ", ".join(state["workspace_dirs"])
            return {"success": False, "error": f"Path must be within one of the workspace directories: {directories}"}

        filtering_options = arguments.get("file_filtering_options") if isinstance(arguments.get("file_filtering_options"), dict) else {}
        ignore = arguments.get("ignore") if isinstance(arguments.get("ignore"), list) else None
        outcome = list_directory_entries(
            resolved,
            display_root=state["display_root"],
            ignore_patterns=[item for item in ignore if isinstance(item, str)] if ignore else None,
            vendor_ignore_filename=".qwenignore",
            respect_git_ignore=bool(filtering_options.get("respect_git_ignore", True)),
            respect_vendor_ignore=bool(filtering_options.get("respect_qwen_ignore", True)),
        )
        if not outcome["ok"]:
            return {"success": False, "error": str(outcome["error"])}
        return format_qwen_list_result(outcome, vendor_label="qwen")

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
