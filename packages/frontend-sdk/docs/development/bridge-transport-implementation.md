# Bridge transport implementation

## Public boundary

`BridgeConnectionTransport` combines the normal `Transport` request method with
connection, pairing, identity, and resume lifecycle methods.

`createBridgeConnectionTransport()` is the mode boundary:

- absent or `websocket` returns `BridgeTransport`;
- `http` returns `HttpBridgeTransport`;
- `hybrid` returns `HybridBridgeTransport`.

Keep mode-specific behavior in those implementations. In particular, do not
add HTTP branches to the compatibility `BridgeTransport`.

## Compatibility WebSocket transport

`BridgeTransport` owns:

- Phoenix app WebSocket creation and channel join;
- pairing and ephemeral-session resume;
- heartbeat and suspect-socket validation;
- pending reply correlation;
- UTF-8 request chunking and response reassembly;
- request timeout and socket-reset decisions.

The transport serializes ordinary object bodies to JSON strings. It switches
to the legacy chunk events above its configured threshold and keeps streaming
response state separate from normal Phoenix replies.

## HTTP transport

`HttpBridgeTransport` owns:

- bridge HTTP-origin derivation/override;
- version-1 capability negotiation;
- HTTP discovery, pairing, and resume validation;
- pairing-token authentication;
- body conversion and response parsing;
- timeout controllers and disconnect abortion.

HTTP discovery and control use JSON. Proxy bodies remain raw fetch bodies.
`X-Crystal-Bridge-Body-Present` preserves the distinction between no body and
a present zero-length body.

`prepareForResume()` sets a validation flag. The next request validates before
proxying even if the host has not called `connect()` again.

## Hybrid composition

`HybridBridgeTransport` owns one HTTP transport and lazily constructs one
legacy transport from the HTTP transport's current server ID and pairing
token.

`isLegacyEventRequest()` is the only routing predicate. Control methods always
delegate to HTTP. Pairing completion discards any old legacy child and creates
a new one with the new credential.

The legacy child receives the same timeout, heartbeat, WebSocket factory, and
logging options as a directly constructed compatibility transport.

## Persistence boundary

`BridgeConnectionRecord.transportMode` is optional. Consumers must apply the
factory default rather than rewriting old stored records. The SDK connection
record owns data shape; each host owns storage and reconstruction.

## Error and retry policy

Each transport reports its own failure. Hybrid does not catch an HTTP request
failure and resubmit through the legacy child. This protects non-idempotent
requests and keeps rollout defects visible.

The host may construct a new WebSocket-mode transport after the failed request
has terminated.

## Tests

Focused unit tests cover:

- URL derivation;
- HTTP discovery, pairing, resume, JSON, and binary bodies;
- resolved timeout and abortion;
- exact hybrid matching;
- factory default and explicit modes;
- no fallback;
- legacy request/chunking, heartbeat, reconnect, and timeout behavior.

`src/integration/__tests__/bridge.e2e.integration.test.ts` is the assembled
production-adapter boundary. It should retain one representative case for
legacy payloads, HTTP raw payloads, hybrid routing, restart, and legacy
concurrency rather than duplicating internal state-machine matrices.

The cross-package
[bridge-connectivity technical specification](../../../../docs/development/specifications/bridge-connectivity/technical-spec.md)
owns the complete architecture and verification boundary.
