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
from tool_compat_shared import write_text_file

from .activity import has_read_path, record_read_path
from .interop import claude_tool_interop_contribution


WRITE_DESCRIPTION = (
    "Writes a file to the local filesystem.\n\n"
    "Usage:\n"
    "- This tool will overwrite the existing file if there is one at the provided path.\n"
    "- If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail if you did not read the file first.\n"
    "- Prefer the Edit tool for modifying existing files — it only sends the diff. Only use this tool to create new files or for complete rewrites.\n"
    "- NEVER create documentation files (*.md) or README files unless explicitly requested by the User.\n"
    "- Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked."
)

WRITE_SCHEMA: Dict[str, Any] = {
    "name": "Write",
    "description": WRITE_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "content": {
                "description": "The content to write to the file",
                "type": "string",
            },
            "file_path": {
                "description": "The absolute path to the file to write (must be absolute, not relative)",
                "type": "string",
            },
        },
        "required": ["file_path", "content"],
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


class ClaudeWriteTool(ToolPlugin):
    name = "claude_write_tool"
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
        return [WRITE_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "Write"

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
            "anthropic_content": [_tool_result_block(tool_use_id, message, is_error=not success)],
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
        context: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "Write":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "Write input must be an object"}

        raw_path = payload.get("file_path")
        content = payload.get("content")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return {"success": False, "error": "file_path must be a non-empty string"}
        if not isinstance(content, str):
            return {"success": False, "error": "content must be a string"}

        tool_use_id = "call_Write"
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

        outcome = write_text_file(path, content)
        if not outcome.get("ok"):
            return self._error(
                tool_use_id,
                f"<tool_use_error>{outcome.get('error')}</tool_use_error>",
                path=str(path),
            )

        record_read_path(path, context=context, state=state)
        if outcome.get("created"):
            message = f"File created successfully at: {path}"
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
            "single_line": f"Write: {Path(path).name if path else 'file'}",
        }


__all__ = ["ClaudeWriteTool", "WRITE_SCHEMA"]