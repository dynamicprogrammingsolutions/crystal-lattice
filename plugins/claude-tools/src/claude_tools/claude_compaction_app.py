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

"""Application plugin that runs Claude compaction in the background.

The plugin exposes ``compact_conversation`` and ``cancel_claude_compaction``.
Starting an operation validates the request, reserves the session's
application operation, and launches a :class:`ClaudeCompactionProcess` that
drives the synchronous ``claude_compaction`` feature action on a worker
thread while publishing progress through session notifications. The action
returns promptly with an accepted operation envelope, mirroring the OpenAI
Responses native-compaction application plugin.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid

from agent_app.managed_processes import get_managed_process_registry
from agent_app.operations import (
    ApplicationOperationBusyError,
    get_application_operation_service,
    session_operation_exclusivity_key,
)

from .claude_compaction_feature import (
    FEATURE_TAG,
    _MIN_COMPACTABLE_MESSAGE_COUNT,
    _resolve_compaction_indices,
)
from .claude_compaction_process import (
    APP_PLUGIN_ID,
    ClaudeCompactionProcess,
    FEATURE_PLUGIN_ID,
    SYNC_ACTION_ID,
)

OPERATION_PREFIX = "claude_compaction"


class ClaudeCompactionAppPlugin:
    name = APP_PLUGIN_ID
    version = "0.1.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config
        tags = context.get("tags") if isinstance(context, dict) else None
        if not isinstance(tags, list) or FEATURE_TAG not in tags:
            return []
        return [
            {
                "ui_type": "session_action",
                "id": "compact_conversation",
                "label": "Compact conversation",
                "icon": "archive",
                "order": 46,
                "action_id": "compact_conversation",
                "action_owner": "application",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "start": "$dialog.start",
                    "end": "$dialog.end",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact conversation",
                    "message": (
                        "Python-style range (start:end). The selected messages "
                        "will be compacted into a Claude-style compact summary "
                        "in the background."
                    ),
                    "inputs": [
                        {
                            "name": "start",
                            "type": "integer",
                            "label": "Start index",
                            "required": False,
                            "placeholder": "e.g. 0 or -10 (leave blank for start)",
                        },
                        {
                            "name": "end",
                            "type": "integer",
                            "label": "End index",
                            "required": False,
                            "placeholder": "e.g. 10 or -1 (leave blank for end)",
                        },
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": (
                                "Optional extra instructions for the compaction "
                                "summary"
                            ),
                        },
                    ],
                },
            },
            {
                "ui_type": "message_action",
                "id": "compact_up_to_here",
                "label": "Compact messages up to here",
                "icon": "archive",
                "order": 25,
                "action_id": "compact_conversation",
                "action_owner": "application",
                "fixed_params": {"start": 0, "end_inclusive": True},
                "param_map": {
                    "session_id": "$session.session_id",
                    "end": "$message.index",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact messages up to here",
                    "message": (
                        "The messages up to here will be compacted into a "
                        "Claude-style compact summary in the background."
                    ),
                    "inputs": [
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": (
                                "Optional extra instructions for the compaction "
                                "summary"
                            ),
                        }
                    ],
                },
            },
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": SYNC_ACTION_ID,
                "label": "Compact conversation",
                "description": (
                    "Compact a selected conversation range into a Claude-style "
                    "summary in the background."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                    "end_inclusive": {"type": "boolean", "required": False},
                    "instructions": {"type": "string", "required": False},
                },
            },
            {
                "id": "cancel_claude_compaction",
                "label": "Cancel Claude compaction",
                "description": (
                    "Request cancellation of a running background Claude " "compaction."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "operation_id": {"type": "string", "required": True},
                },
            },
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = state
        if action_id == "cancel_claude_compaction":
            return self._cancel(app, params)
        if action_id != SYNC_ACTION_ID:
            raise KeyError(action_id)
        return self._start(app, params, context)

    def _start(
        self,
        app: Any,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        if app.get_selected_session_snapshot(session_id) is not None:
            raise RuntimeError(f"Session {session_id!r} is viewing a readonly snapshot")

        start_raw = params.get("start")
        end_raw = params.get("end")
        end_inclusive = params.get("end_inclusive", False)
        instructions = params.get("instructions")
        start_int = (
            start_raw
            if isinstance(start_raw, int) and not isinstance(start_raw, bool)
            else None
        )
        end_int = (
            end_raw
            if isinstance(end_raw, int) and not isinstance(end_raw, bool)
            else None
        )
        instructions_text = (
            instructions.strip() if isinstance(instructions, str) else None
        )

        with app.acquire_session_lock(session_id):
            loaded = app.load_session(session_id)
            if loaded is None:
                raise KeyError(f"Session {session_id!r} not found")
            core, base_config, session = loaded
            baseline_file_state = app.get_session_file_state(session_id)

        if len(session.messages) == 0:
            raise ValueError("Error: No messages to compact")
        if len(session.messages) < _MIN_COMPACTABLE_MESSAGE_COUNT:
            raise ValueError("Not enough messages to compact.")

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        effective_config = app.resolve_effective_config(base_config, session, overrides)
        has_feature_action = any(
            isinstance(action, dict)
            and action.get("plugin") == FEATURE_PLUGIN_ID
            and action.get("id") == SYNC_ACTION_ID
            for action in core.get_session_actions(effective_config)
        )
        if not has_feature_action:
            raise RuntimeError("Claude compaction is not available for this session")

        # Resolve the range synchronously so invalid selections fail the
        # action call immediately instead of producing a failed background
        # operation.
        _resolve_compaction_indices(
            session,
            start=start_int,
            end=end_int,
            end_inclusive=bool(end_inclusive),
        )

        action_params: Dict[str, Any] = {}
        if start_int is not None:
            action_params["start"] = start_int
        if end_int is not None:
            action_params["end"] = end_int
        if end_inclusive:
            action_params["end_inclusive"] = True
        if instructions_text is not None:
            action_params["instructions"] = instructions_text

        operation_id = f"{OPERATION_PREFIX}:{uuid.uuid4().hex}"
        operations = get_application_operation_service(app.get_runtime_store())
        try:
            operation = operations.reserve(
                operation_id=operation_id,
                owner_id=APP_PLUGIN_ID,
                session_id=session_id,
                exclusivity_keys=(session_operation_exclusivity_key(session_id),),
            )
        except ApplicationOperationBusyError as exc:
            return {
                "status": "error",
                "error_type": "session_busy",
                "message": "The session is busy with another operation.",
                "operation": exc.current.to_dict(),
            }

        registry = get_managed_process_registry(app.get_runtime_store())
        process = ClaudeCompactionProcess(
            app=app,
            registry=registry,
            process_id=operation_id,
            operation=operation,
            session_id=session_id,
            core=core,
            base_config=base_config,
            session=session,
            effective_config=effective_config,
            baseline_file_state=baseline_file_state,
            action_params=action_params,
            action_context=context,
        )
        try:
            registry.start(operation_id, process)
        except Exception:
            operation.release()
            raise

        return {
            "status": "ok",
            "operation_status": "accepted",
            "message": "Claude compaction started.",
            "operation_id": operation_id,
            "notification_id": process.notification_id,
        }

    def _cancel(self, app: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        session_id = params["session_id"]
        operation_id = params["operation_id"]
        operations = get_application_operation_service(app.get_runtime_store())
        current = operations.get(operation_id)
        if (
            current is None
            or current.owner_id != APP_PLUGIN_ID
            or current.session_id != session_id
        ):
            return {
                "status": "error",
                "error_type": "operation_not_found",
                "message": "The compaction operation is no longer active.",
            }
        registry = get_managed_process_registry(app.get_runtime_store())
        process = registry.get(operation_id)
        if not isinstance(process, ClaudeCompactionProcess):
            return {
                "status": "error",
                "error_type": "operation_not_found",
                "message": "The compaction process is no longer active.",
            }
        if not process.matches(
            session_id=session_id,
            operation_id=operation_id,
        ):
            return {
                "status": "error",
                "error_type": "stale_operation",
                "message": "The compaction action no longer matches this session.",
            }
        if not process.request_cancel():
            return {
                "status": "error",
                "error_type": "operation_not_cancellable",
                "message": "The compaction operation can no longer be cancelled.",
            }
        return {
            "status": "ok",
            "operation_status": "cancellation_requested",
            "message": "Compaction cancellation requested.",
        }


__all__ = ["ClaudeCompactionAppPlugin"]
