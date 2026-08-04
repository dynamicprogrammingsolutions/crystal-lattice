# Event Stream Types

This document describes the **event types** produced by the application
layer (`AgentApplication` + `ToolLoopRunner`) and exposed via:

- HTTP polling: `GET /events` in `application/python/agent_terminal_app/server.py`
- Bridge streaming: `session_event` messages forwarded by
  `application/python/agent_terminal_app/bridge_client.py` and
  `bridge-elixir`.

Each event is a JSON object stored in an `EventStore` implementation
(`core/python/agent_app/events.py`) and augmented with a monotonically
increasing string `event_id` when published.

---

## Application and session notifications

Notification lifecycle events reuse `GET /events` and
`ActionDisplayPayload`.

Application notifications are stored durably by the runtime-injected
`ApplicationNotificationStore`:

- `application_notification_created`
- `application_notification_updated`
- `application_notification_dismissed`
- `application_notification_expired`
- omit `session_id` and are polled without a session filter
- survive `AgentApplication` replacement and server-process restart
- retain terminal history until retention removes it
- apply TTL only when a frontend freshly presents a notification; TTL does
  not emit an event or remove an already displayed notification
- rehydrate through `GET /application/notifications`; event replay remains
  best effort and is not the persistence authority

Session notifications are persisted under
`Session.metadata.notifications.items`:

- `session_notification_created`
- `session_notification_updated`
- `session_notification_resolved`
- `session_notification_dismissed`
- `session_notification_expired`
- include `session_id` and use ordinary session-filtered polling
- reload from session metadata on reconnect
- remain hidden from model/provider history in Stage 1

Both records have stable `id` and `key`, an integer `revision`,
pending/dismissed/resolved/expired status, info/success/warning/error severity,
title/body, timestamps, source provenance, an action display, and
`model_visibility: "hidden"`. Created/updated events upsert by `id`; creating
with the key of an active notification updates it in place. Creating with the
key of a terminal notification creates a new lifecycle occurrence.

Server-side dismiss, resolve, and expire mutations retain terminal records for
authoritative listing. Existing records without `revision` accept their
`updated_at` as the compatibility expected-revision token and gain integer
revision `1` on first mutation.

Mobile Dismiss controls cache and hide the exact displayed revision before
using the server mutation routes. A failed request is retried for that
unchanged revision during reconnect/rehydration; a newer revision invalidates
the cache and remains presentable. Desktop uses server-authoritative
success-only dismissal: a failed mutation leaves the notification visible.

Notification delivery is best effort. Event publication and the tool-facing
`notification_sink` cannot fail the user request.

### Notification state endpoints

```text
GET  /application/notifications
POST /application/notifications/{notification_id}/dismiss
GET  /sessions/{session_id}/notifications
POST /sessions/{session_id}/notifications/{notification_id}/dismiss
```

List endpoints return active records by default. Set
`include_terminal=true` to include dismissed, resolved, and expired records.
Dismiss accepts optional `expected_revision` and `reason` fields. A stale
revision or invalid lifecycle transition returns HTTP 409 with the current
notification record.

### Standard display presentations

Presentation support depends on the producer and host:

| Producer | `banner` | `inline` | `modal` |
| --- | --- | --- | --- |
| Application notification | Mobile Sessions rail; aggregated desktop message/detail rail | Rejected because no application-global inline owner exists | Mobile Sessions modal; desktop normalizes to inline in the aggregated message/detail rail |
| Session notification | Matching mobile Chat rail; active desktop ChatPane rail | Persistent matching-Chat notification region | Matching mobile Chat modal; desktop normalizes to inline in the active ChatPane rail |
| Direct action response | Owning mobile Sessions/Chat rail; connection-level or active-session desktop rail | Nearest owning Sessions or Chat region | Mobile modal on the owning screen; desktop normalizes to the corresponding rail |

On mobile, application notifications render only on Sessions below the
search/filter row. Session notifications render only on the exact matching Chat
below its header. Both rails participate in normal layout and push
session-list/transcript content down. Displays received while another surface
is active remain pending until their owning surface opens. Connection and
session labels are omitted because placement supplies that context.

Desktop aggregates connection-level notifications from every open connection
in one normal-flow rail in the message/detail area. Each connection-level card
includes the friendly connection name, falling back to connection id. The
active ChatPane contributes its own session notifications to the same visual
location without a redundant session label. When no ChatPane is open, the
connection-level rail remains above the detail placeholder.

Direct action responses without a presentation default to `modal`; session
notifications default to `inline`. Application notifications must use
`banner` or `modal`; attempts to create an inline application notification are
rejected by the application contract.

Display ownership is independent from storage lifetime. Application
notifications are connection-level. Session notifications are session-level
and require `session_id`. Direct action responses default to session ownership
when they carry `session_id`, while session-list/application surfaces may
explicitly retain connection ownership.

---

## Storage and Transport

- **Event store protocol**: `core/python/agent_app/events.py`
  - `EventStore` interface (`publish`, `list`).
  - `InMemoryEventStore` adds `event_id: str` on `publish`.

- **Application event producer**: `core/python/agent_app/application_future.py`
  - `AgentApplication.send_request(...)` yields events from
    `ToolLoopRunner.run(...)` and prepends a `request_started` event.

- **Application notification store**:
  `core/python/agent_app/application_notifications.py`
  - `ApplicationNotificationStore` defines lifecycle persistence.
  - `SQLiteApplicationNotificationStore` is the terminal/server runtime
    implementation.
  - `InMemoryApplicationNotificationStore` supports tests and embedding.
  - Also handles cancellation and marks requests as completed.

- **Tool loop and streaming**: `core/python/agent_app/tool_loop.py`
  - `ToolLoopRunner` emits request / assistant / tool / error events.
  - Internal `session_checkpoint` events include live `Session` objects
    and are meant for in-process persistence only.

- **HTTP exposure**: `application/python/agent_terminal_app/server.py`
  - `POST /sessions/{session_id}/send` starts a background worker which
    calls `AgentApplication.send_request(..., stream=True)` and
    publishes all yielded events into the shared event store.
  - `GET /events` returns a window of events filtered by
    `since_id`, `session_id`, and/or `request_id`.
    - When called with ``session_id`` but no ``since_id``, the server
      defaults to the per-session cursor (``cursor_event_id``) so that
      polling does not replay the entire history for that session.
    - When called with no ``since_id``, no ``session_id``, and no
      ``request_id``, the server returns an empty ``events`` list and a
      ``latest_event_id`` field suitable for bootstrapping polling
      without replaying existing events.
    - For non-bootstrap calls, the server applies a lightweight
      compaction pass that drops redundant ``partial`` / ``tool_partial``
      events before terminal events and merges consecutive partials for
      the same request into a single event.
  - Session/message routes publish additional lifecycle events
    (`session_created`, `message_appended`, etc.).

- **Bridge forwarding (streaming)**:
  - `application/python/agent_terminal_app/bridge_client.py`:
    - `_forward_events_loop()` polls the event store with `since_id` and
      sends each new event as a `session_event` Phoenix message on topic
      `server:<server_id>`.
  - `bridge-elixir/lib/bridge/server_channel.ex`:
    - `handle_in("session_event", ...)` re-broadcasts events via
      `Phoenix.PubSub` on `"events:server:<server_id>"`.
  - `bridge-elixir/lib/bridge/app_channel.ex`:
    - App sockets subscribe to `"events:server:<server_id>"` when a
      pairing session is established.
    - `handle_info({:session_event, event}, ...)` pushes the event to
      the app as `event: "session_event", payload: {"event": event}`.
  - Mobile bridge client (`BridgeAdapter`) receives these
    `session_event` messages and passes the raw `event` to listeners.

---

## Common Fields

All externally visible events share a few common patterns:

- `event_id: str`
  - Assigned by `InMemoryEventStore.publish` when the event is stored.
  - Used with `since_id` in `/events` and the bridge forwarder.

- `type: str`
  - Discriminator for the event’s schema.

- `session_id: str`
  - The logical session this event belongs to.

- `request_id: str`
  - Present for request/streaming/tool events.
  - Absent for pure session lifecycle events such as `session_created`.

Additional fields depend on `type` and are described below.

---

## Request Lifecycle Events

Defined in:

- `core/python/agent_app/application_future.py`
  - `AgentApplication.send_request` (request_started, request_cancelled)
- `core/python/agent_app/tool_loop.py`
  - `ToolLoopRunner.run` (request_completed, error)

### `request_started`

Emitted once per logical request, before any streaming tokens or tool
events.

```jsonc
{
  "type": "request_started",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "stream": true
}
```

### `request_cancelled`

Emitted when a request is cancelled via
`AgentApplication.cancel_request(request_id)`.

```jsonc
{
  "type": "request_cancelled",
  "session_id": "<session-id>",
  "request_id": "<request-id>"
}
```

### `request_completed`

Emitted after the tool loop finishes successfully or with an error
(always the final event for a given `request_id`).

```jsonc
{
  "type": "request_completed",
  "session_id": "<session-id>",
  "request_id": "<request-id>"
}
```

### `error`

Represents a fatal error during the request/tool loop.

```jsonc
{
  "type": "error",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "detail": "<human-readable message>"
}
```

---

## Assistant Streaming Events

Defined in:

- `core/python/agent_app/tool_loop.py`
  - `_run_llm_phase` (assistant_message, partial, final)

### `assistant_message`

Signals the lifecycle of a streamed assistant reply.

```jsonc
{
  "type": "assistant_message",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "phase": "start" | "end"
}
```

### `partial`

Streaming assistant chunks. Each `partial` event contains a single
assistant `message` chunk.

```jsonc
{
  "type": "partial",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "message": {
    "role": "assistant",
    "content": "...",         // may be incremental
    "metadata": { /* optional, provider-specific */ }
  }
}
```

### `final`

Final assistant messages for a phase.

```jsonc
{
  "type": "final",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "messages": [
    { "role": "assistant", "content": "...", "metadata": { /* ... */ } },
    // possibly multiple assistant/tool/system messages
  ]
}
```

> Note: Internal `final` events inside the tool loop also carry a live
> `session` object. That field is **not** required or relied upon by
> external consumers; the shared event store and bridge forwarding
> work with the serializable parts.

---

## Tool Calling Events

Defined in:

- `core/python/agent_app/tool_loop.py`
  - `_apply_tool_calls` (tool_calls, tool_partial, tool_results)

### `tool_calls`

Emitted when the LLM requests tools to be executed.

```jsonc
{
  "type": "tool_calls",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "tool_calls": [
    {
      "id": "<call-id>",          // or "tool_call_id"
      "function": {
        "name": "tool_name",
        "arguments": "{...}"      // JSON-encoded arguments
      },
      // additional provider-specific fields may be present
    }
  ]
}
```

### `tool_partial`

Optional streaming events for tool output when `stream_tools=True`.

```jsonc
{
  "type": "tool_partial",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "tool_call_id": "<call-id>",
  "phase": "start" | "stream" | "end",
  "payload": {
    // For "start" / "stream": chunk from iter_tool_messages (includes "part")
    // For "end": { "result": <final tool message dict> }
  }
}
```

### `tool_results`

Summary of final tool messages appended to the session.

```jsonc
{
  "type": "tool_results",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "messages": [
    {
      "role": "tool",         // or another valid message role
      "content": "...",
      "metadata": {
        "tool_call_id": "<call-id>",
        "tool_name": "tool_name",
        // provider- or tool-specific metadata
        //
        // Optional display helper used by terminal and other UIs.
        // When present and display.type == "text", renderers prefer
        // display.content over the raw message.content when showing
        // tool output.
        "display": {
          "type": "text",
          "content": "human-friendly, possibly truncated output"
        }
      }
    }
  ]
}
```

---

## Internal Checkpoint Events

Defined in:

- `core/python/agent_app/tool_loop.py`
  - `_run_llm_phase`, `_apply_tool_calls`

### `session_checkpoint` (internal only)

These events are **internal only** and are used by the server and
terminal app to persist `Session` objects incrementally.

```jsonc
{
  "type": "session_checkpoint",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "session": { /* live Session object; not intended for external use */ }
}
```

The application-layer session request coordinator
(`core/python/agent_app/request_execution.py`) consumes these events but does
**not** forward them to `/events` or the bridge as public API. An optional
in-process checkpoint callback lets terminal-style consumers track the live
`Session`. The package-local maintainer guide lives at
`application/python/docs/development/request-execution.md`.

The low-level application request flow persists request checkpoints and emits
lightweight, serializable **checkpoint marker** events into the shared event
store (described below).

### `checkpoint` (marker event)

Defined in:

- `core/python/agent_app/application_future.py`
  - request checkpoint persistence and `record_checkpoint`
- `core/python/agent_app/request_execution.py`
  - shared request execution and internal checkpoint filtering
- `application/python/agent_terminal_app/server.py`
  - non-request session/message lifecycle endpoints

Lightweight marker emitted whenever a session has just been persisted to disk,
either:

- by the low-level application request flow after processing a request
  checkpoint, or
- after a non-streaming HTTP operation that modifies a session and
  saves it (append/modify/delete messages, create/fork sessions,
  certain agent updates).

```jsonc
{
  "type": "checkpoint",
  "session_id": "<session-id>",
  "request_id": "<request-id>", // may be omitted for non-request ops
  "timestamp": "2025-01-01T00:00:00Z"
}
```

Semantics:

- `checkpoint` events are written to the same `EventStore` as all
  other events and therefore receive an `event_id` on publish.
- The server tracks the most recent **session cursor** event id per
  session and exposes it as `cursor_event_id` from
  `GET /sessions/{session_id}/messages`. The cursor may correspond to
  the `event_id` of a `checkpoint` event or to another event (for
  example, a `final` or `message_appended` event) whose effects are
  known to be reflected in the persisted session state.
- Within a single LLM/tool phase, `ToolLoopRunner` emits public
  events (such as `final` or `tool_results`) *before* the internal
  `session_checkpoint` that captures the updated `Session`. When the
  server handles this `session_checkpoint` and records a corresponding
  `checkpoint` marker, the resulting session cursor is always at or
  after the events that produced the last messages visible in the
  persisted session history.
- A client that loads messages and then starts polling `GET /events`
  with `since_id = cursor_event_id` will not receive events whose
  effects are already reflected in that snapshot.

---

## Session & Message Lifecycle Events

Defined in `application/python/agent_terminal_app/server.py`:

- `create_session` (`POST /sessions`)
- `fork_session` (`POST /sessions/{session_id}/fork`)
- `add_message` (`POST /sessions/{session_id}/messages`)
- `update_message` (`PATCH /sessions/{session_id}/messages/{index}`)
- `delete_messages` (`DELETE /sessions/{session_id}/messages`)

These events are written into the same shared event store so that
terminal and HTTP/mobile frontends see a unified history.

### `session_created`

Emitted when a new session is created, either directly or via fork.

```jsonc
{
  "type": "session_created",
  "session_id": "<session-id>",
  "agent_id": "default" | "<agent-id>",
  "source_session_id": "<id>"?,    // present for forked sessions
  "session": { /* full serialized Session */ }
}
```

### `message_appended`

Emitted when a user/system/assistant/tool message is appended.

```jsonc
{
  "type": "message_appended",
  "session_id": "<session-id>",
  "role": "user" | "assistant" | "system" | "tool",
  "content": "...",
  "metadata": { /* per-message metadata, if any */ },
  "message": { /* serialized Message */ },
  "session": { /* full serialized Session after append */ }
}
```

### `message_modified`

Emitted when a message’s content is modified.

```jsonc
{
  "type": "message_modified",
  "session_id": "<session-id>",
  "index": 0,
  "content": "new content",
  "session": { /* full serialized Session after modification */ }
}
```

### `messages_deleted`

Emitted when one or more messages are deleted from a session.

```jsonc
{
  "type": "messages_deleted",
  "session_id": "<session-id>",
  "indices": [0, 1, 2],
  "session": { /* full serialized Session after deletion */ }
}
```

---

## Where These Events Are Consumed

- **Terminal rendering**:
  - `application/python/agent_terminal_app/event_rendering.py`
    - Renders `partial`, `final`, `tool_*`, `request_*`, and error events
      into a human-readable terminal view.
    - For tool messages/results, prefers `metadata.display.content`
      (when `display.type == "text"`) over the raw `content` field, so
      tools can provide a dedicated, user-facing rendering separate
      from their full machine-oriented output.

- **Terminal application logic**:
  - `application/python/agent_terminal_app/terminal_app.py`
    - Uses the shared event store to poll and aggregate events for the
      interactive terminal (see `poll_new_events`, `list_events`).

- **HTTP API**:
  - `application/python/agent_terminal_app/server.py`
    - `GET /events` exposes stored events for web/mobile clients,
      applying cursor-aware defaults and basic compaction as described
      above.

- **Bridge + mobile**:
  - `application/python/agent_terminal_app/bridge_client.py`
    - Forwards stored events to the Elixir bridge via `session_event`.
  - `bridge-elixir/lib/bridge/server_channel.ex`
    - Receives `session_event` from servers and broadcasts via PubSub.
  - `bridge-elixir/lib/bridge/app_channel.ex`
    - Pushes `session_event` messages to app sockets.
  - `mobile/crystal-lattice-control-rn/App.tsx`
    - `BridgeAdapter` receives `session_event` and surfaces the raw
      event to listeners.
  - `mobile/crystal-lattice-control-rn/src/useSessionEvents.ts`
    - High-level hook that either consumes pushed events (bridge) or
      polls `/events` and passes them to screens.
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
    - Currently logs per-session events; will later use them to drive
      live message-list updates.

Together, these components define the end-to-end contract for event
streaming across terminal, HTTP, bridge, and mobile clients.
