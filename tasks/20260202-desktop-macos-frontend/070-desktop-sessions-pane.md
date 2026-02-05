# Subtask: Desktop sessions pane (left column bottom)

Implement the left-column sessions list (below connections) using `SessionsController`.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/060-desktop-connections-panel.md`

## Status

- [ ] Planned (implementation-ready)

## Requirements

- When connected, list sessions.
- Selecting a session opens it as a tab in the main column (do not navigate away).
- If the session is already open in a tab, focus the existing tab.
- Sessions list should refresh when:
  - focused connection changes
  - user requests refresh
  - a session is created/deleted (controller or plugin events)

Notes:

- Multiple connections can be open at the same time.
- The sessions pane lists sessions for a single `focusedConnectionId` at a time.
- Opening a session creates/activates a tab keyed by `{ connectionId, sessionId }`.

## Related code (already implemented)

Current desktop app already has the layout + tab model; 070 is primarily “replace placeholder with real controller-driven sessions pane”.

- Left column currently renders `SessionsPanelPlaceholder`:
  - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:289`
  - Placeholder component: `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanelPlaceholder.tsx:1`
- Tabs already exist and already enforce “open or focus existing”:
  - `openTab()` dedupes by `tabId = ${connectionId}:${sessionId}` and sets `activeTabId`.
  - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:173`
- Connection runtime backends live in `openConnectionsById`:
  - `desktop/crystal-lattice-control-desktop-rn/src/connections/useOpenConnections.ts:1`
- Sessions list offline cache is already persisted (added in 060):
  - Cache hook: `desktop/crystal-lattice-control-desktop-rn/src/cache/useSessionsCache.ts:1`
  - Cache shape: `desktop/crystal-lattice-control-desktop-rn/src/cache/types.ts:1`
- SDK controller to use:
  - `packages/frontend-sdk/src/sessions/sessionsController.ts:1`
  - Hook helper (optional): `packages/frontend-sdk-react/src/useSessionsController.ts:1`

## Implementation plan (authoritative for 070)

### A) Replace placeholder with real `SessionsPanel`

1) Add new component `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx`.

Props (minimum viable):

- `focusedConnectionId: string | null`
- `focusedConnectionName: string | null`
- `backend: AgentBackend | null` (from `openConnectionsById[focusedConnectionId]?.backend`)
- `cachedSessions: SessionSummary[]`
- `cachedLastLoadedAt: number | null`
- `isOnline: boolean`
- `onUpdateCache: (connectionId: string, sessions: SessionSummary[]) => void`
- `onOpenSessionTab: (params: { connectionId: string; sessionId: string; title?: string }) => void`

2) Update `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx` to render `SessionsPanel` instead of `SessionsPanelPlaceholder`.

Notes:

- Keep using the existing `openTab()` logic in `DesktopRoot` so 070 doesn’t touch tabs behavior.
- Continue to show cached sessions when offline.

### B) Controller wiring + refresh rules

Goal: sessions pane is driven by `SessionsController` when online, but gracefully falls back to cache.

1) Create a `SessionsController` for the focused connection when `backend` is available.

Recommended approach for Phase 5:

- Use `useSessionsController({ backend, initialSessions: cachedSessions, limit })`.
- Also hydrate with `useHydrateControllerFromCache` so `lastLoadedAt` and cached sessions apply exactly once per controller.

2) Implement refresh triggers:

- **Focused connection changes**: when `focusedConnectionId` changes and `backend` is non-null, call `controller.loadIfStale({ staleMs: 30_000 })`.
  - If it returns a list, call `onUpdateCache(focusedConnectionId, list)`.
- **User requests refresh**: add a refresh button (use `PanelHeader menuLabel="↻"` + `onPressMenu`) that calls `controller.load({ force: true })`.
  - On success: `onUpdateCache(...)`.
- **Session created**: after creating a session, force-refresh sessions list and update cache.
- **Session deleted / plugin-triggered refresh**:
  - Phase 5 baseline: do not implement delete UI yet (no `deleteSession` in `AgentBackend`).
  - Add a small “public” `refresh()` helper inside `SessionsPanel` so later work (080) can wire additional refresh triggers easily.

3) Loading/error behavior:

- Show cached sessions immediately.
- When online and controller is loading, show a compact loading row/spinner.
- If controller has an error, show it inline but keep cached list visible.

### C) Sessions list UI (desktop-friendly)

Implement in `SessionsPanel.tsx`:

- Header:
  - `PanelHeader` title: `Sessions`
  - Subtitle should include focused connection name (or “No focused connection”), online/offline, and cache timestamp.
  - Refresh button: `menuLabel="↻"`.
- Controls row (top of panel content):
  - search input (`TextInput`) with local filter state
  - “New” button (`Pressable`) aligned right
  - Disable “New” when offline/no backend.
- List:
  - Render sessions sorted by `modified` descending (client-side), unless we decide to keep server order.
  - Each row click calls `onOpenSessionTab({ connectionId: focusedConnectionId, sessionId, title })`.
  - Title heuristic (Phase 5): `session.preview?.trim() || session.session_id.slice(0, 8)`.

### D) “New session” behavior (choose Option A)

- Click “New”:
  1) `await controller.createSession()` (no agent picker in Phase 5 unless required)
  2) immediately `onOpenSessionTab({ connectionId, sessionId, title: 'New session' })`
  3) `await controller.load({ force: true })` and write to cache

If `createSession()` fails, show an inline error (and optionally an `Alert`).

### E) Done criteria / checklist

- [ ] `SessionsPanelPlaceholder` is no longer rendered.
- [ ] Online: sessions load and refresh works; cache is updated.
- [ ] Offline: cached sessions still visible; refresh/new session disabled.
- [ ] Clicking a session opens/focuses a tab (existing `openTab()` behavior).
- [ ] Switching focused connection switches the sessions list and triggers load-if-stale when online.

## Open questions (need approval before implementing)

1) New session agent selection
   - Should desktop Phase 5 choose an agent (like mobile) or call `createSession({})` and let the server pick?
   - If we must pick: we’ll add `useAgentsController` + a lightweight dropdown in the sessions pane.

2) Session ordering
   - Default recommendation: sort by `modified` descending client-side.
   - Alternative: keep server order.

3) Refresh policy
   - Is `loadIfStale({ staleMs: 30_000 })` on focus-change acceptable, or should we always force reload on focus-change?

## Work plan

### 1) Create a `SessionsController` instance

- Use `@crystal-lattice/frontend-sdk-react` hook (`useSessionsController`) or instantiate controller directly.
- Desktop app owns controller lifecycle per connection.

Recommendation:

- Keep one `SessionsController` per open connection.
- Switching `focusedConnectionId` swaps which controller’s state is rendered.

### 2) Session list UI

- Keep UI desktop-friendly:
  - search input at top of sessions panel
  - list below
  - “New session” button

### 3) Open session in main tabs

When a row is clicked:

- call `openTab({ connectionId: focusedConnectionId, sessionId })` which:
  - adds a new tab if not present
  - sets `activeTabId`

### 4) Minimal session metadata

- Use SDK session list presentation helpers if desired.
- Avoid coupling to mobile’s markdown renderer.

## Open questions

1) Session creation behavior
   - Option A (recommended): create session and open a new tab immediately.
   - Option B: create session but do not open until user clicks.

2) Sessions ordering
   - Option A: sort by `last_modified_at` if available.
   - Option B: server order.
