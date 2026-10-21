# Bridge connectivity

Status: Transport baseline verified; HTTP product-default follow-up in progress

The bridge-connectivity specification defines how a remote Crystal Lattice
frontend discovers, pairs with, and sends HTTP-shaped requests to a registered
local server through the distributed bridge service.

It covers the complete current subsystem, including the compatibility
WebSocket path and the HTTP product path with explicit legacy diagnostics:

- [Product behavior](product-spec.md)
- [Technical architecture](technical-spec.md)
- [Wire protocol](protocol.md)
- [Deployment and operations](deployment-and-operations.md)
- [Frontend behavior](frontend-behavior.md)
- [Requirements and evidence](requirements.md)

## Ownership

The contract is cross-package because no single package owns the end-to-end
behavior:

| Responsibility | Current owner |
| --- | --- |
| WebSocket channels, pairing, server registry, sessions, HTTP API, and transfer coordination | `bridge-elixir` |
| Frontend transport contract and WebSocket/HTTP/hybrid implementations | `packages/frontend-sdk` |
| Registered server connection and local HTTP forwarding | `application/python/agent_terminal_app` |
| Saved bridge connection, mode selection, foreground recovery, and repair flow | `mobile/crystal-lattice-control-rn` |
| Cluster and secure-edge configuration | `bridge-elixir` deployment assets |

The formal specification owns the portable target and requirement status.
Package documentation describes the current implementation and operating
commands without redefining this contract.

## Scope

The bridge-connectivity subsystem begins when a local server opens its bridge
control WebSocket and ends where that server forwards a proxied request into
its local HTTP application. It includes:

- registration, discovery, health, conflict handling, and cluster visibility;
- pairing codes, signed pairing credentials, resume, and ephemeral legacy
  sessions;
- legacy WebSocket proxying and text chunking;
- HTTP v1 control/proxy routes and v2 server control events;
- raw request and response streaming, limits, cancellation, and cleanup;
- frontend transport selection, persistence, and rollback;
- single-node, clustered, load-balanced, and TLS-edge behavior.

## Explicit exclusions

The specification does not define:

- the semantics or payload schemas of proxied application routes such as
  `/sessions`, `/messages`, or `/events`;
- event contents, polling cadence, or frontend refresh orchestration;
- agent, provider, plugin, tool, or model behavior;
- cloud-orchestrator connectivity;
- direct HTTP or Bonjour discovery beyond distinguishing them from the bridge;
- mobile presentation outside bridge connection selection and lifecycle;
- desktop behavior that is not wired to the new bridge modes;
- historical or abandoned bridge designs.

## Sources and evidence

Current claims are bounded to the directly connected bridge modules, SDK
transports, Python server adapter, mobile connection host, deployment
definitions, and their focused tests. Inspection alone is not accepted as
verification. The [requirements table](requirements.md) distinguishes
implemented behavior, automated evidence, pending evidence, and human rollout
gates.

Primary delivery tracking:

- `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`
- commit `61140c0e` (`Add opt-in HTTP bridge transport path`)
- commit `70346cec` (`Harden HTTP bridge integration coverage`)
