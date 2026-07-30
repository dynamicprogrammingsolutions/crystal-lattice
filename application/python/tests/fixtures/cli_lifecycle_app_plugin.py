from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


class CliLifecycleAppPlugin:
    name = "cli_lifecycle_app_plugin"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application = app_config.get("application")
        config = application if isinstance(application, dict) else {}
        return {
            "actions_path": str(config.get("cli_lifecycle_actions_path") or ""),
            "closes_path": str(config.get("cli_lifecycle_closes_path") or ""),
        }

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Dict[str, Any] | None = None,
        context: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, context
        return []

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "record_server_settings_changed",
                "label": "Record server settings changed",
                "inputs": {},
                "trigger": "server_settings_changed",
            }
        ]

    def get_commands(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Dict[str, Any] | None,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app, params
        record = {
            "action_id": action_id,
            "context": dict(context or {}),
            "pid": os.getpid(),
        }
        self._append_jsonl(state.get("actions_path"), record)
        return {"record": record}

    def close(self, state: Dict[str, Any]) -> None:
        self._append_jsonl(
            state.get("closes_path"),
            {
                "pid": os.getpid(),
            },
        )

    @staticmethod
    def _append_jsonl(path: Any, payload: Dict[str, Any]) -> None:
        if not isinstance(path, str) or not path:
            return
        marker_path = Path(path)
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        with marker_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str, sort_keys=True) + "\n")


__all__ = ["CliLifecycleAppPlugin"]
