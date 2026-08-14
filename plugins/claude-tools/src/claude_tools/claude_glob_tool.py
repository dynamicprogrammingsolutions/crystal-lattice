# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from tool_compat_shared.search_engine import glob_search

from .interop import claude_tool_interop_contribution


GLOB_DESCRIPTION = (
    "- Fast file pattern matching tool that works with any codebase size\n"
    '- Supports glob patterns like "**/*.js" or "src/**/*.ts"\n'
    "- Returns matching file paths sorted by modification time\n"
    "- Use this tool when you need to find files by name patterns\n"
    "- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead"
)

GLOB_SCHEMA: Dict[str, Any] = {
    "name": "Glob",
    "description": GLOB_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "path": {
                "description": 'The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter "undefined" or "null" - simply omit it for the default behavior. Must be a valid directory path if provided.',
                "type": "string",
            },
            "pattern": {
                "description": "The glob pattern to match files against",
                "type": "string",
            },
        },
        "required": ["pattern"],
        "type": "object",
    },
}

MAX_RESULTS = 100
TRUNCATION_MESSAGE = (
    "(Results are truncated. Consider using a more specific path or pattern.)"
)


def _resolve_path(raw_path: str, *, working_directory: str) -> Path:
    path = Path(os.path.expanduser(raw_path))
    if not path.is_absolute():
        path = Path(working_directory) / path
    return path.resolve()


def _allowed_roots(config: Dict[str, Any], *, working_directory: str) -> List[Path]:
    raw_allowed = config.get("allowed_paths")
    values = (
        raw_allowed
        if isinstance(raw_allowed, list) and raw_allowed
        else [working_directory]
    )
    roots = []
    for item in values:
        if isinstance(item, str) and item.strip():
            roots.append(_resolve_path(item, working_directory=working_directory))
    return roots or [Path(working_directory).resolve()]


def _is_within_allowed(path: Path, roots: List[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _tool_result_block(
    tool_use_id: str,
    content: str,
    *,
    is_error: bool = False,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "cache_control": {"type": "ephemeral"},
    }
    if is_error:
        block["is_error"] = True
    return block


class ClaudeGlobTool(ToolPlugin):
    name = "claude_glob_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        return {
            "config": config,
            "working_directory": working_directory,
            "allowed_roots": _allowed_roots(
                config, working_directory=working_directory
            ),
        }

    def get_tool_interop_contribution(self, state: Dict[str, Any]):
        return claude_tool_interop_contribution()

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [GLOB_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "Glob"

    def _result(
        self,
        *,
        tool_use_id: str,
        message: str,
        success: bool,
        path: str,
    ) -> Dict[str, Any]:
        return {
            "success": success,
            "anthropic_content": [
                _tool_result_block(tool_use_id, message, is_error=not success)
            ],
            "text": message,
            "path": path,
        }

    def _error(self, tool_use_id: str, message: str, *, path: str) -> Dict[str, Any]:
        return self._result(
            tool_use_id=tool_use_id,
            message=message,
            success=False,
            path=path,
        )

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        tool_call: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "Glob":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "Glob input must be an object"}

        pattern = payload.get("pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            return {"success": False, "error": "pattern must be a non-empty string"}

        tool_use_id = "call_Glob"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        working_directory = str(state.get("working_directory") or os.getcwd())
        raw_path = payload.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            try:
                search_root = _resolve_path(raw_path, working_directory=working_directory)
            except Exception as exc:
                return self._error(
                    tool_use_id,
                    f"<tool_use_error>Unable to resolve path: {exc}</tool_use_error>",
                    path=raw_path,
                )
            path_display = str(search_root)
        else:
            search_root = Path(working_directory).resolve()
            path_display = str(search_root)

        allowed_roots = state.get("allowed_roots")
        roots = allowed_roots if isinstance(allowed_roots, list) else []
        if roots and not _is_within_allowed(search_root, roots):
            return self._error(
                tool_use_id,
                f"<tool_use_error>Access denied for path: {search_root}</tool_use_error>",
                path=str(search_root),
            )
        if not search_root.exists():
            return self._error(
                tool_use_id,
                (
                    f"<tool_use_error>Directory does not exist: {search_root}. "
                    f"Note: your current working directory is {working_directory}."
                    "</tool_use_error>"
                ),
                path=str(search_root),
            )
        if not search_root.is_dir():
            return self._error(
                tool_use_id,
                f"<tool_use_error>Path is not a directory: {search_root}</tool_use_error>",
                path=str(search_root),
            )

        outcome = glob_search(
            pattern,
            search_directories=[str(search_root)],
            display_root=working_directory,
            case_sensitive=False,
            respect_git_ignore=False,
            respect_vendor_ignore=False,
            sort_mode="alphabetical",
            max_results=MAX_RESULTS,
        )
        if not outcome.get("ok"):
            return self._error(
                tool_use_id,
                f"<tool_use_error>{outcome.get('error')}</tool_use_error>",
                path=path_display,
            )

        matches = outcome.get("paths") or []
        if not isinstance(matches, list):
            matches = []
        results: List[str] = []
        if isinstance(raw_path, str) and raw_path.strip():
            results = [str(Path(item)) for item in matches if isinstance(item, str)]
        else:
            for item in matches:
                if not isinstance(item, str):
                    continue
                candidate = Path(item)
                try:
                    results.append(candidate.relative_to(search_root).as_posix())
                except ValueError:
                    results.append(str(candidate))

        if not results:
            return self._result(
                tool_use_id=tool_use_id,
                message="No files found",
                success=True,
                path=path_display,
            )

        body = "\n".join(results)
        count = outcome.get("count")
        if isinstance(count, int) and count >= MAX_RESULTS:
            body = f"{body}\n{TRUNCATION_MESSAGE}"
        return self._result(
            tool_use_id=tool_use_id,
            message=body,
            success=True,
            path=path_display,
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        content = result.get("anthropic_content")
        if isinstance(content, list) and all(
            isinstance(item, dict) for item in content
        ):
            return make_provider_native_tool_result(
                format=FORMAT_ANTHROPIC_MESSAGES,
                content=content,
                text=str(result.get("text") or ""),
            )
        if result.get("success"):
            return str(result.get("text") or result.get("result") or "")
        return f"Error: {result.get('error')}"

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        path = str(result.get("path") or "")
        return {
            "type": "text",
            "content": text,
            "single_line": f"Glob: {Path(path).name if path else 'search'}",
        }


__all__ = ["ClaudeGlobTool", "GLOB_SCHEMA"]