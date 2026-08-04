# Actions menu components

`ActionsMenuBar` composes built-in and plugin-contributed actions using stable
keys. It supports complete-menu and pinned representations while leaving pin
persistence and platform menu presentation to consuming applications.

Maintainer entry point:

- `src/actions/ActionsMenuBar.tsx`

Mobile and desktop inject platform-appropriate menu surfaces and own
connection-scoped pin state.