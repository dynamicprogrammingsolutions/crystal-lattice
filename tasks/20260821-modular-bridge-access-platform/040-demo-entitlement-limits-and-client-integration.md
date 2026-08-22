# Demo Entitlement, Limits, And Client Integration

Deliver the first complete external-provider vertical slice from mobile and
terminal/server clients through bridge authorization and enforced limits over
WebSocket, HTTP, and hybrid transports.

## Requirements checklist

### Functional requirements

- [ ] **P1** — Mobile and terminal/server clients obtain and refresh demo trial
  or challenge access grants.
- [ ] **P1** — The demo provider and bridge enforce entitlement expiration and
  configurable server, session, transfer, request-size, and data-window limits,
  with visibly different base and higher-limit tiers.
- [ ] **P1** — Demo-provider access works with pairing required and pairing
  disabled.

### Non-functional requirements

- [ ] **P1** — Entitlement and limit enforcement is equivalent across
  WebSocket, HTTP, and hybrid transports.
- [ ] **P1** — Demo credentials and grants use secure storage and do not appear
  in ordinary connection persistence or logs.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/030-replaceable-access-providers-and-demo-challenge-service.md`
- `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`

## Specifications and requirements

- `docs/development/specifications/bridge-access-control/index.md`:
  `BAC-004`, `BAC-005`, `BAC-007`, `BAC-009`, `BAC-011`, `BAC-012`,
  `BAC-013`, `BAC-014`
- `docs/development/specifications/bridge-connectivity/index.md`:
  `BRG-015`, `BRG-018`

## Required reading

- Mobile connection flow in `mobile/crystal-lattice-control-rn/App.tsx`
- `packages/frontend-sdk/src/transport/bridgeConnectionTransport.ts` on the
  mixed-transport branch
- Bridge registries, sessions, WebSocket channels, HTTP router, and transfer
  coordinator
- Python `BridgeClient` registration and reconnect behavior

## Supporting details

Minimum reusable enforcement boundaries:

- registered servers per subject;
- active app-to-server sessions per subject;
- active transfers/requests per subject;
- request and response size;
- transferred bytes per configurable window;
- explicit lease acquisition/release;
- idempotent usage reporting.

The demo implementation may use simple persistent coordination, but bridge
hooks and public schemas must permit a later distributed provider. The merged
HTTP transfer byte streams are the accounting source for HTTP and hybrid
traffic; do not create a parallel transfer mechanism.

Usage windows range from short injected test intervals to multi-day intervals
and are not coupled to calendar months. End-to-end provider-replacement tests
must prove that changing providers does not change transport protocols.

## Execution plan

Status: Draft

Add client-facing demo trial/challenge flows, issue app- and server-scoped
grants, and wire normalized decisions into bridge registration, discovery,
session creation, resume, and byte transfer. Exercise pairing both on and off.
Expose clear status and limit errors rather than generic connection failures.

### Implementation decisions and open questions

- The first-use trial defaults to 24 hours but tests use injected short clocks.
- Usage-window duration is independent from grant duration.
- Hard limits reject new servers, sessions, or transfers; they do not terminate
  a valid in-progress request solely because another operation reaches a cap.
- Demo limit values remain configurable examples.

### Documentation

- Add mobile and terminal demo walkthroughs, trial/challenge states, pairing
  variants, limit meanings, reset windows, error codes, and troubleshooting.
- Document which state is local demo state versus stable public contract.

### Task checklist

- [ ] Add mobile trial/challenge/status UI and secure credentials.
- [ ] Add terminal/server demo grant and refresh flow.
- [ ] Bind server registration and visibility to demo subject.
- [ ] Implement server/session/transfer leases and usage batches.
- [ ] Meter WebSocket and HTTP/hybrid data paths consistently.
- [ ] Enforce configurable windows and tier changes.
- [ ] Add explicit protocol and UI errors.
- [ ] Add unit, integration, cluster, mobile, and E2E tests.
- [ ] Add user and maintainer documentation.

### Requirement verification

- Run trial, expiry, five-question renewal, and ten-question upgrade flows.
- Prove base limits reject behavior that the higher tier allows.
- Prove usage survives reconnect and does not double-count retried batches.
- Prove pairing-required cannot be bypassed and pairing-disabled never prompts.
- Run equivalent proxied requests through WebSocket, HTTP, and hybrid modes.
- Prove one subject cannot access another subject's server.

### Additional implementation verification

- Restart the demo provider and bridge during active/expired windows.
- Exercise provider timeout and temporary unavailability.
- Inspect logs, saved mobile records, and terminal profiles for credential
  leakage.
