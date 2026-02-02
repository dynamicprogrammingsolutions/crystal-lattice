# Phase 4 — Headless controllers (logic/UI separation)

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/040-phase-3-bridge-transport.md`

Extract screen logic into headless SDK controllers so frontends are largely “representation-only”.

This is the major milestone enabling multiple frontends with minimal duplicated logic.

## Status

- [x] Phase 4.1 complete (chat controller)
- [x] Phase 4.2 complete (sessions controller)
- [x] Phase 4.3 complete (plugins registry)
- [x] Phase 4.4 complete (scroll anchoring; see `tasks/20260129-frontend-sdk/060-phase-4-4-chat-persistence-scroll-reconcile.md`)

## Phase 4.1 — Chat controller

### What exists

- Core controller: `packages/frontend-sdk/src/chat/chatController.ts`
- Polling events source: `packages/frontend-sdk/src/events/pollingEventSource.ts`
- Presentation helpers:
  - `packages/frontend-sdk/src/chat/presentation.ts`
- Range parsing helpers:
  - `packages/frontend-sdk/src/utils/range.ts`

React bindings:

- `packages/frontend-sdk-react/src/useChatController.ts`
- `packages/frontend-sdk-react/src/useSessionEvents.ts` (standalone polling hook, used by shims)

RN integration:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` delegates most stateful logic to the controller.

### Known behavior notes

- Event streaming start is intentionally delayed until an initial snapshot exists (cursor or messages) to avoid mount-time churn and reduce the risk of “stuck loading” when cursor is temporarily null.
  - Implemented by `760a16a`.

## Phase 4.2 — Sessions controller

### What exists

- `packages/frontend-sdk/src/sessions/sessionsController.ts`
- Session list presentation helpers:
  - `packages/frontend-sdk/src/sessions/sessionListPresentation.ts`

React bindings:

- `packages/frontend-sdk-react/src/useSessionsController.ts`

RN integration:

- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx` delegates loading/staleness and creation to the controller.

## Phase 4.3 — Plugins registry and action semantics

### What exists

- Headless plugin registry: `packages/frontend-sdk/src/plugins/pluginsRegistry.ts`
- Action runner returning typed “effects”: `packages/frontend-sdk/src/plugins/actionRunner.ts`
- Session UI schema controller:
  - `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`
- Agents controller:
  - `packages/frontend-sdk/src/agents/agentsController.ts`

React bindings / wrappers:

- `packages/frontend-sdk-react/src/applicationPlugins.tsx` (replaces old mobile context)
- `packages/frontend-sdk-react/src/useSessionUiSchemaController.ts`
- `packages/frontend-sdk-react/src/useAgentsController.ts`
- `packages/frontend-sdk-react/src/usePluginActionDialog.ts`

RN integration uses shims to preserve old import paths:

- `mobile/crystal-lattice-control-rn/src/ApplicationPluginsContext.tsx` (re-export shim)
- `mobile/crystal-lattice-control-rn/src/useSessionEvents.ts` (re-export shim)
- `mobile/crystal-lattice-control-rn/src/usePluginActionDialog.ts` (re-export shim)

### Cleanup performed

- Removed no-longer-used mobile-local helpers:
  - `mobile/crystal-lattice-control-rn/src/useSessionAgents.ts`
  - `mobile/crystal-lattice-control-rn/src/applicationActionsExecutor.ts`

## Verification checklist

- [x] Mobile app builds with the SDK packages
- [x] Sessions list loads via `SessionsController`
- [x] Chat loads/sends via `ChatController`
- [x] Plugin schema/actions load via SDK registry wrappers
- [x] Bridge and manual connections still work

## Implementation notes (deviations / follow-ups)

- Metro required explicit extraNodeModules mapping for workspace packages (commit `49621fa`).
- The refactor improved separation, but some UX issues remain and are grouped into Phase 4.4:
  - scroll restoration defaults to top too often (fixed in Phase 4.4)
  - cache snapshots lag behind event-applied state (addressed in Phase 4.5)
  - send still does an eager reload (addressed in Phase 4.5)

## Relevant commits

- `2acc7b2` Phase 4 scaffold: headless controllers and React hooks
- `44c665d` Wire RN screens to ChatController and SessionsController
- `b494458` Plan: define representation-only boundaries
- `50efbef` Move view-model helpers, schema controller, and action effects into SDK
- `ef1c870` Extract agents controller and dialog hook; push range parsing into ChatController
- `267473c` Cleanup: remove unused mobile agent/action helpers
- `49621fa` Fix Metro resolution for workspace SDK packages
- `760a16a` Fix chat polling start to avoid send hang and improve tab switch performance
- `b4374cf` Mobile chat: inverted FlatList + scroll anchor persistence

## Additional references

- Representation-only guidelines: `plans/frontend-sdk/08-ui-representation-boundaries.md`
