from __future__ import annotations

import shlex
import time
from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import enumerate_workspace_paths, resolve_workspace_root

from .command_result import CommandResultMixin, command_error, command_result


FIND_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "find",
        "description": (
            "List workspace paths recursively with find-like filtering. Equivalent "
            "to `find <path> -type <type> -name <name> -print`, optionally sorted."
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Workspace-relative starting path; defaults to .",
                },
                "name": {
                    "type": "string",
                    "description": "Filename glob such as `*.md`",
                },
                "names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Alternative filename globs combined as OR",
                },
                "type": {
                    "type": "string",
                    "enum": ["file", "directory", "any"],
                    "description": "Path type, equivalent to `find -type f` or `-type d`",
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden paths",
                },
                "max_depth": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum recursive depth below the starting path",
                },
                "sort": {
                    "type": "boolean",
                    "description": "Sort paths, equivalent to piping output to sort",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Requested path cap; app limits remain authoritative",
                },
            },
            "required": [],
        },
    },
}


class CodexLikeFindTool(CommandResultMixin, ToolPlugin):
    name = "embedded_codex_find"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": resolve_workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [FIND_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "find"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        started = time.monotonic()
        if tool_name != "find" or not isinstance(payload, dict):
            return command_error(
                "find",
                "find: input must be an object",
                started=started,
            )
        path = payload.get("path")
        path = path if isinstance(path, str) and path else "."
        kind = payload.get("type")
        kind = kind if kind in {"file", "directory", "any"} else "any"
        name = payload.get("name")
        names = payload.get("names")
        patterns = [
            item for item in names if isinstance(item, str) and item
        ] if isinstance(names, list) else []
        if isinstance(name, str) and name:
            patterns.insert(0, name)
        command_parts = ["find", shlex.quote(path)]
        if kind == "file":
            command_parts.extend(["-type", "f"])
        elif kind == "directory":
            command_parts.extend(["-type", "d"])
        for pattern in patterns:
            command_parts.extend(["-name", shlex.quote(pattern)])
        command_parts.append("-print")
        if bool(payload.get("sort", True)):
            command_parts.extend(["|", "sort"])
        command = " ".join(command_parts)
        max_depth = payload.get("max_depth")
        max_depth = (
            max_depth
            if isinstance(max_depth, int) and max_depth > 0
            else None
        )
        requested_limit = payload.get("max_results")
        requested_limit = (
            requested_limit
            if isinstance(requested_limit, int) and requested_limit > 0
            else 500
        )
        try:
            result = enumerate_workspace_paths(
                state["workspace_root"],
                start_path=path,
                name_globs=patterns or None,
                kind=kind,
                include_hidden=bool(payload.get("include_hidden", False)),
                max_depth=max_depth,
                max_results=requested_limit,
                sort_results=bool(payload.get("sort", True)),
            )
            paths = [entry.path for entry in result.paths]
            return command_result(
                command,
                "\n".join(paths),
                started=started,
                truncated=result.truncated,
            )
        except (OSError, ValueError) as error:
            return command_error(command, f"find: {error}", started=started)