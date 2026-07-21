# Stage 2a Backend — Wait-Only Interactions

Implement backend support for generic interactive notifications that wait for user input without suspending the request. The interceptor blocks in the pre-execution hook; the action handler signals the waiting interceptor.

## Requirements checklist

- [ ] Implement interaction lifecycle: create, respond, resolve, expire, cancel.
- [ ] Implement wait-only signaling mechanism (DP10 — open).
- [ ] Wire the signaling into the tool-call interceptor pre-execution hook.
- [ ] Add timeout with `default_action_id` fallback.
- [ ] Add cancellation: request cancellation unblocks the waiting interceptor.
- [ ] Publish interaction lifecycle events.
- [ ] Add dummy interceptor plugin tests for interaction choices.
- [ ] Ensure interaction failures do not abort requests.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:
- `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- `tasks/20260619-generic-session-notifications/050-stage-2-interaction-flow-design.md`
- `tasks/20260717-tool-call-interceptor-capability.md`

## Backend Requirements

Build on Stage 1 notifications. Interactions are `kind: "interaction"` notifications with `status: "pending_response"` and a `response` field.

Add to `SessionNotifications` (DP13 — open, suggested same module):

```python
def create_interaction(
    self,
    session_id: str,
    interaction: dict,
    *,
    request_id: str | None = None,
) -> dict:
    """Create a kind=interaction notification. Returns the stored interaction."""

def respond_to_interaction(
    self,
    session_id: str,
    interaction_id: str,
    response: dict,
    *,
    request_id: str | None = None,
) -> dict:
    """Store the response, mark status=responded, signal the waiting interceptor."""

def resolve_interaction(
    self,
    session_id: str,
    interaction_id: str,
    resolution: dict,
    *,
    request_id: str | None = None,
) -> dict:
    """Mark status=resolved. Called by the interceptor after applying the response."""

def expire_interaction(
    self,
    session_id: str,
    interaction_id: str,
    *,
    request_id: str | None = None,
) -> dict:
    """Apply the default_action_id and mark status=expired. Called by the timeout handler."""
```

## Interceptor Integration

The tool-call interceptor (from `tasks/20260717-tool-call-interceptor-capability.md`) provides a pre-execution hook. A blocking interceptor implementation:

```python
class DummyBlockingInterceptor:
    def pre_execute(self, call, context, phase_state):
        # 1. Emit interaction
        interaction = context["notification_sink"].create_interaction({
            "key": "dummy:interaction:approve",
            "kind": "interaction",
            "status": "pending_response",
            "severity": "warning",
            "title": "Approve tool call?",
            "body": f"The tool `{call['tool_name']}` wants to run.",
            "source": { "plugin": "dummy_interceptor", "tool_name": call["tool_name"], "call_id": call["call_id"] },
            "display": { /* ActionDisplayPayload with Approve/Deny buttons */ },
            "timeout": { "seconds": 300, "default_action_id": "deny" },
        })
        interaction_id = interaction["id"]

        # 2. Wait for response (DP10 — open)
        response = self._wait_for_response(interaction_id, timeout_seconds=300, cancellation=context.get("cancellation"))

        # 3. Apply response
        if response is None or response.get("status") == "cancelled":
            return {"short_circuit": True, "result": {"role": "tool", "content": "cancelled", ...}}
        if response["action_id"] == "approve":
            return {"proceed": True}  # let the tool execute
        else:  # deny
            return {"short_circuit": True, "result": {"role": "tool", "content": "denied by user", ...}}
```

## Open Decision Point: DP10 — Wait-Only Signaling Mechanism

**Question:** How does the interceptor wait for the user response, and how does the action handler signal it?

### Option A: `concurrent.futures.Future` keyed by `interaction_id`

**Internal interface:**

```python
# On AgentApplication (process-local dict):
class AgentApplication:
    self._interaction_futures: Dict[str, concurrent.futures.Future] = {}

    def _register_interaction_future(self, interaction_id: str) -> concurrent.futures.Future:
        future = concurrent.futures.Future()
        self._interaction_futures[interaction_id] = future
        return future

    def _resolve_interaction_future(self, interaction_id: str, response: dict) -> None:
        future = self._interaction_futures.pop(interaction_id, None)
        if future is not None and not future.done():
            future.set_result(response)

    def _cancel_interaction_future(self, interaction_id: str) -> None:
        future = self._interaction_futures.pop(interaction_id, None)
        if future is not None and not future.done():
            future.set_result({"status": "cancelled"})
```

**Interceptor behavior:**

```python
def _wait_for_response(self, interaction_id, timeout_seconds, cancellation):
    future = self._app._register_interaction_future(interaction_id)
    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"status": "expired", "action_id": "deny"}
        if cancellation is not None and cancellation.is_cancelled():
            return {"status": "cancelled"}
        try:
            return future.result(timeout=min(remaining, 1.0))
        except concurrent.futures.TimeoutError:
            continue
```

**Action handler behavior:**

```python
def execute_action(self, app, action_id, params, context, state):
    if action_id == "respond_to_interaction":
        interaction_id = params["interaction_id"]
        response = {"action_id": params["action_id"], "values": params.get("values", {}), "status": "responded"}
        app.respond_to_interaction(session_id, interaction_id, response)
        app._resolve_interaction_future(interaction_id, response)
        return {"message": "Response submitted"}
```

**Pros:** Built-in timeout; simple API; `Future.set_result` is thread-safe.
**Cons:** Process-local (doesn't survive restart — fine for 2a); polling loop for cancellation (1s granularity).

### Option B: `threading.Event` + shared response dict

**Internal interface:**

```python
class InteractionWaiter:
    def __init__(self):
        self._event = threading.Event()
        self._response = None
        self._lock = threading.Lock()

    def set_response(self, response):
        with self._lock:
            self._response = response
        self._event.set()

    def wait(self, timeout, cancellation=None):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"status": "expired", "action_id": "deny"}
            if cancellation and cancellation.is_cancelled():
                return {"status": "cancelled"}
            if self._event.wait(timeout=min(remaining, 0.5)):
                with self._lock:
                    return self._response
```

**Pros:** More explicit control; no `Future` abstraction.
**Cons:** More code; same polling loop; no real advantage over Option A.

### Option C: `asyncio.Future` via `AsyncRuntimeHost`

**Internal interface:**

```python
# Interceptor runs async via AsyncRuntimeHost.run_blocking:
async def _wait_for_response_async(self, interaction_id, timeout):
    future = asyncio.get_event_loop().create_future()
    self._app._interaction_futures[interaction_id] = future
    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        return {"status": "expired", "action_id": "deny"}

def _wait_for_response(self, interaction_id, timeout_seconds, cancellation):
    return self._app._async_runtime_host.run_blocking(
        self._wait_for_response_async(interaction_id, timeout_seconds)
    )
```

**Pros:** Matches the existing async pattern; clean cancellation via `asyncio.wait_for`.
**Cons:** Forces the interceptor hook to bridge sync→async; the interceptor protocol may not assume async; more complex.

### Suggested choice

**Option A** — simplest, built-in timeout, thread-safe. The polling loop for cancellation is a small price for Stage 2a. Stage 2b replaces this with persistence + restart, so the in-memory mechanism is throwaway.

## Timeout Behavior

When the wait times out, `expire_interaction` is called:
- Applies `default_action_id` as the response.
- Marks `status: "expired"`.
- Publishes `session_notification_resolved` event with `resolution: { "action_id": "default_action_id", "reason": "expired" }`.
- Signals the waiting interceptor with the expired response.

## Cancellation Behavior

When the request is cancelled while an interceptor is waiting:
- The cancellation handler calls `_cancel_interaction_future(interaction_id)`.
- The interceptor's wait returns `{"status": "cancelled"}`.
- The interceptor returns a short-circuit "cancelled" tool result.
- The interaction is marked `status: "cancelled"`.
- `session_notification_resolved` event is published with `resolution: { "reason": "cancelled" }`.

## Safety Requirements

- A timed-out interaction must not leave a request permanently stuck (timeout is bounded).
- A cancelled request must publish a clear event and update interaction state.
- A stale response (e.g., response for an already-resolved interaction) must be rejected or treated as a no-op with a clear result.
- Response handling must be idempotent where practical (duplicate responses for the same interaction are no-ops).

## Dummy Plugin Coverage

Use simplistic dummy plugins, not MCP:

- Dummy blocking interceptor (provider extension):
  - `approve` → proceed with tool execution
  - `deny` → short-circuit with "denied by user" result
  - `run_followup` → short-circuit with a follow-up action result

- Dummy tool plugin:
  - emits an interaction before executing
  - user response controls returned result

The labels and semantics must remain plugin-defined test logic.

## Tests

Add `core/python/tests/test_session_interactions.py`:

- `test_create_interaction_persists_metadata` — create → reload → assert interaction in metadata.
- `test_respond_to_interaction_signals_interceptor` — create → respond → assert future resolved.
- `test_respond_to_interaction_stores_response` — create → respond → assert `status: "responded"`, `response` populated.
- `test_interaction_timeout_applies_default_action` — create with timeout → wait → assert `status: "expired"`, `default_action_id` applied.
- `test_interaction_cancellation_unblocks_wait` — create → cancel request → assert wait returns cancelled.
- `test_stale_response_is_noop` — create → respond → respond again → assert second response is no-op.
- `test_interaction_events_published` — create/respond/resolve/expire → assert events.
- `test_dummy_interceptor_approve_proceeds` — dummy interceptor → approve → tool executes.
- `test_dummy_interceptor_deny_short_circuits` — dummy interceptor → deny → tool does not execute, "denied" result returned.
- `test_dummy_interceptor_timeout_denies` — dummy interceptor → no response → timeout → `default_action_id: "deny"` applied.

Avoid MCP-specific names. Use generic names like `dummy:interaction:approve`.