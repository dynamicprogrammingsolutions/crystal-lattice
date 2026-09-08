from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid

from agent_app.managed_processes import get_managed_process_registry
from agent_app.operations import (
    ApplicationOperationBusyError,
    get_application_operation_service,
    session_operation_exclusivity_key,
)

from .openai_responses_native_compaction_process import (
    EXTENSION_ID,
    OpenAIResponsesNativeCompactionProcess,
    PLUGIN_ID,
    SYNC_ACTION_ID,
)


class OpenAIResponsesNativeCompactionAppPlugin:
    name = PLUGIN_ID
    version = "0.1.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "compact_native_history",
                "label": "Compact native history",
                "description": (
                    "Start OpenAI Responses native compaction in the background."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "end_index": {"type": "integer", "required": False},
                    "message_index": {"type": "integer", "required": False},
                },
            },
            {
                "id": "cancel_native_compaction",
                "label": "Cancel native compaction",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "operation_id": {"type": "string", "required": True},
                },
            },
        ]

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config
        tags = context.get("tags") if isinstance(context, dict) else None
        if not isinstance(tags, list) or (
            "ext:openai_responses_native_compaction" not in tags
        ):
            return []
        return [
            {
                "ui_type": "session_action",
                "id": "compact_native_history",
                "label": "Compact native history",
                "icon": "archive",
                "order": 46,
                "action_id": "compact_native_history",
                "action_owner": "application",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "end_index": "$dialog.end_index",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact native history",
                    "message": (
                        "Compact provider-native history in the background using "
                        "the OpenAI Responses compact API."
                    ),
                    "inputs": [
                        {
                            "name": "end_index",
                            "type": "number",
                            "label": "Compact visible messages [:end]",
                            "required": False,
                            "placeholder": "Leave empty to compact the full history",
                        }
                    ],
                },
            },
            {
                "ui_type": "message_action",
                "id": "compact_native_history_through_message",
                "label": "Compact native history up to here",
                "icon": "archive",
                "order": 25,
                "action_id": "compact_native_history",
                "action_owner": "application",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "message_index": "$message.index",
                },
                "dialog": {
                    "kind": "confirm",
                    "title": "Compact native history up to here",
                    "message": (
                        "Compact provider-native history through this message "
                        "in the background?"
                    ),
                },
            },
        ]

    def get_commands(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = state
        if action_id == "cancel_native_compaction":
            return self._cancel(app, params)
        if action_id != "compact_native_history":
            raise KeyError(action_id)
        return self._start(app, params, context)

    def _start(
        self,
        app: Any,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        session_id = params["session_id"]
        if app.get_selected_session_snapshot(session_id) is not None:
            raise RuntimeError(f"Session {session_id!r} is viewing a readonly snapshot")

        loaded = app.load_session(session_id)
        if loaded is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, base_config, session = loaded
        end_index = params.get("end_index")
        message_index = params.get("message_index")
        if end_index is not None and message_index is not None:
            raise ValueError("end_index and message_index cannot both be provided")
        if message_index is not None:
            if (
                not isinstance(message_index, int)
                or isinstance(message_index, bool)
                or message_index < 0
                or message_index >= len(session.messages)
            ):
                raise ValueError(
                    "message_index must identify a visible session message"
                )
            end_index = message_index + 1
        if end_index is not None:
            if (
                not isinstance(end_index, int)
                or isinstance(end_index, bool)
                or end_index <= 0
            ):
                raise ValueError("end_index must be a positive integer")
            if end_index > len(session.messages):
                raise ValueError("end_index cannot exceed the visible message count")

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        effective_config = app.resolve_effective_config(
            base_config,
            session,
            overrides,
        )
        has_sync_adapter = any(
            action.get("plugin") == EXTENSION_ID and action.get("id") == SYNC_ACTION_ID
            for action in core.get_session_actions(effective_config)
            if isinstance(action, dict)
        )
        if not has_sync_adapter:
            raise RuntimeError(
                "OpenAI Responses native compaction is not enabled for this session"
            )

        operation_id = f"openai_responses_native_compaction:{uuid.uuid4().hex}"
        operations = get_application_operation_service(app.get_runtime_store())
        try:
            operation = operations.reserve(
                operation_id=operation_id,
                owner_id=PLUGIN_ID,
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
        process = OpenAIResponsesNativeCompactionProcess(
            app=app,
            registry=registry,
            process_id=operation_id,
            operation=operation,
            session_id=session_id,
            end_index=end_index,
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
            "message": "Native compaction started.",
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
            or current.owner_id != PLUGIN_ID
            or current.session_id != session_id
        ):
            return {
                "status": "error",
                "error_type": "operation_not_found",
                "message": "The compaction operation is no longer active.",
            }
        registry = get_managed_process_registry(app.get_runtime_store())
        process = registry.get(operation_id)
        if not isinstance(process, OpenAIResponsesNativeCompactionProcess):
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


__all__ = ["OpenAIResponsesNativeCompactionAppPlugin"]
