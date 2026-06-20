# Stage 2 Backend Interaction Lifecycle

Implement backend support for generic interactive notifications that can wait for user input and resume or resolve work according to plugin-defined action semantics.

## Requirements checklist

- [ ] Implement interaction response persistence and events.
- [ ] Add request/tool wait hooks only after the Stage 2 design is approved.
- [ ] Add timeout/default behavior.
- [ ] Add cancellation/resolution behavior.
- [ ] Add dummy plugin tests for interaction choices.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:

- `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- `tasks/20260619-generic-session-notifications/050-stage-2-interaction-flow-design.md`

## Backend Requirements

The implementation should build on Stage 1 notifications rather than create a separate prompt store.

Add support for:

- creating `kind: "interaction"` notifications
- responding to interactions
- recording response payloads
- publishing response/resolution events
- optionally pausing/resuming request or tool progress

## Dummy Plugin Coverage

Use simplistic dummy plugins, not MCP, to test interaction semantics:

- dummy request/preparation interaction:
  - choice A: continue
  - choice B: cancel/fail
  - choice C: run a follow-up action
- dummy tool interaction:
  - emits an interaction before returning a result
  - user response controls returned result

The labels and semantics must remain plugin-defined test logic.

## Safety Requirements

- A timed-out interaction must not leave a request permanently stuck.
- A cancelled request must publish a clear event and update notification state.
- A stale response must be rejected or treated as a no-op with a clear result.
- Response handling must be idempotent where practical.