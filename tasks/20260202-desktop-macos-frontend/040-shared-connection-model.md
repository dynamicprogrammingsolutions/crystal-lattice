# Subtask: Shared connection model + persistence (SDK)

Extract connection record types and persistence helpers into the SDK so mobile + desktop do not diverge.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/000-main.md`

## Status

- [x] Done

Implemented in:

- SDK:
  - `packages/frontend-sdk/src/storage/keyValueStore.ts:1`
  - `packages/frontend-sdk/src/connections/types.ts:1`
  - `packages/frontend-sdk/src/connections/store.ts:1`
  - Tests: `packages/frontend-sdk/src/connections/__tests__/store.test.ts:1`
- Mobile adoption:
  - `mobile/crystal-lattice-control-rn/App.tsx:1`
  - `mobile/crystal-lattice-control-rn/src/connectionInfo.ts:1`
  - `mobile/crystal-lattice-control-rn/src/ConnectionsScreen.tsx:1`
  - `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx:1`
- Desktop adoption (Option B):
  - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx:1`

## Decisions (approved)

- Keep the existing storage key and JSON shape to avoid breaking existing saved connections:
  - `clc_connections_v1` (currently `STORAGE_KEY_CONNECTIONS` in `mobile/crystal-lattice-control-rn/App.tsx:76`).
- Include all connection kinds in the SDK types now (`manual`, `discovery`, `bridge`) so the mobile migration can be no-behavior-change.
- Introduce `KeyValueStore` as an SDK abstraction (SDK must not import `AsyncStorage`).
- Desktop adoption: **Option B**
  - Add `@react-native-async-storage/async-storage` to the desktop app.
  - Use the SDK persistence helpers at runtime.
  - Add a tiny “connections debug” UI so persistence can be manually verified (add/clear; persists across relaunch).

## What exists today

Mobile defines its own connection record model and persistence in `mobile/crystal-lattice-control-rn/App.tsx`:

- Types:
  - `ConnectionRecord` union starts at `mobile/crystal-lattice-control-rn/App.tsx:42`
- Storage keys:
  - `STORAGE_KEY_CONNECTIONS` at `mobile/crystal-lattice-control-rn/App.tsx:77`

Desktop Phase 5 needs connections in the left column (top section), so duplicating this in desktop would create drift.

## Work plan

### 1) Add SDK connection types

- Create `packages/frontend-sdk/src/connections/types.ts` with:
  - `BaseConnectionRecord`
  - `ManualConnectionRecord`
  - `ConnectionRecord`

For Phase 5, the desktop app only uses manual connections, but the type should remain extensible.

### 2) Add SDK persistence helpers

Note: the SDK currently does **not** expose a `KeyValueStore` type yet (it only
exists in historical planning notes such as
`archive/plans/frontend-sdk/proposed-interfaces.ts:196`).

As part of this subtask, add the `KeyValueStore` interface to the SDK and export it from `packages/frontend-sdk/src/index.ts`.

- Create `packages/frontend-sdk/src/connections/store.ts` implementing:
  - `loadConnections(store: KeyValueStore): Promise<ConnectionRecord[]>`
  - `saveConnections(store: KeyValueStore, connections: ConnectionRecord[]): Promise<void>`
  - Optionally, a `ConnectionStore` class.

Use the SDK `KeyValueStore` abstraction (do not import `AsyncStorage` from SDK).

Additional requirements:

- Provide `CONNECTIONS_STORAGE_KEY` as an exported SDK constant equal to `clc_connections_v1`.
- Add unit tests for `loadConnections`/`saveConnections` using an in-memory `KeyValueStore`.

### 3) Adopt in mobile (no behavior change)

- Update mobile to use the SDK types/helpers.
- Keep the stored JSON schema + key compatible (do not bump) unless unavoidable.

Also update any mobile modules that import `ConnectionRecord` from `../App` to import the SDK type instead:

- `mobile/crystal-lattice-control-rn/src/connectionInfo.ts:1`
- `mobile/crystal-lattice-control-rn/src/ConnectionsScreen.tsx:12`
- `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx:6`

### 4) Adopt in desktop

- Add `@react-native-async-storage/async-storage` to `desktop/crystal-lattice-control-desktop-rn/`.
- Add a `KeyValueStore` adapter over AsyncStorage in the desktop app.
- Use the SDK `loadConnections`/`saveConnections` at runtime.
- Add a minimal debug UI to verify persistence:
  - shows saved connection count and names
  - “Add demo manual connection” button
  - “Clear connections” button

## Open question

Should discovery/bridge variants be included in the SDK types now?

- Option A (recommended): include them, but allow desktop to only *use* manual.
- Option B: only implement manual now; extend later when desktop needs it.

Decision: Option A.
