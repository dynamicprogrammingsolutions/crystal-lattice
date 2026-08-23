# Bridge frontend behavior

## Shared transport interface

Frontend bridge implementations satisfy one structural connection interface:

- `connect()` and `disconnect()`;
- `prepareForResume()`;
- pairing/server identity accessors;
- `isPaired()`;
- discovery, pairing request, and code submission;
- the normal `Transport.request()` contract.

The factory accepts `websocket`, `http`, or `hybrid`. Omission selects
`websocket`.

## WebSocket mode

WebSocket mode constructs the established `BridgeTransport` without adding
HTTP branches to it. It:

- opens and joins a Phoenix app channel;
- pairs or resumes to obtain an ephemeral session;
- validates liveness through Phoenix heartbeat;
- sends small UTF-8 bodies in one event;
- sends large UTF-8 bodies through ordered chunks;
- reconstructs chunked text responses;
- rejects in-flight work when the socket becomes unusable.

Timeout of a normal non-poll request can make the socket suspect and trigger
reconnection. Event-poll timeout does not alone destroy an otherwise
heartbeat-healthy socket.

## HTTP mode

HTTP mode:

- derives `http` from `ws` and `https` from `wss`;
- removes a trailing `/ws` or `/ws/websocket` path;
- accepts an explicit HTTP base when public origins differ;
- checks capability version 1 during connect;
- validates a saved pairing credential when one is present;
- uses HTTP for discovery, pairing, resume, events, and every proxied request;
- never opens a frontend WebSocket.

`disconnect()` aborts active fetches. `prepareForResume()` requires pairing
validation before the next request/connection use.

Request timeout selection uses the same transport timeout policy inputs as the
other frontend transports.

## Hybrid mode

Hybrid owns one HTTP transport and lazily creates one unchanged legacy
WebSocket transport from the same server ID and pairing credential.

HTTP owns discovery, pairing, resume validation, and normal requests. The
legacy transport is used only when:

```text
method == GET
and (path == /events or path starts with /events?)
```

When an already-paired hybrid transport connects, it validates HTTP access and
connects/resumes the legacy event transport. After a new HTTP pairing, it
rebuilds the legacy transport from the newly issued credential.

Both child transports disconnect or prepare for resume together.

## Response contract

HTTP JSON responses are parsed as JSON. Text, XML, JavaScript, and form
responses are returned as text. Other content types are returned as an
`ArrayBuffer`.

An HTTP error is raised with status, method, path, and an available server
error detail. A transport/network error is not replayed through the other
transport family.

## Persistence and migration

A saved bridge connection contains:

- bridge WebSocket URL;
- server ID and display name;
- pairing credential, or `null` when repair is required;
- optional transport mode.

The mode remains optional for backward compatibility. A record without it is
always interpreted as `websocket`; existing records are not migrated to HTTP
or hybrid implicitly.

Changing modes retains the same server ID and pairing credential. A mode
change affects a newly constructed transport and does not retry an in-flight
request.

## Mobile lifecycle

The mobile connection wizard labels HTTP and hybrid as experimental and keeps
WebSocket selected by default. Successful pairing persists the explicit
selection.

Reopening a saved bridge record:

1. reconstructs its selected mode, defaulting an absent value to WebSocket;
2. validates/resumes with the saved server ID and pairing credential;
3. enters a repair flow if the credential is invalid, the server is absent, or
   the expected server mismatches;
4. clears an invalid or mismatched credential before re-pairing.

On foreground recovery, the host calls `prepareForResume()` and reconnects
through the structural bridge interface rather than checking for one concrete
transport class.

## Rollout rule

The mode factory and persisted field are opt-in controls. The application-wide
default remains WebSocket. Permanent default migration is outside the current
baseline and requires the rollout evidence in `BRG-014`.
