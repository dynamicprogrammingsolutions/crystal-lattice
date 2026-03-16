from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    DEFAULT_QWEN_LINE_LIMIT,
    format_qwen_glob_result,
    format_tool_result_text,
    glob_search,
    resolve_path,
    validate_path_within_directories,
)


class QwenGlobTool(ToolPlugin):
    name = "qwen_glob_tool"
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
        }

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "glob",
                    "description": "Fast file pattern matching tool that works with any codebase size\n- Supports glob patterns like \"**/*.js\" or \"src/**/*.ts\"\n- Returns matching file paths sorted by modification time\n- Use this tool when you need to find files by name patterns\n- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead\n- You have the capability to call multiple tools in a single response. It is always better to speculatively perform multiple searches as a batch that are potentially useful.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "The glob pattern to match files against",
                            },
                            "path": {
                                "type": "string",
                                "description": "The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter \"undefined\" or \"null\" - simply omit it for the default behavior. Must be a valid directory path if provided.",
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

        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"], state["global_temp_dir"], state["user_skills_dir"]]
        raw_path = arguments.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            resolved = resolve_path(raw_path, working_directory=state["working_directory"], allow_relative=True)
            if not validate_path_within_directories(resolved, allowed_dirs):
                return {"success": False, "error": f"Path must be within one of the workspace directories: {', '.join(state['workspace_dirs'])}"}
            search_directories = [resolved]
            search_description = f"within {resolved}"
        else:
            search_directories = [state["working_directory"]]
            search_description = "in the workspace directory"

        outcome = glob_search(
            pattern,
            search_directories=search_directories,
            display_root=state["display_root"],
            vendor_ignore_filename=".qwenignore",
            case_sensitive=False,
        )
        return format_qwen_glob_result(
            outcome,
            pattern=pattern,
            search_description=search_description,
            line_limit=state["line_limit"],
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
