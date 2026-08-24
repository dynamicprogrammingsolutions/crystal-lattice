# Durable Suspend And Continue

Persist a pending interaction, complete the current request safely, and start
at most one owner-aware no-message continuation after the user responds.

## Requirements checklist

### Functional requirements

- [ ] A tool-call interceptor can persist an interaction and return a valid
  pending/suspended tool result without holding a waiter.
- [ ] The current request completes with durable correlation needed for later
  response and continuation.
- [ ] A valid response stores plugin-defined values and starts a coordinated
  request continuation without appending a synthetic user message.
- [ ] The interceptor recognizes the responded interaction during continuation
  and applies the response without creating another interaction.
- [ ] Timeout and cancellation can terminally resolve a suspended interaction
  without unwanted continuation.
- [ ] Application/server restart can recover suspended interaction state and
  preserve explicit user continuation behavior.
- [ ] Admission failure preserves the response and offers a safe manual
  Continue action.

### Non-functional requirements

- [ ] Continuation uses `SessionRequestCoordinator` or its public
  `AgentApplication` wrapper and never the low-level request iterator.
- [ ] Response/retry/reconnect cannot start duplicate continuations.
- [ ] Continuation cannot race another request, application reload, session
  mutation, or stale generation.
- [ ] Persisted correlation is minimal, provider-neutral, and hidden from model
  history except deliberate tool/request content.
- [ ] External side-effect replay limitations are explicit and not hidden by
  test-only shortcuts.
- [ ] A failed continuation does not erase the stored response or corrupt the
  prior completed request.

Parent Task:
`tasks/20260824-interactive-notifications-and-request-suspension/000-main.md`

Depends On:

- `tasks/20260824-interactive-notifications-and-request-suspension/010-interaction-contract-and-record-model.md`
- `tasks/20260717-tool-call-interceptor-capability.md`
- `tasks/20260824-operational-notifications-and-global-attention/030-request-operation-notifications-and-status.md`

## Open requirement questions

1. Should continuation replay the intercepted tool call deterministically or
   begin another LLM phase from persisted pending context?
   - Recommendation: define a provider-neutral pending tool/result contract
     and let the normal no-message request/tool loop consume it; do not rely on
     the model spontaneously recreating an identical call.

## Execution plan

Status: Draft

Finalize the persisted suspended-correlation shape after subtask 010 and the
generic interceptor are stable. The initial request stores enough call,
interaction, and continuation identity to make the response idempotent, then
completes through a valid model/tool history representation.

The response operation transitions the interaction and attempts one
application-coordinated no-message continuation. Admission state and a durable
continuation identity prevent duplicates. The continuation applies the stored
response through the interceptor and reaches normal resolved/cancelled/failed
operation state.

Stop for user review if correct continuation requires restoring arbitrary
session snapshots, injecting provider-specific native history outside normal
core reconstruction, or replaying completed external side effects.

### Implementation decisions and open questions

- Decision: no synthetic user message.
- Decision: one response occurrence owns at most one continuation identity.
- Decision: admission failure preserves a manual continuation path.
- Open: approve deterministic pending tool/result continuation contract.

### Documentation

- Document suspended history representation, continuation identity,
  idempotency, restart, admission failure, and side-effect limits.
- Cross-link shared request execution and operation notification docs.

### Task checklist

- [ ] Approve pending history/continuation contract.
- [ ] Add suspended correlation and continuation identity.
- [ ] Add pending short-circuit path.
- [ ] Add response-triggered coordinated continuation.
- [ ] Add interceptor response consumption and terminal resolution.
- [ ] Add admission failure/manual Continue.
- [ ] Add restart, concurrency, cancellation, and side-effect tests.
- [ ] Add SDK/frontend real-backend coverage.
- [ ] Complete manual suspend/respond/continue checkpoint.
- [ ] Update specifications and documentation.

### Requirement verification

- Initial request completes with one suspended interaction.
- Response starts exactly one no-message continuation.
- Continuation applies approve/deny/form response and resolves the interaction.
- Restart/reconnect retains the response and continuation availability.
- Busy/reloading session produces no duplicate or unsafe start.

### Additional implementation verification

- Provider-native history rebuild preserves pending/continued tool identity.
- Stale continuation workers cannot overwrite newer session history.
- Cancellation after response but before start has explicit outcome.