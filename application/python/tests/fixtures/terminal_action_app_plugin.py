from __future__ import annotations

from typing import Any, Dict, List


class TerminalActionAppPlugin:
    name = "terminal_action_fixture"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application = app_config.get("application")
        fixture = (
            application.get("terminal_action_fixture")
            if isinstance(application, dict)
            else None
        )
        configured_path = (
            fixture.get("slash_path") if isinstance(fixture, dict) else None
        )
        slash_path = (
            configured_path
            if isinstance(configured_path, list)
            and configured_path
            and all(isinstance(token, str) and token for token in configured_path)
            else ["fixture", "record"]
        )
        return {"calls": [], "slash_path": slash_path}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "record",
                "label": "Record inputs",
                "inputs": {
                    "text": {"type": "string", "required": True},
                    "count": {"type": "integer", "required": False, "default": 2},
                    "enabled": {
                        "type": "boolean",
                        "required": False,
                        "default": False,
                    },
                    "ratio": {"type": "number", "required": False, "default": 1.5},
                    "choice": {
                        "type": "string",
                        "required": False,
                        "default": "alpha",
                    },
                    "note": {"type": "string", "required": False},
                    "secret": {"type": "string", "required": False},
                    "password": {"type": "string", "required": False},
                    "session_id": {"type": "string", "required": False},
                    "message_index": {"type": "integer", "required": False},
                },
            },
            {
                "id": "show_followup",
                "label": "Show follow-up",
                "inputs": {},
            },
            {
                "id": "bare",
                "label": "Bare procedure",
                "inputs": {},
            },
        ]

    def get_commands(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Dict[str, Any] | None = None,
        context: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, context
        form = {
            "kind": "form",
            "title": "Record values",
            "inputs": [
                {"name": "text", "type": "text", "label": "Text", "required": True},
                {
                    "name": "count",
                    "type": "integer",
                    "label": "Count",
                    "default": 2,
                },
                {
                    "name": "enabled",
                    "type": "boolean",
                    "label": "Enabled",
                    "default": False,
                },
                {
                    "name": "note",
                    "type": "multiline",
                    "label": "Note",
                    "required": False,
                    "submit_empty": True,
                },
                {
                    "name": "secret",
                    "type": "secret",
                    "label": "Secret",
                    "required": False,
                },
                {
                    "name": "password",
                    "type": "password",
                    "label": "Password",
                    "required": False,
                },
                {
                    "name": "ratio",
                    "type": "number",
                    "label": "Ratio",
                    "default": 1.5,
                },
                {
                    "name": "choice",
                    "type": "select",
                    "label": "Choice",
                    "default": "alpha",
                    "options": [
                        {"value": "alpha", "label": "Alpha"},
                        {"value": "beta", "label": "Beta"},
                    ],
                },
            ],
        }
        mapping = {
            "text": "$dialog.text",
            "count": "$dialog.count",
            "enabled": "$dialog.enabled",
            "note": "$dialog.note",
            "secret": "$dialog.secret",
            "password": "$dialog.password",
            "ratio": "$dialog.ratio",
            "choice": "$dialog.choice",
            "session_id": "$session.session_id",
        }
        cli_form = {
            "kind": "form",
            "inputs": [
                {"name": "value", "type": "text", "required": True},
                {"name": "count", "type": "integer", "default": 2},
                {"name": "enabled", "type": "boolean", "default": False},
            ],
        }
        return [
            {
                "ui_type": "cli_command",
                "id": "fixture_cli",
                "path": ["fixture", "record"],
                "label": "Fixture record",
                "description": "Record fixture values.",
                "action_id": "record",
                "dialog": cli_form,
                "param_map": {
                    "text": "$dialog.value",
                    "count": "$dialog.count",
                    "enabled": "$dialog.enabled",
                },
            },
            {
                "ui_type": "slash_command",
                "id": "fixture_slash",
                "path": state["slash_path"],
                "aliases": [["record", "fixture"]],
                "label": "Fixture record",
                "description": "Record fixture values.",
                "scope": "session",
                "action_id": "record",
                "dialog": form,
                "param_map": mapping,
            },
            {
                "ui_type": "application_action",
                "id": "fixture_application",
                "label": "Fixture application action",
                "action_id": "record",
                "dialog": form,
                "param_map": mapping,
                "order": 20,
            },
            {
                "ui_type": "session_list_action",
                "id": "fixture_session_list",
                "label": "Fixture session-list action",
                "action_id": "record",
                "fixed_params": {"text": "session-list"},
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {"kind": "none"},
                "order": 15,
            },
            {
                "ui_type": "session_action",
                "id": "fixture_session",
                "label": "Fixture session action",
                "action_id": "record",
                "dialog": form,
                "param_map": mapping,
                "order": 10,
            },
            {
                "ui_type": "session_action",
                "id": "fixture_disabled",
                "label": "Disabled fixture action",
                "action_id": "record",
                "dialog": form,
                "param_map": mapping,
                "disabled": True,
                "disabled_reason": "fixture is unavailable",
                "order": 30,
            },
            {
                "ui_type": "message_action",
                "id": "fixture_message",
                "label": "Fixture message action",
                "action_id": "record",
                "fixed_params": {"text": "message"},
                "param_map": {
                    "session_id": "$session.session_id",
                    "message_index": "$message.index",
                },
                "condition": {"path": "role", "eq": "user"},
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "message_action",
                "id": "fixture_message_followup",
                "label": "Fixture message follow-up",
                "action_id": "show_followup",
                "condition": {"path": "role", "eq": "user"},
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "fixture_show_followup",
                "label": "Show fixture follow-up",
                "action_id": "show_followup",
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "fixture_confirm",
                "label": "Confirm fixture action",
                "action_id": "record",
                "fixed_params": {"text": "confirmed"},
                "dialog": {
                    "kind": "confirm",
                    "title": "Run fixture action?",
                },
            },
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Dict[str, Any] | None,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app
        if action_id == "show_followup":
            return {
                "display": {
                    "format": "text",
                    "title": "Fixture follow-up",
                    "body": "A follow-up is available.",
                    "display_id": "fixture-followup",
                    "form": {
                        "kind": "form",
                        "inputs": [
                            {
                                "name": "text",
                                "type": "text",
                                "label": "Text",
                                "required": True,
                            }
                        ],
                    },
                    "actions": [
                        {
                            "kind": "run_action",
                            "id": "record-followup",
                            "label": "Record follow-up",
                            "plugin": self.name,
                            "action_id": "record",
                            "fixed_params": {
                                "count": 4,
                                "enabled": True,
                            },
                            "param_map": {
                                "text": "$form.text",
                                "count": "$dialog.count",
                                "session_id": "$session.session_id",
                                "message_index": "$message.index",
                            },
                            "dialog": {
                                "kind": "form",
                                "inputs": [
                                    {
                                        "name": "count",
                                        "type": "integer",
                                        "label": "Count",
                                        "default": 4,
                                    }
                                ],
                            },
                            "preserve_display": True,
                        }
                    ],
                }
            }
        if params.get("text") == "raise-sensitive-error":
            raise RuntimeError(
                f"fixture failed with {params.get('secret')} "
                f"and {params.get('password')}"
            )
        record = {
            "action_id": action_id,
            "params": dict(params),
            "context": dict(context or {}),
        }
        state["calls"].append(record)
        return {
            "display": {
                "format": "text",
                "title": "Recorded",
                "body": (
                    f"Recorded {params.get('text')}; "
                    f"secret={params.get('secret')}; "
                    f"password={params.get('password')}"
                ),
                "variant": "success",
            },
            "record": record,
        }


__all__ = ["TerminalActionAppPlugin"]
