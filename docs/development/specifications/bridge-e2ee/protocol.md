# Bridge E2EE protocol target

The exact reviewed protocol construction and cipher suite remain open. This
page fixes the required transcript, envelope, and interoperability properties
that any selected construction must satisfy.

## Protocol layers

```text
Access authorization
    └── establishes that app/server subjects may interact

Authenticated E2EE handshake
    └── establishes peer identity and shared session key material

Encrypted application envelope
    └── protects HTTP-shaped request/response metadata and body bytes

Bridge connectivity envelope
    └── routes opaque ciphertext over WebSocket, HTTP, or hybrid transport
```

Access authorization and encryption are independent. A valid access grant does
not become a content key, and a valid E2EE key does not bypass authorization.

## Handshake requirements

The handshake:

- authenticates the frontend and registered server peer keys;
- binds deployment/server/client identity and protocol version;
- uses fresh ephemeral contribution for forward-secrecy properties supported
  by the selected construction;
- incorporates the pairing confirmation without deriving security solely from
  the six-digit code;
- prevents relay substitution and unknown-key-share attacks;
- yields direction-separated keys;
- produces a transcript or peer fingerprint suitable for explicit confirmation
  and diagnostics without exposing secret material.

## Encrypted request envelope

Protected fields include:

- method;
- path and query;
- application headers;
- body presence and content metadata;
- request body chunks;
- content-bearing request errors.

Associated/routing data may include:

- envelope version;
- routing session/pairing context;
- request ID;
- direction;
- chunk sequence;
- final/cancel marker;
- ciphertext length.

Associated data is authenticated even when not encrypted.

## Encrypted response envelope

Protected fields include:

- status;
- application response headers;
- response body chunks;
- content-bearing errors.

Response messages bind to the originating request and direction.

## Streaming

- Each stream has an ordered sequence space.
- Duplicate, missing, reordered beyond allowed buffering, or replayed chunks
  fail the request.
- Cancellation and terminal markers are authenticated.
- No nonce/key reuse occurs across directions, requests, sessions, or key
  epochs.
- The bridge may meter ciphertext bytes but does not interpret plaintext size
  metadata beyond what transport framing necessarily reveals.

## Reconnect and resume

Reconnect:

- revalidates access authorization;
- reuses long-term peer trust only according to key-lifecycle policy;
- establishes fresh session keys;
- does not replay an uncertain non-idempotent request automatically;
- rejects changed peer keys until explicit repair/re-pairing.

## Version negotiation

- Capabilities advertise supported E2EE versions and required policy.
- Required E2EE rejects peers with no mutually supported approved version.
- Version negotiation is transcript-bound.
- Plaintext downgrade is prohibited when either effective policy or saved
  trusted state requires E2EE.

## Algorithms and test vectors

The selected implementation must use an established maintained construction
and libraries available for React Native/native mobile and Python.

Machine-readable vectors cover:

- handshake transcript;
- key derivation;
- request/response envelope encryption;
- streaming/chunk sequence;
- replay rejection;
- wrong peer/context;
- tampering;
- version/downgrade behavior.
