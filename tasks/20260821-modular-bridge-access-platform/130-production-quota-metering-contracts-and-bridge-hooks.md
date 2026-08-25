# Production Quota/Metering Contracts And Bridge Hooks

Define public distributed quota, lease, and usage contracts and make the bridge
enforcement path replaceable without publishing commercial values or hosted
storage implementation.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Public schemas cover server limits, concurrent sessions,
  concurrent transfers, request/response size, and transfer-window allowances.
- [ ] **P1** — Session and transfer lease acquisition, renewal, release, and
  expiry are explicit and idempotent.
- [ ] **P1** — Usage is reported through bounded, idempotent, retryable batches
  that meter WebSocket, HTTP, and hybrid traffic consistently across arbitrary
  quota windows.
- [ ] **P1** — Provider outage and delayed usage reporting have bounded,
  explicit behavior.

### Non-functional requirements

- [ ] **P1** — Public quota behavior and errors expose actionable limit state
  without exposing commercial thresholds, administrative policy, or account
  internals.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/040-demo-entitlement-limits-and-client-integration.md`
- `tasks/20260821-modular-bridge-access-platform/070-e2ee-implementation.md`

## Required reading

- Demo limit implementation from Task 040
- Bridge session/transfer lifecycle
- Mixed-transport raw-byte flow
- Public access-grant schema

## Execution plan

Status: Draft

Generalize the proven demo limits into versioned provider contracts and
production-capable bridge hooks. Keep counters and commercial policy external,
but ensure the bridge can reserve capacity and report usage without a
per-chunk synchronous service call.

Demo, fake, and hosted-style quota providers must pass the same reusable
contract suite. Provider-author and maintainer documentation remains part of
task delivery rather than a separate product requirement.

### Implementation decisions and open questions

- Hard caps reject new work rather than interrupting a valid in-progress
  request unless safety requires termination.
- Usage windows are provider-defined and not assumed monthly.
- Existing access may continue only within bounded cached grants/leases during
  provider outage; new hosted-style access fails closed.

### Documentation

- Publish schemas, semantics, retries, idempotency, error codes, outage
  behavior, examples, and contract-test instructions.

### Task checklist

- [ ] Finalize quota/lease/usage schemas.
- [ ] Add bridge provider interfaces and batching.
- [ ] Meter all transport and E2EE ciphertext paths correctly.
- [ ] Implement demo/fake adapters and contract suite.
- [ ] Add outage, retry, duplicate, expiry, and cleanup tests.
- [ ] Add provider and maintainer documentation.

### Requirement verification

- Run one contract suite against demo, fake, and hosted-style test adapters.
- Prove retries do not double-count usage.
- Prove cluster nodes enforce shared decisions rather than node-local limits.
- Prove provider outage behavior and recovery are bounded.
