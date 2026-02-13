# Desktop: add “Plugins…” to session actions + UI container

Parent Task: tasks/20260213-session-plugins-ui/000-main.md

Depends On:
- tasks/20260213-session-plugins-ui/030-shared-ui-and-controller.md

## Description

Add a “Plugins…” action to the desktop app’s session actions bar (same placement as Session settings), and open a UI that lists plugins with switches + reset.

## Background / current code

- Desktop session actions are defined in:
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
  - Built-in actions array includes `'settings'` and is rendered via `ActionsMenuBar`.

- “Settings…” opens a dedicated desktop window via:
  - `setActiveSessionSettingsWindow(...)` then `DesktopWindowManager?.openSessionSettingsWindow(...)`
  - Window content: `desktop/.../src/windows/SessionSettingsWindow.tsx`

There is no existing “Plugins” window.

## Implementation options (choose one)

### Option A (recommended for first iteration): in-ChatPane modal (JS-only)

Pros:
- No native macOS window wiring.
- Fastest path.

Cons:
- Not identical to “Settings…” window UX.

Steps:

1) Update action keys:
   - Extend `ChatSessionActionKey` union to include `'plugins'`.
2) Add built-in action definition:
   - Add `{ key: 'plugins', label: 'Plugins…', iconName: 'toggle-left' | 'package' | 'sliders' }` to `BUILTIN_SESSION_ACTIONS`.
3) Add state to control the modal:
   - `pluginsVisible: boolean`
4) In `handleSessionAction`, handle `'plugins'` similarly to `'settings'`:
   - Check `backend` exists.
   - Check `backend.getCapabilities().sessionPlugins`.
   - `setPluginsVisible(true)`.
5) Create a view component (could live in `desktop/.../src/windows/` or `desktop/.../src/chat/`):
   - e.g. `desktop/.../src/windows/SessionPluginsModal.tsx`
   - Uses the shared controller hook and shared list component.

### Option B: dedicated desktop window (parity with Settings)

Pros:
- Matches existing desktop settings UX more closely.

Cons:
- Requires macOS native window manager changes (more involved).

Steps:

1) Add a coordinator similar to `sessionSettingsCoordinator.ts`:
   - `sessionPluginsCoordinator.ts`
2) Add a new window React entry similar to `SessionSettingsWindow.tsx`:
   - `SessionPluginsWindow.tsx`
3) Extend the macOS native module to support opening/closing this window:
   - Update `DesktopWindowManagerModule` interface and native implementation.
4) Wire ChatPane action to open the window.

## Shared component usage

Whichever container you choose, the inner content should:

- Use `useSessionPluginsController({ backend, sessionId })`
- Render `SessionPluginsList` from `@crystal-lattice/frontend-rn-components`

## Done when

- Desktop ChatPane has a “Plugins…” action next to “Settings…”.
- Clicking it opens a UI and toggles persist to server.
- Capability gating disables action on backends that don’t support it.
