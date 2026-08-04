"""Application layer for the AI Agent Platform.

Provides a thin, imperative shell around the functional `agent_core` SDK.

The public entry point is `AgentApplication`, which exposes a typed,
core-first API suitable for HTTP/JSON APIs while delegating all message
processing to `AgentCore`.
"""

from __future__ import annotations

from .application_future import AgentApplication
from .application_notifications import (
    ApplicationNotificationStore,
    InMemoryApplicationNotificationStore,
    SQLiteApplicationNotificationStore,
)
from .application_owner import (
    AgentApplicationOwner,
    ApplicationReloadPendingError,
)
from .request_execution import (
    SessionOperationBusyError,
    SessionRequestAlreadyRunningError,
    SessionRequestResult,
    SessionRequestStart,
)
from .operations import (
    ApplicationOperationBusyError,
    ApplicationOperationClosedError,
    ApplicationOperationLease,
    ApplicationOperationLeaseReleasedError,
    ApplicationOperationRegistration,
    ApplicationOperationService,
    get_application_operation_service,
    session_operation_exclusivity_key,
)
from .managed_processes import (
    ManagedProcess,
    ManagedProcessAlreadyExistsError,
    ManagedProcessRegistry,
    ManagedProcessRegistryClosedError,
    get_managed_process_registry,
)

__all__ = [
    "AgentApplication",
    "ApplicationOperationBusyError",
    "ApplicationOperationClosedError",
    "ApplicationOperationLease",
    "ApplicationOperationLeaseReleasedError",
    "ApplicationOperationRegistration",
    "ApplicationOperationService",
    "ApplicationNotificationStore",
    "AgentApplicationOwner",
    "ApplicationReloadPendingError",
    "InMemoryApplicationNotificationStore",
    "ManagedProcess",
    "ManagedProcessAlreadyExistsError",
    "ManagedProcessRegistry",
    "ManagedProcessRegistryClosedError",
    "SessionRequestAlreadyRunningError",
    "SessionOperationBusyError",
    "SessionRequestResult",
    "SessionRequestStart",
    "SQLiteApplicationNotificationStore",
    "get_managed_process_registry",
    "get_application_operation_service",
    "session_operation_exclusivity_key",
]
