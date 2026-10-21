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

Within Chat, the combined connection/session rail scrolls within a bounded
height so notifications cannot consume the transcript. Short panes cap the
rail at 12% of the pane height; taller panes cap it at 180 points. Notification
content, follow-up actions, and dismissal retain their existing ownership.

See the shared React Native
[notification components](../../../../packages/frontend-rn-components/docs/development/notification-components.md),
the frontend SDK
[notification implementation](../../../../packages/frontend-sdk/docs/development/notification-implementation.md),
and the cross-package
[notification frontend behavior](../../../../docs/development/specifications/notifications/frontend-behavior.md)
for portable contracts.

An unconfirmed ordinary send uses the compact Chat status row above the
transcript, with **Resend** and **Cancel**, instead of a blocking alert.
Resend submits the original payload with its original idempotency key, including
attachments. It clears the ordinary draft only when that draft still matches
the retried payload. Cancel dismisses local recovery and retains the draft;
it does not claim to cancel server work. Known active requests continue to use
the existing request cancellation controls.

This transient recovery state is connection/session-scoped. It shares the
request/action progress slot and does not replace server-owned notification
rails or their dismissal protocol. Long transport errors do not expand the
main message area because the row presents a short, bounded summary.

Maintainer entry points:

- `src/DesktopRoot.tsx`
- `src/ui/DesktopGlobalDisplayLayer.tsx`
- `src/windows/ActionDisplayWindow.tsx`
- `src/windows/actionDisplayWindowCoordinator.ts`
- `src/panels/SessionsPanel.tsx`
- `src/chat/ChatPane.tsx`
- `src/chat/ChatPanePlaceholder.tsx`
