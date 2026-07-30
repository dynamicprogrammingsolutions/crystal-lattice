# Port Transcript Navigation Controls to Mobile

Add desktop-style message-range controls and compact transcript edge-navigation buttons to the mobile chat screen while preserving mobile's inverted FlatList behavior.

## Requirements checklist

- [x] Mobile history defaults to the last 50 messages (`-50:`), matching desktop.
- [x] Mobile offers contextual controls for older, newer, all, and last-page ranges.
- [x] Mobile offers compact, easily clickable chevron-up and chevron-down buttons for navigating to the loaded transcript edges.
- [x] Range and edge-navigation behavior remains accessible, tested, and compatible with streaming, cache restoration, and the existing arbitrary-range modal.
- [x] Cross-platform Detox coverage verifies transcript top/bottom navigation on an iOS Simulator and Android Emulator.

## Task checklist

- [x] `tasks/20260712-mobile-transcript-navigation-controls/010-mobile-message-range-controls.md`
- [x] `tasks/20260712-mobile-transcript-navigation-controls/020-mobile-transcript-edge-buttons.md`
- [x] `tasks/20260712-mobile-transcript-navigation-controls/030-cross-platform-detox-transcript-scroll-tests.md`

## Context and current state

- Desktop range planning currently lives in `desktop/crystal-lattice-control-desktop-rn/src/chat/messageRangeControls.ts` and is covered by `desktop/crystal-lattice-control-desktop-rn/__tests__/messageRangeControls.test.ts`.
- Desktop defaults to `-50:` and exposes contextual older/newer/all/last controls from `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.
- Mobile already has a Python-style range modal in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`, but currently defaults to an open range and does not expose contextual range buttons.
- The shared cache type already contains `rangeStartText` and `rangeEndText` in `packages/frontend-sdk/src/storage/sessionScopedMessagesCache.ts`; mobile does not yet wire those fields through its cache API.
- Mobile uses an inverted `DependencyFlatList`. In its coordinates, offset zero is the visual bottom and the maximum offset is the visual top.
- Mobile currently relies on `maintainVisibleContentPosition` and simple bottom-gap persistence. This task does not port the desktop macOS scroll coordinator.

## Approved implementation plan

1. Complete `tasks/20260712-mobile-transcript-navigation-controls/010-mobile-message-range-controls.md`.
2. Complete `tasks/20260712-mobile-transcript-navigation-controls/020-mobile-transcript-edge-buttons.md`.
3. Share pure range-planning behavior where practical, while keeping platform-specific visual and scroll implementations local.
4. Preserve mobile's inverted-list model and existing bottom-follow behavior instead of introducing the desktop convergence coordinator.
5. Update this main checklist as each subtask is completed.

## Testing plan

1. Run shared frontend SDK pure tests, including range-planning coverage.
2. Run mobile unit/component tests for cache persistence, range controls, inverted geometry, and edge-button actions.
3. Run targeted desktop range-control tests if desktop starts consuming shared range logic.
4. Run mobile TypeScript and lint checks for changed files or the package, reporting unrelated existing failures separately.
5. Manually verify on iOS and Android when available: short and long histories, all edge-button visibility states, streaming at and away from the bottom, range expansion/sliding, show-last navigation, and keyboard/composer overlap.

## Completion Notes

Added during completion on 2026-07-12.

- Shared the canonical range planner through `@crystal-lattice/frontend-sdk` while retaining the desktop import surface.
- Added mobile last-50 defaults, persisted per-session ranges, contextual range controls, inverted-list geometry, and compact chevron edge controls.
- Kept mobile's existing `maintainVisibleContentPosition` behavior and did not port the desktop convergence coordinator.
- Automated verification passed: frontend SDK 187 tests, mobile 69 tests, focused mobile 17 tests after final refinements, desktop range 15 tests, mobile TypeScript, Prettier, and `git diff --check`.
- `npm run lint` was attempted but could not run because the mobile package currently has no ESLint configuration file.
- iOS and Android manual platform checks remain recommended; no native mobile harness exists in this package and no device/simulator run was performed in this completion.
- Reopened on 2026-07-12 for the approved Detox follow-up in `tasks/20260712-mobile-transcript-navigation-controls/030-cross-platform-detox-transcript-scroll-tests.md`.
- The Detox follow-up is complete. A shared 300-message production viewport harness passes on iPhone 17 Pro/iOS 26.1 and Android AVD `Medium_Phone_API_36.1`.
