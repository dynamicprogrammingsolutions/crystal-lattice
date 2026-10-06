# Session Chat controls and actions

Action names in native action popovers may wrap to two lines. Popup width
accounts for label text, icons, state values, and pin controls; rendered row
height drives popup height, with scrolling for long menus. The OpenAI
message-compaction action is displayed as **OpenAI compaction up to here**;
its plugin/action IDs and inclusive message boundary remain unchanged.

This page describes desktop-specific placement and native presentation of rich
session controls and actions in `ChatPane`, including request-action
eligibility. Shared normalized control and action-menu behavior remains owned
by the frontend SDK and shared React Native package.

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

See the shared React Native
[actions menu components](../../../../packages/frontend-rn-components/docs/development/actions-menu-components.md)
and frontend SDK
[rich session UI implementation](../../../../packages/frontend-sdk/docs/development/rich-session-ui.md)
for portable behavior.

Maintainer entry points:

- `src/chat/ChatPane.tsx`
- `src/windows/SessionSettingsWindow.tsx`
- `src/native/MacSelect.tsx`
- `src/native/MacComboBox.tsx`
- `src/windows/desktopPopoverCoordinator.ts`
