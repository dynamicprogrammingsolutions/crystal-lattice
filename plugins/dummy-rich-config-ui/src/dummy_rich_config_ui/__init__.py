"""Opt-in controls for manually testing portable rich configuration UI."""

from __future__ import annotations

from typing import Any


_APPEARANCE_OPTIONS = [
    {
        "value": "primary",
        "label": "Primary",
        "icon": "circle",
        "tone": "primary",
    },
    {
        "value": "highlight",
        "label": "Highlight",
        "icon": "star",
        "tone": "highlight",
    },
    {
        "value": "warning",
        "label": "Warning",
        "icon": "alert-triangle",
        "tone": "warning",
    },
    {
        "value": "success",
        "label": "Success",
        "icon": "check-circle",
        "tone": "success",
    },
    {
        "value": "danger",
        "label": "Danger",
        "icon": "x-circle",
        "tone": "danger",
    },
    {
        "value": "muted",
        "label": "Muted",
        "icon": "minus-circle",
        "tone": "muted",
    },
]

_TOGGLE_OPTIONS = [
    {
        "value": False,
        "label": "Off",
        "icon": "toggle-left",
        "tone": "primary",
    },
    {
        "value": True,
        "label": "On",
        "icon": "toggle-right",
        "tone": "success",
    },
]


class DummyRichConfigUiFeature:
    """Expose opt-in settings that exercise portable rich UI presentation."""

    name = "dummy_rich_config_ui"
    version = "0.1.0"
    default_enabled = False

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "dummy_rich_ui_appearance": {
                "type": "string",
                "enum": [option["value"] for option in _APPEARANCE_OPTIONS],
                "default": "primary",
                "description": "Selected semantic appearance in the dummy rich UI.",
            },
            "dummy_rich_ui_toggle": {
                "type": "boolean",
                "default": False,
                "description": "Enabled state of the dummy rich toggle.",
            },
        }

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        _ = config, context
        return [
            {
                "ui_type": "config",
                "type": "select",
                "key": "dummy_rich_ui_appearance",
                "label": "Dummy rich appearance",
                "icon": "sliders",
                "description": (
                    "Exercises semantic option icons and tones without changing "
                    "a production provider."
                ),
                "default": "primary",
                "options": _APPEARANCE_OPTIONS,
                "rich_ui": {
                    "kind": "dropdown",
                    "label": "Appearance",
                    "show_label": False,
                    "options": _APPEARANCE_OPTIONS,
                    "placements": ["composer", "session_header"],
                    "default_pinned": True,
                },
            },
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "dummy_rich_ui_toggle",
                "label": "Dummy rich toggle",
                "icon": "toggle-left",
                "description": "Exercises immediate rich Boolean mutation.",
                "default": False,
                "rich_ui": {
                    "kind": "toggle",
                    "label": "Dummy toggle",
                    "show_label": False,
                    "options": _TOGGLE_OPTIONS,
                    "placements": ["composer"],
                    "default_pinned": True,
                },
            },
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "dummy_rich_ui_disabled_toggle",
                "label": "Disabled dummy rich toggle",
                "icon": "slash",
                "description": "Exercises disabled compact-control presentation.",
                "default": True,
                "disabled": True,
                "rich_ui": {
                    "kind": "toggle",
                    "label": "Disabled",
                    "show_label": False,
                    "options": _TOGGLE_OPTIONS,
                    "placements": ["session_header"],
                    "default_pinned": False,
                },
            },
        ]


__all__ = ["DummyRichConfigUiFeature"]
