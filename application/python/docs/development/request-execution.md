# Application request execution

This page explains how the application layer starts, coordinates, executes,
and finishes a model request. It is the canonical maintainer guide for request
ownership shared by HTTP, terminal, application plugins, and background work.

The key distinction is:

- `SessionRequestCoordinator` owns the application-facing request operation;
- `AgentApplication.send_request(...)` is the lower-level event generator;
- `ToolLoopRunner` performs provider and tool-loop phases;
- FastAPI and terminal are adapters that delegate to the application layer.

## Main implementation files

- `core/python/agent_app/request_execution.py`
  - request admission, preparation, background execution, public event
    publication, and cleanup;
- `core/python/agent_app/application_future.py`
  - `AgentApplication`, request lifecycle actions, persistence reconciliation,
    cancellation state, and the low-level request generator;
- `core/python/agent_app/application_owner.py`
  - application-generation admission and reload draining;
- `core/python/agent_app/tool_loop.py`
  - provider execution, streaming, tool calls, checkpoints, and cancellation;
- `application/python/agent_terminal_app/server.py`
  - HTTP validation, idempotency, response mapping, and route definitions;
- `application/python/agent_terminal_app/terminal_app.py`
  - terminal-facing delegation and current-session state;
- `application/python/agent_terminal_app/terminal.py`
  - prompt-toolkit input and event rendering.

Related documentation:

- [Runtime owner integration](runtime-owner-integration.md)
- [Application README](../../README.md)
- [Event API](../../../../core/python/docs/events.md)
- [Runtime reload specification](../../../../docs/development/specifications/application-runtime-reload/index.md)

## Ownership map

| Component | Responsibility |
|---|---|
| `SessionRequestCoordinator` | Single-flight admission, request preparation, worker ownership, public event publication, and cleanup |
| `AgentApplication` | Sessions, effective config, lifecycle actions, cancellation, persistence, notifications, and the low-level request generator |
| `AgentApplicationOwner` | Admit work against one application generation and wait for admitted work before reload |
| `ToolLoopRunner` | Provider phases, streaming, tool execution, request checkpoints, and cooperative cancellation |
| Event store | Public request events, checkpoint markers, session cursors, and frontend polling |
| FastAPI | HTTP parsing, idempotency keys, status/error translation, and serialization |
| Terminal | User input, current-session presentation state, event polling, and rendering |
| Application plugin or background process | Choose when to start a request and react to the returned start/result object |

The normal background flow is:

```text
HTTP / terminal / plugin
        |
        v
AgentApplication.start_session_request(...)
        |
        v
SessionRequestCoordinator
  1. acquire application generation
  2. validate and reserve the session
  3. optionally append a message
  4. capture the request baseline
  5. start the request worker
        |
        v
AgentApplication.send_request(...)
        |
        v
ToolLoopRunner -> provider -> tools -> provider ...
        |
        v
session persistence + public events + cleanup
```

## Application request APIs

`AgentApplication` exposes coordinated request operations for background and
synchronous adapters.

### Start from existing history

```python
started = app.start_session_request(
    session_id,
    overrides={"temperature": 0.2},
    stream=True,
)
```

This starts a background request without appending a message. It is the
application-layer equivalent of:

```text
POST /sessions/{session_id}/send
```

### Atomically append and start

```python
started = app.start_session_request_with_message(
    session_id,
    role="user",
    content="Explain the latest result.",
    metadata=None,
    overrides={},
    stream=True,
)
```

Admission occurs before append. If another request is already active, the
message is not appended.

This is the application-layer equivalent of:

```text
POST /sessions/{session_id}/send_message
```

### Run synchronously

```python
result = app.run_session_request(
    session_id,
    overrides={},
    stream=True,
    on_checkpoint=handle_live_session,
    on_event=observe_public_event,
    timeout=600,
)
```

This uses the same admission, preparation, event publication, and cleanup
logic but runs in the calling thread. Terminal compatibility APIs use this
form when they need a final result tuple.

### Atomically append and run synchronously

```python
result = app.run_session_request_with_message(
    session_id,
    role="user",
    content="Inspect the current implementation.",
    overrides={},
    stream=True,
    on_event=observe_public_event,
    timeout=600,
)
```

This uses the same preparation path as atomic background append-and-start, but
executes in the caller's thread and returns the final result directly.
Admission happens before append, so a same-session conflict does not add the
message.

The optional event observer receives stored public events in request order.
Internal session checkpoints remain private. If the observer raises, the
coordinator requests cancellation, drains request cleanup, and re-raises the
observer exception.

A positive finite timeout requests cooperative cancellation through the
request ID. It does not abandon an unowned worker; a non-cooperative blocking
provider or tool may finish its current operation before execution returns.

### Inspect the active request

```python
request_id = app.get_active_session_request_id(session_id)
```

This is the authoritative application-process single-flight state. Adapters
must not maintain a separate active-request map.

### Query derived status for explicit sessions

```python
snapshot = app.get_session_request_statuses(["session-one", "session-two"])
```

`SessionRequestStatusService` checks coordinated active state first. When no
request is active, it classifies the persisted conversation tail and caches
that classification by the session store's opaque revision. Empty history is
`idle`, a user tail is `not_started`, a final assistant tail without tool
calls is `succeeded`, and every other incomplete conversational tail is
`interrupted`.

FastAPI exposes this through `POST /sessions/request-statuses`. The request
must contain explicit `session_ids`; omitted IDs never mean all sessions.
Missing sessions are partial results. The response authority is
`derived_transient`, so it does not claim durable failure/cancellation history
and can later delegate to persisted operation state.

### Cancel

```python
app.cancel_request(request_id)
app.soft_cancel_request(request_id)
```

Cancellation remains owned by `AgentApplication`. `cancel_request` is hard
cancellation: cooperative providers and foreground tools are interrupted.
`soft_cancel_request` interrupts a provider, but lets an already-running tool
finish, append its result, and checkpoint before stopping the request. No
later tool or provider phase starts.

## Start and result objects

A background start returns `SessionRequestStart`:

```python
SessionRequestStart(
    status="started",  # or "already_running"
    session_id=session_id,
    request_id=request_id,
)
```

When admission finds an existing request, it returns
`status="already_running"` with that existing request ID.

A synchronous run returns `SessionRequestResult`:

```python
SessionRequestResult(
    session_id=session_id,
    request_id=request_id,
    final_session=serialized_session_or_none,
    final_messages=[...],
    status="succeeded",  # failed, cancelled, or interrupted
    error=None,          # bounded SessionRequestError when applicable
)
```

Status is derived from the public request events consumed by the coordinator.
Cancellation outranks failure when cancellation is observed, an explicit
fatal error outranks an intermediate final tool-call response, a final
assistant response is success, and a request ending without any of those facts
is interrupted.

The application-package `LocalAgentRuntime` converts this compatibility result
to `AgentRunResult`, which intentionally omits `final_session` and adds
deterministic final assistant text. Its bounded `RunProgress` records are
normalized from the observer path. See the
[local headless agent runs guide](../headless-agent-runs.md).

## Admission and preparation

### Application-generation admission

Before preparing a request, the coordinator asks `ApplicationControl` to
acquire an owner operation.

The operation must refer to the same `AgentApplication` instance as the
coordinator. This prevents background work from starting through an
application generation that has already been replaced.

While reload is pending, owner admission raises
`ApplicationReloadPendingError`. A request is rejected before an optional
message append.

The worker retains the owner operation after an HTTP route returns its
immediate acknowledgement. Reload waits for the worker to release it.

Applications constructed without an `AgentApplicationOwner` remain supported;
in that case no owner-operation handle is required.

### Session lock and writable view

Preparation runs under the shared per-session lock:

1. reject a selected readonly snapshot;
2. load the current session and its configured agent runtime;
3. check whether the coordinator already has an active request;
4. reserve the generated request ID;
5. optionally append and persist a message;
6. capture the current session file state as the request baseline.

The active request is reserved before append. This provides the important
invariant:

> An append-and-start operation that loses admission does not append.

### Configuration overrides

Request overrides are merged in this order:

1. session-owned `Session.metadata["overrides"]`;
2. explicit overrides supplied to the coordinated request operation.

Explicit request overrides win on conflicts.

The merged mapping is passed to `AgentApplication.send_request(...)`.
`AgentApplication.resolve_effective_config(...)` combines it with the agent
base configuration and uses the result for message conversion, lifecycle
actions, provider setup, and tool preparation.

### Atomic message append

Append-and-start resolves effective config, calls `AgentCore.add_message(...)`,
persists the resulting immutable session, publishes `message_appended`, and
records a checkpoint before the request worker begins.

Multipart attachment content follows the same path. HTTP validates and
normalizes the multipart payload before calling the application API.

## Background and synchronous execution

Both forms call the same internal execution path.

### Background start

The coordinator creates one daemon worker thread for the prepared request and
returns `SessionRequestStart` immediately.

The worker owns:

- iteration of the low-level request generator;
- internal checkpoint filtering;
- public event publication;
- final result collection;
- active-request cleanup;
- application-generation operation release.

Unexpected worker exceptions are logged. Application/provider failures that
are represented as normal request events still flow through the event store.

### Synchronous run

`run_session_request(...)` performs the same work in the caller's thread. It
is useful for terminal compatibility, tests, and other callers that need the
final result directly.

If the session already has an active request, the synchronous form raises
`SessionRequestAlreadyRunningError`.

The message-bearing synchronous form follows the same rule and guarantees
that the rejected message was not appended.

## Low-level request lifecycle

`AgentApplication.send_request(...)` remains the low-level generator. It
receives a prepared core, session, base config, merged overrides, request ID,
and file-state baseline.

Its lifecycle is:

1. reconcile the prepared session against persisted state;
2. run `request_prepare` lifecycle actions;
3. resolve effective config and streaming mode;
4. emit `request_started`;
5. prepare tools;
6. install the live `RequestCancellation`;
7. run provider/tool-loop phases;
8. persist request checkpoints;
9. run `request_complete` or `request_error` lifecycle actions;
10. expire request-retained notifications;
11. emit `request_completed`;
12. clear application cancellation state.

### Tool-loop phases

`ToolLoopRunner` performs one or more phases:

```text
provider response
    |
    +-- no tool calls --> final response
    |
    +-- tool calls --> execute tools --> checkpoint --> next provider phase
```

The runner receives callbacks for:

- cooperative cancellation;
- checkpoint persistence;
- reconciling session state before another phase;
- refreshing config and prepared tools when the session changes.

### Streaming fallback

The application may initially request streaming. If the provider reports that
streaming is not implemented before yielding tool-loop events, the application
marks that provider class as non-streaming and retries the phase without
streaming.

This fallback belongs to the low-level generator, not the coordinator or HTTP
adapter.

## Persistence and reconciliation

The request starts from a session/file-state baseline captured during
preparation.

Before request execution and at subsequent checkpoints, application
reconciliation checks that persisted history is still compatible. It rejects
conflicting message or protected-metadata changes instead of silently
overwriting them.

Compatible non-protected metadata updates can be merged. This is important for
application-owned state such as notifications that may change while other
work is running.

On a conflict, the application emits an error event, preserves a conflict
backup where configured, and completes the request without replacing the
conflicting stored history.

## Internal checkpoints and public events

`ToolLoopRunner` and `AgentApplication.send_request(...)` may yield an internal
event containing a live `Session` object:

```json
{
  "type": "session_checkpoint",
  "session_id": "...",
  "request_id": "...",
  "session": "<live Session object>"
}
```

`SessionRequestCoordinator` does not publish this object to the public event
store.

- Background execution consumes it internally.
- Synchronous execution may pass its `Session` to `on_checkpoint`.

All other request events are published through
`AgentApplication.publish_event(...)`.

When a synchronous request has an observer, the stored public event is passed
to it after publication. Observer delivery does not replace the event store.

Checkpoint persistence records a serializable `checkpoint` marker in the
event store. The per-session cursor points to the latest persistence boundary.

`GET /sessions/{session_id}/messages` derives frontend `active_request_id`
from the checkpoint at that cursor. This keeps the message snapshot, cursor,
and request state aligned.

For event shapes and polling semantics, see the
[Event API](../../../../core/python/docs/events.md).

## Cancellation timing

Cancellation can arrive before or after the live `RequestCancellation` object
is installed.

Both cancellation methods record a mode before the live controller is
installed. Registration initializes the controller atomically from that mode.
Hard cancellation wins races and can promote an earlier soft cancellation;
soft cancellation cannot downgrade hard cancellation.

The tool loop checks cancellation:

- before provider phases;
- while streaming;
- before and during tool execution;
- while waiting for async or blocking components that register callbacks.

The controller separates overall stop, provider interruption, and hard-only
tool interruption. Tools receive only the hard-only signal, so soft
cancellation is observed at the post-tool checkpoint. A non-cooperative
provider or tool may still finish before cancellation is observed.

Explicit background commands are outside request cancellation after successful
handoff. Their existing process-specific stop mechanism remains authoritative.

## Reload and application close

### Managed application reload

The request worker owns an `ApplicationOperation` for its exact application
generation. `AgentApplicationOwner` does not replace the application until all
admitted operations release.

During a pending reload:

- HTTP middleware rejects new application operations;
- direct coordinator starts also fail owner admission;
- active requests are allowed to finish.

### Direct application close

`AgentApplication.close()` closes its coordinator before other runtime
resources.

## Compact history projection

`agent_app.history_projection` owns a deterministic derived history view.
`AgentApplication.get_compact_session_history(...)` loads canonical persisted
state and delegates to that projector;
`AgentApplication.get_session_message(...)` serializes one explicitly selected
canonical message in full.

Projection applies canonical Python-style range bounds before role filtering,
retains the newest bounded selected rows, allocates content budget from newest
to oldest, and returns rows in chronological order with their original
indices. Tool rows prefer safe `metadata.display.single_line` text. Native
history, multipart bodies, and unrestricted metadata are not projected.

The projection is not persisted, does not advance a cursor, and is not another
history authority. The local Python runtime and one-shot CLI share it;
interactive terminal rendering remains an adapter.

Coordinator close:

- rejects new starts;
- requests cooperative cancellation for active request workers;
- prevents later public event publication through the closed coordinator.

Normal owner-managed replacement should already have drained request workers
before close.

## Adapter responsibilities

### FastAPI

FastAPI owns transport concerns:

- request-body validation;
- multipart normalization;
- HTTP idempotency keys;
- HTTP status and exception mapping;
- JSON serialization;
- route declarations.

FastAPI does not own:

- active request state;
- request IDs;
- worker threads;
- request event publication;
- message append transaction semantics;
- application-generation retention.

`/send` returns the coordinator's `started` or `already_running` result.
`/send_message` maps `already_running` to HTTP 409 and does not append a second
message.

HTTP idempotency remains separate from application single-flight admission.
Replaying an idempotency key returns the original HTTP response; starting a
different request for an already-active session returns the active request
result.

### Terminal

Ordinary terminal input calls atomic append-and-start. The explicit `/append`
operation remains append-only.

The terminal polls and renders public events. It does not create its own
request worker or hold a separate owner operation.

Assistant lifecycle start/end events carry `message_index`, equal to the LLM
phase's existing `start_index`. During streaming this is the reserved index the
assistant message will occupy if the phase commits. Cancellation after partial
output can leave that displayed index without a stored message; the terminal
does not persist an incomplete assistant solely to make the index expandable.

`TerminalApplication.poll_new_events()` applies the shared application event
compactor before rendering. Redundant assistant/tool stream chunks may be
dropped when their aggregate terminal event is present, but
`tool_partial(phase="end")` is preserved because it carries the final
display-aware tool result and stored message index. Terminal renderers do not
reconstruct a lost end event from `tool_results`.

`TerminalApplication.send_request(...)` remains as a synchronous compatibility
API and delegates to `run_session_request(...)`.

### Application plugins and background work

Application plugins should use the coordinated APIs rather than invoking the
low-level generator directly.

For example, background compaction can start a follow-up request without
appending a message:

```python
started = app.start_session_request(session_id)
```

This preserves ordinary admission, reload ownership, event publication,
cancellation, and frontend request visibility.

## Failure semantics and invariants

The application-layer request path maintains these invariants:

- at most one coordinated request is active for a session;
- a failed duplicate append-and-start does not append;
- every admitted request clears admission in a `finally` path;
- every owner-operation handle is released;
- internal live `Session` objects are not published as public events;
- HTTP-specific exceptions and idempotency do not enter `agent_app`;
- request IDs are stable across start responses, events, cancellation, and
  cleanup;
- stale application generations cannot start new work;
- session conflicts are reported instead of silently overwriting history.

## Source and test map

Primary implementation:

- `core/python/agent_app/request_execution.py`
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/application_owner.py`
- `core/python/agent_app/tool_loop.py`
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `application/python/agent_terminal_app/terminal.py`

Primary tests:

- `application/python/tests/test_session_request_coordinator.py`
- `application/python/tests/test_agent_terminal_app_server.py`
- `application/python/tests/test_terminal_application.py`
- `application/python/tests/test_application_reload_owner.py`
- `core/python/tests/test_application_layer_streaming.py`
- `core/python/tests/test_application_tool_loop_session_concurrency.py`

When changing request ownership, run at minimum:

```bash
pytest core/python/tests -q
pytest application/python/tests -q
npm --workspace @crystal-lattice/frontend-sdk test
```

For provider, mobile, and desktop follow-up expectations, see the repository
development workflow in the root `AGENTS.md`.

Requests also participate in the shared application-operation admission and
lookup model. See [Application operations](operations.md) for cross-producer
session exclusivity, minimal active registration, managed-process integration,
plugin-owned status, and future operation-menu extensions.