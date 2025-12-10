"""
FileReaderTool example (class-based tool plugin) derived from PLUGIN_EXAMPLES.md.
"""

import os
from typing import Any, Dict, List
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
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "text",
                "key": "allowed_paths",
                "label": "Allowed Paths (comma-separated)",
            }
        ]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Tool state is an opaque dict owned by the tool. This example
        # only relies on configuration values.
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a text file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read",
                            }
                        },
                        "required": ["file_path"],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name != "read_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        file_path = arguments.get("file_path", "")
        allowed = state["config"].get("allowed_paths", ["."])
        if not any(
            os.path.abspath(file_path).startswith(os.path.abspath(base))
            for base in allowed
        ):
            return {
                "success": False,
                "error": f"Access denied: {file_path} not in allowed paths",
            }
        try:
            size = os.path.getsize(file_path)
            if size > state["config"].get("max_file_size", 1048576):
                return {"success": False, "error": f"File too large: {size} bytes"}
            with open(file_path, "r", encoding="utf-8") as f:
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
