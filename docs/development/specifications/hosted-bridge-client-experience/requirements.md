# Hosted bridge client-experience requirements

All requirements are not started. Verification and documentation evidence is
added by the implementing tasks.

| ID | Priority | Requirement | Implementation | Verification | Documentation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| HBC-001 | P1 | Direct local, Bonjour/local-network, and custom self-hosted bridge connections remain available without a Crystal Lattice hosted subscription. | Not started | Unverified | Pending | — |
| HBC-002 | P1 | Mobile supports Apple and Google login through OIDC Authorization Code + PKCE, and terminal/server supports device authorization for headless login. | Not started | Unverified | Pending | — |
| HBC-003 | P1 | Apple and Google identities link explicitly to stable product accounts; email matching alone never merges accounts or defines ownership/billing identity. | Not started | Unverified | Pending | — |
| HBC-004 | P1 | Users can claim, unclaim, replace, and transfer stable server IDs through explicit account-bound workflows using revocable server-scoped credentials. | Not started | Unverified | Pending | — |
| HBC-005 | P1 | iOS and Android purchase flows display store-provided localized products/offers and associate purchase attempts with the current canonical account for server verification. | Not started | Unverified | Pending | — |
| HBC-006 | P1 | Restore and entitlement synchronization reconstruct authoritative account access without silently attaching one purchase to another account. | Not started | Unverified | Pending | — |
| HBC-007 | P1 | The client represents trial, active, grace, billing issue, pending, cancelled-paid-through, hold/pause, expired, refunded/revoked, and unavailable subscription states with appropriate actions. | Not started | Unverified | Pending | — |
| HBC-008 | P1 | Hosted access requires current login, `bridge_access` entitlement, server ownership/scope, effective pairing policy, quota approval, and required E2EE. | Not started | Unverified | Pending | — |
| HBC-009 | P1 | Valid Apple or Google purchases produce the same product-account entitlement on supported clients while each platform continues to use its native purchase mechanism. | Not started | Unverified | Pending | — |
| HBC-010 | P1 | Manage-subscription, logout, and account-deletion flows are platform-correct and explain continued Apple billing/refund limits and supported Google cancellation/refund behavior. | Not started | Unverified | Pending | — |
| HBC-011 | P1 | OIDC, store-association, access-grant, static-token, and E2EE credentials use secure storage and are excluded from ordinary connection persistence, logs, errors, and diagnostics. | Not started | Unverified | Pending | — |
| HBC-012 | P1 | Capabilities drive pairing, E2EE, transport, and limit presentation rather than hardcoded hosted deployment assumptions. | Not started | Unverified | Pending | — |
| HBC-013 | P1 | Login, purchase, restore, subscription, pairing, limits, management, and deletion controls meet approved accessibility and localization behavior. | Not started | Unverified | Pending | — |
| HBC-014 | P1 | Store review and support paths allow authorized reviewers/users to exercise a reliable hosted bridge without exposing private operational credentials. | Not started | Unverified | Pending | — |
| HBC-015 | P1 | Public privacy, terms, product pages, store disclosures, support, and account-deletion URLs distinguish free/self-hosted and paid hosted behavior, match implemented data/E2EE/subscription behavior, and exclude private operational detail. | Not started | Unverified | Pending | — |
