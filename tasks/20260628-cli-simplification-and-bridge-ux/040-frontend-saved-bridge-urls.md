# Frontend — Saved Bridge URLs

Make bridge URLs easy to save and reuse in the mobile app. The default
workflow should be: use a previously added bridge, add a new bridge, or
remove a saved bridge — instead of typing the URL manually every time.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md

---

## Requirements checklist

- [ ] Add a `SavedBridgeUrl` type to the frontend SDK (`packages/frontend-sdk/src/connections/types.ts`)
- [ ] Add storage functions for saved bridge URLs (`loadSavedBridgeUrls`, `saveSavedBridgeUrls`) in a new or existing store module
- [ ] Export new types and functions from `packages/frontend-sdk/src/index.ts`
- [ ] Add frontend SDK unit tests for the saved bridge URL store
- [ ] Update `App.tsx` bridge connection wizard to show saved bridge URLs first
- [ ] Tapping a saved bridge URL connects to it immediately (lists servers)
- [ ] "Add new bridge" option for entering a URL manually; on successful connect, auto-save the URL
- [ ] "Remove" action (trash icon or swipe) to delete a saved bridge URL
- [ ] When a bridge connection succeeds, auto-save the bridge URL for future use
- [ ] Update `ConnectionsScreen.tsx` or bridge wizard UI as needed for the new flow
- [ ] Run frontend SDK tests (`npm --workspace @crystal-lattice/frontend-sdk test`)

---

## Implementation notes

### Current bridge connection flow (`App.tsx`)

The bridge wizard (`renderBridgeConnection()`, line ~580) currently:
1. Shows a `TextInput` for the bridge URL.
2. User types the URL and taps "Connect to Bridge".
3. `connectToBridge()` (line ~470) creates a `BridgeTransport`, connects, and lists servers.
4. User selects a server, enters pairing code, and connects.

There is no saved-bridge-URL concept. Every time the user wants to connect via bridge, they must retype the URL.

### Saved bridge URL type

```typescript
export interface SavedBridgeUrl {
  url: string;
  label?: string;
  lastUsedAt: number;
}
```

### Storage

Create `packages/frontend-sdk/src/connections/savedBridges.ts`:

```typescript
export const SAVED_BRIDGES_STORAGE_KEY = 'clc_saved_bridges_v1';

export async function loadSavedBridgeUrls(store: KeyValueStore): Promise<SavedBridgeUrl[]> {
  // Same pattern as loadConnections
}

export async function saveSavedBridgeUrls(
  store: KeyValueStore,
  bridges: readonly SavedBridgeUrl[],
): Promise<void> {
  // Same pattern as saveConnections
}
```

Reuse the existing `KeyValueStore` interface from `packages/frontend-sdk/src/storage/keyValueStore.ts`.

### Mobile app changes (`App.tsx`)

1. Add state: `savedBridgeUrls: SavedBridgeUrl[]`, loaded on mount (same pattern as `connections`).
2. Add `connectionsStore`-based persistence for saved bridges (same `useEffect` save pattern).
3. Modify `renderBridgeConnection()`:
   - When `!connectingBridgeTransport` (initial bridge screen):
     - If `savedBridgeUrls.length > 0`: show a list of saved bridges (URL + label, tap to connect).
     - Show "Add new bridge" button → reveals the URL `TextInput` + "Connect" button.
     - Each saved bridge has a trash icon to remove it.
   - When `connectingBridgeTransport` is set: show server list / pairing as before.
4. In `connectToBridge()`: after successful connect, upsert the bridge URL into `savedBridgeUrls`.
5. Add `handleDeleteSavedBridge(url: string)` to remove a saved bridge.

### UI layout for saved bridges

```
Bridge Connection

Saved Bridges:
  ┌──────────────────────────────────────┐
  │ wss://crystal-bridge...  🗑          │  ← tap to connect
  └──────────────────────────────────────┘
  ┌──────────────────────────────────────┐
  │ ws://192.168.1.100:4000  🗑          │  ← tap to connect
  └──────────────────────────────────────┘

  [ + Add New Bridge ]

  (when "Add New Bridge" is tapped, show the TextInput + Connect button)
```

### Key files to modify

- `packages/frontend-sdk/src/connections/types.ts` — add `SavedBridgeUrl`
- `packages/frontend-sdk/src/connections/savedBridges.ts` — new store module
- `packages/frontend-sdk/src/index.ts` — export new types and functions
- `packages/frontend-sdk/src/connections/__tests__/store.test.ts` or a new test file — saved bridge store tests
- `mobile/crystal-lattice-control-rn/App.tsx` — bridge wizard UI changes

### Testing approach

- Frontend SDK: unit test `loadSavedBridgeUrls` / `saveSavedBridgeUrls` (same pattern as existing `store.test.ts`).
- Test that saving and loading round-trips correctly.
- Test that deleting a bridge URL removes it from the list.
- Mobile app: the existing test infrastructure may not cover `App.tsx` integration; focus on SDK-level tests and manual verification.
- Run: `npm --workspace @crystal-lattice/frontend-sdk test`