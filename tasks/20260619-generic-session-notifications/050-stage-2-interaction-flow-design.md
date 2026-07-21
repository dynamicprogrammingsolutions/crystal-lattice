# Stage 2 Interaction Flow Design

Design blocking or semi-blocking user interactions on top of the generic notification substrate. This stage supports prompts that can pause/resume request or tool progress, but only after Stage 1 notifications are proven.

## Requirements checklist

- [ ] Define interaction lifecycle states for Stage 2a (wait-only) and Stage 2b (real suspend).
- [ ] Define request/tool suspension and timeout behavior.
- [ ] Define how action forms submit interaction responses.
- [ ] Define persistence and event semantics for responses.
- [ ] Define how Stage 2 reuses Stage 1 notification rendering.
- [ ] Reference the tool-call interceptor task as a co-dependency for the blocking-via-tool-call flow.
- [ ] Compare reusable ideas from CL-150 without adopting its implementation wholesale.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:
- `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`
- `tasks/20260717-tool-call-interceptor-capability.md` (for the blocking-via-tool-call flow)

## Target User Flow

The motivating flow (combined with the tool-call interceptor task):

1. Request sent.
2. LLM calls a tool.
3. Tool call interceptor blocks the tool call and emits a notification with a display and buttons assigned to actions.
4. User responds; action is sent to the server.
5. Tool call interceptor passes through the tool call upon response.

This flow is generic. Core does not hardcode labels like "allow", "deny", or "continue". The interceptor implementation (a provider extension or plugin) defines the actions and semantics.

## Relationship To The Tool-Call Interceptor Task

`tasks/20260717-tool-call-interceptor-capability.md` adds a provider-neutral pre/post-execution hook in `ToolLoopRunner` with three capabilities: parameter modification, short-circuit (return any result), and result modification.

For the blocking flow:
- The interceptor's **pre-execution hook** is the suspension point. It emits an interaction notification, then either waits (Stage 2a) or short-circuits with a pending result (Stage 2b).
- The interceptor task stays generic and provider-neutral. The *implementation* of a blocking interceptor uses the notifications substrate from this task.
- Stage 2a and 2b of this task own the end-to-end proof; the interceptor task's own tests stay provider-neutral (no notification references).

## Two Suspension Strategies

### Stage 2a — Wait-Only (simpler, start here)

- Interceptor's pre-execution hook emits an `interaction` notification, then blocks on a signaling primitive keyed by `interaction_id` (with timeout + cancellation support).
- The plugin's `respond_to_interaction` action stores the response, resolves the notification, and signals the waiting interceptor.
- The interceptor's wait returns; it returns the response as the short-circuit tool result.
- The request stays in-flight the whole time. No restart needed.
- Downsides: holds the request thread open; doesn't survive server restart; timeout/cancellation must be wired carefully.

### Stage 2b — Real Suspend (ideal, follow-up)

- Interceptor's pre-execution hook emits an `interaction` notification, short-circuits with a "pending" tool result, and the request completes normally (no thread held).
- Session is saved with the pending interaction + tool-call context.
- The plugin's `respond_to_interaction` action stores the response in the notification's `resolution`, then calls `app.send_request(...)` to restart the request.
- On restart, the interceptor sees the resolved interaction (by `key`) and either passes the tool call through or uses the stored response directly.
- Downsides: requires request restart logic; interceptor must be idempotent on restart; more complex.

## Proposed Lifecycle

Notifications are extended with `kind: "interaction"`:

```json
{
  "id": "notif_<uuid>",
  "key": "dummy:interaction:approve",
  "kind": "interaction",
  "status": "pending_response",
  "severity": "warning",
  "title": "Approve tool call?",
  "body": "The tool `dummy_tool` wants to run. Do you want to allow it?",
  "created_at": "...",
  "updated_at": "...",
  "request_id": "req_...",
  "source": { "plugin": "dummy_interceptor", "tool_name": "dummy_tool", "call_id": "call_..." },
  "display": {
    "format": "markdown",
    "body": "The tool `dummy_tool` wants to run. Do you want to allow it?",
    "title": "Approve tool call?",
    "variant": "warning",
    "presentation": "inline",
    "dismissible": false,
    "actions": [
      { "kind": "run_action", "id": "approve", "label": "Approve", "plugin": "dummy_interceptor_app", "action_id": "respond_to_interaction", "fixed_params": { "interaction_id": "notif_<uuid>", "action_id": "approve" } },
      { "kind": "run_action", "id": "deny", "label": "Deny", "plugin": "dummy_interceptor_app", "action_id": "respond_to_interaction", "fixed_params": { "interaction_id": "notif_<uuid>", "action_id": "deny" } }
    ]
  },
  "response": null,
  "resolution": null,
  "timeout": { "seconds": 300, "default_action_id": "deny" },
  "model_visibility": "hidden"
}
```

### Statuses

Stage 2a:
- `pending_response` — emitted, waiting for user response
- `responded` — user responded; response stored; interceptor unblocked
- `resolved` — interaction completed (response applied); final state
- `cancelled` — request cancelled while waiting; final state
- `expired` — timeout reached; `default_action_id` applied; final state

Stage 2b adds:
- `suspended` — request completed with pending result; waiting for restart
- (on restart) transitions back to `responded` → `resolved`

## Response Submission

Responses are submitted through the existing application action flow. The notification's `display.actions[]` includes `run_action` buttons that call a plugin-defined `respond_to_interaction` action. The action handler:
1. Validates the response against the pending interaction.
2. Stores the response in the notification's `response` field.
3. Resolves the notification (Stage 2a: signals waiting interceptor; Stage 2b: triggers request restart).
4. Publishes `session_notification_responded` event.

No dedicated HTTP endpoint is added (see DP12 — open).

## Reuse Of Stage 1 Rendering

Stage 2 interactions reuse the same `ActionDisplayPayload` + `ActionResultInlineCard` + `SessionNotificationsHost` from Stage 1. The `kind: "interaction"` field is the only addition; the RN host renders interactions and notifications identically (the display drives the UI).

## Open Decision Points

The following decision points are deferred for later review. They are detailed in the respective subtask files:

- **DP10: Wait-only signaling mechanism** — see `060-stage-2a-backend-wait-only.md`.
- **DP11: Real suspend — request restart mechanism** — see `080-stage-2b-real-suspend.md`.
- **DP12: Interaction response routing** — see below.
- **DP13: Interaction lifecycle — same module as notifications or separate** — see below.

### DP12: Interaction Response Routing

**Question:** Should interaction responses go through the existing application action flow, or a dedicated HTTP endpoint?

**Public interface (Option A — existing action flow):**

```python
# Plugin defines an action:
{
  "id": "respond_to_interaction",
  "label": "Respond",
  "inputs": {
    "interaction_id": {"type": "string", "required": True},
    "action_id": {"type": "string", "required": True},
    "values": {"type": "object", "required": False}
  }
}

# Frontend calls existing endpoint:
POST /sessions/{session_id}/actions
{
  "plugin": "dummy_interceptor_app",
  "action_id": "respond_to_interaction",
  "inputs": { "interaction_id": "notif_...", "action_id": "approve" }
}
```

**Public interface (Option B — dedicated endpoint):**

```http
POST /sessions/{session_id}/notifications/{notification_id}/respond
{ "action_id": "approve", "values": {} }
```

**Behavior:**
- Option A: reuses existing action execution, idempotency, deep-link routing. The plugin handles resolution + signaling in `execute_action`. Works with mobile deep-link callbacks (`crystal-lattice://action/...`).
- Option B: more REST-conventional, but duplicates action execution logic, idempotency, and deep-link routing. Requires new SDK method + RN handler.

**Example (Option A):**

Notification display action:
```json
{
  "kind": "run_action",
  "id": "approve",
  "label": "Approve",
  "plugin": "dummy_interceptor_app",
  "action_id": "respond_to_interaction",
  "fixed_params": { "interaction_id": "notif_123", "action_id": "approve" }
}
```

Mobile deep-link:
```text
crystal-lattice://action/<connection-id>/<session-id>/dummy_interceptor_app/respond_to_interaction?interaction_id=notif_123&action_id=approve
```

**Suggested choice:** A — reuses existing infrastructure and deep-link routing; no new HTTP surface area. (Consistent with Stage 1 DP7.)

### DP13: Interaction Lifecycle — Same Module As Notifications Or Separate

**Question:** Should interaction methods live in `core/python/agent_app/notifications.py` (same module) or a new `core/python/agent_app/interactions.py` (separate module)?

**Public interface (Option A — same module):**

```python
# core/python/agent_app/notifications.py
class SessionNotifications:
    def create(self, ...) -> dict: ...           # Stage 1
    def update(self, ...) -> dict: ...           # Stage 1
    def resolve(self, ...) -> dict: ...          # Stage 1
    def create_interaction(self, ...) -> dict: ...       # Stage 2
    def respond_to_interaction(self, ...) -> dict: ...   # Stage 2
    def resolve_interaction(self, ...) -> dict: ...      # Stage 2
    def expire_interaction(self, ...) -> dict: ...       # Stage 2

# AgentApplication thin methods:
app.create_session_notification(...)
app.create_session_interaction(...)
app.respond_to_interaction(...)
```

**Public interface (Option B — separate module):**

```python
# core/python/agent_app/notifications.py
class SessionNotifications:
    def create(self, ...) -> dict: ...
    def update(self, ...) -> dict: ...
    def resolve(self, ...) -> dict: ...

# core/python/agent_app/interactions.py
class SessionInteractions:
    def __init__(self, notifications: SessionNotifications): ...
    def create(self, ...) -> dict: ...
    def respond(self, ...) -> dict: ...
    def resolve(self, ...) -> dict: ...
    def expire(self, ...) -> dict: ...
```

**Behavior:**
- Option A: single persistence path (`Session.metadata["notifications"]["items"]`), shared event types, `kind` field distinguishes. One module, one set of helpers. Matches "don't copy CL-150's separate prompt store" principle.
- Option B: cleaner separation of concerns, but duplicated event types, duplicated persistence logic, and extra indirection (`SessionInteractions` wraps `SessionNotifications`).

**Example (Option A):**

```python
# Interactions and notifications share the same list:
metadata["notifications"]["items"] = [
  { "id": "notif_1", "kind": "notification", "status": "pending", ... },
  { "id": "notif_2", "kind": "interaction", "status": "pending_response", ... },
]

# Same event types:
{ "type": "session_notification_created", "notification": { "kind": "notification", ... } }
{ "type": "session_notification_created", "notification": { "kind": "interaction", ... } }
# Or separate event types:
{ "type": "session_interaction_created", "interaction": { ... } }
```

**Suggested choice:** A — interactions are a specialization of notifications (same persistence, same UI, same event stream). One module is simpler. (Consistent with the "don't copy CL-150" principle.)

## Relationship To CL-150

CL-150 includes:
- prompt lifecycle events
- pending prompt selectors
- prompt response endpoint
- suspend/resume behavior

Reusable ideas:
- pending/resolved lifecycle
- explicit response payload
- evented prompt creation
- frontend selector over persisted state

Do not reuse directly without redesign because:
- it is coupled to tool-call/tool-result interception
- it stores prompt state in assistant message metadata
- it introduces broad directive semantics all at once
- the branch has significant unrelated churn

## Open Questions (Stage 2b)

- Should Stage 2b initially support only request preparation waits, or full tool execution waits? (Stage 2a already covers tool execution waits via the interceptor hook.)
- What is the default behavior when the user does not respond? (Timeout → `default_action_id`.)
- How should cancellation interact with already-started provider requests? (Cancel unblocks the wait; the interceptor returns a cancelled result.)
- Should interactions be model-visible in any cases? (Default `hidden`; future `summary` may summarize the interaction for the model.)