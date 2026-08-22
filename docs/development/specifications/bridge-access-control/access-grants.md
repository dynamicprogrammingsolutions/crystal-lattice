# Bridge access grants

## Purpose

An access grant is a short-lived signed statement that lets the bridge validate
identity, entitlement, ownership scope, and effective limits without calling a
provider for every proxied request.

## Required claims

Conceptual claims:

```json
{
  "version": 1,
  "type": "bridge_access",
  "issuer": "https://issuer.example",
  "audience": "crystal-lattice-bridge",
  "subject": "stable-subject",
  "subject_type": "app",
  "account_id": "product-account-uuid",
  "entitlements": ["bridge_access"],
  "server_scope": ["server-id"],
  "quota_policy": "policy-reference",
  "issued_at": 1787000000,
  "expires_at": 1787000900,
  "grant_id": "unique-id",
  "key_id": "signing-key-id"
}
```

Exact serialization and signature format remain an open design decision.

## Validation

The bridge validates:

- supported version and type;
- signature and key ID;
- issuer and audience;
- issued-at/not-before/expiration;
- subject type;
- stable subject/account identifiers;
- entitlement requirement;
- server ownership/scope;
- grant ID where revocation or replay policy requires it.

Invalid grants do not create protected side effects.

## App and server grants

App grants authorize discovery, pairing according to policy, resume, and
requests under the subject's visible server scope.

Server grants authorize registration and reconnect for an owned server ID.
They do not contain or reuse the user's mobile refresh token.

## Expiration and revocation

- Grants are intentionally short-lived.
- Long-lived sockets reauthenticate or close at expiration.
- Provider-driven revocation may close connections earlier.
- The documented grant lifetime bounds worst-case revocation delay.
- Signing-key rotation supports an overlap period with multiple public keys.

## Storage

Access grants are credentials:

- mobile stores them in credential-appropriate secure storage when persistence
  is required;
- terminal/server stores server-scoped credentials separately from ordinary
  profile data;
- bridge logs, connection records, errors, and diagnostics do not contain raw
  grant values.
