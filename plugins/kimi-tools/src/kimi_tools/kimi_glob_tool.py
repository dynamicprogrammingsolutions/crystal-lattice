from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    glob_search,
    resolve_path,
    validate_path_within_directories,
)


MAX_MATCHES = 1000


class KimiGlobTool(ToolPlugin):
    name = "kimi_glob_tool"
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
                    "name": "Glob",
                    "description": (
                        "Find files and directories using glob patterns. "
                        "This tool supports standard glob syntax like `*`, `?`, and `**` "
                        "for recursive searches.\n\n"
                        "**When to use:**\n"
                        "- Find files matching specific patterns (e.g., all Python files: `*.py`)\n"
                        "- Search for files recursively in subdirectories (e.g., `src/**/*.js`)\n"
                        "- Locate configuration files (e.g., `*.config.*`, `*.json`)\n"
                        "- Find test files (e.g., `test_*.py`, `*_test.go`)\n\n"
                        "**Example patterns:**\n"
                        "- `*.py` - All Python files in current directory\n"
                        "- `src/**/*.js` - All JavaScript files in src directory recursively\n"
                        "- `test_*.py` - Python test files starting with \"test_\"\n"
                        f"- Maximum {MAX_MATCHES} matches returned.\n\n"
                        "**Bad example patterns:**\n"
                        "- `**`, `**/*.py` - Any pattern starting with '**' will be rejected.\n"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Glob pattern to match files/directories.",
                            },
                            "directory": {
                                "type": "string",
                                "description": (
                                    "Absolute path to the directory to search in "
                                    "(defaults to working directory)."
                                ),
                            },
                            "include_dirs": {
                                "type": "boolean",
                                "description": "Whether to include directories in results.",
                                "default": True,
                            },
                        },
                        "required": ["pattern"],
                    },
                },
            }
        ]

    def _list_top_level(self, working_directory: str) -> str:
        """List top-level directory entries for **-prefix rejection message."""
        root = Path(working_directory)
        if not root.is_dir():
            return ""
        entries = []
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            name = child.name
            if child.is_dir():
                name += "/"
            entries.append(name)
        return "\n".join(entries)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "Glob":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        pattern = arguments.get("pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            return {"success": False, "error": "pattern is required."}

        working_directory = state["working_directory"]
        allowed_dirs = list(state["workspace_dirs"])

        # **-prefix rejection
        if pattern.startswith("**"):
            ls_result = self._list_top_level(working_directory)
            return {
                "success": False,
                "error": (
                    f"Pattern `{pattern}` starts with '**' which is not allowed. "
                    "This would recursively search all directories and may include large "
                    "directories like `node_modules`. Use more specific patterns instead. "
                    "For your convenience, a list of all files and directories in the "
                    "top level of the working directory is provided below."
                ),
                "result": ls_result,
            }

        # Resolve search directory
        raw_directory = arguments.get("directory")
        if raw_directory is not None:
            if not isinstance(raw_directory, str) or not raw_directory.strip():
                return {"success": False, "error": "directory must be a non-empty string."}
            if not os.path.isabs(raw_directory):
                return {
                    "success": False,
                    "error": (
                        f"`{raw_directory}` is not an absolute path. "
                        "You must provide an absolute path to search."
                    ),
                }
            search_dir = str(Path(raw_directory).resolve())
            # Validate directory is within workspace
            if not validate_path_within_directories(search_dir, allowed_dirs):
                return {
                    "success": False,
                    "error": (
                        f"`{raw_directory}` is outside the workspace. "
                        "You can only search within the working directory "
                        "and additional directories."
                    ),
                }
        else:
            search_dir = working_directory

        search_target = Path(search_dir)
        if not search_target.exists():
            return {"success": False, "error": f"`{raw_directory}` does not exist."}
        if not search_target.is_dir():
            return {"success": False, "error": f"`{raw_directory}` is not a directory."}

        include_dirs = arguments.get("include_dirs", True)

        outcome = glob_search(
            pattern,
            search_directories=[search_dir],
            display_root=working_directory,
            case_sensitive=False,
            respect_git_ignore=True,
            sort_mode="alphabetical",
            max_results=MAX_MATCHES,
            include_dirs=include_dirs,
        )

        if not outcome["ok"]:
            return {"success": False, "error": outcome.get("error", "Glob failed.")}

        # Format relative paths
        abs_paths = outcome["paths"]
        try:
            rel_root = Path(search_dir).resolve()
            relative_paths = sorted(
                str(Path(p).resolve().relative_to(rel_root)) for p in abs_paths
            )
        except ValueError:
            relative_paths = sorted(abs_paths)

        message = (
            f"Found {len(relative_paths)} matches for pattern `{pattern}`."
            if len(relative_paths) > 0
            else f"No matches found for pattern `{pattern}`."
        )

        if len(relative_paths) > MAX_MATCHES:
            relative_paths = relative_paths[:MAX_MATCHES]
            message += (
                f" Only the first {MAX_MATCHES} matches are returned. "
                "You may want to use a more specific pattern."
            )

        return {
            "success": True,
            "result": "\n".join(relative_paths),
            "message": message,
            "kind": "text",
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success") is not True:
            error = result.get("error", "Unknown error")
            extra = result.get("result", "")
            if extra:
                return f"Error: {error}\n\n{extra}"
            return f"Error: {error}"
        payload = result.get("result", "")
        return payload

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "text", "content": text}
