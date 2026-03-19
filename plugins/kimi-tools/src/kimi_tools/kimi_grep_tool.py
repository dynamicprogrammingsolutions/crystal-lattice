from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import grep_search


class KimiGrepTool(ToolPlugin):
    name = "kimi_grep_tool"
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
                    "name": "Grep",
                    "description": "Search for patterns in file contents using regular expressions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "The regular expression pattern to search for in file contents",
                            },
                            "path": {
                                "type": "string",
                                "description": (
                                    "File or directory to search in. Defaults to current "
                                    "working directory. If specified, it must be an absolute path."
                                ),
                                "default": ".",
                            },
                            "glob": {
                                "type": "string",
                                "description": (
                                    "Glob pattern to filter files (e.g. `*.js`, `*.{ts,tsx}`). "
                                    "No filter by default."
                                ),
                            },
                            "output_mode": {
                                "type": "string",
                                "enum": ["content", "files_with_matches", "count_matches"],
                                "description": (
                                    "`content`: Show matching lines (supports `-B`, `-A`, "
                                    "`-C`, `-n`, `head_limit`); "
                                    "`files_with_matches`: Show file paths (supports `head_limit`); "
                                    "`count_matches`: Show total number of matches. "
                                    "Defaults to `files_with_matches`."
                                ),
                                "default": "files_with_matches",
                            },
                            "-B": {
                                "type": "integer",
                                "description": (
                                    "Number of lines to show before each match (the `-B` option). "
                                    "Requires `output_mode` to be `content`."
                                ),
                            },
                            "-A": {
                                "type": "integer",
                                "description": (
                                    "Number of lines to show after each match (the `-A` option). "
                                    "Requires `output_mode` to be `content`."
                                ),
                            },
                            "-C": {
                                "type": "integer",
                                "description": (
                                    "Number of lines to show before and after each match "
                                    "(the `-C` option). Requires `output_mode` to be `content`."
                                ),
                            },
                            "-n": {
                                "type": "boolean",
                                "description": (
                                    "Show line numbers in output (the `-n` option). "
                                    "Requires `output_mode` to be `content`."
                                ),
                                "default": False,
                            },
                            "-i": {
                                "type": "boolean",
                                "description": "Case insensitive search (the `-i` option).",
                                "default": False,
                            },
                            "type": {
                                "type": "string",
                                "description": (
                                    "File type to search. Examples: py, rust, js, ts, go, java, etc. "
                                    "More efficient than `glob` for standard file types."
                                ),
                            },
                            "head_limit": {
                                "type": "integer",
                                "description": (
                                    "Limit output to first N lines, equivalent to `| head -N`. "
                                    "Works across all output modes."
                                ),
                            },
                            "multiline": {
                                "type": "boolean",
                                "description": (
                                    "Enable multiline mode where `.` matches newlines and "
                                    "patterns can span lines (the `-U` and `--multiline-dotall` options). "
                                    "By default, multiline mode is disabled."
                                ),
                                "default": False,
                            },
                        },
                        "required": ["pattern"],
                    },
                },
            }
        ]

    def _relative_path(self, abs_path: str, search_path: str) -> str:
        """Convert absolute path to relative path from search directory."""
        try:
            return str(Path(abs_path).resolve().relative_to(Path(search_path).resolve()))
        except ValueError:
            return abs_path

    def _format_content_result(self, results: list[dict[str, Any]], search_path: str) -> str:
        """Format content-mode results as plain text lines."""
        lines: list[str] = []
        for item in results:
            path_str = self._relative_path(item["path"], search_path)
            line = item.get("line", "")
            line_num = item.get("line_number", 0)
            if line_num:
                lines.append(f"{path_str}:{line_num}:{line}")
            else:
                lines.append(f"{path_str}:{line}")
        return "\n".join(lines)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "Grep":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        pattern = arguments.get("pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            return {"success": False, "error": "pattern is required."}

        raw_path = arguments.get("path", ".")
        if isinstance(raw_path, str) and raw_path.strip():
            if os.path.isabs(raw_path):
                search_path = raw_path
            else:
                search_path = str((Path(state["working_directory"]) / raw_path).resolve())
        else:
            search_path = state["working_directory"]

        output_mode = arguments.get("output_mode", "files_with_matches")
        if output_mode not in ("content", "files_with_matches", "count_matches"):
            return {
                "success": False,
                "error": (
                    f"Invalid output_mode: `{output_mode}`. "
                    "Must be 'content', 'files_with_matches', or 'count_matches'."
                ),
            }

        context_before = arguments.get("-B")
        context_after = arguments.get("-A")
        context_both = arguments.get("-C")
        show_line_numbers = arguments.get("-n", False)
        ignore_case = arguments.get("-i", False)
        glob_pattern = arguments.get("glob")
        type_filter = arguments.get("type")
        head_limit = arguments.get("head_limit")
        multiline = arguments.get("multiline", False)

        # Apply -C to both before and after if specified
        if context_both is not None:
            if context_before is None:
                context_before = context_both
            if context_after is None:
                context_after = context_both

        # Map output_mode to grep_search parameters
        names_only = output_mode == "files_with_matches"
        count_mode = output_mode == "count_matches"

        outcome = grep_search(
            pattern,
            search_path=search_path,
            display_root=state["working_directory"],
            glob_pattern=glob_pattern,
            ignore_case=ignore_case,
            names_only=names_only,
            count_mode=count_mode,
            show_line_numbers=show_line_numbers,
            context_before=context_before,
            context_after=context_after,
            type_filter=type_filter,
            multiline=multiline,
            respect_git_ignore=True,
        )

        if not outcome["ok"]:
            return {"success": False, "error": outcome.get("error", "Grep failed.")}

        results = outcome["results"]

        if not results:
            return {
                "success": True,
                "result": "",
                "message": "No matches found.",
                "kind": "text",
            }

        # Format output based on mode
        message = ""

        if output_mode == "files_with_matches":
            output_lines = sorted(set(
                self._relative_path(item["path"], search_path) for item in results
            ))
            output_text = "\n".join(output_lines)
        elif output_mode == "count_matches":
            output_lines = []
            for item in results:
                count = item.get("count", 0)
                rel = self._relative_path(item["path"], search_path)
                output_lines.append(f"{rel}:{count}")
            output_text = "\n".join(output_lines)
        else:  # content
            output_text = self._format_content_result(results, search_path)

        # Apply head_limit
        if head_limit is not None and isinstance(head_limit, int) and head_limit > 0:
            lines = output_text.split("\n")
            if len(lines) > head_limit:
                output_text = "\n".join(lines[:head_limit])
                message = f"Results truncated to first {head_limit} lines"
                output_text += f"\n... (results truncated to {head_limit} lines)"

        return {
            "success": True,
            "result": output_text,
            "message": message,
            "kind": "text",
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success") is not True:
            return f"Error: {result.get('error')}"
        payload = result.get("result", "")
        message = result.get("message", "")
        if message:
            return f"{payload}\n\n{message}"
        return payload

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
