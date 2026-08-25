# Mobile offline workspace and cache access

Make saved connections focusable independently from connectivity and keep
cached Sessions and Messages navigation useful, honest, and correctly scoped
while a runtime is closed, unavailable, reconnecting, or under repair.

## Requirements checklist

- [ ] Selecting any saved connection focuses its cached workspace immediately,
  regardless of whether opening succeeds.
- [ ] Cached session and message content remains navigable after launch,
  explicit close, failed connect, connection loss, and repair cancellation.
- [ ] Offline/freshness, empty-cache, loading, invalidated, and refresh-failed
  states are distinct and preserve prior cached content.
- [ ] Server-authoritative actions are disabled or initiate explicit
  reconnection while local browsing, filtering, copying, transcript
  navigation, and drafting remain available.
- [ ] Saved connections, sessions cache, workspace selection, and messages
  cache cannot be overwritten by pre-hydration initial state.
- [ ] Close, credential reset, cache clear, draft discard, and saved-connection
  deletion have distinct user-visible effects and confirmations.
- [ ] Automated and native relaunch tests demonstrate cached offline
  navigation through production screens.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On:

- `tasks/20260823-frontend-connection-lifecycle/015-mobile-connection-host-specification.md`
- `tasks/20260823-frontend-connection-lifecycle/030-mobile-connection-race-and-cancellation-cleanup.md`

## Supporting details

- Normative requirements: `FCL-002`, `FCL-009`, `FCL-011`,
  `FCL-014`–`FCL-015`, `FCL-020`–`FCL-021`.
- Mobile package requirements: `MCL-006`–`MCL-009`, `MCL-012`–`MCL-013`.
- `ConnectedRoot` already accepts nullable backends and can render selected
  cached sessions/messages, but mobile cannot reliably select an unreachable
  saved connection.
- Messages persistence already has an explicit hydration queue; saved
  connections and the monolithic sessions cache need equivalent safety.
- Desktop's focused offline session presentation provides useful current
  behavior but does not define the portable mobile UX.
- Complete attachment/text draft persistence remains in subtask 050; this
  subtask must preserve current drafts and keep the composer reachable.

## Execution plan
Status: Draft

Persist and restore focused connection and per-connection selected session.
Make row focus immediate and independent from an optional Open/Retry attempt.
Use the lifecycle runtime map to provide a backend only when the focused
connection has a usable runtime.

Consolidate mobile saved-connection and sessions-cache hydration behind guarded
hooks or shared storage primitives. Preserve cached content through failed
refresh and expose freshness/invalidation separately from runtime status.

Keep Sessions and Messages mounted/navigable for focused cache. Gate each
server-authoritative action at the action boundary while retaining local
operations. Replace generic “No active connection” errors with offline state
and recovery actions where cached content exists.

Define explicit close/delete/cache-clear behavior. Deleting or clearing local
state names cached content and drafts in confirmation text and does not imply
remote deletion.

### Implementation decisions and open questions

- **Recommendation:** Reuse or generalize the shared session-scoped storage
  pattern instead of retaining one unvalidated monolithic sessions-cache JSON
  value.
- **Decision:** Focusing a row is immediate; a combined focus-and-open gesture
  may begin opening but open failure does not undo focus.
- **Decision:** Offline compose remains available, but automatic send queueing
  is excluded.
- **Decision:** Explicit Close leaves the connection focused by default because
  Close means runtime closure and the product target preserves workspace
  continuity.

### Documentation

- Update mobile user docs for focusing offline saved connections, cache
  freshness, action availability, and local-data controls after delivery.
- Update mobile development docs for hydration/store ownership and offline
  backend gating.
- Update `MCL-*` evidence for host persistence/offline behavior.
- Update requirement evidence only for complete verified outcomes.

### Task checklist

- [ ] Add guarded saved-connection and sessions-cache hydration hooks.
- [ ] Persist focused connection and selected session per connection.
- [ ] Focus saved records independently from Open/Retry attempts.
- [ ] Present cache freshness, offline, empty, invalidated, and failed-refresh
  states.
- [ ] Preserve prior caches through network failure.
- [ ] Gate server actions while retaining local interactions and composer.
- [ ] Separate close, credential reset, cache clear, draft discard, and delete
  UX.
- [ ] Add storage/hydration and component tests.
- [ ] Add production-screen offline relaunch/navigation tests on supported
  mobile platforms.
- [ ] Run mobile, shared storage, backend-adapter, and documentation checks.
- [ ] Update current docs and requirement evidence.

### Requirement verification

- `FCL-002`, `FCL-009`: launch/failure tests focus an unreachable saved
  connection and navigate its cached sessions/messages without a backend.
- `FCL-011`: connection/session restoration remains isolated for duplicate
  session IDs on different connections.
- `FCL-014`: delayed-storage tests prove no initial empty write and deterministic
  edits during hydration for every touched store.
- `FCL-015`: failed refresh leaves prior content and timestamp visible while
  marking it unavailable/stale.
- `FCL-020`: component tests verify the exact local state removed by each
  destructive action and its confirmation.
- `FCL-021`: native/component checks cover offline indicators and disabled
  action accessibility.
- `MCL-006`–`MCL-008`, `MCL-012`–`MCL-013`: package evidence covers
  workspace persistence, hydration, offline surfaces, deletion scopes, and
  native selectors.

### Additional implementation verification

- App launch does not use a fixed delay as a substitute for hydration.
- Closing the runtime while viewing Messages keeps the same connection/session
  and draft visible.
- Reconnect success refreshes authoritative data without stealing navigation
  from a newer user action.
- A corrupt cache entry does not prevent other connections from hydrating.