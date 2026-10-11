# Notification and action-display presentation

This page describes desktop ownership and placement for application/session
notifications and direct action displays. Portable notification behavior is
owned by the shared frontend packages and the cross-package notification
specification.

`DesktopRoot` owns one application-notification controller for each open
backend connection.

Connection-level notifications and application/session-list action responses
from open connections render in one normal-flow message/detail-area rail with
connection labels. The active `ChatPane` contributes its session notifications
and session/message action responses at the same visual location.

Desktop notification modal requests use inline fallback. Direct action
responses requesting modal presentation open the generic action-display React
window; inline and banner results retain their existing rails. Lengthy window
content scrolls inside the action card. The Sessions header uses the shared
pinnable action model.

Closing a direct action result removes that presentation without retaining a
dismissed revision. Invoking the action again opens its result even when its
`display_id` and body are unchanged, as with the duration report. Both the card's
Close button and the native window close use this behavior. Server notification
dismissal retains its separate revision and backend authority rules.
The global display owner subscribes to the native action-window close event,
so dismissal follows the same path in the main app and focused native harness.

See the shared React Native
[notification components](../../../../packages/frontend-rn-components/docs/development/notification-components.md),
the frontend SDK
[notification implementation](../../../../packages/frontend-sdk/docs/development/notification-implementation.md),
and the cross-package
[notification frontend behavior](../../../../docs/development/specifications/notifications/frontend-behavior.md)
for portable contracts.

Maintainer entry points:

- `src/DesktopRoot.tsx`
- `src/ui/DesktopGlobalDisplayLayer.tsx`
- `src/windows/ActionDisplayWindow.tsx`
- `src/windows/actionDisplayWindowCoordinator.ts`
- `src/panels/SessionsPanel.tsx`
- `src/chat/ChatPane.tsx`
- `src/chat/ChatPanePlaceholder.tsx`
