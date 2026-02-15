Add support for large JSON request bodies through the Elixir bridge by implementing an application-level chunking protocol for proxied HTTP requests over Phoenix Channels. The goal is to let apps/FastAPI behave as if sending/receiving one large HTTP request, while the transport layers split and reassemble it.

## Step 1 — Prepare

1) Read task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/100-bridge-chunked-http-over-websocket.md`

2) Inspect current end-to-end bridge code paths:

Frontend SDK:
- `packages/frontend-sdk/src/transport/bridgeTransport.ts`

Elixir:
- `bridge-elixir/lib/bridge/app_channel.ex`
- `bridge-elixir/lib/bridge/server_channel.ex`
- `bridge-elixir/lib/bridge/endpoint.ex`

Python server bridge client:
- `application/python/agent_terminal_app/bridge_client.py`

3) Identify constraints and gaps to address:
- WebSocket message size limits (Python `websockets` max_size default)
- Existing timeouts (TS 30s, Elixir 60s, Python httpx 10s)
- Whether to implement chunk ACK/backpressure

4) Share an implementation plan with the user:
- Proposed events (init/chunk/end) and payload fields
- Whether to keep legacy `http_request` and add threshold-based chunking
- Timeout and size-limit defaults (and how to make them configurable)
- Test plan (unit + optional end-to-end)

Do not implement yet.

## Step 2 — Complete (after user approval)

1) Implement TS `BridgeTransport` chunking.

2) Implement Elixir forwarding for new chunked events.

3) Implement Python `BridgeClient` buffering/reassembly and configuration changes.

4) Add tests and run the smallest relevant suites.
