from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    DEFAULT_QWEN_CHAR_LIMIT,
    DEFAULT_QWEN_LINE_LIMIT,
    format_qwen_grep_result,
    format_tool_result_text,
    grep_search,
    resolve_path,
    validate_path_within_directories,
)


class QwenGrepSearchTool(ToolPlugin):
    name = "qwen_grep_search_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("workspace_dirs") or config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        global_temp_dir = str(config.get("global_temp_dir") or tempfile.gettempdir())
        user_skills_dir = str(config.get("user_skills_dir") or Path.home() / ".qwen" / "skills")
        return {
            "working_directory": working_directory,
            "display_root": str(Path(working_directory).resolve()),
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
            "global_temp_dir": str(Path(global_temp_dir).resolve()),
            "user_skills_dir": str(Path(user_skills_dir).resolve()),
            "line_limit": int(config.get("truncate_tool_output_lines") or DEFAULT_QWEN_LINE_LIMIT),
            "char_limit": int(config.get("truncate_tool_output_threshold") or DEFAULT_QWEN_CHAR_LIMIT),
        }

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "grep_search",
                    "description": "A powerful search tool for finding patterns in files\n\n  Usage:\n  - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command. The Grep tool has been optimized for correct permissions and access.\n  - Supports full regex syntax (e.g., \"log.*Error\", \"function\\s+\\w+\")\n  - Filter files with glob parameter (e.g., \"*.js\", \"**/*.tsx\")\n  - Case-insensitive by default\n  - Use Task tool for open-ended searches requiring multiple rounds\n",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "The regular expression pattern to search for in file contents",
                            },
                            "glob": {
                                "type": "string",
                                "description": "Glob pattern to filter files (e.g. \"*.js\", \"*.{ts,tsx}\")",
                            },
                            "path": {
                                "type": "string",
                                "description": "File or directory to search in. Defaults to current working directory.",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Limit output to first N matching lines. Optional - shows all matches if not specified.",
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

        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"], state["global_temp_dir"], state["user_skills_dir"]]
        raw_path = arguments.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            resolved = resolve_path(raw_path, working_directory=state["working_directory"], allow_relative=True)
            if not validate_path_within_directories(resolved, allowed_dirs):
                return {"success": False, "error": f"Path must be within one of the workspace directories: {', '.join(state['workspace_dirs'])}"}
            search_path = resolved
            search_description = f'in path "{raw_path}"'
        else:
            search_path = state["working_directory"]
            search_description = "in the workspace directory"

        limit = arguments.get("limit")
        outcome = grep_search(
            pattern,
            search_path=search_path,
            display_root=state["display_root"],
            glob_pattern=arguments.get("glob") if isinstance(arguments.get("glob"), str) else None,
            total_max_matches=int(limit) if isinstance(limit, (int, float)) else None,
            ignore_case=True,
            vendor_ignore_filename=".qwenignore",
        )
        effective_line_limit = int(limit) if isinstance(limit, (int, float)) else state["line_limit"]
        return format_qwen_grep_result(
            outcome,
            pattern=pattern,
            search_description=search_description,
            glob_pattern=arguments.get("glob") if isinstance(arguments.get("glob"), str) else None,
            line_limit=effective_line_limit,
            char_limit=state["char_limit"],
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
