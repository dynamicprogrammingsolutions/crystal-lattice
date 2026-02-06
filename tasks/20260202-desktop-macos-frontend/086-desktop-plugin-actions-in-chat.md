# Subtask: Plugin-backed actions in chat (session + message)

Expose plugin-provided actions inside the desktop chat pane:

- Session-level plugin actions (in the chat header)
- Message-level plugin actions (in the message actions menu)

Use the same underlying SDK contract as mobile and the same desktop macOS window/popover plumbing already used in the sessions pane.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/085-desktop-message-actions-and-sharing.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Plugins registry provider + hooks (read 1–80): `packages/frontend-sdk-react/src/applicationPlugins.tsx:1`
- SDK action runner + effects contract (read 17–120): `packages/frontend-sdk/src/plugins/actionRunner.ts:17`
- Desktop sessions pane plugin action wiring (reference; read 237–299): `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:237`
- Desktop macOS application action dialog coordinator (reference; read 320–387): `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:320`

## Requirements

- For an online tab, chat pane can list plugin actions.
- Running an action shows the action dialog UI and executes the action.
- Action “effects” are respected:
  - `navigateToSession` opens/focuses a tab
  - `reloadSession` reloads the active chat controller
  - `reloadSessionsList` publishes `desktopEventBus.sessionsReloadRequested`

## Deliverables

### 1) Ensure chat pane is inside an `ApplicationPluginsProvider`

- For each tab, wrap the chat pane subtree with:
  - `<ApplicationPluginsProvider backend={backend} connectionId={connectionId}>...`.

### 2) Session-level plugin actions

- Add plugin session actions to the header actions dropdown.
- Use `useApplicationPlugins()` to get `actionsById` + `sessionActions`.

### 3) Message-level plugin actions

- Add plugin message actions to `MessageActionsBar` as `extraActions`.
- When invoked, open a plugin action dialog for the selected message context.

### 4) Dialog + macOS surface integration

- Reuse `usePluginActionDialog` from `@crystal-lattice/frontend-sdk-react`.
- Reuse the desktop macOS approach used in the sessions pane:
  - On macOS, open a dedicated window/popover via `DesktopWindowManager` and coordinate via a singleton coordinator.
  - On non-macOS, fall back to the shared `ApplicationActionDialog` component.

If chat pane needs to duplicate coordinator boilerplate:

- Extract a small desktop-only helper module so sessions pane + chat pane share the same window/popover integration.

## Verification

- Run a plugin session action that mutates sessions; confirm sessions list refresh triggers.
- Run a plugin message action; confirm dialog opens with prefilled message context.
- Confirm macOS window/popover closes on cancel/submit and doesn’t leak state.
