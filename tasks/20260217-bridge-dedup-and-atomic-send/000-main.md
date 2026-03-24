# Bridge deduplication + atomic send (single-target routing, takeover, idempotency)

## Description

Users observed that when running multiple `agent_terminal_app` servers with the **same** `--bridge-server-id` (even on different local ports), a single bridged request is delivered multiple times. Root cause is **bridge fan-out**: the Elixir bridge forwards requests via PubSub broadcast to a topic that **all server connections with the same `server_id` subscribe to**.

This task introduces end-to-end safeguards so duplicates are prevented at multiple layers:

1. **Elixir bridge**: enforce **single active server connection per `server_id`** (takeover or reject policy), and **route requests to exactly one server connection** (no PubSub fan-out).
2. **Python BridgeClient**: handle bridge “superseded/takeover” instruction and gracefully stop the older client; optionally add a local single-instance guard.
3. **FastAPI server**: make `/send` **single-flight** per session + support **idempotency keys**; add an **atomic append+send** endpoint.
4. **Frontend SDK / mobile app**: use the atomic endpoint and send idempotency keys to make retries safe.

This is designed to work alongside the existing bridge chunking work.

## Background / Findings (already investigated)

### Repro symptom

If two server processes register with the same bridge `server_id`, they both receive the same `http_request` from the bridge.

### Root cause (Elixir bridge fan-out)

* `Bridge.ServerChannel` subscribes every registered server websocket to the PubSub topic `"tunnel:server:<server_id>"`:
  * `bridge-elixir/lib/bridge/server_channel.ex` (register handler) lines ~28–32.
* `Bridge.AppChannel` forwards `http_request` by broadcasting to that PubSub topic:
  * `bridge-elixir/lib/bridge/app_channel.ex` `handle_in("http_request", ...)` lines ~183–214.
* Therefore, if **N** server websocket connections are registered/subscribed for the same `server_id`, the request is delivered **N** times.

`Bridge.ServerRegistry` stores only one ETS record per `server_id` (set semantics), but that does **not** prevent multiple server channel processes from being subscribed to PubSub.

### Existing bridge chunking task overlap

See `tasks/20260215-multipart-upload/100-bridge-chunked-http-over-websocket.md`.

That work adds `http_request_init/chunk/end` and chunked responses and explicitly keeps Elixir as a forwarder. This task must ensure the new routing logic applies consistently to **all** of:

* legacy `http_request`
* chunked `http_request_*` messages
* pairing-related pushes (`pairing_requested`, `paired`)

## Goals

* No duplicate delivery of bridged requests when multiple servers share the same `server_id`.
* Clear operational behavior when a second server registers the same `server_id`:
  * Prefer “takeover”: new connection supersedes old.
  * Optionally “reject”: new connection is refused.
* Server-side safety: multiple `/send` triggers for the same session become single-flight and/or idempotent.
* Provide a single atomic endpoint for append+send.

## Non-goals

* Strong security guarantee against a malicious actor on the same bridge (this remains a trusted environment assumption).
* Rewriting the entire bridging protocol.

## Subtasks

- [x] `tasks/20260217-bridge-dedup-and-atomic-send/010-elixir-single-target-routing-and-takeover.md`
- [x] `tasks/20260217-bridge-dedup-and-atomic-send/020-python-bridgeclient-takeover-and-local-guard.md`
- [x] `tasks/20260217-bridge-dedup-and-atomic-send/030-fastapi-send-singleflight-idempotency.md`
- [x] `tasks/20260217-bridge-dedup-and-atomic-send/040-fastapi-atomic-append-send-endpoint.md`
- [x] `tasks/20260217-bridge-dedup-and-atomic-send/050-frontend-sdk-use-atomic-and-idempotency.md`

## Acceptance criteria (end-to-end)

* Start two `agent_terminal_app` processes with the same `BRIDGE_SERVER_ID` (different ports is fine) and pair a client:
  * Bridged `http_request` is forwarded to **only one** server.
  * Either the old server is disconnected/superseded, or the second server cannot register (depending on configured policy).
* When duplicates still occur (e.g., due to client retry), FastAPI ensures only one request run occurs per session:
  * Multiple calls to `/sessions/{id}/send` while a request is active do not start multiple tool loops.
* Atomic endpoint exists and is used by frontend SDK:
  * “Send” from UI results in exactly one appended message and exactly one request run, even with retry.

## Notes

* Prefer a config toggle for bridge behavior (takeover vs reject), defaulting to takeover for UX.
* Ensure behavior covers both legacy and chunked request paths.
* `AgentApplication.acquire_session_lock(session_id)` is used intermittently during request execution (e.g., checkpoint persistence). Do not hold it for the whole duration of a send; use it for short mutation sections and use separate bookkeeping locks for single-flight/idempotency.
