# Phase 3 — Bridge transport extraction (Phoenix protocol)

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/030-phase-2-agentbackend-restbackend.md`

Extract the “bridge mode” transport logic (previously embedded in the RN app) into `@crystal-lattice/frontend-sdk`.

The bridge protocol proxies HTTP-like requests over WebSocket/Phoenix. The chosen design is:

- `BridgeTransport` implements `Transport`.
- `RestAgentBackend` composes over `Transport`.

## Status

- [x] Completed on branch `frontend-sdk`.

## What exists today

- `Transport` interface: `packages/frontend-sdk/src/transport/transport.ts`
- REST transport (fetch): `packages/frontend-sdk/src/transport/fetchTransport.ts`
- Bridge transport: `packages/frontend-sdk/src/transport/bridgeTransport.ts`

Mobile app wiring:

- Mobile selects between fetch/bridge transport based on the chosen connection record.
- The same `RestAgentBackend` is used; only the transport changes.

## Verification / smoke checks

- Manual connection (HTTP) should work.
- Bridge connection (server via bridge) should work.

## Implementation notes (deviations)

- Workspace + Metro resolution issues required a follow-up fix (not part of Phase 3 originally):
  - `49621fa` adds `resolver.extraNodeModules` mappings in `mobile/crystal-lattice-control-rn/metro.config.js`.

## Relevant commits

- `72a1b4c` Add BridgeTransport; remove local adapters/shims.
- `49621fa` Fix Metro resolution for workspace SDK packages.
