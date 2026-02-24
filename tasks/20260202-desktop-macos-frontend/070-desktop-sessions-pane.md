# Subtask: Desktop sessions pane (left column bottom)

Implement the left-column sessions list (below connections) using `SessionsController`.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/060-desktop-connections-panel.md`

## Status

- [x] Implemented

## Implementation Notes (macOS / Fabric)

This subtask uncovered several macOS-specific constraints under the New Architecture (Fabric) and implemented native container workarounds.

### 1) RN `Modal` is unreliable on macOS + Fabric

- We hit a repeatable crash when showing dropdowns via `Modal` (stack referenced `ReactFabric-dev.js` and `RCTModalHostView`).
- Because of this, the desktop app intentionally avoids React Native `Modal` for macOS interactions that need overlays.

### 2) Session actions dropdown on macOS uses `NSPopover` (not `Modal`)

- `ActionsMenuBar` on macOS `variant="dropdown"` uses a native anchored popover.
  - JS entry point: `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx:1`
  - Native container: `toggleActionsPopover(...)` in `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm:1`
  - Popover content (separate RN root): `desktop/crystal-lattice-control-desktop-rn/src/windows/ActionsPopoverView.tsx:1`
- The popover content uses the same layout primitives as mobile:
  - `ActionsMenuContent` (icon + label + star pin toggle)
    - `packages/frontend-rn-components/src/actions/ActionsMenuContent.tsx:1`

### 3) Cross-root state for popovers uses a coordinator module

- Because the popover is a separate RN root, we pass menu data and handlers via a small in-memory coordinator:
  - `packages/frontend-rn-components/src/actions/actionsPopoverCoordinator.ts:1`
- Anchor tracking was added so subsequent dialogs can anchor to the last actions menu location:
  - `getLastActionsPopoverAnchorTag()` / `setLastActionsPopoverAnchorTag(...)` in `packages/frontend-rn-components/src/actions/actionsPopoverCoordinator.ts:1`

### 4) Pinned state race fix + optimistic local state

- A stale-props race caused "pin item 1" then "pin item 2" to unpin item 1 when toggling quickly.
- Fixed the underlying toggle logic to compute from the latest pinned state using a ref:
  - `packages/frontend-rn-components/src/actions/useActionsMenuModel.ts:1`
- To improve responsiveness, the macOS actions popover also maintains optimistic local pinned state while still calling upstream `onTogglePinned`:
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/ActionsPopoverView.tsx:1`

### 5) Plugin action dialogs on macOS use native containers (popover default, window optional)

- The shared `ApplicationActionDialog` (mobile) is Modal-based; for macOS we needed a Modal-free layout.
- Solution:
  - Extracted `ApplicationActionDialogLayout` (no RN `Modal`) and kept `ApplicationActionDialog` for non-macOS.
    - `packages/frontend-rn-components/src/ApplicationActionDialog.tsx:1`
  - Implemented a dedicated desktop dialog host RN root that can render inside either an `NSPopover` or an `NSWindow`.
    - Coordinator: `desktop/crystal-lattice-control-desktop-rn/src/windows/applicationActionDialogCoordinator.ts:1`
    - Host view: `desktop/crystal-lattice-control-desktop-rn/src/windows/ApplicationActionDialogWindow.tsx:1`
    - Native window APIs: `openApplicationActionDialogWindow(...)` / `closeApplicationActionDialogWindow()`
    - Native popover APIs: `openApplicationActionDialogPopover(...)` / `closeApplicationActionDialogPopover()`
      - All in `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm:1`
- Presentation mode is switchable from code and defaults to popover:
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/applicationActionDialogPresentation.ts:1`

### 6) Popover sizing behavior (height is controlled by caller)

- Neither the Session Actions popover nor the Action Dialog popover auto-measure their height from rendered content.
- The working pattern used across the app is: compute a height in JS and pass it into native `NSPopover`.
  - Session actions size computation: `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx:1`
  - Action dialog size computation: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:1`
- If a simple confirmation appears too tall, the controlling clamp is in the JS-side height calculation (not native).

### 7) Temporary NSMenu/NSPopover demos were removed

- We briefly added standalone NSMenu + NSPopover demos to validate native anchoring.
- After confirming `NSPopover` was the correct direction, the demo UI and demo native APIs were removed.

## Requirements

- When connected, list sessions.
- Clicking a session row selects/focuses it in the list (does not open a tab).
- A dedicated “Open” button (or similar affordance) opens the session as a tab in the main column (do not navigate away).
- If the session is already open in a tab, opening focuses the existing tab.
- Desktop sessions UI should reach feature parity with the mobile sessions list:
  - Title/subtitle/meta derived from plugin-provided session list fields.
  - Session list actions (plugin-provided actions) via the shared pinnable actions UI.
  - Per-session pinned toggle (⭐) via plugin-provided pinned toggle UI element.
  - Search.
  - New session with agent selection.
- Sessions list should refresh when:
  - focused connection changes
  - user requests refresh
  - a session is created/deleted (controller or plugin events)

Notes:

- Multiple connections can be open at the same time.
- The sessions pane lists sessions for a single `focusedConnectionId` at a time.
- Opening a session creates/activates a tab keyed by `{ connectionId, sessionId }`.

## Related code (already implemented)

Current desktop app already has the layout + tab model; 070 replaces the sessions placeholder with a real controller-driven sessions pane.

- Left column sessions pane:
  - Rendered from: `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1`
  - Component: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:1`
- Tabs already exist and already enforce “open or focus existing”:
  - `openTab()` dedupes by `tabId = ${connectionId}:${sessionId}` and sets `activeTabId`.
  - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1`
- Connection runtime backends live in `openConnectionsById`:
  - `desktop/crystal-lattice-control-desktop-rn/src/connections/useOpenConnections.ts:1`
- Sessions list offline cache is already persisted (added in 060):
  - Cache hook: `desktop/crystal-lattice-control-desktop-rn/src/cache/useSessionsCache.ts:1`
  - Cache shape: `desktop/crystal-lattice-control-desktop-rn/src/cache/types.ts:1`
- Sessions reload triggers are decoupled via an app-level event bus:
  - `desktop/crystal-lattice-control-desktop-rn/src/events/desktopEventBus.ts:1`
- New session agent selection uses a dedicated macOS window:
  - Window component: `desktop/crystal-lattice-control-desktop-rn/src/windows/AgentPickerWindow.tsx:1`
  - Native window manager: `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm:1`
- SDK controller to use:
  - `packages/frontend-sdk/src/sessions/sessionsController.ts:1`
  - Hook helper (optional): `packages/frontend-sdk-react/src/useSessionsController.ts:1`

Mobile reference implementation (target parity):

- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx:1`
- Uses plugin registry + action runner:
  - `packages/frontend-sdk-react/src/applicationPlugins.tsx:1`
  - `packages/frontend-sdk/src/plugins/actionRunner.ts:1` (via `runApplicationAction`)
- Uses shared pinnable-actions UI primitive:
  - `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx:1`
- Uses shared wrappers / helpers (extracted during 070):
  - `packages/frontend-rn-components/src/actions/SessionActionsBar.tsx:1`
  - `packages/frontend-rn-components/src/ApplicationActionDialog.tsx:1`
  - `packages/frontend-rn-components/src/sessionActions.ts:1`
  - `packages/frontend-sdk-react/src/usePersistentPinnedActions.ts:1`

## Implementation plan (authoritative for 070)

### 0) Scope / non-goals

070 covers the *sessions list pane* (left column bottom). The main chat UI + per-tab chat controller lifecycle are handled in `080`.

However, 070 should implement the sessions pane UX to match the mobile sessions list (search, new session w/ agent selection, pinned toggle, per-row actions).

### A) Avoid duplication: extract clearly-shared UI/logic

Desktop must not copy/paste mobile UI or reimplement shared patterns.

1) Extract the “pinnable actions bar” wrappers used by mobile into shared components.

- Create shared RN components in `packages/frontend-rn-components/` (or move existing files there):
  - `SessionActionsBar` wrapper around `ActionsMenuBar`
  - (optional now, but recommended for parity with 080) `MessageActionsBar`

- Also extract the built-in action definition lists so desktop and mobile share the same keys/labels/icons:
  - Move `mobile/crystal-lattice-control-rn/src/sessionActions.ts` into a shared module (recommended: `packages/frontend-rn-components/`), and update mobile + desktop imports.
  - (Optional now, but recommended for 080): move `mobile/crystal-lattice-control-rn/src/messageActions.ts` similarly.

Migration requirement:

- Any extraction/move must be accompanied by updating the existing mobile app code to import/use the new shared module(s).
  - No “optional later” follow-ups; the mobile app must build/run against the refactor in the same PR.
  - Prefer deleting the now-unused mobile-local files after migration to prevent drift.

Design constraint:

- Shared wrappers should not hard-depend on a specific icon library.
- Provide `renderIcon`/`renderPinIcon`/`renderCloseIcon` props (same pattern as `ActionsMenuBar`) so apps can supply Feather (mobile/desktop) or any other renderer.

2) Extract the plugin action dialog UI.

- Move `mobile/crystal-lattice-control-rn/src/components/ApplicationActionDialog.tsx` into `packages/frontend-rn-components/` so desktop and mobile can share one implementation.
- Update it to use `@crystal-lattice/frontend-rn-components` theme and `extractByPath` from `@crystal-lattice/frontend-sdk`.

Migration requirement:

- Update mobile call sites to use the shared `ApplicationActionDialog` immediately.

3) Add a shared persistence hook for pinned action keys.

- Add a storage-agnostic hook in `packages/frontend-sdk-react/` that persists a string-array to a `KeyValueStore`.
  - Example API:
    - `usePersistentStringArray({ store, key, initial })`
    - `usePersistentPinnedActions({ store, key, initialPinned })`
- Desktop will use this with `desktop/.../src/storage/asyncStorageKeyValueStore.ts`.
- Mobile must be migrated to use this shared hook as part of this subtask.
  - This includes switching to per-connection storage keys.
  - Implement a `KeyValueStore` adapter for mobile (AsyncStorage-backed) so the hook can be used there.

Persistence rules:

- Pinned session-list action keys must be scoped per connection id.
  - Example storage key: `clc_pinned_session_list_actions_v1:${connectionId}`.
  - If mobile uses a global key today, update it during this subtask (migration should preserve existing pinned keys for the currently-selected connection when possible).

### B) Replace placeholder with real `SessionsPanel`

1) Add new component `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx`.

Props (minimum viable):

- `focusedConnectionId: string | null`
- `focusedConnectionName: string | null`
- `backend: AgentBackend | null` (from `openConnectionsById[focusedConnectionId]?.backend`)
- `connectionId: string | null` (passed explicitly; required for plugin registry + cache keys)
- `cachedSessions: SessionSummary[]`
- `cachedLastLoadedAt: number | null`
- `isOnline: boolean`
- `onUpdateCache: (connectionId: string, sessions: SessionSummary[]) => void`
- `onOpenSessionTab: (params: { connectionId: string; sessionId: string; title?: string }) => void`

2) Update `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx` to render `SessionsPanel` instead of `SessionsPanelPlaceholder`.

Notes:

- Keep using the existing `openTab()` logic in `DesktopRoot` so 070 doesn’t touch tabs behavior.
- Continue to show cached sessions when offline.

### C) Controller wiring + refresh rules

Goal: sessions pane is driven by `SessionsController` when online, but gracefully falls back to cache.

1) Create a `SessionsController` for the focused connection when `backend` is available.

Recommended approach for Phase 5:

- Use `useSessionsController({ backend, initialSessions: cachedSessions, limit })`.
- Also hydrate with `useHydrateControllerFromCache` so `lastLoadedAt` and cached sessions apply exactly once per controller.

Controller lifecycle note:

- Prefer keeping one controller per *open connection* (keyed by `connectionId`) so switching focus does not cause redundant loads.
- If `useSessionsController` is too “focused-only”, implement a small desktop-only controller map:
  - `useSessionsControllerByConnectionId(connectionId, backend, cache)`.
  - (Optional) if useful beyond RN, consider a shared keyed-controller helper in `packages/frontend-sdk-react/`.

2) Implement refresh triggers:

- **Focused connection changes**: when `focusedConnectionId` changes and `backend` is non-null, call `controller.loadIfStale({ staleMs: 30_000 })`.
  - If it returns a list, call `onUpdateCache(focusedConnectionId, list)`.
- **User requests refresh**: add a refresh button (use `PanelHeader menuLabel="↻"` + `onPressMenu`) that calls `controller.load({ force: true })`.
  - On success: `onUpdateCache(...)`.
- **Session created**: after creating a session, force-refresh sessions list and update cache.
- **Session deleted / plugin-triggered refresh**:
  - Phase 5 baseline: do not implement delete UI yet (no `deleteSession` in `AgentBackend`).
  - Keep this flexible for future “reload triggers” originating elsewhere (e.g. chat pane actions in 080):
    - Implement an app-level event bus now (see section J) so any surface (sessions pane, chat pane, menus) can request a reload without reaching into component internals.

3) Loading/error behavior:

- Show cached sessions immediately.
- When online and controller is loading, show a compact loading row/spinner.
- If controller has an error, show it inline but keep cached list visible.

### D) Plugins + session list presentation (match mobile)

1) Load plugin UI schema for the focused connection.

- In desktop root (or within `SessionsPanel`), wrap the sessions pane in:
  - `ApplicationPluginsProvider` from `@crystal-lattice/frontend-sdk-react`
  - Use `backend` + `connectionId` as provider inputs.

2) Use plugin-provided session list fields for title/subtitle/meta.

- Use `useApplicationPlugins()` to access `sessionListFields`.
- Use SDK helpers to compute display strings:
  - `groupSessionListFields()` / `deriveSessionListPresentationFromGroups()` from `@crystal-lattice/frontend-sdk`

### E) Sessions list UI (desktop-friendly)

Implement in `SessionsPanel.tsx`:

- Header:
  - `PanelHeader` title: `Sessions`
  - Subtitle should include focused connection name (or “No focused connection”), online/offline, and cache timestamp.
  - Refresh button: `menuLabel="↻"`.
- Controls row (top of panel content):
  - search input (`TextInput`) with local filter state
  - “New session” button (`Pressable`) aligned right
  - Disable “New” when offline/no backend.
- List:
  - Keep server order (match mobile).
  - Row click selects (highlights) but does not open.
  - Each row has an “Open” button that appears on hover.
  - Double-clicking a row opens it.
  - “Open” (button or double-click) calls `onOpenSessionTab({ connectionId, sessionId, title })`.
  - Row text:
    - Use plugin presentation (`deriveSessionListPresentationFromGroups`).
    - Fall back to `session.preview` / `session_id` if no plugin fields.

### F) Session pinned toggle (⭐) (match mobile)

Mobile supports a per-session “pinned” flag via a plugin-provided UI element.

- Use `useApplicationPlugins()` to access `sessionListPinnedToggles`.
- If `sessionListPinnedToggles[0]` exists:
  - Render a ⭐ icon button in each session row.
  - On press: execute the plugin action via `runApplicationAction` (SDK) using `usePluginActionDialog` (SDK React).
    - Use `effects: { reloadSessionsListOnMutations: true }` so pin/unpin triggers `reloadSessionsList` consistently.
  - If action effects include `reloadSessionsList`, call `controller.load({ force: true })` and update cache.

### G) Session list actions (pinnable buttons) (match mobile)

Mobile renders a per-session `SessionActionsBar` and supports:

- Built-in actions (reload, agent switch, settings, etc.)
- Plugin-provided session-list actions (`sessionListActions`)
- Persisted pinned action buttons (user-configurable)

Desktop plan:

1) Use `useApplicationPlugins()` to access `sessionListActions` + `actionsById`.
2) Map plugin elements to `ActionDefinition` objects for the shared `SessionActionsBar` wrapper.
3) Persist the pinned action keys using the shared `usePersistentPinnedActions` hook (from section A.3).
   - Persistence must be scoped per connection id (see Open questions / decisions below).
4) Execute plugin actions using `runApplicationAction` and respond to effects:
   - `navigateToSession` should translate to `onOpenSessionTab({ connectionId, sessionId })`.
   - `reloadSessionsList` should reload + update cache.
   - Use `effects: { reloadSessionsListOnMutations: true }` so actions that mutate sessions consistently request a reload.

### H) “New session” with agent selection (match mobile)

Mobile flow uses `useAgentsController` and an agent picker modal before creating the session.

Desktop plan:

1) Use `useAgentsController({ backend, cacheKey: connectionId, enabled: isOnline && isActive })`.
2) “New session” button opens an agent picker UI:
   - Use a separate desktop window (`NSWindow`), like the connection editor.
   - Window should not create sessions directly; it should return a selected `agentId` to the main window.
     - This keeps session creation + cache/tab updates centralized in `DesktopRoot`/`SessionsPanel`.
3) Create session:
   - Choose agent id (or fall back using `pickDefaultAgentId` from SDK).
   - `await controller.createSession({ agentId })`.
   - Immediately open/focus the new tab via `onOpenSessionTab({ connectionId, sessionId })`.
   - Refresh sessions list + update cache.

If `createSession()` fails, show an inline error (and optionally an `Alert`).

### I) Done criteria / checklist

- [x] `SessionsPanelPlaceholder` is no longer rendered.
- [x] Online: sessions load and refresh works; cache is updated.
- [x] Offline: cached sessions still visible; refresh/new session disabled.
- [x] Clicking a row selects it; “Open” (hover button or double-click) opens/focuses a tab (existing `openTab()` behavior).
- [x] Switching focused connection switches the sessions list and triggers load-if-stale when online.
- [x] Title/subtitle/meta match `deriveSessionListPresentationFromGroups` output when plugin fields exist.
- [x] Per-session pinned toggle (⭐) works when a pinned toggle element exists.
- [x] Per-session action bar uses shared pinnable-actions UI (no duplicated implementation).

### J) App-level event bus (enables future reload triggers)

Add a lightweight event bus in desktop app code.

Rationale:

- We know we’ll need cross-surface triggers (e.g. a plugin action invoked from the chat pane requests the sessions list reload).
- An event bus keeps this decoupled without forcing prop-drilling everywhere.

Plan:

- Add `desktop/crystal-lattice-control-desktop-rn/src/events/desktopEventBus.ts`.
- Use a minimal typed pub/sub (either a tiny custom emitter or a thin wrapper around `EventEmitter`).
- Use a plain TypeScript pub/sub module (no Node `EventEmitter`).
- Events (initial set):
  - `sessionsReloadRequested`: `{ connectionId: string; reason?: string }`
  - `sessionOpenRequested`: `{ connectionId: string; sessionId: string }` (optional; may be redundant with direct callbacks today)
- `SessionsPanel` subscribes to `sessionsReloadRequested` for its `connectionId` and triggers `controller.load({ force: true })` + cache update.
- `SessionsPanel` emits `sessionsReloadRequested` after actions that require reload.
- `080` can emit `sessionsReloadRequested` after chat actions that mutate sessions.

## Open questions (need approval before implementing)

Resolved decisions (from latest guidance):

- Agent picker UI: use a dedicated `NSWindow` (Option B).
- Sessions ordering: keep server order (match mobile).
- Session list built-in actions: skip settings/agent-switch built-ins here; plugin-provided actions are mandatory.
- Pinned action persistence: scope per connection id; if mobile uses a global key today, fix it.
- Reload triggers: add an app-level event bus (section J).
- Open affordance: show “Open” on hover + double-click opens.

Remaining open questions:

None.
