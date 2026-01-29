# Extraction map: current RN code → `@crystal-lattice/frontend-sdk`

This maps *existing* code in `mobile/crystal-lattice-control-rn/` to the proposed SDK modules. The intent is to move code with minimal behavior changes, then iterate toward cleaner APIs.

## 1) Low-level protocol + helpers (safe to extract first)

| Current file | What it contains | SDK target |
|---|---|---|
| `mobile/crystal-lattice-control-rn/src/api.ts` | Type-only re-export shim (keeps mobile imports stable). | `packages/frontend-sdk/src/types/*` (already extracted) |
| `mobile/crystal-lattice-control-rn/src/eventsTypes.ts` | Client-side event types. | `packages/frontend-sdk/src/events/types.ts` |
| `mobile/crystal-lattice-control-rn/src/messageUtils.ts` | `selectDisplayContent(message)` fallback logic. | `packages/frontend-sdk/src/messages/displayContent.ts` |
| `mobile/crystal-lattice-control-rn/src/uiSchemaUtils.ts` | `extractByPath`, `renderTemplate`, footer/status filters. | `packages/frontend-sdk/src/ui-schema/utils.ts` |
| `mobile/crystal-lattice-control-rn/src/connectionInfo.ts` | Small helper for connection metadata display. | Keep in UI (presentation), or move to `src/connections/utils.ts` if reused |

## 2) Backend adapters / transport

| Current file | What it contains | SDK target |
|---|---|---|
| `mobile/crystal-lattice-control-rn/App.tsx` | Connection wizard + constructs SDK transports/backends (`FetchTransport`/`BridgeTransport` + `RestAgentBackend`). | `packages/frontend-sdk/src/transport/fetchTransport.ts`, `packages/frontend-sdk/src/transport/bridgeTransport.ts`, `packages/frontend-sdk/src/backend/restBackend.ts` |

Notes:

- `HttpAdapter`/`BridgeAdapter` should be extracted as *transport/backends*, not UI code.
- UI “connection wizard” logic stays in frontends; the SDK just provides the building blocks.

## 3) Headless controllers (biggest reuse win)

### 3.1 Chat controller

Source of logic today:

- `mobile/crystal-lattice-control-rn/src/useSessionEvents.ts` → polling implementation.
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` → message range parsing, send/cancel logic, event application (`partial`/`final`/`tool_results`), and derived status bar fields.
- `mobile/crystal-lattice-control-rn/src/useSessionAgents.ts` → agent list caching.
- `mobile/crystal-lattice-control-rn/src/applicationActionsExecutor.ts` + `src/usePluginActionDialog.ts` → plugin action execution.

SDK targets:

- `packages/frontend-sdk/src/events/pollingEventSource.ts` (headless class)
- `packages/frontend-sdk/src/chat/chatReducer.ts` (pure reducer for applying events)
- `packages/frontend-sdk/src/chat/chatController.ts` (state + actions)

Additional SDK targets to make the RN screen representation-only:

- `packages/frontend-sdk/src/ui-schema/sessionUiSchemaController.ts` (load/caching of per-session schema)
- `packages/frontend-sdk/src/chat/presentation.ts` (pure helpers for status bar/footer derivation)
- `packages/frontend-sdk/src/plugins/actionRunner.ts` (execute plugin action and return typed `effects`)
- `packages/frontend-sdk-react/src/useHydrateControllerFromCache.ts` (deduplicate hydration boilerplate in UIs)

### 3.2 Sessions controller

Source of logic today:

- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx` → reload, caching timestamps, create session, derive title/subtitle/meta from plugin-provided `session_list_field` schema.

SDK targets:

- `packages/frontend-sdk/src/sessions/sessionsController.ts`
- `packages/frontend-sdk/src/ui-schema/sessionListDerivation.ts` (pure derivation helpers)

Additional SDK targets:

- `packages/frontend-sdk/src/sessions/staleness.ts` or a method on `SessionsController` (`loadIfStale`)
- `packages/frontend-sdk/src/plugins/actionRunner.ts` (reuse the same effects model)

### 3.3 Plugins registry

Source today:

- `mobile/crystal-lattice-control-rn/src/ApplicationPluginsContext.tsx` → load actions + UI schema and categorize by `ui_type`, plus caching by connection id.

SDK targets:

- `packages/frontend-sdk/src/plugins/pluginsRegistry.ts` (headless, no React context)

## 4) Persistence: connections and per-frontend preferences

Today this is spread across:

- `mobile/crystal-lattice-control-rn/App.tsx` (saved connections + sessions/messages caches)
- `mobile/crystal-lattice-control-rn/src/PinnedActionsContext.tsx` and `src/usePersistentPinnedActions.ts`

SDK targets:

- `packages/frontend-sdk/src/storage/keyValueStore.ts` (interfaces)
- `packages/frontend-sdk/src/connections/connectionStore.ts` (persist/rehydrate `ConnectionRecord[]`)
- `packages/frontend-sdk/src/preferences/pinnedActionsStore.ts` (persist pinned action lists)

The RN app becomes responsible for providing the platform store implementation (e.g. AsyncStorage), but the data format and logic live in the SDK.
