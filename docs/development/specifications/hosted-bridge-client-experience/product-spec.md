# Hosted bridge client-experience product specification

## Product boundary

Crystal Lattice clients support connection choices with different account and
payment requirements:

| Connection | Account required | Subscription required | Operator |
| --- | --- | --- | --- |
| Direct local HTTP | no | no | user |
| Bonjour/local network | no | no | user |
| Custom self-hosted bridge | deployment policy | no Crystal Lattice hosted subscription | user/community |
| Crystal Lattice hosted bridge | yes | active hosted entitlement | Dynamic Programming Solutions |

The paid subscription unlocks only the operated hosted bridge. It does not
remove free direct or self-hosted functionality.

## Accounts and login

- Initial identity providers are Apple and Google.
- Mobile uses a system-browser OIDC Authorization Code + PKCE flow.
- Terminal/server supports device authorization for headless use.
- External identities link explicitly to one stable product account.
- Matching email alone never merges accounts.
- Email login may be added later without changing account or billing identity.

## Server ownership

A user can claim a stable local server ID under their product account. The
server receives revocable server-scoped credentials and short-lived bridge
registration grants. It does not store the user's mobile refresh token.

Ownership conflict, transfer, unclaim, replacement, deletion, and credential
revocation have explicit workflows.

## Subscription purchase

- iOS purchases use StoreKit.
- Android purchases use Google Play Billing.
- The client associates purchase attempts with the current product account.
- The hosted service verifies purchases authoritatively.
- Store-returned localized products, prices, and offers are displayed.
- The app does not direct a user to purchase through the other platform.

## Subscription access

Normalized statuses include:

- trial;
- active;
- grace;
- billing issue/retry;
- pending;
- cancelled but paid through;
- account hold or pause where applicable;
- expired;
- refunded/revoked;
- temporarily unavailable.

Hosted bridge access follows the normalized entitlement, E2EE policy, pairing
policy, ownership, and quota decisions. Store-specific internal payloads are
not shown to clients.

## Restore and cross-platform use

Restore/synchronize reconstructs entitlement through server verification.
After login, a valid purchase from either supported store provides the same
account entitlement on both mobile platforms, while each platform continues to
offer its native purchase mechanism.

## Trial and price

The technical sandbox launch does not enable the public introductory offer.
The public launch includes a store-managed trial; duration remains HBC-Q001.

The initial commercial direction is a monthly product around USD 10, but the
client always displays the localized value returned by the store. Exact
commercial configuration is not a public client protocol.

## Account deletion

The client:

- explains the effect on hosted access and retained records;
- offers platform-correct subscription management;
- supports immediate or scheduled product-account deletion as supplied by the
  hosted service;
- does not claim Apple billing is automatically cancelled/refunded;
- can request Google cancellation/revocation/refund through the hosted service
  where policy and API permit.

## Non-goals

- Email/password login in the initial release.
- Web checkout.
- Annual product in the initial release unless separately approved.
- Organization/team sharing.
- Hiding store/provider outages as successful entitlement.
