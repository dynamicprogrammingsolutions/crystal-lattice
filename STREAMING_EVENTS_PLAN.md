Comprehensive Plan – Server‑Side Streaming Events via Elixir Bridge
===================================================================

This document defines the architecture for **server‑side streaming events**
with the Elixir bridge as a durable event hub.

It must be self‑contained: a future conversation will rely only on this file
to implement the feature.


1. Goals and Constraints
------------------------

### 1.1 Functional goals

- Stream **per‑session events** (tool calls, partial/final assistant
  messages, lifecycle events) to frontends in near real‑time.
- Support **replay** via a `since_id` cursor so clients can:
  - Catch up after reconnects.
  - Start streaming from a known historical point.
- Allow frontends to choose:
  - Per‑session streams ("only events for session X").
  - Global streams ("all events on this server").
- Make the Elixir bridge the **durable event hub** that can later drive
  **push notifications** when clients are offline.

### 1.2 Consistency requirements

When a frontend opens a session while a request is already streaming:

- The **message list snapshot** must correspond to a concrete checkpointed
  version of the session.
- The **event stream** must start strictly **after** that checkpoint so
  that:
  - No events are replayed whose effects are already in the snapshot.
  - No events that happened after the snapshot are lost.

Important constraints:

- Internal core `session_checkpoint` events currently carry a live `Session`
  object and are **not JSON‑serializable**. They must *not* be stored or
  forwarded as normal events.
- `event_id` values are **local to a single Python process / server** and
  must **not** be persisted in session files. Another server process loading
  the same session JSON must not rely on event IDs from a different
  process.

### 1.3 Non‑functional constraints

- The software is **not live**; we do **not** need backwards compatibility
  with earlier message or event shapes.
- We want to avoid invasive changes to core types (`Session`, `Message`) and
  **do not introduce per‑message UUIDs** unless strictly necessary. The
  design below makes that unnecessary for streaming.


2. Existing Building Blocks
---------------------------

### 2.1 Core types and sessions (Python)

- `core/python/agent_core/types.py`:
  - `Message` data class:
    - Fields: `role`, `content`, `metadata`.
    - No message UUID today.
  - `Session` data class:
    - Fields: `session_id: str`, `messages: List[Message]`,
      `metadata: Dict[str, Any]`.
    - Messages are addressed by index.

### 2.2 Event store (Python application layer)

- `core/python/agent_app/events.py`:
  - `InMemoryEventStore`:
    - `publish(event)`:
      - Copies the event.
      - Adds `event_id` if missing; this is a **stringified integer** from a
        local counter (`"1"`, `"2"`, ...).
    - `list(since_id=None, request_id=None, session_id=None, limit=100)`:
      - Filters by optional `since_id`, `request_id`, `session_id` and
        returns up to `limit` events.
      - `since_id` is **exclusive**: events with
        `int(event.event_id) <= int(since_id)` are skipped.
  - This store is **per‑process**, in‑memory, and not persisted.

### 2.3 Python HTTP server and streaming

- `application/python/agent_terminal_app/server.py`:
  - Builds a process‑wide `AgentApplication` (`get_agent_app`).
  - Uses `AgentApplication.send_request(..., stream=True)` to drive
    streaming requests.
  - `_run_send_request_background(...)`:
    - Runs `send_request` in a background thread.
    - For each event from the core:
      - If `type == "session_checkpoint"`:
        - Carries a live `Session` object; used to save session to disk.
        - **Not** published to the shared `EventStore`.
      - Else:
        - Published to the store via `store.publish(ev)`.
  - `GET /events`:
    - Returns `{"events": [...]}` from the event store.
  - `GET /sessions/{session_id}/messages`:
    - Returns a slice of messages addressed by index.
    - Currently does not return any event cursor.

### 2.4 Elixir bridge

- `bridge-elixir`:
  - Phoenix WebSocket bridge (`/ws/websocket`).
  - Accepts:
    - `type=server` connections from Python servers.
    - `type=app` connections from mobile/desktop clients.
  - Manages pairing via codes and sessions.
  - Forwards **HTTP** traffic via `http_request` / `http_response` messages.
  - Currently does **not** store or stream Python events.

### 2.5 Mobile bridge client (high level)

- `mobile/crystal-lattice-control-rn/App.tsx`:
  - `BridgeAdapter` implements `ConnectionAdapter` over the bridge.
  - Sends `list_servers`, `pair_request`, `pair_submit`, `http_request`.
  - Routes `phx_reply` messages to pending requests by `ref`.
  - Ignores unsolicited push messages (no general event streaming yet).


3. Architectural Overview
-------------------------

### 3.1 Responsibilities

- **Python server (per process / per server_id):**
  - Generates events for streaming requests and lifecycle operations.
  - Assigns `event_id` via its `InMemoryEventStore`.
  - Publishes events into that store, including lightweight checkpoint
    markers (defined below).
  - Forwards events to the Elixir bridge via its `type=server` WebSocket.

- **Elixir bridge (cluster):**
  - Receives event batches from one or more Python servers.
  - Persists them in its own storage (e.g., Postgres or ETS) using the
    Python‑assigned `event_id`.
  - Exposes **subscription** APIs to app clients:
    - `events_subscribe` (with `session_id` and `since_id`).
    - `events_unsubscribe`.
    - Pushes `events_update` messages to subscribed clients.
  - Later, drives push notifications based on the same event stream.

- **Frontends (mobile and others):**
  - Obtain a **message snapshot** from the Python HTTP server.
  - Obtain an **aligned event cursor** (`checkpoint_event_id`).
  - Use the bridge to stream events **after** that checkpoint.
  - When not using the bridge, fall back to HTTP `/events` polling.

### 3.2 Key design choices

1. Use **`event_id` as the primary cursor**; do not add message UUIDs.
   - Frontends align on `event_id` and `session_id`.
   - The triple `(snapshot messages, checkpoint_event_id, subsequent
     events)` is sufficient for consistency.

2. Represent checkpoints as **lightweight marker events**:
   - Internal `session_checkpoint` events with live `Session` objects remain
     internal only.
   - For each such internal event, we publish a small, serializable
     **checkpoint marker** event into the `EventStore` and record its
     `event_id`.

3. Keep `event_id` **per server and ephemeral**:
   - Each Python process has its own event store and `event_id` counter.
   - Event IDs are never written into session files.
   - A different server loading the same session file starts its own
     independent event ID space.


4. Python Side – Detailed Design
--------------------------------

### 4.1 Lightweight checkpoint marker events

We introduce a new, serializable **checkpoint marker** event type, separate
from the internal `session_checkpoint` events.

- Example shape:

  ```json
  {
    "type": "checkpoint",
    "session_id": "<session-id>",
    "request_id": "<request-id>",
    "timestamp": "2025-01-01T00:00:00Z",
    "kind": "auto"  // optional
  }
  ```

- Properties:
  - Published to the shared `EventStore`.
  - Receives a normal `event_id` from `InMemoryEventStore.publish`.
  - Contains **no** `Session` object or message list.
  - Forwarded to the Elixir bridge and persisted there.

### 4.2 Tracking the latest checkpoint per session

Each Python server process maintains an in‑memory map:

- `last_checkpoint_event_id_by_session: Dict[str, Optional[str]]`
  - Keys: `session_id`.
  - Values: `event_id` of the most recent **checkpoint marker** for that
    session, or `None` if no checkpoint marker exists yet.
  - This map is **not** written to disk and is per process.

It is updated whenever a new checkpoint marker is published.

### 4.3 Integrating with `_run_send_request_background`

Current behaviour (simplified):

- For each event from `AgentApplication.send_request(..., stream=True)`:
  - If `type == "session_checkpoint"`:
    - Extracts a `Session` object and saves it to disk.
    - Does **not** publish this event.
  - Else:
    - Publishes the event via `store.publish(ev)`.

New behaviour for **internal** `session_checkpoint` events:

1. Introduce a **per‑session lock** (e.g., keyed by `session_id`) used both
   here and in `GET /sessions/{id}/messages`.
2. When a `session_checkpoint` event arrives, under that lock:
   - Save the `Session` object to disk as today.
   - Publish a **checkpoint marker** event:

     ```python
     marker = store.publish({
         "type": "checkpoint",
         "session_id": session_id,
         "request_id": request_id,
         "timestamp": <now>,
     })
     checkpoint_event_id = marker["event_id"]
     last_checkpoint_event_id_by_session[session_id] = checkpoint_event_id
     ```

3. Continue handling all non‑checkpoint events as today (publishing them
   directly), without any embedded `Session` objects.

The internal `session_checkpoint` event with the live `Session` object
remains **internal‑only** and is never serialized.

### 4.4 Aligning message snapshots with checkpoints

`GET /sessions/{session_id}/messages` will be extended to return a
checkpoint cursor:

- Response shape (conceptually):

  ```json
  {
    "messages": [ ... ],
    "checkpoint_event_id": "1234"  // or null
  }
  ```

Semantics:

- `messages` reflect the session as saved on disk at the time of the most
  recent checkpoint marker handled by this process.
- `checkpoint_event_id` is the `event_id` of that marker, taken from
  `last_checkpoint_event_id_by_session[session_id]`.

Implementation sketch:

1. Acquire the **per‑session lock** for this `session_id`.
2. Load the session from disk (as done today).
3. Read `checkpoint_event_id = last_checkpoint_event_id_by_session.get(session_id)`.
4. Return `{"messages": ..., "checkpoint_event_id": checkpoint_event_id}`.

Because both checkpoint handling and snapshot reading run inside the same
per‑session critical section, we avoid races where the snapshot and
`checkpoint_event_id` refer to different checkpoints.

If no checkpoint marker exists yet:

- `checkpoint_event_id` is `null` / omitted.
- The snapshot corresponds to whatever initial or manually saved state
  exists.

### 4.5 Python → Elixir event forwarding

To make the bridge the durable hub, each Python server must forward all
published events (including checkpoint markers) to the bridge.

High‑level behaviour in `BridgeClient` (`application/python/agent_terminal_app/bridge_client.py`):

- Maintain a local cursor: `last_forwarded_event_id` (string, initially
  `None`).
- Run a background worker that periodically:
  - Calls the local event store’s `list(since_id=last_forwarded_event_id, limit=N)`.
  - Sends any returned events as a batch Phoenix message on the server
    channel, e.g.:

    ```json
    {
      "topic": "server:<server_id>",
      "event": "session_event",
      "payload": {
        "events": [ ... ],
        "server_id": "<server-id>"
      }
    }
    ```

  - Updates `last_forwarded_event_id` to the maximum `event_id` in the
    batch.

Notes:

- Polling interval can be tuned (e.g., 100–200ms) to approximate
  real‑time streaming without tight coupling.
- The existing HTTP `/events` endpoint remains available for non‑bridge
  clients and tests.


5. Elixir Bridge – Event Storage and Subscription
-------------------------------------------------

### 5.1 Event storage model

We introduce an event storage layer on the Elixir side. Exact mechanics
(Postgres vs ETS) can be chosen during implementation, but conceptually each
stored event will include at least:

- `server_id`: which Python server produced this event.
- `event_id`: copied from the Python event’s `event_id` (stringified
  integer) and treated as an ordered cursor within that server.
- `session_id`: session this event belongs to, if any.
- `request_id`: optional, for request‑specific filtering.
- `type`: event type (`"partial"`, `"final"`, `"tool_results"`,
  `"checkpoint"`, etc.).
- `timestamp`: when it was ingested.
- `payload`: the JSON event payload (excluding any live objects).

Key invariants:

- Elixir **preserves** Python’s `event_id`; it does not re‑number events.
- For a given `server_id`, `event_id` defines a total order of events.
- Checkpoint markers (`"checkpoint"` type) are stored like other events
  and are useful for analysis, but frontends do not need to treat them
  specially.

### 5.2 Ingesting events from Python

In `ServerChannel` (Elixir):

- Add a handler for incoming `"session_event"` messages from Python:
  - Extract `events` from the payload.
  - For each event, insert into the event store with its `server_id`,
    `event_id`, `session_id`, etc.
  - Optionally, broadcast these events to a PubSub topic for live
    subscribers.

### 5.3 Event subscription protocol for apps

New app‑side channel events on `app:<client_id>`:

#### 5.3.1 Subscribe

- **Event:** `"events_subscribe"`.
- **Payload:**

  ```json
  {
    "session_id": "optional-session-id-or-null",
    "since_id": "optional-event-id-or-null",
    "mode": "replay_then_live" | "live_only" | "replay_only"
  }
  ```

- **Reply (`phx_reply`) on success:**

  ```json
  {
    "status": "ok",
    "response": {
      "subscription_id": "sub-uuid",
      "effective_since_id": "<since-id-used>"
    }
  }
  ```

Semantics:

- `session_id` filters events to a single session; if omitted, the
  subscription covers all events for that server.
- `since_id` is **exclusive**: only events with `event_id > since_id` are
  replayed.
- `mode`:
  - `"replay_then_live"` (default): replay history, then stream new
    events.
  - `"live_only"`: ignore history; stream only new events.
  - `"replay_only"`: replay history then end the subscription.

#### 5.3.2 Pushed updates

- **Event:** `"events_update"` (bridge → app, unsolicited).
- **Payload:**

  ```json
  {
    "subscription_id": "sub-uuid",
    "events": [
      { "event_id": "42", "session_id": "S", "type": "partial", ... },
      { "event_id": "43", "session_id": "S", "type": "final", ... }
    ]
  }
  ```

Semantics:

- Events are ordered by `event_id` ascending within each batch.
- Batches may be small; clients treat them as incremental updates.

#### 5.3.3 Unsubscribe

- **Event:** `"events_unsubscribe"`.
- **Payload:**

  ```json
  { "subscription_id": "sub-uuid" }
  ```

- **Reply:** standard `phx_reply` with `{ "status": "ok" }`.

### 5.4 Implementing replay and live streaming

When handling `"events_subscribe"` in `AppChannel`:

1. Resolve which `server_id` the subscription refers to (from the existing
   pairing/session machinery).
2. Record the subscription (socket + server_id + session_id + since_id +
   mode).
3. For **replay**:
   - Query the event store:

     ```text
     WHERE server_id = :server_id
       AND (session_id = :session_id OR :session_id IS NULL)
       AND event_id > :since_id
     ORDER BY event_id ASC
     ```

   - Send the results as one or more `events_update` batches.
4. For **live**:
   - Use Phoenix.PubSub or a process registry to route newly ingested
     events for that server/session to active subscriptions.
   - Push new events as `events_update` batches.

`event_id` semantics match the Python `/events` API, so mental models and
tests can be reused.


6. Frontend Interaction Model (High Level)
------------------------------------------

Actual event handling and streaming abstractions in the mobile app will be
defined in a separate plan. This section only outlines how frontends should
conceptually use the new architecture.

### 6.1 Opening a session while a request is in progress

For a given `session_id = S` on a specific Python server (and corresponding
`server_id` in the bridge):

1. **Load a consistent snapshot from Python**

   - Frontend calls:

     ```http
     GET /sessions/S/messages?start=...&end=...
     ```

   - Server responds:

     ```json
     {
       "messages": [...],
       "checkpoint_event_id": "100"  // or null
     }
     ```

   - Interpretation:
     - `messages` reflect the session as of checkpoint marker event `100`.
     - All events with `event_id <= 100` have their effects included in the
       snapshot.

2. **Start streaming from the bridge**

   - Frontend sends over the bridge (simplified):

     ```json
     {
       "event": "events_subscribe",
       "payload": {
         "session_id": "S",
         "since_id": "100",
         "mode": "replay_then_live"
       }
     }
     ```

   - The bridge:
     - Replays all stored events for `S` with `event_id > 100`.
     - Then continues to push new events as they are ingested.

3. **Client‑side cursor tracking**

   - The frontend maintains `lastSeenEventId` for each subscription.
   - On reconnect or app restart, it can re‑subscribe with that `since_id`
     to avoid duplicates.

This guarantees a consistent view even when the underlying request was
already mid‑stream when the session was opened.

### 6.2 Global (all‑events) subscriptions

For debugging or advanced features, frontends may subscribe to all events on
the server:

- Omit `session_id` in `events_subscribe`.
- Choose an initial `since_id` by:
  - Calling `GET /events?limit=1` and taking the highest `event_id`, or
  - Adding a small helper endpoint like `GET /events/last` that returns the
    global last `event_id`.


7. Push Notifications (Future Work)
-----------------------------------

Once this architecture is in place, the Elixir bridge can be extended to
drive push notifications:

- Persist events durably with enough metadata (`session_id`, `type`,
  timestamps, user/pairing identity).
- Define which events are notification‑worthy (e.g., `"final"` assistant
  messages).
- Add a `register_push_token` message on the app socket to bind a push
  token to a user/pairing.
- Implement a background worker that consumes events and sends push
  notifications via APNs/FCM.

This can be added without changing the core Python event generation model or
the subscription protocol.


8. Files to Read Before Implementation
--------------------------------------

Before implementing this plan, read and understand at least the following
files:

**Core and application layer (Python)**

- `core/python/agent_core/types.py`
  - `Message` and `Session` data classes.
- `core/python/agent_app/events.py`
  - `EventStore` and `InMemoryEventStore` (`event_id` semantics).
- `core/python/agent_app/application_future.py`
  - `AgentApplication.send_request` event stream semantics.

**Terminal / HTTP app (Python)**

- `application/python/agent_terminal_app/server.py`
  - `_run_send_request_background` (event publishing and checkpoints).
  - `/sessions/{session_id}/messages` endpoint.
  - `/events` endpoint.
- `application/python/agent_terminal_app/bridge_client.py`
  - Current bridge client implementation (server‑side WebSocket).
  - Where to add event forwarding logic.

**Elixir bridge**

- `bridge-elixir/AGENTS.md`
  - Overview of sockets, channels, and responsibilities.
- `bridge-elixir/README.md`
  - Current WebSocket protocol and message types.
- `bridge-elixir/lib/bridge/socket.ex`
  - Socket / channel configuration for `type=server` and `type=app`.
- `bridge-elixir/lib/bridge/server_channel.ex`
  - Handling of server connections; place to ingest `session_event`.
- `bridge-elixir/lib/bridge/app_channel.ex`
  - Handling of app connections; place to add `events_subscribe`,
    `events_unsubscribe`, and `events_update`.
- `bridge-elixir/lib/bridge/server_registry.ex`
  - Server tracking used by health checks and pairing.
- `bridge-elixir/lib/bridge/session_manager.ex`
  - Session tracking between app and server.
- `bridge-elixir/lib/bridge/pairing_manager.ex`
  - Existing pattern for pairing flows, useful for designing
    subscription tracking.

**Mobile app (for context; detailed design in a separate plan)**

- `mobile/crystal-lattice-control-rn/App.tsx`
  - `ConnectionAdapter` and `BridgeAdapter`.
  - Current `WebSocket` handling (where to integrate event streaming).
- `mobile/crystal-lattice-control-rn/src/api.ts`
  - Existing HTTP calls (`/sessions`, `/sessions/{id}/messages`, `/events`).

These files provide the necessary context to implement Python event
generation, bridge ingestion, and event subscription safely and
consistently.


9. Implementation Stages
------------------------

This plan can be implemented incrementally. The following stages reflect
the intended order of work when coordinating with the mobile app changes
described in MOBILE_STREAMING_EVENTS_PLAN.md.

### 9.1 Stage 1 – Minimal server changes (no bridge changes required)

Purpose:

- Provide enough server-side functionality for the mobile app’s **Stage 1**
  (polling-based event consumption) to work with a consistent view, without
  requiring any changes to the Elixir bridge.

Scope (Python only):

1. **Checkpoint marker events**
   - Implement the lightweight `checkpoint` marker events as described in
     section 4.1:
     - Internal `session_checkpoint` events remain in-process only.
     - For each internal checkpoint, publish a small `checkpoint` event to
       the shared `EventStore` and record its `event_id` in
       `last_checkpoint_event_id_by_session`.
   - Update docs/api/events.md to include the new public `checkpoint`
     event type, clearly differentiating it from the internal
     `session_checkpoint` event.

2. **Per-session checkpoint cursor in `/sessions/{id}/messages`**
   - Extend `GET /sessions/{session_id}/messages` to return
     `checkpoint_event_id` alongside `messages`, as described in section
     4.4.
   - Ensure the endpoint and the checkpoint handling both use the same
     per-session lock so that the snapshot and `checkpoint_event_id`
     always refer to the same checkpoint.

3. **Keep bridge behaviour unchanged for now**
   - Do **not** yet rely on Elixir-side event storage or
     `events_subscribe`/`events_update`.
   - Existing behaviour (if any) for forwarding events to the bridge may
     remain, but the mobile app’s Stage 1 will only consume events via
     HTTP `/events` and use `checkpoint_event_id` to set `since_id`.

Result:

- Mobile clients can:
  - Load a session’s message list and get an aligned `checkpoint_event_id`.
  - Use HTTP `/events` with `since_id=checkpoint_event_id` to poll for
    subsequent events.
  - Reason about consistency between the snapshot and the event stream,
    even without any Elixir changes.

### 9.2 Stage 2 – Full bridge event hub and streaming

Once the mobile app’s Stage 1 (polling) is in place and the Python-side
checkpoint support is working, implement the rest of this plan:

1. **Python → Elixir event forwarding**
   - Add the background `_forward_events_loop` (or equivalent) in
     `BridgeClient` to poll the local event store by `since_id` and send
     `session_event` batches to the bridge, as described in section 4.5.

2. **Elixir event storage and subscription protocol**
   - Implement the event storage model in the bridge (section 5.1).
   - Wire up `ServerChannel` to ingest `session_event` messages and persist
     each event, as in section 5.2.
   - Implement `events_subscribe`, `events_unsubscribe`, and
     `events_update` in `AppChannel` (section 5.3), including replay and
     live streaming semantics (section 5.4).

3. **Bridge as durable hub for future features**
   - With storage and subscription in place, the bridge now serves as the
     durable event hub.
   - Future work (such as push notifications) can build on top of this
     without changing the Python event model or the subscription protocol.

This staging ensures that:

- Mobile Stage 1 can land with minimal, Python-only server changes.
- The more involved bridge-side work (persistence, subscription
  management) can follow without blocking initial mobile integration.
