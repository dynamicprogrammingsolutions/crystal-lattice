# Frontend connection lifecycle and offline continuity

Create and implement a durable cross-package connection lifecycle that makes
asynchronous connection work deterministic, keeps cached workspaces available
offline, preserves composed messages, and supports a future mobile
multiple-open-connection UX without changing existing bridge transport
semantics.

## Requirements checklist

- [x] A cross-package living specification defines the target user experience,
  portable frontend behavior, technical lifecycle contract, persistence and
  offline contract, stable requirements, and material design decisions.
- [x] Mobile and desktop package refinements define host/native ownership,
  package requirements, and platform verification without duplicating the
  root UX contracts.
- [ ] Saved connections, focused workspaces, live runtimes, and in-progress
  attempts behave as independent state, with authoritative cancellation and
  non-destructive candidate promotion.
- [ ] Mobile direct, discovery, bridge, and cloud connection flows cannot apply
  stale completion, repair, error, or navigation effects after cancellation,
  supersession, or newer user intent.
- [ ] A saved connection can be focused and its cached sessions/messages
  navigated while its runtime is closed or unavailable, with honest freshness
  and disabled server-authoritative actions.
- [ ] Text and attachment drafts survive normal navigation, connection
  changes, application lifecycle changes, and process restart without ordinary
  cache eviction silently deleting them.
- [ ] Mobile exposes several independently open runtimes while one
  connection/session workspace is focused, with isolated lifecycle,
  notifications, deep links, caches, and drafts.
- [ ] Desktop preserves several open runtimes and cached tabs while adding
  authoritative connection controls, deterministic focus/tab behavior,
  offline composition, and complete draft continuity.
- [ ] Automated and native acceptance evidence covers the important lifecycle,
  offline, and draft boundaries without repeating shared race cases for every
  transport kind.
- [ ] Current package user and development documentation describes the
  delivered behavior without presenting unimplemented specification targets
  as available.

## Scope and sequencing

The program establishes package refinements and a shared
multi-runtime-capable lifecycle model, adopts it through an intermediate
one-runtime mobile migration, exposes existing caches offline, completes draft
durability, enables final mobile multi-open behavior, and converges the current
desktop multi-open workspace on the same contract.

The following remain target behavior but are not separate approved
implementation work in this task set:

- automatic offline send queues;
- broad automatic reconnect/backoff policy;
- complete desktop migration to all connection kinds;
- changing bridge WebSocket/HTTP/hybrid routing or defaults.

## Roadmap status updates

Primary roadmap:
[Product Development Roadmap](../../roadmaps/product-development-roadmap.md)

Release-overlap roadmap:
[Open Source and iOS Release](../../roadmaps/open-source-and-ios-release.md)

Instructions:
[Updating a roadmap through CSV](../../roadmaps/docs/updating-roadmaps.md)

Do not read the linked roadmap or instructions, inspect roadmap state, or
update the roadmap as part of routine task execution or completion. Do so only
when the user explicitly requests a roadmap status update, for example:
“update the task status in the roadmap as per the instructions in the main
task.”

That explicit request authorizes reading the linked files, updating the
authored CSV and generated Markdown, and synchronizing the configured Google
Sheets as required by the instructions. Every represented subtask is updated
in the product roadmap. Subtasks `010`, `015`, `020`, `030`, `040`, `050`, and
`060` are also updated in the release-overlap roadmap. The request does not
authorize unrelated roadmap changes. If the user limits the request to local
files, do not mutate either sheet.

## Subtasks

- [x] `tasks/20260823-frontend-connection-lifecycle/010-connection-lifecycle-specification.md`
- [x] `tasks/20260823-frontend-connection-lifecycle/015-mobile-connection-host-specification.md`
- [x] `tasks/20260823-frontend-connection-lifecycle/017-desktop-connection-host-specification.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/020-shared-connection-lifecycle-controller.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/030-mobile-connection-race-and-cancellation-cleanup.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/040-mobile-offline-workspace-and-cache-access.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/050-durable-composer-drafts.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/060-mobile-multiple-open-connections.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/070-desktop-connection-workspace-ux.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/080-desktop-durable-composer-drafts.md`

## Supporting details

- **Fact:** Mobile currently owns one global transport/backend pair and normally
  sets its selected connection only after network success. Its screens already
  have partial support for cached sessions/messages with no backend.
- **Fact:** Mobile bridge repair and saved-connection completion can mutate
  state after awaited work without checking whether newer user intent
  superseded them.
- **Fact:** Desktop already separates focused and open direct connections and
  supports several runtimes, but closing while opening does not invalidate a
  late completion.
- **Fact:** The shared message cache includes composer text but not attachment
  drafts. Mobile cache eviction can select draft-only entries before
  message-loaded entries.
- **Decision:** The normative target is
  `docs/development/specifications/frontend-connection-lifecycle/`.
- **Decision:** The existing bridge-connectivity specification continues to
  own pairing, resume, transport modes, routing, and wire behavior.
- **Decision:** The shared runtime model supports multiple open connections
  while mobile presentation uses one runtime only as an intermediate migration
  state.
- **Decision:** Root UX/portable behavior remains authoritative; mobile and
  desktop package specifications own host/native technical refinements.
- **Decision:** Desktop initially remains manual-direct-only while its current
  multi-runtime workspace adopts the shared lifecycle.

## Execution plan
Status: Draft

Execute the specification and implementation through the listed subtasks.
Subtask 010 and the package specification subtasks are documentation work
authorized by the user. Software implementation waits for separate approval of
each Draft plan.

The shared lifecycle foundation establishes connection identity, operation
authority, candidate promotion, normalized lifecycle outcomes, and
connection-kind adapters. Mobile then adopts that foundation before offline
workspace and complete draft behavior are layered on it. This order prevents
offline and draft callbacks from being built on ambiguous connection/session
ownership. Final mobile multi-open behavior follows those foundations.

Desktop's limited manual-hook migration proves the shared controller in
subtask 020. Full desktop connection/workspace UX proceeds independently after
that foundation, while complete desktop drafts wait for the shared draft
schema delivered with mobile.

Verification is risk-scaled:

- shared deterministic tests own promise-order, cancellation, and
  supersession matrices;
- adapter tests own transport-kind normalization;
- mobile component tests own status, action, navigation, and offline
  presentation;
- a small native matrix owns real cancellation, cached relaunch, and draft
  restoration;
- existing bridge and backend integration tests protect transport/protocol
  compatibility.

### Implementation decisions and open questions

- **Decided:** Focus is independent from runtime availability.
- **Decided:** Logical operation authority is mandatory even where physical
  abort is supported.
- **Decided:** Candidate validation precedes replacement closure.
- **Decided:** Drafts are protected state, not ordinary expendable message
  cache.
- **Decided:** Mobile presentation of several concurrently open runtimes is
  required after the shared model, one-runtime migration, offline workspace,
  and complete drafts are verified.
- **Decided:** Desktop follow-active-tab synchronizes connection/session when
  enabled and preserves independent Sessions focus when disabled.
- **Decided:** Desktop bridge/cloud/Bonjour UI remains deferred.
- **Implementation decision for subtask 050:** Select the concrete
  app-managed attachment storage mechanism when that Draft plan is approved;
  the required outcome already excludes ephemeral picker access as the sole
  durable reference.

### Documentation

- Keep target behavior and live status in
  `docs/development/specifications/frontend-connection-lifecycle/`.
- Keep mobile/desktop host targets and package evidence in their package
  connection-lifecycle specifications.
- Update package development pages when the shared SDK, mobile, or desktop
  implementation changes.
- Update package user documentation only for delivered behavior and without
  task phases, requirement IDs, or implementation-progress labels.
- Link rather than duplicate bridge connectivity, transcript navigation, and
  notification contracts.

### Task checklist

- [x] Create the approved cross-package specification and stable requirements.
- [x] Complete and validate mobile/desktop package refinements.
- [ ] Approve and execute the shared lifecycle-controller subtask.
- [ ] Approve and execute mobile lifecycle adoption and race corrections.
- [ ] Approve and execute offline workspace/cache behavior.
- [ ] Approve and execute shared/mobile durable draft behavior.
- [ ] Approve and execute mobile multiple-open behavior.
- [ ] Approve and execute desktop connection/workspace behavior.
- [ ] Approve and execute desktop complete draft behavior.
- [ ] Reconcile requirement evidence and current documentation after each
  implementation delivery.
- [ ] Complete final cross-package verification and human checkpoints.

### Requirement verification

- Specification requirement: owning index, product, frontend, technical,
  persistence, requirements, and decision pages are authored and linked from
  `docs/development/index.md`.
- Lifecycle foundation: verify `FCL-001`–`FCL-008` and `FCL-012`–`FCL-013`
  through shared controller/adapter tests and consuming frontend behavior.
- Mobile lifecycle: verify `FCL-001`–`FCL-011` and `FCL-021` through component
  tests and production-screen native race/cancellation scenarios.
- Offline continuity: verify `FCL-002`, `FCL-009`, `FCL-011`, `FCL-014`–`FCL-015`,
  and `FCL-020` through offline launch, cached navigation, failure-retention,
  and deletion-boundary evidence.
- Draft continuity: verify `FCL-011`, `FCL-014`, and `FCL-016`–`FCL-020`
  through storage/controller tests and production composer relaunch evidence.
- Mobile multi-open: verify `FCL-023` and `MCL-010`–`MCL-013` through
  independent-runtime, focus switching, failure isolation, and native
  lifecycle evidence.
- Desktop workspace: verify `FCL-022`, `DCL-001`–`DCL-008`, and
  `DCL-012`–`DCL-016` through shared-consumer, panel/tab, editor, and macOS
  evidence.
- Desktop drafts: verify `DCL-009`–`DCL-012`, `DCL-015` through warm-pane,
  offline composer, relaunch, and uncertain-send evidence.

### Additional implementation verification

- Existing frontend SDK fast tests and focused bridge integration tests.
- Mobile TypeScript, Jest, and production-screen iOS/Android scenarios affected
  by connection or draft changes.
- Desktop fast tests when shared controller/cache changes affect its current
  consumer behavior.
- Documentation preparation and normal MkDocs build after authored
  documentation changes.

## Implementation Notes

- 2026-08-23: The specification subtask was executed under the user's explicit
  request. No software implementation subtask has been approved.
- 2026-08-23: User approved package host refinements and task expansion for
  mobile multi-open plus desktop workspace/drafts. Software plans remain Draft.
- 2026-08-23: Mobile and desktop package specification subtasks completed with
  documentation preparation tests/build and unique `MCL-*`/`DCL-*`
  requirements.