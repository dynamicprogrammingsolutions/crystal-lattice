# Subtask: Qt desktop prototype

Parent Task: tasks/20260305-cross-framework-desktop-prototype/000-main.md

## Description
Implement the prototype described in `tasks/20260305-cross-framework-desktop-prototype/blueprint.md` using **Qt** (Widgets or QML; choose one).

Primary evaluation areas:
- Popovers/menus with dynamic height (1–10 items) + edge-aware placement
- Virtualized scrolling for large, heterogeneous message rows
- Markdown rendering with **selectable** content
- Modal dialog vs separate settings window

## Decision point
Pick one of:
1) Qt Widgets
2) Qt Quick/QML

## Requirements checklist
- [ ] Tabs + global “…” tab actions menu
- [ ] Last 3 visited tabs preloaded
- [ ] Left rail: Connections + Sessions
- [ ] Message list: mixed types + collapsibles with max-height + internal scroll
- [ ] **Virtual scrolling** for messages (required)
- [ ] Markdown/plain toggle; **all text selectable**
- [ ] Popovers/menus randomized 1–10 items (deterministic)
- [ ] Edit Connection is a **modal dialog** (font-aware fixed layout)
- [ ] Settings is a **separate window**, variable height, scrollable on overflow
- [ ] Narrow mode page switching: Messages/Sessions/Connections

## Notes / implementation hints (non-binding)
- For virtualization: consider `QListView` + delegates (Widgets) or `ListView` (QML).
- For markdown selection: evaluate native text vs embedded web renderer; selection is mandatory.
