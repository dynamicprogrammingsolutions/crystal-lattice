from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    format_with_line_numbers,
    is_binary_file,
    read_file_with_encoding,
    resolve_path,
    truncate_line,
    validate_path_within_directories,
)


# Kimi content limits
MAX_LINES = 1000
MAX_LINE_LENGTH = 2000
MAX_BYTES = 100 << 10  # 100KB


class KimiReadFileTool(ToolPlugin):
    name = "kimi_read_file_tool"
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
                    "name": "ReadFile",
                    "description": (
                        "Read text content from a file.\n\n"
                        "**Tips:**\n"
                        "- Make sure you follow the description of each tool parameter.\n"
                        "- A `<system>` tag will be given before the read file content.\n"
                        "- The system will notify you when there is anything wrong when reading the file.\n"
                        "- This tool is a tool that you typically want to use in parallel. "
                        "Always read multiple files in one response when possible.\n"
                        "- This tool can only read text files. To read images or videos, "
                        "use other appropriate tools. To list directories, use the Glob tool or "
                        "`ls` command via the Shell tool. To read other file types, use "
                        "appropriate commands via the Shell tool.\n"
                        "- If the file doesn't exist or path is invalid, an error will be returned.\n"
                        "- If you want to search for a certain content/pattern, prefer Grep tool over ReadFile.\n"
                        "- Content will be returned with a line number before each line like `cat -n` format.\n"
                        "- Use `line_offset` and `n_lines` parameters when you only need to read a part of the file.\n"
                        f"- The maximum number of lines that can be read at once is {MAX_LINES}.\n"
                        f"- Any lines longer than {MAX_LINE_LENGTH} characters will be truncated, ending with \"...\".\n"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": (
                                    "The path to the file to read. Absolute paths are required "
                                    "when reading files outside the working directory."
                                ),
                            },
                            "line_offset": {
                                "type": "integer",
                                "description": (
                                    "The line number to start reading from. "
                                    "By default read from the beginning of the file. "
                                    "Set this when the file is too large to read at once."
                                ),
                                "default": 1,
                            },
                            "n_lines": {
                                "type": "integer",
                                "description": (
                                    f"The number of lines to read. "
                                    f"By default read up to {MAX_LINES} lines, which is the max allowed value. "
                                    "Set this value when the file is too large to read at once."
                                ),
                                "default": MAX_LINES,
                            },
                        },
                        "required": ["path"],
                    },
                },
            }
        ]

    def _detect_file_kind(self, file_path: str) -> str:
        """Detect file kind: text, image, video, binary, unknown."""
        suffix = Path(file_path).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        if isinstance(mime_type, str):
            if mime_type.startswith("image/"):
                return "image"
            if mime_type.startswith("video/"):
                return "video"
        if suffix == ".svg":
            return "text"
        if is_binary_file(file_path):
            return "binary"
        return "text"

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "ReadFile":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        raw_path = arguments.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "File path cannot be empty."}

        line_offset = arguments.get("line_offset", 1)
        if not isinstance(line_offset, int) or line_offset < 1:
            return {"success": False, "error": "line_offset must be at least 1."}

        n_lines = arguments.get("n_lines", MAX_LINES)
        if not isinstance(n_lines, int) or n_lines < 1:
            return {"success": False, "error": "n_lines must be at least 1."}

        working_directory = state["working_directory"]
        resolved = resolve_path(raw_path, working_directory=working_directory, allow_relative=True)
        allowed_dirs = list(state["workspace_dirs"])

        # Absolute paths are required for files outside workspace
        if not os.path.isabs(raw_path) and not validate_path_within_directories(resolved, allowed_dirs):
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` is not an absolute path. "
                    "You must provide an absolute path to read a file "
                    "outside the working directory."
                ),
            }

        target = Path(resolved)
        if not target.exists():
            return {"success": False, "error": f"`{raw_path}` does not exist."}
        if not target.is_file():
            return {"success": False, "error": f"`{raw_path}` is not a file."}

        # Detect file type
        file_kind = self._detect_file_kind(str(target))
        if file_kind in ("image", "video"):
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` is a {file_kind} file. "
                    "Use other appropriate tools to read image or video files."
                ),
            }
        if file_kind == "binary":
            return {
                "success": False,
                "error": (
                    f"`{raw_path}` seems not readable. "
                    "You may need to read it with proper shell commands, Python tools "
                    "or MCP tools if available."
                ),
            }

        # Read content
        content = read_file_with_encoding(target)
        if not content:
            return {
                "success": True,
                "result": "",
                "message": "No lines read from file.",
                "kind": "text",
            }
        all_lines = content.split("\n")

        # Slice and apply limits
        lines: list[str] = []
        n_bytes = 0
        truncated_line_numbers: list[int] = []
        max_lines_reached = False
        max_bytes_reached = False

        for i, line in enumerate(all_lines):
            current_line_no = i + 1  # 1-based
            if current_line_no < line_offset:
                continue
            truncated = truncate_line(line, MAX_LINE_LENGTH, marker="...")
            if truncated != line:
                truncated_line_numbers.append(current_line_no)
            lines.append(truncated)
            n_bytes += len(truncated.encode("utf-8"))
            if len(lines) >= n_lines:
                break
            if len(lines) >= MAX_LINES:
                max_lines_reached = True
                break
            if n_bytes >= MAX_BYTES:
                max_bytes_reached = True
                break

        # Format with line numbers
        formatted_output = format_with_line_numbers(lines, start_line=line_offset, width=6)

        # Build Kimi-style message
        if len(lines) > 0:
            message = f"{len(lines)} lines read from file starting from line {line_offset}."
        else:
            message = "No lines read from file."

        if max_lines_reached:
            message += f" Max {MAX_LINES} lines reached."
        elif max_bytes_reached:
            message += f" Max {MAX_BYTES} bytes reached."
        elif len(lines) < n_lines:
            message += " End of file reached."
        if truncated_line_numbers:
            message += f" Lines {truncated_line_numbers} were truncated."

        return {
            "success": True,
            "result": formatted_output,
            "message": message,
            "kind": "text",
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success") is not True:
            return f"Error: {result.get('error')}"
        payload = result.get("result", "")
        message = result.get("message", "")
        if message:
            return f"<system>\n{message}\n</system>\n{payload}"
        return payload

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
