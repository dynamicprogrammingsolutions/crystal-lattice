"""Context recording plugin for testing application-level context enrichment.

This plugin records all context it receives during execute_action calls,
allowing tests to verify that context flows correctly through the application
layer to feature plugins.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class ContextRecordingPlugin:
    """Feature plugin that records context for testing purposes.

    This plugin is used by application-level tests to verify that:
    1. Core-level context (core, config) is present
    2. Application-level context (app, base_config) is present
    3. Custom context from higher layers flows through correctly
    """

    name = "context_recording"
    version = "1.0.0"
    priority = 100

    # Class-level storage for captured contexts
    _captured_contexts: List[Dict[str, Any]] = []

    @classmethod
    def get_captured_contexts(cls) -> List[Dict[str, Any]]:
        """Return all captured contexts and clear the storage."""
        contexts = list(cls._captured_contexts)
        cls._captured_contexts = []
        return contexts

    @classmethod
    def clear_captured_contexts(cls) -> None:
        """Clear all captured contexts."""
        cls._captured_contexts = []

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        return []

    def required_tags(self) -> List[str]:
        return []

    def forbidden_tags(self) -> List[str]:
        return []

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        request_key = "context_recording_request_marker"
        request_value = state.get("config", {}).get(request_key) if isinstance(state.get("config"), dict) else None
        if isinstance(request_value, str) and request_value:
            request = state.get("request") if isinstance(state.get("request"), dict) else {}
            return native_messages, {
                **state,
                "request": {
                    **request,
                    request_key: request_value,
                },
            }
        return native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "record_context",
                "label": "Record context",
                "description": "Record the context for testing.",
                "inputs": {},
            },
            {
                "id": "record_initialized_context",
                "label": "Record initialized context",
                "description": "Record context after explicit request initialization.",
                "inputs": {},
            },
            {
                "id": "record_context_with_trigger",
                "label": "Record context with trigger",
                "description": "Record context when triggered by lifecycle.",
                "inputs": {},
                "trigger": "request_complete",
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
        effective_state = state
        if action_id == "record_initialized_context" and isinstance(context, dict):
            core = context.get("core")
            request_runtime = context.get("request_runtime")
            request_context = context.get("request_context")
            if (
                core is not None
                and isinstance(request_runtime, dict)
                and isinstance(request_context, dict)
            ):
                _, effective_state = core.initialize_action_request(
                    native_messages,
                    state,
                    request_runtime,
                    request_context,
                )

        # Record the context
        if isinstance(context, dict):
            ContextRecordingPlugin._captured_contexts.append({
                **context,
                "_action_id": action_id,
                "_request": effective_state.get("request"),
            })

        return {
            "native_messages": native_messages,
            "session_metadata": {"context_recorded": True, "action_id": action_id},
        }

    def get_template(self, config: Dict[str, Any]) -> str:
        return ""

    def get_completions(
        self,
        config: Dict[str, Any],
        text: str,
    ) -> List[Dict[str, Any]]:
        return []


__all__ = ["ContextRecordingPlugin"]
