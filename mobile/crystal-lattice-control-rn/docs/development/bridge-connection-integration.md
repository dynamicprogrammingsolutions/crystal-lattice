# Bridge connection integration

This page describes how the mobile application integrates the shared bridge
transports: connection selection, pairing, saved-record reconstruction,
foreground recovery, and repair. The frontend SDK owns the transport
implementations and their portable contracts.

Bridge transports are created only through the frontend SDK's
`createBridgeConnectionTransport()` factory. Mobile supports:

| Selection | Mobile behavior |
| --- | --- |
| WebSocket | Compatibility default for discovery, pairing, events, and requests. |
| HTTP | Discovery, pairing, events, and requests through bridge HTTP v1; no frontend WebSocket. |
| Hybrid | HTTP discovery/pairing/normal requests and legacy WebSocket only for exact `GET /events`. |

HTTP and hybrid are labeled experimental. There is no automatic fallback.
Rollback means selecting WebSocket and constructing another transport.

Successful pairing stores a `BridgeConnectionRecord` with bridge URL, server
ID/name, pairing token, and the selected `transportMode`. The field is optional
for backward compatibility. All reconstruction sites resolve a missing mode to
the shared WebSocket default, so old records are not silently migrated.

Reopening a saved record supplies its server ID and pairing token to the mode
factory. Invalid token or server mismatch clears the stale token and opens the
repair flow. A temporarily absent server keeps the record available for
re-pairing when it returns.

Foreground recovery uses the structural `BridgeConnectionTransport` lifecycle:

1. call `prepareForResume()`;
2. reconnect/validate;
3. persist a changed pairing token if one is returned;
4. open repair when the server or credential is no longer valid.

`src/connectionInfo.ts` renders the effective mode in saved-connection details.
Stable production test IDs on the bridge method and mode selectors support the
focused iOS/Android Detox scenario.

Current evidence covers default selection plus explicit HTTP, hybrid, and
WebSocket rollback on both simulators. A shared helper used by `App.tsx` has
focused tests for absent, WebSocket, HTTP, and hybrid saved records while
preserving the same server identity and pairing token. Physical-device network
checks remain a gate before a separately approved default switch.

See the frontend SDK's
[bridge transport implementation](../../../../packages/frontend-sdk/docs/development/bridge-transport-implementation.md)
for mode-specific transport ownership. The cross-package
[bridge-connectivity frontend specification](../../../../docs/development/specifications/bridge-connectivity/frontend-behavior.md)
owns portable mode and migration behavior, while the mobile
[connection lifecycle specification](specifications/connection-lifecycle/index.md)
defines mobile lifecycle requirements.

Maintainer entry points:

- `App.tsx`
- `src/connectionInfo.ts`
- `src/bridgeConnection.ts`
- bridge connection and transport-mode component tests
- focused bridge transport Detox scenarios