# Mobile connection actions and compact layout

Replace the mobile Connections tab's active-connection panel and existing
cards with per-card pinnable actions, compact status presentation, and modal
health/settings flows while retaining the header action bar delivered by 030.

## Requirements checklist

### Functional requirements

- [x] Saved connection cards show no Last used row and include a bottom row
  with left-aligned Open/Closed status and right-aligned pinnable actions.
- [x] Card actions include Delete, Health Check, Open, Disconnect, and Server
  Settings wherever applicable to the card's state.
- [x] Delete retains destructive confirmation; deleting the active connection
  safely disconnects it.
- [x] Health Check shows successful response or failure details in a modal.
- [x] Active-card Settings opens the established Server Settings modal.
- [x] The large Connected to panel is absent and the Connections list uses the
  available tab height with a compact bold title.

### Non-functional requirements

- [x] Card controls reuse the shared `ActionsMenuBar` and existing
  pinned-action persistence rather than custom overflow/pinning UI.
- [x] One centralized action model computes stable definitions,
  availability, disabled state, icons, and routing.
- [x] One persisted card pin set is shared across connection records and is
  filtered for each row's applicable actions.
- [x] In-flight opening, health-checking, disconnecting, and deletion prevent
  duplicate conflicting operations and expose accessible state.
- [x] Existing manual, discovery, bridge repair, cloud, reconnect, and
  disconnect behavior remains owned by `App.tsx` and is invoked through
  callbacks rather than duplicated in the screen.

Parent Task: `tasks/20260827-cross-platform-markdown-and-mobile-connections/000-main.md`

Depends On: `tasks/20260827-cross-platform-markdown-and-mobile-connections/030-mobile-global-settings-and-markdown.md`

## Execution plan
Status: Approved

Remove the active `ConnectionScreen` section from `ConnectedRoot` and let
`ConnectionsScreen` fill the tab when the connection wizard is not active.
Pass the active record ID, backend, transport, disconnect callback, and modal
triggers needed to calculate row state and route actions.

Retain the stable header actions and production Global Settings entry point
delivered by 030. Define stable card actions (`delete`, `healthCheck`, `open`,
`disconnect`, `serverSettings`) with a separate versioned shared card pin key.
Render `ActionsMenuBar` at the right of each card footer. Filter available card
actions by active/closed state and disable actions during relevant
asynchronous work.

Keep the existing card name, method badge, and connection detail. Remove Last
used display while retaining `lastUsedAt` for existing sort/persistence
behavior. Add Open/Closed status text using `theme.success` and
`theme.textSecondary`. Compact the list title to card-title typography.

Preserve the New Connection and Global Settings routes from 030. Route active
Server Settings to one `ServerSettingsModal` instance hosted by the connected
shell. Run Health Check through the active transport's existing `/api/hello`
request and present a dedicated `PanelModalFrame` result modal. Preserve delete
confirmation and make active deletion disconnect first.

Add focused card/action/modal tests, run the mobile package and relevant
connection regression checks, and update the mobile Connections development
documentation in this subtask before marking it complete. Include integration
coverage for the 030 header where the combined full-list layout makes that
earlier work newly testable.

### Implementation decisions and open questions

- Header pins remain owned and verified by 030.
- Card pins are shared across all records; unavailable pinned actions simply
  do not render for that row.
- Default card pins are Open, Disconnect, Health Check, and Settings;
  Delete starts in the complete menu but remains pinnable.
- Active is defined by matching `activeConnectionId` plus live
  backend/transport. The UI shows only `Open` and `Closed`, as requested; an
  in-flight action may use disabled/spinner treatment without adding a third
  persisted status.
- Open continues to call the existing saved-connection callback. Whether the
  current automatic navigation to Sessions remains should be preserved unless
  implementation inspection shows it conflicts with seeing the updated row;
  no transport behavior should be rewritten merely for navigation.
- The list heading remains `Connections` (plural) but takes the smaller bold
  card-title style.

### Documentation

- Extend mobile development documentation with the Connections host layout,
  card action applicability table, card-pin ownership, active-status
  definition, modal routing, and primary tests.
- Keep bridge transport documentation unchanged unless a callback signature
  needs a factual hosting update; transport semantics do not change.

### Task checklist

- [x] Centralize card action definitions/applicability.
- [x] Add persistent shared card pin state.
- [x] Add per-card footer status and `ActionsMenuBar`.
- [x] Remove Last used and the upper Connected to panel.
- [x] Add Global Settings and Server Settings routing.
- [x] Add health-check result modal and async state.
- [x] Preserve safe delete/disconnect and all connection methods.
- [x] Add focused component and flow tests.
- [x] Run relevant mobile package and connection regression checks.
- [x] Update mobile Connections development documentation.
- [x] Record mobile connection verification evidence.

### Requirement verification

- Component tests cover empty and populated lists, compact heading, absence of
  Connected to/Last used, card default pins, pin changes, and stored card-pin
  reconstruction.
- State-table tests cover closed, active, and in-flight rows, including exact
  available/disabled actions and Open/Closed colors.
- Interaction tests cover New Connection, Global Settings, Open, Disconnect,
  confirmed/cancelled Delete, active Server Settings, and successful/failed
  Health Check modal output.
- Existing bridge/manual/cloud callback tests confirm screens still delegate
  to production connection ownership.
- A human checks card wrapping, footer alignment, action menus, and both modal
  flows on representative iOS and Android widths.

### Additional implementation verification

- Run focused Connections/ConnectedRoot/Settings mobile Jest tests.
- Run the full mobile Jest suite, TypeScript check, and lint.
- Update and run the focused connection Detox path if stable native geometry
  or action selection cannot be demonstrated at component level.
- Re-run bridge transport mode coverage because the New/Open action routes use
  the same parent connection callbacks.

## Implementation Notes

- Kept connection opening, reconnect/repair, disconnect, and deletion in
  `App.tsx`; the redesigned screen only routes actions to those owners.
- Preserved the existing `connections-new-connection` production test ID on
  the new pinned action.

## Completion Notes

- Removed the upper Connected to section and Last used rows, compacted the
  title, and added Open/Closed card footers with shared pinnable card actions.
- Added active Server Settings routing and modal success/error health results.
- Focused Connections tests and the full 124-test mobile suite passed; mobile
  TypeScript passed.
- Existing connection transport semantics and backend APIs were unchanged.
- Card geometry and modal presentation on representative iOS/Android devices
  remain human checkpoints.

## Post-completion follow-up

- [x] Add focused Detox coverage for header/card actions, pin persistence,
  status, health and server-settings modals, and native card geometry.
- [x] Pass the focused Connections/Settings scenario on iOS and Android.
- [x] Re-run the existing bridge-transport scenario on iOS and Android.

Follow-up evidence:

- The focused scenario passed on both configured native targets and covered
  header/card actions, pin persistence after relaunch, Open/Closed state,
  health and server-settings modals, Open/Disconnect, and card/preview bounds.
- The existing bridge-transport scenario passed on both targets and exercised
  the production `connections-new-connection` pinned action.

### Shared tab-gutter alignment follow-up

Status: Approved

Connections no longer adds a second screen-level inset inside the common
`ConnectedRoot` content gutter. Its visible card edges now match Sessions and
Messages. The Connections title uses the card content inset, aligning its
optical left edge with connection-card titles.

Component coverage proves the Connections root does not own extra padding and
derives title alignment from the card padding/border styles. The production
Connections/Settings Detox scenario compares native title/card-title bounds.

Completion evidence:

- Complete mobile Jest passes 31 suites and 137 tests; TypeScript passes.
- Fresh iOS and Android Detox builds pass.
- Connections/Settings passes on iOS and on an Android fresh-emulator retry.
  The first Android attempt was blocked before the harness appeared by an
  emulator `Activity.setTheme` ANR.