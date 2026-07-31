# Portable Frontend Notification and Sessions-Action Specifications

Specify frontend behavior independently of TypeScript, React, React Native,
mobile, desktop, web, or any other implementation language.

## Requirements checklist

- [ ] A root frontend notification-presentation specification is sufficient to
  implement compliant notification and action-display behavior in a new
  frontend.
- [ ] A root frontend Sessions-actions specification defines the reusable
  action surface, built-ins, plugin actions, pinning, settings/new-session
  behavior, result routing, and accessibility.
- [ ] Stable `FNT-*` and `FSA-*` requirements contain portable acceptance
  examples and evidence links.
- [ ] The specifications distinguish normative frontend behavior from current
  SDK, React Native component, mobile, and desktop implementation choices.
- [ ] Reusable frontend capabilities are specified conceptually without
  requiring current component/class names.
- [ ] Cross-package notification and action-display shapes are referenced
  rather than duplicated.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

Depends On:
`tasks/20260730-runtime-notification-specification-documentation/010-notification-and-action-display-contracts.md`

## Approved artifacts

```text
docs/development/specifications/
├── notifications/
│   └── frontend-behavior.md
└── sessions-actions/
    ├── index.md
    ├── technical-spec.md
    └── requirements.md
```

## Notification-presentation content

Define:

- frontend inputs: persisted session metadata, application events, session
  events, and direct action responses;
- stable-ID upsert and updated-display replacement;
- session metadata authority after reconnect;
- local dismissal versus backend resolution;
- backend/connection isolation;
- route matrix:

| Presentation | Portable placement |
|---|---|
| `banner` | Connection-aware global banner rail |
| application `inline` | Application/global shell region |
| session `inline` | Owning session/Messages region |
| action-response `inline` | Initiating surface |
| `modal` | Platform-appropriate modal result surface |

- explicit presentation precedence and contract defaults;
- persistence across navigation within a connection;
- multi-connection labeling;
- maximum visible banners per connection;
- semantic info/success/warning/error treatments;
- title/body/context/action hierarchy;
- accessible alert and action semantics;
- follow-up actions, including a modal result that returns a banner;
- handling notification updates after local dismissal;
- reconnect examples for persistent session versus owner-memory application
  state.

Specify conceptual reusable capabilities:

- notification state/controller;
- event merger/selectors;
- display router;
- semantic banner;
- connection-aware banner rail;
- session notification host;
- inline display renderer;
- modal display host;
- follow-up action runner.

Do not name `ApplicationNotificationsController`, `DisplayEnvelope`,
`NotificationBannerHost`, React contexts, hooks, or platform window classes in
normative requirements. Package documentation may map those names later.

## Sessions-actions content

Define:

- one reusable Sessions action surface containing Server settings, Refresh
  sessions, New session, and plugin-contributed application actions;
- distinction between Refresh sessions and Reload application;
- stable action identity;
- complete-menu and pinned representations invoking the same action;
- frontend-local, connection-scoped pin persistence;
- plugin dialog and parameter handling;
- result routing through the action-display contract;
- agent selection for new sessions when needed;
- platform-appropriate anchored menu behavior;
- platform-standard Server settings surface;
- action disabling/loading semantics;
- accessible labels and stable test selectors.

## Portable acceptance examples

Include examples such as:

- a reload banner remains visible after moving from Sessions to Messages;
- application and session banners share visual semantics and one rail;
- a session inline notification appears only in its owning session;
- two server connections have independently dismissible labeled banners;
- a notification update replaces the pending version;
- local dismissal leaves persisted metadata unchanged;
- an explicit banner response is not coerced because it originated from a
  session-list or message action;
- built-in and plugin actions can both be pinned and remain connection-scoped.

## Current implementation references

Use these for evidence, not as the specification source:

- `packages/frontend-sdk/src/notifications/`
- `packages/frontend-sdk/src/plugins/displayPresentation.ts`
- `packages/frontend-rn-components/src/notifications/`
- `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx`
- mobile `ConnectedRoot.tsx`, `SessionsScreen.tsx`, and
  `SessionChatScreen.tsx`
- desktop `DesktopRoot.tsx`, `SessionsPanel.tsx`, `ChatPane.tsx`, and global
  display/window coordinators.
