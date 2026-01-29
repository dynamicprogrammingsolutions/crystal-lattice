# Remove full session history from events; add SDK reducer + dirty fallback; eliminate frontend reloads

This task changes the event contract so events **never** embed a full serialized session (no `session: {messages: [...]}` in events). Clients should bootstrap by fetching session history once, then keep state correct by applying incremental events via a **pure reducer** in `@crystal-lattice/frontend-sdk`.

The frontend should stop doing unconditional full reloads (especially after send); reload becomes a fallback only when the reducer cannot apply an event safely (mark session as **dirty**).

This is a standalone task (not a subtask of the frontend SDK extraction), because it touches both the Python event producers and the TypeScript SDK/frontends.

## Requirements (paraphrased)

- Events must never contain full session history.
- `session_created` events should contain only the new `session_id` (and optional metadata like `agent_id`, `source_session_id`). Clients fetch the session messages once to bootstrap.
- All other session mutation events must contain **just enough information** to update a client that has the previous session state and has applied prior events.
- The SDK must provide a **pure reducer** that takes `(messageHistory, event) -> newMessageHistory` (and returns whether the session should be considered dirty).
- Frontends must remove all unconditional full reloads; reload only when dirty or on explicit user action.

## Status checklist

- [ ] Define new minimal event schemas (including indices/positions)
- [ ] Update Python event producers to stop embedding `session`
- [ ] Update Python tests/docs to reflect new event schema
- [ ] Update TypeScript SDK event types to match
- [ ] Implement SDK pure reducer + dirty semantics
- [ ] Update `ChatController` to use reducer, track cursor(s), and expose `dirty`
- [ ] Remove unconditional reloads from the mobile frontend (send/resend, delete/modify)

## Subtasks

- `tasks/20260129-events-no-full-session/005-sdk-reducer-prep-no-ux-change.md`
- `tasks/20260129-events-no-full-session/010-event-contract.md`
- `tasks/20260129-events-no-full-session/020-python-event-producers.md`
- `tasks/20260129-events-no-full-session/030-python-tests-and-docs.md`
- `tasks/20260129-events-no-full-session/040-sdk-event-types.md`
- `tasks/20260129-events-no-full-session/050-sdk-pure-reducer.md`
- `tasks/20260129-events-no-full-session/060-chatcontroller-integration.md`
- `tasks/20260129-events-no-full-session/070-mobile-remove-reloads.md`

## Current state (what exists today)

### Python: several events embed full sessions

In `application/python/agent_terminal_app/server.py`, these published events include `"session": new_session.to_dict()` (which contains the full `messages` list):

- `session_created`: `application/python/agent_terminal_app/server.py:410`
- `message_appended`: `application/python/agent_terminal_app/server.py:742`
- `message_modified`: `application/python/agent_terminal_app/server.py:1025`
- `messages_deleted`: `application/python/agent_terminal_app/server.py:1223`
- `session_created` (fork): `application/python/agent_terminal_app/server.py:1663`

In `application/python/agent_terminal_app/terminal_app.py`, similar events embed full sessions:

- `session_created`: `application/python/agent_terminal_app/terminal_app.py:120`
- `message_appended`: `application/python/agent_terminal_app/terminal_app.py:246`
- `messages_deleted`: `application/python/agent_terminal_app/terminal_app.py:422`
- `message_modified`: `application/python/agent_terminal_app/terminal_app.py:600`
- `message_appended` (append to arbitrary session): `application/python/agent_terminal_app/terminal_app.py:789`

### TypeScript: event types are loose and controller “guesses indices”

- SDK event types allow extra properties (`[key: string]: any`): `packages/frontend-sdk/src/types/events.ts:1`
- `ChatController` appends messages by “lastIndex + 1” on several event types:
  - `packages/frontend-sdk/src/chat/chatController.ts:278` (`final`)
  - `packages/frontend-sdk/src/chat/chatController.ts:293` (`message_appended`)
  - `packages/frontend-sdk/src/chat/chatController.ts:305` (`tool_results`)

This guessing becomes fragile once delete/modify are supported without reload.

### Mobile frontend: still does full reloads

- `handleSend()` and `handleResend()` call `loadMessages()` after send: `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:441`

## Implementation notes / relationship to other plans

- This task intentionally **removes** any plan that relies on consuming `event.session.messages`.
- The previous “Phase 4.4” frontend cleanup plan must be adjusted to the new contract; this task supersedes the “use full session snapshot in events” idea.
