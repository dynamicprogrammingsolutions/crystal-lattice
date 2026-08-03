from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Any

import pytest

from agent_app.application_future import AgentApplication, RuntimeStore
from agent_app.application_notifications import InMemoryApplicationNotificationStore
from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
from agent_app.events import InMemoryEventStore
from agent_app.managed_processes import (
    ManagedProcessAlreadyExistsError,
    ManagedProcessRegistry,
    ManagedProcessRegistryClosedError,
    get_managed_process_registry,
)
from tests.fixtures.managed_process_app_plugin import (
    CREATED_MANAGED_PROCESSES,
    ManagedProcessFixture,
    ManagedProcessFixtureAppPlugin,  # noqa: F401
)


class _Process:
    def __init__(
        self,
        *,
        start_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.start_error = start_error
        self.close_error = close_error
        self.started = False
        self.closed = False
        self.messages: list[str] = []

    def start(self) -> None:
        self.started = True
        if self.start_error is not None:
            raise self.start_error

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error

    def send(self, message: str) -> None:
        self.messages.append(message)


def test_start_lookup_communication_remove_and_close() -> None:
    registry = ManagedProcessRegistry()
    process = registry.start("process-1", _Process())

    assert process.started is True
    assert registry.get("process-1") is process
    process.send("hello")
    assert process.messages == ["hello"]

    assert registry.remove("process-1", process) is True
    assert registry.get("process-1") is None
    registry.close()
    assert process.closed is False


def test_duplicate_id_is_rejected_without_starting_second_process() -> None:
    registry = ManagedProcessRegistry()
    first = registry.start("same", _Process())
    second = _Process()

    with pytest.raises(ManagedProcessAlreadyExistsError):
        registry.start("same", second)

    assert registry.get("same") is first
    assert second.started is False
    registry.close()
    assert first.closed is True


def test_stale_identity_cannot_remove_replacement() -> None:
    registry = ManagedProcessRegistry()
    first = registry.start("reused", _Process())
    assert registry.remove("reused", first) is True

    replacement = registry.start("reused", _Process())
    assert registry.remove("reused", first) is False
    assert registry.get("reused") is replacement

    registry.close()
    assert replacement.closed is True


def test_startup_failure_is_cleaned_without_affecting_other_processes() -> None:
    registry = ManagedProcessRegistry()
    healthy = registry.start("healthy", _Process())
    failing = _Process(start_error=RuntimeError("start failed"))

    with pytest.raises(RuntimeError, match="start failed"):
        registry.start("failing", failing)

    assert failing.closed is True
    assert registry.get("failing") is None
    assert registry.get("healthy") is healthy
    registry.close()
    assert healthy.closed is True


def test_close_failure_does_not_prevent_remaining_process_closes() -> None:
    registry = ManagedProcessRegistry()
    failing = registry.start(
        "failing-close",
        _Process(close_error=RuntimeError("close failed")),
    )
    healthy = registry.start("healthy-close", _Process())

    registry.close()

    assert failing.closed is True
    assert healthy.closed is True


def test_close_is_idempotent_and_rejects_later_starts() -> None:
    registry = ManagedProcessRegistry()
    process = registry.start("process", _Process())

    registry.close()
    registry.close()

    assert process.closed is True
    with pytest.raises(ManagedProcessRegistryClosedError):
        registry.start("later", _Process())


def test_concurrent_duplicate_starts_admit_exactly_one_process() -> None:
    registry = ManagedProcessRegistry()
    entered = threading.Event()
    release = threading.Event()

    class _BlockingStartProcess(_Process):
        def start(self) -> None:
            self.started = True
            entered.set()
            release.wait(timeout=5)

    first = _BlockingStartProcess()
    second = _Process()
    errors: list[BaseException] = []

    def _start_first() -> None:
        try:
            registry.start("shared", first)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=_start_first)
    thread.start()
    assert entered.wait(timeout=2)

    with pytest.raises(ManagedProcessAlreadyExistsError):
        registry.start("shared", second)

    release.set()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert errors == []
    assert registry.get("shared") is first
    assert second.started is False
    registry.close()


def test_process_can_request_removal_while_start_is_returning() -> None:
    registry = ManagedProcessRegistry()

    class _ImmediateCompletionProcess(_Process):
        def start(self) -> None:
            self.started = True
            assert registry.remove("fast", self) is True

    process = registry.start("fast", _ImmediateCompletionProcess())

    assert process.started is True
    assert registry.get("fast") is None
    registry.close()
    assert process.closed is False


def test_close_racing_with_start_closes_process_before_returning() -> None:
    registry = ManagedProcessRegistry()
    entered = threading.Event()
    release = threading.Event()
    close_started = threading.Event()
    close_finished = threading.Event()
    start_errors: list[BaseException] = []

    class _BlockingStartProcess(_Process):
        def start(self) -> None:
            self.started = True
            entered.set()
            release.wait(timeout=5)

    process = _BlockingStartProcess()

    def _start() -> None:
        try:
            registry.start("racing", process)
        except BaseException as exc:
            start_errors.append(exc)

    start_thread = threading.Thread(target=_start)
    start_thread.start()
    assert entered.wait(timeout=2)

    def _close() -> None:
        close_started.set()
        registry.close()
        close_finished.set()

    close_thread = threading.Thread(target=_close)
    close_thread.start()
    assert close_started.wait(timeout=2)
    assert close_finished.wait(timeout=0.05) is False

    release.set()
    start_thread.join(timeout=2)
    close_thread.join(timeout=2)

    assert not start_thread.is_alive()
    assert not close_thread.is_alive()
    assert process.closed is True
    assert len(start_errors) == 1
    assert isinstance(start_errors[0], ManagedProcessRegistryClosedError)


def test_runtime_store_owns_and_closes_registry() -> None:
    runtime_store = RuntimeStore()
    registry = get_managed_process_registry(runtime_store)
    same_registry = get_managed_process_registry(runtime_store)
    first = registry.start("first", _Process())
    second = registry.start("second", _Process())

    assert same_registry is registry
    runtime_store.close()

    assert first.closed is True
    assert second.closed is True
    with pytest.raises(ManagedProcessRegistryClosedError):
        registry.start("later", _Process())


def test_registry_helper_rejects_incompatible_runtime_store_value() -> None:
    class _RuntimeStore:
        def get_or_create(self, key: str, factory: Any) -> Any:
            _ = key, factory
            return object()

    with pytest.raises(TypeError, match="incompatible"):
        get_managed_process_registry(_RuntimeStore())


def test_application_plugin_managed_process_closes_on_owner_replacement(
    tmp_path: Path,
) -> None:
    CREATED_MANAGED_PROCESSES.clear()
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "providers": {},
                "agents": {},
                "plugins": [
                    "tests.fixtures.managed_process_app_plugin." "ManagedProcessFixtureAppPlugin"
                ],
            }
        ),
        encoding="utf-8",
    )
    event_store = InMemoryEventStore()
    notification_store = InMemoryApplicationNotificationStore()

    def factory(control: ApplicationControl) -> AgentApplication:
        return AgentApplication(
            config_path,
            tmp_path / "sessions",
            event_store=event_store,
            application_notification_store=notification_store,
            application_control=control,
        )

    owner = AgentApplicationOwner(factory, event_store=event_store)
    old_application = owner.current

    started = old_application.execute_application_action(
        "managed_process_fixture",
        "start",
        {"process_id": "fixture-process"},
    )
    assert started["process"]["started"] is True
    process = CREATED_MANAGED_PROCESSES[-1]
    assert isinstance(process, ManagedProcessFixture)

    sent = old_application.execute_application_action(
        "managed_process_fixture",
        "send",
        {
            "process_id": "fixture-process",
            "message": "cancel-later",
        },
    )
    assert sent["found"] is True
    assert sent["process"]["messages"] == ["cancel-later"]

    status = old_application.execute_application_action(
        "managed_process_fixture",
        "status",
        {"process_id": "fixture-process"},
    )
    assert status["found"] is True
    assert status["process"]["closed"] is False

    reload_result = owner.request_reload(reason="managed-process-test")
    assert owner.wait_for_reload(reload_result["reload_id"], timeout=5)
    assert owner.current is not old_application
    assert process.closed is True

    replacement_status = owner.current.execute_application_action(
        "managed_process_fixture",
        "status",
        {"process_id": "fixture-process"},
    )
    assert replacement_status == {
        "found": False,
        "process_id": "fixture-process",
    }
    owner.close()
