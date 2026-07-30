# Add Mobile Transcript Edge Buttons

Add small but comfortably clickable chevron-up and chevron-down controls that navigate to the visual top and bottom of the mobile inverted transcript.

## Requirements checklist

- [x] A chevron-up button is shown only when the visual top is meaningfully away.
- [x] A chevron-down button is shown only when the visual bottom is meaningfully away.
- [x] Buttons use `chevron-up` and `chevron-down`, not arrow icons.
- [x] Buttons are as visually small as practical while retaining an easy touch target.
- [x] Buttons do not obscure the composer, range controls, or important message content.
- [x] Scroll-to-bottom uses inverted-list offset zero and resumes normal pinned-bottom behavior after arrival.
- [x] Scroll-to-top reaches the oldest loaded content and detaches the saved anchor from the bottom.
- [x] Button navigation is one-shot intent and does not introduce a persistent desktop-style scroll lock.
- [x] Existing streaming and `maintainVisibleContentPosition` behavior remains intact.

## Task checklist

- [x] Add a pure inverted-transcript geometry helper.
- [x] Track content height, viewport height, offset, top gap, and bottom gap from layout/content/scroll callbacks.
- [x] Update React affordance state only when edge availability changes.
- [x] Add named `scrollToTranscriptTop` and `scrollToTranscriptBottom` callbacks with inverted-list command mapping.
- [x] Add a relatively positioned transcript frame and compact floating chevron buttons.
- [x] Add accessibility labels, roles, and stable test IDs.
- [x] Ensure the visual control is compact while the pressable hit area remains easy to target.
- [x] Add pure geometry and component interaction tests.
- [x] Run mobile tests, type checks, and lint checks.
- [x] Document platform/manual verification findings.

Parent Task: `tasks/20260712-mobile-transcript-navigation-controls/000-main.md`

Depends On: `tasks/20260712-mobile-transcript-navigation-controls/010-mobile-message-range-controls.md`

## Context and references

- Mobile inverted-list scroll anchor helpers: `mobile/crystal-lattice-control-rn/src/chatScroll.ts`.
- Current offset tracking and restoration: `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`, around `handleListScroll` and `maybeRestoreScroll`.
- Current list wrapper: `mobile/crystal-lattice-control-rn/src/components/DependencyFlatList.tsx`.
- Desktop visual reference: floating edge buttons in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.
- For mobile's inverted list, `contentOffset.y === 0` is the visual bottom; the visual top is at `contentHeight - viewportHeight`.

## Approved implementation plan

1. Add a pure helper that clamps native metrics and derives top/bottom gaps and edge-button availability for an inverted list.
2. Feed the helper from `onScroll`, `onLayout`, and `onContentSizeChange`.
3. Keep continuously changing offsets in refs, but update component state only when `canScrollToTop`, `canScrollToBottom`, or pinned status changes.
4. Map visual-bottom navigation to `scrollToOffset({offset: 0, animated: true})`.
5. Map visual-top navigation to `scrollToEnd({animated: true})`.
6. Wrap the transcript in a relatively positioned frame and overlay controls on the right.
7. Use a compact circular visual surface with `chevron-up`/`chevron-down`; retain approximately a 44-point pressable area through the outer pressable or `hitSlop`.
8. Position the lower control above the composer and provide enough transcript inset that controls do not make content unusable.
9. Let confirmed native metrics update bottom affinity and saved anchors; do not add a persistent navigation lease or port desktop convergence behavior.
10. Preserve `maintainVisibleContentPosition` for streaming and bottom following.

## Testing plan

1. Pure tests: offset zero, middle, maximum offset, short content, viewport larger than content, clamping, and exact threshold boundaries.
2. Component tests: neither/one/both controls visible, chevron names, accessibility labels, and correct callbacks.
3. Verify scroll-to-bottom calls offset zero and scroll-to-top calls the inverted-list end method.
4. Verify bottom navigation updates pinned state after native metrics and top navigation leaves it detached.
5. Run mobile Jest tests, TypeScript, and lint.
6. Manually verify on iOS and Android with short and long transcripts, middle position, streaming at and away from bottom, keyboard open/closed, and range changes.

## Completion Notes

Added during completion on 2026-07-12.

- Added `deriveInvertedTranscriptScrollState` and named top/bottom command helpers in `mobile/crystal-lattice-control-rn/src/invertedTranscriptScroll.ts`.
- Added 34-point circular chevron surfaces with 8-point hit slop, accessibility labels, and stable test IDs.
- The top command maps to `scrollToEnd`; the bottom command maps to offset zero.
- Scroll affordance React state changes only when top/bottom availability or pinned status changes.
- Pure geometry, command mapping, component interaction, full mobile Jest, and TypeScript checks passed.
- The lint command was attempted but the package has no ESLint configuration; this pre-existing tooling gap is recorded rather than bypassed.
- No iOS or Android simulator/device manual run was performed; the manual scenarios in the testing plan remain recommended.