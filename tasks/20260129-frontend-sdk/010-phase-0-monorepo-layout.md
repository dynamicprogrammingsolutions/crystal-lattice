# Phase 0 — Monorepo layout (no behavior change)

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Create a JS monorepo layout so shared packages can be imported by frontends.

## Status

- [x] Completed on branch `frontend-sdk`.

## What was implemented

- Workspace structure at repo root with `packages/` and per-frontend folders.
- New package directories:
  - `packages/frontend-sdk/` (published name `@crystal-lattice/frontend-sdk`)
  - `packages/frontend-sdk-react/` (published name `@crystal-lattice/frontend-sdk-react`)
- TS configuration allowing frontends to import SDK sources.

## How to verify

- Ensure `packages/frontend-sdk/package.json` exists and has the expected name.
- Ensure the RN app can import `@crystal-lattice/frontend-sdk` without bundler errors.

## Implementation notes (what happened vs plan)

- Although Phase 0 is “no behavior change”, some early commits combined Phase 0 + Phase 1 scaffolding in one go.

## Relevant commits

- `589f610` Modularize project by extracting Crystal Lattice SDK and creating workspace; integrate SDK into mobile app and adjust configurations.
