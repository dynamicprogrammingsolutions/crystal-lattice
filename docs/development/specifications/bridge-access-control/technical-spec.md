# Bridge access-control technical specification

## Architecture

```text
App or server client
    │
    ├── deployment credential / identity credential
    ▼
Access provider or local verifier
    │
    ├── normalized access grant
    └── quota/lease decisions
    ▼
Bridge effective-policy layer
    │
    ├── registration/discovery/pairing/resume authorization
    ├── session/transfer quota enforcement
    └── transport-specific carrier supplied by bridge connectivity
```

The bridge evaluates one normalized effective policy regardless of transport.
Transport handlers adapt WebSocket or HTTP input into the same authorization
context before protected behavior executes.

## Subjects

Supported subject types:

- `app`: a frontend client acting for a product account;
- `server`: a registered Crystal Lattice server owned by a product account;
- `deployment`: a trusted client authenticated only by a static deployment
  token;
- `demo`: a non-production subject issued by the demo provider.

A provider may use other internal identities, but it maps them to these public
roles and a stable subject/account identifier.

## Effective policy

The effective policy includes:

- access profile;
- accepted credential type;
- pairing required or disabled;
- entitlement requirement;
- quota provider and policy reference;
- E2EE required, optional, or disabled;
- transport modes;
- grant issuer/audience/key set;
- provider outage behavior.

Startup constructs and validates this policy. Invalid combinations fail startup
instead of falling back to weaker behavior.

## Authorization boundaries

Policy is evaluated before:

- app or server channel use;
- server registration;
- server discovery;
- pairing request or confirmation;
- pairing resume/validation;
- session creation/resume;
- proxied application requests;
- HTTP transfer creation;
- quota lease acquisition.

Transfer-body endpoints continue to use direction-scoped transfer credentials
issued only after the parent request passes access checks.

## Capability negotiation

The HTTP and WebSocket capability surfaces expose the same public fields:

```json
{
  "access": {
    "profile": "static-token",
    "static_token_required": true,
    "pairing_required": true,
    "entitlement": "disabled",
    "limits": "local",
    "e2ee": "optional"
  }
}
```

The exact transport framing is owned by bridge connectivity. Capabilities do
not expose secrets, servers, sessions, account records, internal provider
names, or commercial thresholds.

## Credential taxonomy

- Deployment access token: long-lived deployment secret supplied to trusted
  app and server clients.
- Pairing token: signed logical app/server pairing credential.
- Access grant: short-lived signed subject/account/entitlement authorization.
- Transfer token: short-lived direction-scoped request-body or response-body
  credential.
- Backend authorization: application header forwarded to the user's local
  server and never interpreted as bridge authentication.

Credential values are never interchangeable.

## Provider failure

Local/static-token profiles do not depend on external providers.

For hosted-style access:

- unverifiable new access fails closed;
- an existing connection may continue only until its verified grant and lease
  expire;
- usage batches may queue only within a strict bounded buffer;
- provider recovery reconciles pending usage and current entitlement;
- no provider outage silently switches to open/static-token behavior.

The exact bounded grant/lease duration remains an implementation decision.

## Long-lived connections

The bridge records the verified grant expiration on the socket/session context.
Before or at expiry, the client must reauthenticate with a current grant or the
connection closes. Revocation can take effect earlier through provider-driven
notification, but the maximum revocation delay cannot exceed the documented
grant lifetime.

## Compatibility and migration

- Existing saved pairing records can be used only when the selected profile
  still accepts them.
- A policy mismatch produces an explicit repair/login/pairing flow.
- Old bridges that do not advertise access capabilities require explicit
  compatibility mode.
- A hosted profile does not reinterpret a legacy pairing token as account
  identity.
