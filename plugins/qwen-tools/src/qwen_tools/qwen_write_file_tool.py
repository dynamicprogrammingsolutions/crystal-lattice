from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import format_tool_result_text, is_path_ignored, validate_path_within_directories, write_text_file


class QwenWriteFileTool(ToolPlugin):
    name = "qwen_write_file_tool"
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
                    "name": "write_file",
                    "description": "Writes content to a specified file in the local filesystem.\n\n      The user has the ability to modify `content`. If modified, this will be stated in the response.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The absolute path to the file to write to (e.g., '/home/user/project/file.txt'). Relative paths are not supported.",
                            },
                            "content": {"type": "string", "description": "The content to write to the file."},
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
            return {"success": False, "error": 'Missing or empty "file_path"'}
        if not isinstance(content, str):
            return {"success": False, "error": "The 'content' parameter must be a string."}
        if not os.path.isabs(file_path):
            return {"success": False, "error": f"File path must be absolute: {file_path}"}

        resolved = str(Path(file_path).resolve())
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"], state["global_temp_dir"], state["user_skills_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            directories = ", ".join(state["workspace_dirs"])
            return {"success": False, "error": f"File path must be within one of the workspace directories: {directories}"}
        if is_path_ignored(resolved, root=state["display_root"], ignore_filename=".qwenignore"):
            return {"success": False, "error": f"File path '{resolved}' is ignored by .qwenignore pattern(s)."}

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