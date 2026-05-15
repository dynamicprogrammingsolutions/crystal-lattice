# Render Only Warm Tabs

Keep the current 3-tab warm model, but stop rendering chat panes for tabs older than the most recent 3 while leaving every tab visible in the tab strip.

## Requirements checklist

- [x] Preserve the current warm-tab behavior for the most recent 3 tabs.
- [x] Keep all tabs visible in the tab strip UI.
- [x] Render and mount `ChatPane` only for warm tabs; tabs older than the warm set must be absent from the component tree.
- [x] Preserve current `isActive` behavior for the warm set so polling, schema loading, and cached controller state still behave the same for those 3 tabs.
- [x] Add or update tests that verify opening a 4th+ tab keeps all tab labels visible while only 3 panes remain mounted.

Parent Task: `tasks/20260513-desktop-warm-tabs-and-session-cache/000-main.md`

## Execution plan

Added during task completion on 2026-05-13 after plan approval.

1. Refactor `ChatPaneTabStack` so warm-tab membership is derived synchronously from the prior MRU list plus current `tabs` and `activeTabId`, avoiding effect-delayed warm-set updates.
2. Keep the current 3-tab warm model, but render `TabFrame` only for tabs in the warm set while leaving `SessionTabs` unchanged so every tab label remains visible in the strip.
3. Preserve current `isActive` semantics for mounted warm tabs and continue passing cached session/message data so cold tabs can remount from cache when they re-enter the warm set.
4. Add a focused desktop test that verifies opening and switching among 4 tabs keeps all labels visible while only 3 panes are mounted, and that selecting a cold tab remounts it into the warm set.

## Current state

- The warm limit lives in `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:14`.
- The MRU logic currently feeds `isActive`, but all panes are still mapped and rendered in `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:145-178`.
- Older tabs are hidden with `opacity: 0` and `display: 'none'` in `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx:189-203` instead of being removed.
- `ChatPane` uses `isActive` to enable event polling and session UI/schema work:
  - controller setup: `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:307-314`
  - schema/settings enable flags: `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:390-407`
- `useChatController` starts and stops polling based on `eventsEnabled` in `packages/frontend-sdk-react/src/useChatController.ts:70-104`.

## Implementation notes

- The simplest target shape is to compute the warm set first, then render `TabFrame` only for tabs whose `tabId` is in that set.
- Keep the active tab in the warm set even if it is not first in visual order.
- Preserve cache lookups by `connectionId/sessionId` so unmounted older tabs can rehydrate when they re-enter the warm set.
- Expect tabs older than the warm set to lose any purely local, non-persisted UI state when they remount. That is acceptable for this task unless another task explicitly persists more of that state.

## Suggested test coverage

- A tab-stack test that opens at least 4 tabs and asserts only the most recent 3 `ChatPane` instances are mounted.
- A regression test that switching back to an older tab brings it back into the warm set and remounts it from cache.
- A test that tab-strip labels and close buttons still render for tabs outside the warm set.

## Completion Notes

Added during task completion on 2026-05-13.

- Updated `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx` to derive the warm MRU set synchronously from current props plus the previous MRU ref, which avoids the old effect-delayed warm-set rendering path.
- Changed the tab stack to render `TabFrame` only for warm tabs while continuing to mark all mounted warm panes as `isActive`, preserving polling and schema-loading behavior for the 3 warm tabs.
- Added `desktop/crystal-lattice-control-desktop-rn/__tests__/ChatPaneTabStack.test.tsx` to verify that opening a 4th tab keeps all tab-strip labels visible while only 3 panes remain mounted, and that selecting an older cold tab remounts it with cached data.
- Verified with `npm test -- --runTestsByPath __tests__/ChatPaneTabStack.test.tsx --runInBand` from `desktop/crystal-lattice-control-desktop-rn`.