from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_tool_result_text,
    is_path_ignored,
    replace_literal_text,
    validate_path_within_directories,
)


class QwenEditTool(ToolPlugin):
    name = "qwen_edit_tool"
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
                    "name": "edit",
                    "description": "Replaces text within a file. By default, replaces a single occurrence. Set `replace_all` to true when you intend to modify every instance of `old_string`. This tool requires providing significant context around the change to ensure precise targeting. Always use the read_file tool to examine the file's current content before attempting a text replacement.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The absolute path to the file to modify. Must start with '/'.",
                            },
                            "old_string": {
                                "type": "string",
                                "description": "The exact literal text to replace, preferably unescaped. For single replacements (default), include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. If this string is not the exact literal text (i.e. you escaped it) or does not match exactly, the tool will fail.",
                            },
                            "new_string": {
                                "type": "string",
                                "description": "The exact literal text to replace `old_string` with, preferably unescaped. Provide the EXACT text. Ensure the resulting code is correct and idiomatic.",
                            },
                            "replace_all": {
                                "type": "boolean",
                                "description": "Replace all occurrences of old_string (default false).",
                            },
                        },
                        "required": ["file_path", "old_string", "new_string"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "edit":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        file_path = arguments.get("file_path")
        old_string = arguments.get("old_string")
        new_string = arguments.get("new_string")
        replace_all = bool(arguments.get("replace_all", False))
        if not isinstance(file_path, str) or not file_path.strip():
            return {"success": False, "error": "The 'file_path' parameter must be non-empty."}
        if not os.path.isabs(file_path):
            return {"success": False, "error": f"File path must be absolute: {file_path}"}
        if not isinstance(old_string, str) or not isinstance(new_string, str):
            return {"success": False, "error": "The 'old_string' and 'new_string' parameters must be strings."}

        resolved = str(Path(file_path).resolve())
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"], state["global_temp_dir"], state["user_skills_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            directories = ", ".join(state["workspace_dirs"])
            return {"success": False, "error": f"File path must be within one of the workspace directories: {directories}"}
        if is_path_ignored(resolved, root=state["display_root"], ignore_filename=".qwenignore"):
            return {"success": False, "error": f"File path '{resolved}' is ignored by .qwenignore pattern(s)."}

        outcome = replace_literal_text(
            resolved,
            old_string,
            new_string,
            replace_all=replace_all,
            allow_missing_with_empty_old=True,
        )
        if not outcome["ok"]:
            code = outcome.get("code")
            if code == "not_found":
                return {"success": False, "error": "File not found. Cannot apply edit. Use an empty old_string to create a new file."}
            if code == "already_exists" and old_string == "":
                return {"success": False, "error": "Failed to edit. Attempted to create a file that already exists."}
            if code == "no_occurrences":
                return {
                    "success": False,
                    "error": f"Failed to edit, 0 occurrences found for old_string in {resolved}. No edits made. The exact text in old_string was not found. Ensure you're not escaping content incorrectly and check whitespace, indentation, and context. Use read_file tool to verify.",
                }
            if code == "multiple_occurrences":
                return {
                    "success": False,
                    "error": f"Failed to edit. Found {outcome.get('occurrences', 0)} occurrences for old_string in {resolved} but replace_all was not enabled.",
                }
            return {"success": False, "error": str(outcome["error"])}

        message = (
            f"Created new file: {resolved} with provided content."
            if outcome["created"]
            else f"The file: {resolved} has been updated."
        )
        return {"success": True, "result": message, "kind": "text", "return_display": message}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}