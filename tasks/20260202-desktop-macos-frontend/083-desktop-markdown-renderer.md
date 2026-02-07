# Subtask: Desktop markdown renderer (desktop-only)

Add a markdown renderer for chat messages in the desktop app.

Important constraint: do **not** force sharing of the markdown renderer between mobile and desktop. This subtask explicitly allows a desktop-only implementation.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/081-desktop-chat-header-and-session-actions.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Desktop transcript rendering baseline (assistant/content rendering; read 620–760):
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx:620`
- Desktop theme tokens used for code blocks (read whole file):
  - `packages/frontend-rn-components/src/theme.ts:1`
- Desktop package dependencies (may need updates; read dependencies section):
  - `desktop/crystal-lattice-control-desktop-rn/package.json:1`

Mobile references (do not copy wholesale; use as behavior reference):

- Mobile markdown implementation (fenced code rules + scroll behavior; read 1–120):
  - `mobile/crystal-lattice-control-rn/src/components/MarkdownMessageContent.tsx:1`
- Mobile per-message render mode toggle (read 802–818 and 1074–1082):
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:802`
- Mobile message actions definition showing assistant-only toggle (read 1–60):
  - `mobile/crystal-lattice-control-rn/src/messageActions.ts:1`

Upcoming integration dependency:

- Desktop message actions + markdown toggle is planned in `085` (read Requirements/Deliverables):
  - `tasks/20260202-desktop-macos-frontend/085-desktop-message-actions-and-sharing.md:1`

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

## Detailed implementation plan (staged, with manual checkpoints)

Important: this subtask builds the *renderer* and integrates it in a testable way, but the per-message markdown toggle UI/state should be wired through message actions in `tasks/20260202-desktop-macos-frontend/085-desktop-message-actions-and-sharing.md` (matching mobile’s behavior). Until `085` lands, the desktop app can default assistant messages to markdown.

### Stage 0: Prep wiring (no new deps; safe + testable)

Goal: add a desktop-local component + wire it in so we can iterate safely.

- Add `desktop/crystal-lattice-control-desktop-rn/src/chat/MarkdownMessageContent.tsx`.
- Initial implementation should be a wrapper that renders raw text only (no markdown libs yet).
- API should anticipate `085`:
  - `text: string`
  - `renderMode?: 'markdown' | 'raw'` (default `'raw'`)
  - (optional) `variant?: 'assistant' | 'user' | 'system' | 'tool'` for styling parity later
- Update `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` message rendering so assistant messages render via `MarkdownMessageContent` (still raw at this stage).

Manual checkpoint:

- Run the desktop app and open a session; transcript renders identically to before.

### Stage 1: Basic markdown rendering (install + simple integration)

Goal: verify a markdown library is compatible with RN macOS, with minimal complexity.

- Install a markdown renderer dependency (first choice mirrors mobile):
  - `react-native-markdown-display`
- Update `desktop/crystal-lattice-control-desktop-rn/src/chat/MarkdownMessageContent.tsx`:
  - When `renderMode === 'markdown'`, render via the markdown component.
  - Keep styles minimal for this stage.
  - Add a hard fallback to raw text if markdown rendering fails (graceful degradation).
- Integrate simply in `ChatPane`:
  - Default assistant messages to `renderMode="markdown"` for now.
  - Leave other roles as raw.

Manual checkpoint:

- Render an assistant message with headings/lists/inline code; confirm it renders and does not crash on macOS.

Fallback/decision point:

- If `react-native-markdown-display` has macOS issues (build/runtime), switch to a more suitable markdown package for macOS and repeat this stage until we have a working baseline.

### Stage 2: Fenced code blocks (separate stage)

Goal: implement fenced code blocks with horizontal scrolling (and optional syntax highlighting).

- Add syntax highlighting dependency (first choice mirrors mobile):
  - `react-native-syntax-highlighter`
  - If required by the style import chain, add `react-syntax-highlighter` explicitly.
- Update `desktop/crystal-lattice-control-desktop-rn/src/chat/MarkdownMessageContent.tsx`:
  - Implement custom render rules for `fence` and `code_block`.
  - Wrap code blocks in a horizontal `ScrollView` so long lines don’t break layout.
  - Consider a max height with vertical scrolling for very tall blocks.
  - Use theme tokens where possible (e.g. `theme.codeBlockBg`, `theme.inlineCodeBg`).
  - Preserve graceful fallback to raw text if code rendering fails.

Manual checkpoint:

- Render a fenced code block with long lines; confirm horizontal scroll works and layout stays stable.

Fallback/decision point:

- If the syntax highlighter or code-block rule approach is problematic on macOS, replace the highlighter and/or code renderer strategy with a macOS-compatible alternative (even if that means no highlighting initially), while keeping horizontal scrolling.

### Stage 3 (follow-up via 085): Per-message toggle (assistant-only)

Goal: match mobile behavior: per-message view mode with an assistant-only toggle.

- Implemented in `tasks/20260202-desktop-macos-frontend/085-desktop-message-actions-and-sharing.md`.
- Store `messageViewModeByIndex: Record<number, 'markdown' | 'raw'>` in the desktop chat pane/message row host.
- Toggle action:
  - only offered for assistant role
  - flips mode for that index
- Pass `renderMode` into `MarkdownMessageContent` per message.

## Standard markdown rendering options (reference)

If the first-choice libraries are not compatible with RN macOS, pick an alternative in the same stage and keep the same checkpoints.

### Option set A: Native-component markdown renderers (Markdown → RN components)

- `react-native-markdown-display` (first choice; mirrors mobile)
- `react-native-markdown-renderer` (older predecessor; sometimes simpler/less maintained)
- `react-native-marked` (markdown rendered as a list; can be helpful for large docs)
- `react-native-remark` (remark/unified based; good for plugins/GFM-style extensions)

### Option set B: Markdown → HTML → RN rendering

- Parse markdown to HTML with `markdown-it` (or `marked`), then render with `react-native-render-html`.
- This is often the most flexible “escape hatch” if markdown-specific RN libraries don’t behave well on macOS.

### Option set C: WebView-based markdown/HTML rendering

- Markdown → HTML, then display via a `WebView`.
- Usually easiest to get GitHub-like visuals, but it’s heavier and can complicate selection/copy, theming, and scroll behavior.

### Option set D: Custom AST renderer

- Use a parser (`markdown-it` / remark) and render the AST to desktop-owned RN components.
- Most control (especially code blocks), but higher implementation cost.

### Code blocks + highlighting (add-on strategy)

- Common approach: implement `fence`/`code_block` rendering rules and wrap blocks in horizontal `ScrollView`.
- Syntax highlighting can be layered in with `react-native-syntax-highlighter`, but if that’s problematic on macOS, fall back to plain monospace text with horizontal scrolling.
