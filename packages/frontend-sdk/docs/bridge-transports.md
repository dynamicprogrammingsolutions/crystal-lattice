# Bridge transports

The frontend SDK exposes one bridge connection interface with three explicit
transport modes. WebSocket is the default and compatibility path; HTTP and
hybrid are opt-in.

## Create a bridge transport

```ts
import {
  createBridgeConnectionTransport,
  type BridgeTransportMode,
} from '@crystal-lattice/frontend-sdk';

const mode: BridgeTransportMode = 'websocket';

const bridge = createBridgeConnectionTransport({
  bridgeUrl: 'wss://bridge.example/ws/websocket',
  mode,
  serverId: savedServerId,
  pairingToken: savedPairingToken,
});

await bridge.connect();
```

Omitting `mode` selects `websocket`.

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

Persist the bridge URL, server ID, pairing token, and explicit mode. A saved
record without a mode should be treated as WebSocket for compatibility.

When `serverId` and `pairingToken` are supplied, `connect()` resumes or
validates the pairing:

- WebSocket and hybrid create a fresh ephemeral legacy session for the
  WebSocket path.
- HTTP validates the token and current server availability without opening a
  frontend WebSocket.

## HTTP origin

HTTP and hybrid accept the normal WebSocket bridge URL. The SDK:

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
that version. Select WebSocket explicitly for an older bridge.
