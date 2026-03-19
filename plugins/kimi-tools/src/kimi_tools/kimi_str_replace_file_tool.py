from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    replace_edits,
    resolve_path,
    validate_path_within_directories,
)


class KimiStrReplaceFileTool(ToolPlugin):
    name = "kimi_str_replace_file_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        return {
            "working_directory": working_directory,
            "workspace_dirs": [str(Path(p).resolve()) for p in workspace_dirs if isinstance(p, str)],
        }

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "StrReplaceFile",
                    "description": (
                        "Replace specific strings within a specified file.\n\n"
                        "**Tips:**\n"
                        "- Only use this tool on text files.\n"
                        "- Multi-line strings are supported.\n"
                        "- Can specify a single edit or a list of edits in one call.\n"
                        "- You should prefer this tool over WriteFile tool and Shell `sed` command.\n"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": (
                                    "The path to the file to edit. Absolute paths are required "
                                    "when editing files outside the working directory."
                                ),
                            },
                            "edit": {
                                "description": (
                                    "The edit(s) to apply to the file. "
                                    "You can provide a single edit or a list of edits here."
                                ),
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "old": {
                                                "type": "string",
                                                "description": "The old string to replace. Can be multi-line.",
                                            },
                                            "new": {
                                                "type": "string",
                                                "description": "The new string to replace with. Can be multi-line.",
                                            },
                                            "replace_all": {
                                                "type": "boolean",
                                                "description": "Whether to replace all occurrences.",
                                                "default": False,
                                            },
                                        },
                                        "required": ["old", "new"],
                                    },
                                    {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "old": {
                                                    "type": "string",
                                                    "description": "The old string to replace. Can be multi-line.",
                                                },
                                                "new": {
                                                    "type": "string",
                                                    "description": "The new string to replace with. Can be multi-line.",
                                                },
                                                "replace_all": {
                                                    "type": "boolean",
                                                    "description": "Whether to replace all occurrences.",
                                                    "default": False,
                                                },
                                            },
                                            "required": ["old", "new"],
                                        },
                                    },
                                ],
                            },
                        },
                        "required": ["path", "edit"],
                    },
                },
            }
        ]

    def _normalize_edit(self, raw: Any) -> Dict[str, Any] | None:
        """Normalize a raw edit argument to a dict with old, new, replace_all."""
        if isinstance(raw, dict):
            if "old" in raw and "new" in raw:
                return {
                    "old": str(raw["old"]),
                    "new": str(raw["new"]),
                    "replace_all": bool(raw.get("replace_all", False)),
                }
        return None

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "StrReplaceFile":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        raw_path = arguments.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "File path cannot be empty."}

        raw_edit = arguments.get("edit")
        if raw_edit is None:
            return {"success": False, "error": "edit is required."}

        # Normalize single edit or list of edits
        if isinstance(raw_edit, list):
            edits = []
            for item in raw_edit:
                normalized = self._normalize_edit(item)
                if normalized is None:
                    return {"success": False, "error": "Each edit must have 'old' and 'new' fields."}
                edits.append(normalized)
        else:
            normalized = self._normalize_edit(raw_edit)
            if normalized is None:
                return {"success": False, "error": "edit must have 'old' and 'new' fields."}
            edits = [normalized]

        if not edits:
            return {"success": False, "error": "No edits provided."}

        working_directory = state["working_directory"]
        resolved = resolve_path(raw_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"])

        # Absolute paths required for files outside workspace
        if not os.path.isabs(raw_path) and not validate_path_within_directories(resolved, allowed_dirs):
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` is not an absolute path. "
                    "You must provide an absolute path to edit a file "
                    "outside the working directory."
                ),
            }

        target = Path(resolved)
        if not target.exists():
            return {"success": False, "error": f"`{raw_path}` does not exist."}
        if not target.is_file():
            return {"success": False, "error": f"`{raw_path}` is not a file."}

        # Build edits with Kimi semantics: reject_ambiguous=False
        shared_edits = [
            {
                "old": edit["old"],
                "new": edit["new"],
                "replace_all": edit["replace_all"],
                "reject_ambiguous": False,
            }
            for edit in edits
        ]

        outcome = replace_edits(resolved, edits=shared_edits)
        if not outcome["ok"]:
            return {
                "success": False,
                "error": "No replacements were made. The old string was not found in the file.",
            }

        total_replacements = outcome["occurrences"]
        message = (
            f"File successfully edited. "
            f"Applied {len(edits)} edit(s) with {total_replacements} total replacement(s)."
        )

        return {
            "success": True,
            "result": "",
            "message": message,
            "kind": "text",
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success") is not True:
            return f"Error: {result.get('error')}"
        return result.get("message", "")

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
