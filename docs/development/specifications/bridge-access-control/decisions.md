# Bridge access-control decisions and open design questions

## Approved decisions

### BAC-D001 — Explicit profile selection

Status: Approved

The initial public profile set is:

- `local-open`;
- `static-token`;
- `demo-challenge`;
- `hosted-style`.

There is no prepackaged `community-external` profile. Community operators can
attach compatible providers through the public contracts.

### BAC-D002 — Pairing is independent from authentication

Status: Approved

Pairing can be required or disabled when another authentication mechanism is
active. `local-open` requires pairing. Hosted production policy remains open in
BAC-Q001.

### BAC-D003 — Demo provider precedes production providers

Status: Approved

The demo challenge provider and limits are implemented before production
identity, billing, and quota providers. It proves provider replacement,
entitlement expiry, tiered limits, configurable windows, and access grants.

The reference demo recognizes one configured non-production subject and starts
with a 24-hour first-use trial. Tests may use shorter injected durations.

## Open design decisions

### BAC-D004 — WebSocket deployment-token carrier

Status: Open

Required outcome:

- authenticate before protected channel behavior;
- do not put the long-lived token in a logged URL;
- support React Native, desktop/browser constraints, and Python;
- preserve proxy/edge redaction.

Options include a WebSocket header, subprotocol, redacted socket parameter, or
mandatory initial authentication exchange.

Decision trigger: compatibility spike in Task 010.

### BAC-D005 — Access-grant signature format

Status: Open

Required outcome:

- offline bridge verification;
- issuer/audience/expiry/key ID;
- public key rotation;
- interoperable provider implementations.

Options include a standard JWT/JWS profile or another versioned signed
structure. Decide before hosted-style grant enforcement.

### BAC-D006 — Provider outage grace

Status: Open

Required outcome:

- no unbounded access;
- no fallback to weaker profile;
- bounded continuity for already verified connections where approved;
- deterministic reconciliation.

Decide grant lifetime, lease lifetime, and any outage grace before production
hosted deployment.
