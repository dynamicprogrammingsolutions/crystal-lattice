"""Unit tests for :mod:`summarize_range_app` application plugin."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any, Dict, List

import json
import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_app.operations import get_application_operation_service
from agent_app.request_execution import SessionOperationBusyError

from plugins.controllable_openai_test_provider import (
    get_controllable_openai_test_provider_state,
    release_controllable_openai_test_provider_call,
    reset_controllable_openai_test_provider_state,
    wait_for_controllable_openai_test_provider_call,
)

import summarize_range_app as plugin_module
from summarize_range_app import SummarizeRangeAppPlugin  # noqa: F401


def _wait_until(predicate: Any, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition did not become true")


def _get_mutations(result: Dict[str, Any]) -> Dict[str, Any]:
    mutations = result.get("mutations")
    return mutations if isinstance(mutations, dict) else {}


def _make_config_with_summarize_range(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
    extra_plugins: List[str] | None = None,
    filename: str = "config_summarize_range.json",
) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "controlled": {
                "provider": "controllable_openai_test_provider",
                "model": "test-model",
                **dict(provider_config or {}),
            }
        },
        "plugins": [
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
            *(extra_plugins or []),
            "summarize_range_app.SummarizeRangeAppPlugin",
        ],
        "agents": {
            "default": {"provider": "controlled"},
        },
        "application": {
            "summarize_range_agent_id": "default",
            "summarize_range_prompt": "Summarize this range succinctly.",
            **dict(application_config or {}),
        },
    }

    path = tmp_path / filename
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
    extra_plugins: List[str] | None = None,
    filename: str = "config_summarize_range.json",
    session_dir: str = "sessions",
) -> AgentApplication:
    config_path = _make_config_with_summarize_range(
        tmp_path,
        provider_config=provider_config,
        application_config=application_config,
        extra_plugins=extra_plugins,
        filename=filename,
    )
    session_root = tmp_path / session_dir
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    core, base_config, session = app.create_session("default")

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def _start(app: AgentApplication, session_id: str, **params: Any) -> Dict[str, Any]:
    return app.execute_application_action(
        plugin_id="summarize_range",
        action_id="summarize_range",
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


def _loaded_messages(app: AgentApplication, session_id: str) -> List[Any]:
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx
    return session.messages


def _build_asset_expanding_app(tmp_path: Path) -> AgentApplication:
    """App whose provider expands session assets during native rebuilds."""

    cfg: Dict[str, Any] = {
        "providers": {
            "assets": {
                "provider": "asset_expanding_test_provider",
                "model": "test-model",
                "response_text": "Summary of the range.",
            }
        },
        "plugins": [
            "asset_expanding_test_provider.AssetExpandingTestProvider",
            "summarize_range_app.SummarizeRangeAppPlugin",
        ],
        "agents": {"default": {"provider": "assets"}},
        "application": {
            "summarize_range_agent_id": "default",
            "summarize_range_prompt": "Summarize this range succinctly.",
        },
    }
    path = tmp_path / "config_asset_expanding.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return AgentApplication(
        str(path), str(tmp_path / "sessions_asset"), event_store=InMemoryEventStore()
    )


class _FastHeartbeatProcess(plugin_module.SummarizeRangeProcess):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(heartbeat_interval=0.02, **kwargs)


@pytest.fixture(autouse=True)
def _fast_heartbeat(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(plugin_module, "SummarizeRangeProcess", _FastHeartbeatProcess)


def test_summarize_range_replaces_range_with_single_message(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Range summary"},
    )

    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = _start(app, session_id, start=1, end=3)

    assert result["status"] == "ok"
    assert result["operation_status"] == "accepted"
    assert result["operation_id"].startswith("summarize_range:")
    assert result["notification_id"]
    _wait_for_operation_done(app, result["operation_id"])

    messages = _loaded_messages(app, session_id)
    assert len(messages) == 3
    assert [m.content for m in messages] == [
        "m0",
        "Range summary",
        "m3",
    ]
    assert messages[1].role == "assistant"

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "success"
    assert notification["title"] == "Summarization complete"
    assert notification["operation"]["state"] == "succeeded"
    assert notification["ui_effects"] == {"reload_session_ids": [session_id]}
    app.close()


def test_background_action_publishes_heartbeats_and_blocks_concurrent_requests(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={
            "response_text": "Blocked summary",
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        filename="config_summarize_range_blocked.json",
        session_dir="sessions_blocked",
    )
    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = _start(app, session_id, start=1, end=3)

    assert result["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)
    _wait_until(
        lambda: "Elapsed:" in _latest_notification(app, session_id).get("body", "")
    )
    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "warning"
    assert notification["display"]["variant"] == "warning"
    assert notification["display"]["presentation"] == "banner"
    assert notification["display"]["dismissible"] is True
    assert notification["key"] == "summarize_range:range_summarization"
    cancel_action = notification["display"]["actions"][0]
    assert cancel_action["action_id"] == "cancel_summarize_range"
    assert cancel_action["label"] == "Cancel summarization"
    assert cancel_action["fixed_params"] == {
        "session_id": session_id,
        "operation_id": result["operation_id"],
    }
    assert notification["operation"]["id"] == result["operation_id"]
    assert notification["operation"]["phase"] == "waiting_for_model"

    operations = get_application_operation_service(app.get_runtime_store()).list_active(
        session_id=session_id
    )
    assert len(operations) == 1
    assert operations[0].owner_id == "summarize_range"
    assert operations[0].operation_id == result["operation_id"]

    with pytest.raises(SessionOperationBusyError):
        app.start_session_request(session_id)

    release_controllable_openai_test_provider_call()
    _wait_for_operation_done(app, result["operation_id"])

    snapshots = app.list_session_snapshots(session_id)
    assert len(snapshots) == 1
    assert snapshots[0].reason == "Before summarizing messages [1:3]"
    assert snapshots[0].metadata == {
        "origin": "automatic",
        "plugin": "summarize_range",
        "action": "summarize_range",
        "operation_id": result["operation_id"],
        "range": {"start": 1, "end": 3},
    }

    completed = _latest_notification(app, session_id)
    assert completed["status"] == "pending"
    assert completed["severity"] == "success"
    assert completed["operation"]["state"] == "succeeded"
    assert completed["ui_effects"] == {"reload_session_ids": [session_id]}

    assert [m.content for m in _loaded_messages(app, session_id)] == [
        "m0",
        "Blocked summary",
        "m3",
    ]
    app.close()


def test_summarize_before_message_ui_action_is_inclusive() -> None:
    plugin = SummarizeRangeAppPlugin()
    plugin.init({"application": {}})

    elements = plugin.get_ui_elements(plugin._state)
    action = next(el for el in elements if el.get("id") == "summarize_before_message")

    assert action["ui_type"] == "message_action"
    assert action["action_owner"] == "application"
    assert action["fixed_params"]["start"] == 0
    assert action["fixed_params"]["end_inclusive"] is True
    assert action["param_map"]["end"] == "$message.index"


def test_end_inclusive_replaces_selected_message_too(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Inclusive summary"},
        filename="config_summarize_range_inclusive.json",
        session_dir="sessions_inclusive",
    )

    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = _start(app, session_id, start=0, end=2, end_inclusive=True)
    _wait_for_operation_done(app, result["operation_id"])

    messages = _loaded_messages(app, session_id)
    assert [m.content for m in messages] == [
        "Inclusive summary",
        "m3",
    ]
    assert messages[0].role == "assistant"
    app.close()


def test_prompt_input_overrides_config_default(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_mode": "echo_last_user"},
        filename="config_summarize_range_echo.json",
        session_dir="sessions_echo",
    )

    session_id = _create_session_with_messages(app, ["hello", "world"])
    custom_prompt = "Custom summarization prompt"

    result = _start(app, session_id, start=0, end=2, prompt=custom_prompt)
    _wait_for_operation_done(app, result["operation_id"])

    messages = _loaded_messages(app, session_id)
    assert len(messages) == 1
    assert messages[0].role == "assistant"
    assert custom_prompt in str(messages[0].content)
    app.close()


def test_summarize_range_internal_request_disables_tools_with_real_app(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Condensed summary"},
        application_config={
            "summarize_range_settings_overrides": {
                "request_options": {"temperature": 0.4},
            }
        },
        extra_plugins=[
            "plugins.openai_tools_extension.OpenAIToolsExtension",
            "plugins.request_options_feature.RequestOptionsFeature",
            "plugins.tool_gating_feature.ToolGatingFeature",
            "plugins.math_tools.MathTools",
        ],
        filename="config_summarize_range_tools.json",
        session_dir="sessions_tools",
    )

    session_id = _create_session_with_messages(app, ["First message", "Second message"])

    result = _start(
        app,
        session_id,
        start=0,
        end=2,
        prompt="Use this custom summarize prompt.",
    )
    _wait_for_operation_done(app, result["operation_id"])

    messages = _loaded_messages(app, session_id)
    provider_state = get_controllable_openai_test_provider_state()

    assert len(messages) == 1
    assert messages[0].content == "Condensed summary"
    assert provider_state["payload"] == {
        "model": "test-model",
        "temperature": 0.4,
    }
    assert provider_state["last_user_message"] == "Use this custom summarize prompt."
    app.close()


def test_failed_notification_when_no_assistant_reply(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_mode": "none"},
        filename="config_summarize_range_no_reply.json",
        session_dir="sessions_no_reply",
    )

    session_id = _create_session_with_messages(app, ["one", "two"])

    result = _start(app, session_id, start=0, end=2)
    assert result["status"] == "ok"
    _wait_for_operation_done(app, result["operation_id"])

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "error"
    assert notification["title"] == "Summarization failed"
    assert "no assistant reply" in notification["body"]
    assert notification["operation"]["state"] == "failed"
    retry_action = notification["display"]["actions"][0]
    assert retry_action["action_id"] == "summarize_range"
    assert retry_action["id"] == "retry"

    assert [m.content for m in _loaded_messages(app, session_id)] == ["one", "two"]
    app.close()


def test_cancel_during_provider_request_leaves_session_unchanged(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={
            "response_text": "Cancelled summary",
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        filename="config_summarize_range_cancel.json",
        session_dir="sessions_cancel",
    )
    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = _start(app, session_id, start=1, end=3)
    assert wait_for_controllable_openai_test_provider_call(2.0)

    cancel_result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="cancel_summarize_range",
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
    assert notification["title"] == "Summarization cancelled"
    assert notification["operation"]["state"] == "cancelled"

    assert [m.content for m in _loaded_messages(app, session_id)] == [
        "m0",
        "m1",
        "m2",
        "m3",
    ]
    assert app.list_session_snapshots(session_id) == []
    app.close()


def test_cancel_reports_missing_operation(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        filename="config_summarize_range_cancel_missing.json",
        session_dir="sessions_cancel_missing",
    )
    session_id = _create_session_with_messages(app, ["m0", "m1"])

    result = app.execute_application_action(
        plugin_id="summarize_range",
        action_id="cancel_summarize_range",
        params={
            "session_id": session_id,
            "operation_id": "summarize_range:does-not-exist",
        },
    )
    assert result["status"] == "error"
    assert result["error_type"] == "operation_not_found"
    app.close()


def test_busy_session_returns_error_envelope(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={
            "response_text": "First summary",
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        filename="config_summarize_range_busy.json",
        session_dir="sessions_busy",
    )
    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    first = _start(app, session_id, start=1, end=3)
    assert first["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)

    second = _start(app, session_id, start=0, end=2)
    assert second["status"] == "error"
    assert second["error_type"] == "session_busy"
    assert second["operation"]["operation_id"] == first["operation_id"]

    release_controllable_openai_test_provider_call()
    _wait_for_operation_done(app, first["operation_id"])
    app.close()


def test_validation_error_bubbles_synchronously(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        filename="config_summarize_range_validation.json",
        session_dir="sessions_validation",
    )
    session_id = _create_session_with_messages(app, ["one", "two"])

    with pytest.raises(Exception):
        _start(app, session_id, start=5, end=1)
    app.close()


def test_summarize_range_conflicts_when_session_changes_mid_action(
    tmp_path: Path,
) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={
            "response_text": "summary output",
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        filename="config_summarize_range_conflict.json",
        session_dir="sessions_conflict",
    )
    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = _start(app, session_id, start=1, end=3)
    assert result["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)

    ctx = app.load_session(session_id)
    assert ctx is not None
    core_live, base_live, live_session = ctx
    advanced = core_live.add_message(
        live_session,
        "user",
        "concurrent edit",
        None,
        base_live,
    )
    app.save_session(advanced, acquire_lock=True)

    release_controllable_openai_test_provider_call()
    _wait_for_operation_done(app, result["operation_id"])

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "error"
    assert notification["title"] == "Summarization failed"
    assert "Concurrent session modification detected while summarizing messages" in (
        notification["body"]
    )

    assert [msg.content for msg in _loaded_messages(app, session_id)] == [
        "m0",
        "m1",
        "m2",
        "m3",
        "concurrent edit",
    ]
    assert app.list_session_snapshots(session_id) == []
    app.close()


def test_application_close_interrupts_running_process(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={
            "response_text": "Interrupted summary",
            "block_until_released": True,
            "block_wait_timeout": 5.0,
        },
        filename="config_summarize_range_interrupt.json",
        session_dir="sessions_interrupt",
    )
    session_id = _create_session_with_messages(app, ["m0", "m1", "m2", "m3"])

    result = _start(app, session_id, start=1, end=3)
    assert result["status"] == "ok"
    assert wait_for_controllable_openai_test_provider_call(2.0)

    app.close()

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "warning"
    assert notification["title"] == "Summarization interrupted"
    assert notification["operation"]["state"] == "interrupted"

    release_controllable_openai_test_provider_call()

    assert [m.content for m in _loaded_messages(app, session_id)] == [
        "m0",
        "m1",
        "m2",
        "m3",
    ]


def test_summarize_range_resolves_session_assets_during_rebuilds(
    tmp_path: Path,
) -> None:
    """Regression test: every native-history rebuild triggered by the
    background summarization must receive a context carrying
    ``session_asset_store``.

    Providers that expand session asset references during
    ``initialize_request`` (such as the OpenAI Responses provider) fail on
    rebuilds whose context lacks the store. Before the fix, both the
    prompt-append rebuild and the commit-phase rewrite rebuild failed with
    "session asset attachment requires session_asset_store in context".

    The deterministic fixture provider mirrors that contract without network
    access; the Ollama integration test covers the streaming leg only.
    """

    import base64

    from agent_core import Message, Session
    from agent_core.tool_result_payloads import (
        FORMAT_OPENAI_CHAT_COMPLETIONS,
        make_provider_native_tool_result,
    )

    app = _build_asset_expanding_app(tmp_path)
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    record = app.get_session_asset_store().store_base64(
        session_id=session_id,
        attachment_type="image",
        filename="test.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"fake-image").decode("ascii"),
    )
    asset_ref = {
        "kind": "session_asset",
        "session_id": session_id,
        "asset_id": record.asset_id,
        "attachment_type": "image",
    }
    tool_result = make_provider_native_tool_result(
        format=FORMAT_OPENAI_CHAT_COMPLETIONS,
        content=[
            {"type": "text", "text": "Tool result with image"},
            {"type": "image_url", "image_url": {"asset_ref": dict(asset_ref)}},
        ],
    )
    messages = [
        Message(role="user", content="Hello", metadata={"native_indices": [0]}),
        Message(
            role="tool",
            content="",
            metadata={
                "native_indices": [1],
                "tool_call_id": "tc1",
                "tool_name": "view_image",
            },
            tool_result=tool_result,
        ),
        Message(role="assistant", content="Done", metadata={"native_indices": [2]}),
    ]
    stored = Session(
        session_id=session_id,
        messages=messages,
        metadata={
            **session.metadata,
            "native_messages": [message.to_dict() for message in messages],
            "native_messages_integrity": core._compute_native_integrity(messages),
        },
    )
    app.save_session(stored)

    result = _start(app, session_id, start=0, end=3)
    assert result["status"] == "ok"
    assert result["operation_status"] == "accepted"
    _wait_for_operation_done(app, result["operation_id"])

    notification = _latest_notification(app, session_id)
    assert notification["severity"] == "success", notification.get("body")

    loaded = _loaded_messages(app, session_id)
    assert [(message.role, message.content) for message in loaded] == [
        ("assistant", "Summary of the range.")
    ]
    summary_metadata = loaded[0].metadata or {}
    assert summary_metadata["summarized_range"] == {
        "start_index": 0,
        "end_index": 3,
    }
    app.close()
