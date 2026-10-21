"""Application-level tests for background Claude compaction."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_app.operations import get_application_operation_service
from agent_app.request_execution import SessionOperationBusyError

from plugins.controllable_openai_test_provider import (
    release_controllable_openai_test_provider_call,
    reset_controllable_openai_test_provider_state,
    wait_for_controllable_openai_test_provider_call,
)

import claude_tools.claude_compaction_app as app_module
import claude_tools.claude_compaction_feature as feature_module
from agent_core import Session

_SUMMARY_BODY = "\n".join(
    [
        "1. Primary Request and Intent:",
        "  - Compact the seeded conversation.",
        "2. Key Technical Concepts:",
        "  - Background Claude compaction.",
        "3. Files and Code Sections:",
        "  - None.",
        "4. Errors and fixes:",
        "  - None.",
        "5. Problem Solving:",
        "  - None.",
        "6. All user messages:",
        "  - Seeded test messages.",
        "7. Pending Tasks:",
        "  - None.",
        "8. Current Work:",
        "  - Verifying background compaction.",
        "9. Optional Next Step:",
        "  - Assert the rewritten session.",
    ]
)
_COMPACTION_RESPONSE = (
    f"<analysis>ok</analysis>\n<summary>\n{_SUMMARY_BODY}\n</summary>"
)


def _wait_until(predicate: Any, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition did not become true")


class _FastHeartbeatProcess(app_module.ClaudeCompactionProcess):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(heartbeat_interval=0.02, **kwargs)


@pytest.fixture(autouse=True)
def _fast_heartbeat(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(app_module, "ClaudeCompactionProcess", _FastHeartbeatProcess)


def _make_config(
    tmp_path: Path,
    *,
    provider: str = "controlled",
    provider_overrides: Dict[str, Any] | None = None,
    include_feature: bool = True,
) -> Path:
    if provider == "echo":
        provider_entry = {"provider": "echo_openai_like", "model": "test-model"}
        provider_plugin = "plugins.echo_openai_like_provider.EchoOpenAILikeProvider"
    else:
        provider_entry = {
            "provider": "controllable_openai_test_provider",
            "model": "test-model",
            "response_text": _COMPACTION_RESPONSE,
            **(provider_overrides or {}),
        }
        provider_plugin = (
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider"
        )
    plugins = [provider_plugin]
    if include_feature:
        plugins.append("claude_tools.claude_compaction_feature.ClaudeCompactionFeature")
    plugins.append("claude_tools.claude_compaction_app.ClaudeCompactionAppPlugin")
    cfg: Dict[str, Any] = {
        "providers": {provider: provider_entry},
        "plugins": plugins,
        "agents": {"default": {"provider": provider}},
        "application": {},
    }
    path = tmp_path / f"config_claude_compaction_app_{provider}.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path,
    *,
    provider: str = "controlled",
    provider_overrides: Dict[str, Any] | None = None,
    include_feature: bool = True,
    session_dir: str = "sessions",
) -> AgentApplication:
    return AgentApplication(
        str(
            _make_config(
                tmp_path,
                provider=provider,
                provider_overrides=provider_overrides,
                include_feature=include_feature,
            )
        ),
        str(tmp_path / session_dir),
        event_store=InMemoryEventStore(),
    )


def _seed_session(app: AgentApplication) -> str:
    core, base_config, session = app.create_session("default")
    for role, text in [
        ("user", "ONE"),
        ("assistant", "one"),
        ("user", "TWO"),
        ("assistant", "two"),
        ("user", "THREE"),
        ("assistant", "three"),
    ]:
        session = core.add_message(session, role, text, config=base_config)
    app.save_session(session)
    return session.session_id


def _start(app: AgentApplication, session_id: str, **params: Any) -> Dict[str, Any]:
    return app.execute_application_action(
        plugin_id="claude_compaction_app",
        action_id="compact_conversation",
        params={"session_id": session_id, **params},
    )


def _wait_for_operation_done(app: AgentApplication, operation_id: str) -> None:
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            operation_id
        )
        is None
    )


def _latest_notification(app: AgentApplication, session_id: str) -> Dict[str, Any]:
    notifications = app.list_session_notifications(session_id)
    assert notifications, "expected at least one session notification"
    return notifications[0]


def _loaded(app: AgentApplication, session_id: str) -> Session:
    loaded = app.load_session_record(session_id)
    assert loaded is not None
    return loaded


def test_background_compaction_rewrites_session_and_completes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _build_app(tmp_path, provider="echo")

    def _fake_run_compaction_request(
        core: Any,
        session: Session,
        config: Dict[str, Any],
        context: Dict[str, Any] | None = None,
    ) -> str:
        _ = core, session, config, context
        return _COMPACTION_RESPONSE

    monkeypatch.setattr(
        feature_module,
        "_run_compaction_request",
        _fake_run_compaction_request,
        raising=True,
    )
    session_id = _seed_session(app)

    result = _start(app, session_id, start=1, end=5)

    assert result["status"] == "ok"
    assert result["operation_status"] == "accepted"
    assert result["operation_id"].startswith("claude_compaction:")
    assert result["notification_id"]
    _wait_for_operation_done(app, result["operation_id"])

    loaded = _loaded(app, session_id)
    contents = [message.content for message in loaded.messages]
    assert contents[0] == "ONE"
    assert contents[1].startswith("This session is being continued")
    assert contents[2].startswith("<local-command-caveat>")
    assert contents[3] == "No response requested."
    assert contents[4:] == ["three"]

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "success"
    assert notification["title"] == "Compaction complete"
    assert notification["operation"]["state"] == "succeeded"
    assert notification["operation"]["type"] == "claude_compaction"
    assert notification["ui_effects"] == {"reload_session_ids": [session_id]}

    snapshots = app.list_session_snapshots(session_id)
    assert len(snapshots) == 1
    assert snapshots[0].reason == "Before compacting conversation"
    assert snapshots[0].metadata["plugin"] == "claude_compaction_app"
    assert snapshots[0].metadata["operation_id"] == result["operation_id"]

    metadata = loaded.metadata.get("claude_compaction")
    assert isinstance(metadata, dict)
    assert metadata["compacted"] is True
    app.close()


def test_background_compaction_publishes_heartbeats_and_blocks_concurrent_requests(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_overrides={
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        session_dir="sessions_blocked",
    )
    session_id = _seed_session(app)

    result = _start(app, session_id)
    assert result["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)
    _wait_until(
        lambda: "Elapsed:" in _latest_notification(app, session_id).get("body", "")
    )
    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "warning"
    assert notification["key"] == "claude_tools:compaction"
    assert notification["operation"]["phase"] == "waiting_for_model"
    cancel_action = notification["display"]["actions"][0]
    assert cancel_action["action_id"] == "cancel_claude_compaction"
    assert cancel_action["label"] == "Cancel compaction"
    assert cancel_action["fixed_params"] == {
        "session_id": session_id,
        "operation_id": result["operation_id"],
    }

    operations = get_application_operation_service(app.get_runtime_store()).list_active(
        session_id=session_id
    )
    assert len(operations) == 1
    assert operations[0].owner_id == "claude_compaction_app"

    with pytest.raises(SessionOperationBusyError):
        app.start_session_request(session_id)

    release_controllable_openai_test_provider_call()
    _wait_for_operation_done(app, result["operation_id"])

    completed = _latest_notification(app, session_id)
    assert completed["severity"] == "success"
    assert completed["operation"]["state"] == "succeeded"
    app.close()


def test_cancel_during_model_request_leaves_session_unchanged(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_overrides={
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        session_dir="sessions_cancel",
    )
    session_id = _seed_session(app)

    result = _start(app, session_id, start=1, end=5)
    assert wait_for_controllable_openai_test_provider_call(2.0)

    cancel_result = app.execute_application_action(
        plugin_id="claude_compaction_app",
        action_id="cancel_claude_compaction",
        params={
            "session_id": session_id,
            "operation_id": result["operation_id"],
        },
    )
    assert cancel_result["status"] == "ok"
    assert cancel_result["operation_status"] == "cancellation_requested"

    release_controllable_openai_test_provider_call()
    _wait_for_operation_done(app, result["operation_id"])

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "warning"
    assert notification["title"] == "Compaction cancelled"
    assert notification["operation"]["state"] == "cancelled"

    loaded = _loaded(app, session_id)
    assert [message.content for message in loaded.messages] == [
        "ONE",
        "one",
        "TWO",
        "two",
        "THREE",
        "three",
    ]
    assert app.list_session_snapshots(session_id) == []
    app.close()


def test_failed_summary_notification_when_response_has_no_summary_block(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_overrides={"response_text": "no summary block here"},
        session_dir="sessions_failed",
    )
    session_id = _seed_session(app)

    result = _start(app, session_id, start=1, end=5)
    assert result["status"] == "ok"
    _wait_for_operation_done(app, result["operation_id"])

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "error"
    assert notification["title"] == "Compaction failed"
    assert "missing <summary> block" in notification["body"]
    assert notification["operation"]["state"] == "failed"
    retry_action = notification["display"]["actions"][0]
    assert retry_action["action_id"] == "compact_conversation"
    assert retry_action["id"] == "retry"

    loaded = _loaded(app, session_id)
    assert [message.content for message in loaded.messages] == [
        "ONE",
        "one",
        "TWO",
        "two",
        "THREE",
        "three",
    ]
    app.close()


def test_busy_session_returns_error_envelope(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_overrides={
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        session_dir="sessions_busy",
    )
    session_id = _seed_session(app)

    first = _start(app, session_id)
    assert first["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)

    second = _start(app, session_id)
    assert second["status"] == "error"
    assert second["error_type"] == "session_busy"
    assert second["operation"]["operation_id"] == first["operation_id"]

    release_controllable_openai_test_provider_call()
    _wait_for_operation_done(app, first["operation_id"])
    app.close()


def test_concurrent_session_change_fails_without_overwriting(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_overrides={
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        session_dir="sessions_conflict",
    )
    session_id = _seed_session(app)

    result = _start(app, session_id, start=1, end=5)
    assert result["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)

    ctx = app.load_session(session_id)
    assert ctx is not None
    core_live, base_live, live_session = ctx
    advanced = core_live.add_message(
        live_session,
        "user",
        "concurrent edit",
        config=base_live,
    )
    app.save_session(advanced, acquire_lock=True)

    release_controllable_openai_test_provider_call()
    _wait_for_operation_done(app, result["operation_id"])

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "error"
    assert notification["title"] == "Compaction failed"
    assert "Concurrent session modification detected while compacting" in (
        notification["body"]
    )

    loaded = _loaded(app, session_id)
    assert [message.content for message in loaded.messages] == [
        "ONE",
        "one",
        "TWO",
        "two",
        "THREE",
        "three",
        "concurrent edit",
    ]
    assert app.list_session_snapshots(session_id) == []
    app.close()


def test_start_validates_message_count_and_range(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path, session_dir="sessions_validation")

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "one", config=base_config)
    app.save_session(session)

    with pytest.raises(ValueError, match="Not enough messages to compact"):
        _start(app, session.session_id)

    session_id = _seed_session(app)
    with pytest.raises(ValueError, match="range selects no messages"):
        _start(app, session_id, start=4, end=1)
    app.close()


def test_start_rejects_sessions_without_the_feature(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path, include_feature=False, session_dir="sessions_nofeature")
    core, base_config, session = app.create_session("default")
    for role, text in [
        ("user", "ONE"),
        ("assistant", "one"),
        ("user", "TWO"),
    ]:
        session = core.add_message(session, role, text, config=base_config)
    app.save_session(session)

    with pytest.raises(RuntimeError, match="Claude compaction is not available"):
        _start(app, session.session_id)
    app.close()


def test_cancel_reports_missing_operation(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path, session_dir="sessions_cancel_missing")
    session_id = _seed_session(app)

    result = app.execute_application_action(
        plugin_id="claude_compaction_app",
        action_id="cancel_claude_compaction",
        params={
            "session_id": session_id,
            "operation_id": "claude_compaction:does-not-exist",
        },
    )
    assert result["status"] == "error"
    assert result["error_type"] == "operation_not_found"
    app.close()


def test_application_close_interrupts_running_process(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_overrides={
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        session_dir="sessions_interrupt",
    )
    session_id = _seed_session(app)

    result = _start(app, session_id)
    assert result["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)

    app.close()

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "warning"
    assert notification["title"] == "Compaction interrupted"
    assert notification["operation"]["state"] == "interrupted"

    release_controllable_openai_test_provider_call()

    loaded = _loaded(app, session_id)
    assert [message.content for message in loaded.messages] == [
        "ONE",
        "one",
        "TWO",
        "two",
        "THREE",
        "three",
    ]


def test_session_ui_uses_application_owned_background_actions(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path, session_dir="sessions_ui")
    session_id = _seed_session(app)

    schema = app.get_session_application_ui_schema(session_id)

    compact = next(item for item in schema if item.get("id") == "compact_conversation")
    assert compact["plugin"] == "claude_compaction_app"
    assert compact["action_owner"] == "application"
    assert compact["ui_type"] == "session_action"

    through_message = next(
        item for item in schema if item.get("id") == "compact_up_to_here"
    )
    assert through_message["ui_type"] == "message_action"
    assert through_message["action_owner"] == "application"
    assert through_message["fixed_params"] == {"start": 0, "end_inclusive": True}
    app.close()


def test_session_ui_omits_actions_without_the_feature(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path, include_feature=False, session_dir="sessions_ui_off")
    session_id = _seed_session(app)

    schema = app.get_session_application_ui_schema(session_id)

    assert not any(item.get("plugin") == "claude_compaction_app" for item in schema)
    app.close()
