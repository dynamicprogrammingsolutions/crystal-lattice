# Bridge service architecture

## Supervision

`Bridge.Application` starts one supervision tree containing:

- `Bridge.PubSub`;
- `Bridge.HttpProxyTaskSupervisor` for non-blocking legacy response waiters;
- `Bridge.HttpTransferSupervisor` for temporary v2 coordinators;
- `Bridge.ClusterSupervisor`;
- server, pairing, persistent-pairing, and session managers;
- `Bridge.Endpoint`.

`Bridge.HttpRouter` runs before `Plug.Parsers`, allowing proxy and transfer
routes to consume raw request bytes. `Bridge.Router` owns `/health`.

## WebSocket channels

`Bridge.Socket` accepts `type=server` and `type=app`.

`Bridge.ServerChannel` owns the active server control connection. It registers
the server PID, relays pairing notices and request metadata to the Python
server, receives legacy responses, and publishes v2 response initialization.
It unregisters its server on termination.

`Bridge.AppChannel` owns the compatibility frontend path. It discovers
servers, drives pairing, creates/resumes ephemeral sessions, validates those
sessions on requests, and starts supervised response waiters. Response waiting
does not block the channel mailbox, so later requests can progress.

## State managers

`Bridge.ServerRegistry` stores a per-node ETS view and replicates changes over
the `servers:registry` PubSub topic. The owning node monitors the active server
channel. Duplicate IDs either take over or are rejected according to
`BRIDGE_SERVER_ID_CONFLICT_POLICY`.

`Bridge.PairingManager` stores pending six-digit codes in ETS on the owner
node. Codes have expiry and attempt limits.

`Bridge.PersistentPairingManager` is a compatibility façade over stateless
`Bridge.PairingToken` credentials. It does not persist sessions or token
records.

`Bridge.SessionManager` stores node-local ephemeral sessions used only by the
legacy app channel. Session IDs are recreated from a verified pairing token
and expire after inactivity.

## Legacy request coordination

For each full or completed chunked request, `AppChannel` starts a task that:

1. subscribes to `tunnel:request:<request_id>`;
2. sends the request to the active server PID;
3. waits for full or chunked response events;
4. replies/pushes to the original app channel;
5. times out and cleans up independently.

This ordering prevents a fast response from racing ahead of the subscription.

## HTTP transfer coordination

`Bridge.HttpRouter` verifies the frontend pairing token, resolves the server,
issues request/response transfer credentials, starts `Bridge.HttpTransfer`,
and sends `http_request_v2`.

The coordinator subscribes to `http_transfer:<request_id>` and monitors:

- frontend proxy handler;
- registered server PID;
- request-body download handler;
- response-body upload handler.

Handlers on any connected bridge node publish attach messages through PubSub.
The coordinator enforces claim identity, one attachment per direction, byte
counts, an overall timeout, and demand/acknowledgement backpressure.

On failure it notifies peers and emits `http_request_v2_cancel`. On final
frontend acknowledgement it tells the uploader to complete and stops
normally.

The current transfer admission path checks active children before starting a
new temporary child. The formal target requires an atomic supervisor-enforced
bound; focused hardening remains tracked in `BRG-009`.

## Header and compression ownership

The HTTP router removes bridge authentication, host, framing, and hop-by-hop
request headers. The Python server removes `Accept-Encoding` and requests
identity from its local application.

The Python server removes stale response length/encoding and hop-by-hop
headers. The bridge then creates a streamed viewer response; Cowboy or the
public edge owns compression.

## Cluster model

The cluster may use gossip, DNS polling, or no topology. PubSub distributes
registry and transfer messages. HTTP pairing handles carry the finite existing
owner-node name so confirmation can call the node that stores the pending code.

The system does not require load-balancer affinity for HTTP pairing or transfer
legs. Loss of the owner node invalidates its pending pairing/transfer work but
does not invalidate stateless pairing credentials when surviving nodes share
the signing configuration.

## Connected implementation owners

- Frontend transport implementation:
  `packages/frontend-sdk/src/transport/`
- Registered Python server:
  `application/python/agent_terminal_app/bridge_client.py`
- Mobile lifecycle:
  `mobile/crystal-lattice-control-rn/App.tsx`
- Deployment:
  `docker-compose*.yml`, `haproxy*.cfg`, and `deploy/aws-*`
