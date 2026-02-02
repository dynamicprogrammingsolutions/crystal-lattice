# Subtask: Shared connection model + persistence (SDK)

Extract connection record types and persistence helpers into the SDK so mobile + desktop do not diverge.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/000-main.md`

## Status

- [ ] Not started

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

- Create `packages/frontend-sdk/src/connections/store.ts` implementing:
  - `loadConnections(store: KeyValueStore): Promise<ConnectionRecord[]>`
  - `saveConnections(store: KeyValueStore, connections: ConnectionRecord[]): Promise<void>`
  - Optionally, a `ConnectionStore` class.

Use the SDK `KeyValueStore` abstraction (do not import `AsyncStorage` from SDK).

### 3) Adopt in mobile (no behavior change)

- Update mobile to use the SDK types/helpers.
- Keep the stored JSON schema compatible if possible, or bump a versioned storage key.

### 4) Adopt in desktop

- Desktop uses the same model/persistence for its connections panel.

## Open question

Should discovery/bridge variants be included in the SDK types now?

- Option A (recommended): include them, but allow desktop to only *use* manual.
- Option B: only implement manual now; extend later when desktop needs it.
