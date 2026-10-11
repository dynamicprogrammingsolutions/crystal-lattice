# Frontend — Saved Bridge URLs

Make bridge URLs easy to save and reuse in the mobile app. The default
workflow should be: use a previously added bridge, add a new bridge, or
remove a saved bridge — instead of typing the URL manually every time.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md

---

## Requirements checklist

- [x] Add a `SavedBridgeUrl` type to the frontend SDK (`packages/frontend-sdk/src/connections/types.ts`)
- [x] Add storage functions for saved bridge URLs (`loadSavedBridgeUrls`, `saveSavedBridgeUrls`) in a new or existing store module
- [x] Export new types and functions from `packages/frontend-sdk/src/index.ts`
- [x] Add frontend SDK unit tests for the saved bridge URL store
- [x] Update `App.tsx` bridge connection wizard to show saved bridge URLs first
- [x] Tapping a saved bridge URL connects to it immediately (lists servers)
- [x] "Add new bridge" option for entering a URL manually; on successful connect, auto-save the URL
- [x] "Remove" action (trash icon or swipe) to delete a saved bridge URL
- [x] When a bridge connection succeeds, auto-save the bridge URL for future use
- [x] Update `ConnectionsScreen.tsx` or bridge wizard UI as needed for the new flow
- [x] Run frontend SDK tests (`npm --workspace @crystal-lattice/frontend-sdk test`)

---

## Reconciliation with the HTTP bridge rollout

The approved follow-up plan in
`tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
now includes delivery of this task's existing requirements. Keep this checklist
open until those requirements are implemented and verified; merging a plan does
not complete the saved-URL workflow.

Preserve the user-facing behavior described here: saved bridges are shown
first, selecting one immediately connects and lists servers, Add New Bridge
enables manual entry, successful bridge discovery saves the endpoint before
server pairing, and Remove deletes only the saved URL.

Saved bridge endpoints remain separate from paired server connection records.
The HTTP rollout changes transport selection: normal discovery/pairing uses
HTTP, and a global override in Home → Development Settings can explicitly
select legacy WebSocket or hybrid for later connection construction. Saved URL
entries do not contain that override or pairing credentials.

The implementation guidance below is interpreted through that approved plan:
use the shared mode factory, hydrate saved URLs before writes, and verify the
actual picker-to-discovery connection as well as storage and native UI.

---

## Implementation notes

### Baseline before implementation (`App.tsx`)

Before this follow-up, the bridge wizard (`renderBridgeConnection()`):
1. Shows a `TextInput` for the bridge URL.
2. User types the URL and taps "Connect to Bridge".
3. `connectToBridge()` uses the shared bridge mode factory, connects, and lists servers.
4. User selects a server, enters pairing code, and connects.

There was no separate saved-bridge-URL concept. The implemented flow and
remaining native verification are recorded at the end of this task and in
the owning bridge follow-up.

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
2. Add `connectionsStore`-based persistence for saved bridges with a hydration
   guard so initial empty state cannot overwrite saved endpoints.
3. Modify `renderBridgeConnection()`:
   - When `!connectingBridgeTransport` (initial bridge screen):
     - If `savedBridgeUrls.length > 0`: show a list of saved bridges (URL + label, tap to connect).
     - Show "Add new bridge" button → reveals the URL `TextInput` + "Connect" button.
     - Each saved bridge has a trash icon to remove it.
   - When `connectingBridgeTransport` is set: show server list / pairing as before.
4. In the shared discovery handler: after successful connect and server-list
   retrieval, upsert the bridge URL into `savedBridgeUrls`. This also applies
   to an empty server list and does not require pairing. Retain the existing
   requirement to save the URL after successful paired-server connection.
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
- Mobile app: component/native tests cover saved-first selection, manual add,
  relaunch, and removal. Include one integration through the production picker,
  connection handler, SDK mode factory, and bridge discovery API; mocked
  discovery or store-only tests do not prove this flow.
- Run: `npm --workspace @crystal-lattice/frontend-sdk test`

## Implementation evidence and remaining verification

- The approved bridge follow-up implements the SDK type/store/exports, with
  public round-trip, invalid-storage, and independent-removal tests. The full
  SDK suite passes (381 tests).
- Mobile's delivered Home modal contains the saved-first picker, Add New
  Bridge, discovery auto-save before pairing, and trash removal. App component
  tests and a real bridge integration prove discovery, pairing, relaunch,
  token reuse, and independent endpoint storage.
- Native verification is complete on both iOS and Android. Earlier
  runtime/window-focus blockers and their resolution are recorded in the
  owning follow-up task.

## Completion Notes

Completed on 2026-10-10 through the approved bridge follow-up.

- All existing requirements are implemented: public SDK endpoint type/store,
  exports and tests, and the saved-first mobile bridge picker with manual
  addition, successful-discovery auto-save before pairing, and trash removal.
- Evidence: SDK suite 381 tests; App component/store consumer tests; real
  production App-to-bridge integration; and successful iOS/Android Detox
  journeys with actual discovery/pairing, relaunch/reuse, endpoint removal,
  and paired-server reopen. Removing an endpoint preserves credentials.
- Earlier native blockers were resolved. Android required correcting the
  existing E2E immersive-mode guard on window focus and using a clean plain
  AOSP emulator. Tests still traverse production UI, SDK, and public backend
  paths without bypasses or substituted connection callbacks.
- HTTP-default and general Development Settings delivery remains tracked by
  `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`;
  its human-review and later desktop gates are separate from this completed
  saved-endpoint capability.