# Interactive Notifications And Request Suspension

Extend the existing persistent notification contract with specialized
interaction lifecycle state so plugins can request user input and safely wait,
suspend, cancel, or continue request/tool execution.

## Requirements checklist

### Functional requirements

- [ ] An interaction is represented as a specialized persisted notification
  record using the existing session notification authority, revision, event,
  display, attention, retention, and history contracts.
- [ ] Plugins define interaction choices, forms, defaults, timeout, response,
  cancellation, and result semantics.
- [ ] Responses execute through standard application action and validation
  paths.
- [ ] Wait-only interactions can pause an in-flight tool boundary until
  response, timeout, or cancellation.
- [ ] Durable interactions can complete the current request in a suspended
  state and continue through shared request coordination after response.
- [ ] Pending interactions are visible in their owning Chat and through compact
  waiting-for-input indicators.
- [ ] Important pending interactions can request global attention and explicit
  View navigation.
- [ ] Interaction resolution remains inspectable through notification history.

### Non-functional requirements

- [ ] No second interaction persistence, event, display, history, or frontend
  action framework is introduced.
- [ ] Active interactions are nondismissible as ordinary notifications and
  cannot lose their required response through presentation close.
- [ ] No unbounded wait can permanently occupy a request or block application
  reload/shutdown.
- [ ] Response handling and request continuation are revision-safe and
  idempotent.
- [ ] Interaction state remains hidden from model history except for
  deliberately generated tool/request continuation content.
- [ ] Provider/plugin semantics remain outside generic notification and
  request orchestration.
- [ ] Automated lifecycle/integration tests remain required; manual
  checkpoints cover visual and real-device behavior only.

## Open requirement questions

1. Which execution mode should be the initial product path?
   - Recommendation: implement bounded wait-only first for a deterministic
     vertical slice, then durable suspend/continue after its persisted state
     and continuation contract are approved.
2. Should users be able to hide an active interaction presentation?
   - Recommendation: allow navigation away and compact waiting indicators, but
     do not provide ordinary notification Dismiss while a response is pending.

## Subtasks

- [ ] `tasks/20260824-interactive-notifications-and-request-suspension/010-interaction-contract-and-record-model.md`
- [ ] `tasks/20260824-interactive-notifications-and-request-suspension/020-wait-only-interaction-execution.md`
- [ ] `tasks/20260824-interactive-notifications-and-request-suspension/030-durable-suspend-and-continue.md`
- [ ] `tasks/20260824-interactive-notifications-and-request-suspension/040-frontend-and-native-interaction-ux.md`

## Relationship to earlier work

This task supersedes:

- `tasks/20260619-generic-session-notifications/050-stage-2-interaction-flow-design.md`
- `tasks/20260619-generic-session-notifications/060-stage-2a-backend-wait-only.md`
- `tasks/20260619-generic-session-notifications/070-stage-2a-sdk-and-rn-tests.md`
- `tasks/20260619-generic-session-notifications/080-stage-2b-real-suspend.md`

The earlier plans remain useful research but predate the shared request
coordinator, operation service, current notification lifecycle, persisted
application notifications, global attention, and multiple-open connection
design.

## Supporting facts

- Existing notifications provide IDs, stable keys, revisions, persistence,
  lifecycle events, display/actions/forms, dismissal, resolution, retention,
  history compatibility, and global-attention integration.
- The notification technical contract already reserves `kind` for
  `notification` or `interaction`, but current implementation normalizes only
  ordinary notification states.
- The generic tool-call interceptor is the required execution hook for
  approval/decision interactions at tool-call boundaries.
- `SessionRequestCoordinator` is the owner-aware path for any durable
  continuation.

## Execution plan

Status: Draft

Execute the contract/model subtask first and update the existing notification
service rather than creating a new store. Implement one deterministic dummy
interaction producer and standard response action.

Add bounded wait-only execution using the generic interceptor and cancellation
signals. After that checkpoint, add durable suspended state and no-message
continuation through the shared request coordinator.

Integrate portable SDK/components and production mobile/desktop hosts last,
including compact waiting indicators, global attention, navigation, and native
verification.

Stop for user review if implementation requires a second record store, holding
session locks while waiting, direct low-level request restart, or
provider-specific behavior in generic notification/request code.

### Implementation decisions and open questions

- Decision: interaction is a specialized notification record.
- Decision: active interaction presentation cannot be dismissed as an
  ordinary notification.
- Decision: the interceptor is a hook, not the lifecycle owner.
- Decision: durable continuation uses shared request coordination.
- Open: approve initial execution mode and active-presentation recommendation.

### Documentation

- Extend the root notification specification with interaction lifecycle,
  response, cancellation, timeout, and continuation semantics.
- Update application/tool-loop, SDK, shared component, mobile, desktop, and
  plugin-authoring documentation as stages are delivered.
- Replace old Stage 2 guidance with links to this task and current contracts.

### Task checklist

- [ ] Approve interaction lifecycle and initial execution mode.
- [ ] Execute and verify subtask 010.
- [ ] Execute and verify subtask 020.
- [ ] Complete wait-only manual checkpoint.
- [ ] Plan/approve and execute subtask 030.
- [ ] Execute and verify subtask 040.
- [ ] Complete mobile and desktop native/manual checkpoints.
- [ ] Reconcile notification specifications, history, and documentation.

### Requirement verification

- One interaction persists, renders, accepts a revision-safe response, and
  reaches the plugin/interceptor decision.
- Wait-only response, timeout, and cancellation unblock without deadlock.
- Durable response starts at most one coordinated continuation and survives
  application reconstruction according to the approved recovery contract.
- Mobile/desktop show the interaction only in the correct scope and navigate
  only after explicit View.

### Additional implementation verification

- Stale/duplicate responses cannot alter a newer interaction occurrence.
- Reload/shutdown cannot leave an active waiter or operation indefinitely.
- Historical interaction display cannot submit another response.