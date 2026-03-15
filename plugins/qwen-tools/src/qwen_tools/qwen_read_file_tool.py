from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    DEFAULT_QWEN_CHAR_LIMIT,
    DEFAULT_QWEN_LINE_LIMIT,
    format_tool_result_payload,
    format_tool_result_text,
    is_path_ignored,
    read_qwen_style_file,
    validate_path_within_directories,
)


class QwenReadFileTool(ToolPlugin):
    name = "qwen_read_file_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("workspace_dirs") or config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        global_temp_dir = str(config.get("global_temp_dir") or tempfile.gettempdir())
        user_skills_dir = str(config.get("user_skills_dir") or Path.home() / ".qwen" / "skills")
        return {
            "config": config,
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
                    "name": "read_file",
                    "description": "Reads and returns the content of a specified file. If the file is large, the content will be truncated. The tool's response will clearly indicate if truncation has occurred and will provide details on how to read more of the file using the 'offset' and 'limit' parameters. Handles text, images (PNG, JPG, GIF, WEBP, SVG, BMP), and PDF files. For text files, it can read specific line ranges.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "absolute_path": {
                                "type": "string",
                                "description": "The absolute path to the file to read (e.g., '/home/user/project/file.txt'). Relative paths are not supported. You must provide an absolute path.",
                            },
                            "offset": {
                                "type": "number",
                                "description": "Optional: For text files, the 0-based line number to start reading from. Requires 'limit' to be set. Use for paginating through large files.",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Optional: For text files, maximum number of lines to read. Use with 'offset' to paginate through large files. If omitted, reads the entire file (if feasible, up to a default limit).",
                            },
                        },
                        "required": ["absolute_path"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "read_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        absolute_path = arguments.get("absolute_path")
        if not isinstance(absolute_path, str) or not absolute_path.strip():
            return {"success": False, "error": "The 'absolute_path' parameter must be non-empty."}
        if not os.path.isabs(absolute_path):
            return {
                "success": False,
                "error": f"File path must be absolute, but was relative: {absolute_path}. You must provide an absolute path.",
            }

        offset = arguments.get("offset")
        limit = arguments.get("limit")
        if offset is not None and offset < 0:
            return {"success": False, "error": "Offset must be a non-negative number"}
        if limit is not None and limit <= 0:
            return {"success": False, "error": "Limit must be a positive number"}

        resolved = str(Path(absolute_path).resolve())
        allowed_dirs = list(state["workspace_dirs"]) + [
            state["project_temp_dir"],
            state["global_temp_dir"],
            state["user_skills_dir"],
        ]
        if not validate_path_within_directories(resolved, allowed_dirs):
            workspace_dirs = ", ".join(state["workspace_dirs"])
            error = (
                "File path must be within one of the workspace directories: "
                f"{workspace_dirs} or within the project temp directory: {state['project_temp_dir']}"
            )
            return {"success": False, "error": error}

        display_root = state["display_root"]
        if is_path_ignored(resolved, root=display_root, ignore_filename=".qwenignore"):
            return {
                "success": False,
                "error": f"File path '{resolved}' is ignored by .qwenignore pattern(s).",
            }

        outcome = read_qwen_style_file(
            resolved,
            display_root=display_root,
            offset=int(offset) if offset is not None else None,
            limit=int(limit) if limit is not None else None,
            line_limit=state["line_limit"],
            char_limit=state["char_limit"],
        )
        return format_tool_result_payload(outcome)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}