# Bridge E2EE threat model

## Assets

- application request method, path, query, and headers;
- prompts, messages, tool inputs/results, attachments, and other request bodies;
- response status, headers, content, and content-bearing errors;
- long-term endpoint private keys;
- session keys and counters;
- peer trust records;
- recovery/reset state.

## Trusted components

- the supported frontend endpoint while uncompromised;
- the supported user server endpoint while uncompromised;
- platform secure storage to the degree guaranteed by each operating system;
- reviewed cryptographic libraries.

## Untrusted or partially trusted components

- bridge nodes;
- public edge/CDN/load balancer;
- network path;
- external identity, entitlement, quota, and usage services with respect to
  application content;
- logs, metrics, and support tooling;
- other tenants and bridge clients.

## Threats

### Passive relay inspection

A bridge operator or attacker reading bridge memory/logs must not recover
protected content.

### Active relay modification

Modification, insertion, deletion, reordering, truncation, or replay of
protected envelopes must be detected or fail safely.

### Peer impersonation

An attacker must not impersonate a registered server or authorized frontend
without the authenticated peer key and required access authorization.

### Low-entropy pairing code

The six-digit code must not be used directly as an encryption key or sufficient
offline key-derivation secret. It can authenticate/confirm a stronger
ephemeral exchange under a reviewed construction.

### Stolen pairing token or access grant

Authorization credentials alone must not reveal content keys. A stolen
credential may remain an authorization risk until expiry/revocation, but it
must not decrypt prior content.

### Replay

Captured envelopes must not be accepted outside their request/session/sequence
context.

### Downgrade

An attacker must not cause a required-E2EE connection to fall back to
plaintext, an older unsafe protocol, or a different unverified peer.

### Device or server loss

Loss, reinstall, or replacement must have explicit recovery behavior and must
not silently trust a new key.

### Compromised endpoint

E2EE cannot protect content from malware or an attacker controlling the
frontend or user server. This is an explicit non-goal.

### Metadata analysis

The design does not fully hide endpoint IPs, connection timing, traffic
volume, ciphertext sizes, or routing identifiers. Minimize metadata but
describe residual visibility honestly.

## Security review

Review covers:

- protocol construction and transcript binding;
- key derivation and domain separation;
- authenticated encryption and nonce/counter use;
- replay and reordering;
- pairing authentication;
- downgrade/version negotiation;
- multi-device behavior;
- secure storage and key deletion;
- error handling and side channels;
- test-vector correctness;
- implementation use of native/runtime cryptographic APIs.

Critical or high findings block implementation approval or production launch,
depending on when discovered.
