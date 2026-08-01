# Mobile frontend hosting

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
- Application and session Dismiss controls persist through the backend and
  update the initiating mobile frontend from the successful response.
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
real Python HTTP backend because they are not native-only behaviors.