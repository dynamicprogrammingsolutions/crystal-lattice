# Home, Watchlist, notes, and request-status hosting

`ConnectedRoot` hosts four mounted destinations: Home, Connections, Sessions,
and Messages. Home is selected after hydration. It consumes cached summaries
without constructing transports and delegates connection opening plus
session/navigation selection through one host command guarded by current user
intent.

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

`deriveHomeSessionCollections()` preserves stored Watchlist order and derives a
separate modified-descending Recent Sessions timeline. The timeline applies
the exact `24h`, `3d`, or `1w` cutoff and excludes watched composite identities.

## Presentation

`HomeScreen` is not a variant of `SessionsScreen`:

- Watchlist uses exactly two columns of workspace tiles;
- each tile has a dedicated PanResponder drag handle and accessible
  Move Earlier/Move Later actions;
- Recent Sessions uses a vertical activity timeline;
- bookmark language belongs only to the local Watchlist;
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
uses independent cancellable timers, stops in the background, and applies
bounded per-connection backoff. Unsupported readers are not repeatedly
probed. Loss of authority removes stale Running state.

## Verification

Primary tests:

- `core/python/tests/test_session_request_status.py`
- `application/python/tests/test_session_request_status_http.py`
- `packages/frontend-sdk/src/types/sessionRequestStatus.test.ts`
- mobile Home workspace, reader, polling, Home, Sessions-note, and
  `ConnectedRoot` component tests
- `src/testing/MobileHomeHarness.tsx`
- `e2e/home.e2e.test.ts`