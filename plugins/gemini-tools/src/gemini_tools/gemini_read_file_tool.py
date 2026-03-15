from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_tool_result_payload,
    format_tool_result_text,
    is_path_ignored,
    read_gemini_style_file,
    resolve_path,
    validate_path_within_directories,
)


class GeminiReadFileTool(ToolPlugin):
    name = "gemini_read_file_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        return {
            "config": config,
            "working_directory": working_directory,
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
        }

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads and returns the content of a specified file. If the file is large, the content will be truncated. The tool's response will clearly indicate if truncation has occurred and will provide details on how to read more of the file using the 'start_line' and 'end_line' parameters. Handles text, images (PNG, JPG, GIF, WEBP, SVG, BMP), audio files (MP3, WAV, AIFF, AAC, OGG, FLAC), and PDF files. For text files, it can read specific line ranges.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "The path to the file to read."},
                            "start_line": {
                                "type": "number",
                                "description": "Optional: The 1-based line number to start reading from.",
                            },
                            "end_line": {
                                "type": "number",
                                "description": "Optional: The 1-based line number to end reading at (inclusive).",
                            },
                        },
                        "required": ["file_path"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "read_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        file_path = arguments.get("file_path")
        if not isinstance(file_path, str) or not file_path.strip():
            return {"success": False, "error": "The 'file_path' parameter must be non-empty."}

        start_line = arguments.get("start_line")
        end_line = arguments.get("end_line")
        if start_line is not None and start_line < 1:
            return {"success": False, "error": "start_line must be at least 1"}
        if end_line is not None and end_line < 1:
            return {"success": False, "error": "end_line must be at least 1"}
        if start_line is not None and end_line is not None and start_line > end_line:
            return {"success": False, "error": "start_line cannot be greater than end_line"}

        working_directory = state["working_directory"]
        resolved = resolve_path(file_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            workspace_dirs = ", ".join(state["workspace_dirs"])
            error = (
                f'Path not in workspace: Attempted path "{resolved}" resolves outside the allowed workspace directories: '
                f"{workspace_dirs} or the project temp directory: {state['project_temp_dir']}"
            )
            return {"success": False, "error": error}

        if is_path_ignored(resolved, root=working_directory, ignore_filename=".geminiignore"):
            return {
                "success": False,
                "error": f"File path '{resolved}' is ignored by configured ignore patterns.",
            }

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