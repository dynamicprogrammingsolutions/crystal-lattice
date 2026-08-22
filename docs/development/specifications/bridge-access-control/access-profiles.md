# Bridge access profiles

## Profile contract

Each deployment selects one explicit access profile. A profile defines required
credentials, pairing, entitlement, limits, and E2EE policy.

| Profile | Authentication | Pairing | Entitlement | Limits | E2EE | Intended use |
| --- | --- | --- | --- | --- | --- | --- |
| `local-open` | none | required | none | local safety | optional | local development and explicitly trusted networks |
| `static-token` | deployment token | required or disabled | none | local/configured | optional | user-deployed trusted single-user or small trusted group |
| `demo-challenge` | demo access grant | required or disabled | demo trial/challenge | demo provider | optional | architecture and lifecycle testing only |
| `hosted-style` | external app/server access grant | configurable pending BAC-Q001 | required | external distributed provider | required for production | separately operated hosted service |

## `local-open`

- Must be selected explicitly.
- Pairing is required.
- Internet-facing or production configuration rejects this profile unless an
  explicit unsafe development override is present.
- Missing credentials never cause another profile to fall back to
  `local-open`.

## `static-token`

- Requires a configured deployment token.
- The same deployment may require pairing or disable it.
- With pairing disabled, a token holder can discover and connect to registered
  servers in that deployment.
- The first implementation may use one token for trusted app and server
  clients; future role-specific credentials may refine this without changing
  the profile's required outcome.

## `demo-challenge`

- Uses the public access-grant contract.
- Recognizes one configured non-production demo subject.
- Provides a configurable first-use trial with a 24-hour reference default.
- Five correct arithmetic answers grant the base demo tier.
- Ten correct answers grant a higher demo tier.
- Grant duration and usage-window duration are independent.
- The provider is not secure authentication and is rejected in production
  unless an explicit unsafe test override is present.

## `hosted-style`

- Requires valid app and server subjects under product accounts.
- Requires the configured hosted entitlement.
- Applies external distributed quotas.
- Requires E2EE in production.
- Pairing policy remains open until BAC-Q001 is resolved.
- A pairing token never replaces a current access grant.

## Startup validation

Startup rejects at least:

- unknown profile;
- required static token missing;
- pairing disabled with no other authentication;
- hosted-style profile without issuer/audience/JWKS configuration;
- hosted-style profile without entitlement provider;
- hosted production with E2EE disabled or unavailable;
- demo provider in production without an explicit test override;
- advertised HTTP/hybrid support without compatible routes.
