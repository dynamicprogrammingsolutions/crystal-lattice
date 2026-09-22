# Application events

Crystal Lattice uses one application event store for request progress,
streaming messages, tool execution, notifications, and terminal-owned session
changes. This page documents the event schemas and makes each ownership
boundary explicit.

Events can be observed directly from `AgentApplication`, through the terminal
application's `GET /events` endpoint, or through transports such as the bridge.
Transport and UI packages consume the contract; they do not redefine the
application-owned event shapes.

## Ownership at a glance

| Layer | Responsibility |
|---|---|
| `core/python/agent_app/events.py` | Event-store protocol, IDs, filtering, retention, cursors, and process-local session locks |
| `core/python/agent_app/application_future.py` | Request lifecycle, serializable checkpoint markers, and notification publication |
| `core/python/agent_app/tool_loop.py` | Assistant, tool, cancellation, error, and internal session-checkpoint events |
| `core/python/agent_app/request_execution.py` | Filters internal session checkpoints, publishes public request events, and coordinates persistence |
| `application/python/agent_terminal_app/server.py` | HTTP polling plus session, message, and snapshot lifecycle events |
| Bridge and frontend packages | Transport, reduce, display, or react to public events |

## Event-store envelope and cursors

Every public event has:

- `event_id: str`: assigned by the event store when absent;
- `type: str`: discriminator for the event-specific schema.

Fields such as `session_id` and `request_id` depend on the event:

- session and request progress events have `session_id`;
- request progress and tool-loop events have `request_id`;
- terminal session mutations usually have `session_id` but no `request_id`;
- application-global notification events intentionally have neither
  `session_id` nor a top-level `request_id`; their notification record may
  contain a request association.

Consumers should treat `event_id` as an opaque cursor. The current
`InMemoryEventStore` generates `<store-instance>:<counter>` IDs that increase
within one store instance. A cursor from another store instance safely replays
from the beginning instead of being compared as a global integer.

`EventStore.list` supports:

- `since_id`: return events after this cursor;
- `request_id`: filter by request;
- `session_id`: filter by session;
- `limit`: bound the result.

It returns:

```json
{
  "events": [],
  "latest_event_id": "<opaque-id-or-null>",
  "cursor_expired": false
}
```

`cursor_expired` becomes true when the requested cursor belongs to the current
store instance but retention already evicted events after that boundary.
Applications should reload authoritative state before resuming from the newest
cursor.

The in-memory implementation can prune by a global event count and maximum
age. It is process-local and is not itself durable event history.

## Application request events

`AgentApplication.send_request` emits `request_started`, delegates the
assistant/tool phases to `ToolLoopRunner`, performs lifecycle hooks, and ends a
normally completed loop with `request_completed`.

### Request lifecycle

| Type | Additional fields | Meaning |
|---|---|---|
| `request_started` | `session_id`, `request_id`, `stream` | The effective request mode has been resolved and request processing is starting |
| `request_cancelled` | `session_id`, `request_id` | Cooperative cancellation was observed |
| `error` | `session_id`, `request_id`, `detail` | A fatal request, tool-loop, preparation, or persistence error |
| `request_completed` | `session_id`, `request_id` | The logical request reached its terminal application event |

Example:

```json
{
  "event_id": "9f…:17",
  "type": "request_started",
  "session_id": "session-123",
  "request_id": "request-456",
  "stream": true
}
```

An `error` can be followed by `request_completed`. A cancellation observed
before the loop starts can terminate after `request_cancelled`; consumers
should therefore treat both `request_completed` and `request_cancelled` as
terminal request-state signals.

### Assistant messages

#### `assistant_message`

Marks the start and end of one streamed assistant message:

```json
{
  "type": "assistant_message",
  "session_id": "session-123",
  "request_id": "request-456",
  "phase": "start",
  "message_index": 4
}
```

`phase` is `start` or `end`. `message_index` is the session index at which the
completed message starts. If a provider returns a final message without first
emitting partials, the tool loop still emits a synthetic start before the
final event.

#### `partial`

Carries one incremental core-message-shaped chunk:

```json
{
  "type": "partial",
  "session_id": "session-123",
  "request_id": "request-456",
  "message": {
    "role": "assistant",
    "content": "incremental text",
    "metadata": {}
  }
}
```

Partials are incremental output and are not guaranteed to contain all content
received so far. HTTP compaction may merge consecutive textual partials.

#### `final`

Carries the completed core messages for one provider phase:

```json
{
  "type": "final",
  "session_id": "session-123",
  "request_id": "request-456",
  "start_index": 4,
  "messages": [
    {
      "role": "assistant",
      "content": "complete response",
      "metadata": {}
    }
  ]
}
```

`start_index` identifies where the returned messages begin in persisted
session history. The public event does not include a live `Session` object.

### Tool execution

#### `tool_calls`

Emitted when final model output requests tool execution:

```json
{
  "type": "tool_calls",
  "session_id": "session-123",
  "request_id": "request-456",
  "tool_calls": [
    {
      "id": "call-1",
      "type": "function",
      "function": {
        "name": "read_file",
        "arguments": "{\"file_path\":\"README.md\"}"
      }
    }
  ]
}
```

The entries retain their provider/tool-interop shape. Consumers should not
assume every call uses the OpenAI function-call example shown above.

#### `tool_partial`

Optional incremental tool output when tool streaming is enabled:

```json
{
  "type": "tool_partial",
  "session_id": "session-123",
  "request_id": "request-456",
  "tool_call_id": "call-1",
  "phase": "start",
  "payload": {
    "part": "incremental output"
  }
}
```

`phase` is:

- `start` for the first streamed payload;
- `stream` for later payloads;
- `end` for the final tool message.

An `end` event additionally has `message_index`, and its payload is:

```json
{
  "result": {
    "role": "tool",
    "content": "final result",
    "metadata": {
      "tool_call_id": "call-1",
      "tool_name": "read_file"
    }
  }
}
```

#### `tool_results`

Summarizes final tool messages after they have been appended to the session:

```json
{
  "type": "tool_results",
  "session_id": "session-123",
  "request_id": "request-456",
  "start_index": 5,
  "messages": [
    {
      "role": "tool",
      "content": "final result",
      "metadata": {
        "tool_call_id": "call-1",
        "tool_name": "read_file"
      }
    }
  ]
}
```

Tool messages can also contain structured `toolResult` data and
display-oriented metadata. Treat additional fields as forward-compatible.

## Checkpoint events

Two similarly named events have different audiences.

### `session_checkpoint`: in-process only

`ToolLoopRunner` emits:

```python
{
    "type": "session_checkpoint",
    "session_id": session.session_id,
    "request_id": request_id,
    "session": session,  # live Session object
}
```

This is an in-process persistence handoff. `SessionRequestCoordinator`
consumes it and does not publish it to the shared event store, HTTP clients, or
the bridge. Direct callers of the low-level application generator may observe
it and must not serialize it as a public event.

### `checkpoint`: public serializable marker

After session state has been persisted, `AgentApplication.record_checkpoint`
publishes:

```json
{
  "type": "checkpoint",
  "session_id": "session-123",
  "request_id": "request-456",
  "timestamp": "2026-01-01T00:00:00Z"
}
```

`request_id` can be `null` for persistence outside a request.

The application stores the newest event ID whose effects are reflected in
persisted session state as that session's cursor. A client can:

1. load `GET /sessions/{session_id}/messages`;
2. read its `cursor_event_id`;
3. poll `GET /events?session_id=...&since_id=...`.

This avoids replaying events already represented by the loaded message
snapshot. Public `final` and `tool_results` events are emitted before the
internal checkpoint for their phase, so the resulting persistence cursor is
at or after those visible messages.

See the
[request-execution maintainer guide](../../../application/python/docs/development/request-execution.md)
for persistence, concurrency, and operation coordination.

## Notification events

Notification state is authoritative in notification storage. Event
publication is best effort and does not make a tool or user request fail.

### Application notifications

Application-global notification events are:

- `application_notification_created`;
- `application_notification_updated`;
- `application_notification_dismissed`;
- `application_notification_expired`.

They have this envelope:

```json
{
  "event_id": "9f…:24",
  "type": "application_notification_updated",
  "notification": {
    "id": "notification-id",
    "key": "stable-key",
    "kind": "notification",
    "status": "pending",
    "revision": 2,
    "severity": "info",
    "title": "Title",
    "body": "Body",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:01Z",
    "source": {"plugin": "plugin-name"},
    "display": {"presentation": "banner"},
    "model_visibility": "hidden"
  }
}
```

Application notification events intentionally omit `session_id`. Resolving an
application notification currently publishes
`application_notification_updated` with the resolved record rather than a
separate resolved event.

The terminal/server runtime can inject a durable application notification
store. Clients rehydrate authoritative state through
`GET /application/notifications`; event replay is only an incremental signal.

### Session notifications

Session-scoped notification events are:

- `session_notification_created`;
- `session_notification_updated`;
- `session_notification_resolved`;
- `session_notification_dismissed`;
- `session_notification_expired`.

They have:

```json
{
  "type": "session_notification_created",
  "session_id": "session-123",
  "request_id": "request-456",
  "notification": {
    "id": "notification-id",
    "key": "stable-key",
    "status": "pending",
    "revision": 1,
    "severity": "info",
    "title": "Title",
    "body": "Body",
    "source": {"plugin": "plugin-name"},
    "display": {"presentation": "inline"},
    "model_visibility": "hidden"
  }
}
```

`request_id` can be `null`. Session notification records are persisted in
`Session.metadata.notifications.items` and reloaded with the session. They do
not enter model/provider message history.

Notification records can also carry retention, operation, resolution,
dismissal, expiration, display, and UI-effect data. For the complete producer
contract and supported presentations, see
[Notifications and action displays](../../../plugins/docs/notifications-and-action-displays.md).

## Terminal-owned session events

The terminal and HTTP package publishes session lifecycle events into the same
store. These are integration-owned additions, not schemas emitted by
`ToolLoopRunner`.

| Type | Fields beyond `event_id` and `type` |
|---|---|
| `session_created` | `session_id`, `agent_id`; forked sessions also have `source_session_id` and `fork_upto_index` |
| `message_appended` | `session_id`, `index`, `role`, `content`, `metadata`, `message` |
| `message_modified` | `session_id`, `index`, `content`, `message` |
| `messages_deleted` | `session_id`, `indices` |
| `session_snapshot_selected` | `session_id`, `snapshot_id` |
| `session_snapshot_cleared` | `session_id` |
| `session_restored_from_snapshot` | `session_id`, `snapshot_id` |

The HTTP mutation response may contain a full serialized session, but these
event payloads do not.

Examples:

```json
{
  "type": "message_appended",
  "session_id": "session-123",
  "index": 3,
  "role": "user",
  "content": "Next question",
  "metadata": {},
  "message": {
    "role": "user",
    "content": "Next question"
  }
}
```

```json
{
  "type": "session_created",
  "session_id": "fork-id",
  "agent_id": "default",
  "source_session_id": "source-id",
  "fork_upto_index": 4
}
```

Snapshot selection is a readonly view state. While a snapshot is selected,
session-filtered HTTP event polling retains only snapshot select, clear, and
restore events so ordinary live-session updates do not modify the readonly
view.

## HTTP exposure

The terminal application exposes:

```text
GET /events
```

Query parameters are:

- `since_id`;
- `request_id`;
- `session_id`;
- `limit` for the returned compacted events;
- `internal_limit` for the raw event window considered during compaction.

Behavior:

- With no cursor or filters, the endpoint returns no historical events and
  only the current `latest_event_id`, allowing polling to start “from now.”
- With `session_id` but no `since_id`, it starts from the application-managed
  session cursor when one exists.
- It can filter by request and/or session.
- It drops assistant partials superseded by a later `final`.
- It drops non-final tool partials superseded by `tool_results`.
- It can merge consecutive textual `partial` events and consecutive textual
  `tool_partial` events for the same request.
- It caps the compacted result to `limit` and reports whether the source cursor
  expired.

Both `POST /sessions/{session_id}/send` and the atomic
`POST /sessions/{session_id}/send_message` flow publish request events through
the shared application coordinator.

## Bridge and frontend consumers

The Python bridge client polls the shared event store and forwards public
events as `session_event` messages. The Elixir bridge distributes those
messages to paired app sockets. The event dictionary remains the application
event payload through that transport.

The shared frontend SDK owns TypeScript event interfaces and reducers under
`packages/frontend-sdk/src/`. React bindings provide event consumption to the
mobile and desktop applications. Terminal rendering remains under
`application/python/agent_terminal_app/event_rendering.py`.

Consumers should:

- ignore unknown event types they do not use;
- tolerate additional fields;
- reload authoritative session or notification state after an expired cursor
  or a reducer-detected gap;
- use event indices and persistence cursors rather than assuming every event
  contains a full session snapshot.

See the [application package documentation](../../../application/python/docs/index.md)
for HTTP/runtime guidance and the frontend package documentation for
consumer-specific behavior.