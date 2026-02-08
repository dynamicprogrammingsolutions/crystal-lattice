# Subtask: Rich message rendering (desktop) + message actions (copy/modify/markdown)

Deliver a desktop-friendly chat transcript by first copying the working mobile message UI directly into the desktop app, then iterating visuals + adding message actions/editing.

Important philosophy for this milestone:

- Prefer shipping a correct UI quickly (copy mobile), then refine.
- Avoid premature extraction into shared packages until we have verified what stays the same across mobile + desktop.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/083-desktop-markdown-renderer.md`

## Status

- [x] Completed (Stages 1–2)

## Context to read first (files + line numbers)

- Mobile message rendering reference (copy-first, then diverge in later stages):
  - Reasoning + tool calls UI (read 340–568): `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:340`
  - Tool call preview formatting (read 520–568): `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:520`
- Streaming row shape (reasoning/content deltas; read 1–120): `packages/frontend-sdk/src/chat/streamingStateReducer.ts:1`

## Requirements

- Assistant messages should support:
  - reasoning (collapsed by default)
  - tool calls list (collapsed by default, with previews when available)
- Tool-role messages should be readable and clearly delineated (collapsed preview + expandable body).
- Add desktop message actions and minimal editing support (pulled forward from a previously-separate subtask):
  - Copy message content
  - Modify message content (non-tool)
  - Toggle markdown rendering (assistant-only)
- Must not break offline mode: cached messages should render identically.

## Deliverables

### Stage 1: Copy mobile message UI into desktop (ship behavior first)

- Add a desktop-local message bubble component by copying the relevant mobile components:
  - Source: `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:1`
  - Destination (suggested): `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx`
- Wire the desktop transcript to render messages using the copied component (instead of the current minimal inline renderer in `ChatPane`).
- Ensure assistant metadata rendering works on desktop:
  - `message.metadata.reasoning` (string)
  - `message.metadata.tool_calls` (array)
  - `message.metadata.tool_call_previews` (array; optional)
- Wire the streaming row through the same component (build a synthetic `ApiMessage` from `chatState.streamingRow`).

Manual checkpoint:

- Trigger an assistant response with reasoning + tool calls; confirm collapse/expand works.
- Trigger a tool message; confirm tool output is readable and doesn’t overflow.
- Confirm offline cached messages render identically.

### Stage 2: Desktop polish + message actions + edit mode

- Iterate visuals to be desktop-friendly (spacing/typography/max heights), while keeping Stage 1 behavior.
- Add desktop message actions UI + handlers:
  - Copy
  - Modify (enter edit mode; call `chatController.modifyMessage(index, nextContent)`)
  - Toggle markdown (assistant-only; per-message preferred)

Manual checkpoint:

- Copy works and does not crash.
- Modify updates a message and transcript re-renders.
- Toggle markdown affects assistant rendering.

### Stage 3 (optional): Extract stable duplicates into `@crystal-lattice/frontend-rn-components`

Only after Stage 1+2 are stable on desktop.

- Candidate extractions (not commitments):
  - Expand/collapse primitives (`ExpandableSection`)
  - Tool calls disclosure logic (`ToolCallsDisclosure`) with render-prop customization
  - Tool output disclosure logic (`ToolOutputDisclosure`) with render-prop customization
  - Role routing wrapper (`MessageByRole`) that calls app-provided renderers
  - Message actions definitions / `MessageActionsBar` wrapper (if unchanged across apps)

Specific extraction choices and APIs are decided later, based on what stays identical across mobile + desktop.

## Duplication guidance

- Stage 1 explicitly allows direct copy from mobile into desktop to ship a working UI.
- After desktop iteration, extract only the pieces that remain stable across both apps.

## Verification

- Trigger an assistant response with reasoning + tool calls; confirm collapse/expand works.
- Confirm tool call previews are readable and don’t overflow the pane.
- Confirm message actions (copy/modify/markdown) work on desktop.

---

## Completion Notes (added 2026-02-08)

Stage 1 is implemented.

- Added a desktop-local message bubble component with mobile-equivalent assistant/tool disclosure UI:
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx`
- Wired `ChatPane` to use `DesktopMessageBubble` for both persisted messages and the streaming row:
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
- Desktop bubble supports:
  - Assistant markdown rendering via `MarkdownMessageContent`
  - Collapsible reasoning (metadata `reasoning`)
  - Collapsible tool calls (metadata `tool_calls` + `tool_call_previews`)
  - Collapsible tool message output (tool role)

Stage 2 (actions/edit mode + polish) remains.

### Stage 2 completion notes (added 2026-02-08)

- Added desktop message actions + edit mode (copy/modify/toggle-markdown) with mobile-matching wiring:
  - Action definitions: `desktop/crystal-lattice-control-desktop-rn/src/chat/messageActions.ts`
  - Actions menu wrapper: `desktop/crystal-lattice-control-desktop-rn/src/chat/MessageActionsBar.tsx`
  - Wiring + state (edit mode, per-message markdown): `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
  - Bubble rendering + edit UI: `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx`
- Desktop keeps actions in the header row (desktop-only layout choice) while keeping the same action semantics as mobile.
- Raw (non-markdown) assistant content uses the same selectable read-only `TextInput` approach as mobile.
- Desktop-only disclosure polish:
  - Assistant reasoning + tool calls show a persistent single-line preview row with chevron; the whole row is clickable.
  - Reasoning preview row is placed near the top (below expanded reasoning, above content).
  - Tool calls preview row is placed near the bottom (below content, above expanded tool calls).
  - Tool-role result disclosure row is also full-row clickable.
- Session UI schema footer elements are loaded (when online) and passed through to bubbles for rendering.
- Pinned message actions persistence now matches the mobile structure (JSON “by role”), with a migration path from the earlier desktop per-role keys.
- `MarkdownMessageContent` is markdown-only; raw-vs-markdown switching happens in `AssistantMessageBubble` (matching mobile structure).

Stage 3 (optional extraction) remains.
