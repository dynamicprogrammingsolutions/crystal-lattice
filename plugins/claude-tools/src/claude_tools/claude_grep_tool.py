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
from tool_compat_shared.search_engine import grep_search

from .interop import claude_tool_interop_contribution


GREP_DESCRIPTION = (
    "A powerful search tool built on ripgrep\n\n"
    "  Usage:\n"
    "  - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command. The Grep tool has been optimized for correct permissions and access.\n"
    '  - Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+")\n'
    '  - Filter files with glob parameter (e.g., "*.js", "**/*.tsx") or type parameter (e.g., "js", "py", "rust")\n'
    '  - Output modes: "content" shows matching lines, "files_with_matches" shows only file paths (default), "count" shows match counts\n'
    "  - Use Agent tool for open-ended searches requiring multiple rounds\n"
    "  - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping (use `interface\\{\\}` to find `interface{}` in Go code)\n"
    '  - Multiline matching: By default patterns match within single lines only. For cross-line patterns like `struct \\{[\\s\\S]*?field`, use `multiline: true`\n'
)

GREP_SCHEMA: Dict[str, Any] = {
    "name": "Grep",
    "description": GREP_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "-A": {
                "description": 'Number of lines to show after each match (rg -A). Requires output_mode: "content", ignored otherwise.',
                "type": "number",
            },
            "-B": {
                "description": 'Number of lines to show before each match (rg -B). Requires output_mode: "content", ignored otherwise.',
                "type": "number",
            },
            "-C": {
                "description": "Alias for context.",
                "type": "number",
            },
            "-i": {
                "description": "Case insensitive search (rg -i)",
                "type": "boolean",
            },
            "-n": {
                "description": 'Show line numbers in output (rg -n). Requires output_mode: "content", ignored otherwise. Defaults to true.',
                "type": "boolean",
            },
            "context": {
                "description": 'Number of lines to show before and after each match (rg -C). Requires output_mode: "content", ignored otherwise.',
                "type": "number",
            },
            "glob": {
                "description": 'Glob pattern to filter files (e.g. "*.js", "*.{ts,tsx}") - maps to rg --glob',
                "type": "string",
            },
            "head_limit": {
                "description": 'Limit output to first N lines/entries, equivalent to "| head -N". Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). Defaults to 250 when unspecified. Pass 0 for unlimited (use sparingly — large result sets waste context).',
                "type": "number",
            },
            "multiline": {
                "description": "Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false.",
                "type": "boolean",
            },
            "offset": {
                "description": 'Skip first N lines/entries before applying head_limit, equivalent to "| tail -n +N | head -N". Works across all output modes. Defaults to 0.',
                "type": "number",
            },
            "output_mode": {
                "description": 'Output mode: "content" shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit), "files_with_matches" shows file paths (supports head_limit), "count" shows match counts (supports head_limit). Defaults to "files_with_matches".',
                "enum": ["content", "files_with_matches", "count"],
                "type": "string",
            },
            "path": {
                "description": "File or directory to search in (rg PATH). Defaults to current working directory.",
                "type": "string",
            },
            "pattern": {
                "description": "The regular expression pattern to search for in file contents",
                "type": "string",
            },
            "type": {
                "description": "File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types.",
                "type": "string",
            },
        },
        "required": ["pattern"],
        "type": "object",
    },
}

DEFAULT_HEAD_LIMIT = 250


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


def _sort_paths_by_mtime_desc(paths: List[str]) -> List[str]:
    return sorted(
        paths,
        key=lambda value: (-Path(value).stat().st_mtime, value),
    )


def _relative_or_absolute(path_value: str, *, provided_path: bool, working_directory: str) -> str:
    if provided_path:
        return path_value
    path = Path(path_value)
    root = Path(working_directory).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _head_limit_value(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    return DEFAULT_HEAD_LIMIT


def _offset_value(value: Any) -> int:
    if isinstance(value, (int, float)):
        return max(0, int(value))
    return 0


def _apply_offset_and_limit(items: List[Any], *, offset: int, head_limit: int) -> List[Any]:
    visible = items[offset:]
    if head_limit == 0:
        return visible
    return visible[: max(0, head_limit)]


class ClaudeGrepTool(ToolPlugin):
    name = "claude_grep_tool"
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
        return [GREP_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "Grep"

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
        if tool_name != "Grep":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "Grep input must be an object"}

        pattern = payload.get("pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            return {"success": False, "error": "pattern must be a non-empty string"}

        tool_use_id = "call_Grep"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        working_directory = str(state.get("working_directory") or os.getcwd())
        raw_path = payload.get("path")
        provided_path = isinstance(raw_path, str) and bool(raw_path.strip())
        if provided_path:
            try:
                search_path = _resolve_path(str(raw_path), working_directory=working_directory)
            except Exception as exc:
                return self._error(
                    tool_use_id,
                    f"<tool_use_error>Unable to resolve path: {exc}</tool_use_error>",
                    path=str(raw_path),
                )
            path_display = str(search_path)
        else:
            search_path = Path(working_directory).resolve()
            path_display = str(search_path)

        allowed_roots = state.get("allowed_roots")
        roots = allowed_roots if isinstance(allowed_roots, list) else []
        if roots and not _is_within_allowed(search_path, roots):
            return self._error(
                tool_use_id,
                f"<tool_use_error>Access denied for path: {search_path}</tool_use_error>",
                path=str(search_path),
            )
        if not search_path.exists():
            return self._error(
                tool_use_id,
                (
                    f"<tool_use_error>Path does not exist: {search_path}. "
                    f"Note: your current working directory is {working_directory}."
                    "</tool_use_error>"
                ),
                path=str(search_path),
            )

        output_mode = payload.get("output_mode")
        mode = output_mode if isinstance(output_mode, str) and output_mode else "files_with_matches"
        if mode not in {"files_with_matches", "content", "count"}:
            return self._error(
                tool_use_id,
                f"<tool_use_error>Invalid output_mode: {mode}</tool_use_error>",
                path=str(search_path),
            )

        context_value = payload.get("context")
        context_before = payload.get("-B")
        context_after = payload.get("-A")
        context_both = payload.get("-C")
        if not isinstance(context_before, (int, float)):
            context_before = None
        if not isinstance(context_after, (int, float)):
            context_after = None
        if isinstance(context_both, (int, float)):
            if context_before is None:
                context_before = int(context_both)
            if context_after is None:
                context_after = int(context_both)
        elif isinstance(context_value, (int, float)):
            if context_before is None:
                context_before = int(context_value)
            if context_after is None:
                context_after = int(context_value)

        show_line_numbers = bool(payload.get("-n", True))
        if mode != "content":
            show_line_numbers = False
            context_before = None
            context_after = None

        outcome = grep_search(
            pattern,
            search_path=str(search_path),
            display_root=working_directory,
            glob_pattern=payload.get("glob") if isinstance(payload.get("glob"), str) else None,
            names_only=mode == "files_with_matches",
            count_mode=mode == "count",
            ignore_case=bool(payload.get("-i", False)),
            context_before=int(context_before) if isinstance(context_before, int) else None,
            context_after=int(context_after) if isinstance(context_after, int) else None,
            show_line_numbers=show_line_numbers,
            type_filter=payload.get("type") if isinstance(payload.get("type"), str) else None,
            multiline=bool(payload.get("multiline", False)),
            respect_git_ignore=True,
        )
        if not outcome.get("ok"):
            return self._error(
                tool_use_id,
                f"<tool_use_error>{outcome.get('error')}</tool_use_error>",
                path=str(search_path),
            )

        results = outcome.get("results") or []
        if not isinstance(results, list) or not results:
            return self._result(
                tool_use_id=tool_use_id,
                message="No files found",
                success=True,
                path=path_display,
            )

        head_limit = max(0, _head_limit_value(payload.get("head_limit")))
        offset = _offset_value(payload.get("offset"))

        if mode == "files_with_matches":
            paths = [
                str(item.get("path"))
                for item in results
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            ]
            visible_paths = _apply_offset_and_limit(
                _sort_paths_by_mtime_desc(paths),
                offset=offset,
                head_limit=head_limit,
            )
            if not visible_paths:
                return self._result(
                    tool_use_id=tool_use_id,
                    message="No files found",
                    success=True,
                    path=path_display,
                )
            rendered = [
                _relative_or_absolute(
                    item,
                    provided_path=provided_path,
                    working_directory=working_directory,
                )
                for item in visible_paths
            ]
            count = len(rendered)
            noun = "file" if count == 1 else "files"
            message = f"Found {count} {noun}\n" + "\n".join(rendered)
            return self._result(
                tool_use_id=tool_use_id,
                message=message,
                success=True,
                path=path_display,
            )

        if mode == "count":
            entries = [
                item
                for item in results
                if isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and isinstance(item.get("count"), int)
            ]
            visible_entries = _apply_offset_and_limit(
                entries,
                offset=offset,
                head_limit=head_limit,
            )
            if not visible_entries:
                return self._result(
                    tool_use_id=tool_use_id,
                    message="No files found",
                    success=True,
                    path=path_display,
                )
            lines = []
            total_count = 0
            for item in visible_entries:
                path_value = _relative_or_absolute(
                    str(item["path"]),
                    provided_path=provided_path,
                    working_directory=working_directory,
                )
                count_value = int(item["count"])
                total_count += count_value
                lines.append(f"{path_value}:{count_value}")
            file_count = len(visible_entries)
            noun = "file" if file_count == 1 else "files"
            message = (
                "\n".join(lines)
                + "\n\n"
                + f"Found {total_count} total occurrences across {file_count} {noun}."
            )
            return self._result(
                tool_use_id=tool_use_id,
                message=message,
                success=True,
                path=path_display,
            )

        lines = []
        sortable_results = [
            item
            for item in results
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        ]
        sortable_results.sort(
            key=lambda item: (
                str(item["path"]),
                int(item.get("line_number") or 0),
                str(item.get("line") or ""),
            )
        )
        for item in sortable_results:
            path_value = _relative_or_absolute(
                str(item["path"]),
                provided_path=provided_path,
                working_directory=working_directory,
            )
            if show_line_numbers and isinstance(item.get("line_number"), int):
                lines.append(f"{path_value}:{int(item['line_number'])}:{str(item.get('line') or '')}")
            else:
                lines.append(f"{path_value}:{str(item.get('line') or '')}")
        visible_lines = _apply_offset_and_limit(
            lines,
            offset=offset,
            head_limit=head_limit,
        )
        if not visible_lines:
            return self._result(
                tool_use_id=tool_use_id,
                message="No files found",
                success=True,
                path=path_display,
            )
        return self._result(
            tool_use_id=tool_use_id,
            message="\n".join(visible_lines),
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
            "single_line": f"Grep: {Path(path).name if path else 'search'}",
        }


__all__ = ["ClaudeGrepTool", "GREP_SCHEMA"]