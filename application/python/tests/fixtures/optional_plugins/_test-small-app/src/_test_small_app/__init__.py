from __future__ import annotations

import tomli_w


DEPENDENCY_SENTINEL = tomli_w.dumps({"fixture": True})


class SmallTestAppPlugin:
    name = "_test_small_app"
    version = "0.1.0"

    def get_config_schema(self) -> dict:
        return {}

    def get_ui_elements(self, state: dict, config=None, tags=None, models=None):
        _ = state, config, tags, models
        return []

    def get_commands(self, state: dict) -> list[dict]:
        _ = state
        return []

    def init(self, app_config: dict) -> dict:
        _ = app_config
        return {"dependency_sentinel": DEPENDENCY_SENTINEL}

    def get_actions(self, state: dict) -> list[dict]:
        _ = state
        return [
            {
                "id": "_test_small_app.ping",
                "label": "Fixture Ping",
                "description": "Test-only application plugin action",
                "inputs": {},
            }
        ]

    def execute_action(
        self,
        app,
        action_id: str,
        params: dict,
        context: dict | None,
        state: dict,
    ) -> dict:
        _ = app, params, context
        if action_id != "_test_small_app.ping":
            raise ValueError(f"Unknown action: {action_id}")
        return {"ok": True, "dependency_sentinel": state["dependency_sentinel"]}
