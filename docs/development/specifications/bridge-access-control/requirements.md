# Bridge access-control requirements

All requirements are not started. Verification and documentation evidence is
added by the implementing tasks.

| ID | Priority | Requirement | Implementation | Verification | Documentation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| BAC-001 | P1 | A configured static-token profile requires the correct deployment token before app or server clients use protected WebSocket, HTTP, or hybrid bridge operations; missing or invalid tokens create no protected side effect. | Not started | Unverified | Pending | — |
| BAC-002 | P1 | Health and minimal capability discovery remain unauthenticated without exposing protected server, session, secret, account, or commercial-policy data. | Not started | Unverified | Pending | — |
| BAC-003 | P1 | Mobile and terminal/server clients can configure and reuse a deployment token, and persisted values use credential-appropriate secure storage. | Not started | Unverified | Pending | — |
| BAC-004 | P1 | Access profiles are explicit and startup rejects missing, unknown, unsafe, or internally inconsistent authentication, pairing, entitlement, provider, transport, or E2EE configuration. | Not started | Unverified | Pending | — |
| BAC-005 | P1 | HTTP and WebSocket capability negotiation expose the same effective transport and access policy, and clients use that policy when constructing or repairing connections. | Not started | Unverified | Pending | — |
| BAC-006 | P1 | Identity, entitlement, quota, usage, and access-grant providers are replaceable independently of bridge routing and pass one public compatibility contract. | Not started | Unverified | Pending | — |
| BAC-007 | P1 | Demo access supports a configurable first-use trial, challenge-earned base and higher-limit tiers, independent grant/usage windows, and a production-use guard. | Not started | Unverified | Pending | — |
| BAC-008 | P1 | Access grants are signed, issuer/audience-bound, expiring, key-rotatable, subject/account-scoped, and validated before protected bridge behavior. | Not started | Unverified | Pending | — |
| BAC-009 | P1 | Server registration, visibility, pairing, resume, and request access enforce product-account ownership, entitlement, pairing policy, and cross-account isolation. | Not started | Unverified | Pending | — |
| BAC-010 | P1 | Long-lived hosted-style connections reauthenticate or close at grant expiration, and revocation takes effect within the documented bounded interval. | Not started | Unverified | Pending | — |
| BAC-011 | P1 | Server, session, and transfer quota leases are atomic, expiring, renewable, releasable, and idempotent across retries, reconnect, and node loss. | Not started | Unverified | Pending | — |
| BAC-012 | P1 | Usage batches are bounded, idempotent, retryable, compatible with arbitrary quota windows, and meter WebSocket, HTTP, hybrid, and E2EE relay traffic consistently. | Not started | Unverified | Pending | — |
| BAC-013 | P1 | Provider outage behavior is bounded: new hosted-style access fails closed, existing work lasts no longer than verified grants/leases, and usage buffering is limited and reconcilable. | Not started | Unverified | Pending | — |
| BAC-014 | P1 | Deployment tokens, access grants, pairing tokens, transfer tokens, and backend authorization remain distinct and are excluded from inappropriate URLs, logs, errors, diagnostics, persistence, forwarding, and caching. | Not started | Unverified | Pending | — |
| BAC-015 | P1 | Local and static-token deployments operate without hosted-service dependencies, and selecting a hosted-style profile does not reinterpret legacy pairing credentials as account identity. | Not started | Unverified | Pending | — |
| BAC-016 | P2 | Public access and quota errors provide actionable client state without exposing account internals, provider-private payloads, commercial thresholds, or administrative rules. | Not started | Unverified | Pending | — |
| BAC-017 | P2 | Community operators can deploy supported profiles, attach replacement providers, rotate/reset credentials and E2EE trust, diagnose failures, and understand security/data-retention responsibilities through validated public guidance that excludes private hosted operations. | Not started | Unverified | Pending | — |
