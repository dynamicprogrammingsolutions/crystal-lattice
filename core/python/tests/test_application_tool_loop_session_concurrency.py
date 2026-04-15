from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List

from agent_app.application_future import AgentApplication
from agent_core import AgentCore, Session
from agent_core.types import ProviderPlugin

from .dummy_lifecycle_app_plugin import DummyLifecycleAppPlugin  # noqa: F401
from .dummy_lifecycle_extension import DummyLifecycleExtension  # noqa: F401
from .dummy_tool import DummyCalculator  # noqa: F401


@dataclass
class ConfigAwareProvider(ProviderPlugin):
    name: str = "config_aware_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "required": True}}

    def get_ui_elements(self, config=None, tags=None, models=None) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": dict(config)}

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ):
        return list(native_messages), state

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ):
        return [], [], list(native_messages), state

    def finalize(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]):
        return [], list(native_messages), state

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ):
        model = str((state.get("config") or {}).get("model") or "unknown")
        final = {
            "role": "assistant",
            "content": f"model={model}",
            "metadata": {},
        }
        return [], [final], [*native_messages, final], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        for char in "unused":
            yield {"content": char}


def _write_config(tmp_path: Path, *, include_lifecycle: bool = False) -> Path:
    plugins = [
        "tests.test_application_tool_loop_session_concurrency.ConfigAwareProvider",
        "tests.dummy_tool.DummyCalculator",
    ]
    if include_lifecycle:
        plugins.extend(
            [
                "tests.dummy_lifecycle_extension.DummyLifecycleExtension",
                "tests.dummy_lifecycle_app_plugin.DummyLifecycleAppPlugin",
            ]
        )

    config = {
        "providers": {
            "dummy": {"provider": "config_aware_provider", "model": "initial-model"},
        },
        "plugins": plugins,
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _make_pending_tool_call_session(
    app: AgentApplication,
) -> tuple[AgentCore, Dict[str, Any], Session]:
    core, base_config, session = app.create_session("default")
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": [tool_call]},
    )
    app.save_session(session)
    return core, base_config, session


def test_concurrent_override_change_is_applied_before_next_phase(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    core, base_config, session = _make_pending_tool_call_session(app)

    events_iter = app.send_request(core, session, base_config, overrides=None, stream=False)
    events: List[Dict[str, Any]] = []
    updated = False

    for event in events_iter:
        events.append(event)
        if event.get("type") != "session_checkpoint" or updated:
            continue
        checkpoint = event.get("session")
        if not isinstance(checkpoint, Session):
            continue
        if len(checkpoint.messages) != 2:
            continue

        stored = app.load_session_record(session.session_id)
        assert stored is not None
        new_metadata = dict(stored.metadata)
        new_metadata["overrides"] = {"model": "updated-model"}
        app.save_session(
            Session(
                session_id=stored.session_id,
                messages=stored.messages,
                metadata=new_metadata,
            )
        )
        updated = True

    assert updated, "expected to update overrides after the tool checkpoint"

    final_events = [ev for ev in events if ev.get("type") == "final"]
    assert final_events
    assert final_events[-1]["messages"][-1]["content"] == "model=updated-model"

    stored_final = app.load_session_record(session.session_id)
    assert stored_final is not None
    assert stored_final.metadata["overrides"]["model"] == "updated-model"


def test_concurrent_non_settings_change_stops_request_and_saves_backup(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, include_lifecycle=True)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    core, base_config, session = _make_pending_tool_call_session(app)

    events_iter = app.send_request(core, session, base_config, overrides=None, stream=False)
    events: List[Dict[str, Any]] = []
    modified = False

    for event in events_iter:
        events.append(event)
        if event.get("type") != "session_checkpoint" or modified:
            continue
        checkpoint = event.get("session")
        if not isinstance(checkpoint, Session):
            continue
        if len(checkpoint.messages) < 2:
            continue

        stored = app.load_session_record(session.session_id)
        assert stored is not None
        external = Session(
            session_id=stored.session_id,
            messages=[
                *stored.messages,
                type(stored.messages[0])(
                    role="user",
                    content="concurrent edit",
                    metadata={},
                ),
            ],
            metadata=stored.metadata,
        )
        app.save_session(external)
        modified = True

    assert modified, "expected to inject a concurrent conflicting edit"

    error_events = [ev for ev in events if ev.get("type") == "error"]
    assert error_events
    detail = str(error_events[-1]["detail"])
    assert "Concurrent session modification detected" in detail
    match = re.search(r"Backup saved to (.+)$", detail)
    assert match is not None
    backup_path = Path(match.group(1).strip())
    assert backup_path.exists()

    request_completed = [ev for ev in events if ev.get("type") == "request_completed"]
    assert request_completed

    stored_final = app.load_session_record(session.session_id)
    assert stored_final is not None
    assert stored_final.messages[-1].content == "concurrent edit"