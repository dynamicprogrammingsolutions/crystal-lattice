STREAMING EVENTS CURSOR & COMPACTION PLAN

This plan describes coordinated changes to the HTTP `/events` endpoint, the shared `EventStore`, and the terminal application so that:

- Event polling never replays the entire history for sessions that already have a known cursor.
- Clients can bootstrap global polling without pulling all historical events.
- Poll responses are compacted to strip redundant `partial` and `tool_partial` events once final results are available, while preserving live streaming behavior.

It builds on the existing checkpoint/cursor design in `AgentApplication` and keeps the underlying `EventStore` as an append-only, un-opinionated log.

---

1. CURRENT BEHAVIOR

1.1 HTTP `/events` endpoint

- Location: `application/python/agent_terminal_app/server.py`.

- Current implementation:

  - Signature:

    - `GET /events` with query params:
      - `since_id: Optional[str]`
      - `request_id: Optional[str]`
      - `session_id: Optional[str]`
      - `limit: int = 100`

  - Behavior:

    - Calls `app_instance.get_event_store()` and delegates to `store.list(...)`:
      - `since_id=since_id`
      - `request_id=request_id`
      - `session_id=session_id`
      - `limit=limit`
    - Returns `{ "events": events }`.

- `EventStore.list` in `core/python/agent_app/events.py`:

  - `InMemoryEventStore` implementation:
    - Computes `since` as:
      - `since = int(since_id)` when `since_id` is not `None` and parses.
      - `since = 0` when `since_id` is `None`.
    - Iterates over `_events` in insertion order, and for each event:
      - Skips if its `event_id` (as int) `<= since`.
      - Skips if `request_id` filter does not match.
      - Skips if `session_id` filter does not match.
      - Appends matching events until `limit` is reached.

- Consequence:

  - When `/events` is called with `since_id=None` and `session_id` set, the handler returns **all events for that session** up to `limit`.
  - When `/events` is called with both `since_id=None` and `session_id=None`, it returns **all events in the store** up to `limit`.

1.2 Terminal polling behavior

- Location: `application/python/agent_terminal_app/terminal_app.py`.

- Terminal and HTTP server can share an `InMemoryEventStore` when run together.

- `TerminalApplication` maintains `_last_event_id: str | None` to track the last seen event:
  - Initialized to `None` in `__init__`.
  - Reset to `None` in several places, including:
    - After creating a session (`create_session`).
    - After switching sessions (`switch_session`).

- Streaming poll:

  - `poll_new_events(self, limit: int = 50) -> List[Dict[str, Any]]`:
    - Determines current `session = self.session`.
    - Calls `store.list(...)` with:
      - `since_id=self._last_event_id`
      - `request_id=None`
      - `session_id=session.session_id`
      - `limit=limit`
    - If events are returned, sets `self._last_event_id` to the `event_id` of the last event in the returned list.
    - Returns the events to the terminal UI for rendering.

- `switch_session(session_id: str)` currently:
  - Loads the session via `self._app.load_session(session_id)`.
  - Sets `self._core`, `self._base_config`, and `self._session`.
  - Resets `_last_event_id = None`.

- Consequence:

  - When switching to an existing session in the terminal, the next `poll_new_events` call uses `since_id=None`.
  - This causes the full event history for that session to be replayed to the UI.
  - A similar replay happens for any HTTP client that calls `/events` without a `since_id`.

1.3 AgentApplication cursors and checkpoints

- Location: `core/python/agent_app/application_future.py`.

- `AgentApplication` maintains:
  - Per-session locks.
  - A mapping `_session_cursor_event_id_by_session: Dict[str, Optional[str]]`.
  - Helper methods:
    - `record_checkpoint(session_id, request_id)` – emits a public `checkpoint` event and advances the per-session cursor.
    - `get_session_cursor_event_id(session_id)` – returns the stored cursor for a session (or `None`).

- The HTTP endpoint `GET /sessions/{id}/messages` already uses this cursor to return `cursor_event_id` alongside messages.

- Mobile and other clients can use `cursor_event_id` as a safe `since_id` for `/events`.

---

2. TARGET SEMANTICS

The goals for the updated behavior are:

1. **Session-aware default cursor:**
   - When `/events` is called with `session_id` but **without** `since_id`, the server should default to the stored cursor for that session, not replay from the beginning.

2. **Global bootstrap without replay:**
   - When `/events` is called **without** both `since_id` and `session_id` (and no `request_id`), the server should **not** return the full event log.
   - Instead, it should provide an empty `events` list plus a special `latest_event_id` field that clients can use as a high-watermark for the first real poll.

3. **Terminal parity:**
   - When switching sessions in the terminal, streaming event polling should resume from that session's cursor instead of replaying its entire history.

4. **Partial compaction:**
   - When polling, the server and terminal should strip redundant `partial` and `tool_partial` events from the returned batch if corresponding final events (`final` or `tool_results`) are present.
   - Live streaming behavior must remain unchanged for in-flight requests (no final yet).

---

3. SERVER-SIDE CHANGES: `/events` CURSOR SEMANTICS

3.1 Extend EventStore interface with get_latest_event_id

- File: `core/python/agent_app/events.py`.

- Add a new method to the `EventStore` protocol:

  - `get_latest_event_id(self, *, request_id: Optional[str] = None, session_id: Optional[str] = None) -> Optional[str]`.

- Semantics:
  - Returns the `event_id` (as string) of the most recent event matching the optional filters, or `None` if no such event exists.
  - Filters by `session_id` and `request_id` in the same way as `list`.

- Implement in `InMemoryEventStore`:
  - Iterate `_events` in reverse order.
  - Find the first event whose `request_id` and `session_id` match the provided filters.
  - Return its `event_id` as a string.
  - If no event matches, return `None`.

3.2 Default since_id from session cursor

- File: `application/python/agent_terminal_app/server.py`.

- Adjust the `/events` handler to compute an "effective since_id" when the caller omits `since_id` but provides `session_id`:

  - Logic:

    - Start with the user-provided `since_id` (may be `None`).
    - If `since_id` is `None` and `session_id` is not `None`:
      - Call `cursor = app_instance.get_session_cursor_event_id(session_id)`.
      - Use `cursor` as the effective `since_id` when calling `store.list`.

  - Behavior:
    - If a cursor exists for the session, only events **after** that cursor are returned.
    - If no cursor exists (e.g. legacy session with no checkpoints), behavior gracefully falls back to the existing "from the beginning" semantics.

3.3 Global bootstrap behavior when no session_id and no since_id

- Still in `/events` handler.

- Special-case the following request as a bootstrap call:

  - `since_id is None`
  - `session_id is None`
  - `request_id is None`

- New behavior for this case:
  - Do **not** call `store.list(...)` to fetch events.
  - Instead:
    - Call `latest_event_id = store.get_latest_event_id()` (no filters).
    - Return a response of the form:
      - `{ "events": [], "latest_event_id": latest_event_id }`.

- Rationale:
  - This scenario is not used by current clients, so we can change it without breaking compatibility.
  - It gives future clients a cheap way to bootstrap polling from "now" without reading the entire log.

3.4 Other cases: explicit since_id or request_id

- For all other requests to `/events`:

  - If `since_id` is provided (non-null), pass it through unchanged.
  - If `request_id` is provided, pass it through unchanged.
  - If `session_id` is provided and `since_id` is also provided, do not modify `since_id`.

- In all of these cases, `/events` should behave as today, except for the compaction step described in section 5.

---

4. TERMINAL CHANGES: RESUMING FROM CURSOR

4.1 Use session cursor when switching sessions

- File: `application/python/agent_terminal_app/terminal_app.py`.

- Current `switch_session(session_id: str)` behavior:
  - Loads the session via `self._app.load_session(session_id)`.
  - Updates `self._core`, `self._base_config`, and `self._session`.
  - Sets `self._last_event_id = None`.

- New behavior:
  - After successfully loading the session and updating `_core`, `_base_config`, and `_session`:
    - Call `cursor = self._app.get_session_cursor_event_id(session.session_id)`.
    - Set `self._last_event_id = cursor`.
  - If `cursor` is `None`, leave `_last_event_id = None` as the fallback.

- Effect on polling:
  - The next `poll_new_events` call will use `since_id=self._last_event_id`, which now reflects the session cursor instead of `None`.
  - This ensures only events after the persisted cursor are fetched and rendered; historical events are not replayed on session switch.

4.2 Preserve explicit history behavior for list_events

- `TerminalApplication.list_events(...)` is used for explicit history queries (e.g. `events` command):
  - It passes `since_id` through to `store.list` unchanged.
  - When `since_id` is omitted, it intentionally returns the full (filtered) history.

- Plan:
  - Leave `list_events` semantics untouched so that users can still inspect full history via the terminal when desired.

---

5. EVENT COMPACTION: PARTIAL AND TOOL_PARTIAL OPTIMIZATION

5.1 Motivation

- During streaming, the event log includes many `partial` and `tool_partial` events representing incremental reasoning and content updates.
- Once a `final` event (for assistant messages) or `tool_results` event (for tools) has been emitted for a given request, earlier partials for that request become redundant from a polling client perspective.
- When clients poll after a request has completed, there is no need to replay all of those partials if the complete message or tool results are available.

5.2 compact_events helper in AgentApplication

- File: `core/python/agent_app/application_future.py`.

- Add a new helper method and supporting configuration to control compaction behavior:

  - `def compact_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]`.

  - Internal flags (e.g. attributes or parameters) to allow enabling/disabling compaction methods, at least:
    - `enable_compaction: bool` – master on/off switch for **all** compaction.
    - `enable_drop_redundant_partials: bool` – controls dropping of `partial`/`tool_partial` events when finals exist.
    - `enable_merge_consecutive_partials: bool` – controls merging of consecutive partial events.

- Responsibilities:
  - Takes a single batch of events returned from `EventStore.list`.
  - Optionally applies one or more compaction passes depending on which flags are enabled:
    - Dropping redundant partials before finals/tool_results.
    - Merging consecutive partials when they share compatible structure.
  - Does not modify the underlying store or any shared state.

5.3 Compaction rules

Within one poll's `events` list:

1. Assistant messages (LLM content):
   - Terminal/complete events:
     - `type == "final"` (contains assistant `messages`).
   - Partial events:
     - `type == "partial"`.
   - For each `(session_id, request_id)` pair:
     - If the batch contains a `final` event, drop all earlier `partial` events for that `(session_id, request_id)` that appear **before** that `final` in this batch.
     - Keep:
       - The `final` event.
       - Any `assistant_message` lifecycle events.
       - Any `partial` events for requests that do **not** have a `final` in this batch.

2. Tool calls:
   - Terminal/complete events:
     - `type == "tool_results"`.
   - Partial events:
     - `type == "tool_partial"`.
   - For each `(session_id, request_id)` pair:
     - If the batch contains a `tool_results` event, drop all earlier `tool_partial` events for that `(session_id, request_id)` that appear **before** that `tool_results` in this batch.
     - Keep:
       - The `tool_results` event.
       - Any `tool_partial` events for requests that have no `tool_results` in this batch.

3. In-flight requests:
   - If a request is mid-flight (only `partial` or `tool_partial` seen, no `final` or `tool_results` yet), keep all partial events.
   - This preserves live streaming semantics for ongoing requests.

4. Other event types:
   - Do not drop or modify any events of other types (e.g. `request_started`, `request_completed`, `error`, `checkpoint`, `message_appended`).
   - Preserve the original order of all kept events.

5.4 Implementation strategy for compact_events

- Overall shape:
  - `compact_events` should be structured so that **each compaction method** can be toggled independently, for testing and debugging.
  - A suggested structure is:
    - If `not enable_compaction`, return `events` unchanged.
    - Otherwise, apply zero or more passes conditionally:
      - If `enable_drop_redundant_partials`: apply the drop pass.
      - If `enable_merge_consecutive_partials`: apply the merge pass.

- 5.4.1 Dropping redundant partials (existing optimization)

  - Use a two-pass approach over a single batch of events:

    1. Walk the `events` list **backwards** to determine which partials are redundant:
       - Maintain two maps keyed by `(session_id, request_id)`:
         - `seen_final[(sid, rid)] -> bool`.
         - `seen_tool_results[(sid, rid)] -> bool`.
       - Maintain a boolean array `keep[i]` for each event index.
       - For each event from end to start:
         - Extract `etype = ev.get("type")`, `sid = ev.get("session_id")`, `rid = ev.get("request_id")`.
         - If `etype == "final"`:
           - Mark `seen_final[(sid, rid)] = True` and `keep[i] = True`.
         - Else if `etype == "tool_results"`:
           - Mark `seen_tool_results[(sid, rid)] = True` and `keep[i] = True`.
         - Else if `etype == "partial"`:
           - If `seen_final[(sid, rid)]` is true, mark `keep[i] = False` (drop).
           - Otherwise, `keep[i] = True`.
         - Else if `etype == "tool_partial"`:
           - If `seen_tool_results[(sid, rid)]` is true, mark `keep[i] = False`.
           - Otherwise, `keep[i] = True`.
         - Else:
           - Mark `keep[i] = True` (never drop other types).

    2. Build the intermediate list by iterating forward and including only indices where `keep[i]` is true.

  - This preserves the order of all kept events and efficiently prunes only redundant partials.

- 5.4.2 Merging consecutive partials (new optimization)

  - After the drop pass (if enabled), we can optionally merge runs of consecutive partials to further reduce traffic when many tiny deltas are emitted.

  - Target patterns to merge (based on the actual event structures):

    1. Assistant partial containing reasoning:
       - Events where `type == "partial"` and the payload contains incremental reasoning text, typically found under `message.metadata.reasoning`.

    2. Assistant partial containing content:
       - Events where `type == "partial"` and the payload contains incremental assistant content, typically found under `message.content`.

    3. Tool result partials:
       - Events where `type == "tool_partial"` and the payload contains incremental tool output content.

  - Matching criteria:
    - We only merge **adjacent** partial events when ALL of the following hold:
      - Same `session_id`.
      - Same `request_id`.
      - Same `type` (`partial` vs `tool_partial`).
      - Same structural "shape" of the payload: for example, both have `message` dicts with a `content` string, or both have `metadata.reasoning` strings.
    - We use Python's `match` statement (structural pattern matching) to ensure events match the expected shapes before attempting to merge.

  - Merge behavior:
    - Assistant reasoning partials:
      - For two matching `partial` events A then B where both have `message.metadata.reasoning` as strings:
        - Create a new event C identical to B, but with `reasoning = A.reasoning + B.reasoning`.
        - Drop A from the sequence, keep C.

    - Assistant content partials:
      - For two matching `partial` events A then B where both have `message.content` as strings:
        - Create new event C identical to B, but with `content = A.content + B.content`.
        - Drop A, keep C.

    - Tool result partials:
      - For two matching `tool_partial` events A then B where both carry partial tool output content (e.g. `message.content` or a clearly defined tool-output field):
        - Concatenate the relevant content fields from A and B into a single combined field in C.
        - Drop A, keep C.

  - Pass structure:
    - Walk the (possibly already compacted) event list from start to end and build a new list:
      - Keep a `current` accumulator for the latest mergeable partial.
      - For each next event `ev`:
        - If `current` is `None`, set `current = ev`.
        - Else, attempt to merge `current` and `ev`:
          - If they match the same `(session_id, request_id, type)` and satisfy one of the merge patterns (using `match`):
            - Replace `current` with the merged event and continue.
          - Otherwise, push `current` to the output list and set `current = ev`.
      - At the end, push any remaining `current`.

  - Safety and readability:
    - Use Python `match`/`case` to clearly express the event shapes we support for merging.
    - If an event does not match any expected pattern, do not attempt to merge it.

  - Control via flags:
    - If `enable_merge_consecutive_partials` is `False`, skip this pass entirely and return the list from the drop pass (or the original list if drop is also disabled).

---

6. APPLYING COMPACTION IN SERVER AND TERMINAL

6.1 HTTP `/events` endpoint

- After computing the effective `since_id` (and before returning), apply compaction to the batch returned by `store.list`:

  - Pseudocode for non-bootstrap cases:

    - `raw_events = store.list(...)`.
    - `events = app_instance.compact_events(raw_events)`.
    - Return `{ "events": events }` (plus `latest_event_id` only in the bootstrap case).

- For the global bootstrap case (no `since_id`, no `session_id`, no `request_id`):
  - Do not call `store.list` at all; simply return an empty `events` list and the `latest_event_id` from `get_latest_event_id`.

6.2 Terminal poll_new_events

- In `TerminalApplication.poll_new_events`:

  - Currently:
    - Calls `store.list(...)`.
    - Updates `_last_event_id` from the last returned event.
    - Returns the raw events.

  - New behavior:
    - `raw_events = store.list(...)`.
    - `events = self._app.compact_events(raw_events)`.
    - If `raw_events` is non-empty:
      - Set `_last_event_id` from the `event_id` of the **last raw event** (not the last compacted event).
    - Return `events` to the terminal UI.

- Rationale:
  - The terminal sees fewer redundant partials after final/tool_results events.
  - `_last_event_id` still advances to the true high-watermark, so no events are accidentally re-fetched or skipped.

6.3 Terminal session switching and compaction together

- After implementing both cursor-based `_last_event_id` initialization and event compaction:

  - On `switch_session`:
    - `_last_event_id` is set to the session's cursor (if available).
    - The next `poll_new_events` call fetches only events after this cursor and compacts them.

  - If there are pending streaming events after the cursor (e.g. a request in progress when the session was last seen), the poll will:
    - Return the partials and finals as they arrive.
    - Once a final or tool_results appears in a subsequent poll, earlier partials in that same batch will be dropped.

---

7. TESTING AND DOCUMENTATION UPDATES

7.1 Tests

- HTTP server tests (e.g. `application/python/tests/test_agent_terminal_app_server.py`):

  1. **Cursor-based default since_id**:
     - Set up a session with some events and a known `cursor_event_id` (via checkpoints).
     - Call `/events?session_id=...` with `since_id` omitted.
     - Assert that the underlying store is queried with `since_id` equal to the cursor and that only newer events are returned.

  2. **Global bootstrap**:
     - Create several events across sessions.
     - Call `/events` with no query parameters.
     - Assert that the response is `{ "events": [], "latest_event_id": <max-id-or-null> }`.

  3. **Partial compaction (assistant)**:
     - For a given session/request, publish a series of `partial` events followed by a `final`.
     - Call `/events` with `since_id` set before the first partial and `session_id` set.
     - Assert that the returned list includes the `final` but omits earlier `partial` events.

  4. **Partial compaction (tools)**:
     - For a given session/request, publish `tool_partial` events followed by `tool_results`.
     - Call `/events` similarly and assert that only `tool_results` (and non-tool events) are returned for that request.

  5. **In-flight requests**:
     - Publish only `partial` and/or `tool_partial` events for a request, with no final/tool_results.
     - Call `/events` and assert that all partials are preserved.

- Terminal tests (e.g. new tests for `TerminalApplication`):

  1. **Session switch uses cursor**:
     - Create a session, produce some events, and ensure a cursor is recorded.
     - Switch away and back using `switch_session`.
     - Assert that `_last_event_id` is set to the session's cursor.
     - Call `poll_new_events` and confirm that only events after the cursor are returned.

  2. **Terminal compaction**:
     - Using the shared event store, generate partial + final sequences for a request.
     - Call `poll_new_events` and assert that:
       - `final` and/or `tool_results` are present.
       - Redundant `partial` and `tool_partial` events before those finals are not returned.
       - `_last_event_id` has advanced to the raw last event.

7.2 Documentation

- Update `docs/api/events.md` to document:
  - Default cursor behavior for `/events` when `session_id` is provided.
  - Global bootstrap response shape when `since_id` and `session_id` are omitted.
  - The recommendation to obtain a snapshot + `cursor_event_id` from `/sessions/{id}/messages` and use that as `since_id`.

- Update `STREAMING_EVENTS_PLAN.md` and `application/python/agent_terminal_app/server_endpoints_parity.md` to:
  - Reflect cursor-aware polling semantics.
  - Describe that polling responses may omit redundant `partial` and `tool_partial` events in favor of the final assistant or tool results.
  - Mention that additional compaction/merging optimizations may also
    be applied within the Elixir bridge when persisting and replaying
    events (Stage 2 of the streaming events plan). These bridge-side
    optimizations would mirror the Python `compact_events` semantics,
    be controlled by flags, and are intended purely as future
    storage/throughput optimizations, not as a change to the core
    correctness model.

---

8. SUMMARY OF INTENDED OUTCOME

After implementing this plan:

- The HTTP server will:
  - Use per-session cursors as the default `since_id` for `/events` when `session_id` is provided but `since_id` is not.
  - Provide a safe bootstrap mechanism for global polling via `latest_event_id` without replaying history.
  - Return event batches that are compacted to remove redundant `partial` and `tool_partial` entries that precede final results in the same batch.

- The terminal application will:
  - Resume event polling from the session cursor when switching sessions, avoiding full history replays.
  - Show fewer redundant streaming events after requests have completed, while still preserving live streaming for in-flight requests.

- The underlying `EventStore` will remain an append-only, unfiltered log, with compaction and cursor semantics implemented at the application layer where they can be shared consistently between HTTP and terminal frontends.
