from __future__ import annotations

from typing import Any, Dict, List, Optional


class DummyLifecycleExtension:
    name = "dummy_lifecycle_extension"
    version = "1.0.0"

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ):
        _ = native_chunk
        return partial_messages, final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {"id": "on_session_create", "label": "On create", "inputs": {}, "trigger": "session_create"},
            {
                "id": "on_session_save_prepare",
                "label": "On save",
                "inputs": {},
                "trigger": "session_save_prepare",
            },
            {
                "id": "on_request_prepare",
                "label": "On request prepare",
                "inputs": {},
                "trigger": "request_prepare",
            },
            {
                "id": "on_request_complete",
                "label": "On request complete",
                "inputs": {},
                "trigger": "request_complete",
            },
            {
                "id": "on_request_error",
                "label": "On request error",
                "inputs": {},
                "trigger": "request_error",
            },
            {"id": "on_session_fork", "label": "On fork", "inputs": {}, "trigger": "session_fork"},
            {
                "id": "on_agent_switch_prepare",
                "label": "On switch prepare",
                "inputs": {},
                "trigger": "agent_switch_prepare",
            },
            {
                "id": "on_agent_switch_complete",
                "label": "On switch complete",
                "inputs": {},
                "trigger": "agent_switch_complete",
            },
        ]

    def execute_action(
        self,
        action_id: str,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = params, state
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides = overrides_val if isinstance(overrides_val, dict) else {}
        lifecycle_log = metadata.get("extension_lifecycle_log")
        if not isinstance(lifecycle_log, list):
            lifecycle_log = []

        lifecycle = (context or {}).get("lifecycle") if isinstance(context, dict) else None
        if isinstance(lifecycle, str):
            lifecycle_log = [*lifecycle_log, lifecycle]

        patch: Dict[str, Any] = {"extension_lifecycle_log": lifecycle_log}

        if action_id == "on_session_create":
            patch["overrides"] = {**overrides, "created_by_extension": True}
        elif action_id == "on_session_save_prepare":
            patch["saved_by_extension"] = True
        elif action_id == "on_request_prepare":
            patch["overrides"] = {**overrides, "prepared_by_extension": True}
        elif action_id == "on_request_complete":
            patch["request_completed_by_extension"] = True
        elif action_id == "on_request_error":
            error = (context or {}).get("error") if isinstance(context, dict) else None
            if isinstance(error, dict):
                patch["request_error_message"] = error.get("message")
        elif action_id == "on_session_fork":
            original = (context or {}).get("original_session") if isinstance(context, dict) else None
            if isinstance(original, dict):
                patch["fork_source_session_id"] = original.get("session_id")
        elif action_id == "on_agent_switch_prepare":
            patch["agent_switch_prepare_to"] = (context or {}).get("next_agent_id")
        elif action_id == "on_agent_switch_complete":
            patch["agent_switch_complete_to"] = (context or {}).get("next_agent_id")
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unknown action_id {action_id!r}")

        return {
            "native_messages": list(native_messages),
            "session_metadata": patch,
        }
