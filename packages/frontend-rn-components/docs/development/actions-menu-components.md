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

## Rich configuration and session actions

`RichConfigDropdownControl` renders the compact current-value trigger shared
by mobile and desktop. `RichConfigDropdownPanel` renders declared options,
custom string entry, and reset. Hosts choose the surrounding modal or native
popover and use the normal session-settings controller for mutations.

`SessionListRichActionControl` and `SessionListRichActionList` also render
normalized rich `session_action` elements in chat. Their placement argument
accepts the session-list slots and the chat `session_header`/`composer` slots.
The components do not execute actions directly; hosts provide the ordinary
action runner callbacks.

Additional maintainer entry points:

- `src/actions/RichConfigDropdown.tsx`
- `src/actions/SessionListActionsBar.tsx`
- `src/actions/SessionActionsBar.tsx`