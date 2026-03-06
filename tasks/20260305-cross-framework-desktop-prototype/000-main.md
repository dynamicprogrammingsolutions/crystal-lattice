# Cross-framework desktop + IDE prototype (main task)

## Description
Build a **UI/UX and performance evaluation prototype** (mock-data only) that can be implemented consistently across multiple desktop frameworks and IDE extension hosts.

The prototype is intended to:
- Compare framework **capabilities** (popovers, modals, multi-window, selectable rich text, nested scrolling).
- Compare **performance characteristics** (virtual scrolling + large message sets; markdown rendering).
- Provide a reusable base for iterating on the product’s initial design after selecting the target framework.

This directory contains the current **blueprint/spec** plus implementation subtasks per target framework.

## Supporting docs
- Blueprint/spec: `tasks/20260305-cross-framework-desktop-prototype/blueprint.md`

## Subtasks
1. `tasks/20260305-cross-framework-desktop-prototype/010-electron-desktop.md`
2. `tasks/20260305-cross-framework-desktop-prototype/020-javafx-swing-desktop.md`
3. `tasks/20260305-cross-framework-desktop-prototype/030-qt-desktop.md`
4. `tasks/20260305-cross-framework-desktop-prototype/040-flutter-dart-desktop.md`
5. `tasks/20260305-cross-framework-desktop-prototype/050-vscode-extension-webview.md`
6. `tasks/20260305-cross-framework-desktop-prototype/060-jetbrains-ide-plugin.md`

## Shared constraints (apply to all subtasks)
- Use **deterministic mock data** (seeded generator) so all implementations can be compared fairly.
- Keep interactions simple; implement only the behaviors called out in the blueprint (esp. those that expose performance/capability issues).
- Ensure **virtual scrolling** is available and used for the large message list (or the closest supported equivalent).
- Ensure **text selection** works across all message content, including markdown-rendered content.
