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

## Storage and Transport

- **Event store protocol**: `core/python/agent_app/events.py`
  - `EventStore` interface (`publish`, `list`).
  - `InMemoryEventStore` adds `event_id: str` on `publish`.

- **Application event producer**: `core/python/agent_app/application_future.py`
  - `AgentApplication.send_request(...)` yields events from
    `ToolLoopRunner.run(...)` and prepends a `request_started` event.
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

The HTTP server’s background worker (`_run_send_request_background` in
`application/python/agent_terminal_app/server.py`) consumes these
events but does **not** forward them to `/events` or the bridge as
public API.

Instead, whenever the server processes a `session_checkpoint` it
emits a lightweight, serializable **checkpoint marker** event into the
shared event store (described below).

### `checkpoint` (marker event)

Defined in:

- `application/python/agent_terminal_app/server.py`
  - `_run_send_request_background`
  - Session/message lifecycle endpoints

Lightweight marker emitted whenever a session has just been persisted
to disk, either:

- after processing an internal `session_checkpoint` from the tool
  loop, or
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

- **Terminal application logic**:
  - `application/python/agent_terminal_app/terminal_app.py`
    - Uses the shared event store to poll and aggregate events for the
      interactive terminal (see `poll_new_events`, `list_events`).

- **HTTP API**:
  - `application/python/agent_terminal_app/server.py`
    - `GET /events` exposes raw stored events for web/mobile clients.

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
