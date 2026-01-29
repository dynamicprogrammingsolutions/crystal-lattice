# Phase 2 — Backend interface + REST backend implementation

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/020-phase-1-types-and-helpers.md`

Unify all “talk to the server” operations behind an SDK-owned `AgentBackend` interface, and implement it with the current Python REST API.

## Status

- [x] Completed on branch `frontend-sdk`.

## Required outcomes (what should be true)

- Mobile app does not call the old `src/api.ts` endpoints directly.
- Backend calls flow through `AgentBackend`.

## What exists today

### Core interface

- `AgentBackend` is defined in `packages/frontend-sdk/src/backend/backend.ts`.
- `BackendCapabilities` exists so frontends can conditionally enable features that are not yet supported by the REST server (e.g., feature completions).

### REST implementation

- `RestAgentBackend` is implemented in `packages/frontend-sdk/src/backend/restBackend.ts`.
- It uses a pluggable `Transport` (`packages/frontend-sdk/src/transport/transport.ts`).

### Capability gaps (important for later VS Code / terminal parity)

- `RestAgentBackend.getCapabilities()` currently returns `featureCompletions: false` and `applicationConfig: false`.
- The plan docs call out missing server endpoints for these.

## Verification / smoke checks

- In the RN app, sending / loading sessions should work with `RestAgentBackend`.
- Confirm the mobile app imports the SDK backend rather than `mobile/.../src/api.ts`.

## Implementation notes (deviations)

- Phase 2 and Phase 3 were implemented together: the REST backend was made transport-agnostic, then bridge support was added by providing `BridgeTransport`.

## Relevant commits

- `b89ae1a` Refactor to replace `ConnectionAdapter` with `AgentBackend` in application logic.
- `72a1b4c` Migrate RN app to use SDK Transport and AgentBackend; add BridgeTransport; remove local adapters/shims.
