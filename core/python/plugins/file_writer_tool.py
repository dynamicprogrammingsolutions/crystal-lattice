"""
FileWriterTool plugin: write text content to a file within allowed paths.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from agent_core.types import ToolPlugin


class FileWriterTool(ToolPlugin):
    name: str = "file_writer"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "allowed_paths": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["."],
                "description": "Allowed base paths for file writing",
            },
            "max_file_size": {
                "type": "integer",
                "default": 5 * 1024 * 1024,
                "description": "Maximum content size to write in bytes",
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Tools are free to choose their own internal state shape. This
        # implementation only needs access to configuration values.
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write text content to a file (overwrites if exists)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to write",
                            },
                            "content": {
                                "type": "string",
                                "description": "Text content to write",
                            },
                        },
                        "required": ["file_path", "content"],
                    },
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name != "write_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        raw_path = arguments.get("file_path", "")
        file_path = str(raw_path).strip()
        content = arguments.get("content", "")
        try:
            abs_path = os.path.abspath(file_path)
        except Exception:
            return {"success": False, "error": f"Invalid path: {file_path}"}
        allowed = state.get("config", {}).get("allowed_paths", ["."])
        if not any(abs_path.startswith(os.path.abspath(base)) for base in allowed):
            return {
                "success": False,
                "error": f"Access denied: {file_path} not in allowed paths",
            }
        try:
            data = content if isinstance(content, str) else str(content)
            max_size = int(state.get("config", {}).get("max_file_size", 5 * 1024 * 1024))
            if len(data.encode("utf-8")) > max_size:
                return {"success": False, "error": "Content too large"}
            os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(data)
            return {
                "success": True,
                "result": {"path": abs_path, "bytes_written": len(data.encode("utf-8"))},
            }
        except Exception as e:
            return {"success": False, "error": f"Error writing file: {str(e)}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return (
            f"File written: {result['result'].get('path')} ({result['result'].get('bytes_written')} bytes)"
            if result.get("success")
            else f"Error: {result.get('error')}"
        )
