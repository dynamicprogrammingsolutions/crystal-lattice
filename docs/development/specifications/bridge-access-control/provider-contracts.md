# Bridge access provider contracts

## Design goal

Providers are replaceable services or local implementations. The bridge uses
normalized contracts and does not import provider-specific authentication,
billing, database, or policy code.

## Identity and grant provider

Inputs:

- presented credential;
- subject type (`app` or `server`);
- requested bridge audience;
- optional server identity;
- deployment context.

Output:

- verified subject/account identity;
- signed access grant or a normalized grant payload for bridge-local signing;
- public expiration and reauthentication information;
- explicit public error.

Representative errors:

- `authentication_required`;
- `invalid_credential`;
- `account_disabled`;
- `server_not_owned`;
- `provider_unavailable`.

## Entitlement provider

Input:

- stable product account ID;
- requested entitlement key;
- environment.

Output:

- entitlement key;
- normalized status;
- effective and expiry times;
- source class without private payload;
- decision timestamp.

The provider hides store-specific receipts, purchase tokens, event payloads,
and operational fields.

## Quota provider

The quota provider:

- returns effective public limits or policy references;
- acquires and renews server/session/transfer leases;
- releases or expires leases idempotently;
- accepts idempotent usage batches;
- reports public limit state and reset/window information;
- keeps commercial thresholds and administrative policy private.

## Usage sink

Usage reporting is asynchronous and batched. A batch contains:

- stable batch ID;
- account/subject scope;
- bridge deployment/node identity;
- usage window or event time;
- transferred request and response bytes;
- relevant server/session/transfer identifiers;
- event count;
- checksum or signature as required.

Retries with the same batch ID do not double-count.

## Provider compatibility suite

The public repository supplies one contract suite used by:

- demo provider;
- fake provider;
- provider-unavailable fixture;
- hosted-style test adapter;
- community implementations.

The suite verifies schemas, expiry, idempotency, public errors, outage behavior,
and absence of provider-private fields. The suite is verification
infrastructure; provider implementation details are not part of this contract.
