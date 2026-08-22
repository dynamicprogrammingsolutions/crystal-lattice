# Bridge deployment and operations specification

## Supported topologies

### Single node

One Phoenix endpoint may serve health, server/app WebSockets, and HTTP v1
routes. This is suitable for development and trusted-network use. An
internet-facing deployment requires TLS termination at an edge or reverse
proxy.

### Cluster behind a load balancer

Multiple bridge nodes may run behind round-robin HAProxy or another
WebSocket-capable HTTP load balancer. Nodes form an Erlang cluster through
either:

- gossip, the default local/Docker strategy;
- DNS polling for service-discovery environments; or
- no clustering for intentionally single-node tasks.

The load balancer does not need sticky sessions for HTTP v1:

- server registration is replicated through PubSub;
- HTTP pairing confirmation dispatches to the owner of the pending code;
- transfer consumers/uploaders attach through the cluster-wide transfer topic.

Legacy frontend WebSocket sessions naturally remain on the node that owns the
socket.

### Secure edge

A public edge must:

- redirect or require HTTPS/WSS;
- forward WebSocket upgrade headers;
- forward query strings and all supported HTTP methods;
- forward `Authorization`, `Content-Type`, `X-Crystal-Bridge-Token`, and
  `X-Crystal-Bridge-Body-Present`;
- disable caching for control, proxy, and transfer traffic;
- use timeouts compatible with long request/response streaming.

The committed secure CloudFront definitions advertise HTTP/2 to viewers,
enable compression, and disable application-response caching. The TLS HAProxy
example advertises `h2,http/1.1`. Plain Phoenix origins normally use HTTP/1.1.

## Shared cluster configuration

All nodes in one logical bridge deployment must share:

- the Erlang distribution cookie;
- `BRIDGE_TOKEN_SECRET`;
- `BRIDGE_TOKEN_SALT`;
- `BRIDGE_HTTP_TRANSFER_TOKEN_SALT`;
- compatible credential lifetimes and transfer limits.

Changing a signing secret invalidates credentials issued under the old secret.
Rotate with an explicit re-pairing plan.

## Configuration contract

| Setting | Default | Purpose |
| --- | --- | --- |
| `PORT` | `4000` | Phoenix HTTP/WebSocket listener. |
| `BRIDGE_CLUSTER_STRATEGY` | `gossip` | `gossip`, `dns_poll`, or `none`. |
| `GOSSIP_PORT` | `45892` | Gossip cluster port. |
| `GOSSIP_MULTICAST_ADDR` | `230.1.1.251` | Gossip multicast address. |
| `BRIDGE_CLUSTER_DNS_NAME` | `bridge.local` | DNS polling query. |
| `BRIDGE_CLUSTER_NODE_BASENAME` | `bridge` | DNS cluster node basename. |
| `PAIRING_CODE_TTL` | `300` seconds | Pairing-code lifetime. |
| `MAX_PAIRING_ATTEMPTS` | `3` | Wrong-code attempt limit. |
| `SESSION_TIMEOUT` | `3600` seconds | Legacy session inactivity lifetime. |
| `BRIDGE_PAIRING_TOKEN_TTL_SECONDS` | `2592000` | Signed pairing credential lifetime. |
| `BRIDGE_HTTP_TRANSFER_TOKEN_TTL_SECONDS` | `180` | Body-transfer credential lifetime. |
| `BRIDGE_HTTP_TIMEOUT_MS` | `120000` | Legacy response and HTTP transfer timeout. |
| `BRIDGE_HTTP_MAX_BODY_BYTES` | `104857600` | HTTP v1 request/response byte limit. |
| `BRIDGE_MAX_PENDING_HTTP_TRANSFERS` | `128` | Intended per-node active transfer bound. |
| `BRIDGE_MAX_PENDING_HTTP_REQUESTS` | `128` | Per-app legacy response-waiter bound. |
| `BRIDGE_HTTP_COMPRESS_THRESHOLD_BYTES` | `1024` | Cowboy viewer gzip threshold. |
| `BRIDGE_SERVER_ID_CONFLICT_POLICY` | `takeover` | `takeover` or `reject`. |

The active HTTP transfer bound is not considered fully verified until
admission is atomic under concurrent starts. See `BRG-009`.

## Compression

The Python server requests identity encoding from the local application and
removes stale encoding/length response headers. The viewer-facing Phoenix
endpoint may negotiate gzip for responses at or above its threshold.

Brotli is edge-dependent. The Phoenix origin does not require an in-process
Brotli implementation. A compatible edge may negotiate Brotli when its
compression policy and response type allow it.

## Health

`GET /health` returns:

```json
{
  "status": "healthy",
  "node": "bridge@node",
  "cluster_size": 2,
  "active_servers": 1,
  "active_sessions": 3
}
```

`cluster_size` is the current node plus connected Erlang nodes.
`active_servers` is the local node's replicated registry view.
`active_sessions` is the local node's ephemeral legacy-session count, not a
cluster aggregate.

Load balancers should use `/health` for origin checks. HAProxy statistics can
be exposed separately and must not be treated as a bridge API.

## Logging and credentials

Proxy and edge logs must not capture pairing credentials, transfer bearer
tokens, or request bodies. The bridge's common responses are no-store, but
operators must also disable caching at the edge.

Production deployments must not use the development fallback token secret.
WebSocket origin checks are permissive in the current mobile-oriented endpoint;
deployments with a fixed browser origin should restrict allowed origins.

## Recovery

- A failed bridge node is removed from the Erlang cluster by normal cluster
  membership behavior.
- A pending HTTP pairing owned by the failed node cannot be confirmed; request
  a new code.
- A transfer coordinator lost with its node fails that request; clients may
  decide whether a later request is safe to retry.
- A reconnecting server registers the same stable ID and becomes discoverable.
- A valid pairing credential survives bridge process/node changes because it
  is stateless and signed, provided the signing configuration is unchanged.

## Operating guides

Command-oriented setup, Docker, TLS reverse-proxy, AWS, and cleanup procedures
remain in `bridge-elixir/PRODUCTION_DEPLOYMENT.md`. The bridge package
quickstart covers local first use. This specification defines required
behavior, not provider-specific deployment steps.
