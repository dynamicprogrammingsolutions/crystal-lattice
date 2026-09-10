from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from agent_app.application_future import AgentApplication
from agent_app.plugin_sources.dotted import DottedClassSource
from agent_core.types import ProviderPlugin


class EmbeddedSmokeProvider(ProviderPlugin):
    name = "embedded_smoke_provider"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"config": config}

    def call_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        final = {
            "role": "assistant",
            "content": "Embedded runtime smoke response",
            "metadata": {"development_smoke_provider": True},
        }
        return [], [final], [*native_messages, final], state

    def stream_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> Iterator[dict[str, Any]]:
        _ = native_messages, state
        yield {"content": "Embedded runtime smoke response"}


def _config_payload() -> dict[str, Any]:
    return {
        "plugin_policy": {
            "allow_bash_tools": False,
            "allow_dynamic_plugin_install": False,
            "allow_node_tools": False,
            "allow_remote": False,
        },
        "providers": {
            "embedded": {
                "provider": "embedded_smoke_provider",
                "model": "embedded-smoke",
            }
        },
        "plugins": [
            "crystal_lattice_mobile_runtime.EmbeddedSmokeProvider",
        ],
        "agents": {
            "local": {
                "provider": "embedded",
            }
        },
    }


def run_application_smoke(runtime_root: str) -> dict[str, Any]:
    root = Path(runtime_root)
    config_dir = root / "config"
    sessions_dir = root / "sessions"
    workspace_dir = root / "workspace"
    config_dir.mkdir(parents=True, exist_ok=True)
    sessions_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(_config_payload(), indent=2) + "\n",
        encoding="utf-8",
    )

    application = AgentApplication(
        config_path,
        sessions_dir,
        plugin_sources=[DottedClassSource()],
    )
    core, base_config, session = application.create_session("local")
    session = core.add_message(
        session,
        "user",
        "Embedded application smoke",
        config=base_config,
    )
    application.save_session(session)
    stored = application.load_session_record(session.session_id)
    if stored is None:
        raise RuntimeError("Embedded session was not persisted")

    return {
        "status": "ready",
        "pythonVersion": ".".join(map(str, __import__("sys").version_info[:3])),
        "pythonPlatform": __import__("sys").platform,
        "agents": application.list_agents(),
        "sessionId": stored.session_id,
        "messageCount": len(stored.messages),
    }