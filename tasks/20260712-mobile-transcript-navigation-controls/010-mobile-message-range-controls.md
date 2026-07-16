# Add Mobile Message-Range Controls

Port the desktop contextual history-range controls to mobile, default mobile history to the last 50 messages, and persist the selected range per session.

## Requirements checklist

- [x] New mobile sessions default to `startText = "-50"` and `endText = ""`.
- [x] A cached per-session range overrides the default after hydration.
- [x] The existing arbitrary Python-style range modal continues to work.
- [x] Contextual controls expose older, newer, all, and last-50 actions when each action is applicable.
- [x] The working history window uses a page size of 50 and a maximum range of 100 before sliding, matching desktop.
- [x] A range button reloads the exact requested range without relying on asynchronous React state propagation.
- [x] Range buttons are disabled while messages are loading.
- [x] The selected range survives session switching and persisted-cache hydration.
- [x] Older/newer expansion preserves overlapping visible content where native `maintainVisibleContentPosition` can do so; show-last intentionally returns to the newest edge.

## Task checklist

- [x] Move or expose the pure desktop range planner through `@crystal-lattice/frontend-sdk`.
- [x] Update desktop imports/tests to consume the canonical shared planner without changing desktop behavior.
- [x] Add mobile cache APIs and props for reading and saving `rangeStartText`/`rangeEndText`.
- [x] Initialize mobile range state from cache with a `-50:` fallback.
- [x] Add an explicit range-reload callback that passes planned values directly to `ChatController`.
- [x] Route the existing range modal through the explicit reload callback.
- [x] Render responsive range controls at the visual top and bottom of the inverted transcript.
- [x] Add accessibility labels and loading/disabled presentation.
- [x] Add and run pure, cache, and component tests.
- [x] Update relevant mobile documentation.

Parent Task: `tasks/20260712-mobile-transcript-navigation-controls/000-main.md`

## Context and references

- Existing planner: `desktop/crystal-lattice-control-desktop-rn/src/chat/messageRangeControls.ts`.
- Existing planner tests: `desktop/crystal-lattice-control-desktop-rn/__tests__/messageRangeControls.test.ts`.
- Desktop integration: `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`, around the range state, `applyMessageLimitAndReload`, and transcript header/footer controls.
- Mobile range state and modal: `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`.
- Mobile cache: `mobile/crystal-lattice-control-rn/src/cache/useMessagesCache.ts`, `mobile/crystal-lattice-control-rn/src/cache/types.ts`, and `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx`.
- Shared cache fields already exist in `packages/frontend-sdk/src/storage/sessionScopedMessagesCache.ts`.

## Approved implementation plan

1. Put the pure planner and its public types in the shared frontend SDK and export them from the package entry point.
2. Keep desktop behavior identical while replacing the desktop-local implementation with the shared implementation.
3. Use page size 50 and maximum range 100.
4. Initialize mobile to `-50:` unless a cached range exists.
5. Add explicit `reloadMessagesForRange({startText, endText, reason})` behavior so a one-tap action cannot reload a stale state range.
6. Persist range fields per connection/session using the existing serialized message-cache persistence chain.
7. Derive contextual button presentation from the first and last loaded message indices and the current range.
8. On the inverted list, put older/all controls at the visual top and newer/last controls at the visual bottom, composing them with existing header content rather than replacing it.
9. Keep the arbitrary range modal and have it use the same reload path.
10. Rely first on stable message keys and `maintainVisibleContentPosition` for overlapping-content preservation; avoid importing the desktop scroll coordinator.

## Testing plan

1. Port the existing desktop planner cases to frontend SDK tests: suffix expansion, absolute expansion, capped sliding, end detection, show-all, show-last, labels, and hidden actions.
2. Verify desktop targeted range tests continue to pass against the shared export.
3. Extend mobile cache tests for save, update preservation, and hydration of range fields.
4. Add mobile component tests for button visibility, labels, disabled state, and callbacks.
5. Verify the exact planned range is passed directly to the controller despite asynchronous state updates.
6. Run `npm --workspace @crystal-lattice/frontend-sdk test`.
7. Run the relevant desktop Jest range-control test.
8. Run mobile Jest tests and TypeScript/lint checks.
9. Manually verify older/newer/show-all/show-last behavior on both iOS and Android, including range sliding and viewport preservation.

## Completion Notes

Added during completion on 2026-07-12.

- The planner is now implemented in `packages/frontend-sdk/src/chat/messageRangeControls.ts`; the desktop-local module re-exports it to preserve existing imports.
- Mobile defaults are centralized in `mobile/crystal-lattice-control-rn/src/transcriptRange.ts`.
- `reloadMessagesForRange` passes explicit values directly to the chat controller and optionally returns show-last actions to offset zero.
- Range fields are persisted through `useMessagesCache` and restored by `ConnectedRoot`.
- Shared planner, desktop compatibility, mobile cache, component, TypeScript, and full mobile tests passed.
- Native viewport preservation should still be manually checked on iOS and Android.