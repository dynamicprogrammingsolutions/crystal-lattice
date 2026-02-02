Mobile Event Streaming Plan – Abstraction, Polling, and Bridge Streaming
=======================================================================

This document defines the plan for updating the React Native mobile app
(mobile/crystal-lattice-control-rn) to consume the server event stream
with a transport-agnostic abstraction that supports:
- HTTP polling against /events.
- Real-time streaming over the Elixir bridge.
- Robust handling of connection loss, reconnection, and continuation of the
  event stream using since_id.

It assumes the server/bridge-side architecture described in
STREAMING_EVENTS_PLAN.md and the event shapes defined in
docs/api/events.md (including a future checkpoint event that must be
documented there before Stage 1 begins).

1. Goals and Constraints
------------------------

1.1 Functional goals

- Provide frontends with a single abstraction for consuming events,
  regardless of whether the underlying transport is HTTP polling or bridge
  streaming.
- Support per-session event consumption with:
  - Alignment to a session snapshot via cursor_event_id.
  - Continuation via an event_id cursor (since_id).
- Handle lost connections and reconnection gracefully:
  - On reconnect, resume from the last seen event_id.
  - When using the bridge, optionally fall back to HTTP polling when the
    WebSocket is unavailable.
- Provide a minimal but useful display for testing:
  - Update the chat view by processing final and message_appended events.
  - Optionally trigger a full message reload on request_completed.
  - Offer a dedicated debug overlay that shows all events with expandable
    details.

1.2 Development stages

The work is split into two stages:

- Stage 1 – Polling only
  - Implement the abstraction and minimal display using only HTTP polling
    against /events.
  - Must work with the current version of the bridge (which only acts
    as an HTTP proxy for the mobile app) and not depend on new bridge
    streaming features.

- Stage 2 – Bridge streaming
  - Integrate real-time streaming over the Elixir bridge using
    session_event push messages.
  - Keep the polling implementation intact and easily switchable by
    build-time flag or runtime option.

1.3 Constraints and assumptions

- The server/bridge event architecture from STREAMING_EVENTS_PLAN.md is
  assumed:
  - Python generates events and checkpoint markers.
  - Elixir stores events and exposes streaming via
    events_subscribe and events_update.
  - Mobile connects either directly via HTTP or via the bridge.
- Event shapes are defined in docs/api/events.md and must remain the
  single source of truth for:
  - Request lifecycle events (request_started, request_completed, etc.).
  - Assistant streaming events (partial, final).
  - Tool events (tool_calls, tool_partial, tool_results).
  - Session/message lifecycle events (session_created, message_appended,
    message_modified, messages_deleted).
  - Internal session_checkpoint events (internal only).
  - New checkpoint marker events to be added for alignment.
- We do not change the core Message or Session types (no per-message
  UUIDs); all continuation and consistency are based on event_id and a
  per-session cursor_event_id.

2. Core Mobile Abstractions
---------------------------

2.1 Event type definitions

Create central TypeScript definitions that mirror docs/api/events.md.
These can live in a new file (src/eventsTypes.ts) or inside src/api.ts.

Key types (conceptual, not exact syntax):

- BaseEvent
  - event_id: string
  - type: string
  - session_id: string
  - request_id?: string

- FinalEvent
  - type: final
  - messages: ApiMessage[] (from docs/api/events.md)

- MessageAppendedEvent
  - type: message_appended
  - role: user | assistant | system | tool
  - content: string
  - metadata?: object
  - message?: ApiMessage
  - session?: object (full Session; not used by mobile in Stage 1)

- RequestCompletedEvent
  - type: request_completed

- Other events (for completeness and future use):
  - RequestStartedEvent, ErrorEvent.
  - PartialEvent (assistant streaming chunks).
  - ToolCallsEvent, ToolPartialEvent, ToolResultsEvent.
  - SessionCreatedEvent, MessageModifiedEvent, MessagesDeletedEvent.
  - CheckpointEvent (new checkpoint marker; see STREAMING_EVENTS_PLAN.md).

All events seen by the mobile app should be typed as a discriminated union
Event = FinalEvent | MessageAppendedEvent | RequestCompletedEvent | ...

2.2 Events API helpers

Extend src/api.ts to wrap /events (HTTP) and surface cursor_event_id.

- Add types:
  - ListEventsParams
    - sessionId?: string
    - sinceId?: string
    - requestId?: string
    - limit?: number
  - ListEventsResponse
    - events: Event[]

- Add helper apiListEvents(adapter, params) that:
  - Builds a query string with session_id, since_id, request_id, limit.
  - Calls adapter.get(/events?...) and returns data.events as Event[].

- Extend apiListMessages to surface cursor_event_id:
  - ListMessagesResponse
    - messages: IndexedMessage[]
    - cursor_event_id?: string | null

Frontends will use cursor_event_id as the initial since_id cursor when
subscribing to events.

2.3 SessionEventSource abstraction

Introduce a transport-agnostic interface for consuming session events:

- SessionEventSource
  - start(options):
    - sessionId: string | null
    - initialSinceId: string | null
    - onEvents(events: Event[]): void
  - stop(): void
  - getLastEventId(): string | null
  - getStatus(): idle | running | error

Two concrete implementations:

- PollingEventSource – HTTP polling only (Stage 1 and fallback in Stage 2).
- BridgeEventSource – push-based streaming over the Elixir bridge
  (Stage 2), with optional polling fallback.

2.4 useSessionEvents hook

Create src/useSessionEvents.ts exposing a hook that builds and manages a
SessionEventSource.

Signature (conceptual):

- UseSessionEventsOptions
  - adapter: ConnectionAdapter
  - sessionId: string | null
  - enabled: boolean
  - initialSinceId: string | null (from cursor_event_id)
  - mode?: auto | polling | bridge

- UseSessionEventsResult
  - lastEventId: string | null
  - status: idle | running | error
  - error: Error | null

- useSessionEvents(options, onEvents): UseSessionEventsResult

Responsibilities:

- Construct a SessionEventSource when sessionId, adapter, or mode change,
  and when enabled is true.
- Start the source with (sessionId, initialSinceId, onEvents).
- Stop the previous source on cleanup.
- Track lastEventId, status, and error in React state.

Source selection policy:

- Stage 1: always use PollingEventSource.
- Stage 2:
  - If mode == polling: use PollingEventSource.
  - If mode == bridge and adapter is a BridgeAdapter: use BridgeEventSource,
    else PollingEventSource.
  - If mode == auto (default):
    - If adapter is a BridgeAdapter: BridgeEventSource.
    - Otherwise: PollingEventSource.

3. Stage 1 – Polling Implementation
-----------------------------------

Stage 1 uses HTTP polling only but establishes the abstraction and minimal
display logic that Stage 2 will reuse.

3.1 PollingEventSource

Implementation outline:

- Fields:
  - adapter: ConnectionAdapter
  - timer: Timeout | null
  - sessionId: string | null
  - sinceId: string | null
  - onEvents: function | null
  - lastEventId: string | null
  - status: idle | running | error
  - stopped: boolean
  - intervalMs: number (e.g., 1000)
  - backoffMs: number (e.g., 5000)

- start(options):
  - Store sessionId, onEvents.
  - Initialize sinceId and lastEventId from initialSinceId.
  - Set stopped = false, status = running.
  - Schedule pollOnce immediately (delay 0).

- pollOnce():
  - If stopped or sessionId is null or onEvents is null: return.
  - Call apiListEvents(adapter, { sessionId, sinceId, limit: 100 }).
  - On success:
    - If events length > 0:
      - Compute max event_id; update lastEventId and sinceId.
      - Call onEvents(events).
    - Set status = running.
    - Schedule next poll after intervalMs.
  - On error:
    - Set status = error.
    - Leave sinceId unchanged (so we resume from the same point).
    - Schedule next poll after backoffMs.

- stop():
  - Set stopped = true.
  - Clear timer if present.
  - Set status = idle.

- getLastEventId() and getStatus() return stored values.

3.2 useSessionEvents – Stage 1 behaviour

- On mount or when options change:
  - Stop any existing source.
  - If enabled is true and sessionId is non-null:
    - Create a new PollingEventSource for the adapter.
    - Wrap onEvents to update lastEventId state.
    - Call source.start({ sessionId, initialSinceId, onEvents: wrapped }).
- On unmount or when disabled / sessionId becomes null:
  - Call source.stop().

The hook maintains:

- lastEventId (starting from initialSinceId).
- status and error (optional but recommended).

3.3 Minimal display logic in SessionChatScreen

SessionChatScreen integrates useSessionEvents and processes events into the
chat view and the debug buffer.

3.3.1 Using cursor_event_id

- When loading messages via apiListMessages:
  - Store cursor_event_id as initialSinceId for useSessionEvents.
  - Messages represent the session state as of that cursor.

3.3.2 Event processing goals

Minimal Stage 1 behaviour:

- Show all message roles (user, assistant, system, tool) contained in
  final events by appending them to the chat view.
- Process message_appended events to reflect messages appended by other
  clients or the server.
- Optionally trigger a full message reload on request_completed for
  consistency, controlled by a simple constant (false by default).

3.3.3 Feature flag for reload-on-complete

- In SessionChatScreen.tsx (or imported config):
  - AUTO_RELOAD_ON_REQUEST_COMPLETED = false

If set to true, SessionChatScreen should call reloadMessages() when it sees
request_completed for the current session.

3.3.4 Event handler implementation

- handleEvents(events):
  - Filter events by session_id == current sessionId.
  - For each relevant event:
    - If type == final: call applyFinalEvent.
    - If type == message_appended: call applyMessageAppendedEvent.
    - If type == request_completed and AUTO_RELOAD_ON_REQUEST_COMPLETED is
      true: call reloadMessages().
  - Regardless of type, pass the full batch to appendEventsToDebugBuffer so
    the debug overlay sees all events.

3.3.5 applyFinalEvent – append based on finals

- For a FinalEvent ev:
  - Iterate through ev.messages.
  - For each message:
    - Append to the local messages state as a new IndexedMessage, with
      index = current length (client-side index).
  - This is approximate (indices may diverge from server indices when
    showing only the last N messages) but sufficient for initial streaming
    display.
  - The authoritative state is restored on reloadMessages().

3.3.6 applyMessageAppendedEvent

- For a MessageAppendedEvent ev:
  - If ev.message is present:
    - Append { index: current length, message: ev.message } to the local
      messages state.
  - This keeps the chat UI in sync with appended messages from other
    sources.

4. Debug Overlay for Events
---------------------------

Add a debug overlay that:

- Appears on top of the current view without unmounting it.
- Shows all events seen by useSessionEvents for the connection.
- Allows expanding each event to inspect its full JSON payload.
- Provides a concise unexpanded view so users can easily choose the right
  event to inspect.
- Is triggered by an explicit action in the session UI.

4.1 Triggering the debug view

- In SessionChatScreen (or a containing component):
  - Maintain debugVisible state (boolean).
  - Add a button or action (for example, in session actions or header) that
    sets debugVisible = true. A label like "Debug events" is fine.

4.2 Overlay structure

- Render the debug overlay as a full-screen absolute View layered above the
  chat UI:
  - Container View with position: absolute, top/left/right/bottom = 0.
  - Semi-opaque background (e.g., rgba(0,0,0,0.85)).
  - Contains DebugEventsView and a close button.
- Example structure:
  - Outer View (flex: 1)
    - ChatView (existing chat UI)
    - If debugVisible:
      - Debug overlay View covering the screen.
        - DebugEventsView (list of events)
        - Close button that sets debugVisible = false.

4.3 Debug event buffer

- SessionChatScreen maintains a debugEvents array in state.
- appendEventsToDebugBuffer(events) should:
  - Concatenate new events onto the buffer.
  - Optionally cap the buffer size (e.g., last 200 events) to bound memory.

4.4 DebugEventsView UI

- Top-level controls:
  - Close button (e.g., top-right) calling onClose.
  - Optional future filters (by type, request_id) can be added later.

- Event list:
  - Use FlatList or ScrollView to render events in reverse chronological
    order or in event_id order.
  - For each event row:
    - Collapsed view:
      - Show event_id, type, session_id, and optional request_id.
      - Show a short, type-specific summary:
        - final: "final – N messages (roles: assistant, tool, ...)".
        - message_appended: "message_appended – role: user, content: 'Hello...'".
        - tool_results: "tool_results – N messages".
        - error: "error – detail: '...shortened...'".
      - This summary helps users quickly identify the right event.
    - Expanded view:
      - Show the full event as pretty-printed JSON in a monospace font.
      - Wrap it in a height-limited ScrollView so large payloads are
        scrollable without expanding the entire row.
  - Tapping a row toggles expanded/collapsed state per event_id.

This overlay acts as a developer-facing event inspector while being usable
for advanced users.

5. Stage 2 – Bridge Streaming
-----------------------------

Stage 2 adds real-time streaming over the Elixir bridge while preserving
the Stage 1 abstraction and behaviour.

5.1 BridgeAdapter – surfacing session_event

Server/bridge prerequisites (from STREAMING_EVENTS_PLAN.md and
docs/api/events.md):

- Python BridgeClient forwards stored events to the bridge as session_event
  messages.
- ServerChannel in Elixir re-broadcasts these via PubSub.
- AppChannel pushes to app sockets with event: "session_event" and
  payload: { event: <event-json> }.

On the mobile side, extend BridgeAdapter (in App.tsx) to expose these
events.

- Extend WebSocket onmessage handler:
  - After ref-based reply routing, if data.event == "session_event" and
    data.payload.event exists, call a new handleSessionEvent(ev) method.

- Add SessionEventListener support:
  - Define type SessionEventListener = (event: Event) => void.
  - Maintain a Set of listeners on BridgeAdapter.
  - Implement addSessionEventListener(listener) and
    removeSessionEventListener(listener).
  - handleSessionEvent(ev) should iterate listeners and call each with ev
    (catching and logging errors so one listener cannot break others).

5.2 BridgeEventSource implementation

Implement BridgeEventSource to satisfy SessionEventSource for bridge-based
streaming.

- Fields:
  - adapter: BridgeAdapter
  - sessionId: string | null
  - sinceId: string | null
  - lastEventId: string | null
  - status: idle | running | error
  - onEvents: function | null
  - listener: SessionEventListener | null
  - fallbackPolling: PollingEventSource | null (optional)

- start(options):
  - Store sessionId, onEvents.
  - Initialize sinceId and lastEventId from initialSinceId.
  - Set status = running.
  - Optionally perform a one-off HTTP catch-up via apiListEvents using
    initialSinceId, then deliver that batch to onEvents.
  - Register listener on adapter:
    - For each pushed event ev:
      - If sessionId is non-null and ev.session_id != sessionId: ignore.
      - If sinceId is non-null and ev.event_id <= sinceId: ignore.
      - Update lastEventId and sinceId to ev.event_id.
      - Call onEvents([ev]).

- stop():
  - Remove listener from BridgeAdapter.
  - Stop fallbackPolling if present.
  - Set status = idle.

- getLastEventId and getStatus return stored values.

Fallback to polling (optional):

- On WebSocket disconnect or repeated errors (exposed by BridgeAdapter via
  onclose/onerror or dedicated hooks):
  - Mark status = error.
  - Create a PollingEventSource starting from current lastEventId.
  - Use it to continue delivering events via onEvents until the bridge
    reconnects, at which point polling can be stopped.

5.3 useSessionEvents – strategy selection

In Stage 2, useSessionEvents chooses between PollingEventSource and
BridgeEventSource based on mode and adapter type:

- If mode == polling:
  - Always use PollingEventSource.
- If mode == bridge:
  - If adapter is BridgeAdapter: use BridgeEventSource.
  - Else: use PollingEventSource.
- If mode == auto (default):
  - If adapter is BridgeAdapter: use BridgeEventSource.
  - Otherwise: use PollingEventSource.

Switching back to polling only:

- Build-time: default mode to polling.
- Runtime: expose a simple app-level or dev-only toggle to force mode to
  polling.

The event processing in SessionChatScreen and the debug overlay logic
remain unchanged and continue to rely only on the Event[] batches from
useSessionEvents.

6. Testing Strategy
-------------------

6.1 Stage 1 – Polling

- Unit/integration tests (optional but recommended):
  - PollingEventSource polls /events with correct session_id and since_id,
    updates lastEventId, and reschedules correctly on success and error.
  - useSessionEvents starts and stops sources based on sessionId and
    enabled, and passes lastEventId/status/error back to callers.
- Manual tests:
  - Run Python server locally, connect mobile via direct HTTP.
  - Open a session and send a request; confirm:
    - /events includes final, message_appended, request_completed, and
      other events as per docs/api/events.md.
    - The chat view updates when final and message_appended events arrive.
    - The debug overlay displays all events with summaries and expandable
      raw JSON.
    - Enabling AUTO_RELOAD_ON_REQUEST_COMPLETED triggers a full reload
      after request_completed.

6.2 Stage 2 – Bridge streaming

- With bridge event forwarding configured:
  - Confirm BridgeAdapter receives session_event messages and invokes
    listeners with parsed Event objects.
  - Verify BridgeEventSource filters by sessionId and sinceId and updates
    lastEventId.
  - Test disconnect/reconnect scenarios:
    - Bridge or network failure should not crash the app; if fallback
      polling is implemented, events continue via HTTP.
    - On reconnect, events resume from the correct cursor without
      duplicates.
  - Confirm chat view and debug overlay behave similarly under streaming
    and polling (except for latency differences).

7. Files to Read Before Implementation
--------------------------------------

Before implementing this plan, read and understand at least the following
files:

Server / bridge docs:
- STREAMING_EVENTS_PLAN.md
  - Overall event architecture, checkpoint markers, and bridge streaming
    design.
- docs/api/events.md
  - Full description of event types, fields, and where they are produced.
  - Must be updated to include the new checkpoint event.

Python application and bridge:
- application/python/agent_terminal_app/server.py
  - /events and /sessions/{session_id}/messages endpoints.
  - How events and checkpoints are published.
- application/python/agent_terminal_app/bridge_client.py
  - How events are forwarded to the bridge (polling with since_id).
- bridge-elixir/AGENTS.md, bridge-elixir/README.md
  - Bridge responsibilities and message contracts.
- bridge-elixir/lib/bridge/server_channel.ex
  - Handling of session_event messages from servers.
- bridge-elixir/lib/bridge/app_channel.ex
  - How events are pushed to app sockets (session_event).

Mobile app:
- mobile/crystal-lattice-control-rn/AGENTS.md
  - General guidelines for React Native code, styling, and architecture.
- mobile/crystal-lattice-control-rn/App.tsx
  - ConnectionAdapter and BridgeAdapter implementations.
  - Current WebSocket handling and where to add session_event listeners.
- mobile/crystal-lattice-control-rn/src/api.ts
  - Existing HTTP wrappers for /sessions, /sessions/{id}/messages, and
    /events.
- mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx
  - Chat UI, message loading, and where to integrate useSessionEvents and
    the debug overlay.
- mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx
  - High-level navigation and how SessionChatScreen is used.

These files provide the necessary context to implement the mobile event
abstraction, minimal display logic, and debug overlay in a way that aligns
with the existing architecture and upcoming server/bridge changes.
