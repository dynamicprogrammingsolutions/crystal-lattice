from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List

import pytest

from agent_app.application_future import AgentApplication, SessionConflictError
from agent_core import AgentCore, Message, Session
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


def _make_user_prompt_session(
    app: AgentApplication,
) -> tuple[AgentCore, Dict[str, Any], Session]:
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello", {})
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
    config_path = _write_config(tmp_path)
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


def test_reconciled_save_detects_conflict_for_long_running_action(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore)

    _core, _base_config, session = _make_user_prompt_session(app)
    baseline_file_state = app.get_session_file_state(session.session_id)

    stored = app.load_session_record(session.session_id)
    assert stored is not None
    external = Session(
        session_id=stored.session_id,
        messages=[*stored.messages, Message(role="user", content="external edit", metadata={})],
        metadata=stored.metadata,
    )
    app.save_session(external)

    modified = Session(
        session_id=session.session_id,
        messages=[*session.messages, Message(role="assistant", content="summary", metadata={})],
        metadata=session.metadata,
    )

    with pytest.raises(SessionConflictError) as exc_info:
        app.save_session(
            modified,
            reconcile=True,
            baseline_session=session,
            baseline_file_state=baseline_file_state,
            conflict_prefix="Concurrent session modification detected while saving action result; ",
            backup_on_conflict=True,
            conflict_request_id="action-conflict",
        )

    assert "Concurrent session modification detected while saving action result" in str(
        exc_info.value
    )
    assert exc_info.value.backup_path is not None
    assert exc_info.value.backup_path.exists()

    stored_final = app.load_session_record(session.session_id)
    assert stored_final is not None
    assert stored_final.messages[-1].content == "external edit"


def test_request_preflight_applies_override_only_drift_before_first_phase(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    session_root = tmp_path / "sessions"
    app_terminal = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    app_server = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, stale_session = _make_user_prompt_session(app_terminal)

    stored = app_server.load_session_record(stale_session.session_id)
    assert stored is not None
    updated = Session(
        session_id=stored.session_id,
        messages=stored.messages,
        metadata={**stored.metadata, "overrides": {"model": "updated-model"}},
    )
    app_server.save_session(updated)

    events = list(
        app_terminal.send_request(core, stale_session, base_config, overrides=None, stream=False)
    )

    error_events = [ev for ev in events if ev.get("type") == "error"]
    assert not error_events

    final_events = [ev for ev in events if ev.get("type") == "final"]
    assert final_events
    assert final_events[-1]["messages"][-1]["content"] == "model=updated-model"

    stored_final = app_server.load_session_record(stale_session.session_id)
    assert stored_final is not None
    assert stored_final.metadata["overrides"]["model"] == "updated-model"


def test_request_preflight_allows_non_protected_metadata_drift_before_first_phase(
    tmp_path: Path,
) -> None:
    config_path = _write_config(tmp_path)
    session_root = tmp_path / "sessions"
    app_terminal = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    app_server = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, stale_session = _make_user_prompt_session(app_terminal)

    stored = app_server.load_session_record(stale_session.session_id)
    assert stored is not None
    updated = Session(
        session_id=stored.session_id,
        messages=stored.messages,
        metadata={**stored.metadata, "pinned": True},
    )
    app_server.save_session(updated)

    events = list(
        app_terminal.send_request(core, stale_session, base_config, overrides=None, stream=False)
    )

    assert not [ev for ev in events if ev.get("type") == "error"]
    assert [ev for ev in events if ev.get("type") == "final"]

    stored_final = app_server.load_session_record(stale_session.session_id)
    assert stored_final is not None
    assert stored_final.metadata["pinned"] is True


def test_request_preflight_rejects_stale_terminal_session_before_first_phase(
    tmp_path: Path,
) -> None:
    config_path = _write_config(tmp_path)
    session_root = tmp_path / "sessions"
    app_terminal = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    app_server = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, stale_session = _make_user_prompt_session(app_terminal)

    fresh_ctx = app_server.load_session(stale_session.session_id)
    assert fresh_ctx is not None
    server_core, server_base_config, fresh_session = fresh_ctx
    server_events = list(
        app_server.send_request(
            server_core, fresh_session, server_base_config, overrides=None, stream=False
        )
    )
    assert [ev for ev in server_events if ev.get("type") == "final"]

    stale_events = list(
        app_terminal.send_request(core, stale_session, base_config, overrides=None, stream=False)
    )

    error_events = [ev for ev in stale_events if ev.get("type") == "error"]
    assert error_events
    assert "Concurrent session modification detected before request start" in str(
        error_events[-1]["detail"]
    )
    assert not [ev for ev in stale_events if ev.get("type") == "final"]
    assert not [ev for ev in stale_events if ev.get("type") == "session_checkpoint"]

    stored_final = app_server.load_session_record(stale_session.session_id)
    assert stored_final is not None
    assert len(stored_final.messages) == 2
    assert stored_final.messages[-1].role == "assistant"


def test_fresh_concurrent_request_reloaded_from_storage_fails_later_with_error_event(
    tmp_path: Path,
) -> None:
    config_path = _write_config(tmp_path)
    session_root = tmp_path / "sessions"
    app_a = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    app_b = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    _core, _base_config, created = _make_pending_tool_call_session(app_a)

    ctx_a = app_a.load_session(created.session_id)
    assert ctx_a is not None
    core_a, base_config_a, session_a = ctx_a
    events_a_iter = app_a.send_request(
        core_a, session_a, base_config_a, overrides=None, stream=False
    )
    events_a: List[Dict[str, Any]] = [next(events_a_iter)]
    assert events_a[0]["type"] == "request_started"

    ctx_b = app_b.load_session(created.session_id)
    assert ctx_b is not None
    core_b, base_config_b, session_b = ctx_b
    events_b_iter = app_b.send_request(
        core_b, session_b, base_config_b, overrides=None, stream=False
    )
    events_b: List[Dict[str, Any]] = [next(events_b_iter)]
    assert events_b[0]["type"] == "request_started"

    for event in events_a_iter:
        events_a.append(event)
        if event.get("type") == "session_checkpoint":
            break

    events_b.extend(list(events_b_iter))

    error_events_b = [ev for ev in events_b if ev.get("type") == "error"]
    assert error_events_b
    assert "Concurrent session modification detected before the next phase" in str(
        error_events_b[-1]["detail"]
    )

    stored_final = app_a.load_session_record(created.session_id)
    assert stored_final is not None
    assert len(stored_final.messages) == 2


def test_concurrent_non_protected_metadata_change_is_merged_during_tool_loop(
    tmp_path: Path,
) -> None:
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
        app.save_session(
            Session(
                session_id=stored.session_id,
                messages=stored.messages,
                metadata={**stored.metadata, "pinned": True},
            )
        )
        updated = True

    assert updated, "expected to update pinned metadata after the tool checkpoint"
    assert not [ev for ev in events if ev.get("type") == "error"]

    stored_final = app.load_session_record(session.session_id)
    assert stored_final is not None
    assert stored_final.metadata["pinned"] is True


@pytest.mark.xfail(
    reason=(
        "Known unresolved append-and-send race: the older request detects the "
        "conflict, but the request started from the appended session does not."
    ),
    strict=True,
)
def test_cross_process_append_then_send_should_eventually_stop_both_requests(
    tmp_path: Path,
) -> None:
    """Known failing regression for the unresolved append-and-send race.

    Current behavior lets the request that appended a user message continue
    from the malformed history, while the older in-flight request notices the
    conflict and stops. A later fix should propagate that conflict so both
    competing requests stop.
    """

    config_path = _write_config(tmp_path)
    session_root = tmp_path / "sessions"
    app_a = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    app_b = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    _core, _base_config, created = _make_pending_tool_call_session(app_a)

    ctx_a = app_a.load_session(created.session_id)
    assert ctx_a is not None
    core_a, base_config_a, session_a = ctx_a
    events_a_iter = app_a.send_request(
        core_a, session_a, base_config_a, overrides=None, stream=False
    )
    events_a: List[Dict[str, Any]] = [next(events_a_iter)]
    assert events_a[0]["type"] == "request_started"

    stored_before_append = app_b.load_session_record(created.session_id)
    assert stored_before_append is not None
    appended = Session(
        session_id=stored_before_append.session_id,
        messages=[
            *stored_before_append.messages,
            type(stored_before_append.messages[0])(
                role="user",
                content="new user turn",
                metadata={},
            ),
        ],
        metadata=stored_before_append.metadata,
    )
    app_b.save_session(appended)

    ctx_b = app_b.load_session(created.session_id)
    assert ctx_b is not None
    core_b, base_config_b, session_b = ctx_b
    events_b = list(
        app_b.send_request(core_b, session_b, base_config_b, overrides=None, stream=False)
    )

    events_a.extend(list(events_a_iter))

    error_events_a = [ev for ev in events_a if ev.get("type") == "error"]
    assert error_events_a, "the older in-flight request should notice the appended message"

    error_events_b = [ev for ev in events_b if ev.get("type") == "error"]
    assert error_events_b, (
        "known gap: the request started from the appended session should also stop once the "
        "other request detects the conflict"
    )
