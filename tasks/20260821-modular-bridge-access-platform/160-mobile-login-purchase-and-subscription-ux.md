# Mobile Login, Purchase, And Subscription UX

Add public React Native account, purchase, restore, entitlement, management,
and deletion experiences while keeping server-side store verification behind
replaceable hosted contracts.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Users can sign in with Apple and Google and explicitly link
  identities.
- [ ] **P1** — Mobile purchase flows display store-provided localized products
  and prices and associate completed purchases with the current canonical
  account for server verification.
- [ ] **P1** — Restore and entitlement synchronization reconstruct the account
  subscription state and represent all supported lifecycle statuses.
- [ ] **P1** — Manage-subscription, logout, and account-deletion UX is
  platform-correct.
- [ ] **P1** — Direct and self-hosted connections remain available without a
  subscription, while hosted access requires current login, entitlement,
  policy, and E2EE.

### Non-functional requirements

- [ ] **P1** — Sensitive credentials use secure storage and do not leak into
  logs, diagnostics, or ordinary connection records.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`
- `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`
- Production store/control-plane contracts supplied through the public API

## Approved ownership clarification — October 7, 2026

The requirement checklist remains intact. Base login/logout/account-switch
and identity-link UI is owned by
`tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`.
Credit it here only after that task supplies evidence. This task owns the
additional purchase, restore, subscription management, paywall and associated
account-deletion presentation. It stays pending; scope approval is not delivery.

The free hosted demo is owned by
`tasks/20260821-modular-bridge-access-platform/175-hosted-demo-and-invited-tester-release.md`
and does not wait for this purchase implementation. Public commercial trial
presentation remains gated by 230.

## Required reading

- Mobile `AGENTS.md`, `README.md`, connection flow, deep links, and navigation
- Apple StoreKit subscription and account-deletion guidance
- Google Play Billing subscription, security, and account-deletion guidance
- Public account, entitlement, access-grant, and error schemas

## Execution plan

Status: Draft

Reuse the base account/session UI and OIDC clients delivered by 080. Add
subscription screens/services behind public interfaces and connect native
StoreKit/Play Billing results to server verification. Keep commercial paywall
behavior separate from the authenticated free demo and direct/self-hosted
choices.

### Implementation decisions and open questions

- Initial purchase provider is the native store on each platform.
- Apple/Google cross-platform entitlement is account-based after server
  verification; the app does not steer users to another platform's payment.
- Email login remains deferred without changing account schemas.
- Public trial presentation is deferred until release Task 230.

### Documentation

- Document login/linking, purchase, restore, status, management, deletion,
  hosted versus self-hosted access, and troubleshooting.

### Task checklist

- [ ] Verify and credit the base account/session service and screens from 080.
- [ ] Verify and credit Apple/Google login/linking UX from 080.
- [ ] Add StoreKit and Play Billing clients.
- [ ] Add purchase association, verification, restore, and refresh.
- [ ] Add subscription/paywall/status/management UI.
- [ ] Add logout and platform-correct deletion UX.
- [ ] Gate hosted connection while preserving free modes.
- [ ] Add tests, accessibility labels, and documentation.

### Requirement verification

- Run mocked and real sandbox purchase/restore flows on both platforms.
- Verify cross-platform entitlement through the same account.
- Verify expired/refunded/pending/grace states and offline/provider errors.
- Verify non-subscribers can still use direct and self-hosted connections.
- Verify account deletion warnings and platform-specific management links.
