# Subtask: JetBrains IDE plugin prototype

Parent Task: tasks/20260305-cross-framework-desktop-prototype/000-main.md

## Description
Implement the prototype described in `tasks/20260305-cross-framework-desktop-prototype/blueprint.md` as a **JetBrains IDE plugin**.

This is primarily to evaluate:
- Swing-based UI constraints (ToolWindow + dialogs)
- performance of large virtualized lists in the IDE environment
- markdown rendering + **selectable text** (native vs JCEF tradeoffs)
- popover/menus sizing (1–10 items) and edge placement

## Requirements checklist
- [ ] Narrow mode navigation: pages for Messages/Sessions/Connections within a ToolWindow
- [ ] Tabs concept: in-ToolWindow tabs (keep simple)
- [ ] Last 3 visited tabs preloaded (rendered but hidden)
- [ ] Message list virtual scrolling up to 1000 messages
- [ ] Markdown/plain toggle; all text selectable
- [ ] Popovers/menus randomized 1–10 items (deterministic)
- [ ] Edit Connection opens a modal dialog (fixed layout, font-aware)
- [ ] Settings opens as a separate dialog/tool window (separate surface); scrollable if too many sections

## Notes / implementation hints (non-binding)
- If markdown selection is poor with native components, evaluate embedding JCEF for markdown rendering; document pros/cons.
- Ensure UI remains responsive in the IDE event dispatch thread (EDT).
