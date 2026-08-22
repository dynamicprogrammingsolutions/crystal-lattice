# Hosted bridge frontend behavior

## Account states

The client distinguishes:

- signed out;
- authenticating;
- signed in;
- token refresh required;
- provider unavailable;
- account disabled;
- deletion scheduled/in progress;
- account conflict requiring explicit linking or support.

Raw access/refresh tokens are never displayed.

## Connection chooser

Free direct and self-hosted choices remain visible without hosted login.

The hosted bridge choice:

1. requests login when signed out;
2. obtains current account/entitlement;
3. presents purchase/restore when no entitlement exists;
4. obtains a short-lived bridge access grant;
5. follows E2EE and pairing capability requirements;
6. shows public quota state and useful denial errors.

## Identity linking

Linking a second provider requires:

- an authenticated current account;
- a fresh authentication with the provider being linked;
- explicit confirmation;
- conflict behavior if that identity already belongs to another account.

No automatic email-based merge occurs.

## Purchase and restore

Purchase UI:

- loads native-store product/offer details;
- displays localized title, duration, price, trial, renewal, privacy, and terms
  information required by the platform;
- disables duplicate purchase actions while one is pending;
- handles user cancellation separately from failure;
- waits for authoritative entitlement synchronization before claiming hosted
  access.

Restore:

- queries the platform purchase history/current purchases;
- sends relevant purchase identity to the hosted verification path;
- refreshes normalized entitlement;
- does not attach a purchase to a different product account silently.

## Subscription presentation

The UI shows a public state and appropriate action:

| State | Presentation/action |
| --- | --- |
| trial/active | access available; renewal or expiry information |
| grace | access available with billing warning |
| billing issue/account hold | access policy and manage-subscription action |
| pending | purchase pending; no duplicate purchase |
| cancelled-paid-through | access through effective expiry |
| expired | renew/purchase/restore |
| refunded/revoked | access removed; support/manage action |
| unavailable | retry/status explanation; no false inactive claim |

## Pairing

Capabilities determine whether hosted access:

- requires the existing pairing-code flow; or
- connects under account ownership without pairing.

The client does not hardcode the production choice.

## Limits

Public errors distinguish:

- server limit;
- concurrent-session limit;
- concurrent-transfer limit;
- request/response size;
- transfer-window warning or hard limit;
- administrative suspension.

Commercial internal thresholds or reasons are not exposed unless approved for
public display.

## Logout

Logout:

- clears account and hosted credentials from secure storage;
- ends or disables hosted connections;
- leaves unrelated direct/self-hosted connection data intact;
- follows defined E2EE key retention/removal behavior.

## Account deletion

The client presents:

- subscription-management warning;
- immediate versus scheduled deletion choices supplied by the service;
- Apple refund-request/manage-subscription flow;
- Google cancellation/refund result where supported;
- retained-record disclosure;
- confirmation before destructive action.

## Accessibility and localization

Login, paywall, restore, manage, limits, deletion, and pairing controls have
stable accessibility identifiers and localized user-facing strings. Store
prices and offer terms come from the store rather than hardcoded formatting.
