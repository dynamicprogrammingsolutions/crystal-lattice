# Subtask: Electron desktop prototype

Parent Task: tasks/20260305-cross-framework-desktop-prototype/000-main.md

## Description
Implement the prototype described in `tasks/20260305-cross-framework-desktop-prototype/blueprint.md` using **Electron**.

The goal is not product correctness but a faithful UI testbed to evaluate:
- Virtual list performance at 50–1000 messages
- Markdown rendering + **selectable** content
- Popover sizing (1–10 items) and edge placement behavior
- Modal dialog (Edit Connection) vs separate Settings window
- Tab preloading of last 3 tabs

## Requirements checklist
- [ ] Top tab strip with simple tabs (`tabId`, `title`) + a global “…” button (not overflow)
- [ ] Tab switching with last 3 visited tabs kept rendered but hidden
- [ ] Left rail: Connections + Sessions
- [ ] Messages list: mixed message types, collapsibles with max-height + inner scroll
- [ ] **Virtual scrolling** for messages (required)
- [ ] Markdown/plain toggle; **all message text selectable**
- [ ] Message popover randomized 1–10 items (deterministic), includes Edit/Delete/Copy
- [ ] Connections popover randomized 1–10 items (deterministic), includes Edit/Delete
- [ ] Edit Connection opens **modal** (font-aware fixed layout)
- [ ] Settings opens **separate window**; variable height; inner scroll if too many fields
- [ ] Narrow mode page switching: Messages/Sessions/Connections

## Notes / implementation hints (non-binding)
- Consider a single web UI stack (React/Vue/Svelte) shared with VSCode webview to reduce work.
- For virtualization: `react-window`/`react-virtualized` equivalents.
- For markdown: ensure selection works across rendered markdown and code blocks.
