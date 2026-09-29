# Bridge registered-server adapter

`agent_terminal_app.bridge_client.BridgeClient` connects the local terminal
HTTP application to the distributed bridge as a registered server. It is an
integration adapter: it forwards opaque HTTP requests and does not implement
application route semantics.

## Lifecycle ownership

The FastAPI startup hook creates the bridge client only from an explicit
`ServerIntegrationRuntimeConfig` and starts `BridgeClient.run()` as a
background task. The CLI constructs that process-local object from explicit
flags, project/profile state, resolved application configuration, effective
host/port, and built-in defaults. Direct FastAPI embedders call
`configure_integrations(...)` before startup.

For an embedding process that already owns FastAPI startup, construct the
runtime settings directly:

```python
import socket

from agent_terminal_app import server
from agent_terminal_app.bridge_client import BridgeConfig

server.configure_integrations(
    server.ServerIntegrationRuntimeConfig(
        bridge=BridgeConfig(
            bridge_url="wss://bridge.example/ws/websocket",
            server_id="my-server",
            display_name="My server",
            computer_name=socket.gethostname(),
            location=None,
            local_http_base="http://127.0.0.1:9000",
        )
    )
)
# Start server.app through the embedding ASGI server.
```

For Bonjour, pass a `BonjourRuntimeConfig(service_name=..., port=...)` member.
To disable both integrations for subsequent startup, call
`server.configure_integrations(None)`.

The client:

1. connects to `<bridge-url>?type=server`;
2. joins `server:<server_id>`;
3. registers display/computer/location metadata;
4. receives pairing notices and request events;
5. reconnects after transient WebSocket loss until stopped.

FastAPI shutdown stops the bridge client before tearing down the local HTTP
application. Stop, disconnect, and supersession cancel in-flight request tasks.

The default bridge conflict policy makes a newer registration for one
`server_id` active. A superseded Python client stops; it can optionally exit
the process. The optional local lock guard prevents two local processes from
using the same ID, and takeover can terminate the recorded process before
acquiring the lock.

## Configuration

Common CLI options:

| Option | Purpose |
| --- | --- |
| `--enable-bridge` | Enable bridge registration using resolved configuration. |
| `--bridge-url` | Public bridge WebSocket URL. |
| `--bridge-display-name` | Human-readable discovery name. |
| `--bridge-location` | Optional display metadata. |
| `--bridge-server-id` | Stable server identity. |
| `--bridge-local-http-base` | Local FastAPI origin used for forwarded requests. |
| `--bridge-http-base` | Public HTTP origin used for v2 body download/upload when it cannot be derived. |
| `--bridge-exit-on-superseded` | Exit after a newer registration replaces this client. |
| `--bridge-local-guard` | Enable the per-server-ID local lockfile. |
| `--bridge-takeover-local` | Terminate the lockfile owner before takeover. |

The bridge URL resolves from CLI, project/profile state, or
`application.bridge_url`. The adapter is disabled when bridge registration is
not requested or no URL can be resolved.

`application.bridge` owns the advanced WebSocket-size, HTTP timeout, legacy
chunk size/threshold, adapter body-limit, and debug settings. The parser
validates these values and supplies the resulting values to `BridgeConfig`.
The defaults are shared with `BridgeConfig` so an omitted application object
and the maintained default config have the same behavior.

FastAPI startup does not inspect ambient `BRIDGE_*`, `BONJOUR_*`,
`ENABLE_BONJOUR`, `SERVER_HOST`, `SERVER_PORT`, or `PORT` values. This is an
integration-lifecycle invariant: a tool-launched child may inherit those names,
but cannot accidentally register the parent's bridge identity or advertise
Bonjour. The normal process environment is not sanitized.

The integration configuration is process-owned. Application reload swaps the
agent application while leaving the HTTP listener, bridge client, and Bonjour
registration alive; changing integration settings therefore requires a
process restart.

## Legacy request path

For `http_request`, the adapter forwards method, path, string body, and string
headers through `httpx`, then returns `http_response`.

The compatibility chunk protocol buffers ordered UTF-8 request chunks up to
the configured body limit. It executes the local request after
`http_request_end`. Responses above the configured threshold are emitted as
ordered `http_response_init`, `http_response_chunk`, and
`http_response_end` events.

Each completed request executes in a tracked task, so a slow request does not
block the server WebSocket receive loop. A send lock keeps each response's
WebSocket messages contiguous.

## HTTP v2 request path

`http_request_v2` contains metadata and two short-lived transfer
credentials—not body bytes.

For a request with a body, the adapter:

1. opens the request-body path with its bearer credential;
2. passes the raw asynchronous byte iterator to the local `httpx` request;
3. requests `Accept-Encoding: identity` from the local application.

For the local response, it:

1. filters stale framing/encoding and hop-by-hop headers;
2. sends `http_response_v2_init` through the server WebSocket;
3. streams `local_response.aiter_raw()` into the response-body `PUT`.

An adapter-side failure attempts a `502` JSON response through the same v2
metadata/upload path. Failure to upload that fallback is logged without
creating another protocol path.

## Task tracking and cancellation

All bridge HTTP tasks are tracked in `_inflight_http_tasks`. V2 tasks are also
indexed by request ID in `_inflight_v2_tasks`.

- A repeated v2 request ID cancels the earlier task.
- `http_request_v2_cancel` cancels the indexed task.
- WebSocket close, explicit stop, and server supersession cancel all tracked
  tasks and clear incomplete legacy chunk state.
- Completion callbacks remove tasks from both collections.

Phase-specific tests cancel work during request download, local stream setup,
and response upload through explicit cancel, bridge close, stop, and
supersession. Each asserts both task registries are empty afterward.

## Header boundary

The adapter does not forward:

- host, content length, transfer encoding, or hop-by-hop request headers;
- bridge transfer bearer credentials;
- local response content length/content encoding or hop-by-hop response
  headers.

The application `Authorization` header is preserved. Viewer-facing compression
is owned by the bridge origin or public edge.

## Verification

Focused tests:

- `test_bridge_client_local_request.py`
- `test_bridge_client_chunked_http.py`
- `test_bridge_client_http_transfer.py`
- `test_bridge_client_superseded.py`
- `test_server_integration_settings.py`
- bridge-related CLI explicit-configuration/isolation tests

The frontend SDK bridge E2E is the public assembled boundary using the real
Elixir bridge, this Python adapter, FastAPI, and production frontend
transports.

The cross-package
[bridge-connectivity specification](../../../../docs/development/specifications/bridge-connectivity/index.md)
owns the complete portable behavior.
