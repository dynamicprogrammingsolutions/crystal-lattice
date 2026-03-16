from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_gemini_grep_result,
    format_tool_result_text,
    grep_search,
    resolve_path,
    validate_path_within_directories,
)


class GeminiGrepSearchTool(ToolPlugin):
    name = "gemini_grep_search_tool"
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
                    "name": "grep_search",
                    "description": "Searches for a regular expression pattern within file contents. Max 100 matches.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "The regular expression (regex) pattern to search for within file contents (e.g., 'function\\s+myFunction', 'import\\s+\\{.*\\}\\s+from\\s+.*').",
                            },
                            "dir_path": {
                                "type": "string",
                                "description": "Optional: The absolute path to the directory to search within. If omitted, searches the current working directory.",
                            },
                            "include_pattern": {
                                "type": "string",
                                "description": "Optional: A glob pattern to filter which files are searched (e.g., '*.js', '*.{ts,tsx}', 'src/**'). If omitted, searches all files (respecting potential global ignores).",
                            },
                            "exclude_pattern": {
                                "type": "string",
                                "description": "Optional: A regular expression pattern to exclude from the search results. If a line matches both the pattern and the exclude_pattern, it will be omitted.",
                            },
                            "names_only": {
                                "type": "boolean",
                                "description": "Optional: If true, only the file paths of the matches will be returned, without the line content or line numbers. This is useful for gathering a list of files.",
                            },
                            "max_matches_per_file": {
                                "type": "integer",
                                "description": "Optional: Maximum number of matches to return per file. Use this to prevent being overwhelmed by repetitive matches in large files.",
                                "minimum": 1,
                            },
                            "total_max_matches": {
                                "type": "integer",
                                "description": "Optional: Maximum number of total matches to return. Use this to limit the overall size of the response. Defaults to 100 if omitted.",
                                "minimum": 1,
                            },
                        },
                        "required": ["pattern"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "grep_search":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        pattern = arguments.get("pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            return {"success": False, "error": "The 'pattern' parameter must be non-empty."}

        working_directory = state["working_directory"]
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        dir_path = arguments.get("dir_path")
        if isinstance(dir_path, str) and dir_path.strip():
            resolved = resolve_path(dir_path, working_directory=working_directory, allow_relative=True)
            if not validate_path_within_directories(resolved, allowed_dirs):
                return {"success": False, "error": f"Path not in workspace: {resolved}"}
            search_path = resolved
            search_description = f'in path "{dir_path}"'
        else:
            search_path = working_directory
            search_description = "in the workspace directory"

        total_max_matches = arguments.get("total_max_matches")
        max_matches_per_file = arguments.get("max_matches_per_file")
        outcome = grep_search(
            pattern,
            search_path=search_path,
            display_root=working_directory,
            glob_pattern=arguments.get("include_pattern") if isinstance(arguments.get("include_pattern"), str) else None,
            exclude_pattern=arguments.get("exclude_pattern") if isinstance(arguments.get("exclude_pattern"), str) else None,
            names_only=bool(arguments.get("names_only", False)),
            max_matches_per_file=int(max_matches_per_file) if isinstance(max_matches_per_file, (int, float)) else None,
            total_max_matches=int(total_max_matches) if isinstance(total_max_matches, (int, float)) else 100,
            ignore_case=False,
            vendor_ignore_filename=".geminiignore",
        )
        return format_gemini_grep_result(
            outcome,
            pattern=pattern,
            search_description=search_description,
            names_only=bool(arguments.get("names_only", False)),
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
