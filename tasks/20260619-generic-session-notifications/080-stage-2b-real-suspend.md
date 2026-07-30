# Stage 2b Backend — Real Suspend Interactions

Implement backend support for generic interactive notifications that suspend the request (short-circuit with a pending result) and resume via request restart. The interceptor does not hold a thread; the action handler restarts the request on response.

## Requirements checklist

- [ ] Implement short-circuit-with-pending: interceptor returns a "pending" tool result; request completes normally.
- [ ] Persist interaction + tool-call context in `Session.metadata`.
- [ ] Implement request restart on response (DP11 — open).
- [ ] Implement interceptor idempotency on restart (check resolved interaction by key before blocking).
- [ ] Add timeout with default behavior (no thread to unblock; timeout handler marks expired and optionally restarts).
- [ ] Add cancellation/resolution behavior.
- [ ] Add dummy plugin tests for the real-suspend flow.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:
- `tasks/20260619-generic-session-notifications/060-stage-2a-backend-wait-only.md`
- `tasks/20260619-generic-session-notifications/070-stage-2a-sdk-and-rn-tests.md`
- `tasks/20260717-tool-call-interceptor-capability.md`

## Backend Requirements

Build on Stage 2a. The key difference: the interceptor does not wait. It short-circuits with a "pending" tool result, and the request completes. The response is stored persistently, and the request is restarted.

### Interaction lifecycle in Stage 2b

```text
pending_response → suspended → responded → resolved
                              ↘ expired
                              ↘ cancelled
```

- `pending_response` → `suspended`: interceptor short-circuits, request completes.
- `suspended` → `responded`: user responds; action handler stores response.
- `responded` → `resolved`: request restart completes; interceptor applies response.
- `suspended` → `expired`: timeout.
- `suspended` → `cancelled`: request cancelled (e.g., user deletes session).

### Short-circuit with pending

The interceptor's pre-execution hook:

```python
def pre_execute(self, call, context, phase_state):
    # 1. Check if there's already a resolved interaction for this key (idempotency)
    existing = context["notification_sink"].list_by_key("dummy:interaction:approve")
    if existing and existing["status"] == "responded":
        response = existing["response"]
        if response["action_id"] == "approve":
            return {"proceed": True}
        else:
            return {"short_circuit": True, "result": {"role": "tool", "content": "denied", ...}}

    # 2. No resolved interaction; emit and short-circuit with pending
    context["notification_sink"].create_interaction({
        "key": "dummy:interaction:approve",
        "kind": "interaction",
        "status": "pending_response",
        "source": { "plugin": "dummy_interceptor", "tool_name": call["tool_name"], "call_id": call["call_id"] },
        "display": { /* Approve/Deny buttons */ },
        "timeout": { "seconds": 300, "default_action_id": "deny" },
    })
    return {"short_circuit": True, "result": {
        "role": "tool",
        "content": "pending user approval",
        "metadata": {"pending_interaction": True, "interaction_key": "dummy:interaction:approve"}
    }}
```

The request completes with the pending tool result. The LLM sees the "pending user approval" message and can end its turn.

### Request restart on response

The `respond_to_interaction` action handler:

```python
def execute_action(self, app, action_id, params, context, state):
    if action_id == "respond_to_interaction":
        interaction_id = params["interaction_id"]
        response = {"action_id": params["action_id"], "values": params.get("values", {}), "status": "responded"}
        # 1. Store response in the interaction
        app.respond_to_interaction(session_id, interaction_id, response)
        # 2. Restart the request (DP11 — open)
        app.send_request(session_id, ...)  # synthetic "continue" turn
        return {"message": "Response submitted; request restarted"}
```

On restart, the LLM continues, calls the tool again (or the tool loop replays the pending call), and the interceptor sees the resolved interaction and applies the response.

## Open Decision Point: DP11 — Real Suspend Request Restart Mechanism

**Question:** How does the action handler restart the request, and how does the interceptor become idempotent on restart?

### Option A: Synthetic "continue" turn + interceptor idempotency by key

**Public interface:**

```python
# Action handler calls send_request with a synthetic turn:
app.send_request(
    session_id,
    user_message={"role": "user", "content": "[system] Interaction resolved, continuing."},
    # or a special "continue" flag
)
```

**Interceptor idempotency:**

```python
def pre_execute(self, call, context, phase_state):
    key = self._interaction_key(call)
    existing = context["notification_sink"].list_by_key(key)
    if existing and existing["status"] in ("responded", "resolved"):
        response = existing["response"]
        if response["action_id"] == "approve":
            return {"proceed": True}
        else:
            return {"short_circuit": True, "result": {"role": "tool", "content": "denied", ...}}
    # No resolved interaction; emit and short-circuit
    context["notification_sink"].create_interaction({...})
    return {"short_circuit": True, "result": {"role": "tool", "content": "pending", ...}}
```

**Behavior:**
1. User responds → action handler stores response, calls `send_request` with synthetic turn.
2. LLM continues, calls the tool again (or the tool loop replays).
3. Interceptor's `pre_execute` runs again, sees the resolved interaction by key, applies the response.

**Example transcript:**
```text
[user]    Run the dummy tool
[assistant] tool_call(dummy_tool)
[tool]    pending user approval
[user]    [system] Interaction resolved, continuing.
[assistant] tool_call(dummy_tool)          # re-issued
[tool]    approved result                  # interceptor applied approve
[assistant] The tool returned: approved result
```

**Pros:** Simplest correct approach; reuses `send_request`; interceptor handles idempotency via the same dedupe mechanism from Stage 1.
**Cons:** The LLM sees an extra "pending user approval" tool result + synthetic turn in history; may confuse some models. The interceptor must be idempotent.

### Option B: Restore pre-interception state and replay the tool loop

**Public interface:**

```python
# Action handler restores the session to the pre-interception state:
app.restore_session_to_checkpoint(session_id, checkpoint_event_id)
# Then restarts the request:
app.send_request(session_id, ...)
```

**Behavior:**
1. Action handler restores the session to the state before the tool call.
2. Restarts the request; the LLM re-issues the same tool call.
3. Interceptor sees the resolved interaction and applies the response.

**Example transcript (after restore):**
```text
[user]    Run the dummy tool
[assistant] tool_call(dummy_tool)          # re-issued after restore
[tool]    approved result                  # interceptor applied approve
[assistant] The tool returned: approved result
```

**Pros:** No synthetic turn in history; cleaner transcript.
**Cons:** Requires snapshotting and restoring; fragile; may lose other state changes; the restored session may conflict with concurrent modifications.

### Option C: Inject the tool result directly, bypass the interceptor

**Public interface:**

```python
# Action handler injects the tool result and calls the LLM:
app.inject_tool_result(session_id, call_id, result)
app.continue_request(session_id)
```

**Behavior:**
1. Action handler synthesizes the tool result from the response.
2. Injects it into the session.
3. Calls the LLM with the extended history.

**Example transcript:**
```text
[user]    Run the dummy tool
[assistant] tool_call(dummy_tool)
[tool]    approved result                  # injected by action handler
[assistant] The tool returned: approved result
```

**Pros:** Simplest; no restart; no interceptor re-invocation.
**Cons:** Bypasses the interceptor; loses "interceptor passes through" semantics; the interceptor's `post_execute` hook doesn't run; requires a new `inject_tool_result` API.

### Suggested choice

**Option A** — matches the user's description ("response stored in session file, request restarted within the action handler") and keeps the interceptor in the loop. Idempotency-by-key is the same dedupe mechanism Stage 1 already provides. The extra "pending" tool result in history is acceptable for Stage 2b; a future refinement could suppress it.

## Timeout Behavior (Stage 2b)

When the timeout expires, there's no waiting thread to unblock. The timeout handler:
- Marks the interaction `status: "expired"`.
- Applies `default_action_id`.
- Optionally restarts the request (if the request was suspended, not yet completed).

If the request already completed (suspended state), the timeout just marks the interaction expired; no restart is needed (the interaction is already in history as a pending result).

## Cancellation Behavior (Stage 2b)

If the user cancels the session or deletes it while an interaction is suspended:
- The interaction is marked `status: "cancelled"`.
- No restart is triggered.
- `session_notification_resolved` event is published with `resolution: { "reason": "cancelled" }`.

## Safety Requirements

- A suspended interaction must not leave the request in an inconsistent state.
- The interceptor must be idempotent on restart (check by key before blocking).
- A stale response (e.g., response for an already-resolved interaction) must be rejected or treated as a no-op.
- Response handling must be idempotent where practical.

## Dummy Plugin Coverage

Use simplistic dummy plugins, not MCP:

- Dummy real-suspend interceptor:
  - `approve` → on restart, proceed with tool execution
  - `deny` → on restart, short-circuit with "denied" result
  - `run_followup` → on restart, short-circuit with a follow-up action result

- Dummy tool plugin:
  - emits an interaction before executing
  - on restart, user response controls returned result

## Tests

Add `core/python/tests/test_session_interactions_real_suspend.py`:

- `test_short_circuit_with_pending_completes_request` — interceptor short-circuits → request completes → interaction `status: "suspended"`.
- `test_respond_restarts_request_and_applies_response` — respond → restart → interceptor applies response → tool executes (approve) or short-circuits (deny).
- `test_interceptor_idempotency_on_restart` — restart → interceptor sees resolved interaction → does not emit a new one.
- `test_timeout_marks_expired` — timeout → `status: "expired"`, `default_action_id` applied.
- `test_cancel_marks_cancelled` — cancel session → `status: "cancelled"`.
- `test_stale_response_is_noop` — respond → respond again → second is no-op.
- `test_interaction_events_published` — create/respond/restart/resolve → assert events.

Avoid MCP-specific names. Use generic names like `dummy:interaction:approve`.

## SDK And React Native Tests

Add `packages/frontend-sdk/src/integration/__tests__/sessionInteractionsRealSuspend.integration.test.ts` and `mobile/crystal-lattice-control-rn/__integration__/SessionInteractionsRealSuspend.realBackend.integration.test.tsx` following the Stage 2a patterns.

Test flow:
1. Start backend with dummy real-suspend interceptor.
2. Send a request → assert interaction `status: "suspended"`, request completed.
3. Respond → assert request restarted, interaction `status: "resolved"`.
4. Assert the tool executed (approve) or short-circuited (deny).