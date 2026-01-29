# Phase 1 — Extract pure TS helpers + types

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/010-phase-0-monorepo-layout.md`

Extract shared domain types and “pure logic” utilities into `@crystal-lattice/frontend-sdk` so they can be reused across frontends.

## Status

- [x] Completed on branch `frontend-sdk`.

## What was implemented

The SDK now contains shared types and pure helper utilities previously embedded in the RN app.

Examples (not exhaustive):

- Domain types: messages, sessions, events, UI schema
- UI schema utilities: `extractByPath`, `renderTemplate`
- Small presentation utilities (non-React)

Mobile app imports these from `@crystal-lattice/frontend-sdk`.

## Where to look

- SDK exports: `packages/frontend-sdk/src/index.ts`
- Types: `packages/frontend-sdk/src/types/`
- UI schema helpers: `packages/frontend-sdk/src/uiSchema/` (and related helpers)

## How to verify

- Run Metro for the RN app and confirm no local copies are used for these helpers.
- Grep for older paths in mobile and confirm they point to SDK imports.

## Implementation notes (deviations)

- Some “phase 1” extraction happened alongside the `AgentBackend` refactor rather than as a strict separate step.

## Relevant commits

- `589f610` Modularize project by extracting Crystal Lattice SDK and creating workspace; integrate SDK into mobile app and adjust configurations.
- `b89ae1a` Refactor to replace `ConnectionAdapter` with `AgentBackend` in application logic; integrate new backend handling for all session operations.
