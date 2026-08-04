from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import set_key


def _restore_file(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(previous)


class ApplicationConfigAppPlugin:
    name = "application_config"
    version = "1.0.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        application = app_config.get("application")
        plugin_config = (
            application.get("application_config")
            if isinstance(application, dict)
            else None
        )
        if not isinstance(plugin_config, dict):
            plugin_config = {}
        env_file = plugin_config.get("env_file")
        env_path = Path(
            env_file if isinstance(env_file, str) and env_file else "~/.crystal/.env"
        ).expanduser()
        editable_keys = plugin_config.get("editable_env_keys")
        allowed = (
            {key for key in editable_keys if isinstance(key, str) and key}
            if isinstance(editable_keys, list)
            else set()
        )
        provider_keys = plugin_config.get("provider_env_keys")
        mappings = (
            {
                provider_id: env_key
                for provider_id, env_key in provider_keys.items()
                if (
                    isinstance(provider_id, str)
                    and provider_id
                    and isinstance(env_key, str)
                    and env_key in allowed
                )
            }
            if isinstance(provider_keys, dict)
            else {}
        )
        return {
            "env_file": env_path,
            "provider_env_keys": mappings,
        }

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [
            {
                "id": "reload_application",
                "label": "Reload application",
                "description": "Request a complete application reload.",
                "inputs": {},
            },
            {
                "id": "set_provider_api_key",
                "label": "Set provider API key",
                "description": "Update one configured dotenv provider key and reload.",
                "inputs": {
                    "provider_id": {"type": "string", "required": True},
                    "api_key": {
                        "type": "string",
                        "required": True,
                        "sensitive": True,
                    },
                },
            },
        ]

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        _ = config, context
        provider_keys = state.get("provider_env_keys")
        options = (
            [
                {"value": provider_id, "label": provider_id}
                for provider_id in sorted(provider_keys)
            ]
            if isinstance(provider_keys, dict)
            else []
        )
        return [
            {
                "ui_type": "application_action",
                "id": "reload_application",
                "label": "Reload application",
                "icon": "refresh-cw",
                "order": 10,
                "action_id": "reload_application",
                "dialog": {
                    "kind": "confirm",
                    "title": "Reload application",
                    "message": (
                        "Finish current work, then reconstruct the application?"
                    ),
                },
            },
            {
                "ui_type": "application_action",
                "id": "set_provider_api_key",
                "label": "Set provider API key",
                "icon": "key",
                "order": 20,
                "action_id": "set_provider_api_key",
                "dialog": {
                    "kind": "form",
                    "title": "Set provider API key",
                    "inputs": [
                        {
                            "name": "provider_id",
                            "type": "select",
                            "label": "Provider",
                            "required": True,
                            "options": options,
                        },
                        {
                            "name": "api_key",
                            "type": "secret",
                            "label": "API key",
                            "required": True,
                            "placeholder": "Enter a new API key",
                        },
                    ],
                },
                "param_map": {
                    "provider_id": "$dialog.provider_id",
                    "api_key": "$dialog.api_key",
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
        _ = context
        if action_id == "reload_application":
            return app.request_application_reload(reason="application_config_action")
        if action_id != "set_provider_api_key":
            raise KeyError(f"Unknown action {action_id!r}")

        provider_id = str(params.get("provider_id") or "")
        api_key = str(params.get("api_key") or "")
        provider_keys = state.get("provider_env_keys")
        env_key = (
            provider_keys.get(provider_id) if isinstance(provider_keys, dict) else None
        )
        if not isinstance(env_key, str) or not env_key:
            raise ValueError(f"Provider {provider_id!r} is not editable")
        if env_key in os.environ:
            raise ValueError(
                f"{env_key} is supplied by the process environment and is externally managed"
            )
        if not api_key:
            raise ValueError("api_key must be a non-empty string")

        env_path = state.get("env_file")
        if not isinstance(env_path, Path):
            raise RuntimeError("Application config env_file is unavailable")
        previous = env_path.read_bytes() if env_path.exists() else None
        env_path.parent.mkdir(parents=True, exist_ok=True)
        set_key(str(env_path), env_key, api_key, quote_mode="always")

        def rollback() -> None:
            _restore_file(env_path, previous)

        try:
            return app.request_application_reload(
                reason=f"provider_api_key:{provider_id}",
                on_failure=rollback,
            )
        except Exception:
            rollback()
            raise


__all__ = ["ApplicationConfigAppPlugin"]
