# Actions menu components

`ActionsMenuBar` composes built-in and plugin-contributed actions using stable
keys. It supports complete-menu and pinned representations while leaving pin
persistence and platform menu presentation to consuming applications.

The compact bar hosts pinned actions in a shrinkable, clipped flex viewport
and hosts the overflow trigger in a separate non-shrinking slot. Consumers may
set `maxPinnedActionsForBar` to limit only the compact representation. Actions
beyond that limit remain pinned and available in the complete menu; pin
persistence and menu star state always use the full pinned-key set.

Consumers may set `pinnedRows={2}` and choose
`secondPinnedRowPlacement="above" | "below"`. One row remains the default.
Two-row bars wrap by available width, right-align both rows, retain the
overflow trigger on the primary row, and leave controls beyond the visible two
rows in the complete menu.

`ActionsMenuPanel` constrains its title to the space before the close control.
Long titles wrap to at most two lines and truncate at the tail, while the close
control remains inside the panel.

Complete action-menu rows keep their icon and pin controls at fixed widths.
The ordinary title and neutral state value share the remaining width and
truncate independently at the tail. Sizing is adaptive rather than a fixed
percentage: a short title leaves the remaining width to a long value. The
action accessibility label retains both complete strings.

Maintainer entry point:

- `src/actions/ActionsMenuBar.tsx`
- `src/actions/ActionsMenuPanel.tsx`
- `src/actions/model.ts`

Mobile and desktop inject platform-appropriate menu surfaces and own
connection-scoped pin state.

Hosts supply action-specific disabled predicates. Request progress must not be
projected as a blanket disabled state across the entire action menu: duplicate
request starts, cancellation, append, attachments, config mutation, and
plugin actions have separate eligibility. Enabled actions continue through
their normal backend path so the server remains authoritative for concurrent
mutation acceptance.

## Rich configuration and session actions

`RichConfigDropdownControl` renders the compact current-value trigger shared
by mobile and desktop. It supports visual label/icon suppression,
host-provided character truncation, and selected-option icon/tone. The outer
config element supplies the ordinary action-menu icon and the compact fallback
icon. A selected option icon overrides it only for compact presentation.
`RichConfigDropdownPanel` uses one field for filtering and validated custom
entry. `RichConfigToggleControl` renders Boolean settings with false/true
option appearance. Hosts choose the surrounding modal or native popover and
use the normal session-settings controller for mutations.

Use the opt-in `plugins/dummy-rich-config-ui` feature to inspect every
supported semantic option tone and icon on simulators or physical devices
without modifying a provider plugin.

`SessionListRichActionControl` and `SessionListRichActionList` also render
normalized rich `session_action` elements in chat. Their placement argument
accepts the session-list slots and the chat `session_header`/`composer` slots.
The components do not execute actions directly; hosts provide the ordinary
action runner callbacks.

Additional maintainer entry points:

- `src/actions/RichConfigDropdown.tsx`
- `src/actions/SessionListActionsBar.tsx`
- `src/actions/SessionActionsBar.tsx`