# E2EE Protocol And Threat Model

Define a reviewable end-to-end encryption protocol for all bridge transports so
the relay can route traffic without reading user request or response content.

## Requirements checklist

### Functional requirements

- [ ] **P1** — The protocol authenticates the mobile/desktop client and user's
  server during key establishment without treating the six-digit pairing code
  as encryption key material.
- [ ] **P1** — The protocol encrypts application request, response, header,
  path/query, body, and content-bearing error data while exposing only the
  minimal versioned routing metadata required by the bridge.
- [ ] **P1** — The protocol defines interoperable key and session lifecycle
  behavior for WebSocket, HTTP, hybrid, streaming, chunking, reconnect,
  multiple devices, rotation, secure storage, reset, and deletion.

### Non-functional requirements

- [ ] **P1** — The threat model identifies protected content, visible metadata,
  trusted endpoints, compromised components, replay, impersonation, and
  key-loss risks.
- [ ] **P1** — The protocol uses established, maintained, cross-language
  cryptographic algorithms and libraries and includes machine-verifiable test
  vectors.
- [ ] **P1** — Independent security review finds no unresolved critical or high
  issue in the protocol before implementation is approved.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On: `tasks/20260821-modular-bridge-access-platform/040-demo-entitlement-limits-and-client-integration.md`

## Specifications and requirements

- `docs/development/specifications/bridge-e2ee/index.md`:
  `BEE-001` through `BEE-013`

## Required reading

- Current bridge pairing, session, token, and mixed-transfer protocols
- `bridge-elixir/docs/bridge-protocol.md` on the mixed-transport branch
- Mobile deep-link and secure-storage capabilities
- Python bridge-client request/response flow
- Current iOS export-compliance configuration
- Established protocol/library documentation selected during the task

## Supporting details

The six-digit pairing code has insufficient entropy to become an encryption
key. It may authenticate or confirm an ephemeral public-key exchange, but the
design must use an established authenticated key-agreement construction and
authenticated encryption.

The visible envelope may include protocol version, routing/session identifier,
request identifier, sequence/chunk information, ciphertext length, and
delivery flags. It must not expose application paths, prompts, attachments,
headers, model/provider selections, or response contents.

Public and marketing language must remain bounded to the behavior and metadata
limitations the reviewed protocol can prove.

## Execution plan

Status: Draft

Create a cross-package protocol and threat model, perform small
interoperability spikes in React Native and Python, select established
libraries, publish deterministic test vectors, and obtain an independent
security review before implementation is approved.

### Implementation decisions and open questions

- Hosted production requires E2EE; community deployments may require, allow,
  or disable it.
- The bridge operator remains able to observe unavoidable connection and
  traffic metadata; documentation must say so.
- Do not invent cryptographic primitives.
- Decide whether pairing authenticates a Noise-style handshake, a PAKE, or
  another reviewed construction only after interoperability and review.
- Define recovery semantics explicitly; silent server-key replacement is not
  acceptable.

### Documentation

- Complete and maintain the owning protocol/threat-model specification,
  test-vector reference, key lifecycle, compatibility/migration, and
  security-review checklist.
- Prepare precise future marketing text but do not publish it as current
  behavior before Task 070 completes.

### Task checklist

- [ ] Inventory sensitive fields and current transport envelopes.
- [ ] Define adversaries, trust boundaries, metadata leakage, and non-goals.
- [ ] Evaluate established protocols/libraries across RN and Python.
- [ ] Define handshake, keys, envelopes, replay protection, rotation, and
  recovery.
- [ ] Define streaming/chunking and reconnect behavior.
- [ ] Add interoperable proof-of-concept and test vectors.
- [ ] Review export-compliance impact.
- [ ] Obtain independent security review and resolve findings.
- [ ] Finalize protocol and implementation acceptance criteria.

### Requirement verification

- Independent review confirms no unresolved critical/high finding.
- React Native and Python spikes exchange and decrypt published test vectors.
- Threat-model scenarios cover relay compromise, active MITM, replay, device
  loss, server replacement, and stale pairing credentials.
- Protocol examples are machine-validated.
