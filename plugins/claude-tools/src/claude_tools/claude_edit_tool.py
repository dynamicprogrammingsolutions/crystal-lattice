# Licensing note:
# This file may contain both original code authored for this repository and
# material derived from or adapted from Claude Code or other
# Anthropic-authored materials.
#
# Original code in this file authored for this repository is licensed under
# the Apache License, Version 2.0.
#
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
#
# Anthropic-derived material in this file is not licensed by us under
# Apache-2.0, and are instead subject to Anthropic's terms:
#
# © Anthropic PBC. All rights reserved. Use is subject to Anthropic's
# Commercial Terms of Service:
# https://www.anthropic.com/legal/commercial-terms

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from tool_compat_shared import replace_literal_text

from .activity import has_read_path, record_read_path
from .interop import claude_tool_interop_contribution


EDIT_DESCRIPTION = (
    "Performs exact string replacements in files.\n\n"
    "Usage:\n"
    "- You must use your `Read` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file.\n"
    "- When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: line number + tab. Everything after that is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.\n"
    "- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.\n"
    "- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.\n"
    "- The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`.\n"
    "- Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance."
)

EDIT_SCHEMA: Dict[str, Any] = {
    "name": "Edit",
    "description": EDIT_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "file_path": {
                "description": "The absolute path to the file to modify",
                "type": "string",
            },
            "new_string": {
                "description": "The text to replace it with (must be different from old_string)",
                "type": "string",
            },
            "old_string": {
                "description": "The text to replace",
                "type": "string",
            },
            "replace_all": {
                "default": False,
                "description": "Replace all occurrences of old_string (default false)",
                "type": "boolean",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
        "type": "object",
    },
}


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
    cache_control: bool = True,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
    }
    if is_error:
        block["is_error"] = True
    if cache_control:
        block["cache_control"] = {"type": "ephemeral"}
    return block


class ClaudeEditTool(ToolPlugin):
    name = "claude_edit_tool"
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
        return [EDIT_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "Edit"

    def _result(
        self,
        *,
        tool_use_id: str,
        message: str,
        success: bool,
        path: str,
        cache_control: bool = True,
    ) -> Dict[str, Any]:
        return {
            "success": success,
            "anthropic_content": [
                _tool_result_block(
                    tool_use_id,
                    message,
                    is_error=not success,
                    cache_control=cache_control,
                )
            ],
            "text": message,
            "path": path,
        }

    def _error(
        self,
        tool_use_id: str,
        message: str,
        *,
        path: str,
        cache_control: bool = True,
    ) -> Dict[str, Any]:
        return self._result(
            tool_use_id=tool_use_id,
            message=message,
            success=False,
            path=path,
            cache_control=cache_control,
        )

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        tool_call: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "Edit":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "Edit input must be an object"}

        raw_path = payload.get("file_path")
        old_string = payload.get("old_string")
        new_string = payload.get("new_string")
        replace_all = bool(payload.get("replace_all", False))
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "file_path must be a non-empty string"}
        if not isinstance(old_string, str) or not isinstance(new_string, str):
            return {
                "success": False,
                "error": "old_string and new_string must be strings",
            }

        tool_use_id = "call_Edit"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        working_directory = str(state.get("working_directory") or os.getcwd())
        try:
            path = _resolve_path(raw_path, working_directory=working_directory)
        except Exception as exc:
            return self._error(
                tool_use_id,
                f"<tool_use_error>Unable to resolve path: {exc}</tool_use_error>",
                path=raw_path,
            )

        allowed_roots = state.get("allowed_roots")
        roots = allowed_roots if isinstance(allowed_roots, list) else []
        if roots and not _is_within_allowed(path, roots):
            return self._error(
                tool_use_id,
                f"<tool_use_error>Access denied for path: {raw_path}</tool_use_error>",
                path=str(path),
            )

        if path.exists() and path.is_dir():
            return self._error(
                tool_use_id,
                f"<tool_use_error>Path is a directory, not a file: {path}</tool_use_error>",
                path=str(path),
            )

        if path.exists() and not has_read_path(path, context=context, state=state):
            return self._error(
                tool_use_id,
                "<tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>",
                path=str(path),
            )

        outcome = replace_literal_text(
            path,
            old_string,
            new_string,
            replace_all=replace_all,
            allow_missing_with_empty_old=False,
        )
        if not outcome.get("ok"):
            code = outcome.get("code")
            if code == "no_occurrences":
                return self._error(
                    tool_use_id,
                    f"<tool_use_error>String to replace not found in file.\nString: {old_string}</tool_use_error>",
                    path=str(path),
                )
            if code == "multiple_occurrences":
                count = int(outcome.get("occurrences") or 0)
                return self._error(
                    tool_use_id,
                    (
                        "<tool_use_error>"
                        f"Found {count} matches of the string to replace, but replace_all is false. "
                        "To replace all occurrences, set replace_all to true. "
                        "To replace only one occurrence, please provide more context to uniquely identify the instance.\n"
                        f"String: {old_string}"
                        "</tool_use_error>"
                    ),
                    path=str(path),
                )
            if code == "not_found":
                return self._error(
                    tool_use_id,
                    f"<tool_use_error>File not found: {path}</tool_use_error>",
                    path=str(path),
                )
            if code == "no_change":
                return self._error(
                    tool_use_id,
                    f"<tool_use_error>{outcome.get('error')}</tool_use_error>",
                    path=str(path),
                )
            if code == "already_exists":
                return self._error(
                    tool_use_id,
                    f"<tool_use_error>{outcome.get('error')}</tool_use_error>",
                    path=str(path),
                )
            return self._error(
                tool_use_id,
                f"<tool_use_error>{outcome.get('error')}</tool_use_error>",
                path=str(path),
            )

        record_read_path(path, context=context, state=state)
        if replace_all:
            message = (
                f"The file {path} has been updated. All occurrences were successfully replaced."
            )
        else:
            message = f"The file {path} has been updated successfully."
        return self._result(
            tool_use_id=tool_use_id,
            message=message,
            success=True,
            path=str(path),
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
            "single_line": f"Edit: {Path(path).name if path else 'file'}",
        }


__all__ = ["ClaudeEditTool", "EDIT_SCHEMA"]