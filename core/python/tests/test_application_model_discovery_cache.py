from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent_app.application_future import AgentApplication
from agent_core import AgentCore


class CountingLifecycleProvider:
    name = "counting_lifecycle_provider"
    version = "1.0.0"
    get_models_calls = 0

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        type(self).get_models_calls += 1
        return [{"id": str(config.get("model", "default-model"))}]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": dict(config)}

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        _ = state
        return list(messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        _ = state
        return list(native_messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], [], list(native_messages), state


class CountingLifecycleExtension:
    name = "counting_lifecycle_extension"
    version = "1.0.0"

    def process_chunk(
        self,
        native_chunk: Dict[str, Any] | None,
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        _ = native_chunk
        return partial_messages, final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "mark_session_create",
                "label": "Mark create",
                "inputs": {},
                "trigger": "session_create",
            },
            {
                "id": "mark_session_save",
                "label": "Mark save",
                "inputs": {},
                "trigger": "session_save_prepare",
            },
        ]

    def execute_action(
        self,
        action_id: str,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Dict[str, Any] | None,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = params, state
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        log = metadata.get("counting_lifecycle_log")
        if not isinstance(log, list):
            log = []
        lifecycle = (context or {}).get("lifecycle") if isinstance(context, dict) else None
        if isinstance(lifecycle, str):
            log = [*log, lifecycle]
        return {
            "native_messages": list(native_messages),
            "session_metadata": {
                "counting_lifecycle_log": log,
                action_id: True,
            },
        }


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {
            "default": {
                "provider": "counting_lifecycle_provider",
                "model": "test-model",
            }
        },
        "plugins": [
            "tests.test_application_model_discovery_cache.CountingLifecycleProvider",
            "tests.test_application_model_discovery_cache.CountingLifecycleExtension",
        ],
        "agents": {"default": {"provider": "default"}},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_agent_application_shares_model_discovery_cache_across_fresh_cores(
    tmp_path: Path,
) -> None:
    CountingLifecycleProvider.get_models_calls = 0
    app = AgentApplication(
        str(_write_config(tmp_path)),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )

    _core, _base_config, session = app.create_session("default")

    assert session.metadata["mark_session_create"] is True
    assert session.metadata["mark_session_save"] is True
    assert session.metadata["counting_lifecycle_log"] == [
        "session_create",
        "session_save_prepare",
    ]
    assert CountingLifecycleProvider.get_models_calls == 1

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    core2, base_config2, loaded_session = loaded
    core2.get_session_actions(base_config2)

    assert loaded_session.session_id == session.session_id
    assert CountingLifecycleProvider.get_models_calls == 1