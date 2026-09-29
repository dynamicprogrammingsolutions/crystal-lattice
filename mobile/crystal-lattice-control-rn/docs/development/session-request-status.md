# Session request status

This page describes the cross-layer status source and the mobile reader and
polling integration used by Home, Sessions, and Messages. The frontend SDK and
frontend SDK React package own the portable wire projection and polling hook;
the shared React Native package owns presentation contracts.

## Derived status source

`SessionRequestStatusService` lives in `agent_app`. Its explicit-ID query:

1. reads the active coordinated request ID;
2. otherwise loads the requested session record;
3. caches tail classification by the store's opaque revision;
4. emits only `idle`, `not_started`, `running`, `succeeded`, or
   `interrupted`.

FastAPI adapts the service at `POST /sessions/request-statuses`. The response
declares `authority: derived_transient`; it is not request history.

The frontend SDK exposes an optional backend method and normalized projection.
See its
[session request-status implementation](../../../../packages/frontend-sdk/docs/development/session-request-status-implementation.md)
for the wire and transport boundary. The host-neutral polling hook is exported
by `@crystal-lattice/frontend-sdk-react`.

## Mobile reading and polling

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

The shared React Native
[Home and status contracts](../../../../packages/frontend-rn-components/docs/development/home-workspace-and-status.md)
own labels, tones, and portable indicator presentation.

## Verification

Primary coverage includes:

- `core/python/tests/test_session_request_status.py`
- `application/python/tests/test_session_request_status_http.py`
- `packages/frontend-sdk/src/types/sessionRequestStatus.test.ts`
- mobile status reader and polling tests
- Home, Sessions, and `ConnectedRoot` component tests
- `src/testing/MobileHomeHarness.tsx`
- `e2e/home.e2e.test.ts`
