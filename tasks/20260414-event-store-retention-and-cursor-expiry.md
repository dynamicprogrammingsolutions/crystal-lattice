# Event Store Retention And Cursor Expiry

Design and implement bounded retention for the in-memory event store so it does not grow without limit, while keeping clients correct by treating missing/expired cursors as a normal recovery case.

## Requirements checklist

- [x] Add safe bounded-retention behavior to the shared event store without breaking normal polling/recovery semantics.
- [x] Define and implement explicit cursor-expiry handling across the backend and frontend SDK.
- [x] Preserve the current restart-safe opaque event cursor model.
- [x] Evaluate optional follow-ups for partial-event compaction, differentiated retention by event type, and active-consumer cursor tracking.

## Current context

Recent related work already changed event ids from plain numeric strings to opaque per-store ids in `core/python/agent_app/events.py`, currently shaped as `<store-instance>:<counter>`. That solved the restart/polling bug by making `since_id` safe across server restarts without adding an HTTP-only epoch field.

Relevant current files:

- `core/python/agent_app/events.py`
- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `packages/frontend-sdk/src/backend/backend.ts`
- `packages/frontend-sdk/src/backend/restBackend.ts`
- `packages/frontend-sdk/src/events/pollingEventSource.ts`
- `packages/frontend-sdk/src/chat/chatController.ts`
- `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`
- `application/python/tests/test_agent_terminal_app_server.py`
- `core/python/tests/test_event_store_cursors_and_locks.py`

Current behavior summary:

- Session state is durable in session JSON files.
- The event store is transient, in-memory, and intended for incremental UI updates.
- Clients can already recover by reloading `/sessions/{id}/messages` and restarting polling from the returned cursor.
- Event compaction currently happens mostly on read in `AgentApplication.compact_events(...)`, not at event-store retention time.

This makes bounded retention a good fit: the event store does not need to be the permanent source of truth.

## Recommended implementation scope

### Phase 1: Safe bounded retention and cursor expiry

This is the safest and highest-value change. Implement these two together.

1. Add retention limits to `InMemoryEventStore`.
2. Add explicit cursor-expired signaling when a client asks for a `since_id` that has fallen out of retention.
3. Teach the frontend SDK polling/controller path to recover by reloading messages when the cursor expires.

### Phase 2: Optional improvements

These are useful but should be treated as follow-up or clearly isolated sub-steps:

- publish-time compaction of partial events
- differentiated retention by event type
- tracking the oldest cursor needed by active consumers

## Detailed implementation plan

### 1. Extend the event-store interface for retention-aware listing

Current interface in `core/python/agent_app/events.py`:

- `publish(event) -> event`
- `list(..., since_id, request_id, session_id, limit) -> List[Dict[str, Any]]`
- `get_latest_event_id(...) -> Optional[str]`

Proposed change:

- keep `publish(...)` unchanged
- keep `get_latest_event_id(...)` unchanged
- replace `list(...) -> List[Dict[str, Any]]` with a richer result, for example:

```python
class EventListResult(TypedDict):
    events: List[Dict[str, Any]]
    latest_event_id: Optional[str]
    cursor_expired: bool
```

Updated protocol shape:

```python
def list(
    self,
    *,
    since_id: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100,
) -> EventListResult:
    ...
```

Why:

- The store is the correct layer to know whether a cursor is still representable within retention.
- `cursor_expired` should not be inferred in HTTP code by poking through store internals.
- Returning `latest_event_id` directly from the store result reduces duplicate lookup work in server/app callers.

Notes:

- This is a contract change inside Python app layers, but not necessarily a public user-facing SDK change yet.
- Callers in `server.py` and `terminal_app.py` will need small updates.

### 2. Add retention configuration to `InMemoryEventStore`

In `core/python/agent_app/events.py`, extend `InMemoryEventStore.__init__` with optional limits:

```python
def __init__(
    self,
    *,
    max_events_global: Optional[int] = 10000,
    max_events_per_session: Optional[int] = None,
    max_event_age_seconds: Optional[float] = None,
) -> None:
```

Recommended first implementation:

- support `max_events_global`
- support `max_event_age_seconds`
- leave `max_events_per_session` optional if easy, but it can be postponed if it complicates pruning logic too much

Implementation details:

- store lightweight publish metadata per event, e.g. `_published_at_monotonic`
- prune after each `publish(...)`
- global cap:
  - keep the newest `max_events_global` events
- age cap:
  - drop events older than the configured age

Important rule:

- retention is about what remains listable for incremental polling
- it must not affect session JSON persistence or session cursor correctness

### 3. Detect cursor expiry at the store layer

The store should report `cursor_expired=True` when all of these are true:

- caller supplied `since_id`
- `since_id` is not the sentinel bootstrap value (`None` or `"0"`)
- `since_id` cannot be found in the retained event window
- there are still relevant events in the store for that filter scope, or the store’s retained low-water mark is newer than `since_id`

Practical implementation approach:

- keep track of the oldest retained event id globally
- optionally keep oldest retained event id per session if per-session retention is enabled
- when `since_id` belongs to the current store instance but predates the retained window, mark `cursor_expired=True`

Important distinction:

- `since_id` from another store instance after restart is not an error
  - current opaque id logic should still replay safely from the beginning of the current store
- `since_id` from the current store instance but already pruned by retention is the true expiry case

### 4. Expose cursor expiry through the application/server layers

#### HTTP server

In `application/python/agent_terminal_app/server.py`, update `/events` response shape to include:

```json
{
  "events": [...],
  "latest_event_id": "...",
  "cursor_expired": false
}
```

This is the one intentional wire-level addition for Phase 1.

Why this field is acceptable:

- unlike the earlier `server_instance_id`, this is not leaking transport-specific lifecycle details
- it is a real cross-consumer semantic needed for safe recovery

#### Terminal application

In `application/python/agent_terminal_app/terminal_app.py`:

- update `poll_new_events(...)` to handle store results, not just raw event lists
- if `cursor_expired` is true, decide whether terminal should:
  - set a local “needs reload” flag and surface a message, or
  - automatically reload the active session before continuing

Recommended terminal behavior:

- do not silently ignore expiry
- surface a clear “event cursor expired; reload required” state, or perform an explicit reload if that aligns with terminal UX

### 5. Update frontend SDK backend contracts

In `packages/frontend-sdk/src/backend/backend.ts`, evolve:

```ts
export interface ListEventsResult {
  events: Event[];
  latestEventId: string | null;
  cursorExpired: boolean;
}
```

Then update `RestAgentBackend.listEvents(...)` in `packages/frontend-sdk/src/backend/restBackend.ts` to map `cursor_expired` from the HTTP response.

### 6. Add polling/controller recovery for cursor expiry

#### Polling layer

In `packages/frontend-sdk/src/events/pollingEventSource.ts`:

- when `listEvents(...)` returns `cursorExpired: true`
  - stop treating the stream as incremental
  - surface a typed failure to the controller layer rather than silently continuing

Suggested API addition:

```ts
export type PollingStatus = 'idle' | 'running' | 'error' | 'expired';
```

or emit a dedicated callback/event:

```ts
onCursorExpired?: () => void;
```

I recommend the explicit callback, because expiry is a recoverable state transition, not just a generic polling status.

#### Controller layer

In `packages/frontend-sdk/src/chat/chatController.ts`:

- add a dedicated recovery method if needed, e.g. `recoverAfterCursorExpiry()`
- implementation:
  - stop event streaming
  - reload messages for the current range
  - clear stale transient request/streaming state as appropriate
  - restart event streaming from the fresh cursor

This is similar to the existing manual recovery path, but should be explicit and tied to cursor expiry.

### 7. Tests for the safe core scope

#### Python unit tests

Add coverage in `core/python/tests/test_event_store_cursors_and_locks.py` or a new dedicated file:

- retained-window pruning keeps event ids opaque and monotonic within one store instance
- old `since_id` from same store but pruned window returns `cursor_expired=True`
- `since_id` from another store instance after restart still replays safely and does not report expiry
- age-based pruning behaves as expected

#### Python app/server tests

Extend `application/python/tests/test_agent_terminal_app_server.py`:

- `/events` includes `cursor_expired: false` for normal responses
- `/events` includes `cursor_expired: true` when asking for a pruned cursor
- session-scoped filtered responses still include `latest_event_id`

#### Frontend SDK tests

Add or extend tests around:

- `RestAgentBackend.listEvents()` mapping `cursor_expired`
- `PollingEventSource` handling cursor expiry
- `ChatController` automatic recovery path if implemented there

#### Real integration tests

Extend `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`:

- bounded-retention scenario where a client’s old cursor expires
- verify the client reloads and continues correctly
- keep the existing restart/cache tests green

## Optional items

### Optional A: Publish-time partial compaction

Current state:

- compaction mainly happens on read via `AgentApplication.compact_events(...)`

Potential improvement:

- reduce memory pressure by compacting at publish time for `partial` and `tool_partial`

Possible design:

- per `(session_id, request_id, type)` rolling buffer inside `InMemoryEventStore`
- instead of appending every partial event separately:
  - merge consecutive partials for the same stream before storing
- on terminal events (`final`, `tool_results`):
  - flush or replace the rolling partial state appropriately

Benefits:

- large reduction in memory usage for long streams

Risks:

- more complex publish path
- debug consumers may lose exact token-by-token granularity

Recommendation:

- implement only after the safe retention/expiry path is finished
- likely behind a config flag first

### Optional B: Differentiated retention by event type

Goal:

- keep durable/recovery-relevant events longer than transient noisy ones

Example policy:

- `partial`, `tool_partial`
  - short retention or aggressive compaction
- `request_started`, `request_completed`, cancel lifecycle
  - medium retention
- `final`, `tool_results`, `checkpoint`, `message_appended`, `message_modified`, `messages_deleted`
  - longest retention within the in-memory store

Possible interface:

```python
def __init__(
    self,
    *,
    max_events_global: Optional[int] = 10000,
    max_event_age_seconds: Optional[float] = None,
    retention_by_type: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
```

Potential pitfalls:

- pruning order becomes more complex
- per-type retention interacts with cursor-expired detection

Recommendation:

- use only after the simpler global/age retention is proven
- likely easiest if implemented as “prune transient types first” rather than a fully general policy engine

### Optional C: Track the oldest active cursor across consumers

Goal:

- retain only what active clients may still need, instead of using only a fixed-size/fixed-age window

Possible design:

- introduce explicit consumer registration in the event store or app layer:

```python
register_consumer(consumer_id: str, session_id: Optional[str], cursor_id: Optional[str]) -> None
update_consumer_cursor(consumer_id: str, cursor_id: Optional[str]) -> None
unregister_consumer(consumer_id: str) -> None
```

- prune only events older than the minimum active cursor

Pros:

- optimal retention under active load

Cons:

- significantly more stateful
- HTTP polling clients are currently stateless, so this requires leases/heartbeats/cleanup
- more hidden failure modes if consumers disconnect without unregistering

Recommendation:

- interesting future optimization, but not a good first implementation
- consider only if fixed retention proves too blunt

## Proposed sequencing

1. Change the Python event-store list contract to return retention metadata.
2. Add basic global/age retention to `InMemoryEventStore`.
3. Implement cursor-expired detection for same-store pruned cursors.
4. Expose `cursor_expired` through `/events`.
5. Update frontend SDK backend contract and poller/controller recovery.
6. Add unit/server/integration coverage for retention expiry.
7. Optionally evaluate publish-time compaction.
8. Optionally evaluate differentiated retention.
9. Defer active-consumer cursor tracking unless needed.

## Success criteria

- Long-running sessions no longer cause unbounded event-store growth.
- Clients with expired cursors recover automatically via reload rather than silently missing updates.
- Restart-safe opaque cursor behavior remains correct.
- Existing restart/cache integration regressions remain green.

## Open questions

- Should `cursor_expired` trigger automatic reload in all frontend consumers, or only surface a typed error and let the app decide?
- Should terminal polling auto-reload on expiry, or show a visible “reload required” notice?
- Do we want retention configuration exposed in app config immediately, or keep it constructor-only first for the in-memory store?

## Execution plan

Added during completion.

1. Change `EventStore.list(...)` and `InMemoryEventStore.list(...)` to return structured retention metadata, then implement global-count and age-based pruning in the event store with same-store cursor-expiry detection.
2. Update Python callers in the terminal app and HTTP server to consume the richer list result and expose `cursor_expired` through `/events`.
3. Extend the frontend SDK backend contract to carry `cursorExpired`, then update the polling layer to surface expiry and the chat controller to recover automatically via reload + polling restart.
4. Add and update unit/server/integration tests for pruning, cursor expiry, and end-to-end client recovery, then update this task file with completion notes and checklist status.

## Completion notes

Added during completion.

- Implemented Stage 1 retention and expiry handling in `core/python/agent_app/events.py`.
  - `EventStore.list(...)` now returns a structured result with `events`, `latest_event_id`, and `cursor_expired`.
  - `InMemoryEventStore` now supports `max_events_global` and `max_event_age_seconds`.
  - The store tracks evicted high-water marks globally, per session, and per request so cursor expiry is scoped to the relevant logical stream.
  - Opaque `<store-instance>:<counter>` event ids remain the restart-safe cursor format.

- Implemented backend/server propagation.
  - `/events` in `application/python/agent_terminal_app/server.py` now returns `cursor_expired`.
  - The HTTP route continues to expose the global `latest_event_id` bootstrap hint for compatibility.
  - `application/python/agent_terminal_app/terminal_app.py` keeps its public polling/list methods list-shaped and surfaces cursor expiry via a synthetic `events_cursor_expired` event in polling.

- Implemented frontend SDK recovery.
  - `packages/frontend-sdk/src/backend/backend.ts` and `packages/frontend-sdk/src/backend/restBackend.ts` now carry `cursorExpired`.
  - `packages/frontend-sdk/src/events/pollingEventSource.ts` surfaces expiry as polling status `expired` and invokes a callback instead of silently continuing.
  - `packages/frontend-sdk/src/chat/chatController.ts` now auto-recovers from cursor expiry by reloading messages and restarting polling.
  - `packages/frontend-sdk-react/src/useChatController.ts` avoids immediately re-starting polling when recovery failed and the controller is in `expired` status.

- Added tests.
  - Python unit coverage in `core/python/tests/test_event_store_cursors_and_locks.py` for restart-safe replay, count-based pruning expiry, and age-based pruning expiry.
  - Server-route coverage in `application/python/tests/test_agent_terminal_app_server.py` for `/events` cursor expiry and retained bootstrap semantics.
  - Terminal coverage in `application/python/tests/test_terminal_application.py` for synthetic `events_cursor_expired`.
  - Frontend SDK unit coverage in `packages/frontend-sdk/src/chat/__tests__/chatController.test.ts` for automatic expiry recovery.
  - Real-backend integration coverage in `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts` for expired cursor recovery with a tiny retained event window.
  - Test harness support for retention-limited backends was added in `packages/frontend-sdk/src/integration/harness.ts` and `scripts/run_backend_server_for_ts_integration_tests.py`.

- Verification:
  - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts`: passed.
  - `npm test` in `packages/frontend-sdk`: passed.
  - `pytest core/python/tests/test_event_store_cursors_and_locks.py core/python/tests/test_application_config_errors.py -q`: passed.
  - `pytest application/python/tests/test_agent_terminal_app_server.py -q -k "server_flow_with_echo_provider or checkpoint_cursor_after_final_event or checkpoint_cursor_after_append or list_session_messages_exposes_active_request_id_during_and_after_request or events_endpoint"`: passed.
  - `pytest application/python/tests/test_terminal_application.py -q -k "poll_new_events_compacts_partials or poll_new_events_surfaces_cursor_expiry"`: passed.
  - `pytest application/python/tests/test_event_payload_size_budget.py -q`: passed.

- Remaining note:
  - The full `application/python/tests/test_agent_terminal_app_server.py -q` run did not complete within the allotted timeout in this session, so verification was done via the targeted subset covering the changed server/event paths.