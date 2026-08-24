# Durable composer drafts

Make the complete composed message—text, attachment state, and uncertain-send
recovery—durable per connection/session and protected from ordinary cache
eviction.

## Requirements checklist

- [ ] Composer text edits persist with bounded debounce and lifecycle flush,
  restore after process restart, and expose saving or failed-persistence state
  without allowing stale writes to replace newer text.
- [ ] Attachment order, placement, metadata, usable content references,
  upload/readiness state, and recoverable attachment errors restore with the
  owning connection/session draft.
- [ ] A non-empty draft is never silently removed by ordinary session/message
  cache limits or hydration/migration.
- [ ] Append/send clears only the acknowledged submitted draft revision and
  cannot erase edits made while the request was pending.
- [ ] Uncertain sends retain durable submitted content and idempotent recovery
  until resolved or explicitly discarded.
- [ ] Explicit discard, cache clear, and saved-connection deletion state
  exactly which draft data is removed and clean up unreferenced local
  attachment content safely.
- [ ] Storage, component, and native relaunch tests prove restoration through
  production composer behavior.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On: `tasks/20260823-frontend-connection-lifecycle/040-mobile-offline-workspace-and-cache-access.md`

## Supporting details

- Normative requirements: `FCL-011`, `FCL-014`, `FCL-016`–`FCL-020`.
- Shared message-cache entries currently persist `composeText` but not a
  versioned complete draft.
- Mobile keeps attachment drafts, metadata, order, and picker/upload recovery
  in component state.
- Mobile text changes update a ref on every keystroke but normally reach
  persistent storage on blur, inactive/unmount, or explicit clear.
- Mobile message-cache eviction sorts `lastLoadedAt == null` first, making a
  draft-only session vulnerable.
- Existing uncertain-send behavior uses an idempotency key in memory and must
  remain compatible.

## Execution plan
Status: Draft

Introduce a versioned session-draft schema in shared storage, keyed by
connection/session and logically independent from expendable message history.
Migrate text-only entries without losing text.

Create a draft controller/hook that applies revisions, updates memory
immediately, debounces durable writes, flushes at all specified lifecycle
boundaries, and exposes saving/saved/error state. Prevent delayed writes and
older acknowledgements from replacing newer revisions.

Represent attachment draft fields needed to reconstruct the production
composer. Materialize ephemeral picker content into app-managed storage before
claiming it as durable, while retaining durable server-owned asset references
when available. Restore unusable items as visible recoverable errors.

Protect non-empty drafts from cache eviction and implement reference-aware
attachment cleanup after acknowledged submission, explicit discard, or
approved local-data deletion.

Persist uncertain-send content and idempotency/status recovery. Do not add
automatic offline sending.

### Implementation decisions and open questions

- **Recommendation:** Store draft metadata in the shared key-value schema and
  app-owned attachment bytes/files in mobile private storage, referenced by a
  stable draft attachment ID.
- **Alternative:** Persist only server-uploaded asset references. This reduces
  local file management but cannot preserve newly selected or failed-upload
  attachments offline, so it does not satisfy the complete target alone.
- **Recommendation:** Keep drafts in a separate indexed namespace from bounded
  message history; this gives eviction and deletion behavior an unambiguous
  boundary.
- **Question for plan approval:** Select the concrete mobile private-file
  implementation and quota policy after inspecting existing attachment
  helpers. The required outcome is fixed: storage pressure cannot silently
  delete a non-empty draft.

### Documentation

- Add/update shared SDK current implementation documentation for the versioned
  draft schema and storage API.
- Update mobile user docs for restored drafts, offline composition,
  persistence errors, and explicit discard after delivery.
- Update mobile development docs for attachment ownership and cleanup.
- Document schema migration as current behavior only when implemented.

### Task checklist

- [ ] Inspect current attachment content/reference lifetimes and cleanup paths.
- [ ] Define versioned shared draft and attachment schemas.
- [ ] Add backward-compatible text-only migration.
- [ ] Implement revisioned debounced persistence and lifecycle flush.
- [ ] Expose saving/saved/failure state to the production composer.
- [ ] Persist/restore attachment state and app-managed content references.
- [ ] Protect non-empty drafts from eviction.
- [ ] Make acknowledgement and uncertain-send recovery revision-safe/durable.
- [ ] Implement explicit discard/deletion and attachment cleanup.
- [ ] Add shared storage/controller tests.
- [ ] Add mobile component tests using the production composer boundary.
- [ ] Add iOS and Android relaunch/restoration acceptance scenarios where
  supported.
- [ ] Run shared SDK, mobile, native, and documentation verification.
- [ ] Update current docs and requirement evidence.

### Requirement verification

- `FCL-014`, `FCL-016`: delayed hydration/write tests and native relaunch prove
  current text revision restoration and visible write failure.
- `FCL-017`: production composer relaunch restores attachment ordering,
  placement, metadata, and usable/recoverable content.
- `FCL-018`: cache-pressure tests exceed ordinary message limits while
  retaining every non-empty draft.
- `FCL-019`: deferred acknowledgement tests preserve newer edits and restore
  uncertain-send recovery after restart.
- `FCL-020`: discard/cache-clear/delete tests verify exact draft and local-file
  cleanup boundaries.
- `FCL-011`: duplicate session IDs under different connections retain isolated
  draft revisions and attachments.

### Additional implementation verification

- Process termination with a focused input does not require blur to preserve
  the last durably accepted edit.
- App background/unmount flush does not race a newer foreground edit.
- Missing or revoked source URI restores a visible recoverable attachment
  state rather than dropping the item.
- Successfully cleared drafts leave no unreferenced app-owned attachment files.
- Automatic reconnection never automatically submits an offline draft.