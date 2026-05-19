# Desktop Warm Tabs And Session Cache

Break the desktop tab/cache work into focused subtasks so implementation can preserve the 3-tab warm model, reduce cache persistence cost, and make close-time saves cheaper.

## Task checklist

- [x] `tasks/20260513-desktop-warm-tabs-and-session-cache/010-render-only-warm-tabs.md`
- [ ] `tasks/20260513-desktop-warm-tabs-and-session-cache/020-session-scoped-message-cache-persistence.md`
- [ ] `tasks/20260513-desktop-warm-tabs-and-session-cache/030-desktop-file-backed-cache-storage.md`
- [ ] `tasks/20260513-desktop-warm-tabs-and-session-cache/040-dirty-close-save-suppression.md`

## Context

Current investigation findings:

- The 3-tab warm behavior is hard-coded by `RECENT_ACTIVE_TAB_COUNT = 3` in `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:14`.
- `ChatPaneTabStack` currently renders every tab pane and only hides older ones with styles, so tabs older than the warm set are still part of the component tree. See `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:145-178` and `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:189-203`.
- `ChatPane` uses `isActive` to control event polling and session UI/schema work. The controller is created in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:307-314`, and active-only schema/settings hooks are enabled in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:390-407`.
- `useChatController` stops polling when `eventsEnabled` is false and starts polling when active state and cached snapshot permit it. See `packages/frontend-sdk-react/src/useChatController.ts:70-104`.
- Closing or unmounting a pane currently triggers multiple persistence paths:
  - chat snapshot flush in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:762-770`
  - draft flush in `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts:162-166`
  - scroll-anchor flush in `desktop/crystal-lattice-control-desktop-rn/src/chat/useProactiveChatScrollPersistence.ts:253-260`
- `useMessagesCache` currently persists the entire cache map to one AsyncStorage key with `JSON.stringify(messagesCache)` in `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:69-78`.
- The desktop app currently has no existing file-backed cache adapter or file-system dependency for React Native macOS. `desktop/crystal-lattice-control-desktop-rn/package.json` only includes `@react-native-async-storage/async-storage` for this storage layer.
- The generic storage contract is still `get/set/delete` in `packages/frontend-sdk/src/storage/keyValueStore.ts:1-5`, so any true file-backed cache should likely be a desktop-specific adapter rather than a global contract change.

## Notes

- Tests should be added as part of the relevant subtask rather than as a separate follow-up task.
- The task files below intentionally preserve the current 3-tab warm behavior for the most recent tabs; only tabs older than the warm set should be unmounted.