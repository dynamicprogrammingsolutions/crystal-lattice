# Mobile and Desktop Frontend Implementation Documentation

Document how the current mobile and macOS frontends host portable notification,
action-display, and Sessions-action behavior, including their different native
surface conventions and verification boundaries.

## Requirements checklist

- [ ] Mobile development documentation explains global display ownership,
  connection changes, kept-mounted tabs, inline/modal hosts, follow-up actions,
  Sessions actions, and native Detox coverage.
- [ ] Desktop development documentation explains multi-backend polling, the
  common banner rail, separate React windows, native popovers, coordinators,
  Sessions actions, and connection isolation.
- [x] A desktop window/popover convention page clearly distinguishes anchored
  transient controls, settings windows, modal result windows, global banners,
  and session inline displays.
- [x] Native test documentation explains deterministic harness registration,
  real-backend component integration, Detox/XCUITest boundaries, and manual
  approval/verification.
- [ ] Platform documentation maps to `FNT-*` and `FSA-*` without redefining
  portable frontend behavior.
- [x] Current unverified macOS native/human evidence remains explicitly
  incomplete until performed.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

Depends On:
`tasks/20260730-runtime-notification-specification-documentation/020-portable-frontend-behavior-specifications.md`

## Proposed artifacts

```text
mobile/crystal-lattice-control-rn/docs/development/
└── frontend-hosting.md

desktop/crystal-lattice-control-desktop-rn/docs/development/
├── frontend-hosting.md
├── window-and-popover-conventions.md
└── native-ui-testing.md
```

## Mobile content

- `ConnectedRoot` as the application-global host lifetime.
- one application notification controller per active backend/connection.
- display subscription, stable revision upsert, authoritative dismissal
  mutation, and hydration after restart/reconnect.
- normal-flow placement below the owning screen header/search region.
- behavior across Connection, Sessions, and Messages kept-mounted tabs.
- Sessions and SessionChat inline/modal responsibilities.
- session notification hydration plus live events.
- follow-up URL, clipboard, file, dismiss, and run-action behavior.
- unified Sessions action bar, default pins, connection-scoped persistence,
  Notifications history, Server settings modal, refresh, and new-session agent
  picker.
- compact history, historical inline/modal replay, and waiting-for-input
  navigation.
- production component tests, real-backend component tests, and focused Detox
  z-order/touch harness.

Primary references:

- `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx`
- `src/components/GlobalDisplayLayer.tsx`
- `src/SessionsScreen.tsx`
- `src/SessionChatScreen.tsx`
- `src/testing/MobileNotificationBannerHarness.tsx`
- `e2e/notificationBanner.e2e.test.ts`
- relevant `__tests__` and `__integration__` files.

## Desktop content

- `DesktopRoot` global display ownership.
- subscription/controller per open backend.
- connection-aware banner labels and authoritative dismissal.
- one message/detail-area rail for connection-level displays from every open
  connection plus active-session displays.
- session inline rendering in ChatPane.
- action-display and Server settings coordinators/windows.
- consumed modal removal and system-window closure.
- unified Sessions action bar and platform-local pins.
- connection/session notification history and historical replay.
- native `NSPopover` for anchored transient action menus.
- generic `openReactWindow` for settings; notification/action modal requests
  use inline fallback in the current desktop runtime.

Primary references:

- `desktop/.../src/DesktopRoot.tsx`
- `src/ui/DesktopGlobalDisplayLayer.tsx`
- `src/panels/SessionsPanel.tsx`
- `src/chat/ChatPane.tsx`
- `src/windows/ActionDisplayWindow.tsx`
- `src/windows/ServerSettingsWindow.tsx`
- display/settings coordinator modules;
- desktop Jest integration and Session Filters XCUITest harness.

## Desktop convention matrix

Document this as a development rule:

| Interaction | Current macOS convention |
|---|---|
| Anchored transient control | Native `NSPopover` |
| Server/session settings | Separate React window |
| Notification/action modal request | Inline fallback in message/detail rail |
| Global/persistent banner presentation | Common connection-aware top rail |
| Session inline presentation | Owning Messages/session region |

## Verification boundary

- Unit/component tests verify routing and component behavior.
- Real-backend tests verify public backend/production adapter integration.
- Detox verifies mobile native layout/touch behavior not reliable below the
  native boundary.
- XCUITest verifies macOS popover/window behavior.
- Human verification remains distinct from successful automated native tests.

## Status audit — August 3, 2026

All proposed platform pages exist, and the macOS native and human checkpoints
were completed on August 2, 2026 after remaining separate until execution.

Incomplete work within the approved current-state scope:

- mobile hosting documentation still describes notification modal presentation
  as a screen-local overlay, while the implementation now uses the native
  full-application modal boundary;
- mobile and desktop pages need fuller follow-up, coordinator, and Sessions
  action ownership detail;
- platform pages do not yet provide concise `FNT-*`/`FSA-*` implementation
  mappings.

Explicit scope decision:

- decide whether notification-history and waiting-for-input hosting
  documentation remains in this subtask until Stages F–H exist or moves to
  those implementation stages. Those future surfaces are not undocumented
  current functionality.
