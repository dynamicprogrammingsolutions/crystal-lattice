# Actions menu components

`ActionsMenuBar` composes built-in and plugin-contributed actions using stable
keys. It supports complete-menu and pinned representations while leaving pin
persistence and platform menu presentation to consuming applications.
Program-defined `baseActions` are listed before plugin-defined
`extraActions`. Numeric `order` values sort actions only within their owning
group, so a plugin cannot move ahead of Settings, Snapshots, or another
program action by declaring a lower order. This grouping applies to the
complete list only; compact pinned controls retain their global numeric order
so established toolbar and two-row composer layouts do not shift.

The compact bar hosts pinned actions in a shrinkable, clipped flex viewport
and hosts the overflow trigger in a separate non-shrinking slot. Consumers may
set `maxPinnedActionsForBar` to limit only the compact representation. Actions
beyond that limit remain pinned and available in the complete menu; pin
persistence and menu star state always use the full pinned-key set.

`showMenuButton={false}` renders only pinned controls and omits the ellipsis
slot and menu surface. The default keeps the menu. Consumers using the option
must supply the actions they want visible as pins; mobile uses it for the
single New connection action.

Consumers may set `pinnedRows={2}` and choose
`secondPinnedRowPlacement="above" | "below"`. One row remains the default.
Two-row bars wrap by available width, right-align both rows, retain the
overflow trigger on the primary row, and leave controls beyond the visible two
rows in the complete menu.

Simple pinned icons and custom rich controls occupy the same 40-point outer
action slot. Rich pills keep their intrinsic width while the shared slot
centers them vertically, including when simple actions wrap onto another row.

`ActionsMenuPanel` constrains its title to the space before the close control.
Long titles wrap to at most two lines and truncate at the tail, while the close
control remains inside the panel.

Complete action-menu rows keep their icon and pin controls at fixed widths.
Action names can wrap once to two lines on mobile and Desktop, with row height
growing to fit. The ordinary title and neutral state value share the remaining
width; the state value remains a single line. A short title leaves the remaining
width to a long value. The action accessibility label retains both complete
strings, and the pin target remains independent of a disabled action.
Application-action custom rows, rich-list options, and rich-config dropdown
options use the same two-line naming rule. Compact pinned controls retain their
existing single-line presentation. Mobile modal surfaces cap their height at
90% of the viewport so the panel's body can scroll when wrapped rows fill it.

Desktop's native action popover measures system-font label widths, including
icon, state, and pin space. Its width is bounded by the host window/screen and
480 points. The React root reports the actual header and scroll-content height;
the native owner caps the resulting height at 80% of the visible screen and
keeps taller menus scrollable. Resize messages include the owning menu ID so
late layout events cannot resize another menu.

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
