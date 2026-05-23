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

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from tool_compat_shared.background_processes import ensure_background_process_registry

from .interop import claude_tool_interop_contribution


TASK_STOP_SCHEMA: Dict[str, Any] = {
    "name": "TaskStop",
    "description": (
        "\n- Stops a running background task by its ID\n"
        "- Takes a task_id parameter identifying the task to stop\n"
        "- Returns a success or failure status\n"
        "- Use this tool when you need to terminate a long-running task\n"
    ),
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "task_id": {
                "description": "The ID of the background task to stop",
                "type": "string",
            },
            "shell_id": {
                "description": "Deprecated: use task_id instead",
                "type": "string",
            },
        },
        "additionalProperties": False,
    },
}


def _runtime_state_root_from_context(
    context: Optional[Dict[str, Any]],
    *,
    working_directory: str,
) -> Path:
    if isinstance(context, dict):
        root = context.get("runtime_state_root")
        if isinstance(root, (str, os.PathLike)):
            return Path(root).expanduser().resolve()
    return (Path(working_directory).resolve() / ".crystal" / "runtime").resolve()


def _tool_runtime_from_context(context: Optional[Dict[str, Any]]) -> Any | None:
    if isinstance(context, dict):
        return context.get("tool_runtime") or context.get("runtime_store")
    return None


def _tool_result_block(
    tool_use_id: str,
    content: str,
    *,
    is_error: bool | None = None,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "cache_control": {"type": "ephemeral"},
    }
    if is_error is not None:
        block["is_error"] = is_error
    return block


class ClaudeTaskStopTool(ToolPlugin):
    name = "claude_task_stop_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        working_directory = str(config.get("working_directory") or os.getcwd())
        return {
            "config": config,
            "working_directory": str(Path(working_directory).resolve()),
        }

    def get_tool_interop_contribution(self, state: Dict[str, Any]):
        return claude_tool_interop_contribution()

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [TASK_STOP_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "TaskStop"

    def _result(
        self,
        *,
        tool_use_id: str,
        content: str,
        success: bool,
        include_is_error: bool,
    ) -> Dict[str, Any]:
        block = _tool_result_block(
            tool_use_id,
            content,
            is_error=(False if include_is_error and success else True if include_is_error else None),
        )
        return {
            "success": success,
            "anthropic_content": [block],
            "text": content,
        }

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
        if tool_name != "TaskStop":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "TaskStop input must be an object"}

        tool_use_id = "call_TaskStop"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        allowed = {"task_id", "shell_id"}
        unexpected = [
            key for key in payload.keys() if isinstance(key, str) and key not in allowed
        ]
        if unexpected:
            details = "\n".join(
                f"An unexpected parameter `{key}` was provided" for key in unexpected
            )
            return self._result(
                tool_use_id=tool_use_id,
                content=(
                    "<tool_use_error>InputValidationError: TaskStop failed due to the following issues:\n"
                    f"{details}</tool_use_error>"
                ),
                success=False,
                include_is_error=True,
            )

        task_id = payload.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            shell_id = payload.get("shell_id")
            task_id = shell_id if isinstance(shell_id, str) and shell_id else ""
        if not task_id:
            return self._result(
                tool_use_id=tool_use_id,
                content="<tool_use_error>TaskStop requires task_id</tool_use_error>",
                success=False,
                include_is_error=True,
            )

        working_directory = str(state.get("working_directory") or os.getcwd())
        registry = ensure_background_process_registry(
            runtime_state_root=_runtime_state_root_from_context(
                context,
                working_directory=working_directory,
            ),
            tool_runtime=_tool_runtime_from_context(context),
        )
        try:
            record = registry.get_process(task_id)
        except FileNotFoundError:
            return self._result(
                tool_use_id=tool_use_id,
                content=f"<tool_use_error>No task found with ID: {task_id}</tool_use_error>",
                success=False,
                include_is_error=True,
            )

        if record.status != "running":
            status_text = "completed" if record.status in {"succeeded", "failed"} else record.status
            return self._result(
                tool_use_id=tool_use_id,
                content=(
                    f"<tool_use_error>Task {task_id} is not running "
                    f"(status: {status_text})</tool_use_error>"
                ),
                success=False,
                include_is_error=True,
            )

        registry.cancel_process(task_id, reason="task_stop")
        response = json.dumps(
            {
                "message": f"Successfully stopped task: {task_id} ({record.command})",
                "task_id": task_id,
                "task_type": "local_bash",
                "command": record.command,
            },
            separators=(",", ":"),
        )
        return self._result(
            tool_use_id=tool_use_id,
            content=response,
            success=True,
            include_is_error=False,
        )

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        content = result.get("anthropic_content")
        if isinstance(content, list) and all(isinstance(item, dict) for item in content):
            return make_provider_native_tool_result(
                format=FORMAT_ANTHROPIC_MESSAGES,
                content=content,
                text=str(result.get("text") or ""),
            )
        if result.get("success"):
            return str(result.get("text") or "")
        return f"Error: {result.get('text') or result.get('error') or ''}"

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "type": "text",
            "content": text,
            "single_line": "Task stop",
        }


__all__ = ["ClaudeTaskStopTool", "TASK_STOP_SCHEMA"]