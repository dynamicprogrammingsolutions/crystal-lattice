# Bridge access control

This specification defines the portable access-control target shared by the
bridge service, frontend SDK, mobile and desktop hosts, the terminal/server
client, and replaceable identity, entitlement, quota, and usage providers.

## Specification documents

- [Product behavior](product-spec.md)
- [Technical architecture](technical-spec.md)
- [Access profiles](access-profiles.md)
- [Provider contracts](provider-contracts.md)
- [Access grants](access-grants.md)
- [Quota and usage](quota-and-usage.md)
- [Requirements and live state](requirements.md)
- [Decisions and open questions](decisions.md)

## Ownership

| Responsibility | Owner |
| --- | --- |
| Effective bridge access policy and profile validation | `bridge-elixir` |
| WebSocket, HTTP, and hybrid credential carriage | [Bridge connectivity](../bridge-connectivity/index.md) |
| Shared frontend access configuration and capability consumption | `packages/frontend-sdk` |
| Mobile credential entry, secure storage, and pairing presentation | `mobile/crystal-lattice-control-rn` |
| Terminal/server credential configuration and server grants | `application/python/agent_terminal_app` |
| Identity, entitlement, quota, usage, and access-grant decisions | Replaceable external providers |
| E2EE key establishment and protected envelopes | [Bridge E2EE](../bridge-e2ee/index.md) |
| Hosted login and subscription presentation | [Hosted bridge client experience](../hosted-bridge-client-experience/index.md) |

This specification owns the meaning of credentials and authorization
decisions. Bridge connectivity owns how those credentials and decisions cross
the supported transports.

## Scope

The target includes:

- deployment-level static-token authentication;
- explicit access profiles and startup validation;
- pairing-required and pairing-disabled behavior;
- public capability negotiation;
- replaceable identity, entitlement, quota, usage, and access-grant providers;
- app and server subjects;
- product-account and server ownership;
- short-lived signed access grants;
- grant expiration, reauthentication, and bounded revocation;
- distributed quota leases and usage reporting;
- consistent enforcement over WebSocket, HTTP, and hybrid transports;
- compatibility with local and self-hosted deployments.

## Exclusions

This specification does not define:

- WebSocket, HTTP, hybrid, proxy, or transfer framing;
- E2EE algorithms, handshake, key storage, or encrypted envelope format;
- Apple or Google purchase verification;
- Authentik production tenant configuration;
- commercial quota values;
- AWS runtime selection or production topology;
- mobile paywall copy or store-review operations.

## Requirement questions

### BAC-Q001 — Production pairing policy

Status: Open

Does hosted production require pairing in addition to account authentication,
or is account/server ownership sufficient?

The answer changes the production user flow and required authorization checks.
The implementation must remain configurable until demo, E2EE, and security
evidence supports a decision.

Decision required before:

- enabling the production hosted access profile;
- finalizing hosted connection UX;
- public launch.

## Relationship to tasks

Primary delivery tracking:

- `tasks/20260821-modular-bridge-access-platform/010-static-token-bridge-security.md`
- `tasks/20260821-modular-bridge-access-platform/020-configurable-bridge-access-and-pairing-profiles.md`
- `tasks/20260821-modular-bridge-access-platform/030-replaceable-access-providers-and-demo-challenge-service.md`
- `tasks/20260821-modular-bridge-access-platform/040-demo-entitlement-limits-and-client-integration.md`
- `tasks/20260821-modular-bridge-access-platform/130-production-quota-metering-contracts-and-bridge-hooks.md`
- `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`
- `tasks/20260821-modular-bridge-access-platform/150-terminal-server-login-and-ownership.md`
- `tasks/20260821-modular-bridge-access-platform/170-mixed-transport-access-e2ee-and-metering-alignment.md`
