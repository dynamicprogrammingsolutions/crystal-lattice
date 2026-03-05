# Blueprint (v0 draft): Cross‑Framework Desktop + IDE Prototype

## A. Core Principles
- **Mock-only**: no real backend; all data generated deterministically from a `seed` so every framework renders the same content.
- **Performance-focused interactions only**: keep logic minimal (no complex state persistence), but include the UI patterns that tend to reveal framework issues (virtual lists, markdown + selectable text, popovers with dynamic height, nested scrolling, modal dialogs, multiple windows).
- **Same UI in all targets**: Electron, JavaFX/Swing, Qt, Flutter; plus VSCode Webview and JetBrains (ToolWindow/dialog).

## B. Layout & Navigation

### B1. Main Shell
- **Top tab strip** with many open tabs (simple tab model: `tabId`, `title` only).
- A **tab-strip “…” button** on the right (global tab actions; **not** overflow indication).
  - Example menu items: `Close tab`, `Close others`, `Close all`.

### B2. Responsive Modes
- **Wide mode**: left rail is always visible with two sections stacked: **Connections** + **Sessions**.
- **Narrow mode** (VSCode/JetBrains-like width): left rail becomes separate pages:
  - Pages: `Messages`, `Sessions`, `Connections`.
  - Top-right buttons toggle between pages (preserve only trivial state like current page; no need for deep state persistence).

## C. Tabs & Preloading
- **Fast tab switching requirement**: last **3 visited tabs are preloaded** (rendered but hidden).
- **No tab state preservation requirement**: scroll positions, expanded collapsibles, composer text do not need to persist across tab switches for v0.

## D. Data Model & Stress Scaling

### D1. Adjustable chat size
- Provide a dropdown (in main UI or Settings window) to choose total message count: **50 / 150 / 300 / 600 / 1000**.
- Changing the size **regenerates** the mock session deterministically (same `seed` + size → same content).

### D2. Message pattern (baseline)
- Default dataset approximates the real pattern: blocks of `user` → many alternating `assistant thinking` + `tool output` → one `assistant final` with **long markdown**; repeated until reaching the selected message count.

## E. Message List (Must-Haves)

### E1. Virtual scrolling (mandatory)
- The message list **must use virtualization** where the framework supports it (or implement recycling manually).
- Include a toggle `Virtual scrolling: On/Off` if feasible, but virtualization support itself is required.

### E2. Mixed row types
Each message row includes:
- **Header line**: `[#index] RoleLabel` + right-side icon buttons + kebab **“…”**.
- **Body**:
  - `User`: short plain text
  - `Assistant thinking`: content in a **collapsible** with **max height** and internal scroll
  - `Tool call`: command + **long output** in a **collapsible** with **max height** and internal scroll
  - `Assistant final`: **long markdown**

### E3. Markdown/plain toggle + selectable text (mandatory)
- Add an icon button to switch **Markdown ↔ Plain text** rendering mode (global is simplest; per-message optional).
- **All message content must be selectable text**:
  - includes markdown-rendered text, code blocks, tool outputs, and collapsed/expanded content.
  - If a framework’s native rich text isn’t fully selectable, embedding a web renderer component is acceptable; the tradeoff is itself useful signal.

## F. Popovers (Core test area: sizing + placement)

### F1. Message actions popover
- Kebab “…” opens a **popover** anchored to the message header.
- The popover’s item count is **randomized 1–10 items** (but deterministic via `seed` + `messageId` for reproducibility across frameworks).
- Must include at least:
  - `Edit…` (opens modal)
  - `Delete`
  - `Copy message`
- Remaining items are filler actions (no-op) to stress sizing.

**Popover sizing/placement requirements**
- Height should adapt to content up to a max; if too tall → internal scroll.
- Placement should auto-flip (open above if near bottom) and remain usable near window edges.

### F2. Connections list popover
- Connections row kebab menu also uses randomized 1–10 items (deterministic), includes `Edit…` and `Delete`.

## G. Modals & Separate Windows

### G1. “Edit Connection” modal (fixed-size, font-aware)
- `Edit…` from Connections opens a **modal dialog** (Name/Host/Port + Cancel/Save).
- “Fixed size” means **fixed layout structure**, but it must **scale with system font size** (don’t hardcode pixel height); use layout-driven sizing and consistent padding.
- Prefer no scrolling here; if extreme font scaling breaks it, allow minimal scroll as a fallback.

### G2. “Session settings” separate window (variable + scrollable)
- One of the **top header icons** opens a separate **Settings window** (not just a modal) to test multi-window behavior.
- Settings content count is randomized **1–10 input sections** (deterministic via `seed` + `tabId/sessionId`).
- Window is **variable height**:
  - If content fits: no scroll.
  - If content overflows: inner scroll area.

## H. Left Rail Content (Keep simple, but realistic)

### H1. Connections
- ~5 items with status (`Open/Closed`), primary action button (`Open/Close`), and kebab menu.
- `Edit…` opens the fixed-size modal above.

### H2. Sessions
- Search box + `New` button + list of sessions.
- Clicking a session opens it in a tab (or focuses an existing tab with same id).

## I. “Enhancements” (Phase 2, only for frameworks that survive Phase 1)
- **Drag to reorder tabs**
- **Tab tear-off** (detach to new window)
- **Animated collapsibles** (measure jank)
- **Keyboard navigation** (arrow keys, Cmd/Ctrl+K quick switcher)
- **Incremental markdown rendering** (progressive render for very long content)

## J. Acceptance Checklist (per framework)
- Tabs render quickly; **last 3 tabs preloaded**.
- Message list supports **virtual scrolling** up to **1000** mixed messages.
- Collapsible blocks with **max height + internal scroll**.
- Markdown/plain toggle works; **all text selectable**.
- Popovers: **random 1–10 items**, height adapts + scroll if needed, edge-aware placement.
- Connections `Edit…` opens **font-aware fixed-layout modal**.
- Settings opens **separate window**; random 1–10 sections; scrollable when needed.
- Narrow mode has `Messages/Sessions/Connections` page switching.
