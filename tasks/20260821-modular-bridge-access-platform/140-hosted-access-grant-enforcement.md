# Hosted Access-Grant Enforcement

Make the public bridge validate normalized short-lived access grants and
enforce subject, server ownership, entitlement, pairing policy and
demo allowances without importing hosted account or billing code.

## Requirements checklist

### Functional requirements

- [ ] **P1** — App and server grants validate signature, issuer, audience,
  time, subject type, and unique identifier before protected access.
- [ ] **P1** — Server registration, discovery, pairing, resume, and request
  access enforce account ownership, entitlement, pairing policy, and subject
  isolation.
- [ ] **P1** — Long-lived connections reauthenticate or close when grants
  expire or are revoked within the documented bound.

### Non-functional requirements

- [ ] **P1** — WebSocket, HTTP, and hybrid paths enforce equivalent
  authorization decisions and return consistent authorization errors.
- [ ] **P1** — Bridge/account credentials, pairing tokens, and backend
  authorization remain distinct. Edge proxies do not cache credentials;
  bridge credentials are not logged or forwarded as backend authorization.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/040-demo-entitlement-limits-and-client-integration.md`
- `tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`

## Approved early-demo boundary — October 7, 2026

This task supplies the basic authenticated grant/ownership path used by
`tasks/20260821-modular-bridge-access-platform/175-hosted-demo-and-invited-tester-release.md`.
It consumes 040's demo allowance enforcement and 080's account/client contracts.
E2EE and production quota/metering integration are owned by
`tasks/20260821-modular-bridge-access-platform/170-mixed-transport-access-e2ee-and-metering-alignment.md`
after 070/130. They do not gate this task or the limited hosted demo.
The implementation plan remains Draft.

## Required reading

- Bridge socket/channels, pairing token, session manager, server registry
- Public access-grant and account/ownership schemas
- Mixed transport capability and HTTP authorization paths

## Execution plan

Status: Draft

Add a hosted-style access profile that consumes only public signed grants and
provider contracts. Bind identity to every server/session/pairing boundary,
enforce expiry on long-lived connections, and retain local/static-token
profiles without hosted dependencies.

Apply the same verifier and account/server checks to every supported
WebSocket/HTTP/hybrid entry point. Enforce the existing demo allowances and
keep bridge, pairing and backend credentials distinct through edge forwarding.
Verify redaction in the base path. Later encrypted and production-metered paths
reuse these decisions through 170.

Hosted-grant enforcement is active only in the selected hosted-style profile.
Self-hosted local and static-token profiles remain the regression baseline and
must not acquire a hosted-service runtime dependency.

### Implementation decisions and open questions

- New hosted-style connections fail closed when grants cannot be verified.
- Existing connections last no longer than their verified grant and demo
  allowance.
- Pairing token alone never restores hosted access without current identity and
  entitlement.
- Production pairing enablement remains an operator configuration.

### Documentation

- Document claim requirements, ownership, expiry/reauthentication, revocation,
  demo allowances, credential separation/redaction, errors, profile isolation,
  and provider test setup. Identify the later encrypted/metered integration
  owned by 170.

### Task checklist

- [ ] Add grant verifier/JWKS cache and key rotation.
- [ ] Authenticate app and server subjects.
- [ ] Bind registration, discovery, pairing, resume, and proxy to ownership.
- [ ] Enforce entitlement and demo allowances through the 040 contracts.
- [ ] Separate bridge/pairing/backend credentials and verify forwarding/redaction.
- [ ] Add expiry timers and reauthentication.
- [ ] Add cross-account, tamper, outage, and compatibility tests.
- [ ] Update protocol and deployment documentation.

### Requirement verification

- Reject forged, expired, wrong-audience, wrong-subject-type, and cross-account
  grants.
- Terminate or reauthenticate long-lived sockets at expiry.
- Prove pairing/resume cannot bypass current entitlement.
- Run equivalent authorization scenarios over all transports.
- Verify credential separation and edge/bridge log redaction over the actual
  forwarding paths; bridge credentials never become backend authorization.
- Verify local/static-token deployments start and operate with no hosted
  provider.
