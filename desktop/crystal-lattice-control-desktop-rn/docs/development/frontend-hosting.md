# Desktop frontend hosting

`DesktopRoot` owns one application-notification controller for each open
backend connection.

It also owns one explicit-ID request-status polling consumer for Home, History,
Sessions, tabs, and the active Chat pane. Status reads reuse open backends or
use supported stateless closed-connection HTTP reads; polling never opens or
focuses a connection.

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
- `src/home/DesktopHomeWorkspaceContext.tsx`
- `src/tabs/desktopWorkspaceState.ts`
- `src/status/DesktopConnectionSessionStatusReader.ts`

## Rich session settings and actions

`ChatPane` renders normalized config-rich dropdowns and rich session actions
at their declared `session_header` or `composer` placement. Config changes use
the ordinary session-settings controller. Rich action controls use the
ordinary action runner.

Compact dropdowns and rich lists open through the native popover coordinator.
The full Session Settings window renders fixed-option dropdowns with
`MacSelect`. Custom-capable dropdowns use the native `MacComboBox`, while
portable filtering, regex validation, and synthetic custom options remain in
the frontend SDK. The composer enables the shared two-row pinned-action layout
with its second row below.

The Send button shows an activity indicator during request submission and
while an active request remains. Active request state gates duplicate
Send/Resend starts and enables Cancel, but does not disable rich settings,
plugin actions, attachment drafting, or Append. Append and attachment work use
their own local in-flight guards, while the server remains authoritative for
accepting concurrent mutations.

Maintainer entry points:

- `src/chat/ChatPane.tsx`
- `src/windows/SessionSettingsWindow.tsx`
- `src/native/MacSelect.tsx`
- `src/native/MacComboBox.tsx`
- `src/windows/desktopPopoverCoordinator.ts`