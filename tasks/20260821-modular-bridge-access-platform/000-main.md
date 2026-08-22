# Modular Bridge Access Platform

Build a public, replaceable bridge access platform that secures user-deployed
bridges, supports configurable authentication and pairing, proves entitlement
and limit enforcement without production payment providers, adds end-to-end
encryption, and exposes stable contracts for separately operated hosted
services.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Bridge deployments support explicit, validated access profiles
  covering static-token authentication and configurable pairing policy across
  WebSocket, HTTP, and hybrid transports.
- [ ] **P1** — Public replaceable identity, entitlement, quota, usage, and
  scaling contracts are proven by working non-production implementations.
- [ ] **P1** — Public clients and bridge transports consume and enforce the
  same normalized identity, access-grant, entitlement, ownership, quota,
  E2EE, and usage contracts.
- [ ] **P2** — Public AWS deployment components expose the configuration,
  metrics, and lifecycle hooks needed by community and hosted deployments.

### Non-functional requirements

- [ ] **P1** — Hosted bridge content is end-to-end encrypted between the
  frontend and the user's server before production launch.
- [ ] **P1** — Public documentation and contracts preserve the public/private
  implementation boundary and do not expose private operational context.

## Subtasks

- [ ] `tasks/20260821-modular-bridge-access-platform/010-static-token-bridge-security.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/020-configurable-bridge-access-and-pairing-profiles.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/030-replaceable-access-providers-and-demo-challenge-service.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/040-demo-entitlement-limits-and-client-integration.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/050-demo-connection-autoscaling-and-load-harness.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/060-e2ee-protocol-and-threat-model.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/070-e2ee-implementation.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/130-production-quota-metering-contracts-and-bridge-hooks.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/150-terminal-server-login-and-ownership.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/160-mobile-login-purchase-and-subscription-ux.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/170-mixed-transport-access-e2ee-and-metering-alignment.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/180-public-aws-bridge-template-modularization.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/200-production-autoscaling-public-metrics-and-validation-tools.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/210-public-privacy-terms-store-and-e2ee-documentation.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/220-public-sandbox-integration-harness.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/230-public-trial-and-paid-release-client-readiness.md`
- [ ] `tasks/20260821-modular-bridge-access-platform/240-community-operations-and-provider-runbook.md`

## Related existing work

- **COMPLETED BASELINE:**
  `tasks/20260421-distribution-release-workstreams/055-aws-fargate-external-bridge.md`
  supplies stateless pairing tokens, public AWS bridge deployment, clustering,
  optional CPU autoscaling, and guarded AWS smoke tests.
- **SUPERSEDED IN PART:**
  `tasks/20260516-auth-notifications-staged-rollout/030-authentik-auth-integration.md`
  remains useful for OIDC, PKCE, and JWKS decisions, but authentication for
  bridge access is owned here independently of notification work.
- **OVERLAP / TRACKED DEPENDENCY:**
  `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
  owns the mixed WebSocket/HTTPS transport implementation. Its access,
  transfer, and capability contracts must be aligned here rather than
  duplicated.

## Scope and ownership

This public umbrella owns the bridge, SDK, mobile, terminal/server, E2EE,
provider interfaces, reference/demo providers, public tests, and community
deployment components.

Production account databases, payment-provider server adapters, commercial
entitlement administration, private infrastructure composition, fraud
operations, and customer-support tooling are supplied by a separately operated
hosted service. Public code communicates with that service only through
versioned, documented contracts and public keys.

The demo profile is the required proof that the replaceable contracts support
trial access, challenge-earned access, tiered limits, expiration, and
enforcement before production providers are integrated.

## Required reading

- `bridge-elixir/AGENTS.md`
- `bridge-elixir/docs/index.md`
- `packages/frontend-sdk/README.md`
- `mobile/crystal-lattice-control-rn/AGENTS.md`
- `application/python/AGENTS.md`
- `tasks/20260421-distribution-release-workstreams/055-aws-fargate-external-bridge.md`
- `tasks/20260516-auth-notifications-staged-rollout/030-authentik-auth-integration.md`
- `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
- `docs/development/repository/specifications.md`

## Specifications and requirements

- `docs/development/specifications/bridge-connectivity/index.md`
  (`BRG-015` through `BRG-020`)
- `docs/development/specifications/bridge-access-control/index.md`
  (`BAC-001` through `BAC-017`)
- `docs/development/specifications/bridge-e2ee/index.md`
  (`BEE-001` through `BEE-013`)
- `docs/development/specifications/hosted-bridge-client-experience/index.md`
  (`HBC-001` through `HBC-015`)

## Execution plan

Status: Draft

Implement the platform as independently useful vertical increments. Start with
static-token protection and deployment policy so current user-deployed bridges
are secure without waiting for accounts or payment. Add a deliberately
non-production external provider and limits implementation next, proving the
replaceable service boundary before production integrations exist. Design and
implement E2EE before making hosted-service claims. Then add public identity,
ownership, quota, client, transport, deployment, and release contracts.

The bridge remains an HTTP-agnostic relay. It consumes normalized access grants
and quota decisions; it does not import Apple, Google, Authentik tenant, or
commercial account implementation code. Public defaults remain useful for
self-hosters and fail safely when a selected security profile is incomplete.

### Implementation decisions and open questions

- `local-open` is explicit local/development behavior and cannot silently
  result from missing production credentials.
- The first static-token implementation uses one deployment-level token for
  trusted app and server clients; later role-specific credentials may refine
  this without changing the transport contract.
- Pairing is either required or disabled per deployment when another
  authentication mechanism is active. Production hosted pairing remains a
  later operational decision.
- The demo provider is intentionally unsuitable for production and must be
  rejected by production configuration without an explicit test override.
- Hosted production requires E2EE. Community deployments may choose whether to
  require it.
- Exact commercial limits, quota windows, AWS region, and EC2 versus Fargate
  remain outside this public umbrella's decisions.

### Documentation

- Create or update a cross-package target specification when the first
  implementation subtask begins, with stable requirements for security
  profiles, provider contracts, E2EE, and compatibility.
- Keep bridge protocol and deployment documentation with `bridge-elixir`.
- Keep frontend transport contracts with `packages/frontend-sdk`.
- Keep mobile and terminal user workflows with their owning applications.
- Public documentation describes delivered behavior only and does not mention
  private task paths, production topology, fraud rules, or internal operations.

### Task checklist

- [ ] Approve and execute each subtask independently.
- [ ] Keep this main checklist synchronized with subtask completion evidence.
- [ ] Reconcile overlapping transport work before modifying shared HTTP/hybrid
  protocol files.
- [ ] Preserve public/private source and audience boundaries throughout.
- [ ] Record material protocol, cryptography, persistence, and compatibility
  decisions in the owning specification.

### Requirement verification

- Static-token deployments reject unauthenticated app and server clients over
  every supported transport.
- Demo-provider E2E proves replaceable identity, entitlement, limits, expiry,
  and access grants without production services.
- E2EE tests prove the relay cannot read protected request and response
  contents.
- Community and hosted-style access grants exercise the same public bridge
  enforcement contract.
- Public AWS tests prove cluster compatibility, metrics, draining, and
  configurable providers without production credentials.
- Public mobile and terminal tests prove login, ownership, subscription-state,
  pairing-policy, and error UX at their public boundaries.
