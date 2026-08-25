# Wait-Only Interaction Execution

Allow a bounded in-flight tool-call interceptor to wait for a persisted
interaction response and then proceed, short-circuit, expire, or cancel within
the same request execution.

## Requirements checklist

### Functional requirements

- [ ] A tool-call interceptor can create an interaction before tool execution
  and wait for its response.
- [ ] A valid response unblocks the interceptor and applies plugin-defined
  proceed, parameter, or short-circuit behavior.
- [ ] Timeout applies the plugin-defined default response or terminal outcome.
- [ ] Request cancellation unblocks the interaction and records cancellation.
- [ ] Application reload/shutdown interrupts active waits with explicit
  lifecycle outcome.
- [ ] Dummy approve, deny, form, timeout, and cancel flows complete through a
  real request/tool loop.

### Non-functional requirements

- [ ] Every wait has a finite configured maximum.
- [ ] Waiting does not hold the session persistence lock.
- [ ] Process-local waiter state is never treated as durable restart recovery
  state.
- [ ] Waiter registration, response, timeout, cancellation, and cleanup are
  thread/async safe and idempotent.
- [ ] Interaction or waiter failure cannot leave request admission or
  application-generation ownership unreleased.
- [ ] Generic waiter/orchestration code contains no plugin-specific choice
  semantics.

Parent Task:
`tasks/20260824-interactive-notifications-and-request-suspension/000-main.md`

Depends On:

- `tasks/20260824-interactive-notifications-and-request-suspension/010-interaction-contract-and-record-model.md`
- `tasks/20260717-tool-call-interceptor-capability.md`

## Execution plan

Status: Draft

Add a minimal application-lifetime interaction waiter registry keyed by
interaction identity and tied to exact application generation/request
cancellation. The interceptor creates the persisted interaction before
registering/waiting and supplies only plugin-owned interpretation callbacks or
data.

Response/cancel/timeout transitions update the authoritative interaction first,
then signal the matching waiter. Cleanup is identity-safe so stale operations
cannot resolve a newer waiter.

Integrate one dummy provider extension/interceptor and deterministic provider
to prove real tool-loop behavior.

### Implementation decisions and open questions

- Decision: persisted interaction state is authoritative; waiter objects are
  disposable process-local coordination.
- Decision: waiters do not survive application reconstruction.
- Recommendation: interrupted reload/shutdown marks the interaction cancelled
  or interrupted rather than attempting automatic recovery.

### Documentation

- Document wait-only lifecycle, timeout, cancellation, reload, and process
  lifetime in application/plugin development docs.
- Keep generic notification lifecycle in the root specification.

### Task checklist

- [ ] Approve interruption outcome.
- [ ] Add waiter registry and cleanup.
- [ ] Wire response/cancel/timeout signaling.
- [ ] Integrate generic interceptor.
- [ ] Add dummy approve/deny/form producer.
- [ ] Add request, cancellation, reload, and failure tests.
- [ ] Add SDK/frontend real-backend integration coverage.
- [ ] Complete manual wait/respond checkpoint.

### Requirement verification

- Approve proceeds with the tool; deny short-circuits it.
- Timeout applies the configured default and request completes.
- Cancellation and reload unblock promptly and release request ownership.
- No session lock is held during user wait.
- Duplicate/stale response cannot signal another interaction.

### Additional implementation verification

- Waiter cleanup occurs after unexpected interceptor/tool-loop exceptions.
- Multiple sessions can wait independently.
- One session cannot admit a conflicting request while its wait-only request
  remains active.