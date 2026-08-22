# Hosted bridge client experience

This specification defines the public account, login, subscription, server
ownership, and hosted-connection behavior shared by mobile, desktop, terminal,
and public hosted-service APIs.

## Specification documents

- [Product behavior](product-spec.md)
- [Frontend behavior](frontend-behavior.md)
- [Technical contracts](technical-spec.md)
- [Requirements and live state](requirements.md)
- [Decisions and open questions](decisions.md)

## Ownership

| Responsibility | Owner |
| --- | --- |
| Portable user-visible hosted-bridge experience | This specification |
| Mobile login, purchase, restore, paywall, and connection UX | `mobile/crystal-lattice-control-rn` |
| Terminal login, server claim, and server credential UX | `application/python/agent_terminal_app` |
| Public account/identity/entitlement/access-grant DTOs | Shared public contracts |
| Bridge authorization and pairing policy | [Bridge access control](../bridge-access-control/index.md) |
| E2EE status and key/reset presentation | [Bridge E2EE](../bridge-e2ee/index.md) |
| Store verification and commercial state | Separately operated hosted service |

## Scope

- free direct, local-network, and custom self-hosted bridge connections;
- account login with Apple and Google;
- explicit identity linking;
- stable product accounts;
- terminal/server login and ownership;
- native-store purchase and restore;
- cross-platform entitlement;
- hosted bridge gating;
- trial and subscription status;
- pairing-policy presentation;
- limits/status errors;
- manage subscription, logout, and account deletion;
- secure credential storage;
- accessibility, localization, review, and support behavior.

## Exclusions

- Apple/Google server-side purchase verification.
- Commercial database and event implementation.
- Exact quota values.
- E2EE protocol internals.
- Production AWS topology.
- Future web checkout.

## Requirement questions

### HBC-Q001 — Public introductory-trial duration

Status: Open

The public offer includes a store-managed trial. Seven days is the current
recommendation; the exact duration is approved before store-product
configuration.

### HBC-Q002 — Production pairing presentation

Status: Open

The client supports pairing required and disabled. The production hosted
setting follows BAC-Q001.

## Relationship to tasks

- `tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`
- `tasks/20260821-modular-bridge-access-platform/150-terminal-server-login-and-ownership.md`
- `tasks/20260821-modular-bridge-access-platform/160-mobile-login-purchase-and-subscription-ux.md`
- `tasks/20260821-modular-bridge-access-platform/210-public-privacy-terms-store-and-e2ee-documentation.md`
- `tasks/20260821-modular-bridge-access-platform/220-public-sandbox-integration-harness.md`
- `tasks/20260821-modular-bridge-access-platform/230-public-trial-and-paid-release-client-readiness.md`
