# Notification presentation

This page describes mobile ownership, placement, dismissal integration, and
verification for application and session notifications. Portable notification
state and component behavior are documented by the cross-package
specification and shared frontend packages.

`ConnectedRoot` owns connection-lifetime application notification state and
display subscriptions.

Current placement:

- Sessions renders connection/application banners below search and filters.
- Session Chat renders exact-session notifications below its header.
- Connections does not present notifications.
- Banners participate in normal layout.
- Mobile modal notifications render through the owning screen's overlay
  boundary.
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

Unconfirmed Chat sends use the compact top activity row, offering **Resend**
and **Cancel**. This replaces the large panel formerly between the transcript
and composer and avoids a blocking ordinary-send error alert. Resend retains
the original payload and idempotency key; subsequent draft changes do not alter
that retry. The draft is cleared after acknowledgement only if it still matches
the retried payload.

Cancel dismisses local recovery while preserving the unsent draft. It does not
claim to cancel a request accepted by the server. Known active work retains the
normal hard/soft cancellation controls. Recovery is not discarded solely
because an unrelated current request is observed. The bounded row participates
in normal layout and leaves transcript gestures available.

See the shared React Native
[notification components](../../../../packages/frontend-rn-components/docs/development/notification-components.md),
the frontend SDK
[notification implementation](../../../../packages/frontend-sdk/docs/development/notification-implementation.md),
and the cross-package
[notification frontend behavior](../../../../docs/development/specifications/notifications/frontend-behavior.md)
for portable contracts.

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
tests and the mobile manual checkpoint; no failure-injection Detox harness is
needed because presentation geometry is unchanged by synchronization failure.
