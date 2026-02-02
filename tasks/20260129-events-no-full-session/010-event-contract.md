# Define minimal event contract (no full session payloads)

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Define the new event schema such that clients can apply events incrementally without ever receiving full session history inside events.

## Status

- [x] Completed

## Deliverables

- A clear list of event types and required fields.
- Explicit index/position semantics so delete/modify/append can be reduced without guessing.
- Compatibility plan (version flag or coordinated rollout).

## Event shapes (implemented)

### Session lifecycle

- `session_created`
  - Required: `type`, `event_id`, `session_id`
  - Optional: `agent_id`, `source_session_id`, `fork_upto_index`
  - No `session` payload.
  - Client behavior: bootstrap by fetching the session messages.

### Message mutations

- `message_appended`
  - Required: `session_id`, `index`, `message` (full message object)
  - Optional: `request_id`

- `message_modified`
  - Required: `session_id`, `index`, `message` (full post-modification message)
  - Do not include the full session.

- `messages_deleted`
  - Required: `session_id`, `indices: number[]`

### Request streaming / completion

- `request_started`, `assistant_message`, `partial`, `error`, `request_completed`, `request_cancelled`, `checkpoint` remain, but must not embed session.

- `final` and `tool_results`
  - Required: `session_id`, `request_id`, `messages: ApiMessage[]`, `start_index: number`
  - `start_index` is the core-session index where `messages[0]` lands.
  - This is generated server-side (application tool loop) at the time messages are appended.

## Index/ordering semantics (must be documented)

- Indices refer to the session message list indices *at the time the event is published*.
- `message_appended.index` must be the index in the post-append session.
- `messages_deleted.indices` refer to indices in the pre-delete session.
- After applying `messages_deleted`, subsequent indices shift down.

- `final.start_index` / `tool_results.start_index` refer to the message count *before* applying the event.

If a client cannot apply an event because its local history length or contents do not match expectations, it marks the session as `dirty`.

## Compatibility / rollout

Chosen:

1) **Hard cutover**: update producers + tests/docs together.

## Where to implement (later subtasks will do it)

- Producers: `application/python/agent_terminal_app/server.py`, `application/python/agent_terminal_app/terminal_app.py`, and potentially core request event generation in `core/python/agent_app/tool_loop.py` for `final/tool_results`.
- Consumers: `packages/frontend-sdk/src/types/events.ts`, new reducer module in SDK, `packages/frontend-sdk/src/chat/chatController.ts`.
