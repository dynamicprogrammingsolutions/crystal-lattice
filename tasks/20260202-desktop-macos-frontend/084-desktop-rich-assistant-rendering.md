# Subtask: Rich assistant rendering (reasoning + tool calls)

Upgrade the desktop chat transcript from the minimal baseline in `080` to a richer message presentation, focused on assistant/tool-related metadata:

- Collapsible reasoning
- Collapsible tool call list + previews
- Better per-role message styling (assistant/user/system/tool)

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/083-desktop-markdown-renderer.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Render toggles that should control visibility (from `081`): `tasks/20260202-desktop-macos-frontend/081-desktop-chat-header-and-session-actions.md`
- Mobile message rendering reference (do not copy wholesale):
  - Reasoning + tool calls UI (read 340–568): `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:340`
  - Tool call preview formatting (read 520–568): `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:520`
- Streaming row shape (reasoning/content deltas; read 1–120): `packages/frontend-sdk/src/chat/streamingStateReducer.ts:1`

## Requirements

- Assistant messages should optionally show:
  - reasoning (collapsed by default)
  - tool calls list (collapsed by default)
- Tool-role messages should be readable and clearly delineated.
- Must not break offline mode: cached messages should render identically.

## Deliverables

### 1) Desktop message row component(s)

- Add `desktop/crystal-lattice-control-desktop-rn/src/chat/MessageRow.tsx` (or similar) to centralize transcript rendering.
- Render by role:
  - user
  - assistant
  - system
  - tool

### 2) Assistant metadata rendering

- Read metadata fields:
  - `message.metadata.reasoning` (string)
  - `message.metadata.tool_calls` (array)
  - `message.metadata.tool_call_previews` (array; optional)

- Implement expand/collapse UI for reasoning/tool calls.
- Use the render options toggles from `081` to hide/show these sections.

### 3) Streaming row presentation

- When `ChatControllerState.streamingRow` is present, render a “streaming” assistant row.
- Respect the same reasoning/tool-call toggles if possible.

## Duplication guidance

- It’s OK to reimplement desktop visuals, but avoid copy/paste of mobile `MessageBubble.tsx`.
- If you find you need shared “collapsible section” logic, extract a small reusable component into `packages/frontend-rn-components/` (optional).

## Verification

- Trigger an assistant response with reasoning + tool calls; confirm collapse/expand works.
- Confirm tool call previews are readable and don’t overflow the pane.
