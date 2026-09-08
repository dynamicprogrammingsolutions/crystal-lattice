# Decision: Anthropic SDK transport

## Context

The provider could use the official Anthropic Python SDK or maintain a direct
HTTP/SSE implementation. The package must support official Anthropic and
Anthropic-compatible base URLs while preserving cancellation, native events,
provider errors, and later OAuth integration.

## Decision

Use the official Anthropic Python SDK for:

- Messages ordinary and streaming requests;
- model discovery;
- configured compatible base URLs;
- request authentication and version headers;
- provider-native event and error objects.

Normalize SDK objects into plain provider-native mappings at the package
boundary. Do not persist SDK objects. Implement request-ID cancellation by
closing or cancelling the active SDK stream/client operation.

The package does not maintain a parallel direct-HTTP Messages transport.

## Consequences

- The implementation aligns with the local `../pi` Anthropic provider and the
  supported SDK usage documented by compatible endpoints.
- Compatibility tests must prove that the SDK works with the selected Ollama
  profile.
- New provider fields may require SDK extra-field or raw-response access, but
  that is handled as an implementation refinement rather than a second
  transport.