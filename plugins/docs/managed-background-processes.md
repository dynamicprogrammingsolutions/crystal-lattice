# Managed background processes

Use the application managed-process registry when a plugin needs to start
in-memory background work, return from an action promptly, find that work in a
later action, and close it when the owning application generation shuts down.

The shared implementation is:

- `core/python/agent_app/managed_processes.py`

It deliberately provides only application-lifetime ownership:

- start a process object under a plugin-chosen ID;
- look it up later;
- remove it by matching object identity;
- close all still-registered objects on application close or replacement.

The registry does not know about notifications, sessions, requests, OpenAI,
subprocesses, progress, or cancellation policy.

## When to use it

Use the managed-process registry for work that:

- is owned by one `AgentApplication` generation;
- runs in a thread, task, subprocess wrapper, or another process-owned
  runtime;
- must return control to the initiating action promptly;
- needs later plugin-specific communication such as cancellation or status;
- must become unable to apply late results after application close.

Examples include:

- provider compaction;
- a long-running export or import;
- a plugin-owned indexing job;
- an in-memory synchronization operation;
- a wrapper around another runtime that should close with the application.

## When not to use it

Do not use this registry as a replacement for a durable subprocess manager.

`tool-compat-shared.BackgroundProcessRegistry` owns:

- persistent process manifests;
- output and completion files;
- detached-process discovery;
- restart reconciliation;
- process-tree termination;
- shutdown and ownership policies.

Use that specialized registry when users need to inspect or reconnect to OS
commands independently of one in-memory application generation.

MCP also keeps its existing aggregate registry. An MCP registry owns multiple
server runtimes, tool discovery, asynchronous calls, and server status. Its
existing `RuntimeStore` ownership already closes it with the application.

The generic managed-process registry may hold a facade around another manager
when that is useful, but individual MCP servers or durable shell processes do
not need to be migrated into it.

## Process contract

Import the public API from `agent_app`:

```python
from agent_app import (
    ManagedProcess,
    ManagedProcessRegistry,
    get_managed_process_registry,
)
```

A process provides two synchronous lifecycle methods:

```python
class ManagedProcess(Protocol):
    def start(self) -> None:
        """Launch background work and return promptly."""

    def close(self) -> None:
        """Signal shutdown, invalidate late work, and return promptly."""
```

Both methods must be bounded.

`start()` launches the actual long-running worker and returns. It must not
perform the provider call, wait for process completion, or hold the action
open for the duration of the operation.

`close()` signals cancellation or invalidation and returns. It must not wait
indefinitely for a provider or subprocess operation that cannot be interrupted.
The worker must check the closed state before committing results or performing
other application-owned side effects.

The concrete process may expose additional methods:

```python
process.request_cancel(reason="user")
process.send(command)
process.snapshot()
```

These methods are owned and interpreted by the plugin. They are not part of
the generic registry protocol.

## Obtaining the registry

Application plugins receive `AgentApplication` directly:

```python
registry = get_managed_process_registry(app.get_runtime_store())
```

Provider-extension actions receive the application only when invoked through
`AgentApplication`:

```python
app = (context or {}).get("app")
if app is None:
    raise RuntimeError("This action requires the application runtime")

registry = get_managed_process_registry(app.get_runtime_store())
```

The helper uses one stable key with `RuntimeStore.get_or_create(...)`.
Different plugins in the same application generation therefore share one
registry while retaining separate process IDs and concrete process types.

No additional `AgentApplication` registry or lookup methods are required.

## Starting a process

Construct the process with all of its dependencies, then start it through the
registry:

```python
process_id = f"compact:{session_id}:{occurrence_id}"
process = CompactionProcess(
    process_id=process_id,
    session_id=session_id,
    publish_progress=publish_progress,
    commit_result=commit_result,
    start_request=start_request,
)
registry.start(process_id, process)

return {
    "status": "accepted",
    "process_id": process_id,
}
```

The plugin chooses the process ID. Use a unique occurrence identifier when the
same logical operation can run more than once.

The registry reserves the ID before calling `process.start()`. A duplicate
raises `ManagedProcessAlreadyExistsError` without starting the second object.

If `start()` fails:

- the reservation is removed;
- `close()` is attempted as best-effort cleanup;
- the original startup error is re-raised.

## Looking up and communicating

A later action can retrieve the same concrete object:

```python
process = registry.get(process_id)
if not isinstance(process, CompactionProcess):
    return {
        "status": "not_found",
        "process_id": process_id,
    }

process.request_cancel(reason="user")
return {
    "status": "cancellation_requested",
    "process_id": process_id,
}
```

Lookup may return the process while its prompt `start()` transition is still
finishing. Concrete communication methods should therefore be safe once the
object has been constructed and registered.

## Normal completion and removal

The process owns terminal behavior:

- commit or discard the result;
- publish success, failure, or cancellation;
- resolve or update notifications;
- perform any operation-specific cleanup.

After terminal behavior is complete, remove the process by ID and identity:

```python
registry.remove(process_id, self)
```

Identity matching prevents an old worker from removing a newer process that
later reused the same ID.

Normal removal does not call `close()`. The process has already completed its
terminal path.

An extremely fast worker may request removal while `start()` is still
returning. The registry records that request and removes the entry after the
startup transition completes.

## Example thread-owned process

```python
from __future__ import annotations

import threading
from typing import Callable

from agent_app import ManagedProcessRegistry


class ExampleProcess:
    def __init__(
        self,
        *,
        process_id: str,
        registry: ManagedProcessRegistry,
        work: Callable[[threading.Event], str],
        publish_result: Callable[[str], None],
    ) -> None:
        self._process_id = process_id
        self._registry = registry
        self._work = work
        self._publish_result = publish_result
        self._closed = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("process already started")
        self._thread = threading.Thread(
            target=self._run,
            name=f"managed-process-{self._process_id}",
            daemon=True,
        )
        self._thread.start()

    def close(self) -> None:
        self._closed.set()

    def request_cancel(self) -> None:
        self._closed.set()

    def _run(self) -> None:
        try:
            result = self._work(self._closed)
            if self._closed.is_set():
                return
            self._publish_result(result)
        finally:
            self._registry.remove(self._process_id, self)
```

The important property is not the use of a thread. It is that:

- `start()` returns after launching work;
- `close()` only signals invalidation;
- the worker checks invalidation before publishing a late result;
- terminal completion removes the exact process object.

## Notifications and cancellation

Notifications are process-owned domain behavior.

The registry must not create a notification automatically because different
operations need different:

- titles and messages;
- progress fields;
- update cadence;
- terminal retention;
- failure guidance;
- follow-up actions;
- cancellation meaning.

Pass narrow notification methods or callbacks into the process. The process
can then create one notification and publish key-based updates, then expose a
plugin-specific cancellation action without coupling generic runtime ownership
to notification semantics.

Similarly, the registry has no `cancel(process_id)` method. A later action
looks up the concrete process and calls its operation-specific cancellation
method.

## Application reload and shutdown

`RuntimeStore` owns the registry. When an `AgentApplication` closes or is
replaced:

1. `RuntimeStore.close()` calls `ManagedProcessRegistry.close()`;
2. the registry rejects new starts;
3. it waits for prompt in-progress `start()` transitions to settle;
4. it calls `close()` on every still-registered process;
5. one failing process close does not prevent remaining closes.

The process must treat `close()` as revocation of authority to mutate the old
application generation. If a provider call returns later, the process discards
the result.

Managed processes are not restored after replacement. The replacement
application receives a new runtime store and a new empty registry.

## Concurrency guarantees

The registry provides:

- exactly one admitted process for a process ID;
- lookup during `starting` and `running`;
- identity-safe completion removal;
- startup failure cleanup;
- close/start race handling;
- idempotent close;
- rejection of starts after close.

The registry does not serialize plugin-specific process methods. The process
must make its own cancellation, status, and communication state thread-safe.

## Testing

Test the generic ownership boundary separately from operation behavior.

Registry tests should cover:

- duplicate starts;
- startup failure;
- stale identity removal;
- close failure isolation;
- completion during startup;
- close during startup;
- runtime-store close.

Plugin tests should use controlled workers and clocks to cover:

- action responsiveness;
- progress updates;
- operation-specific communication;
- late-result rejection;
- success, failure, and cancellation;
- application replacement.

Do not use real long sleeps to test progress heartbeats. Inject a clock or
controllable wait mechanism into the concrete process.

The first production consumer is the OpenAI Responses native compaction
application plugin. It combines:

- `ApplicationOperationService` for minimal active identity, lookup, and
  session admission;
- `ManagedProcessRegistry` for the concrete process object;
- session notifications for progress, Cancel, Retry, and terminal
  presentation;
- an async OpenAI compact transport for prompt HTTP cancellation;
- guarded optimistic reconciliation for the final session update.

See `application/python/docs/development/operations.md` for the application
operation model and `plugins/openai_responses/README.md` for provider-specific
behavior.