# Phase 5 — Desktop frontend (RN macOS)

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/050-phase-4-headless-controllers.md`

Create a new desktop frontend under `desktop/` that reuses `@crystal-lattice/frontend-sdk` controllers/backends.

## Status

- [ ] Not started

## Goal

Add `desktop/crystal-lattice-control-desktop-rn/` (or similar) and get it to:

- connect (manual + bridge)
- list sessions
- open chat
- send messages

All business logic should come from the SDK packages.

## Work checklist

- [ ] Create `desktop/crystal-lattice-control-desktop-rn/` RN project scaffolding
- [ ] Wire dependencies to the workspace packages (`@crystal-lattice/frontend-sdk`, `@crystal-lattice/frontend-sdk-react`)
- [ ] Decide whether to share UI components with mobile (shared UI package) or duplicate initially
- [ ] Implement connection selection UI or reuse the mobile one
- [ ] Verify event streaming and chat controller behaviors on desktop

## Notes

- Desktop UI may diverge. The critical requirement is that UI consumes only `AgentBackend` + controllers.
- Make sure Metro/workspace resolution is configured similarly to the mobile app if using RN + Metro.

## References

- High-level stage definition: `plans/frontend-sdk/04-migration-phases.md`
