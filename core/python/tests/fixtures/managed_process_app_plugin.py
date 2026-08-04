from __future__ import annotations

from typing import Any

from agent_app.managed_processes import get_managed_process_registry


CREATED_MANAGED_PROCESSES: list["ManagedProcessFixture"] = []


class ManagedProcessFixture:
    def __init__(self, process_id: str) -> None:
        self.process_id = process_id
        self.started = False
        self.closed = False
        self.messages: list[str] = []

    def start(self) -> None:
        self.started = True

    def close(self) -> None:
        self.closed = True

    def send(self, message: str) -> None:
        self.messages.append(message)

    def snapshot(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "started": self.started,
            "closed": self.closed,
            "messages": list(self.messages),
        }


class ManagedProcessFixtureAppPlugin:
    name = "managed_process_fixture"
    version = "1.0.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        _ = app_config
        return {}

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [
            {
                "id": "start",
                "label": "Start managed process",
                "inputs": {
                    "process_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "send",
                "label": "Send to managed process",
                "inputs": {
                    "process_id": {"type": "string", "required": True},
                    "message": {"type": "string", "required": True},
                },
            },
            {
                "id": "status",
                "label": "Managed process status",
                "inputs": {
                    "process_id": {"type": "string", "required": True},
                },
            },
        ]

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        _ = state, config, context
        return []

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = context, state
        process_id = str(params["process_id"])
        registry = get_managed_process_registry(app.get_runtime_store())

        if action_id == "start":
            process = ManagedProcessFixture(process_id)
            CREATED_MANAGED_PROCESSES.append(process)
            registry.start(process_id, process)
            return {"process": process.snapshot()}

        process = registry.get(process_id)
        if not isinstance(process, ManagedProcessFixture):
            return {"found": False, "process_id": process_id}

        if action_id == "send":
            process.send(str(params["message"]))
            return {"found": True, "process": process.snapshot()}
        if action_id == "status":
            return {"found": True, "process": process.snapshot()}
        raise KeyError(action_id)


__all__ = [
    "CREATED_MANAGED_PROCESSES",
    "ManagedProcessFixture",
    "ManagedProcessFixtureAppPlugin",
]
