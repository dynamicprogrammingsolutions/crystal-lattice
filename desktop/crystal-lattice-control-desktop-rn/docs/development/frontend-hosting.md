# Desktop frontend hosting

`DesktopRoot` owns one application-notification controller for each open
backend connection.

Connection-level notifications and application/session-list action responses
from open connections render in one normal-flow message/detail-area rail with
connection labels. The active ChatPane contributes its session notifications
and session/message action responses at the same visual location.

Desktop notification modal requests use inline fallback. Direct action
responses requesting modal presentation open the generic action-display React
window; inline and banner results retain their existing rails. Lengthy window
content scrolls inside the action card. The Sessions header uses the shared
pinnable action model.

Maintainer entry points:

- `src/DesktopRoot.tsx`
- `src/ui/DesktopGlobalDisplayLayer.tsx`
- `src/windows/ActionDisplayWindow.tsx`
- `src/windows/actionDisplayWindowCoordinator.ts`
- `src/panels/SessionsPanel.tsx`
- `src/chat/ChatPane.tsx`
- `src/chat/ChatPanePlaceholder.tsx`