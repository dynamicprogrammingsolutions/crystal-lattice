from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    resolve_path,
    validate_path_within_directories,
    write_text_file,
)


class KimiWriteFileTool(ToolPlugin):
    name = "kimi_write_file_tool"
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
                    "name": "WriteFile",
                    "description": (
                        "Write content to a file.\n\n"
                        "**Tips:**\n"
                        "- When `mode` is not specified, it defaults to `overwrite`. "
                        "Always write with caution.\n"
                        "- When the content to write is too long (e.g. > 100 lines), "
                        "use this tool multiple times instead of a single call. "
                        "Use `overwrite` mode at the first time, then use `append` mode "
                        "after the first write.\n"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": (
                                    "The path to the file to write. Absolute paths are required "
                                    "when writing files outside the working directory."
                                ),
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file",
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["overwrite", "append"],
                                "description": (
                                    "The mode to use to write to the file. "
                                    "Two modes are supported: `overwrite` for overwriting "
                                    "the whole file and `append` for appending to the end "
                                    "of an existing file."
                                ),
                                "default": "overwrite",
                            },
                        },
                        "required": ["path", "content"],
                    },
                },
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "WriteFile":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        raw_path = arguments.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "File path cannot be empty."}

        content = arguments.get("content")
        if not isinstance(content, str):
            return {"success": False, "error": "content must be a string."}

        mode = arguments.get("mode", "overwrite")
        if mode not in ("overwrite", "append"):
            return {
                "success": False,
                "error": (
                    f"Invalid write mode: `{mode}`. "
                    "Mode must be either `overwrite` or `append`."
                ),
            }

        working_directory = state["working_directory"]
        resolved = resolve_path(raw_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"])

        # Absolute paths required for files outside workspace
        if not os.path.isabs(raw_path) and not validate_path_within_directories(resolved, allowed_dirs):
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` is not an absolute path. "
                    "You must provide an absolute path to write a file "
                    "outside the working directory."
                ),
            }

        target = Path(resolved)
        if not target.parent.exists():
            return {"success": False, "error": f"`{raw_path}` parent directory does not exist."}

        outcome = write_text_file(resolved, content, mode=mode)
        if not outcome["ok"]:
            return {
                "success": False,
                "error": outcome.get("error", "Failed to write file."),
            }

        file_size = target.stat().st_size
        action = "overwritten" if mode == "overwrite" else "appended to"
        message = f"File successfully {action}. Current size: {file_size} bytes."

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
