# Frontend Refresh Orchestration

Use event-based invalidation and explicit user intent to refresh UI schema/settings only when needed, while keeping message reload focused on messages.

## Requirements checklist

- [ ] Wait until session metadata/UI schema invalidation events exist before removing broad refreshes from message reload.
- [ ] Update mobile/SDK controllers to invalidate UI schema/settings caches from the new event types.
- [ ] Keep manual message reload fast and message-focused after invalidation support is in place.
- [ ] Add explicit refresh behavior for session actions/settings UI when the user opens those surfaces.
- [ ] Deduplicate duplicate UI schema requests between session UI schema and session settings controllers.
- [ ] Add frontend SDK/mobile tests covering message reload, event invalidation, and explicit UI schema refresh.

Parent Task: tasks/20260610-mobile-message-refresh-performance/000-main.md

Depends On: tasks/20260610-mobile-message-refresh-performance/030-session-metadata-ui-schema-invalidation-events.md

## Background

Do not remove UI schema/settings refreshes until the metadata freshness requirement is solved. The current broad refresh exists because server-side metadata changes can happen without an obvious frontend action.

Current behavior:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - `loadMessages({ refreshUiSchema: true })` calls `refreshSessionUiControllers()` before loading messages.
  - Manual reload, dirty-banner reload, action reload, snapshot select/clear/restore, and message limit reload can pass `refreshUiSchema: true`.
- `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts`
  - `load()` fetches `/ui-schema`, `/overrides`, `/config/schema`, and `/config/base` in parallel.
- `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`
  - Separately fetches `/ui-schema`.
- `packages/frontend-sdk/src/uiSchema/sessionApplicationUiSchemaController.ts`
  - Fetches `/application/ui-schema`.

This can create duplicate and competing requests, especially `/ui-schema` being fetched both directly and through settings.

## Implementation Guidance

Once invalidation events exist:

- Message reload should primarily call `/messages` and refresh selected snapshot state as needed.
- UI schema/settings controllers should refresh when:
  - An invalidation event arrives.
  - The user opens session actions/settings UI and the cache is stale or invalidated.
  - A known frontend action changes overrides/config and already knows the cache should be invalidated.

Deduplication options:

- Share `/ui-schema` results between `SessionUiSchemaController` and `SessionSettingsController`.
- Let settings controller accept an externally supplied schema snapshot.
- Introduce a small cache/promise registry keyed by backend/session/path so concurrent loads coalesce.

Tests should verify:

- Manual message reload does not eagerly request schema/settings when there is no invalidation.
- Receiving a session metadata/UI schema invalidation event invalidates the relevant controller caches.
- Opening session actions/settings after invalidation fetches fresh schema/settings.
- Duplicate `/ui-schema` calls are avoided when both controllers need the same data.