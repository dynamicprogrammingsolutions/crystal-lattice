# Configurable Bridge Access And Pairing Profiles

Let bridge operators select a validated access profile and independently
require or disable pairing when another authentication mechanism is active.

## Requirements checklist

### Functional requirements

- [ ] **P1** — The bridge supports validated `local-open` and `static-token`
  profiles, including configurable pairing when another authentication
  mechanism is active, and rejects unsafe or incomplete configurations at
  startup.
- [ ] **P1** — HTTP and WebSocket capability negotiation expose the same
  effective transport, authentication, pairing, entitlement, limits, and E2EE
  policy.
- [ ] **P1** — Mobile and SDK clients use negotiated capabilities when creating
  or restoring connections, including pairing UI and explicit errors when a
  saved connection no longer matches deployment policy.

### Non-functional requirements

- [ ] **P1** — Profile selection cannot silently weaken authentication or
  pairing because of missing, unknown, or invalid configuration.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On: `tasks/20260821-modular-bridge-access-platform/010-static-token-bridge-security.md`

## Specifications and requirements

- `docs/development/specifications/bridge-access-control/index.md`:
  `BAC-004`, `BAC-005`, `BAC-015`
- `docs/development/specifications/bridge-connectivity/index.md`: `BRG-015`

## Required reading

- `bridge-elixir/config/config.exs`
- `bridge-elixir/lib/bridge/socket.ex`
- Mixed-transport `/bridge/v1/capabilities` implementation
- `packages/frontend-sdk/src/transport/bridgeConnectionTransport.ts` on the
  mixed-transport branch
- Mobile bridge connection and saved-connection reconstruction code

## Supporting details

Initial effective profiles:

| Profile | Deployment authentication | Pairing |
| --- | --- | --- |
| `local-open` | none | required |
| `static-token` | deployment token | required or disabled |

When `static-token` has pairing disabled, any holder of the deployment token
can discover and connect to registered servers. This is suitable only for a
trusted single-user or equivalent deployment and must be explicit in UI and
documentation.

Capability responses should report effective policy rather than secret
configuration. HTTP and WebSocket-only clients need equivalent information.

## Execution plan

Status: Draft

Introduce one normalized effective-policy structure used by WebSocket and HTTP
handlers. Add startup validation, capability negotiation, and client behavior
for pairing-required and pairing-disabled deployments. Keep the initial profile
set deliberately small; later demo and hosted providers extend the same policy
without replacing it.

### Implementation decisions and open questions

- Pairing is a deployment-level required/disabled choice in this task, not a
  per-request optional state.
- `local-open` with pairing disabled is rejected unless a clearly named unsafe
  development override is present.
- Unimplemented profiles are not advertised.
- Capabilities are minimally public, but server/session/account information is
  protected.

### Documentation

- Document profile configuration, startup failures, capability fields, client
  behavior, migration, and pairing-on/off threat models.
- Update protocol examples with both HTTP and WebSocket capability discovery.

### Task checklist

- [ ] Define effective access-policy types and configuration.
- [ ] Implement profile selection and startup validation.
- [ ] Apply pairing-required/disabled behavior to WebSocket paths.
- [ ] Apply the same behavior to HTTP/hybrid paths.
- [ ] Extend capabilities over HTTP and WebSocket.
- [ ] Update SDK/mobile factories and pairing UI.
- [ ] Add migration/error handling for saved connections.
- [ ] Add matrix tests and documentation.

### Requirement verification

- Verify `local-open + pairing required`, `static-token + pairing required`,
  and `static-token + pairing disabled` over all three transports.
- Verify unsafe open/no-pairing and missing-token configurations fail startup.
- Verify pairing-disabled mode never creates or requests a pairing code.
- Verify pairing-required mode cannot be bypassed with only the deployment
  token.
- Verify capabilities and effective client behavior agree.
