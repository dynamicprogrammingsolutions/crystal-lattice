# Phase 4.5 — Event contract + reducer-driven message state (no full session in events)

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/050-phase-4-headless-controllers.md`

This phase hardens correctness by making events minimal and reducer-applied.

It is tracked as a standalone task directory because it spans Python + TypeScript SDK + RN UI:

- `tasks/20260129-events-no-full-session/000-main.md`

## Status

- [ ] Not started

## What this phase does (summary)

- Remove full session payloads from all events.
- Ensure append/modify/delete events include enough information to mutate local session state.
- Add a pure message-history reducer to `@crystal-lattice/frontend-sdk`.
- Add a `dirty` fallback that triggers a manual reload only when incremental apply fails.
- Remove unconditional message reloads from the frontend.
