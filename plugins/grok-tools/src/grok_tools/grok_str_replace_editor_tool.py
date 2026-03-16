from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import format_tool_result_text, replace_literal_text, resolve_path, validate_path_within_directories


class GrokStrReplaceEditorTool(ToolPlugin):
    name = "grok_str_replace_editor_tool"
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
                    "name": "str_replace_editor",
                    "description": "Replace specific text in a file. Use this for single line edits only",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to the file to edit"},
                            "old_str": {
                                "type": "string",
                                "description": "Text to replace (must match exactly, or will use fuzzy matching for multi-line strings)",
                            },
                            "new_str": {"type": "string", "description": "Text to replace with"},
                            "replace_all": {
                                "type": "boolean",
                                "description": "Replace all occurrences (default: false, only replaces first occurrence)",
                            },
                        },
                        "required": ["path", "old_str", "new_str"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "str_replace_editor":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        raw_path = arguments.get("path")
        old_str = arguments.get("old_str")
        new_str = arguments.get("new_str")
        replace_all = bool(arguments.get("replace_all", False))
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "The 'path' parameter must be non-empty."}
        if not isinstance(old_str, str) or not isinstance(new_str, str):
            return {"success": False, "error": "The 'old_str' and 'new_str' parameters must be strings."}

        working_directory = state["working_directory"]
        resolved = resolve_path(raw_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            return {"success": False, "error": f"Path not in workspace: {resolved}"}

        outcome = replace_literal_text(
            resolved,
            old_str,
            new_str,
            replace_all=replace_all,
            allow_missing_with_empty_old=False,
        )
        if not outcome["ok"]:
            code = outcome.get("code")
            if code == "not_found":
                return {"success": False, "error": f"File not found: {resolved}"}
            if code == "multiple_occurrences":
                return {
                    "success": False,
                    "error": f"Found {outcome.get('occurrences', 0)} matches for old_str in {resolved}. Set replace_all to true to replace every occurrence.",
                }
            return {"success": False, "error": str(outcome["error"])}

        message = f"Updated file: {resolved}"
        return {"success": True, "result": message, "kind": "text", "return_display": message}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}