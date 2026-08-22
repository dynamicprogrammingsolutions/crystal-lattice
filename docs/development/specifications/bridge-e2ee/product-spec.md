# Bridge E2EE product specification

## Product promise

When E2EE is required and active, application requests and responses sent
through the bridge are encrypted between the Crystal Lattice frontend and the
user's registered Crystal Lattice server. The relay routes ciphertext and
cannot read protected content.

This promise applies to:

- prompts and messages;
- application paths and query strings;
- forwarded application headers;
- request bodies and attachments;
- response status, headers, bodies, and content-bearing errors.

## Endpoints

The cryptographic endpoints are:

- the user's frontend device running the supported Crystal Lattice client;
- the user's registered server running the supported Crystal Lattice server
  adapter.

The bridge, load balancer, CDN/edge, access provider, quota provider, and hosted
control plane are not cryptographic endpoints for application content.

## Visible metadata

The bridge may observe the minimum needed to route and operate the service:

- protocol and envelope version;
- deployment and connection/session routing identity;
- request identifier;
- ciphertext/chunk sequence and length;
- timestamps and connection duration;
- app/server network metadata available at transport boundaries;
- usage bytes and operational failures that do not include protected content.

Public documentation must distinguish protected content from visible metadata.

## User behavior

- New secure pairings establish or authenticate endpoint keys.
- Required E2EE cannot be silently downgraded.
- A peer-key change produces an explicit trust/re-pairing flow.
- Users can remove/reset local keys and re-pair.
- Unpair, logout, account deletion, and server replacement apply the defined
  key-deletion behavior.
- Multiple devices have independent or explicitly shared authorized key state
  according to the final protocol decision.

## Deployment behavior

- Hosted production requires E2EE.
- Community deployments may require, allow, or disable E2EE.
- Capabilities report the effective policy.
- A client that cannot satisfy a required policy is denied before protected
  application traffic.

## Claim boundary

The eventual public claim may state that the hosted bridge cannot read
protected application content only after:

- the protocol is approved;
- cross-language test vectors pass;
- implementation is complete;
- an independent review has no unresolved critical/high finding;
- relay-side capture proves only ciphertext reaches the bridge.

The claim does not promise traffic-analysis resistance or protection from
compromised endpoints.
