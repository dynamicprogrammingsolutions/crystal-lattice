# Mobile frontend hosting

## Bridge connection hosting

`App.tsx` owns bridge connection selection, pairing, saved connection
reconstruction, foreground recovery, and repair.

Bridge transports are created only through the frontend SDK's
`createBridgeConnectionTransport()` factory. The mobile host supports:

| Selection | Mobile behavior |
| --- | --- |
| WebSocket | Compatibility default for discovery, pairing, events, and requests. |
| HTTP | Discovery, pairing, events, and requests through bridge HTTP v1; no frontend WebSocket. |
| Hybrid | HTTP discovery/pairing/normal requests and legacy WebSocket only for exact `GET /events`. |

HTTP and hybrid are labeled experimental. There is no automatic fallback.
Rollback means selecting WebSocket and constructing another transport.

Successful pairing stores a `BridgeConnectionRecord` with bridge URL, server
ID/name, pairing token, and the selected `transportMode`. The field is optional
for backward compatibility. All reconstruction sites resolve a missing mode to
the shared WebSocket default, so old records are not silently migrated.

Reopening a saved record supplies its server ID and pairing token to the mode
factory. Invalid token or server mismatch clears the stale token and opens the
repair flow. A temporarily absent server keeps the record available for
re-pairing when it returns.

Foreground recovery uses the structural `BridgeConnectionTransport` lifecycle:

1. call `prepareForResume()`;
2. reconnect/validate;
3. persist a changed pairing token if one is returned;
4. open repair when the server or credential is no longer valid.

`src/connectionInfo.ts` renders the effective mode in saved-connection details.
Stable production test IDs on the bridge method and mode selectors support the
focused iOS/Android Detox scenario.

Current evidence covers default selection plus explicit HTTP, hybrid, and
WebSocket rollback on both simulators. A shared helper used by `App.tsx` has
focused tests for absent, WebSocket, HTTP, and hybrid saved records while
preserving the same server identity and pairing token. Physical-device network
checks remain a gate before a separately approved default switch.

The cross-package
[bridge-connectivity frontend specification](../../../../docs/development/specifications/bridge-connectivity/frontend-behavior.md)
owns portable mode and migration behavior.

## Notification hosting

`ConnectedRoot` owns connection-lifetime application notification state and
display subscriptions.

Current placement:

- Sessions renders connection/application banners below search and filters.
- Session Chat renders exact-session notifications below its header.
- Connection does not host notification presentation.
- Banners participate in normal layout.
- Mobile modal notifications render through the owning screen's overlay host.
- Application notifications hydrate from the authoritative owner snapshot
  before event polling.
- Application and session Dismiss controls first persist an exact-revision
  AsyncStorage cache entry and hide immediately, then send the backend
  mutation.
- Failed synchronization keeps that revision hidden without a blocking error
  and retries when the same revision is observed after reconnect/rehydration.
- A newer pending revision removes the obsolete cache entry and is presented;
  the expected revision is never rewritten automatically.
- Another already-open frontend is not forced to remove a remotely dismissed
  notification; reconnect or authoritative refresh converges state.
- Direct action-response displays remain transient and close locally.

The Sessions header uses the shared pinnable action bar for Server settings,
Refresh, New session, and plugin actions.

Maintainer entry points:

- `src/ConnectedRoot.tsx`
- `src/components/GlobalDisplayLayer.tsx`
- `src/SessionsScreen.tsx`
- `src/SessionChatScreen.tsx`
- `src/testing/MobileNotificationBannerHarness.tsx`
- `e2e/notificationBanner.e2e.test.ts`

Focused Detox coverage verifies geometry, z-order, touch behavior, and
wrong-surface absence through production screens. Server persistence and
rehydration are verified through production component integration against the
real Python HTTP backend. AsyncStorage reconstruction is covered by component
tests and the mobile manual checkpoint; B-2 does not add a failure-injection
Detox harness because presentation geometry is unchanged.