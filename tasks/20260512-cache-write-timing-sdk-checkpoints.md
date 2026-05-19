# Cache Write Timing From SDK Checkpoints
Define cache timing from real message lifecycle events in the SDK, then debounce storage flushes without redesigning the cache payload shape.

## Requirements checklist
- [ ] Define cache-worthy message snapshot timing in the SDK instead of React component effects.
- [ ] Stop draft and scroll persistence from forcing full transcript snapshot rewrites.
- [ ] Add debounce/coalescing in the cache persistence layer itself.
- [ ] Apply the same timing model to both desktop and mobile chat surfaces.
- [ ] Add tests that prove partial streaming updates do not trigger message snapshot persistence.

## Context

This task starts after the desktop image viewer was removed from `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx` in the current working tree. The remaining work corresponds to plan steps 2-6 from the investigation:

- move message snapshot timing into shared SDK logic
- keep cache structure large if needed, but control when it is written
- add debounced persistence at the cache layer
- make desktop and mobile use the same policy

## What was inspected

### Desktop cache writes are currently driven by React state changes

- `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:69-78`
  - Every `messagesCache` state change triggers `store.set(STORAGE_KEY_MESSAGES_CACHE, JSON.stringify(messagesCache))`.
- `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts:80-140`
  - `updateMessagesCache` rewrites a full session entry and then replaces the connection entry in the top-level cache object.

### Desktop message snapshot timing is currently tied to `ChatPane` effects

- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:696-718`
  - `persistCacheSnapshot()` reads `chatController.getCacheSnapshot()` and forwards the full snapshot to `onUpdateCache(...)`.
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:720-760`
  - A `useEffect` watches `chatState?.messages`, `chatState?.eventsCursorId`, `chatState?.activeRequestId`, and range text, then persists after a 250 ms timer.
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:762-770`
  - The same snapshot is persisted again on unmount.

### Draft typing and scroll persistence also push full message arrays back into cache

- `desktop/crystal-lattice-control-desktop-rn/src/chat/usePersistedChatDraft.ts:63-89`
  - Draft persistence calls `onUpdateCache(...)` with `messages: getMessagesForCache()` and `composeText`.
  - This currently happens on a 300 ms debounce while typing.
- `desktop/crystal-lattice-control-desktop-rn/src/chat/useProactiveChatScrollPersistence.ts:143-187`
  - Scroll anchor persistence also calls `onUpdateCache(...)` with `messages: getMessagesForCache()` and `scrollAnchor`.
  - This currently happens on a debounced/throttled scroll path and also on unmount.

### Mobile has the same architectural problem

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1356-1367`
  - `syncCacheFromController()` persists the full `getCacheSnapshot()` after reloads and recoveries.
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1715-1742`
  - Another `useEffect` persists based on `chatState.messages`, `chatState.activeRequestId`, and `chatState.dirty`.
  - This is also React-state-driven timing, not SDK-defined checkpoint timing.

### The SDK already knows the lifecycle boundaries that matter

- `packages/frontend-sdk/src/chat/chatController.ts:185-198`
  - `getCacheSnapshot()` exposes the current persisted snapshot shape.
- `packages/frontend-sdk/src/chat/chatController.ts:406-457`
  - `applyEvents()` handles event-driven state changes and already separates message history application from request/streaming state updates.
- `packages/frontend-sdk/src/chat/chatController.ts:490-544`
  - `reloadMessages()` is the definitive full-reload completion path.
- `packages/frontend-sdk/src/chat/streamingStateReducer.ts:87-112`
  - `partial` events update streaming state incrementally.
- `packages/frontend-sdk/src/chat/streamingStateReducer.ts:114-135`
  - `final`, `request_completed`, and `request_cancelled` are already modeled distinctly from partial streaming chunks.

## Recommended direction

### 1. Add SDK-level cache checkpoints

Recommended home: `packages/frontend-sdk/src/chat/chatController.ts`

Add a small cache-checkpoint API so apps can subscribe to "persist-worthy snapshot changed" notifications. This can be either:

- a second subscription on `ChatController`, or
- a dedicated callback/setter similar to `setEventsListener`, or
- a small shared helper wrapping `ChatController.subscribe(...)` but using controller-owned timing rules

Recommended checkpoint reasons:

- `reload_complete`
- `messages_committed`
- `dirty_reload_complete`
- `resume_recovery_complete`
- optionally `request_settled` if `activeRequestId` changes after a meaningful snapshot change

Not cache-worthy:

- `partial` streaming chunks
- composer typing
- scroll changes
- plain React renders

### 2. Keep draft and scroll persistence, but do not make them message snapshot writers

Do not redesign the cache structure in this task. Instead:

- draft persistence should update only `composeText`
- scroll persistence should update only `scrollAnchor`
- message snapshot persistence should come only from SDK checkpoints

This preserves the current cache payload shape while fixing the timing problem.

### 3. Debounce writes in the cache layer

Recommended home: `desktop/crystal-lattice-control-desktop-rn/src/cache/useMessagesCache.ts` and the equivalent mobile cache path.

Keep in-memory cache state immediate, but debounce `store.set(...)` itself. Suggested default:

- message cache flush debounce: 750-1500 ms
- coalesce multiple updates into one serialized write
- force flush on shutdown/unmount paths where practical

The main idea: even valid checkpoint bursts should produce one storage write, not many.

### 4. Apply the same timing policy to mobile

Mobile currently mirrors the same React-driven approach, so the SDK checkpoint model should be adopted there too:

- remove render-effect-driven snapshot persistence from `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- use the same checkpoint subscription model as desktop

## Suggested implementation outline

1. Add a checkpoint-emission API to `ChatController`.
2. Emit checkpoints from:
   - successful `reloadMessages()`
   - event application when message history actually changes
   - dirty/backfill reload completion
3. Make desktop `ChatPane` subscribe to checkpoints instead of watching React state for snapshot writes.
4. Stop `usePersistedChatDraft` and `useProactiveChatScrollPersistence` from passing `messages` into cache updates.
5. Add debounced `store.set(...)` inside `useMessagesCache`.
6. Port the same timing model to mobile.
7. Add regression tests around partial events vs committed messages.

## Test ideas

- Unit tests in `packages/frontend-sdk/src/chat/__tests__/chatController.test.ts`:
  - partial events do not emit cache checkpoints
  - final committed message history changes do emit checkpoints
  - reload success emits one checkpoint
  - request completion without history change does not emit redundant checkpoints
- App-level tests:
  - desktop typing no longer causes repeated message snapshot persistence
  - desktop scroll persistence does not carry `messages`
  - mobile no longer persists snapshots from React-state change effects

## Validation note

A quick TypeScript check after the image-viewer revert hit unrelated pre-existing errors outside this task:

- `desktop/crystal-lattice-control-desktop-rn/node_modules/@crystal-lattice/frontend-sdk/src/backend/restBackend.ts`
  - missing `readonly` / `snapshot_id` properties in inferred response type
- `desktop/crystal-lattice-control-desktop-rn/src/ui/ActionResultInlineCard.tsx`
  - `Theme.shadow` type issue

Those failures are not caused by the viewer revert, but they may affect how verification is run during this task.