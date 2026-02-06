# Subtask: Message actions (copy/modify/markdown) + shared extraction

Add message-level actions to the desktop chat pane (copy, modify, toggle markdown), while preventing mobile↔desktop drift by extracting the obvious shared pieces.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/084-desktop-rich-assistant-rendering.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Mobile message actions definitions (to extract; read whole file): `mobile/crystal-lattice-control-rn/src/messageActions.ts:1`
- Mobile message actions handler (expected behaviors; read 792–834): `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:792`
- Mobile message actions bar wrapper (candidate to extract; read 1–80): `mobile/crystal-lattice-control-rn/src/components/MessageActionsBar.tsx:1`
- Shared pinnable actions UI primitive (read 1–200): `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx:1`
- Shared pinned-actions persistence hook (read 20–35): `packages/frontend-sdk-react/src/usePersistentPinnedActions.ts:20`
- Backend modify API (read 236–239): `packages/frontend-sdk/src/chat/chatController.ts:236`

## Requirements

- Desktop message rows show a message actions affordance.
- Implement baseline actions:
  - Copy message content
  - Modify message content (non-tool)
  - Toggle markdown rendering (assistant-only)
- Persist pinned message actions per connection and role.

## Deliverables

### 1) Extract message action definitions into a shared package

- Move `mobile/crystal-lattice-control-rn/src/messageActions.ts` → `packages/frontend-rn-components/src/messageActions.ts`.
- Update exports in `packages/frontend-rn-components/src/index.ts`.
- Update mobile + desktop imports to use `@crystal-lattice/frontend-rn-components`.

Explicit non-goal:

- Do not attempt to share the markdown renderer implementation (that stays desktop-local per `083`).

### 2) Extract a shared `MessageActionsBar`

- Create `packages/frontend-rn-components/src/actions/MessageActionsBar.tsx` as a thin wrapper over `ActionsMenuBar`.
- Update mobile `MessageBubble.tsx` to use the shared wrapper.
- Desktop chat should use the same shared wrapper.

### 3) Persist pinned message actions (avoid bespoke JSON blobs)

Mobile currently persists a single JSON object for pinned-by-role. To avoid duplicating that storage scheme:

- Store pinned keys per-connection and per-role in separate string-array keys, using the existing shared hook:
  - `usePersistentPinnedActions({ store, key: clc_pinned_message_actions_v1:${connectionId}:${role}, initialPinned })`
- Migrate mobile:
  - Read the legacy blob once (if present), write per-role keys, then stop writing the blob.
- Desktop uses the same per-role key format.

### 4) Implement desktop message action handlers

- Copy: platform-specific clipboard implementation (desktop may need a different library than mobile).
- Modify:
  - Enter edit mode for a message index.
  - Call `chatController.modifyMessage(index, nextContent)`.
- Toggle markdown:
  - Either per-message override (like mobile’s `messageViewModeByIndex`) or a simpler global toggle; if global, keep the action but have it toggle the global setting.

## Verification

- Copy action works for each role and does not crash on macOS.
- Modify action updates a message and the transcript re-renders.
- Toggle markdown affects assistant message rendering.
- Pinned actions persist across app restarts (at least for the active connection).
