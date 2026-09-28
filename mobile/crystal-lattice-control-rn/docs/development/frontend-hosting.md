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

## Rich composer controls

Session Chat renders model and reasoning settings as compact dropdowns and web
search as a compact Boolean toggle. The shared pinned-action bar is explicitly
configured for two rows with the leftover row below. Compact setting controls
come first; Append and Resend occupy the lower right-aligned action row.
Composer actions contain Resend, Append, and Append as. Request Cancel is not
duplicated there.

The message input has a fixed side stack with request Cancel above Send. Each
control is 44 points square; the inline input has a 94-point minimum height.
Cancel remains visible and disabled when no request is active. Send uses the
paper-plane `send` icon and Resend uses `repeat`. The Send icon becomes a
spinner during both request submission and the full active-request lifetime;
the maximized composer uses the same state.

An active request disables duplicate Send/Resend starts and enables Cancel,
but does not globally disable model/reasoning/web settings, plugin actions,
attachments, Append, or reload. Append has separate local in-flight state, and
attachment operations retain their own pick/upload guards. Eligible concurrent
operations use the normal backend path and rely on the server to accept or
reject them.

The top Session actions also expose Resend and request Cancel. These entries
reuse the same handlers and request-state eligibility as the composer Resend
and permanent Cancel controls.

The in-frame `maximize-2` control opens a full-screen editor backed by the same
draft, attachments, validation, persistence, and send path. `minimize-2`
collapses without discarding edits. The large native text surface is intended
to support iOS three-finger editing gestures; that operating-system gesture
requires human simulator/device verification.

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

## Rich session settings and actions

`SessionChatScreen` consumes normalized rich config controls and session
actions from the shared frontend SDK.

- Config controls at `composer` use the same effective value and
  `SessionSettingsController` mutations as the full Session Settings modal.
- Rich dropdowns support discovered options, explicit custom string values,
  and reset.
- Session actions default to the header and may opt into the composer through
  `rich_ui.placements`.
- Rich toggle/list controls invoke the ordinary action and keep its dialog as
  fallback.
- Program-provided session actions remain above plugin-contributed actions in
  the complete menu; each group retains its own declared order.
- Connection-scoped pin preferences preserve explicit user choices; plugin
  `default_pinned` values apply only before a preference is stored.

The deterministic production-screen harness is
`src/testing/MobileRichSessionUiHarness.tsx`. Component coverage is in
`__tests__/RichSessionUi.test.tsx`; simulator coverage is in
`e2e/richSessionUi.e2e.test.ts`.