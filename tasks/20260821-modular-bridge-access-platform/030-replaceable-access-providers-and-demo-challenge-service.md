# Replaceable Access Providers And Demo Challenge Service

Introduce a small public provider contract and a working non-production access
service that proves identity, trial, entitlement, limit selection, and
short-lived access grants can be replaced independently of bridge transport.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Identity, entitlement, limit selection, access-grant issuance,
  and provider availability are replaceable independently of bridge routing.
- [ ] **P1** — The non-production demo provider issues configurable first-use
  trial access and challenge-earned base and higher-limit access tiers.
- [ ] **P1** — Access-grant duration and usage-window duration are
  independently configurable.

### Non-functional requirements

- [ ] **P1** — Access grants are signed, audience-bound, expiring,
  tamper-resistant, and usable without a provider call for every proxied
  request.
- [ ] **P1** — Production configuration rejects the demo provider unless an
  explicit unsafe test-only override is set.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On: `tasks/20260821-modular-bridge-access-platform/020-configurable-bridge-access-and-pairing-profiles.md`

## Required reading

- `core/python/agent_core/types.py` and public plugin/Protocol style for
  repository conventions
- `bridge-elixir/lib/bridge/pairing_token.ex`
- `cloud-orchestrator/lib/cloud_orchestrator/token.ex`
- Authentik OIDC/JWKS concepts in
  `tasks/20260516-auth-notifications-staged-rollout/docs/authentik-auth-concepts.md`

## Supporting details

The demo service is a replaceability and lifecycle test, not real
authentication. It may recognize a single configured demo subject and issue:

- a 24-hour default first-use trial;
- a base grant after five correct simple arithmetic answers;
- a higher-limit grant after ten correct answers.

A fake replacement provider must pass the same public contract suite, and the
provider-author documentation must show how another implementation replaces the
demo service without changing bridge or client protocols.

Tests use injected clocks and short durations. Demo defaults for servers,
concurrent sessions, and transfer allowance are configuration examples, not
commercial commitments.

The normalized grant should include subject, subject type, entitlement keys,
limit policy or values, issuer, audience, issued/expiry times, and a unique
identifier. Use public-key verification or an explicitly replaceable signing
boundary so production key rotation does not require a protocol redesign.

## Execution plan

Status: Draft

Define the smallest stable provider and grant contracts, then implement a
standalone demo service plus in-process fake for tests. Add a `demo-challenge`
profile only after it can issue and verify grants. Keep transport, bridge
authorization, and production store semantics outside the provider.

### Implementation decisions and open questions

- The demo challenge is intentionally automatable and must never be described
  as secure authentication or anti-abuse protection.
- A simple persistent store is required so trial/expiry behavior survives
  service restart during realistic tests; the storage implementation is not a
  production contract.
- Exact challenge operations and demo limits are local reversible choices.
- The production provider can be a separate service as long as it implements
  the public grant contract.

### Documentation

- Add provider-contract, access-grant, demo quickstart, test-clock, and
  replacement guides.
- Mark every demo path non-production in API responses and UI.

### Task checklist

- [ ] Define public provider and grant schemas.
- [ ] Implement signing, verification, expiry, audience, and key-set support.
- [ ] Implement trial issuance.
- [ ] Implement five- and ten-question challenge tiers.
- [ ] Add configurable grant and usage windows.
- [ ] Add persistent demo state and deterministic clock seams.
- [ ] Add fake/provider-unavailable implementations.
- [ ] Add contract, lifecycle, tamper, and restart tests.
- [ ] Add documentation and production-use guards.

### Requirement verification

- Prove first-use trial issuance and expiry.
- Prove five versus ten correct answers yield distinct limit tiers.
- Reject incomplete, wrong, replayed where prohibited, expired, wrong-audience,
  and tampered grants.
- Replace the demo provider with the fake without bridge protocol changes.
- Verify production configuration rejects the demo implementation.
