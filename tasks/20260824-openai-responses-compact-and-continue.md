# OpenAI Responses Compact And Continue

Let users optionally start a normal coordinated request immediately after a
successful OpenAI Responses native compaction without appending a synthetic
message.

## Requirements checklist

### Functional requirements

- [ ] The native compaction action offers compact-only and
  compact-and-continue choices.
- [ ] Successful continuation starts a normal model request without appending
  a synthetic user or system message.
- [ ] The continuation uses the latest effective session configuration after
  compaction commits.
- [ ] Continued requests have the same admission, event, persistence,
  cancellation, and frontend visibility behavior as ordinary sends.
- [ ] If continuation cannot obtain admission, compaction remains successful
  and the user receives a manual Continue action.
- [ ] Cancellation or application shutdown before continuation prevents a new
  request from starting.
- [ ] Compaction completion and subsequent request lifecycle are represented
  coherently through the common operation/status notification contract.

### Non-functional requirements

- [ ] Continuation uses the shared request coordinator and never calls the
  low-level request iterator directly.
- [ ] Request start cannot bypass session exclusivity, stale application
  generation checks, or reload draining.
- [ ] Retries and repeated follow-up actions cannot start duplicate requests.
- [ ] Compaction success remains committed even when continuation fails.
- [ ] Provider-specific continuation choices remain inside the OpenAI
  Responses application plugin.
- [ ] Existing compact-only behavior remains compatible and independently
  testable.

Depends On:

- `tasks/20260802-openai-responses-background-compaction.md`
- `tasks/20260824-operational-notifications-and-global-attention/030-request-operation-notifications-and-status.md`

## Supporting facts

- Background native compaction, progress updates, cancellation, guarded commit,
  and frontend refresh are implemented.
- Shared application request-start orchestration supports starting an existing
  session without appending a message.
- The original background-compaction task retains an unimplemented Stage D for
  selectable no-message continuation.
- Request-operation notifications will provide the common authoritative status
  lifecycle for the continued request.

## Execution plan

Status: Draft

Move the original Stage D product scope into this focused follow-up. Add a
standard action input or follow-up choice for compact-only versus
compact-and-continue. After guarded compaction commit and successful operation
cleanup, resolve the latest application/session configuration and request
admission through the shared coordinator.

Keep compaction and continuation as two linked operations. A continuation
failure must not roll back compaction. When admission is unavailable, publish a
terminal compaction-success notification with a manual Continue action that
uses the same coordinator.

### Implementation decisions and open questions

- Decision: no synthetic message is appended.
- Decision: continuation resolves current configuration after commit.
- Decision: compaction and request have distinct operation IDs and lifecycle
  records.
- Recommendation: default to compact-only unless the user explicitly selects
  continuation.

### Documentation

- Update OpenAI Responses compaction docs and action examples.
- Cross-link shared request execution and operation notification contracts.
- Document admission failure and manual Continue behavior.

### Task checklist

- [ ] Confirm selection/default UX.
- [ ] Add action input and result/follow-up behavior.
- [ ] Start continuation through shared request coordination.
- [ ] Add admission failure and manual Continue path.
- [ ] Integrate operation/status notifications.
- [ ] Add application, plugin, HTTP, SDK, and frontend tests.
- [ ] Run selective saved-login/API compaction continuation smoke.
- [ ] Complete mobile/desktop manual checkpoint.
- [ ] Update original compaction task relations and documentation.

### Requirement verification

- Compact-only produces no request.
- Compact-and-continue starts exactly one normal request with no new message.
- A busy/reloading session keeps the compaction result and exposes manual
  continuation.
- Request cancellation and events match ordinary sends.
- Repeated action or follow-up execution cannot double-start.

### Additional implementation verification

- Configuration changed during compaction is reflected in continuation.
- Application shutdown between commit and start produces no late request.
- A request failure changes only request operation state, not compaction
  success.