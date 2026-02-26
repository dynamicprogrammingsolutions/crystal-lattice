"""
FileReaderTool plugin: simple file reading tool with allowlist and size limit.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from agent_core.types import ToolPlugin


class FileReaderTool(ToolPlugin):
    name: str = "file_reader"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "allowed_paths": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["."],
                "description": "Allowed base paths for file reading",
            },
            "max_file_size": {
                "type": "integer",
                "default": 1048576,
                "description": "Maximum file size in bytes",
            },
            "working_directory": {
                "type": "string",
                "default": ".",
                "description": "Working directory for resolving relative paths",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Tools are free to choose their own internal state shape. This
        # implementation only needs access to configuration values.
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        working_dir = state.get("config", {}).get("working_directory", ".")
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": f"Read contents of a text file. Relative paths are resolved from working directory: {working_dir}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read (absolute or relative to working directory)",
                            }
                        },
                        "required": ["file_path"],
                    },
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name != "read_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        file_path = arguments.get("file_path", "")
        
        # Get working directory from config
        working_dir = state.get("config", {}).get("working_directory", ".")
        
        try:
            # If path is relative, resolve it relative to working_directory
            if not os.path.isabs(file_path):
                file_path = os.path.join(working_dir, file_path)
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
            size = os.path.getsize(abs_path)
            if size > state.get("config", {}).get("max_file_size", 1048576):
                return {"success": False, "error": f"File too large: {size} bytes"}
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "result": content}
        except Exception as e:
            return {"success": False, "error": f"Error reading file: {str(e)}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return (
            f"File contents:\n{result['result']}"
            if result.get("success")
            else f"Error: {result.get('error')}"
        )
