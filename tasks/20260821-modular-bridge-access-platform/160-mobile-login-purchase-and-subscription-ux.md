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

## Required reading

- Mobile `AGENTS.md`, `README.md`, connection flow, deep links, and navigation
- Apple StoreKit subscription and account-deletion guidance
- Google Play Billing subscription, security, and account-deletion guidance
- Public account, entitlement, access-grant, and error schemas

## Execution plan

Status: Draft

Add account and subscription screens/services behind public interfaces, then
connect native StoreKit/Play Billing purchase results to server-side
verification. Keep hosted paywall behavior separate from free direct and
self-hosted connection choices.

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

- [ ] Add account/session service and screens.
- [ ] Add Apple/Google login/linking UX.
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
