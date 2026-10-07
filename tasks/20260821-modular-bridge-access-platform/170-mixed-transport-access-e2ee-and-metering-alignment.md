# Mixed Transport Access, E2EE, And Metering Alignment

Integrate access profiles, grants, pairing policy, E2EE, and metering with the
in-progress HTTP/hybrid transport without duplicating or weakening its
transport contracts.

## Requirements checklist

### Functional requirements

- [ ] **P1** — WebSocket, HTTP, and hybrid paths use one capability and access
  model and enforce equivalent identity, entitlement, quota, expiry, and E2EE
  decisions.
- [ ] **P1** — Static tokens, provider grants, pairing state, E2EE credentials,
  and backend authorization use distinct headers or envelopes.
- [ ] **P1** — Raw request and response byte accounting is complete and
  idempotent across all transport modes.
- [ ] **P1** — Transport versioning preserves compatible existing connections,
  and a request is never automatically replayed over another transport after
  it starts.

### Non-functional requirements

- [ ] **P1** — Edge proxies forward required credentials without caching,
  logging, or forwarding bridge credentials to the local backend.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
- `tasks/20260821-modular-bridge-access-platform/070-e2ee-implementation.md`
- `tasks/20260821-modular-bridge-access-platform/130-production-quota-metering-contracts-and-bridge-hooks.md`
- `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`

## Approved later-production boundary — October 7, 2026

140 supplies basic grant/ownership enforcement, authorization parity and
credential separation/redaction for the early demo. This task owns integrating
those decisions with 070's E2EE and 130's production quota/metering across all
transports. It is a prerequisite for the later commercial client and sandbox
deliveries in 160/220; it does not gate the limited hosted demo in 175.
The implementation plan remains Draft.

## Required reading

- The complete mixed-transport task and implementation branch
- Bridge access, quota, E2EE, and capability contracts from this umbrella
- CloudFront/HAProxy forwarding configuration

## Execution plan

Status: Draft

Rebase/reconcile the mixed-transport implementation, centralize credentials and
policy decisions in the shared bridge connection abstraction, make encrypted
payloads and usage hooks first-class in HTTP transfers, and expand the existing
transport matrix rather than adding parallel adapters.

Reuse 140's base verifier, ownership checks and credential handling. Add the
encrypted-path policy and production quota/usage enforcement previously
bundled with grant enforcement. Keep 040's basic demo allowances available
independently of this later integration.

### Implementation decisions and open questions

- `X-Crystal-Bridge-Token` remains the pairing token.
- Deployment/access-grant credentials use separate names or handshake fields.
- Application `Authorization` continues to reach the local backend.
- No transparent HTTP/WebSocket retry after a request starts.

### Documentation

- Consolidate protocol credential taxonomy, capabilities, mode behavior,
  E2EE, metering, edge requirements, and migration/rollback instructions.

### Task checklist

- [ ] Reconcile branches and shared transport interfaces.
- [ ] Apply common authentication and capabilities.
- [ ] Integrate E2EE envelopes and byte accounting.
- [ ] Update edge forwarding/redaction.
- [ ] Expand SDK, bridge, Python, cluster, mobile, and AWS tests.
- [ ] Update protocol and transport documentation.

### Requirement verification

- Run the complete transport/access/E2EE/limits matrix.
- Inspect edge and bridge logs for credentials/plaintext.
- Exercise cross-node raw transfers and reconnect.
- Verify old saved connections retain explicit compatibility behavior.
