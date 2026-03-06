# Subtask: VSCode extension prototype (Webview)

Parent Task: tasks/20260305-cross-framework-desktop-prototype/000-main.md

## Description
Implement the prototype described in `tasks/20260305-cross-framework-desktop-prototype/blueprint.md` as a **VSCode extension** using a **Webview**.

This is specifically to test the narrow-mode constraints and webview-host behavior:
- performance of virtual list + markdown rendering in a webview
- popover sizing/placement inside webview
- opening additional panels (Settings as separate WebviewPanel)

## Requirements checklist
- [ ] Narrow mode navigation: page switch buttons for Messages/Sessions/Connections
- [ ] Tabs concept: map to either in-webview tabs or VSCode tabs; keep behavior as close as practical
- [ ] Last 3 visited tabs preloaded (rendered but hidden) if tabs are implemented in-webview
- [ ] Message list virtual scrolling up to 1000 messages
- [ ] Markdown/plain toggle; all text selectable
- [ ] Popovers with randomized 1–10 items (deterministic)
- [ ] Edit Connection opens a modal UI (in-webview dialog)
- [ ] Settings opens a separate WebviewPanel; variable height; scrollable on overflow

## Notes / implementation hints (non-binding)
- Strong candidate to share UI code with Electron implementation.
- Ensure copy/select works given VSCode webview sandboxing.
