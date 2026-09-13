# Home, Watchlist, notes, and request-status hosting

`ConnectedRoot` hosts four mounted destinations: Home, Connections, Sessions,
and Messages. Home is selected after hydration. It consumes cached summaries
without constructing transports and delegates connection opening plus
session/navigation selection through one host command guarded by current user
intent.

Portable Watchlist/recent selectors, note normalization, request-status
presentation, and measured reorder helpers are owned by
`@crystal-lattice/frontend-rn-components`. The mobile application continues to
own AsyncStorage keys, touch responders, full-screen composition, connection
opening, and navigation.

## Local ownership

`HomeWorkspaceProvider` owns three versioned AsyncStorage records:

- `clc_home_watchlist_v1`: ordered composite
  `(connectionId, sessionId)` identities;
- `clc_session_notes_v1`: permanent note text keyed by session ID alone;
- `clc_mobile_global_preferences_v1`: the semantic Recent Sessions window.

Hydration completes before any of these stores write. Watchlist entries never
copy session summaries. Home resolves them against `sessionsCache`; unresolved
entries remain persisted but are not rendered.

Notes deliberately share across connections when session IDs match. Removing
a Watchlist entry or saved connection leaves notes intact. Only the explicit
Remove Note action deletes note text.

Sessions and Messages add shared static local action definitions to their
existing pinnable Session actions. `localWatchlist` resolves against
`HomeWorkspaceProvider` and changes only composite local membership. Its label
and icon update between Add and Remove without requiring an open backend.
Server session-pin actions remain separate plugin-owned commands.
The local actions stay disabled until Home storage hydration completes.
Pinned-action hydration also preserves an explicit user change made while an
older storage read is in flight; plugin-declared defaults are merged only
after the scoped record has loaded.

`deriveHomeSessionCollections()` preserves stored Watchlist order and derives a
separate modified-descending Recent Sessions timeline. The timeline applies
the exact `24h`, `3d`, or `1w` cutoff. Watchlist membership does not filter the
timeline because the sections answer different questions: the Watchlist is
manually curated and ordered, while Recent Sessions is complete for the
selected time window.

## Presentation

`HomeScreen` is not a variant of `SessionsScreen`:

- Watchlist uses exactly two columns of workspace tiles;
- each tile has a dedicated PanResponder drag handle and accessible
  Move Earlier/Move Later actions;
- the grid owns transient drag state, snapshots measured variable-height
  slots, renders an elevated tile plus same-size target placeholder, and
  persists only the settled move;
- release installs a keyed optimistic order until the Home workspace context
  acknowledges the same stored order, preventing the pre-move arrangement
  from rendering between local drag cleanup and context propagation;
- the responder overlay enters a non-animated settling phase at release: its
  translation snaps to the measured placeholder frame, the preview remains
  mounted, and the translation resets only after acknowledged final tiles
  replace the overlay;
- handle capture disables user scrolling only for the active drag, while
  bounded edge scrolling keeps off-screen Watchlist targets reachable;
- Recent Sessions uses a vertical activity timeline;
- Recent uses the bookmark for adding local Watchlist membership, while a
  Watchlist tile uses `x` to remove that membership;
- server session pins continue to use their existing rich application action.

Tiles bound note previews to two lines and consume semantic typography. Native
selectors include connection and session identity.

## Derived request status

`SessionRequestStatusService` lives in `agent_app`. Its explicit-ID query:

1. reads the active coordinated request ID;
2. otherwise loads the requested session record;
3. caches tail classification by the store's opaque revision;
4. emits only `idle`, `not_started`, `running`, `succeeded`, or
   `interrupted`.

FastAPI adapts the service at `POST /sessions/request-statuses`. The response
declares `authority: derived_transient`; it is not request history.

The frontend SDK exposes an optional backend method and normalized projection.
`MobileConnectionSessionStatusReader` uses:

- the active backend when available;
- one direct HTTP request for closed manual/discovery records;
- one authenticated HTTP-proxy request for modern bridge records, even when
  normal bridge traffic uses WebSocket;
- unsupported state for legacy WebSocket-only and closed cloud records that
  cannot guarantee a no-wake read.

`useSessionRequestStatuses` unions exact consumer IDs, groups by connection,
splits large groups into bounded requests, uses independent cancellable
timers, stops in the background, and applies bounded per-connection backoff.
Successful batches reconcile only their queried IDs. Transient unavailability
retains a recently observed Running result through retry, while authoritative
replacement or bounded loss of authority removes stale Running state.

## Verification

Primary tests:

- `src/__tests__/watchlistDrag.test.ts`
- `core/python/tests/test_session_request_status.py`
- `application/python/tests/test_session_request_status_http.py`
- `packages/frontend-sdk/src/types/sessionRequestStatus.test.ts`
- mobile Home workspace, reader, polling, Home, Sessions-note, and
  `ConnectedRoot` component tests
- `src/testing/MobileHomeHarness.tsx`
- `e2e/home.e2e.test.ts`
