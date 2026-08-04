from __future__ import annotations

"""Demo application plugin for action display embedded form validation."""

from typing import Any


class DummyActionDisplayFormAppPlugin:
    name = "dummy_action_display_form_app"
    version = "1.0.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        _ = app_config
        return {"submitted_values": []}

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "session_action",
                "id": "dummy_show_display_form",
                "label": "Show display form",
                "icon": "form-input",
                "order": 90,
                "action_id": "show_display_form",
                "dialog": {"kind": "none"},
            }
        ]

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [
            {
                "id": "show_display_form",
                "label": "Show display form",
                "description": "Return a generic action display with embedded form fields.",
                "inputs": {},
            },
            {
                "id": "submit_display_form",
                "label": "Submit display form",
                "description": "Echo values submitted through an action display embedded form.",
                "inputs": {
                    "callback_url": {"type": "string", "required": True},
                    "note": {"type": "string", "required": False},
                    "mode": {"type": "string", "required": False},
                    "source": {"type": "string", "required": False},
                },
            },
        ]

    def get_commands(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = app, context
        if action_id == "show_display_form":
            return self._show_display_form()
        if action_id == "submit_display_form":
            return self._submit_display_form(params, state)
        raise ValueError(f"Unknown action_id {action_id!r}")

    def _show_display_form(self) -> dict[str, Any]:
        return {
            "display": {
                "format": "markdown",
                "title": "Dummy Display Form",
                "body": (
                    "Use this form to verify that action displays can collect "
                    "values and pass them to follow-up actions."
                ),
                "variant": "info",
                "presentation": "inline",
                "display_id": "dummy-action-display-form",
                "form": {
                    "kind": "form",
                    "inputs": [
                        {
                            "name": "callback_url",
                            "type": "multiline",
                            "label": "Callback URL",
                            "placeholder": "https://example.test/callback?code=abc&state=xyz",
                            "required": True,
                        },
                        {
                            "name": "note",
                            "type": "string",
                            "label": "Note",
                            "placeholder": "Optional note",
                            "required": False,
                            "submit_empty": True,
                        },
                        {
                            "name": "mode",
                            "type": "select",
                            "label": "Mode",
                            "default": "manual",
                            "required": True,
                            "options": [
                                {"value": "manual", "label": "Manual"},
                                {"value": "automated", "label": "Automated"},
                            ],
                        },
                    ],
                },
                "actions": [
                    {
                        "kind": "run_action",
                        "id": "dummy-submit-display-form",
                        "label": "Submit",
                        "plugin": "dummy_action_display_form_app",
                        "action_id": "submit_display_form",
                        "fixed_params": {"source": "display_form"},
                        "param_map": {
                            "callback_url": "$form.callback_url",
                            "note": "$form.note",
                            "mode": "$form.mode",
                        },
                        "preserve_display": False,
                    },
                    {
                        "kind": "dismiss",
                        "id": "dummy-cancel-display-form",
                        "label": "Cancel",
                    },
                ],
            }
        }

    def _submit_display_form(
        self,
        params: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        callback_url = str(params.get("callback_url") or "")
        note = str(params.get("note") or "")
        mode = str(params.get("mode") or "")
        source = str(params.get("source") or "")

        submitted = state.get("submitted_values")
        if isinstance(submitted, list):
            submitted.append(
                {
                    "callback_url": callback_url,
                    "note": note,
                    "mode": mode,
                    "source": source,
                }
            )

        return {
            "display": {
                "format": "markdown",
                "title": "Dummy Form Submitted",
                "body": (
                    f"- Callback URL: `{callback_url}`\n"
                    f"- Note: `{note}`\n"
                    f"- Mode: `{mode}`\n"
                    f"- Source: `{source}`"
                ),
                "variant": "success",
                "presentation": "inline",
                "display_id": "dummy-action-display-form-result",
                "actions": [
                    {
                        "kind": "dismiss",
                        "id": "dummy-dismiss-confirmation",
                        "label": "Close",
                    }
                ],
            }
        }


__all__ = ["DummyActionDisplayFormAppPlugin"]