# Subtask: Desktop connections panel (manual only)

Implement the left-column top panel showing connections and enabling manual connect (host/port).

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/040-shared-connection-model.md`
- `tasks/20260202-desktop-macos-frontend/050-desktop-shell-layout.md`

## Status

- [ ] In progress

Implemented so far:

- Runtime open connections map + health check (manual connections only).
- Connections panel UI (rows, status, Open/Close, kebab actions).
- New/Edit connection opens in a real macOS `NSWindow`.
- Persisted caches for sessions list + messages (with message cap).
- Sessions pane can display cached sessions while offline.

## Requirements

- Manual connections only for Phase 5.
- The panel shows saved connections and which ones are open.
- Selecting a connection constructs:
  - `FetchTransport`
  - `RestAgentBackend`

Notes:

- Phase 5 supports multiple open connections simultaneously.
- The sessions pane (`070`) uses a `focusedConnectionId` to decide which connection’s sessions list is visible.

Additional decisions (approved during planning):

- “No modal” applies to message/session actions; for creating/editing connections we prefer a macOS-native UX.
  - For Phase 5, implement create/edit connection in a real macOS window (like a Preferences/settings window), not a dropdown/modal.
- Tabs must remain open even if a connection is closed/offline.
  - User can view cached session list and cached messages without a connection.
  - Desktop cache limits should be more generous than mobile:
    - Target: keep the most recent ~50 messages per session.
    - Cache the session list per connection.
- Connection row click behavior should be configurable:
  - Default: clicking a row focuses it and opens/connects.
  - Still render a dedicated Open/Close button so we can change this later.

## Work plan

### 1) Data model: persisted records vs runtime open connections

Persisted (saved) connections:

- Stored as `ConnectionRecord[]` (manual-only in Phase 5).
- Persisted via SDK helpers:
  - `loadConnections(store)`
  - `saveConnections(store, records)`

Runtime (open) connections:

- Maintain an in-memory map keyed by `connectionId`:
  - `openConnectionsById: Record<string, { status: 'closed' | 'connecting' | 'open' | 'error'; baseUrl: string; transport?: FetchTransport; backend?: RestAgentBackend; errorMessage?: string; lastOpenedAt?: number }>`
- Opening a connection constructs:
  - `new FetchTransport({ baseUrl })`
  - `new RestAgentBackend({ transport })`
- Run a lightweight connectivity check on open (recommended):
  - `await backend.listAgents()`

### 2) Desktop storage adapter

- Centralize the AsyncStorage `KeyValueStore` adapter in one place (desktop app code).
- Use it for:
  - connection records (SDK helpers)
  - caches (sessions list + messages)

### 3) Implement offline caches (foundation for 070/080)

Even though sessions/messages UI is implemented in `070`/`080`, this task should introduce the cache storage model so tabs can remain open offline.

Sessions list cache (per connection):

- Persist `{ sessions: SessionSummary[]; lastLoadedAt: number | null }` keyed by `connectionId`.
- Used by `070` to show cached sessions when offline.

Messages cache (per connection + session):

- Persist `{ messages: IndexedMessage[]; lastLoadedAt: number | null; cursorEventId?: string | null; activeRequestId?: string | null; composeText?: string; scrollAnchor?: any }` keyed by `connectionId` + `sessionId`.
- Do not cap message count for a single session.
- Enforce a cap on the number of sessions with message history cached per connection:
  - `MAX_CACHED_SESSIONS_PER_CONNECTION = 50` (drop oldest sessions beyond the limit).
- Used by `080` so chat tabs can be viewed offline.

### 4) Connections panel UI

Replace placeholder connections panel with a real `ConnectionsPanel`.

Row click behavior must be configurable (prop/config):

- `rowClickBehavior: 'focusOnly' | 'focusAndOpen' | 'focusAndToggleOpen'`
- Default: `focusAndOpen`

Connection list rows:

- Show name + `host:port`
- Show status (Closed/Connecting/Open/Error)
- Render a dedicated Open/Close button
- Render a kebab menu (anchored dropdown is fine here):
  - Edit…
  - Delete (confirm; `Alert` acceptable)

Header actions:

- “New connection…” opens the connection editor window.
- Optional quick actions:
  - “Open most recent” / “Close all”

### 5) Create/edit connection in a real macOS window

Implement a small window manager for RN macOS so the connection editor uses a separate `NSWindow`.

Approach:

1) Register an additional RN root component (e.g. `ConnectionEditorWindow`) in `desktop/.../index.js`.
2) Add a native macOS module (bridge) to open a new `NSWindow` hosting that RN component with initial props.
3) Send results back to the main window via an event emitter:
   - `connectionEditorSaved` with a payload containing the updated `ConnectionRecord`.

Editor UI:

- Name, host, port fields
- Save/Cancel
- Validation: host non-empty; port integer 1–65535

Save behavior:

- Upsert the `ConnectionRecord` and update `lastUsedAt`.
- Optionally auto-open the connection after saving (recommended default).

### 6) Auto-reconnect on app start (open question)

Recommended:

- Auto-open the most recent (`lastUsedAt`) connection on startup and set it as `focusedConnectionId`.
- If auto-open fails, show status `error` on that row; cached data remains accessible.

## Open question

Do we need auto-reconnect on app start?

- Option A (recommended): yes, reconnect to the most recent (`lastUsedAt`) and set it as `focusedConnectionId`.
- Option B: no; user must explicitly open a connection.

Current implementation: Option A.

## Implementation notes

- Persisted connections + CRUD
  - `desktop/crystal-lattice-control-desktop-rn/src/connections/usePersistedConnections.ts:1`
  - Uses SDK `loadConnections`/`saveConnections` with AsyncStorage adapter.
- Runtime open connection manager
  - `desktop/crystal-lattice-control-desktop-rn/src/connections/useOpenConnections.ts:1`
  - Opens `FetchTransport` + `RestAgentBackend` and validates via `listAgents()`.
- Connections panel UI
  - `desktop/crystal-lattice-control-desktop-rn/src/panels/ConnectionsPanel.tsx:1`
  - `rowClickBehavior` is a prop; `DesktopRoot` currently uses `focusAndOpen`.
  - “Clear connections” is confirmed via `Alert`.
- New/Edit connection window
  - JS window component: `desktop/crystal-lattice-control-desktop-rn/src/windows/ConnectionEditorWindow.tsx:1`
  - Native window manager module: `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm:1`
  - Registered in: `desktop/crystal-lattice-control-desktop-rn/index.js:1`
  - Save emits `connectionEditorSaved` → app upserts record and auto-opens.
- Offline caches
  - Storage keys: `desktop/crystal-lattice-control-desktop-rn/src/cache/storageKeys.ts:1`
  - Sessions cache hook: `desktop/crystal-lattice-control-desktop-rn/src/cache/useSessionsCache.ts:1`
  - Messages cache hook (cap 50 msgs/session): `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:1`
  - Messages cache hook (cap 50 sessions/connection; no per-session message cap): `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:1`
  - `DesktopRoot` prefetches sessions into cache on successful connect:
    - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1`
  - Cached sessions are rendered in the sessions pane placeholder:
    - `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanelPlaceholder.tsx:1`

## Remaining work

- Make cached messages visible in tabs when offline (Phase 5 expectation).
  - The messages cache is persisted already, but the chat pane is still a placeholder.
- Add explicit “refresh sessions list” behavior when online (hook up the “↻” affordance).
- Decide whether “Delete connection” should keep or clear caches/tabs.
  - Current behavior: delete clears caches and closes tabs for that connection.

## Checklist

- [x] Centralize AsyncStorage `KeyValueStore` adapter in desktop code
- [x] Implement persisted connections model (`ConnectionRecord[]`) via SDK helpers
- [x] Implement runtime `openConnectionsById` map with status + `RestAgentBackend`
- [x] Implement connection health check on open (`listAgents`)
- [x] Add persisted sessions list cache keyed by `connectionId`
- [x] Add persisted messages cache keyed by `connectionId` + `sessionId` with `MAX_CACHED_SESSIONS_PER_CONNECTION = 50`
- [x] Build real `ConnectionsPanel` UI (rows + Open/Close button + kebab menu)
- [x] Add `rowClickBehavior` config (default: open-on-click)
- [x] Implement “New/Edit connection” as a real macOS window (`NSWindow`) hosting an RN component
- [x] Wire editor save event → upsert record → (optional) auto-open
- [x] Implement auto-open most recent on startup (Option A) or document if skipped
- [ ] Verify offline behavior: close connection, tabs remain, cached sessions/messages still visible
