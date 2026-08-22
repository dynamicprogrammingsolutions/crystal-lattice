# Public Sandbox Integration Harness

Provide public, credential-safe integration tooling for exercising Apple and
Google sandbox purchase results through account entitlement, access grants, and
hosted-style bridge access.

## Requirements checklist

### Functional requirements

- [ ] **P1** — The harness targets fake/local, external sandbox, and hosted test
  environments through production adapters without embedding environment
  credentials.
- [ ] **P1** — Apple and Google purchase fixtures and normalized events are
  sanitized and legally redistributable.
- [ ] **P1** — The harness exercises complete purchase, restore, renewal,
  cancellation, expiration, grace, pending, refund/revocation, and
  cross-platform entitlement lifecycles and proves corresponding hosted-access
  activation and denial.
- [ ] **P1** — E2EE, pairing policy, quotas, and WebSocket, HTTP, and hybrid
  transports participate in the same end-to-end scenarios.

### Non-functional requirements

- [ ] **P1** — Real store/API execution requires explicit environment gates,
  reports gated skips as not run, and redacts credentials, transaction
  payloads, and personal data from logs and reports.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`
- `tasks/20260821-modular-bridge-access-platform/160-mobile-login-purchase-and-subscription-ux.md`
- Store/control-plane sandbox endpoints implementing the public contracts

## Specifications and requirements

- `docs/development/specifications/hosted-bridge-client-experience/index.md`:
  `HBC-005` through `HBC-009`, `HBC-014`
- `docs/development/specifications/bridge-access-control/index.md`:
  `BAC-008` through `BAC-013`
- `docs/development/specifications/bridge-e2ee/index.md`:
  `BEE-006`, `BEE-012`

## Required reading

- Existing frontend SDK integration harness and provider selection
- iOS TestFlight and Android Play internal-testing task packages
- Apple StoreKit testing and Google Play Billing test guidance
- Public account/entitlement/access-grant schemas

## Execution plan

Status: Draft

Add deterministic local adapters and gated external-sandbox adapters to one
public E2E harness. Reuse production mobile/SDK/backend adapters and public APIs;
do not add test-only product shortcuts.

### Implementation decisions and open questions

- Public tests may know product IDs and public endpoints, but never store keys
  or administrative credentials.
- Real sandbox execution evidence is environment-specific and is not committed
  if it contains sensitive data.

### Documentation

- Document setup variables, gates, commands, expected lifecycle, cleanup,
  evidence boundaries, and troubleshooting.

### Task checklist

- [ ] Add sanitized lifecycle fixtures and fake adapter.
- [ ] Add external sandbox adapter interfaces.
- [ ] Add mobile/backend/bridge E2E scenarios.
- [ ] Add cross-platform and revocation scenarios.
- [ ] Add gates, redaction, cleanup, and reports.
- [ ] Add documentation.

### Requirement verification

- Run deterministic lifecycle suite in CI.
- Run gated Apple and Google sandbox scenarios when credentials/testers exist.
- Verify requested tests collect and execute rather than silently skip.
- Inspect output for secrets and personal data.
