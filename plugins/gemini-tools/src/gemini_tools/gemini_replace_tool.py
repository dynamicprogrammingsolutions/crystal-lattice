from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_tool_result_text,
    is_path_ignored,
    replace_literal_text,
    resolve_path,
    validate_path_within_directories,
)


class GeminiReplaceTool(ToolPlugin):
    name = "gemini_replace_tool"
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
                    "name": "replace",
                    "description": "Replaces text within a file. By default, the tool expects to find and replace exactly ONE occurrence of `old_string`. If you want to replace multiple occurrences of the exact same string, set `allow_multiple` to true. This tool requires providing significant context around the change to ensure precise targeting. Always use the read_file tool to examine the file's current content before attempting a text replacement.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "The path to the file to modify."},
                            "instruction": {
                                "type": "string",
                                "description": "A clear, semantic instruction for the code change, acting as a high-quality prompt for an expert LLM assistant. It must be self-contained and explain the goal of the change.",
                            },
                            "old_string": {
                                "type": "string",
                                "description": "The exact literal text to replace, preferably unescaped. For single replacements (default), include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. If this string is not the exact literal text (i.e. you escaped it) or does not match exactly, the tool will fail.",
                            },
                            "new_string": {
                                "type": "string",
                                "description": "The exact literal text to replace `old_string` with, preferably unescaped. Provide the EXACT text. Ensure the resulting code is correct and idiomatic. Do not use omission placeholders like '(rest of methods ...)', '...', or 'unchanged code'; provide exact literal code.",
                            },
                            "allow_multiple": {
                                "type": "boolean",
                                "description": "If true, the tool will replace all occurrences of `old_string`. If false (default), it will only succeed if exactly one occurrence is found.",
                            },
                        },
                        "required": ["file_path", "instruction", "old_string", "new_string"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "replace":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        file_path = arguments.get("file_path")
        old_string = arguments.get("old_string")
        new_string = arguments.get("new_string")
        allow_multiple = bool(arguments.get("allow_multiple", False))
        if not isinstance(file_path, str) or not file_path.strip():
            return {"success": False, "error": "The 'file_path' parameter must be non-empty."}
        if not isinstance(old_string, str) or not isinstance(new_string, str):
            return {"success": False, "error": "The 'old_string' and 'new_string' parameters must be strings."}

        working_directory = state["working_directory"]
        resolved = resolve_path(file_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"]) + [state["project_temp_dir"]]
        if not validate_path_within_directories(resolved, allowed_dirs):
            return {"success": False, "error": f"Path not in workspace: {resolved}"}
        if is_path_ignored(resolved, root=working_directory, ignore_filename=".geminiignore"):
            return {"success": False, "error": f"File path '{resolved}' is ignored by configured ignore patterns."}

        outcome = replace_literal_text(
            resolved,
            old_string,
            new_string,
            replace_all=allow_multiple,
            allow_missing_with_empty_old=True,
        )
        if not outcome["ok"]:
            code = outcome.get("code")
            if code == "not_found":
                return {"success": False, "error": f"File not found: {resolved}"}
            if code == "already_exists" and old_string == "":
                return {"success": False, "error": f"File already exists, cannot create: {resolved}"}
            if code == "no_occurrences":
                return {
                    "success": False,
                    "error": f"Failed to edit, 0 occurrences found for old_string in {resolved}. Ensure you're not escaping content incorrectly and check whitespace, indentation, and context. Use read_file tool to verify.",
                }
            if code == "multiple_occurrences":
                occurrences = outcome.get("occurrences", 0)
                return {
                    "success": False,
                    "error": f"Failed to edit. Expected 1 occurrence but found {occurrences} for old_string in file: {resolved}. If you intended to replace multiple occurrences, set 'allow_multiple' to true.",
                }
            return {"success": False, "error": str(outcome["error"])}

        message = (
            f"Created new file: {resolved} with provided content."
            if outcome["created"]
            else f"Successfully modified file: {resolved} ({outcome['occurrences']} replacements)."
        )
        return {"success": True, "result": message, "kind": "text", "return_display": message}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return format_tool_result_text(result)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}