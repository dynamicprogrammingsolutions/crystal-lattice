# Subtask: JavaFX/Swing desktop prototype

Parent Task: tasks/20260305-cross-framework-desktop-prototype/000-main.md

## Description
Implement the prototype described in `tasks/20260305-cross-framework-desktop-prototype/blueprint.md` using **Java (JavaFX and/or Swing)**.

This subtask exists specifically to test:
- Native-feel controls (menus/popovers, dialogs)
- Virtualized lists (`ListView` in JavaFX, custom cell renderers)
- Rich text/markdown rendering with **selectable** content
- Multi-window behavior (Settings as separate window)

## Decision point
Pick one of:
1) JavaFX-only implementation
2) Swing-only implementation
3) Hybrid (Swing shell + JavaFX embedded) if markdown selection/rich rendering is easier

## Requirements checklist
- [ ] Tabs + global “…” tab actions menu
- [ ] Last 3 visited tabs preloaded (rendered/kept alive but hidden)
- [ ] Left rail: Connections + Sessions
- [ ] Message list: mixed types + collapsibles with max-height + internal scroll
- [ ] **Virtual scrolling** for messages (required)
- [ ] Markdown/plain toggle; **all text selectable**
- [ ] Popovers/menus randomized 1–10 items (deterministic)
- [ ] Edit Connection is a **modal dialog** with font-aware fixed layout
- [ ] Settings is a **separate window** with 1–10 randomized sections; scrollable when overflowing
- [ ] Narrow mode page switching: Messages/Sessions/Connections

## Notes / implementation hints (non-binding)
- JavaFX `ListView` is virtualized by default; ensure variable-height rows are handled acceptably.
- For markdown: evaluate options (e.g., render to `WebView` vs native text flow) with selection as a key constraint.
