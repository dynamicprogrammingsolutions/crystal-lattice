from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_gemini_glob_result,
    format_tool_result_text,
    glob_search,
    resolve_path,
    validate_path_within_directories,
)


class GeminiGlobTool(ToolPlugin):
    name = "gemini_glob_tool"
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
                    "name": "glob",
                    "description": "Efficiently finds files matching specific glob patterns (e.g., `src/**/*.ts`, `**/*.md`), returning absolute paths sorted by modification time (newest first). Ideal for quickly locating files based on their name or path structure, especially in large codebases.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "The glob pattern to match against (e.g., '**/*.py', 'docs/*.md').",
                            },
                            "dir_path": {
                                "type": "string",
                                "description": "Optional: The absolute path to the directory to search within. If omitted, searches the root directory.",
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "Optional: Whether the search should be case-sensitive. Defaults to false.",
                            },
                            "respect_git_ignore": {
                                "type": "boolean",
                                "description": "Optional: Whether to respect .gitignore patterns when finding files. Only available in git repositories. Defaults to true.",
                            },
                            "respect_gemini_ignore": {
                                "type": "boolean",
                                "description": "Optional: Whether to respect .geminiignore patterns when finding files. Defaults to true.",
                            },
                        },
                        "required": ["pattern"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "glob":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        pattern = arguments.get("pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            return {"success": False, "error": "The 'pattern' parameter cannot be empty."}

        working_directory = state["working_directory"]
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        dir_path = arguments.get("dir_path")
        if isinstance(dir_path, str) and dir_path.strip():
            resolved = resolve_path(dir_path, working_directory=working_directory, allow_relative=True)
            if not validate_path_within_directories(resolved, allowed_dirs):
                return {"success": False, "error": f"Path not in workspace: {resolved}"}
            search_directories = [resolved]
            search_description = f"within {resolved}"
        else:
            search_directories = list(state["workspace_dirs"])
            search_description = (
                f"within {search_directories[0]}" if len(search_directories) == 1 else f"across {len(search_directories)} workspace directories"
            )

        outcome = glob_search(
            pattern,
            search_directories=search_directories,
            display_root=working_directory,
            vendor_ignore_filename=".geminiignore",
            case_sensitive=bool(arguments.get("case_sensitive", False)),
            respect_git_ignore=bool(arguments.get("respect_git_ignore", True)),
            respect_vendor_ignore=bool(arguments.get("respect_gemini_ignore", True)),
        )
        return format_gemini_glob_result(outcome, pattern=pattern, search_description=search_description)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
