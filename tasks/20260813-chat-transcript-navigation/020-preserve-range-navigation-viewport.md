# Preserve the viewport across overlapping range navigation

Correct TNAV-013 so Show older and Show newer retain the user's visible place
when their old and new loaded ranges overlap, using shared portable semantics
and separate mobile and desktop native adapters.

## Requirements checklist

- [x] Show older preserves an overlapping visible message index at
  approximately the same viewport-relative offset after the new range renders.
- [x] Show newer provides the same preservation guarantee.
- [x] The correction applies to the production mobile and desktop chat
  surfaces without merging their native scroll implementations.
- [x] Existing page-size, maximum-range, contextual-action, and exact-request
  behavior remains unchanged.
- [x] A later range action, explicit edge navigation, user drag, session
  change, failure, or unmount cannot allow a stale operation to take viewport
  ownership.
- [x] No-overlap, unavailable-anchor, and response-consistency cases use a
  deterministic fallback and never silently restore an unrelated message.
- [x] Native acceptance evidence covers a real overlapping range replacement
  on iOS, Android, and macOS production viewport code.
- [x] TNAV-013 and any additionally satisfied navigation requirements are
  updated with concrete implementation and verification evidence.

Parent Task: `tasks/20260813-chat-transcript-navigation/000-main.md`

Depends On:

- `tasks/20260813-chat-transcript-navigation/010-create-baseline-specification.md`

## Scope

In scope:

- Show older and Show newer;
- operation-scoped visible-message anchor capture and restoration;
- shared pure anchor selection and consistency checks;
- app-local mobile and desktop measurement/scroll adapters;
- focused component and native acceptance harnesses;
- current implementation documentation and TNAV evidence.

Out of scope:

- previous/next user-message controls;
- a new server outline endpoint;
- direct navigation to an arbitrary message index;
- changing range page size or maximum range size;
- normalizing show-all, arbitrary-range, or show-last viewport policy beyond
  preventing regressions.

## Supporting facts

- The shared range planner already creates overlap for ordinary older/newer
  transitions.
- Desktop `DependencyFlatList` already exposes measured
  `getVisibleAnchor()` and bounded `scrollToItemAnchor()` primitives.
- Mobile `DependencyFlatList` currently forwards only the native FlatList ref
  and does not expose measured visible-message anchors.
- Mobile rows are reverse-ordered inside an inverted list; desktop rows remain
  ascending inside its configured inverted list. Portable code must use
  message keys and indices rather than array positions.
- `maintainVisibleContentPosition` is enabled on mobile but has no native
  acceptance evidence for replacing the entire loaded range.
- The message response cursor or read-only snapshot context can detect some
  incompatible responses, but indices are not stable identities across
  history deletion.

## Execution plan

Status: Approved

### Approach

Treat each Show older or Show newer press as one bounded navigation operation,
not as an unrelated range state update followed by best-effort list behavior:

```text
capture visible message anchors
        |
select preferred overlap anchor and issue exact range load
        |
validate the completed operation and response
        |
restore the same message key and viewport offset after render
```

The shared SDK will own only pure portable data and decisions. Mobile and
desktop will expose equivalent imperative viewport capabilities but keep their
measurement, list coordinates, and correction loops local.

### Shared operation model

Add small shared types and pure helpers near the existing range planner:

- a viewport-anchor candidate containing message index and offset from the
  visual viewport top plus an identity witness derived from the old loaded
  message;
- an operation descriptor containing a unique token, action, planned range,
  preferred anchor, fallback candidates, and old response consistency context;
- selection of the first deterministic visible candidate that remains in the
  completed response;
- response validation and deterministic no-overlap fallback selection.

Capture candidates in visual top-to-bottom order. Prefer the topmost visible
message that remains unchanged in the response because restoring it
reconstructs the visible reading context without depending on native list
inversion. Keep other visible candidates as fallbacks if the preferred row
disappears or no longer matches.

The helper will compare message indices against the completed response, never
against frontend array positions. An unchanged cursor or matching read-only
snapshot establishes compatibility directly. If a live cursor changed because
of an append or another unrelated event, the helper may still restore a
candidate whose old identity witness matches the completed message at that
index. If neither response context nor the message witness establishes
compatibility, it will decline exact index restoration rather than targeting a
possibly different message. The witness is transient operation data and does
not become a new public stable-message identity.

### Mobile viewport adapter

Extend the production mobile list wrapper and inverted viewport to:

1. retain stable `msg-<index>` row keys and non-collapsible row measurement
   wrappers;
2. track viewable message rows;
3. measure visible row offsets relative to the viewport;
4. expose asynchronous visible-anchor capture;
5. expose bounded scroll-to-message-anchor behavior that first targets the row
   and then corrects measured offset until stable or budget exhaustion;
6. cancel pending anchor restoration on drag, edge navigation, replacement,
   session change, or unmount;
7. emit concise diagnostics usable by the deterministic native harness.

The adapter will derive and verify the correction direction for the inverted
list through native tests rather than sharing desktop coordinate assumptions.
Existing far-top and bottom commands remain independent.

### Desktop viewport adapter

Reuse the existing desktop `getVisibleAnchor()` and
`scrollToItemAnchor()` implementation. Add an operation-scoped facade to the
desktop scroll hook or chat integration that:

1. captures the visible anchor candidates before loading;
2. keeps durable persisted-scroll restoration separate;
3. restores only the current completed range operation;
4. cancels on existing user-interaction and navigation signals;
5. reports completion, timeout, missing-item, and supersession diagnostics.

Avoid rewriting the desktop coordinator or duplicating its bounded item-anchor
correction loop.

### Chat integration

For each frontend:

1. plan the exact range with the existing shared planner;
2. capture anchors before changing range state or controller messages;
3. allocate a new operation token, superseding any previous token;
4. call the current exact-range reload path;
5. retain the completed response's message indices and consistency context;
6. restore from a post-render effect or operation callback only after the
   target row exists in the new list;
7. finalize or cancel the operation without changing normal bottom affinity or
   durable scroll state accidentally.

Failed loads do not restore. An explicit top/bottom press or user drag cancels
the range operation before taking its own viewport action.

### Verification strategy

Add pure tests for:

- visual-order candidate selection independent of data-array order;
- preferred-anchor survival and fallback-candidate selection;
- no overlap;
- cursor or snapshot incompatibility;
- stale operation completion and supersession.

Add component-level tests for:

- capture occurring before the exact range request;
- restoration occurring only after completed data contains the target index;
- disabled, failed, superseded, and unmounted operations;
- range planning and exact request bounds remaining unchanged.

Extend native production-viewport harnesses with deterministic variable-height
range transitions:

- start with a bounded loaded range and place a known message at a measured
  viewport offset;
- invoke the production Show older path and replace data with its actual
  overlapping range;
- assert the same message index remains visible within a bounded pixel
  tolerance;
- repeat for Show newer;
- start a restoration and supersede it with an edge action or drag;
- run the mobile scenario on iOS and Android and the desktop scenario through
  the macOS UI target.

Retain existing mobile edge-navigation and desktop scroll-persistence tests as
regression coverage.

### Implementation decisions and open questions

- **Decision:** Share pure anchor semantics through the frontend SDK, while
  keeping measurement and scrolling app-local. This matches the existing
  ownership boundary and the requirement for independent frontend
  implementations.
- **Decision:** Preserve offset from the visual viewport top on both platforms.
  Native adapters translate that portable value into their own list
  coordinates.
- **Decision:** Prefer the topmost visible overlapping message and retain the
  remaining visible messages as deterministic fallbacks.
- **Decision:** Treat range navigation as transient operation state, separate
  from persisted scroll anchors and automatic bottom-follow leases.
- **Decision:** Cursor or snapshot incompatibility prevents exact index
  restoration. A changed live cursor alone is not treated as incompatibility
  when the old message witness still matches at the target index. Otherwise
  the operation uses the specified no-overlap fallback and emits diagnostics
  rather than scrolling to an unverified row.
- **Local tuning:** Native pixel tolerance and correction budgets will begin
  with the existing platform anchor tolerances and budgets, then be adjusted
  only from deterministic harness evidence.
- No unresolved material decision blocks approval of this plan.

### Documentation

- Update
  `docs/development/specifications/chat-transcript-navigation/requirements.md`
  with implementation and exact test evidence.
- Update the specification only if implementation reveals that the approved
  portable target is incomplete or contradictory.
- Update mobile and desktop current development/testing documentation with the
  production anchor-operation entry points and native harness commands.
- Keep user-facing documentation concise; this correction changes reliability
  rather than adding a new user control.

### Task checklist

- [x] Add shared viewport-anchor types, selection, validation, and pure tests.
- [x] Add measured anchor capture and bounded item-anchor restoration to the
  mobile production viewport.
- [x] Integrate operation-scoped capture/load/restore into mobile range
  actions.
- [x] Reuse desktop measured-anchor primitives through an operation-scoped
  range-navigation facade.
- [x] Integrate capture/load/restore into desktop range actions.
- [x] Add focused mobile and desktop component tests.
- [x] Extend the mobile production viewport harness for overlapping older and
  newer range transitions.
- [x] Extend the macOS production viewport harness for the same transitions.
- [x] Run shared SDK, mobile, desktop, iOS, Android, and macOS verification.
- [x] Update TNAV requirements, current development docs, implementation
  notes, and completion evidence.

### Requirement verification

- TNAV-013: native iOS, Android, and macOS scenarios invoke Show older and Show
  newer, replace the loaded data, and verify the same message index remains at
  approximately the same viewport-top offset.
- Exact range behavior: component/controller tests assert unchanged planned
  bounds and that capture precedes request execution.
- Ownership separation: code inspection and package tests show only pure
  semantics are shared; each app retains its native adapter.
- Stale-operation safety: tests cover failure, supersession, drag, edge
  navigation, session change, and unmount.
- Regression behavior: existing loaded-edge navigation, bottom affinity,
  range planner, cache, and scroll-persistence suites remain green.

### Additional implementation verification

- `npm --workspace @crystal-lattice/frontend-sdk test`
- Focused and full mobile Jest suites plus `npm run tsc`
- Focused and full desktop Jest suites
- `npm run detox:build:ios` and
  `npm run detox:test:transcript:ios`
- `npm run detox:build:android` and
  `npm run detox:test:transcript:android`
- Focused macOS transcript-navigation UI test, followed by
  `npm run test:macos-ui` when the focused run is stable
- Focused lint/format checks and `git diff --check`; unrelated pre-existing
  package lint failures are reported separately

## Implementation Notes

- Execution approved by the user on 2026-08-14.
- Added shared witnessed-anchor selection and retained read-only snapshot
  context in `ChatController`.
- Mobile now exposes measured visible-message anchors and bounded key-based
  restoration through its production inverted list. Restoration is started
  from a post-render effect so an overlapping key cannot be measured against
  stale pre-reload rows.
- Desktop reuses its existing measured item-anchor correction, now exposing
  all measured visible message anchors and an operation-scoped cancellation
  signal.
- Both chat screens allocate monotonic range-navigation operation IDs and
  invalidate them on drag, loaded-edge navigation, ordinary range reload,
  session change, failure, or unmount.
- Added deterministic production-screen harnesses for mobile and desktop.
- Fast verification passed: frontend SDK 302 tests, mobile 111 tests, desktop
  105 tests, mobile TypeScript, focused follow-up tests, and diff checks.
- Desktop TypeScript remains blocked by three pre-existing errors in attachment
  plugin IDs and `ActionResultInlineCard` theme typing; no changed
  range-navigation file introduces an additional error.
- The first iOS native attempt exposed Detox idleness from the normal event
  poll. The deterministic mobile harness now mounts the production chat as
  inactive while preserving its cached controller, range actions, backend
  loads, and viewport.
- The first macOS UI attempt compiled the app and new test but failed before
  test execution because XCUITest timed out enabling automation mode. A retry
  initialized correctly; subsequent realistic failures exposed and guided the
  desktop bottom-follow race correction.
- Native production-screen acceptance passed on iOS, Android, and macOS for
  both older and newer range transitions. The macOS trace showed that
  content-follow could supersede a range anchor while bottom-pinned; range
  replacement now suppresses exactly its next semantic bottom-follow update.

## Completion Notes

TNAV-013 is implemented on both independent frontend surfaces. Range
navigation captures visible message witnesses before the exact range request,
validates overlap against the completed response, and restores the selected
message from a post-render operation. Mobile uses measured window coordinates
and inverted native-offset correction; desktop reuses its measured item-anchor
adapter with the same correction and suppresses the one semantic bottom-follow
update owned by the range replacement.

Requirement evidence:

- Show older and Show newer preserve overlapping message frames within the
  native acceptance tolerance on iOS, Android, and macOS.
- Shared tests cover candidate ordering, cursor changes, reused-index witness
  rejection, snapshot mismatch, and no overlap.
- Mobile component coverage verifies drag and loaded-edge intents invalidate
  pending range ownership.
- Monotonic operation IDs and adapter cancellation prevent failed,
  superseded, session-switched, unmounted, dragged, or edge-navigated
  operations from restoring stale anchors.
- Existing range-planner tests remain unchanged and passing, demonstrating
  that page size, maximum range, action presentation, and exact bounds were
  not altered.

Verification completed:

- `npm test` in `packages/frontend-sdk`: 43 files, 302 tests passed.
- `npm run tsc` and `npm test -- --runInBand` in the mobile package: typecheck
  passed; 26 suites, 111 tests passed.
- `npm test -- --runInBand` in the desktop package: 20 suites, 105 tests
  passed.
- Mobile production-screen Detox range scenario passed on iOS and Android.
- Desktop production-`ChatPane` XCUITest range scenario passed on macOS.
- `git diff --check` passed for all task-owned implementation,
  documentation, specification, and task files.

The desktop package-wide TypeScript command remains blocked by three
pre-existing errors: two attachment plugin-ID arguments in `ChatPane.tsx` and
the missing `Theme.shadow` property in `ActionResultInlineCard.tsx`. The final
typecheck reports no new range-navigation error.

No server contract, message-range planning, direct-index navigation, or
previous/next-user navigation was changed. Those remain in
`tasks/20260813-chat-transcript-navigation/030-add-message-and-turn-navigation.md`.