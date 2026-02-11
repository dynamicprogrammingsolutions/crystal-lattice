# Subtask: Plugin-backed actions in chat (session + message)

Expose plugin-provided actions inside the desktop chat pane:

- Session-level plugin actions (in the chat header)
- Message-level plugin actions (in the message actions menu)

Use the same underlying SDK contract as mobile and the same desktop macOS window/popover plumbing already used in the sessions pane.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/084-desktop-rich-assistant-rendering.md`

## Status

- [x] Investigation complete; plan ready (2026-02-11)
- [x] Implementation complete (2026-02-11)
- [ ] Manual UI verification complete

## Investigation Notes (current state)

- Desktop sessions list already supports plugin actions + dialog UI:
  - Provider wrapper: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:83`
  - Action wiring (`usePluginActionDialog` + `runApplicationAction`): `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:250`
  - Dialog surfaces:
    - macOS window/popover via coordinator + `DesktopWindowManager`: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:333`
    - non-macOS fallback modal `<ApplicationActionDialog />`: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:816`
- Desktop chat already has:
  - Header `ActionsMenuBar` for built-in session actions: `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:988`
  - Message actions UI with support for `extraActions` (but not yet wired):
    - `desktop/crystal-lattice-control-desktop-rn/src/chat/MessageActionsBar.tsx:1`
    - `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx:1`
- Chat tabs are mounted without `ApplicationPluginsProvider`, so `useApplicationPlugins()` is currently unavailable in chat:
  - `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:47`
- macOS dialog presentation uses a singleton coordinator (`applicationActionDialogCoordinator`). Reusing it from both
  sessions pane + chat pane requires scoped/owner-aware coordination to avoid one pane accidentally clearing the
  other pane’s active dialog.

## Context to read first (files + line numbers)

- Plugins registry provider + hooks: `packages/frontend-sdk-react/src/applicationPlugins.tsx:1`
- SDK action runner + effects contract: `packages/frontend-sdk/src/plugins/actionRunner.ts:12`
- Sessions pane (reference implementation):
  - Plugin actions wiring: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:250`
  - macOS dialog window/popover integration: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:333`
  - non-macOS `<ApplicationActionDialog />` rendering: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:816`
- Chat pane (target):
  - Header actions bar: `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:988`
  - Message actions handler: `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:886`
- Tab mounting (where to add provider wrapper): `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:47`
- Tab navigation entrypoint (needed for `navigateToSession`): `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:131`
- macOS dialog singleton state: `desktop/crystal-lattice-control-desktop-rn/src/windows/applicationActionDialogCoordinator.ts:1`
- macOS dialog UI host (renders the same dialog layout): `desktop/crystal-lattice-control-desktop-rn/src/windows/ApplicationActionDialogWindow.tsx:1`

## Requirements

- For an online tab, chat pane can list plugin actions.
- Running an action shows the action dialog UI and executes the action.
- Action “effects” are respected:
  - `navigateToSession` opens/focuses a tab
  - `reloadSession` reloads the active chat controller
  - `reloadSessionsList` publishes `desktopEventBus.sessionsReloadRequested`

## Deliverables

Goal: make chat plugin actions behave identically to SessionsPanel session-list actions:

- Same action discovery: `useApplicationPlugins()` (`sessionActions`, `messageActions`, `actionsById`).
- Same action execution: `runApplicationAction(...)`.
- Same dialog rendering:
  - non-macOS: `<ApplicationActionDialog />`
  - macOS: `DesktopWindowManager` window/popover + `applicationActionDialogCoordinator` + `ApplicationActionDialogWindow`.

### 1) Ensure each chat tab is inside `ApplicationPluginsProvider`

- Update `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx`:
  - Wrap the `ChatPane` subtree per tab frame:
    - `<ApplicationPluginsProvider backend={backend} connectionId={connectionId}>...`.
  - This matches the SessionsPanel provider pattern and guarantees plugin actions are scoped per connection.

### 2) Plumb tab navigation so action effects can open/focus sessions

- Add a callback prop so ChatPane can respond to `navigateToSession` effects.
- Update call chain:
  - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx`:
    - Pass `openTab` into `ChatPaneTabStack` as `onOpenSessionTab`.
  - `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx`:
    - Add `onOpenSessionTab` prop and forward into each `ChatPane`.
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`:
    - Add `onOpenSessionTab` prop and use it when handling effects.

### 3) Session-level plugin actions (chat header)

- In `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`:
  - Call `useApplicationPlugins()` and derive `pluginSessionActionDefs: ActionDefinition[]` from `sessionActions`.
  - Append plugin actions in the existing header `ActionsMenuBar` using `extraActions={pluginSessionActionDefs}`.
  - Extend `handleSessionAction`:
    - Keep built-in actions as the base behavior.
    - If the key matches a plugin session action element id, call `openPluginDialogForElement(...)`.

### 4) Message-level plugin actions (message actions menu)

- In `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`:
  - Derive `pluginMessageActionDefs` from `messageActions` (same mapping as mobile).
  - Pass `pluginActionDefs={pluginMessageActionDefs}` into `DesktopMessageBubble` so the existing
    `MessageActionsBar` receives them as `extraActions`.
  - Extend `handleMessageAction`:
    - Keep built-in message actions as the base behavior.
    - If the key matches a plugin message action element id, call `openPluginDialogForElement(...)` with
      `{ kind: 'message', index, message, sessionSummary }` context.

### 5) Run actions + apply effects

- Use `usePluginActionDialog` + `runApplicationAction` in `ChatPane` (mirror SessionsPanel + mobile semantics).
- Context mapping:
  - Session action: `context: { sessionId, sessionSummary, dialogValues }`
  - Message action: `context: { sessionId, sessionSummary, messageContext: { index, message }, dialogValues }`
- Effects handling (required):
  - `navigateToSession`: call `onOpenSessionTab({ connectionId, sessionId: effect.sessionId, title: effect.sessionId })`.
  - `reloadSession`: call the existing `handleReload()` for the active tab (reloads chat controller).
  - `reloadSessionsList`: `desktopEventBus.publish('sessionsReloadRequested', { connectionId, reason: ... })`.

### 6) Dialog UI + macOS surface integration (reuse SessionsPanel rendering)

- non-macOS:
  - Render `<ApplicationActionDialog />` in `ChatPane` the same way SessionsPanel does.
  - Prefill context:
    - Session action: `{ session: sessionSummary }`
    - Message action: `{ session: sessionSummary, message: { index, ...message } }`

- macOS:
  - Reuse the existing dialog window/popover rendering stack:
    - `applicationActionDialogCoordinator` + `ApplicationActionDialogWindow` + `DesktopWindowManager`.
  - Minimal “advanced coordination” required (singleton safety):
    - Extract a small desktop-only helper (hook/module) used by *both* SessionsPanel and ChatPane so the singleton
      dialog state is owner-scoped.
    - The helper will:
      - Generate a scoped dialog id (e.g. `sessions:<id>` vs `chat:<id>`).
      - Only clear/close the active dialog if the active coordinator id matches the scoped id.
      - Centralize the popover/window open + sizing logic currently embedded in SessionsPanel.
      - Subscribe to the native cancel event (`applicationActionDialogCancelled`) and route cancel to the currently
        active dialog handlers.
  - UX stays identical; this is strictly to prevent cross-talk/leaks once multiple panes can open dialogs.

### 7) SessionSummary availability (best-effort)

- Mobile passes a full `SessionSummary` into plugin action context; desktop chat currently has only `sessionId`.
- Plan:
  - Thread an optional `sessionSummary` into `ChatPane` by looking up the session in `DesktopRoot`’s sessions cache
    (best effort; can be `null` when unavailable/offline).
  - Fall back to `sessionId`-only context when summary is missing.

## Verification

- Open an online session tab; confirm plugin session actions appear in chat header.
- Run a plugin session action that mutates sessions; confirm SessionsPanel refreshes via
  `desktopEventBus.sessionsReloadRequested`.
- Run a plugin message action; confirm dialog opens with prefilled message context.
- Confirm `navigateToSession` opens/focuses the target tab.
- Confirm `reloadSession` reloads the active tab’s chat controller.
- On macOS, confirm the window/popover closes on cancel/submit and doesn’t leak state between SessionsPanel and ChatPane.

---

## Completion Notes (added 2026-02-11)

- Wrapped each chat tab with `ApplicationPluginsProvider` so chat can consume plugin registry state:
  - `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:1`
- Added best-effort `sessionSummary` plumbing into `ChatPane` via `sessionsCache` lookup:
  - `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:1`
  - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:678`
- Added session-level plugin actions to the chat header actions menu (`extraActions`) and message-level plugin actions
  to the message actions menu (`extraActions`):
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:1`
- Implemented chat plugin action execution with `usePluginActionDialog` + `runApplicationAction`, including effect
  handling for `navigateToSession`, `reloadSession`, and `reloadSessionsList`:
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:1`
- Extracted and reused macOS application-action dialog window/popover coordination to avoid cross-talk between the
  Sessions panel and Chat pane:
  - New helper: `desktop/crystal-lattice-control-desktop-rn/src/windows/useMacOSApplicationActionDialog.ts:1`
  - Refactor Sessions panel to use helper: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:1`
