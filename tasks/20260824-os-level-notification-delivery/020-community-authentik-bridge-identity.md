# Community Authentik Bridge Identity

Provide a reproducible optional Authentik deployment and public community
identity/account implementation that self-deployed bridges can use for account
login, stable server ownership, access grants, and notification routing.

## Requirements checklist

### Functional requirements

- [ ] Community operators can deploy and configure Authentik using public
  repository-owned deployment and user documentation.
- [ ] The deployment supports configurable login sources, including Apple and
  Google when operator credentials are supplied.
- [ ] Mobile clients can use Authorization Code with PKCE against the
  configured issuer.
- [ ] Terminal/headless clients can use an appropriate public-client flow.
- [ ] External Authentik identities map explicitly to stable community account
  IDs; email matching alone never merges accounts.
- [ ] A logged-in community account can claim, unclaim, and transfer a stable
  Crystal server ID under explicit conflict rules.
- [ ] Account and server identity can be consumed by notification device
  routing.
- [ ] Logout, identity unlinking, account disablement/deletion, server
  transfer, and credential revocation have explicit behavior.
- [ ] The community identity implementation issues normalized public access
  grants consumed by bridge authorization.
- [ ] Local, pairing-only, and static-token bridge profiles continue working
  without Authentik.
- [ ] Backup, restore, issuer/client configuration, signing-key rotation, and
  recovery are documented and verifiable.

### Non-functional requirements

- [ ] The implementation depends only on public modular bridge contracts and
  contains no private hosted-service references.
- [ ] Authentik-specific behavior remains behind replaceable identity and
  access-provider boundaries.
- [ ] Mobile and terminal are public clients and contain no embedded client
  secrets.
- [ ] Authentik, social-provider, database, and signing credentials are
  excluded from Git, ordinary logs, and deployment output.
- [ ] Authenticated profiles fail closed when issuer, keys, account mapping, or
  grant issuance is unavailable.
- [ ] Unauthenticated community profiles remain operational when Authentik is
  disabled.
- [ ] Deployment guidance distinguishes development defaults from secure
  internet-facing operation.
- [ ] Restart, backup/restore, upgrade, key rotation, and revocation receive
  realistic automated and manual verification.

Parent Task:
`tasks/20260824-os-level-notification-delivery/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/030-replaceable-access-providers-and-demo-challenge-service.md`
- `tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`
- `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`
- `tasks/20260821-modular-bridge-access-platform/150-terminal-server-login-and-ownership.md`

Coordinates With:

- `tasks/20260821-modular-bridge-access-platform/170-mixed-transport-access-e2ee-and-metering-alignment.md`

## Open requirement questions

1. Which deployment form is the first supported community baseline?
   - Recommendation: a documented Docker Compose deployment with explicit
     external-secret and production-hardening paths; add Helm only when a
     concrete operator need justifies it.
2. Where should the minimal community account/ownership/grant adapter run?
   - Recommendation: package it as a replaceable public service adjacent to
     Authentik/bridge rather than embedding account state into the bridge
     relay.
3. Which identity sources are mandatory for deterministic acceptance?
   - Recommendation: deterministic local OIDC fixtures plus one real Authentik
     source; Apple/Google setup remains supported/manual because credentials
     and review are operator-owned.

## Supporting facts

- The public modular bridge task defines replaceable provider, account,
  identity-link, grant, bridge enforcement, and server ownership contracts.
- Authentik authenticates external identities but a separate account mapping
  is required because provider subject/email is not the canonical product
  account identity.
- The public bridge should validate normalized grants rather than importing
  Authentik tenant/account logic.
- The earlier notification/auth task proposed direct Authentik JWT validation
  but did not separate identity, account ownership, and bridge enforcement.

## Execution plan

Status: Draft

First define the community deployment profile and the smallest durable
community account/identity/grant service implementing the public modular
contracts. Keep Authentik as the OIDC identity authority while the community
service owns stable account IDs, identity links, server ownership, revocable
credentials, and grant issuance.

Add public-client configuration for mobile PKCE and terminal/headless login,
then integrate server claim/ownership and bridge grant enforcement through the
existing public tasks. Package reproducible development and hardened community
deployment examples without embedding secrets.

Validate with deterministic issuer/account fixtures, a real local Authentik
deployment, all supported bridge transports covered by the modular task, and
backup/restore/key-rotation scenarios.

Stop for user review if the minimal community service grows into commercial
entitlement, billing, organization/team, or support administration scope.

### Implementation decisions and open questions

- Decision: Authentik owns authentication; the community service owns stable
  accounts and server ownership.
- Decision: the bridge remains an access-grant consumer, not an Authentik
  account database.
- Decision: no commercial entitlement is required for community access.
- Open: approve deployment form, service placement, and acceptance identity
  sources.

### Documentation

- Document deployment topology, DNS/TLS, providers, clients, secrets, account
  mapping, server claiming, profiles, backup/restore, rotation, upgrades, and
  troubleshooting.
- Keep protocol and replaceability contracts in the public modular bridge
  documentation.
- Replace the old Authentik concept/task guidance with current public
  community instructions when delivered.

### Task checklist

- [ ] Approve deployment and community account-service boundaries.
- [ ] Define the community provider/account/grant profile.
- [ ] Add reproducible Authentik and durable service deployment.
- [ ] Configure mobile PKCE and terminal/headless clients.
- [ ] Implement identity linking and stable account bootstrap.
- [ ] Implement server claim/ownership and revocable credentials.
- [ ] Issue and verify normalized bridge access grants.
- [ ] Add disable/delete/revocation and transfer behavior.
- [ ] Add deterministic, local Authentik, transport, and recovery tests.
- [ ] Complete operator manual deployment and recovery checkpoint.
- [ ] Publish public community documentation.

### Requirement verification

- A community operator deploys the stack and completes mobile and terminal
  login.
- Two external identities can link explicitly to one stable account while
  unsafe email merge is rejected.
- A server is claimed by one account and wrong-account takeover fails.
- Revocation prevents new authenticated bridge access within the documented
  bound.
- Local/static/pairing profiles operate with the Authentik stack absent.

### Additional implementation verification

- Signing-key rotation supports overlapping verification.
- Backup restore preserves account/ownership identity and rejects stale
  credentials as designed.
- Production-profile validation rejects insecure default secrets and
  development-only configuration.