# Bridge access-control product specification

## Purpose

A bridge URL is an address, not authorization. An Internet-reachable bridge
must be able to reject unknown app and server clients before they register,
discover servers, pair, resume, or relay application requests.

The platform must support:

- a simple static-token path for user-deployed bridges;
- explicit local development behavior;
- replaceable identity, entitlement, quota, and usage services;
- a non-production demo profile that proves the architecture before production
  providers exist;
- a hosted-style profile that consumes normalized account and entitlement
  decisions without importing commercial service code.

## User and operator outcomes

### User-deployed bridge

An operator can configure one deployment token and provide it to trusted app
and server clients. A person who only knows the bridge URL cannot use protected
bridge operations.

The operator may keep pairing as an additional app/server authorization step or
disable pairing when another authentication mechanism is sufficient. The
selected behavior is explicit and discoverable through capabilities.

### Local development

Local development can retain an explicitly selected open profile. Open access
must never result from a missing production credential or unknown profile.

### Replaceable services

The bridge does not need to know how a provider authenticated a person, sold a
subscription, calculated a quota, or stored usage. It consumes normalized
access grants and quota decisions.

Community operators can implement compatible providers. The public repository
includes demo and fake providers to prove the contracts.

### Hosted-style access

A hosted-style deployment can require:

- a current authenticated app or server subject;
- server ownership under the same product account or approved scope;
- the `bridge_access` entitlement;
- configured pairing policy;
- current quota leases;
- required E2EE support.

The account, purchase, and commercial policy implementation remains outside
the bridge process.

## Access failures

Clients receive explicit failures that distinguish at least:

- static token required or invalid;
- login required;
- access grant expired or invalid;
- entitlement required or expired;
- server not owned or not visible;
- pairing required or invalid;
- server/session/transfer/data limit reached;
- provider temporarily unavailable;
- E2EE required or incompatible.

Errors expose actionable public state without leaking account internals,
commercial thresholds, secrets, or provider implementation detail.

## Compatibility

- Existing local and static-token deployments do not require hosted services.
- The compatibility WebSocket mode remains usable.
- HTTP and hybrid modes enforce the same effective policy.
- A pairing token alone cannot restore hosted-style access after identity or
  entitlement expires.
- Application `Authorization` remains available to the local backend.

## Non-goals

- Defining commercial prices or quota values.
- Defining a universal identity provider.
- Making the demo arithmetic challenge secure authentication.
- Storing account, purchase, or entitlement records in the bridge.
- Replacing E2EE with transport TLS.
- Hiding authorization logic as a security mechanism.
