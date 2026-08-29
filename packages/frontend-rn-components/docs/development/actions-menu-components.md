# Actions menu components

`ActionsMenuBar` composes built-in and plugin-contributed actions using stable
keys. It supports complete-menu and pinned representations while leaving pin
persistence and platform menu presentation to consuming applications.

The compact bar hosts pinned actions in a shrinkable, clipped flex viewport
and hosts the overflow trigger in a separate non-shrinking slot. Consumers may
set `maxPinnedActionsForBar` to limit only the compact representation. Actions
beyond that limit remain pinned and available in the complete menu; pin
persistence and menu star state always use the full pinned-key set.

`ActionsMenuPanel` constrains its title to the space before the close control.
Long titles wrap to at most two lines and truncate at the tail, while the close
control remains inside the panel.

Maintainer entry point:

- `src/actions/ActionsMenuBar.tsx`
- `src/actions/ActionsMenuPanel.tsx`
- `src/actions/model.ts`

Mobile and desktop inject platform-appropriate menu surfaces and own
connection-scoped pin state.