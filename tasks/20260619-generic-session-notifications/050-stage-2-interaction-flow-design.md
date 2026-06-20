# Stage 2 Interaction Flow Design

Design blocking or semi-blocking user interactions on top of the generic notification substrate. This stage should support prompts that can pause/resume request or tool progress, but only after Stage 1 notifications are proven.

## Requirements checklist

- [ ] Define interaction lifecycle states.
- [ ] Define request/tool suspension and timeout behavior.
- [ ] Define how action forms submit interaction responses.
- [ ] Define persistence and event semantics for responses.
- [ ] Define how Stage 2 reuses Stage 1 notification rendering.
- [ ] Compare reusable ideas from CL-150 without adopting its implementation wholesale.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On: `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`

## Target Use Case

The motivating MCP flow is:

1. Request starts.
2. MCP server startup determines one server requires login.
3. Backend sends an interaction to the user:
   - Cancel the request
   - Continue without login
   - Start login
4. Backend applies the selected outcome.

This should be generic. Core should not hardcode these labels or meanings.

## Proposed Lifecycle

Notifications can be extended with:

```json
{
  "kind": "interaction",
  "status": "pending_response",
  "response": null,
  "timeout": {
    "seconds": 300,
    "default_action_id": "continue"
  }
}
```

Possible statuses:

- `pending_response`
- `responded`
- `resolved`
- `cancelled`
- `expired`

## Response Submission

Prefer reusing existing action execution. A `run_action` button can submit an interaction response by calling an application action with `notification_id` / `interaction_id`.

If a dedicated endpoint is needed, design it as generic:

```http
POST /sessions/{session_id}/notifications/{notification_id}/respond
```

with payload:

```json
{
  "action_id": "continue",
  "values": {}
}
```

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

## Open Questions

- Should Stage 2 initially support only request preparation waits, or full tool execution waits?
- What is the default behavior when the user does not respond?
- How should cancellation interact with already-started provider requests?
- Should interactions be model-visible in any cases?