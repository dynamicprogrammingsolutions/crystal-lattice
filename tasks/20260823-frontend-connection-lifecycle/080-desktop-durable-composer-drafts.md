# Desktop durable composer drafts

Adopt the shared complete-draft contract in desktop so offline text,
attachments, persistence status, and uncertain sends survive tab warm-pane
unmount, runtime changes, and application restart.

## Requirements checklist

- [ ] Desktop Chat text remains editable offline and exposes durable
  Saving/Saved/Save failed state while Send/server actions remain
  reconnect-gated.
- [ ] Attachment order, placement, metadata, previews, server/local references,
  readiness, and recoverable errors restore after pane unmount and process
  restart.
- [ ] Non-empty drafts remain independent from ordinary message-cache eviction
  and local preference writes do not advance server freshness.
- [ ] Send acknowledgement clears only the submitted draft revision and never
  erases newer text/attachments.
- [ ] Uncertain sends persist submitted content and idempotent Check
  status/Retry safely behavior across pane/application lifecycle.
- [ ] Draft discard, cache clear, tab close, connection delete, and local
  attachment cleanup execute explicit non-overlapping scopes.
- [ ] Component and macOS acceptance evidence covers offline edit, fourth-tab
  pane eviction/remount, restart, and uncertain send.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On:

- `tasks/20260823-frontend-connection-lifecycle/017-desktop-connection-host-specification.md`
- `tasks/20260823-frontend-connection-lifecycle/050-durable-composer-drafts.md`
- `tasks/20260823-frontend-connection-lifecycle/070-desktop-connection-workspace-ux.md`

## Supporting details

- Normative requirements: `FCL-011`, `FCL-014`, `FCL-016`–`FCL-020`;
  `DCL-007`, `DCL-009`–`DCL-012`, `DCL-015`.
- Task 050 owns shared versioned draft primitives plus mobile adoption.
- Desktop already debounces text but hides persistence failure and disables the
  composer offline.
- Desktop attachment arrays are component-local while only three recent Chat
  panes stay mounted.
- Desktop send failure currently presents an alert without durable idempotent
  recovery.

## Execution plan
Status: Draft

Replace the text-only desktop draft hook with the shared versioned draft
controller while retaining native `MacTextView` integration. Keep text
editable offline and gate only server-authoritative actions.

Persist desktop attachment drafts using durable server asset references and
app-owned local content where an offline path supports it. Flush before a pane
leaves the warm set and restore before rendering the composer.

Integrate draft revisions with send acknowledgement and durable uncertain-send
recovery. Separate server freshness from draft update timestamps and protect
draft storage from message-cache eviction.

### Implementation decisions and open questions

- **Recommendation:** Reuse durable server asset references when upload has
  completed; use app-owned files for attachments selected while offline or
  before upload.
- **Decision:** Tab pane unmount is a normal lifecycle boundary and cannot lose
  draft state.
- **Decision:** Closing a tab does not silently discard a non-empty draft.
- **Question for plan approval:** Whether Close tab with a non-empty draft
  keeps the draft for later reopening or asks to discard. Recommendation: keep
  by default and expose explicit Discard.

### Documentation

- Update desktop user docs for offline composition, save state, restored
  attachments, and uncertain-send recovery.
- Update desktop development docs for shared draft controller, MacTextView
  binding, warm-pane flush/remount, attachment ownership, and tests.
- Update shared/root/package requirement evidence.

### Task checklist

- [ ] Replace text-only hook with shared versioned draft controller.
- [ ] Keep MacTextView editable offline and present save/error status.
- [ ] Persist/restore complete desktop attachment drafts.
- [ ] Flush/restore across warm-pane unmount/remount and application lifecycle.
- [ ] Protect drafts from message eviction and separate freshness timestamps.
- [ ] Integrate revision-safe acknowledgement and uncertain-send recovery.
- [ ] Implement explicit discard/deletion and reference-aware cleanup.
- [ ] Add shared/desktop storage and component tests.
- [ ] Add focused macOS pane-eviction/relaunch/uncertain-send scenarios.
- [ ] Run desktop/shared/mobile regression and documentation checks.
- [ ] Update current docs and `FCL-*`/`DCL-*` evidence.

### Requirement verification

- `FCL-016`, `DCL-009`: offline production composer edits and restores text
  with visible durable state.
- `FCL-017`, `DCL-010`: fourth-tab and relaunch scenarios restore complete
  attachments/status.
- `FCL-018`, `DCL-010`: cache-pressure tests retain every non-empty draft.
- `FCL-019`, `DCL-011`: deferred acknowledgement and restart preserve newer
  edits plus idempotent recovery.
- `FCL-020`, `DCL-012`: tab close, discard, cache clear, and connection delete
  execute documented scopes.
- `FCL-021`, `DCL-015`: save/error/attachment/recovery controls are accessible
  and natively selectable.

### Additional implementation verification

- Text typed within the debounce window flushes before pane unmount.
- A missing local file restores a recoverable attachment row.
- A server asset remains referenced without unnecessary local duplication.
- Reopening a runtime never auto-submits an offline draft.
- Existing mobile draft and shared cache migration tests remain passing.