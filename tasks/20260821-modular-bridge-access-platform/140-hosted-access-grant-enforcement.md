# Hosted Access-Grant Enforcement

Make the public bridge validate normalized short-lived access grants and
enforce subject, server ownership, entitlement, pairing policy, quota, and
E2EE requirements without importing hosted account or billing code.

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

- [ ] **P1** — WebSocket, HTTP, hybrid, and E2EE paths enforce equivalent
  authorization decisions and return consistent authorization errors.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`
- `tasks/20260821-modular-bridge-access-platform/130-production-quota-metering-contracts-and-bridge-hooks.md`

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

Hosted-grant enforcement is active only in the selected hosted-style profile.
Self-hosted local and static-token profiles remain the regression baseline and
must not acquire a hosted-service runtime dependency.

### Implementation decisions and open questions

- New hosted-style connections fail closed when grants cannot be verified.
- Existing connections last no longer than their verified grant/lease.
- Pairing token alone never restores hosted access without current identity and
  entitlement.
- Production pairing enablement remains an operator configuration.

### Documentation

- Document claim requirements, ownership, expiry/reauthentication, revocation,
  errors, profile isolation, and provider test setup.

### Task checklist

- [ ] Add grant verifier/JWKS cache and key rotation.
- [ ] Authenticate app and server subjects.
- [ ] Bind registration, discovery, pairing, resume, and proxy to ownership.
- [ ] Enforce entitlement, E2EE, and quota claims.
- [ ] Add expiry timers and reauthentication.
- [ ] Add cross-account, tamper, outage, and compatibility tests.
- [ ] Update protocol and deployment documentation.

### Requirement verification

- Reject forged, expired, wrong-audience, wrong-subject-type, and cross-account
  grants.
- Terminate or reauthenticate long-lived sockets at expiry.
- Prove pairing/resume cannot bypass current entitlement.
- Run equivalent authorization scenarios over all transports.
- Verify local/static-token deployments start and operate with no hosted
  provider.
