# Bridge transports

The frontend SDK exposes one bridge connection interface with three explicit
transport modes. HTTP is the product default; WebSocket and hybrid remain
explicit development diagnostic choices.

## Create a bridge transport

```ts
import {
  createBridgeConnectionTransport,
  type BridgeTransportMode,
} from '@crystal-lattice/frontend-sdk';

const mode: BridgeTransportMode = 'http';

const bridge = createBridgeConnectionTransport({
  bridgeUrl: 'wss://bridge.example/ws/websocket',
  mode,
  serverId: savedServerId,
  pairingToken: savedPairingToken,
});

await bridge.connect();
```

Omitting `mode` selects `http`. Explicit `websocket` and `hybrid` preserve the
existing legacy implementations.

## Modes

| Mode | Control and pairing | `GET /events` | Other requests |
| --- | --- | --- | --- |
| `websocket` | WebSocket | WebSocket | WebSocket |
| `http` | HTTP | HTTP | HTTP |
| `hybrid` | HTTP | WebSocket | HTTP |

Hybrid matches only exact `GET /events` and `GET /events?...` paths. A
different method or a path such as `/events/archive` uses HTTP.

HTTP failures are never retried automatically over WebSocket. Reconstruct the
connection with `mode: 'websocket'` to roll back future requests.

## Discover and pair

An unpaired transport uses the same interface in all modes:

```ts
await bridge.connect();

const servers = await bridge.listServers();
const server = servers[0];

await bridge.requestPairing(server.server_id);
// Ask the user for the six-digit code shown by the registered server.
await bridge.submitPairingCode(server.server_id, code);

const pairingToken = bridge.getPairingToken();
```

Persist the bridge URL, server ID, and pairing token. The optional historical
record mode remains readable, but mobile reconstructs every saved record as
HTTP unless an app-wide development override is active. New mobile records
store HTTP independently of a diagnostic override.

Endpoint history is separate from paired server connections. The SDK exports
`SavedBridgeUrl` (`url`, optional `label`, and `lastUsedAt` in Unix milliseconds),
`loadSavedBridgeUrls(store)`, `saveSavedBridgeUrls(store, entries)`, and
`SAVED_BRIDGES_STORAGE_KEY`. They use `KeyValueStore` and
`clc_saved_bridges_v1`; removing an endpoint leaves connection credentials intact.

When `serverId` and `pairingToken` are supplied, `connect()` resumes or
validates the pairing:

- WebSocket and hybrid create a fresh ephemeral legacy session for the
  WebSocket path.
- HTTP validates the token and current server availability without opening a
  frontend WebSocket.

## HTTP origin

HTTP and hybrid accept HTTP(S) origins and existing WebSocket bridge URLs.
The SDK:

- converts `ws` to `http` and `wss` to `https`;
- removes a trailing `/ws` or `/ws/websocket`;
- removes query and fragment data.

Use `bridgeHttpBaseUrl` when the deployment publishes different HTTP and
WebSocket origins:

```ts
const bridge = createBridgeConnectionTransport({
  bridgeUrl: 'wss://socket.example/ws/websocket',
  bridgeHttpBaseUrl: 'https://api.example',
  mode: 'http',
});
```

## Request and response bodies

Every bridge mode implements the normal SDK `Transport.request()` contract.

In HTTP/hybrid HTTP-routed requests:

- objects are JSON encoded unless a content type is supplied;
- `ArrayBuffer`, typed-array views, and `Blob` bodies are sent as raw bytes;
- JSON responses are parsed;
- text, XML, JavaScript, and form responses return text;
- other content types return `ArrayBuffer`.

The frontend pairing token is sent as `X-Crystal-Bridge-Token`. An application
`Authorization` header remains available to the proxied backend.

## Timeout and lifecycle

Bridge transports accept the shared default and path/method timeout rules.
HTTP requests use `AbortController` when available. `disconnect()` aborts
active HTTP work and closes an active WebSocket.

Call `prepareForResume()` before reconnecting after a frontend suspension. The
transport validates liveness or pairing before later work:

```ts
bridge.prepareForResume();
await bridge.connect();
```

## Capability compatibility

HTTP and hybrid require bridge HTTP protocol version 1. `connect()` checks
`/bridge/v1/capabilities` and fails clearly if the bridge does not advertise
that version. Missing capability routes (404/405) also report protocol
incompatibility. Update an older bridge or explicitly select legacy WebSocket
for diagnostics. Mobile exposes that choice in Home → Development Settings,
where it applies to later connection construction and leaves open requests
untouched.
