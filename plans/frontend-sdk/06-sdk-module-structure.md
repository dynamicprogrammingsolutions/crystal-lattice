# Proposed module structure for `@crystal-lattice/frontend-sdk`

This is a suggested internal layout for the SDK. The exact filenames can change; the key is maintaining dependency direction and keeping UI out of the core.

## 1) Package layout

```
packages/frontend-sdk/
  src/
    index.ts
    types/
      messages.ts
      sessions.ts
      events.ts
      uiSchema.ts
      plugins.ts

    transport/
      transport.ts
      fetchTransport.ts
      bridgeTransport.ts

    backend/
      backend.ts              # AgentBackend interface + capabilities
      restBackend.ts          # REST implementation using Transport

    connections/
      connectionRecord.ts     # saved connection descriptors
      connectionStore.ts      # persist/rehydrate using KeyValueStore

    storage/
      keyValueStore.ts

    ui-schema/
      utils.ts                # extractByPath, renderTemplate
      sessionListDerivation.ts
      sessionUiSchemaController.ts

    plugins/
      pluginsRegistry.ts      # headless cache + categorization
      executeAction.ts        # param_map/fixed_params merge
      actionRunner.ts         # execute plugin action and return typed effects

    events/
      pollingEventSource.ts   # reusable polling loop (setTimeout-based)

    chat/
      chatReducer.ts          # pure event-to-state updates
      chatController.ts
      presentation.ts         # status bar/footer derivation helpers

    sessions/
      sessionsController.ts

    agents/
      agentsController.ts     # list/caching of available agents

    util/
      observable.ts
      errors.ts
      id.ts
      clock.ts
      logger.ts
```

## 2) Dependency direction (important)

Keep dependencies flowing “inward”:

- `transport/*` has no dependencies on `backend/*`.
- `backend/*` depends on `transport/*` and `types/*`.
- `controllers/*` depend on `backend/*`, `types/*`, and `util/*`.
- `connections/*` depends on `storage/*`.
- No module imports React/React Native.

This is what enables:

- Node usage (VS Code)
- React Native usage
- Future web usage
- Testing controllers with mock backends

## 3) Optional React bindings package

```
packages/frontend-sdk-react/
  src/
    index.ts
    useSubscribable.ts
    useChatController.ts
    useSessionsController.ts
    usePluginsRegistry.ts
    useHydrateControllerFromCache.ts
    useAgentsController.ts
    usePluginActionDialog.ts
```

This package depends on `react` and `@crystal-lattice/frontend-sdk`.

It should only provide ergonomic hooks/wrappers, not business logic.
