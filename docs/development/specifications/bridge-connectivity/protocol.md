# Bridge connectivity protocol

This document is the normative bridge wire contract. Application routes
carried inside a proxied request are opaque to the bridge.

## Endpoint roots

- Phoenix WebSocket: `/ws/websocket?type=server` or
  `/ws/websocket?type=app`
- Health: `GET /health`
- HTTP bridge protocol: `/bridge/v1/*`

Phoenix clients join `server:<server_id>` or `app:<client_id>`. The current
clients encode messages as JSON objects:

```json
{
  "topic": "app:<client_id>",
  "event": "event_name",
  "payload": {},
  "ref": "caller-correlation-reference"
}
```

Replies use Phoenix `phx_reply` status/response envelopes. Server pushes have
no caller request reference. Phoenix heartbeat uses topic `phoenix`, event
`heartbeat`.

## Server control channel

The server connects with `type=server`, joins `server:<server_id>`, and sends:

| Event | Required payload | Meaning |
| --- | --- | --- |
| `register` | `server_id`, `display_name`, `computer_name`; optional `location` | Make this control connection the active server registration. |
| `http_response` | `request_id`, `status`, `headers`, `body` | Complete a small legacy response. |
| `http_response_init` | `request_id`, `status`, `headers`, body/chunk metadata | Start a chunked legacy response. |
| `http_response_chunk` | `request_id`, `seq`, `chunk` | Send one ordered legacy response text chunk. |
| `http_response_end` | `request_id`, `final_seq` | Finish a chunked legacy response. |
| `http_response_v2_init` | `request_id`, `status`, `headers` | Start an HTTP v1 proxy response; the body is uploaded separately. |

The bridge may push:

| Event | Payload | Meaning |
| --- | --- | --- |
| `pairing_requested` | `client_id`, `code`, `expires_at` | Display the six-digit code to the user. |
| `paired` | `client_id`, `session_id` | A legacy ephemeral session was created. |
| `http_request` | request metadata plus text `body` | Execute a small legacy request. |
| `http_request_init` | request and chunk metadata | Start receiving a legacy chunked request. |
| `http_request_chunk` | `request_id`, `seq`, `chunk` | Receive one ordered legacy request text chunk. |
| `http_request_end` | `request_id`, `final_seq` | Execute the assembled legacy request. |
| `http_request_v2` | metadata and transfer paths/tokens | Execute an HTTP v1 proxy request without WebSocket body bytes. |
| `http_request_v2_cancel` | `request_id`, `reason` | Cancel in-flight v2 server work. |
| `superseded` | `server_id`, `reason: "new_connection"` | Stop because a newer registration owns the server ID. |

An `http_request_v2` payload contains:

```json
{
  "type": "http_request_v2",
  "request_id": "<uuid>",
  "method": "POST",
  "path": "/opaque/application/path?query=value",
  "headers": {},
  "request_body_present": true,
  "request_body_path": "/bridge/v1/transfers/<request_id>/request-body",
  "request_body_token": "<signed-token>",
  "response_body_path": "/bridge/v1/transfers/<request_id>/response-body",
  "response_body_token": "<signed-token>"
}
```

The path values may be resolved against an explicitly configured bridge HTTP
origin. The tokens are sent only through the server control channel.

## Legacy app channel

The app connects with `type=app`, joins `app:<client_id>`, and may send:

| Event | Required payload | Successful result |
| --- | --- | --- |
| `list_servers` | none | Public server records. |
| `pair_request` | `server_id` | Requested status and code expiry. |
| `pair_submit` | `server_id`, `code` | Fresh `session_id` and signed `pairing_token`. |
| `resume_session` | `pairing_token`; optional expected `server_id` | Fresh `session_id`. |
| `http_request` | `request_id`, `session_id`, method, path, headers, text body/null | Full legacy response or chunked-response marker. |
| `http_request_init` | request/session metadata and optional body/chunk metadata | Accepted. |
| `http_request_chunk` | `request_id`, `session_id`, `seq`, `chunk` | Accepted. |
| `http_request_end` | `request_id`, `session_id`, `final_seq` | Full legacy response or chunked-response marker. |

Chunked responses are pushed as `http_response_init`,
`http_response_chunk`, and `http_response_end` before the final
`phx_reply`. Sequences begin at zero and must be contiguous. `final_seq` is the
last emitted sequence.

Legacy request and response bodies are UTF-8 strings. This path does not define
a raw-binary WebSocket encoding.

## HTTP v1 API

All bridge HTTP v1 responses set `Cache-Control: no-store`. The router exposes
CORS headers allowing the supported methods and `Content-Type`,
`Authorization`, `X-Crystal-Bridge-Token`, and
`X-Crystal-Bridge-Body-Present`.

Errors use:

```json
{"error": "stable_reason"}
```

### Capabilities

`GET /bridge/v1/capabilities`

No authentication. A compatible response identifies protocol version `1`,
HTTP proxy support, body download/upload support, and `http`/`hybrid` modes.
An HTTP frontend fails explicitly if version 1 is not advertised.

### Discovery

`GET /bridge/v1/servers`

No authentication. Returns:

```json
{
  "servers": [
    {
      "server_id": "<stable-id>",
      "display_name": "Server",
      "computer_name": "host",
      "location": null
    }
  ]
}
```

Internal channel PID, node, and connection timestamp are not public.

### Pairing request

`POST /bridge/v1/pairings/request`

Body:

```json
{"server_id": "<stable-id>", "client_id": "<frontend-id>"}
```

The response contains `status`, ISO-8601 `expires_at`, and an opaque
`pairing_request_token`. The response never contains the six-digit code.

### Pairing confirmation

`POST /bridge/v1/pairings/confirm`

Body:

```json
{"pairing_request_token": "<signed-handle>", "code": "123456"}
```

Success returns `server_id` and `pairing_token`. Representative errors include
expired request (`410`), unavailable owner (`409`), missing server (`404`),
and invalid/not-found pairing (`400`).

### Pairing resume or validation

`POST /bridge/v1/pairings/resume`

Header:

```text
X-Crystal-Bridge-Token: <pairing-token>
```

Body may contain the expected `server_id`. Success returns the token's
`server_id` and current public server record. This route does not create a
frontend WebSocket session.

### Proxied application request

`<supported-method> /bridge/v1/proxy/<opaque-path-and-query>`

Header:

```text
X-Crystal-Bridge-Token: <pairing-token>
```

`X-Crystal-Bridge-Body-Present: 1` explicitly distinguishes a present
zero-length body from no body. Content length or transfer encoding also marks a
body as present.

The bridge strips its path prefix and forwards the remaining path/query to the
registered server. It preserves the caller's application `Authorization`
header. JSON, text, and binary body bytes are opaque to the bridge.

Before response headers, errors are normal JSON HTTP errors. After a streamed
response starts, later errors terminate that response stream.

### Request-body transfer

`GET /bridge/v1/transfers/<request_id>/request-body`

Header:

```text
Authorization: Bearer <request-body-transfer-token>
```

The credential must match request ID, server ID, `request_body` direction, and
expiry. A successful response is an identity-encoded
`application/octet-stream` body. Only one consumer may attach.

### Response-body transfer

`PUT /bridge/v1/transfers/<request_id>/response-body`

Header:

```text
Authorization: Bearer <response-body-transfer-token>
```

The credential must match request ID, server ID, `response_body` direction,
and expiry. Only one uploader may attach. Success returns `204` after the
frontend acknowledges the final response chunk.

## Header filtering

The bridge does not forward:

- `Host`;
- `X-Crystal-Bridge-Token`;
- `X-Crystal-Bridge-Body-Present`;
- `Content-Length` or `Transfer-Encoding`;
- `Connection`, `Keep-Alive`, `Proxy-Authenticate`,
  `Proxy-Authorization`, `TE`, `Trailer`, or `Upgrade`.

The Python server requests `Accept-Encoding: identity` from its local
application. It removes stale local `Content-Length` and `Content-Encoding`
before response metadata crosses the server WebSocket.

## Compatibility

Adding HTTP v1 does not remove or reinterpret legacy app/server channel
events. HTTP/hybrid clients negotiate through capabilities. There is no
protocol-level fallback or replay from HTTP v1 to legacy WebSocket proxying.
