# Mobile multiple open connections

Expose the shared multi-runtime model in mobile so several saved connections
can remain open while one cache-backed workspace is focused, without
cross-connection navigation, event, draft, or failure interference.

## Requirements checklist

- [ ] Several connection rows can be Open concurrently and each row exposes
  independent Open, Opening, Cancel, Close, Unavailable, Retry, and repair
  state.
- [ ] Focusing one connection restores its selected session, caches, and draft
  without opening, closing, or reconstructing another runtime.
- [ ] Runtime failure, retry, repair, events, notifications, invalidations, and
  foreground recovery remain scoped and cannot take focus/navigation from
  another connection.
- [ ] Closing one runtime leaves its saved workspace focused or unfocused
  offline and never silently closes another runtime.
- [ ] Connection-targeted deep links/actions resolve against any matching open
  runtime while navigation remains explicit current intent.
- [ ] Background/foreground and process-restart policies communicate resource
  limits and never silently reopen or close a set of runtimes.
- [ ] iOS and Android production-screen evidence covers concurrent open,
  switching, failure isolation, and close-to-offline continuity.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On:

- `tasks/20260823-frontend-connection-lifecycle/015-mobile-connection-host-specification.md`
- `tasks/20260823-frontend-connection-lifecycle/020-shared-connection-lifecycle-controller.md`
- `tasks/20260823-frontend-connection-lifecycle/030-mobile-connection-race-and-cancellation-cleanup.md`
- `tasks/20260823-frontend-connection-lifecycle/040-mobile-offline-workspace-and-cache-access.md`
- `tasks/20260823-frontend-connection-lifecycle/050-durable-composer-drafts.md`

## Supporting details

- Normative requirements: `FCL-002`, `FCL-008`–`FCL-013`, `FCL-021`,
  `FCL-023`; `MCL-001`, `MCL-005`–`MCL-013`.
- The shared controller and mobile adoption are intentionally multi-runtime
  capable before this UI is enabled.
- Focus, selected session, caches, and drafts are already required to be
  connection-scoped by earlier subtasks.
- Current mobile connection-level deep links and displays are selected-backend
  oriented and must become runtime-map consumers.
- Bridge WebSocket/HTTP/hybrid behavior remains unchanged per runtime.

## Execution plan
Status: Draft

Remove the intermediate one-runtime promotion policy from the mobile host.
Render each saved row from the shared runtime/attempt snapshot and retain all
user-open runtimes until explicit Close, process teardown, or documented
platform lifecycle suspension.

Route focused Sessions/Messages through backend lookup for the focused
connection while connection-level displays, notifications, and deep links can
resolve every open runtime.

Track the current-process desired-open set for foreground recovery. Restore
saved workspaces offline after process restart without automatically opening
every previous runtime. Add an explicit resource-limit response if native
testing demonstrates a necessary bound; do not implement silent LRU closure.

### Implementation decisions and open questions

- **Decision:** Opening one runtime does not close another.
- **Decision:** Closing the focused runtime keeps its workspace focused
  offline.
- **Decision:** Process restart restores workspaces but does not automatically
  reopen all previously open runtimes.
- **Recommendation for approval:** Do not impose a hard maximum until native
  evidence requires one. If required, expose the limit and ask which runtime
  to close.
- **Question for plan approval:** Whether a user setting should later opt into
  reopening a remembered open set. Recommendation: defer; it is not needed for
  initial multiple-open behavior.

### Documentation

- Update mobile current user docs for multiple-open rows, focus versus Open,
  Close-to-offline, and restart behavior after delivery.
- Update mobile development docs for runtime-map consumers and resource
  policy.
- Update root/package requirements with implementation and native evidence.
- Do not change bridge transport documentation or claim automatic reconnect.

### Task checklist

- [ ] Remove the one-runtime host replacement policy.
- [ ] Render independent runtime/attempt state and Open/Close controls per row.
- [ ] Route focused screens by connection backend lookup.
- [ ] Route connection-level displays/notifications across all open runtimes.
- [ ] Resolve deep links/actions against any matching open runtime.
- [ ] Implement per-runtime background/foreground desired-open recovery.
- [ ] Add explicit resource-limit handling if native evidence requires it.
- [ ] Add deterministic host/component multi-runtime tests.
- [ ] Add iOS and Android production-screen multi-open acceptance scenarios.
- [ ] Run mobile/shared/bridge compatibility and documentation checks.
- [ ] Update current docs and `FCL-*`/`MCL-*` evidence.

### Requirement verification

- `FCL-023`, `MCL-010`: native/component tests open A/B, switch focus, close B
  offline, and prove A remains open.
- `FCL-008`, `MCL-005`: foreground recovery executes independently for A/B and
  stale A work cannot modify B.
- `FCL-011`, `MCL-006`: selected sessions and complete drafts restore
  independently while focus changes.
- `FCL-013`, `MCL-011`: unfocused open runtime receives scoped deep links,
  displays, notifications, and invalidations without implicit focus.
- `FCL-021`, `MCL-013`: every row state/action and focused/offline distinction
  is accessible and natively selectable.

### Additional implementation verification

- Two bridge runtimes with different modes retain their own mode/token/server
  identity.
- Direct failure does not stop bridge event observation and vice versa.
- Closing an unfocused connection does not rerender or navigate the focused
  Chat.
- Process relaunch restores both workspaces offline without opening either.
- No runtime credential appears in cross-connection diagnostics.