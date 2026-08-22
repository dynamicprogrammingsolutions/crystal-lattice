# Hosted bridge client-experience technical specification

## Public account model

Conceptual account:

```json
{
  "account_id": "product-account-uuid",
  "status": "active",
  "identities": [
    {"issuer": "https://issuer", "subject": "provider-sub", "provider": "apple"}
  ],
  "deletion": null
}
```

Email may be display/contact data but is not the canonical key.

## Entitlement model

Conceptual entitlement:

```json
{
  "key": "bridge_access",
  "status": "active",
  "source_platform": "apple",
  "effective_at": "timestamp",
  "expires_at": "timestamp",
  "will_renew": true,
  "public_action": "manage_subscription"
}
```

The public response excludes receipts, purchase tokens, original transaction
payloads, RTDN payloads, provider-private status, fraud signals, and
administrative notes.

## OIDC clients

Mobile:

- Authorization Code + PKCE;
- system browser;
- state and nonce validation;
- registered application redirect;
- refresh token only when approved scopes permit;
- Keychain/Keystore-backed storage.

Terminal/server:

- device authorization by default for headless use;
- loopback/browser alternative only when supported safely;
- server-scoped credential issuance after account authentication;
- no mobile refresh-token reuse.

## Purchase association

The hosted service supplies a stable non-PII billing-link identifier:

- Apple purchase uses it as `appAccountToken`;
- Google purchase derives the approved obfuscated account identifier;
- purchase claim/verification occurs under the currently authenticated account.

The client treats purchase completion as pending until the hosted service
returns current entitlement.

## Bridge access grant

The client requests a short-lived public bridge access grant after login and
entitlement refresh. It supplies the grant through the transport carrier owned
by bridge connectivity and access control.

Grant refresh:

- occurs before expiry or on explicit reauthentication signal;
- does not retry an uncertain proxied application request;
- closes hosted access when refresh cannot produce a valid grant.

## Secure storage

Secure storage contains:

- OIDC refresh/access state as appropriate;
- hosted bridge access grant when persistence is necessary;
- deployment static token;
- E2EE endpoint key/trust records according to the E2EE specification.

Ordinary connection records contain non-secret identifiers and references, not
raw credentials.

## Error taxonomy

Public errors cover:

- authentication and identity linking;
- account disabled/deletion;
- purchase/restore;
- entitlement lifecycle;
- access-grant expiry/revocation;
- ownership;
- pairing;
- E2EE;
- quotas;
- provider unavailability;
- bridge/local backend transport.

Errors do not include raw store or provider payloads.
