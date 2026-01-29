# Frontend SDK extraction + multi-frontend architecture (phases 0–6)

Create and maintain a shared SDK (`@crystal-lattice/frontend-sdk` + optional `@crystal-lattice/frontend-sdk-react`) so multiple frontends (RN mobile, RN desktop, VS Code extension, etc.) can share non-UI business logic behind clean interfaces.

This task directory is a standalone handoff of the *current plan* (with all phases/stages) and what has already been implemented on the current branch.

## Status checklist (authoritative)

- [x] Phase 0: Monorepo layout (no behavior change)
- [x] Phase 1: Extract pure TS helpers + types
- [x] Phase 2: Extract REST client and backend interface (`AgentBackend` + `RestAgentBackend`)
- [x] Phase 3: Extract Bridge transport (Phoenix protocol → `BridgeTransport` implementing `Transport`)
- [x] Phase 4.1: Chat controller + representation-only chat screen
- [x] Phase 4.2: Sessions controller + representation-only sessions screen
- [x] Phase 4.3: Plugins registry + action runner + React wrappers
- [ ] Phase 4.4: Chat persistence + scroll anchoring + reconcile-on-completion (planned, not implemented)
- [ ] Phase 5: Desktop frontend (RN macOS)
- [ ] Phase 6: VS Code extension (future)

## Subtasks

- `tasks/20260129-frontend-sdk/010-phase-0-monorepo-layout.md`
- `tasks/20260129-frontend-sdk/020-phase-1-types-and-helpers.md`
- `tasks/20260129-frontend-sdk/030-phase-2-agentbackend-restbackend.md`
- `tasks/20260129-frontend-sdk/040-phase-3-bridge-transport.md`
- `tasks/20260129-frontend-sdk/050-phase-4-headless-controllers.md`
- `tasks/20260129-frontend-sdk/060-phase-4-4-chat-persistence-scroll-reconcile.md`
- `tasks/20260129-frontend-sdk/070-phase-5-desktop-frontend.md`
- `tasks/20260129-frontend-sdk/080-phase-6-vscode-extension.md`

## Where things live (current repo state)

- SDK core: `packages/frontend-sdk/`
- Optional React bindings: `packages/frontend-sdk-react/`
- Existing mobile app: `mobile/crystal-lattice-control-rn/`
- Plans and design notes: `plans/frontend-sdk/`

## Current branch + key commits

All completed work referenced by these tasks exists on branch `frontend-sdk`.

Notable commits (ordered newest → oldest):

- `e20ccba` Phase 4.4 plan doc added
- `760a16a` Fix chat polling start (helps “send hangs” and improves transition performance)
- `49621fa` Fix Metro workspace resolution for SDK packages
- `2acc7b2`, `44c665d`, `50efbef`, `ef1c870`, `267473c` Phase 4 controller extraction + wiring + cleanup
- `72a1b4c` Bridge transport + transport/backend wiring in mobile
- `b89ae1a` `AgentBackend` integration in app logic
- `589f610` Monorepo + initial SDK extraction/wiring
- `688842a` Original plan docs + proposed interfaces

## High-level architecture (current)

- Frontends should depend on **domain operations** via `AgentBackend` rather than calling routes directly.
- Transports are pluggable via `Transport`:
  - REST: `FetchTransport` (RN/web/node)
  - Bridge: `BridgeTransport` (RN/websocket)
- `RestAgentBackend` composes over `Transport`.
- UI logic is moved into headless controllers:
  - `ChatController`
  - `SessionsController`
  - `PluginsRegistry`
  - `AgentsController`
  - `SessionUiSchemaController`

## Implementation notes (deviations / gotchas)

- Metro: workspace packages require explicit mapping (`resolver.extraNodeModules`) in `mobile/crystal-lattice-control-rn/metro.config.js` (commit `49621fa`).
- Event polling start: event streaming is started only after an initial snapshot is present (cursor or messages) to avoid mount-time work and “stuck loading” risks (commit `760a16a`).
- TypeScript in RN: `npx tsc -p mobile/crystal-lattice-control-rn/tsconfig.json --noEmit` currently reports missing `.d.ts` for syntax highlighter packages; this was pre-existing and intentionally not addressed.

## References (extra context)

The tasks are self-contained, but these plan docs contain deeper rationale:

- `plans/frontend-sdk/04-migration-phases.md`
- `plans/frontend-sdk/08-ui-representation-boundaries.md`
- `plans/frontend-sdk/09-chat-persistence-scroll-and-reconcile.md`
