# Subtask: Flutter (Dart) desktop prototype

Parent Task: tasks/20260305-cross-framework-desktop-prototype/000-main.md

## Description
Implement the prototype described in `tasks/20260305-cross-framework-desktop-prototype/blueprint.md` using **Flutter (Dart) for desktop**.

Primary evaluation areas:
- Virtual list performance (50–1000 messages) with heterogeneous rows
- Markdown rendering with **selectable** content
- Popover sizing/placement (1–10 items) and scroll when overflowing
- Windowing: modal dialog (Edit Connection) and separate settings window

## Requirements checklist
- [ ] Tabs + global “…” tab actions menu
- [ ] Last 3 visited tabs preloaded (rendered but hidden)
- [ ] Left rail: Connections + Sessions
- [ ] Message list: mixed types + collapsibles with max-height + internal scroll
- [ ] **Virtual scrolling** for messages (required)
- [ ] Markdown/plain toggle; **all text selectable**
- [ ] Popovers/menus randomized 1–10 items (deterministic)
- [ ] Edit Connection is a **modal** with font-aware fixed layout
- [ ] Settings opens as a **separate window**; variable height; scroll on overflow
- [ ] Narrow mode page switching: Messages/Sessions/Connections

## Notes / implementation hints (non-binding)
- Flutter desktop multi-window may require plugins; if true multi-window is too heavy for v0, document the limitation explicitly (but try to implement).
- For selection in markdown: verify that the chosen markdown widget preserves selection across spans/code blocks.
