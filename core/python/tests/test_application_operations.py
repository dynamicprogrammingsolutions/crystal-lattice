from __future__ import annotations

import threading

import pytest

from agent_app.application_future import RuntimeStore
from agent_app.operations import (
    ApplicationOperationBusyError,
    ApplicationOperationLeaseReleasedError,
    ApplicationOperationService,
    get_application_operation_service,
    session_operation_exclusivity_key,
)


def test_operation_service_reserves_lists_and_releases() -> None:
    service = ApplicationOperationService()
    lease = service.reserve(
        operation_id="request-1",
        owner_id="agent_app.session_request",
        session_id="session-1",
        exclusivity_keys=(session_operation_exclusivity_key("session-1"),),
    )

    registration = lease.registration()
    assert registration.to_dict() == {
        "operation_id": "request-1",
        "owner_id": "agent_app.session_request",
        "session_id": "session-1",
    }
    assert service.get("request-1") == registration
    assert service.get_by_exclusivity_key("session:session-1") == registration
    assert service.list_active(session_id="session-1") == [registration]
    assert service.list_active(owner_id="agent_app.session_request") == [registration]

    assert lease.release() is True
    assert lease.release() is False
    assert service.get("request-1") is None
    assert service.get_by_exclusivity_key("session:session-1") is None

    with pytest.raises(ApplicationOperationLeaseReleasedError):
        lease.registration()


def test_operation_service_rejects_duplicate_exclusivity_atomically() -> None:
    service = ApplicationOperationService()
    barrier = threading.Barrier(3)
    outcomes: list[str] = []

    def _reserve(operation_id: str) -> None:
        barrier.wait()
        try:
            service.reserve(
                operation_id=operation_id,
                owner_id="test",
                session_id="session-1",
                exclusivity_keys=("session:session-1",),
            )
        except ApplicationOperationBusyError:
            outcomes.append("busy")
        else:
            outcomes.append("reserved")

    threads = [
        threading.Thread(target=_reserve, args=("operation-1",)),
        threading.Thread(target=_reserve, args=("operation-2",)),
    ]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join(timeout=5)

    assert sorted(outcomes) == ["busy", "reserved"]


def test_operation_service_release_is_identity_safe() -> None:
    service = ApplicationOperationService()
    first = service.reserve(
        operation_id="operation-1",
        owner_id="test",
        exclusivity_keys=("exclusive",),
    )
    assert first.release() is True
    second = service.reserve(
        operation_id="operation-1",
        owner_id="test",
        exclusivity_keys=("exclusive",),
    )

    assert first.release() is False
    assert service.get("operation-1") == second.registration()


def test_operation_service_close_clears_active_registrations() -> None:
    service = ApplicationOperationService()
    lease = service.reserve(
        operation_id="operation-1",
        owner_id="test",
        session_id="session-1",
        exclusivity_keys=("session:session-1",),
    )

    service.close()

    assert service.list_active() == []
    assert service.get_by_exclusivity_key("session:session-1") is None
    assert lease.release() is False


def test_runtime_store_owns_one_operation_service() -> None:
    runtime_store = RuntimeStore()

    first = get_application_operation_service(runtime_store)
    second = get_application_operation_service(runtime_store)

    assert first is second
    runtime_store.close()
