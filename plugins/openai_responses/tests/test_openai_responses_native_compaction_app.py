from __future__ import annotations

import base64
import concurrent.futures
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict

import pytest

from agent_app.application_future import AgentApplication
from agent_app.managed_processes import get_managed_process_registry
from agent_app.operations import get_application_operation_service
from agent_app.request_execution import SessionOperationBusyError
from agent_core import Message, Session
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
import openai_responses_plugins.openai_responses_native_compaction_app as app_module
import openai_responses_plugins.openai_responses_native_compaction_process as process_module


class _ControlledTransport:
    instances: list["_ControlledTransport"] = []
    result: Dict[str, Any] = {
        "id": "cmp_background",
        "output": [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "hello"}],
            },
            {
                "type": "compaction",
                "encrypted_content": "opaque",
            },
        ],
    }
    error: BaseException | None = None

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs.get("config")
        self.started = threading.Event()
        self.release = threading.Event()
        self.cancelled = threading.Event()
        self.calls: list[Dict[str, Any]] = []
        type(self).instances.append(self)

    def configure(self, config: Dict[str, Any]) -> None:
        self.config = config

    def compact(self, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append(kwargs)
        self.started.set()
        while not self.release.wait(0.01):
            if self.cancelled.is_set():
                raise concurrent.futures.CancelledError()
        if self.error is not None:
            raise self.error
        return self.result

    def cancel(self) -> None:
        self.cancelled.set()


class _FastHeartbeatProcess(process_module.OpenAIResponsesNativeCompactionProcess):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(heartbeat_interval=0.02, **kwargs)


def _wait_until(predicate: Any, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition did not become true")


@pytest.fixture(autouse=True)
def _controlled_transport(monkeypatch: pytest.MonkeyPatch):
    _ControlledTransport.instances = []
    _ControlledTransport.error = None
    monkeypatch.setattr(
        process_module,
        "CancellableAsyncOpenAIResponsesCompactionTransport",
        _ControlledTransport,
    )
    monkeypatch.setattr(
        app_module,
        "OpenAIResponsesNativeCompactionProcess",
        _FastHeartbeatProcess,
    )


def _build_app(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    provider_overrides: Dict[str, Any] | None = None,
    extra_plugins: list[str] | None = None,
) -> tuple[AgentApplication, str]:
    monkeypatch.setattr(OpenAIResponsesProvider, "get_models", lambda self, config: [])
    config = {
        "providers": {
            "openai_responses": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": "test-key",
                **(provider_overrides or {}),
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_native_compaction_extension.OpenAIResponsesNativeCompactionExtension",
            "openai_responses_plugins.openai_responses_native_compaction_app.OpenAIResponsesNativeCompactionAppPlugin",
            *(extra_plugins or []),
        ],
        "agents": {"default": {"provider": "openai_responses"}},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"))
    core, _base_config, session = app.create_session("default")
    messages = [Message(role="user", content="hello", metadata={"native_indices": [0]})]
    stored = Session(
        session_id=session.session_id,
        messages=messages,
        metadata={
            **session.metadata,
            "native_messages": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hello"}],
                }
            ],
            "native_messages_integrity": core._compute_native_integrity(messages),
        },
    )
    app.save_session(stored)
    return app, stored.session_id


def _start(app: AgentApplication, session_id: str) -> Dict[str, Any]:
    return app.execute_application_action(
        "openai_responses_native_compaction_app",
        "compact_native_history",
        {"session_id": session_id},
        context={"session_id": session_id},
    )


def _replace_history_with_asset_tool_result(
    app: AgentApplication,
    session_id: str,
) -> str:
    loaded = app.load_session(session_id)
    assert loaded is not None
    core, _base_config, session = loaded
    image_bytes = b"asset-backed-tool-image"
    record = app.get_session_asset_store().store_base64(
        session_id=session_id,
        attachment_type="image",
        filename="tool-image.png",
        mime_type="image/png",
        data_base64=base64.b64encode(image_bytes).decode("ascii"),
    )
    messages = [
        Message(
            role="tool",
            content="Loaded image file.",
            metadata={
                "native_indices": [0],
                "tool_call_id": "call_asset",
                "tool_name": "view_image",
            },
        )
    ]
    native_messages = [
        {
            "type": "function_call_output",
            "call_id": "call_asset",
            "output": [
                {"type": "input_text", "text": "Loaded image file."},
                {
                    "type": "input_image",
                    "image_url": {
                        "asset_ref": record.asset_ref(),
                        "filename": record.filename,
                        "mime_type": record.mime_type,
                    },
                },
            ],
        }
    ]
    app.save_session(
        Session(
            session_id=session_id,
            messages=messages,
            metadata={
                **session.metadata,
                "native_messages": native_messages,
                "native_messages_integrity": core._compute_native_integrity(messages),
            },
        )
    )
    return f"data:{record.mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def test_background_action_returns_promptly_and_publishes_heartbeats(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)

    result = _start(app, session_id)

    assert result["status"] == "ok"
    assert result["operation_status"] == "accepted"
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)
    _wait_until(
        lambda: (
            (app.list_session_notifications(session_id)[0].get("revision") or 0) >= 3
        )
    )
    notification = app.list_session_notifications(session_id)[0]
    assert notification["severity"] == "warning"
    assert notification["display"]["variant"] == "warning"
    assert notification["display"]["presentation"] == "banner"
    assert notification["display"]["dismissible"] is True
    assert notification["key"] == "openai_responses:native_compaction"
    assert "Elapsed:" in notification["body"]
    assert notification["display"]["actions"][0]["action_id"] == (
        "cancel_native_compaction"
    )
    assert notification["display"]["actions"][0]["label"] == "Cancel compaction"
    assert notification["operation"]["id"] == result["operation_id"]

    operations = get_application_operation_service(app.get_runtime_store()).list_active(
        session_id=session_id
    )
    assert len(operations) == 1
    assert operations[0].owner_id == "openai_responses_native_compaction_app"
    assert operations[0].operation_id == result["operation_id"]

    with pytest.raises(SessionOperationBusyError):
        app.start_session_request(session_id)

    transport.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    saved = app.load_live_session_record(session_id)
    assert saved is not None
    native_messages = saved.metadata.get("native_messages")
    assert isinstance(native_messages, list)
    assert native_messages[-1]["type"] == "compaction"
    snapshots = app.list_session_snapshots(session_id)
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.reason == "Before compacting conversation [:1]"
    assert snapshot.metadata == {
        "origin": "automatic",
        "plugin": "openai_responses_native_compaction_app",
        "action": "compact_native_history",
        "operation_id": result["operation_id"],
        "range": {"start": 0, "end": 1},
    }
    completed_notification = app.list_session_notifications(session_id)[0]
    assert completed_notification["status"] == "pending"
    assert completed_notification["severity"] == "success"
    assert completed_notification["display"]["variant"] == "success"
    assert completed_notification["display"]["presentation"] == "banner"
    assert completed_notification["display"]["dismissible"] is True
    assert completed_notification["title"] == "Native compaction complete"
    assert completed_notification["ui_effects"] == {"reload_session_ids": [session_id]}
    restored = app.restore_session_snapshot(session_id, snapshot.snapshot_id)
    assert restored.metadata["native_messages"] == [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hello"}],
        }
    ]
    restored_notification = app.list_session_notifications(session_id)[0]
    assert restored_notification["id"] == completed_notification["id"]
    assert restored_notification["severity"] == "success"
    app.close()


def test_background_action_resolves_asset_backed_tool_result_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)
    expected_data_url = _replace_history_with_asset_tool_result(app, session_id)

    result = _start(app, session_id)

    assert result["status"] == "ok"
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)
    assert len(transport.calls) == 1
    input_items = transport.calls[0]["input_items"]
    assert "asset_ref" not in repr(input_items)
    assert input_items[0]["output"][1]["image_url"] == expected_data_url

    transport.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    saved = app.load_live_session_record(session_id)
    assert saved is not None
    assert saved.metadata["native_messages"][-1]["type"] == "compaction"
    assert app.list_session_notifications(session_id)[0]["severity"] == "success"
    app.close()


@pytest.mark.parametrize("auth_mode", ["chatgpt", "auto"])
def test_background_action_binds_saved_chatgpt_login_to_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    auth_mode: str,
) -> None:
    credentials_path = tmp_path / "chatgpt-auth.json"
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "saved-chatgpt-token",
                "account_id": "acct_saved",
                "token_type": "Bearer",
            }
        ),
        encoding="utf-8",
    )
    chatgpt_base_url = "https://chatgpt.example/backend-api/codex"
    app, session_id = _build_app(
        tmp_path,
        monkeypatch,
        provider_overrides={
            "auth_mode": auth_mode,
            "chatgpt_credentials_path": str(credentials_path),
            "chatgpt_base_url": chatgpt_base_url,
        },
        extra_plugins=[
            "openai_responses_plugins.openai_responses_chatgpt_auth_feature.OpenAIResponsesChatGPTAuthFeature"
        ],
    )

    result = _start(app, session_id)

    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)
    assert transport.config["auth_mode"] == auth_mode
    assert transport.config["_openai_responses_effective_auth_mode"] == "chatgpt"
    assert transport.config["base_url"] == chatgpt_base_url
    assert transport.config["chatgpt_access_token"] == "saved-chatgpt-token"
    assert transport.config["chatgpt_account_id"] == "acct_saved"

    transport.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    assert app.list_session_notifications(session_id)[0]["severity"] == "success"
    app.close()


def test_background_action_binds_forced_api_compaction_config_to_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials_path = tmp_path / "chatgpt-auth.json"
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "saved-chatgpt-token",
                "account_id": "acct_saved",
                "token_type": "Bearer",
            }
        ),
        encoding="utf-8",
    )
    api_base_url = "https://api.example/v1"
    app, session_id = _build_app(
        tmp_path,
        monkeypatch,
        provider_overrides={
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
            "chatgpt_base_url": "https://chatgpt.example/backend-api/codex",
            "api_base_url": api_base_url,
            "use_chatgpt_auth_for_compaction": False,
        },
        extra_plugins=[
            "openai_responses_plugins.openai_responses_chatgpt_auth_feature.OpenAIResponsesChatGPTAuthFeature"
        ],
    )

    result = _start(app, session_id)

    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)
    assert transport.config["auth_mode"] == "api"
    assert transport.config["_openai_responses_effective_auth_mode"] == "api"
    assert transport.config["base_url"] == api_base_url
    assert "chatgpt_access_token" not in transport.config
    assert "chatgpt_account_id" not in transport.config

    transport.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    assert app.list_session_notifications(session_id)[0]["severity"] == "success"
    app.close()


def test_cancel_action_interrupts_transport_and_discards_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)
    baseline = app.load_live_session_record(session_id)
    assert baseline is not None
    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)

    cancelled = app.execute_application_action(
        "openai_responses_native_compaction_app",
        "cancel_native_compaction",
        {
            "session_id": session_id,
            "operation_id": result["operation_id"],
        },
        context={"session_id": session_id},
    )

    assert cancelled["status"] == "ok"
    assert cancelled["operation_status"] == "cancellation_requested"
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    assert transport.cancelled.is_set()
    current = app.load_live_session_record(session_id)
    assert current is not None
    assert current.messages == baseline.messages
    assert current.metadata["native_messages"] == baseline.metadata["native_messages"]
    assert app.list_session_snapshots(session_id) == []
    notification = app.list_session_notifications(session_id)[0]
    assert notification["status"] == "pending"
    assert notification["severity"] == "warning"
    assert notification["display"]["variant"] == "warning"
    assert notification["display"]["presentation"] == "banner"
    assert notification["display"]["dismissible"] is True
    assert "ui_effects" not in notification
    app.close()


def test_provider_failure_keeps_persistent_retry_notification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ControlledTransport.error = RuntimeError("provider unavailable")
    app, session_id = _build_app(tmp_path, monkeypatch)
    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)
    transport.release.set()

    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    notification = app.list_session_notifications(session_id)[0]
    assert notification["status"] == "pending"
    assert notification["severity"] == "error"
    assert notification["display"]["variant"] == "error"
    assert notification["display"]["presentation"] == "banner"
    assert notification["display"]["dismissible"] is True
    assert notification["display"]["actions"][0]["action_id"] == (
        "compact_native_history"
    )
    assert "ui_effects" not in notification
    assert app.list_session_snapshots(session_id) == []
    app.close()


def test_atomic_send_during_compaction_does_not_append_or_break_compaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)
    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)

    with pytest.raises(SessionOperationBusyError):
        app.start_session_request_with_message(
            session_id,
            role="user",
            content="must not be appended",
        )

    current = app.load_live_session_record(session_id)
    assert current is not None
    assert [message.content for message in current.messages] == ["hello"]

    transport.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    saved = app.load_live_session_record(session_id)
    assert saved is not None
    assert [message.content for message in saved.messages] == ["hello"]
    assert saved.metadata["native_messages"][-1]["type"] == "compaction"
    assert app.list_session_notifications(session_id)[0]["severity"] == "success"
    app.close()


def test_concurrent_history_change_fails_without_overwriting_current_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)
    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)

    core, _base_config, current = app.load_session(session_id)  # type: ignore[misc]
    messages = [
        *current.messages,
        Message(role="user", content="new turn", metadata={"native_indices": [1]}),
    ]
    native_messages = [
        *current.metadata["native_messages"],
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "new turn"}],
        },
    ]
    app.save_session(
        Session(
            session_id=session_id,
            messages=messages,
            metadata={
                **current.metadata,
                "native_messages": native_messages,
                "native_messages_integrity": core._compute_native_integrity(messages),
            },
        )
    )
    transport.release.set()

    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    saved = app.load_live_session_record(session_id)
    assert saved is not None
    assert [message.content for message in saved.messages] == ["hello", "new turn"]
    assert app.list_session_notifications(session_id)[0]["severity"] == "error"
    assert app.list_session_snapshots(session_id) == []
    app.close()


def test_failed_compaction_save_removes_provisional_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)
    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)

    original_save = app.save_session

    def fail_compaction_save(session: Session, *args: Any, **kwargs: Any) -> Any:
        native_messages = (
            session.metadata.get("native_messages")
            if isinstance(session.metadata, dict)
            else None
        )
        if (
            isinstance(native_messages, list)
            and native_messages
            and isinstance(native_messages[-1], dict)
            and native_messages[-1].get("type") == "compaction"
        ):
            raise RuntimeError("save failed")
        return original_save(session, *args, **kwargs)

    monkeypatch.setattr(app, "save_session", fail_compaction_save)
    transport.release.set()

    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    assert app.list_session_snapshots(session_id) == []
    assert app.list_session_notifications(session_id)[0]["severity"] == "error"
    app.close()


def test_application_close_interrupts_compaction_and_cancels_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)
    operations = get_application_operation_service(app.get_runtime_store())
    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)

    app.close()

    assert operations.get(result["operation_id"]) is None
    assert transport.cancelled.is_set()


def test_session_ui_uses_application_owned_background_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)

    schema = app.get_session_application_ui_schema(session_id)

    compaction = next(
        item for item in schema if item.get("id") == "compact_native_history"
    )
    assert compaction["plugin"] == "openai_responses_native_compaction_app"
    assert compaction["action_owner"] == "application"

    through_message = next(
        item
        for item in schema
        if item.get("id") == "compact_native_history_through_message"
    )
    assert through_message["ui_type"] == "message_action"
    assert through_message["label"] == "OpenAI compaction up to here"
    assert through_message["dialog"]["title"] == "OpenAI compaction up to here"
    assert through_message["order"] == 25
    assert through_message["action_id"] == "compact_native_history"
    assert through_message["action_owner"] == "application"
    assert through_message["param_map"] == {
        "session_id": "$session.session_id",
        "message_index": "$message.index",
    }
    app.close()


def test_message_action_compacts_through_selected_visible_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)

    result = app.execute_application_action(
        "openai_responses_native_compaction_app",
        "compact_native_history",
        {"session_id": session_id, "message_index": 0},
        context={"session_id": session_id},
    )

    process = get_managed_process_registry(app.get_runtime_store()).get(
        result["operation_id"]
    )
    assert isinstance(process, process_module.OpenAIResponsesNativeCompactionProcess)
    assert process._end_index == 1

    _ControlledTransport.instances[0].release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    app.close()


@pytest.mark.parametrize("message_index", [-1, 1])
def test_message_action_rejects_invalid_visible_message_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    message_index: Any,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)

    with pytest.raises(
        ValueError, match="message_index must identify a visible session message"
    ):
        app.execute_application_action(
            "openai_responses_native_compaction_app",
            "compact_native_history",
            {"session_id": session_id, "message_index": message_index},
            context={"session_id": session_id},
        )

    app.close()


def test_dismissing_progress_banner_does_not_cancel_operation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)

    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)
    _wait_until(
        lambda: (
            (app.list_session_notifications(session_id)[0].get("revision") or 0) >= 2
        )
    )

    notification = app.list_session_notifications(session_id)[0]
    app.dismiss_session_notification(
        session_id, notification["id"], expected_revision=notification["revision"]
    )

    # The operation remains registered and the transport is still running.
    operations = get_application_operation_service(app.get_runtime_store()).list_active(
        session_id=session_id
    )
    assert len(operations) == 1
    assert operations[0].operation_id == result["operation_id"]
    assert not transport.cancelled.is_set()

    transport.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    app.close()


def test_next_heartbeat_after_dismissal_creates_new_occurrence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)

    result = _start(app, session_id)
    transport = _ControlledTransport.instances[0]
    assert transport.started.wait(2)
    _wait_until(
        lambda: (
            (app.list_session_notifications(session_id)[0].get("revision") or 0) >= 2
        )
    )

    notification = app.list_session_notifications(session_id)[0]
    dismissed_id = notification["id"]
    app.dismiss_session_notification(
        session_id, dismissed_id, expected_revision=notification["revision"]
    )

    # The next heartbeat creates a new pending occurrence with a new ID.
    _wait_until(
        lambda: (
            app.list_session_notifications(session_id)
            and app.list_session_notifications(session_id)[0]["id"] != dismissed_id
        )
    )
    replacement = app.list_session_notifications(session_id)[0]
    assert replacement["status"] == "pending"
    assert replacement["key"] == "openai_responses:native_compaction"
    assert replacement["operation"]["id"] == result["operation_id"]

    transport.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result["operation_id"]
        )
        is None
    )
    app.close()


def test_compaction_uses_one_stable_key_per_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, session_id = _build_app(tmp_path, monkeypatch)

    # First compaction.
    result_a = _start(app, session_id)
    transport_a = _ControlledTransport.instances[0]
    assert transport_a.started.wait(2)
    _wait_until(
        lambda: (
            (app.list_session_notifications(session_id)[0].get("revision") or 0) >= 2
        )
    )
    notification_a = app.list_session_notifications(session_id)[0]
    assert notification_a["key"] == "openai_responses:native_compaction"

    transport_a.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result_a["operation_id"]
        )
        is None
    )

    # Second compaction in the same session uses the same stable key.
    result_b = _start(app, session_id)
    transport_b = _ControlledTransport.instances[1]
    assert transport_b.started.wait(2)
    _wait_until(
        lambda: (
            (app.list_session_notifications(session_id)[0].get("revision") or 0) >= 2
        )
    )
    notification_b = app.list_session_notifications(session_id)[0]
    assert notification_b["key"] == "openai_responses:native_compaction"
    assert notification_b["operation"]["id"] == result_b["operation_id"]

    transport_b.release.set()
    _wait_until(
        lambda: get_application_operation_service(app.get_runtime_store()).get(
            result_b["operation_id"]
        )
        is None
    )
    app.close()
