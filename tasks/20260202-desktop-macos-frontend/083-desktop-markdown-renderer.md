# Subtask: Desktop markdown renderer (desktop-only)

Add a markdown renderer for chat messages in the desktop app.

Important constraint: do **not** force sharing of the markdown renderer between mobile and desktop. This subtask explicitly allows a desktop-only implementation.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/081-desktop-chat-header-and-session-actions.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Mobile markdown implementation (reference only; read 1–120): `mobile/crystal-lattice-control-rn/src/components/MarkdownMessageContent.tsx:1`
- Mobile per-message render mode toggle (read 802–813): `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:802`
- Desktop package dependencies (may need updates; read dependencies section): `desktop/crystal-lattice-control-desktop-rn/package.json:1`

## Requirements

- Controlled by the header render option toggle added in `081` (e.g. `renderMarkdown`).
- Must render at least:
  - basic markdown text
  - fenced code blocks with horizontal scrolling
- Must degrade gracefully to raw text if markdown fails.

## Deliverables

### 1) Add a desktop-local markdown component

- Add `desktop/crystal-lattice-control-desktop-rn/src/chat/MarkdownMessageContent.tsx`.

Implementation options:

- Option A (closest to mobile): use `react-native-markdown-display` + `react-native-syntax-highlighter`.
  - Requires adding these deps to `desktop/crystal-lattice-control-desktop-rn/package.json`.
- Option B: a simpler markdown renderer (no syntax highlighting) if macOS support is problematic.

### 2) Wire into the desktop message renderer

- Update the message rendering in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` (or the message-row component introduced in `084`) to:
  - render assistant content via markdown when enabled
  - otherwise render raw text

## Explicit non-goals

- Do not move `mobile/crystal-lattice-control-rn/src/components/MarkdownMessageContent.tsx` into shared packages.
- Do not attempt to match mobile styling exactly.

## Verification

- Render a message containing:
  - headings
  - lists
  - fenced code blocks
- Verify code blocks are scrollable and don’t break layout.
