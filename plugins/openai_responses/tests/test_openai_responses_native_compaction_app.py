from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict

import pytest

from agent_app.application_future import AgentApplication
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
        _ = kwargs
        self.started = threading.Event()
        self.release = threading.Event()
        self.cancelled = threading.Event()
        type(self).instances.append(self)

    def compact(self, **kwargs: Any) -> Dict[str, Any]:
        _ = kwargs
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
) -> tuple[AgentApplication, str]:
    monkeypatch.setattr(OpenAIResponsesProvider, "get_models", lambda self, config: [])
    config = {
        "providers": {
            "openai_responses": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": "test-key",
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_native_compaction_extension.OpenAIResponsesNativeCompactionExtension",
            "openai_responses_plugins.openai_responses_native_compaction_app.OpenAIResponsesNativeCompactionAppPlugin",
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
    assert notification["display"]["dismissible"] is False
    assert "Elapsed:" in notification["body"]
    assert notification["display"]["actions"][0]["action_id"] == (
        "cancel_native_compaction"
    )
    assert notification["display"]["actions"][0]["label"] == "Cancel compaction"

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
    completed_notification = app.list_session_notifications(session_id)[0]
    assert completed_notification["status"] == "pending"
    assert completed_notification["severity"] == "success"
    assert completed_notification["display"]["variant"] == "success"
    assert completed_notification["display"]["presentation"] == "banner"
    assert completed_notification["display"]["dismissible"] is True
    assert completed_notification["title"] == "Native compaction complete"
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
    notification = app.list_session_notifications(session_id)[0]
    assert notification["status"] == "pending"
    assert notification["severity"] == "warning"
    assert notification["display"]["variant"] == "warning"
    assert notification["display"]["presentation"] == "banner"
    assert notification["display"]["dismissible"] is True
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
    app.close()
