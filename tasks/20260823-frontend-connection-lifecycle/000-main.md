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
- [ ] Automated and native acceptance evidence covers the important lifecycle,
  offline, and draft boundaries without repeating shared race cases for every
  transport kind.
- [ ] Current package user and development documentation describes the
  delivered behavior without presenting unimplemented specification targets
  as available.

## Scope and sequencing

The immediate program establishes a shared multi-runtime-capable lifecycle
model, adopts it in mobile, exposes existing caches offline, and completes
draft durability. Mobile may initially retain a one-open-runtime policy.

The following remain target behavior but are not separate approved
implementation work in this task set:

- exposing several open runtimes simultaneously in the mobile UI;
- automatic offline send queues;
- broad automatic reconnect/backoff policy;
- complete desktop migration to all connection kinds;
- changing bridge WebSocket/HTTP/hybrid routing or defaults.

## Roadmap status updates

Roadmap:
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
Sheet as required by the instructions. It does not authorize unrelated roadmap
changes. If the user limits the request to local files, do not mutate the
sheet.

## Subtasks

- [x] `tasks/20260823-frontend-connection-lifecycle/010-connection-lifecycle-specification.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/020-shared-connection-lifecycle-controller.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/030-mobile-connection-race-and-cancellation-cleanup.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/040-mobile-offline-workspace-and-cache-access.md`
- [ ] `tasks/20260823-frontend-connection-lifecycle/050-durable-composer-drafts.md`

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
  even while mobile presentation initially permits one.

## Execution plan
Status: Draft

Execute the specification and implementation through the listed subtasks.
Subtask 010 is complete under the user's explicit specification-creation
request. Remaining implementation waits for separate approval of its Draft
plan.

The shared lifecycle foundation establishes connection identity, operation
authority, candidate promotion, normalized lifecycle outcomes, and
connection-kind adapters. Mobile then adopts that foundation before offline
workspace and complete draft behavior are layered on it. This order prevents
offline and draft callbacks from being built on ambiguous connection/session
ownership.

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
- **Deferred product extension:** Mobile presentation of several concurrently
  open runtimes will receive separate work after the shared model and one-open
  mobile adoption are verified.
- **Implementation decision for subtask 050:** Select the concrete
  app-managed attachment storage mechanism when that Draft plan is approved;
  the required outcome already excludes ephemeral picker access as the sole
  durable reference.

### Documentation

- Keep target behavior and live status in
  `docs/development/specifications/frontend-connection-lifecycle/`.
- Update package development pages when the shared SDK, mobile, or desktop
  implementation changes.
- Update package user documentation only for delivered behavior and without
  task phases, requirement IDs, or implementation-progress labels.
- Link rather than duplicate bridge connectivity, transcript navigation, and
  notification contracts.

### Task checklist

- [x] Create the approved cross-package specification and stable requirements.
- [ ] Approve and execute the shared lifecycle-controller subtask.
- [ ] Approve and execute mobile lifecycle adoption and race corrections.
- [ ] Approve and execute offline workspace/cache behavior.
- [ ] Approve and execute complete durable draft behavior.
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