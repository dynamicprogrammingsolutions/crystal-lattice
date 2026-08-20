Mobile Streaming Message Display Plan
====================================

This document defines how the React Native mobile app
(`mobile/crystal-lattice-control-rn`) should render chat messages from
the event stream described in `docs/api/events.md`.

It focuses on:

- Stage 1 – Append-on-events display (no incremental streaming text).
- Stage 2 – True streaming display with partial tokens.

The event shapes and semantics are defined in `docs/api/events.md` and
must remain the single source of truth.


1. Goals and Constraints
------------------------

1.1 Functional goals

- Use the event stream as the **primary driver** of what appears in the
  chat view.
- Stage 1:
  - When processing events, append all message-carrying events to the
    in-memory `messages` array so the user sees them without needing a
    full reload.
  - When a request ends in an error, show the error to the user even if
    no final assistant message was produced.
  - Errors are **not** part of the persisted message history and should
    be cleared when a new request starts, the user refreshes, or a
    resend occurs.
- Stage 2:
  - Render true streaming text for assistant replies using `partial`
    events.
  - Maintain a single **ephemeral streaming row** at the bottom of the
    chat for the in-flight reply.
  - When the corresponding `final` event arrives, the streaming row is
    replaced seamlessly by the final content; users should not notice a
    distinct transition between partial and final components.
  - The streaming row is **never** written into the persisted message
    history.

1.2 Event types in scope

From `docs/api/events.md`:

- Request lifecycle:
  - `request_started`, `request_completed`, `request_cancelled`, `error`.
- Assistant streaming:
  - `assistant_message` (start/end), `partial`, `final`.
- Tools:
  - `tool_calls`, `tool_partial`, `tool_results`.
- Session/message lifecycle:
  - `session_created`, `message_appended`, `message_modified`,
    `messages_deleted`.
- Checkpointing:
  - Internal `session_checkpoint` (not exposed to mobile).
  - Public `checkpoint` marker events, used only for cursors.

We do **not** add new event types for this plan; all behaviour is
implemented on top of the existing shapes.

1.3 Constraints and assumptions

- We must not add per-message UUIDs in the core. All mapping between
  events and UI rows is done using:
  - `event_id` (for ordering and cursors), and
  - `request_id` (for grouping streaming phases).
- `/sessions/{id}/messages` + `cursor_event_id` remain the source of
  truth for persisted history. Event-driven updates must be consistent
  with what a reload would show, but they may show information more
  quickly.
- Errors (`type: "error"`) may occur:
  - Before any assistant content.
  - After some partial content has already been shown.
- We do **not** expose `error` as a message in the history; instead we
  show error UI outside the message list.


2. Stage 1 – Append-on-Events Display
-------------------------------------

Stage 1 improves the current behaviour without yet implementing
incremental streaming text. All updates come from discrete events that
carry full messages.

2.1 Message-carrying event types

For Stage 1, the chat view should append messages to its `messages`
array for **all events that carry user-visible messages**:

- `message_appended`
  - Append `ev.message` (if present) as a single row.
  - If `ev.message` is absent but `role`/`content` exist, synthesize a
    message object from those fields.

- `final`
  - Flatten `ev.messages` and append each entry in order.
  - This covers assistant messages and any tool/system messages the
    core chooses to emit in the final block.

- `tool_results`
  - Append each message in `ev.messages` as a tool row.
  - These tool messages are part of the core session history and will
    also appear on reload; checkpoint cursors ensure we do not see their
    events again after a snapshot.

- `session_created`, `message_modified`, `messages_deleted`
  - Do **not** append anything directly to the messages array.
  - These change the structure of the session; at Stage 1 we handle
    them indirectly:
    - Either by ignoring them for the main view and relying on reloads,
      or
    - By adding targeted logic (e.g., removing or updating a message at
      a specific index) in a later refinement.
  - All of them remain visible in the debug event overlay.

The initial implementation should focus on `message_appended`, `final`,
and `tool_results` for the main chat view.

2.2 Error display

Errors must be surfaced clearly but are **not** part of the message
history.

- When an `error` event is received for the active `request_id`:
  - Record an `activeError` state object for that session/request:
    - `activeError = { sessionId, requestId, detail }`.
  - Render a dedicated error component **below** the message list (or
    in a dedicated area of the chat screen).
  - If there is an in-flight partial streaming row (added in Stage 2),
    keep it visible alongside the error until the user starts a new
    request or reloads.

- Clearing errors:
  - When a new request starts for the same session (`request_started`
    with a new `request_id`), clear `activeError`.
  - When the user refreshes/reloads the session messages, clear
    `activeError`.
  - When the user resends the last prompt (starting a new request),
    clear `activeError`.

2.3 Relationship to checkpoints and reloads

- Event-driven append-on-events display is **optimistic** but must stay
  consistent with snapshot reloads.
- Because `cursor_event_id` is always at or after the relevant
  `message_appended`, `final`, and `tool_results` events:
  - After a reload, the UI should:
    - Replace the `messages` array with the snapshot from
      `/sessions/{id}/messages`.
    - Restart event consumption from `since_id = cursor_event_id`.
  - With this contract, event-driven appends will not be duplicated
    after reload.

2.4 Debug view

- The event debug overlay continues to:
  - Show **all** events as a scrollable list.
  - Allow tapping an event to see its full JSON payload.
- This is especially useful for verifying that the main chat view is
  rendering all message-carrying event types correctly.


3. Stage 2 – Streaming Display with Partials
--------------------------------------------

Stage 2 introduces a dedicated streaming row for in-flight assistant
replies, driven by `partial` and `assistant_message` events.

3.1 Streaming row model

Introduce a small in-memory model for streaming state, separate from
the persisted `messages` array:

- `StreamingRowState`
  - `sessionId: string`
  - `requestId: string`
  - `text: string`     // accumulated partial content
  - `metadata?: object`

- Each `SessionChatScreen` tracks at most **one** active streaming row
  per session (the most recent in-flight request).

- The streaming row is rendered **below** the persisted `messages`
  array, and is never written into that array.

3.2 Event handling for streaming

For a given `sessionId` and active `requestId`:

- `request_started`
  - Clear any stale `StreamingRowState` and `activeError` for that
    session.
  - Prepare to accept `partial` / `assistant_message` events.

- `assistant_message` (phase: "start")
  - Initialize `StreamingRowState` for this `requestId` with empty text.
  - Render a streaming row placeholder even if no `partial` has
    arrived yet.

- `partial`
  - If `StreamingRowState` for the matching `sessionId`/`requestId`
    exists, update its `text` by concatenating the new `message`
    content (or using provider-specific rules).
  - Re-render the streaming row with the updated text.
  - Do **not** touch the persisted `messages` array.

- `assistant_message` (phase: "end")
  - Optionally used as an additional fence; in our UI we can treat it
    as a signal that no more `partial` events are expected.
  - Do not modify the `messages` array.

- `final`
  - Append all messages from `ev.messages` to the persisted `messages`
    array (as in Stage 1).
  - Clear `StreamingRowState` for this `requestId` so the streaming row
    disappears.
  - The user experiences this as the streaming text being "replaced" by
    the final message(s), even though under the hood the streaming row
    is removed and new rows are appended.

- `error`
  - If there is an active streaming row, **leave it visible** while
    also showing the error component.
  - The error component explains that the request failed; the partial
    text remains until a new request or reload happens.
  - As in Stage 1, clear both the streaming row and `activeError` when
    a new request starts for the session, or when the user reloads or
    resends.

- `request_completed`
  - Treated as an end-of-request fence. It does not modify the
    `messages` array directly but can be used to ensure that any
    lingering streaming state is cleaned up if no `final` was
    delivered (e.g., error-only flows).

3.3 Keys and identity of the streaming row

We want the streaming row and the final row to feel like the **same**
message from the user’s perspective. Two considerations:

- React keys:
  - A simple approach for the streaming row is `key={requestId}`.
  - Persisted message rows can continue to use indices or other stable
    identifiers derived from the message list.
  - When `final` arrives, we:
    - Remove the streaming row (keyed by `requestId`).
    - Append final messages, which will likely use different keys
      (e.g., index-based).
  - In practice this is usually smooth enough that users do not notice
    the underlying replacement.

- Ideal but optional: reuse the same key
  - In an ideal design, the streaming row and the final row would share
    the same key so React treats them as the same component instance.
  - Achieving this would require a predictable mapping between
    `requestId` and the eventual message identity in the history (e.g.,
    a synthetic `messageKey = f(sessionId, requestId, phaseIndex)`).
  - Since the core does not expose per-message IDs and the number of
    final messages may vary, we treat this as an **optional
    enhancement** rather than a hard requirement.

For this plan, we commit only to the simpler, robust behaviour:

- Streaming row is an ephemeral UI element keyed by `requestId`.
- Final messages are appended to the history when `final` arrives.
- From the user’s perspective, the streaming row disappears and the
  final content appears in its place at the bottom of the chat.


4. Implementation Notes and Next Steps
--------------------------------------

- Stage 1 can be implemented entirely within the existing
  `SessionChatScreen` and `useSessionEvents` hook by expanding
  `handleEvents` to:
  - Append messages for `message_appended`, `final`, and `tool_results`.
  - Track `activeError` via `error` and `request_started` events.

- Stage 2 adds:
  - `StreamingRowState` to `SessionChatScreen` (or a dedicated hook).
  - Event handling for `assistant_message` and `partial` to maintain the
    streaming row.
  - Integration with error handling so partial content remains visible
    until an error is fully surfaced.

- Throughout both stages, the event debug overlay should remain
  available to validate that the UI logic matches the raw stream of
  events described in `docs/api/events.md`.
