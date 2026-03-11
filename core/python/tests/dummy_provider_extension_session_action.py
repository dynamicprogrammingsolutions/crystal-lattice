from __future__ import annotations

from typing import Any, Dict, List, Optional


class DummySessionActionExtension:
    name = "dummy_session_action"
    version = "1.0.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "session_action",
                "id": "append_native_marker",
                "label": "Append native marker",
                "icon": "archive",
                "order": 50,
                "action_id": "append_native_marker",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "marker": "$dialog.marker",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Append native marker",
                    "inputs": [
                        {
                            "name": "marker",
                            "type": "string",
                            "label": "Marker",
                            "required": True,
                        }
                    ],
                },
            }
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "append_native_marker",
                "label": "Append native marker",
                "description": "Append a provider-native marker item.",
                "inputs": {
                    "marker": {"type": "string", "required": True},
                },
            }
        ]

    def execute_action(
        self,
        action_id: str,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = session, state
        if action_id != "append_native_marker":
            raise ValueError(f"Unknown action_id {action_id!r}")

        marker = params.get("marker")
        if not isinstance(marker, str) or not marker:
            raise ValueError("marker must be a non-empty string")

        return {
            "native_messages": [
                *native_messages,
                {"role": "assistant", "content": f"MARKER={marker}"},
            ],
            "message": f"Appended marker {marker}",
        }