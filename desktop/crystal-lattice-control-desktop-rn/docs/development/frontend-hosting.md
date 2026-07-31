# Desktop frontend hosting

`DesktopRoot` owns one application-notification controller for each open
backend connection.

Connection-level notifications and application/session-list action responses
from open connections render in one normal-flow message/detail-area rail with
connection labels. The active ChatPane contributes its session notifications
and session/message action responses at the same visual location.

Desktop notification and action-response modal requests currently use inline
fallback. The Sessions header uses the shared pinnable action model.

Maintainer entry points:

- `src/DesktopRoot.tsx`
- `src/ui/DesktopGlobalDisplayLayer.tsx`
- `src/panels/SessionsPanel.tsx`
- `src/chat/ChatPane.tsx`
- `src/chat/ChatPanePlaceholder.tsx`