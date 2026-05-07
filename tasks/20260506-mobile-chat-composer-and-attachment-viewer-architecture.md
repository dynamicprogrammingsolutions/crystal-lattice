# Mobile Chat Composer And Attachment Viewer Architecture
Investigate and implement a performance-focused refactor of the React Native chat screen so typing does not re-run the full chat screen unnecessarily, and so attachment preview rows stay lightweight by moving modal/download/share logic outside message history.

## Requirements checklist
- [x] Extract the chat composer into a separate component so typing state is no longer owned by `SessionChatScreen`
- [x] Extract the transcript/list into a separate component so transcript rendering is isolated from composer updates
- [x] Refactor message attachment rendering so message rows only render lightweight preview UI
- [x] Move attachment modal, full-resolution loading, download, share, and save flows into an external attachment viewer host outside the message history
- [x] Preserve current attachment preview/open behavior and avoid reintroducing the hook-order crash fixed in `61b54bc8`
- [x] Add or update tests around the refactor, especially for attachment open flow and any crash-prone hook transitions

## Background

This task comes from investigating a mobile app crash that was reported as "sometimes crashes during typing a message." Historically, a similar issue happened when typing caused rerendering on each keystroke.

Current investigation result:

- `SessionChatScreen` still rerenders on every keystroke because `composeText` lives in local state and is updated by the composer `TextInput`.
- The old "every keystroke rerenders every message bubble" issue does not appear to be the current code path, because the transcript uses `DependencyFlatList` with per-row dependency caching.
- Even so, the parent screen rerender still causes transcript-level recalculation work on every keystroke, and message attachment rendering has become much heavier in recent commits.

## What Was Inspected

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/components/DependencyFlatList.tsx`
- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- `mobile/crystal-lattice-control-rn/src/components/AttachmentThumbnailStrip.tsx`
- `mobile/crystal-lattice-control-rn/src/components/MarkdownMessageContent.tsx`
- `mobile/crystal-lattice-control-rn/__tests__/MessageBubble.test.tsx`
- Recent git history for the chat screen and its subcomponents

## Key Findings

### 1. Typing still rerenders the top-level chat screen

`composeText` is owned by `SessionChatScreen`:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:272`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:3140`

Relevant lines:

```tsx
const [composeText, setComposeText] = useState(initialComposeText ?? '');
```

```tsx
<TextInput
  value={composeText}
  onChangeText={(text) => {
    setComposeText(text);
  }}
/>
```

So typing definitely re-executes the parent screen component.

### 2. The transcript has caching that likely prevents full bubble rerenders

The transcript rows are memoized only from `messages`:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:2636`

The list uses `DependencyFlatList`:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:2882`
- `mobile/crystal-lattice-control-rn/src/components/DependencyFlatList.tsx:66`

`DependencyFlatList` reuses cached row elements when:

- the row item identity is unchanged
- the per-row dependency array is shallow-equal

Key logic:

- `mobile/crystal-lattice-control-rn/src/components/DependencyFlatList.tsx:112`
- `mobile/crystal-lattice-control-rn/src/components/DependencyFlatList.tsx:118`

Important detail: `composeText` is not included in the message-row dependency arrays:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:2906`

That means typing alone should not invalidate existing message rows.

### 3. There is still per-keystroke transcript work

Even with row caching, `DependencyFlatList` still maps through all rows and recomputes dependencies on each parent rerender:

- `mobile/crystal-lattice-control-rn/src/components/DependencyFlatList.tsx:112`

So the current state is:

- better than full bubble rerendering
- but still not ideal for very large chats or heavier row subtrees

### 4. `MessageBubble` attachment rendering got significantly heavier

The attachment/rendering history that matters:

#### `db64da90`

Added multipart attachments to message bubbles:

- inline image rendering
- file/pdf rows
- copy/open behavior

#### `5bef5b64`

Moved message attachments to `AttachmentThumbnailStrip`:

- `mobile/crystal-lattice-control-rn/src/components/AttachmentThumbnailStrip.tsx`

#### `46503196`

Greatly expanded `MessageAttachments` in `MessageBubble`:

- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:115`

This commit added:

- local attachment state
- in-flight promise caching
- file system writes via `react-native-fs`
- full-resolution download logic
- `ImageModal`
- save-to-file flow
- save-to-photos flow
- share flow
- zoom-triggered full-resolution loading

This is likely a major contributor to message-row heaviness, even if it is not the original typing crash.

### 5. The follow-up crash fix `61b54bc8` looks legitimate, not suspicious

That fix moved the `parts.length === 0` early return in `MessageAttachments` to after the hooks:

- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:284`

Why it mattered:

- before the fix, `MessageAttachments` could sometimes return before hook declarations and sometimes not
- if the same component instance transitioned between "no attachments" and "has attachments", React hook order could break

The added regression test verifies exactly this:

- `mobile/crystal-lattice-control-rn/__tests__/MessageBubble.test.tsx:117`

This fix likely prevented a real crash. It should not be reverted conceptually.

However, the current structure means every `MessageAttachments` render pays hook setup cost even for messages with no attachments. That is another reason to simplify the in-row attachment component.

## Recommended Refactor Direction

The agreed recommendation from investigation is:

1. Split the composer out of `SessionChatScreen`
2. Split the transcript/list out of `SessionChatScreen`
3. Keep message attachment rendering lightweight inside the history
4. Move attachment modal and download/share/full-resolution logic outside the history

### Recommended component architecture

#### `ChatComposer`

Move composer-local draft state out of `SessionChatScreen`, including:

- `composeText`
- possibly draft attachment UI state that is truly composer-local

Goal:

- typing a message should rerender the composer, not the full chat screen

#### `ChatTranscript`

Move transcript/list rendering into a separate component that receives stable props and owns:

- `DependencyFlatList`
- transcript row derivation
- row dependency logic
- scroll-anchor integration

Goal:

- isolate transcript rendering from composer updates

#### `MessageAttachmentsPreview`

Inside `MessageBubble`, attachment handling should become preview-only:

- derive lightweight preview data
- render `AttachmentThumbnailStrip`
- emit `onOpenAttachment(...)`

This component should not own:

- modal visibility
- full-resolution image loading
- file download/share/save actions
- native module orchestration

#### `AttachmentViewerHost`

Add a viewer/controller outside message history, likely in `SessionChatScreen` as a sibling of the transcript and composer, or in a dedicated controller component.

This external viewer should own:

- selected attachment state
- modal visibility
- full-resolution cache
- original download logic
- save/share actions
- native integrations (`RNFS`, `Share`, `CameraRoll`, `saveDocuments`)

This should be the only place where the heavy modal/download logic lives.

## Why This Architecture Is Preferred

- Message rows stay mostly presentational and cheap.
- The transcript no longer contains per-row native file/viewer logic.
- Typing in the composer should no longer re-execute transcript logic.
- Attachment viewer state survives independently from row lifecycle.
- This avoids reintroducing hook-order problems tied to whether a given message currently has attachments.
- Memoization becomes much simpler and more reliable after the split.

## Important Design Constraints

### Attachment open event should pass stable data

The attachment open callback should not rely only on transient row index lookup. Pass a stable attachment payload or snapshot so the viewer still works if the transcript refreshes while the modal is open.

### Full-resolution cache belongs outside the message row

If the same attachment is opened multiple times, caching should be owned by the external viewer host instead of an individual bubble instance.

### Session changes should clear viewer state

If the user switches sessions while a viewer is open, the viewer state should reset.

### Preserve current user-visible behavior

The refactor should preserve:

- attachment thumbnail preview
- image opening
- PDF open behavior where applicable
- save/share flows

Any deliberate UX change should be called out explicitly.

## Recent Commits Worth Reviewing

- `2e594aaa` Introduced `DependencyFlatList`
- `db64da90` Added message multipart attachment rendering
- `5bef5b64` Introduced `AttachmentThumbnailStrip` and attachment preview strip rendering
- `46503196` Added heavy attachment preview/download/share/full-resolution logic to `MessageBubble`
- `8f208443` Reshaped `MessageBubble` rendering and disclosures
- `61b54bc8` Fixed hook-order crash risk in attachment rendering

## Suggested Implementation Order

1. Extract `ChatComposer` first and move draft typing state there.
2. Extract `ChatTranscript` next and keep transcript props as stable as possible.
3. Refactor `MessageBubble` attachment handling into lightweight preview-only UI.
4. Introduce external `AttachmentViewerHost`.
5. Reconnect preview tile taps to the external viewer.
6. Add regression tests for:
   - typing not requiring transcript rerender coupling at the architecture level
   - attachment open flow
   - attachment/no-attachment transitions
   - session switch clearing viewer state if applicable

## Execution plan

Added during completion after user approval.

1. Create shared attachment view-model helpers, likely in `mobile/crystal-lattice-control-rn/src/messageAttachments.ts`.
   - Export helpers such as `selectMultipartAttachments(message, messageIndex?)`, `attachmentFilename`, `attachmentMimeType`, and `resolveAttachmentDownloadPluginId`.
   - Define a stable `MessageAttachmentSnapshot` payload for preview taps so the viewer does not depend on row index lookups after transcript refreshes.

2. Move heavy attachment viewing logic into `AttachmentViewerHost`.
   - Add `mobile/crystal-lattice-control-rn/src/components/AttachmentViewerHost.tsx`.
   - Own selected attachment state, modal visibility, full-resolution URI cache, in-flight local-file promise cache, original downloads, save-to-file, save-to-photos, and share flows.
   - Move native integrations (`RNFS`, `downloadSessionAttachment`, `Share`, `saveDocuments`, `CameraRoll`) out of `MessageBubble`.
   - Use the existing `react-native-image-modal` imperative `open()` / `close()` API to preserve zoom/modal behavior from a single host outside the list.
   - Preserve current PDF URL opening and unavailable-preview alerts.

3. Replace in-row attachment logic with preview-only UI.
   - Replace `MessageAttachments` in `MessageBubble` with a lightweight `MessageAttachmentsPreview`.
   - Render `AttachmentThumbnailStrip` and call `onOpenAttachment(snapshot)` on tile press.
   - Remove `backend` / `sessionId` attachment responsibilities from `MessageBubble`; keep it mostly presentational.
   - Preserve the no-attachment / has-attachment transition behavior covered by the hook-order regression test from `61b54bc8`.

4. Extract `ChatTranscript`.
   - Move `DependencyFlatList`, transcript row creation, row dependency logic, status row, streaming row, inline action header, scroll restore callbacks, and `MessageBubble` rendering into a memoized transcript component.
   - Keep props stable and explicit: messages, streaming row, status parts, footer/action defs, editing state, pinned actions, message callbacks, scroll callbacks, and `onOpenAttachment`.
   - Continue using the current inverted list and scroll-anchor behavior.

5. Extract `ChatComposer` with local draft ownership.
   - Move `composeText`, `attachmentsAbove`, `attachmentsBelow`, attachment metadata/manage modals, image picker/URL modal state, and composer draft manipulation into the composer component.
   - Expose draft snapshots upward only for commands such as Append, Append-as, and Send.
   - Provide an imperative or callback-based draft persistence API so `SessionChatScreen` can still save draft text on blur/inactive/back without owning every keystroke.
   - Clear the composer draft only after the parent confirms append/send success.

6. Keep `SessionChatScreen` as coordinator.
   - Render header/status/error/recovery UI, `ChatTranscript`, `ChatComposer`, and `AttachmentViewerHost` as siblings.
   - Keep session/controller state in the screen.
   - Clear attachment viewer state when `sessionId` changes.

7. Add/update tests.
   - Update `MessageBubble.test.tsx` so message row tests no longer need to mock `RNFS`, `Share`, `CameraRoll`, document picker, or `ImageModal`.
   - Keep the multipart hook-order regression test.
   - Add tests that preview tiles call `onOpenAttachment` with a stable snapshot.
   - Add focused `AttachmentViewerHost` tests for image open and save/share/download actions with native modules mocked there.
   - Add `ChatComposer` tests showing typing stays local and parent callbacks fire only for blur/persist or explicit Append/Send.
   - Add a lightweight transcript isolation test if practical, proving composer text changes do not rerender a memoized transcript sibling.

8. Verify.
   - Run targeted Jest tests for changed components.
   - Run `npm run tsc` from `mobile/crystal-lattice-control-rn`.
   - Run broader `npm test` if the targeted suite passes and time permits.

Recommended execution approach: staged checkpoints in the order above. Attachment extraction first reduces row weight and test complexity, transcript extraction then preserves behavior, and composer extraction last changes the draft ownership model with a clearer safety net.

## Open Questions For The Implementing Agent

- Which composer-related state should remain at the screen level versus move into `ChatComposer`?
- Should the external attachment viewer live directly in `SessionChatScreen` or in a dedicated hook/component pair such as `useAttachmentViewer` + `AttachmentViewerHost`?
- Are there existing tests or profiling hooks that should be expanded to verify transcript isolation during typing?

## Notes

- No code changes were made as part of the investigation that produced this task.
- The main conclusion to preserve is: this does not currently look like a simple regression back to "typing rerenders every message bubble", but there is still unnecessary top-level rerendering and the in-row attachment system has become heavier than it should be.

## Completion Notes

Added during completion.

- Added shared message attachment snapshot/helpers in `mobile/crystal-lattice-control-rn/src/messageAttachments.ts`.
- Added `mobile/crystal-lattice-control-rn/src/components/AttachmentViewerHost.tsx` so image modal, full-resolution loading, local file caching, save-to-file, save-to-photos, share, and PDF/unavailable handling live outside message rows.
- Refactored `MessageBubble` so attachment rows are preview-only and emit stable `MessageAttachmentSnapshot` payloads through `onOpenAttachment`.
- Extracted `ChatTranscript` inside `SessionChatScreen.tsx`; it owns the `DependencyFlatList`, transcript row construction, row dependency logic, status/stream rows, and message bubble rendering.
- Extracted `ChatComposer` inside `SessionChatScreen.tsx`; it owns `composeText` state and reports draft text to the screen through a ref/persistence callback instead of making the screen rerender on every keystroke.
- Wired `SessionChatScreen` as coordinator for transcript, composer, and `AttachmentViewerHost`, including clearing selected attachment state on session changes.
- Updated `MessageBubble.test.tsx` to keep the multipart hook-order regression and add a stable attachment snapshot open-flow test.
- Added `AttachmentViewerHost.test.tsx` covering image footer/share flow with native modules mocked at the viewer-host boundary.
- Follow-up viewer robustness update:
  - Replaced `react-native-image-modal` with a controlled React Native `Modal` plus `@likashefqet/react-native-image-zoom`.
  - Added `react-native-gesture-handler` / `react-native-reanimated` wiring in `App.tsx`, `index.js`, and `babel.config.js`.
  - Removed the `react-native-image-modal` dependency.
  - Full-size downloads now update the displayed zoom image without imperatively reopening a thumbnail modal.
  - Full-size cache keys now prefer session asset identity and fall back to message/part identity.
- Verification:
  - Passed: `npm test -- --runTestsByPath __tests__/MessageBubble.test.tsx __tests__/AttachmentViewerHost.test.tsx --runInBand`
  - Passed after viewer replacement: `npm test -- --runTestsByPath __tests__/AttachmentViewerHost.test.tsx --runInBand`
  - Attempted: `npm run tsc -- --pretty false`; it still fails on pre-existing unrelated type errors in `node_modules/@crystal-lattice/frontend-sdk/src/backend/restBackend.ts`, `src/components/ActionResultInlineCard.tsx`, and missing style keys in `src/SessionChatScreen.tsx`.