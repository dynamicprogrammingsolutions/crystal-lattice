# Bridge connectivity

Status: Implemented opt-in baseline; focused transfer-safety and planned
access/E2EE extension work pending

The bridge-connectivity specification defines how a remote Crystal Lattice
frontend discovers, pairs with, and sends HTTP-shaped requests to a registered
local server through the distributed bridge service.

It covers the complete current subsystem, including the compatibility
WebSocket path and the opt-in HTTP and hybrid frontend paths:

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

## Related specifications

- [Bridge access control](../bridge-access-control/index.md) owns credential
  meaning, access profiles, pairing policy, subjects, grants, entitlement,
  quota, and provider behavior.
- [Bridge E2EE](../bridge-e2ee/index.md) owns authenticated key establishment,
  protected fields, encrypted envelope semantics, key lifecycle, and security
  review.
- [Hosted bridge client experience](../hosted-bridge-client-experience/index.md)
  owns login, subscription, server ownership, hosted connection, and
  account-deletion presentation.

Bridge connectivity owns how credentials, capabilities, opaque encrypted
envelopes, and usage bytes cross WebSocket, HTTP, hybrid, cluster, and edge
boundaries. It does not redefine their authorization, cryptographic, or
commercial meaning.

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
- access-profile, entitlement, quota, and product-account semantics;
- E2EE cryptographic algorithms, key lifecycle, and public security claims;
- store purchase, subscription, and account-deletion behavior;
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
