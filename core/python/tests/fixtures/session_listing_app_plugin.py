from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core import Session


class SessionListingFixturePlugin:
    name = "session_listing_fixture"
    version = "1.0.0"

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
        _ = state, config, context
        return [
            {
                "ui_type": "session_list_field",
                "id": "fixture_title",
                "role": "title",
                "data": "metadata.title",
                "template": "{{data}}",
                "order": 0,
            },
            {
                "ui_type": "session_list_field",
                "id": "fixture_subtitle",
                "role": "subtitle",
                "data": "metadata.subtitle",
                "template": "{{data}}",
                "order": 0,
            },
            {
                "ui_type": "session_list_field",
                "id": "fixture_count",
                "role": "meta",
                "data": "message_count",
                "template": "{{data}} messages",
                "order": 0,
            },
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        common_inputs = {
            "session_id": {"type": "string", "required": True},
            "session_summary": {"required": True},
            "session": {"required": True},
        }
        return [
            {
                "id": "contribute_listing_fields",
                "label": "Contribute listing fields",
                "inputs": common_inputs,
                "trigger": "session_list",
            },
            {
                "id": "maybe_fail_listing",
                "label": "Maybe fail listing",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "session_summary": {"required": True},
                },
                "trigger": ["session_list"],
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
        _ = app, state
        summary = params.get("session_summary")
        if not isinstance(summary, dict):
            raise TypeError("session_summary is required")
        metadata = summary.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        if action_id == "maybe_fail_listing":
            if metadata.get("fail_list_action"):
                raise RuntimeError("fixture list action failure")
            return {"session_list_fields": {"after_failure_action": True}}

        if action_id != "contribute_listing_fields":
            raise ValueError(f"Unknown action {action_id!r}")

        session = params.get("session")
        if not isinstance(session, Session):
            raise TypeError("session is required")
        if (context or {}).get("lifecycle") != "session_list":
            raise ValueError("session_list lifecycle context is required")

        fields: Dict[str, Any] = {
            "bucket": metadata.get("bucket", 9),
            "sort_name": metadata.get("sort_name", params["session_id"]),
            "message_count": len(session.messages),
        }
        if metadata.get("contribute_reserved_key"):
            fields["preview"] = "must not replace the preview"

        if metadata.get("only_invalid_order"):
            specs: List[Dict[str, Any]] = [
                {
                    "key": "sort_name",
                    "direction": "sideways",
                    "fallback": "",
                    "priority": 10,
                }
            ]
        else:
            specs = [
                {
                    "key": "bucket",
                    "direction": "asc",
                    "fallback": 9,
                    "priority": 10,
                },
                {
                    "key": "sort_name",
                    "direction": "desc",
                    "fallback": "",
                    "priority": 20,
                },
            ]
        if metadata.get("contribute_invalid_order") and not metadata.get("only_invalid_order"):
            specs.append(
                {
                    "key": "sort_name",
                    "direction": "sideways",
                    "fallback": "",
                    "priority": 30,
                }
            )

        return {
            "session_list_fields": fields,
            "session_list_order": specs,
        }


class SessionListingSecondFixturePlugin:
    name = "session_listing_second_fixture"
    version = "1.0.0"

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
        _ = state, config, context
        return []

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "contribute_second_order",
                "label": "Contribute second order",
                "inputs": {
                    "session_summary": {"required": True},
                },
                "trigger": "session_list",
            }
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app, context, state
        if action_id != "contribute_second_order":
            raise ValueError(f"Unknown action {action_id!r}")
        summary = params.get("session_summary")
        if not isinstance(summary, dict):
            raise TypeError("session_summary is required")
        metadata = summary.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        return {
            "session_list_fields": {
                "second_rank": metadata.get("second_rank", 0),
            },
            "session_list_order": [
                {
                    "key": "second_rank",
                    "direction": "asc",
                    "fallback": 0,
                    "priority": 20,
                }
            ],
        }


__all__ = [
    "SessionListingFixturePlugin",
    "SessionListingSecondFixturePlugin",
]
