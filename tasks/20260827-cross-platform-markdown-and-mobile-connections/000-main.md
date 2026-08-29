# Cross-platform markdown display preferences and mobile connections redesign

Plan and track one coordinated implementation that aligns desktop and mobile
markdown typography, adds persistent display controls, and rebuilds the mobile
Connections tab around the existing pinnable action UI.

## Requirements checklist

### Functional requirements

- [x] Desktop and mobile markdown-rendered message prose use the same 15-point
  base font size by default.
- [x] Users can select a supported markdown base font size globally for the
  application; desktop exposes the choice in the macOS View menu and mobile
  exposes it in global Settings.
- [x] Users can select `Normal` or `Small` markdown headers globally from the
  same desktop and mobile settings surfaces.
- [x] The `Normal` header profile gives higher-level headings a proportional
  hierarchy and keeps lower-level headings at body size; the `Small` profile
  preserves the current compact desktop behavior by rendering every heading
  level at body size.
- [x] Display preference changes apply immediately to all markdown-rendered
  messages and remain selected after the application restarts.
- [x] Mobile global Settings uses the established settings modal frame and
  contains one dropdown for base font size and one dropdown for markdown
  headers.
- [x] The mobile Connections header replaces the standalone New Connection
  button with the established pinnable actions component; Settings and New
  Connection are pinned by default.
- [x] Each saved mobile connection card has one bottom action row with
  pinnable Delete, Health Check, Open, Disconnect, and Settings actions,
  filtered or disabled according to that connection's current state.
- [x] Each connection card shows `Open` in green for the active connection or
  `Closed` in gray for an inactive connection on the left side of its bottom
  row, with the action bar right-aligned.
- [x] The mobile connection card no longer shows its Last used row.
- [x] Health Check runs against the active connection and presents either the
  successful response or error details in a modal.
- [x] Settings on the active connection opens the same Server Settings modal
  used by the Sessions header.
- [x] The large mobile Connected to section is removed; the saved-connections
  list fills the Connections tab and its title is compact and bold like the
  connection card titles.

### Non-functional requirements

- [x] Desktop and mobile consume one typed markdown-display preference
  contract for defaults, supported values, normalization, and heading-scale
  calculation despite using different markdown renderers.
- [x] Global display preferences use provider/hook state and platform-owned
  persistence, without mutable module-level application state or broad prop
  threading.
- [x] Mobile reuses `ActionsMenuBar`, persistent pinned-action state,
  `PanelModalFrame`, and the existing option-picker conventions instead of
  introducing parallel action or modal systems.
- [x] Connection action definitions and applicability rules are centralized,
  stable-keyed, accessible, and covered by production test identifiers.
- [x] Existing connection transport, reconnect/repair, session, message,
  notification, and server-setting behavior remains intact; no backend API
  changes are introduced.
- [x] Focused automated tests cover preference normalization and persistence,
  both markdown renderer mappings, desktop native menu wiring, mobile settings
  interaction, connection action availability, and health/settings modal
  routing.
- [x] Current package development documentation describes the delivered
  preference ownership, native-menu bridge, and mobile Connections hosting
  without exposing task-tracking language.

## Scope and workstreams

This is one delivery split into dependency-ordered workstreams so implementation
and evidence can be tracked without dividing approval or release:

1. Define the shared display-preference contract.
2. Wire the contract into desktop native menus, persistence, and markdown.
3. Add mobile global preference state, Settings, persistence, markdown, and
   the production Connections-header entry point.
4. Rebuild mobile connection cards around per-card actions and compact status.

Desktop connection-list behavior is not part of this change. Mobile connection
transport semantics and backend endpoints are also unchanged.

## Resolved requirement decisions

1. **Base font-size choices.** Use `13`, `15 (Default)`, `17`, and `19`,
   represented by point values in both applications.
2. **Exact Normal heading baseline.** Current mobile enriched markdown uses
   `32/24/18/16/13/11` for H1–H6 at a 15-point body, but the request also says
   lower levels should match body text. Use `32/24/18/15/15/15` at the
   15-point baseline and scale those values proportionally for other base
   sizes. This changes current mobile H4–H6 slightly in order to satisfy the
   stated hierarchy.
3. **Meaning of base font size.** The preference controls
   markdown prose, lists, blockquotes, tables, and inline code, while fenced
   code blocks keep the existing dedicated code-size token. Raw message views
   and non-markdown application chrome remain unchanged.

## Supporting findings

- Desktop's primary markdown component uses
  `react-native-markdown-display` and hardcodes 13-point body and inline-code
  text. All six heading levels currently share one bold style with no explicit
  size, which produces the requested `Small` profile.
- Both desktop and mobile themes already define message text as 15 points.
  Mobile's primary enriched markdown renderer uses that token for prose.
- Mobile's enriched renderer explicitly defines its current H1–H6 values.
  A legacy markdown-display component remains in the tree and should consume
  the same preference contract so fallback paths do not drift.
- Desktop already persists View-menu choices in `NSUserDefaults`, sends native
  change events through `DesktopWindowManager`, and supplies the latest values
  as initial props to every new main window.
- Mobile already persists pinnable action choices in AsyncStorage and uses the
  shared `ActionsMenuBar` on Sessions and Messages.
- `PanelModalFrame` is the established frame for mobile Session and Server
  Settings. `OptionsPickerModal` provides the existing dropdown/picker
  interaction.
- Mobile owns one active backend/transport at a time. Consequently, `Open`
  applies to inactive records; `Disconnect`, Health Check, and Server Settings
  apply to the active record; Delete applies to every saved record.

## Subtasks

- [x] `tasks/20260827-cross-platform-markdown-and-mobile-connections/010-shared-markdown-display-contract.md`
- [x] `tasks/20260827-cross-platform-markdown-and-mobile-connections/020-desktop-markdown-view-preferences.md`
- [x] `tasks/20260827-cross-platform-markdown-and-mobile-connections/030-mobile-global-settings-and-markdown.md`
- [x] `tasks/20260827-cross-platform-markdown-and-mobile-connections/040-mobile-connection-actions-and-layout.md`

## Execution plan
Status: Approved

Implement the shared preference vocabulary first, including defensive parsing
of persisted/native inputs and pure heading-size derivation. Keep persistence
platform-owned: macOS `NSUserDefaults` remains authoritative for desktop menu
state, while mobile uses AsyncStorage. A shared React context carries the
resolved preference values to renderers so message rows update immediately
without passing settings through every screen and chat component.

On desktop, add two radio-style View submenus, `Markdown Font Size` and
`Markdown Headers`. Extend the existing AppDelegate → notification →
`DesktopWindowManager` → `DesktopRoot` route used by tab-strip preferences.
Initial props must contain current values for both the first and subsequently
created windows. Feed the resulting context into
`react-native-markdown-display`, setting body-like nodes and explicit
per-heading styles from the shared contract.

On mobile, load and normalize preferences during application startup, wrap the
connected UI with the shared preference provider, and add a Global Settings
modal using `PanelModalFrame`. Each setting opens the existing option-picker
surface. Update both enriched and legacy markdown implementations, including
line-height derivation, so they agree with desktop semantics. In the same
subtask, replace the existing Connections-header New Connection button with
the pinnable Settings/New Connection action bar so the complete mobile
preference workflow is available and manually testable before card redesign.

Then replace the mobile Connections tab's split active/list layout with one
full list and add one shared per-connection pin set for all cards. Build a
small app-local connection action definition layer that computes available
and disabled actions from `activeConnectionId`, backend/transport
availability, and in-flight work. Destructive deletion keeps confirmation.
Active-row Settings opens Server Settings. Health Check uses the active
transport and presents a dedicated result modal built on the standard modal
frame.

Each subtask adds its own focused tests, runs the relevant package checks, and
updates its owning current implementation documentation before it is marked
complete. Later subtasks may add integration evidence for earlier work when
their production wiring makes that work newly testable. Perform manual visual
checks on macOS and at least one iOS and one Android target for actual markdown
geometry and compact connection-card layout; leave those checklist items
incomplete until a human confirms them.

### Risks and mitigations

- Changing markdown metrics can affect transcript height and scroll anchoring.
  Run existing transcript component coverage and manually check a mixed
  heading/code/list transcript before accepting the visual result.
- Desktop preferences must stay synchronized across multiple open windows.
  Reuse the existing native notification route and make new-window initial
  props read current `NSUserDefaults`.
- Mobile settings may render before AsyncStorage hydration. Keep the existing
  loading boundary or add a preference-specific hydration boundary so the
  default does not briefly overwrite or flash before a stored value loads.
- Per-card pin state can become confusing if it is stored per record. Use one
  global connection-card pin list and filter it by each record's available
  actions.
- Opening a second modal immediately after an action-menu modal can be
  unreliable on iOS. Follow the existing deferred-presentation convention
  where needed.

### Implementation decisions and open questions

- Proposed shared owner: `packages/frontend-rn-components` owns the typed
  preference values, options, normalization, scale derivation, provider, and
  hook. Each application owns persistence and menu/modal presentation.
- Proposed persisted defaults: 15-point base and `Normal` headers. Missing,
  malformed, and obsolete values normalize to those defaults.
- Proposed heading scaling: derive sizes relative to a 15-point baseline and
  round to whole points. `Small` maps H1–H6 to the selected body size.
- Proposed mobile connection-card pin defaults: Open, Disconnect, Health
  Check, and Settings are initially pinned; Delete remains available in the
  complete menu and can be pinned by the user.
- Proposed connection status model: because mobile hosts one active
  connection, only the record matching `activeConnectionId` with a live
  backend/transport is `Open`; all other records are `Closed`.
- Proposed applicability: closed records expose Open and Delete; the active
  record exposes Disconnect, Health Check, Settings, and Delete. Actions not
  applicable to a row are omitted from that row's available action list,
  while temporary in-flight states disable relevant actions.
- Proposed title interpretation: retain the user-facing plural `Connections`
  label but restyle it to the same compact bold typography as card titles.
- No standalone specification is proposed. The behavior is application UI
  configuration with a small shared component contract; this approved task
  plus package-local current implementation docs should be proportional.
- The approved requirement decisions above are authoritative for execution.

### Documentation

- The 010 subtask owns shared-package documentation for the exported
  preference provider and derivation API.
- The 020 subtask owns desktop development documentation for markdown display
  preferences, View-menu/native-event ownership, multi-window synchronization,
  and primary tests.
- The 030 subtask owns mobile development documentation for global display
  preference ownership, persistence, markdown renderers, the production
  Settings entry point, and primary tests.
- The 040 subtask owns mobile development documentation for connection-card
  action hosting, applicability, status, modal routing, and primary tests.
- Keep README files unchanged unless implementation reveals a missing setup or
  first-use fact. Do not edit generated documentation-site output directly.

### Task checklist

- [x] Resolve the base-size, heading-baseline, and preference-scope questions.
- [x] Complete and track the shared markdown preference contract subtask.
- [x] Complete and track the desktop View-menu and renderer subtask.
- [x] Complete and track the mobile Settings and renderer subtask.
- [x] Complete and track the mobile Connections redesign subtask.
- [x] Confirm every subtask records its own focused verification,
  documentation, and any still-pending human checks.
- [x] Append implementation and completion notes with concrete evidence.

### Requirement verification

- Shared defaults and matching desktop/mobile output: unit tests assert
  preference normalization and both renderer style maps for every supported
  base size and header profile.
- Desktop controls and persistence: focused tests verify native initial props,
  menu selection/check state, event delivery, new-window values, and rendered
  markdown style changes.
- Mobile controls and persistence: component tests select each option through
  Global Settings, verify immediate renderer updates, reconstruct the
  preference owner from stored values, and verify invalid-value fallback.
- Connections header and cards: component tests assert default pins, pin
  persistence, compact title/layout, absent Last used/Connected to content,
  per-state status text/color, action availability, confirmation, and routing.
- Health and Server Settings: component tests use a production `Transport`
  boundary with controlled success/error responses and assert modal content;
  active-row Settings must render the same `ServerSettingsModal` component
  used by Sessions.
- Human visual verification: compare representative markdown and connection
  cards on macOS, iOS, and Android. This remains incomplete until confirmed by
  a human.

### Additional implementation verification

- Run shared component tests and type checking for affected exports.
- Run focused and full mobile Jest suites, mobile TypeScript checking, and
  lint for touched files.
- Run focused and full desktop Jest suites, desktop lint, and a macOS build or
  focused XCUITest for the native View menu.
- Run existing transcript-scroll and connection-flow regression slices most
  likely to detect layout or reconnect regressions.

## Implementation Notes

- Verification and documentation were completed in 010–040; the former 050
  subtask was removed as requested.
- Moving the production Connections-header entry point into 030 made the
  complete mobile preference workflow independently testable before 040.

## Completion Notes

- Delivered shared 15-point default markdown typography, selectable
  13/15/17/19 sizes, Normal/Small headers, desktop View menus, and mobile
  Global Settings with persistence.
- Delivered the compact mobile Connections layout, global and per-card pinned
  actions, Open/Closed status, Server Settings routing, and modal health
  results.
- Automated evidence passed: shared 35 tests, desktop 110 tests, mobile 124
  tests, mobile/shared TypeScript checks, and the native macOS Debug build.
- Desktop full TypeScript and repository lint are not clean due to existing
  baselines; mobile lint has no configuration. No new lint finding remains in
  the touched desktop markdown file.
- The focused macOS UI test compiled but could not execute because macOS
  automation mode timed out. Human visual checks remain for macOS, iOS, and
  Android typography and connection-card geometry.
- No backend API or connection transport behavior was changed.

## Post-completion follow-up

- Reopened native UI verification with user approval.
- Add and run focused mobile Detox coverage on iOS and Android for production
  Connections, Global Settings, persistence, actions, modals, and geometry.
- Re-run the existing bridge-transport Detox scenario on both platforms.
- Extend the macOS XCTest with renderer geometry assertions, but do not run
  XCTest until the user confirms desktop automation is enabled.

Follow-up results:

- Added a production-component mobile harness and focused Detox scenario.
- The scenario passed on iOS and Android. The existing bridge-transport
  scenario also passed on both platforms.
- Native execution exposed and fixed unreliable nested-modal presentation in
  Global Settings on iOS.
- Added macOS geometry XCTest coverage; execution was intentionally paused
  until user confirmation.

After user confirmation, the focused macOS XCTest class passed both menu
persistence and renderer-geometry tests with zero failures.

### Approved follow-up execution plan

Status: Approved

This follow-up changes connection-card routing and broadens the existing
markdown base-size preference into an explicit display typography preset used
by desktop and mobile.

#### Follow-up requirements

Functional:

- [x] Pressing a mobile connection card navigates to Sessions immediately.
- [x] A closed card begins opening its connection concurrently with
  navigation; an already-open card navigates without reconnecting.
- [x] Pressing the card's Open action opens the connection without navigating
  away from Connections, and other card actions also do not trigger card
  navigation.
- [x] Selectable font sizes are 14, 15 (Default), 16, and 17 on desktop and
  mobile.
- [x] The selected preset updates responsive application text, including
  markdown/message content, message headers and metadata, message footers,
  reasoning/tool text, editing/composer text, responsive settings/actions
  text, and code text.
- [x] Small text observes explicit minimum sizes, so selecting 14 does not
  shrink an 11-point message footer while selecting 16 and 17 increases it.
- [x] Card, panel, modal, and screen titles remain fixed unless they already
  opt into a responsive semantic token.
- [x] Normal prose uses the larger explicit line height in each preset on
  desktop and mobile.
- [x] Normal and Small markdown headers use the selected explicit font-size
  and line-height tables.
- [x] The desktop Markdown Headers menu visibly changes real rendered markdown
  headings; Normal is hierarchical and Small uses body-sized H1-H6.
- [x] Existing stored 13 and 19 selections migrate to 14 and 17 respectively.

Non-functional:

- [x] Shared immutable preset tables are the single source for responsive font
  sizes, line heights, and markdown heading metrics.
- [x] Responsive hardcoded 10-15 point message/chat styles are replaced by
  semantic typography tokens; fixed titles and layout dimensions remain
  explicit.
- [x] Card navigation and connection opening use separate callbacks instead of
  relying on nested press-event behavior.
- [x] Desktop semantic colors and mobile light/dark colors remain
  platform-owned; the shared helper overlays only typography.
- [x] Tests exercise the final markdown renderer boundary, not only the pure
  typography adapter.

#### Explicit typography presets

| Selected | tiny | small | secondary | normal | message | large | code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 11/15 | 12/17 | 13/18 | 14/20 | 14/20 | 16/22 | 14/19 |
| 15 | 11/15 | 12/17 | 13/18 | 14/20 | 15/21 | 16/22 | 14/19 |
| 16 | 12/17 | 13/18 | 14/20 | 15/21 | 16/23 | 16/22 | 15/21 |
| 17 | 13/18 | 14/20 | 15/21 | 16/23 | 17/24 | 17/24 | 16/22 |

Each cell is `font size / line height`. `title`, `screenTitle`, and `display`
remain fixed. Explicit connection-card titles also remain fixed.

Normal markdown headings use:

| Selected | H1 | H2 | H3 | H4-H6 |
| --- | --- | --- | --- | --- |
| 14 | 30/36 | 22/27 | 17/22 | 14/20 |
| 15 | 32/38 | 24/29 | 18/23 | 15/21 |
| 16 | 34/41 | 26/32 | 19/24 | 16/23 |
| 17 | 36/43 | 27/33 | 20/25 | 17/24 |

Small H1-H6 use the selected `message` font size and line height.

#### Approach

Split `ConnectionsScreen` callbacks into card press and Open action paths.
`ConnectedRoot` changes tabs synchronously on card press, then starts opening
only when the record is not already active with a live transport. The Open
action calls the connection owner directly and keeps the Connections tab
active.

Replace 13/15/17/19 with 14/15/16/17 in the shared contract, mobile picker, and
native macOS menu. Normalize legacy 13 to 14 and 19 to 17. Add shared immutable
font-size, line-height, and markdown-heading tables plus a helper that overlays
responsive typography onto a platform color theme.

Apply the typography overlay at each application theme boundary so preference
changes update all mounted consumers. Migrate responsive hardcoded text in
desktop/mobile message and chat surfaces to semantic tokens. Keep title-scale
text, connection-card titles, icons, spacing, and hit targets fixed.

Fix desktop markdown heading rendering by leaving `styles.text` color-only.
`react-native-markdown-display` computes inherited heading typography, but the
current body-sized `styles.text` is applied afterward and overrides it. Keep
base prose typography on `body`, and test actual rendered markdown inheritance.

### Implementation decisions and open questions

- Approved legacy migration: 13 to 14 and 19 to 17.
- Approved responsive preset and heading tables are recorded above; later
  tuning changes table entries rather than introducing scaling formulas.
- Code text participates in the responsive preset. Title-scale typography and
  explicit card titles do not.
- Card navigation occurs before connection completion. On failure, Sessions
  remains visible with available cached/offline state and the existing error
  alert.
- No backend or transport contract changes are required.

### Documentation

- Update shared display-preference documentation with the preset tables,
  responsive/fixed token boundary, and legacy migration.
- Update mobile documentation with card versus Open-action routing and the
  application theme overlay.
- Update desktop documentation with the broader Font Size menu, semantic theme
  overlay, line-height ownership, and final-renderer inheritance fix.

### Task checklist

- [x] Split card navigation from Open-action connection routing.
- [x] Add exact shared font-size, line-height, and heading presets.
- [x] Add legacy preference migration and update both controls.
- [x] Apply typography presets to mobile and desktop theme boundaries.
- [x] Migrate responsive hardcoded message/chat styles to semantic tokens.
- [x] Fix desktop final-renderer heading inheritance.
- [x] Add focused unit, component, Detox, and XCTest coverage.
- [x] Update owning development documentation.
- [x] Record follow-up implementation and completion evidence.

### Requirement verification

- Connection tests prove immediate card navigation before a deferred open
  resolves, no reconnect for an open card, and no navigation from Open or
  other action icons.
- Shared tests assert every font-size, line-height, and heading-table entry,
  fixed title values, malformed fallback, and 13/19 migration.
- Desktop and mobile component tests assert message content/footer/header/code
  styles for every preset and verify actual markdown heading inheritance.
- Mobile Detox verifies card versus Open-action navigation, preference
  persistence, footer/prose geometry, and Normal/Small rendered headings on
  iOS and Android.
- macOS XCTest verifies 14/15/16/17 menu persistence plus actual prose,
  footer, and Normal/Small heading geometry.

### Additional implementation verification

- Run shared component tests and type checking.
- Run complete mobile and desktop Jest suites and mobile TypeScript.
- Build fresh iOS/Android Detox applications and run the focused typography,
  connection, and bridge scenarios on both targets.
- Build and run the focused signed macOS XCTest class.
- Re-run transcript scrolling/layout regression coverage because font and line
  height changes alter row geometry.

Follow-up implementation notes:

- The desktop header defect was confirmed at the final
  `react-native-markdown-display` merge: body-sized `styles.text` overrode the
  inherited heading style. Base metrics now live on `body` and `text` is
  color-only.
- Shared focused verification currently passes 43 tests. Desktop final-renderer
  tests confirm real Normal and Small heading output, not only adapter values.
- Mobile TypeScript passes after introducing required semantic line-height
  tokens and the 14/15/16/17 preset contract.
- Full automated verification passes: shared 43 tests, mobile 134 tests,
  desktop 113 tests, mobile TypeScript, and `git diff --check`.
- Fresh iOS and Android builds pass the Connections/Settings Detox scenario,
  bridge transport regression, and transcript-scroll regression. The native
  scenario verifies card versus Open navigation, persisted 17/Small settings,
  Normal-to-Small heading geometry, larger body metrics, and footer-token
  geometry.
- The updated macOS app and focused XCTest class compile and sign. Two
  execution attempts were blocked before test start by the host automation
  permission gate: `Timed out while enabling automation mode`.
- After automation was enabled, the focused macOS XCTest retry passed both
  tests with zero failures. It verified 17/Small persistence across relaunch,
  actual Normal/Small markdown heading geometry, 14-to-17 body growth, and
  15-to-16 footer-token growth.

#### Follow-up completion notes

- Delivered immediate Sessions navigation from connection cards without
  reconnecting an already-open record. Open and other card actions remain on
  Connections.
- Delivered explicit 14/15/16/17 font-size and line-height presets across
  shared, desktop, and mobile typography consumers, including legacy 13/19
  migration.
- Fixed final desktop markdown heading inheritance and mobile native markdown
  style refresh when display preferences change.
- Verification passed at every planned boundary: shared, mobile, and desktop
  unit/component suites; mobile TypeScript; fresh iOS/Android native builds;
  Connections/Settings, bridge, and transcript Detox on both mobile
  platforms; and the focused signed macOS XCTest class.
- Desktop full TypeScript remains non-clean only for the pre-existing SDK URL,
  ChatPane optional-string, and Theme `shadow` baselines. No touched follow-up
  typography, connection, renderer, harness, or native-menu file appears in
  that error output.

### Completed semantic typography and syntax-highlighter follow-up

After the approved 14/15/16/17 follow-up, the user manually tuned individual
font-size and line-height entries in the explicit display typography presets.
Those maintained preset tables are the current source of truth; the earlier
numeric table in this task records the initially approved baseline rather than
the final tuned values.

Additional completed updates:

- Desktop session cards, connection rows, tabs, the chat header, and related
  application chrome consume semantic theme typography and colors.
- Desktop non-markdown message content consumes the semantic `message` font
  size and line height.
- Desktop and mobile fenced code blocks use a monospace font plus the semantic
  `code` font size and line height.
- `react-native-syntax-highlighter` was forked to
  `ferenci84/react-native-syntax-highlighter` on
  `feature/native-line-height`; commit
  `4602848d2271b4809257be81ae0308f562c99910` adds native line-height support.
- Desktop and mobile consume that fork through direct Git dependencies.

These updates reinforce that consumer and UI tests should obtain expected
metrics from the maintained preset selected by the scenario. Tests may assert
ordering, equality, growth, clipping, or consumer-to-preset mapping, but should
not duplicate the preset's literal numeric entries.

### Session-card typography and desktop Connections follow-up

Status: Approved

This follow-up reopens work in the existing 010, 020, and 030 subtasks. A later
approved mobile gutter correction also reopens 040. It does not create another
subtask.

#### Follow-up requirements

Functional:

- [x] Mobile session cards use `large` for the title, `normal` for the
  subtitle or preview, `small` for the session ID, and `tiny` for metadata.
- [x] Desktop session cards use `normal` for the title, `secondary` for the
  subtitle or preview, `small` for the session ID, and `tiny` for metadata.
- [x] Every session-card font-size role uses the matching semantic line-height
  role on both platforms.
- [x] Rich session actions shown in a card use matching semantic font-size and
  line-height roles for labels and textual icon fallbacks.
- [x] The desktop Connections panel is expanded by default and has an
  accessible chevron that collapses the saved-connection list to its header
  and expands it again.
- [x] An expanded desktop Connections panel with zero through three records
  uses its natural content height and is not scrollable.
- [x] An expanded desktop Connections panel with more than three records uses
  a bounded, scrollable viewport equivalent to about three connection rows,
  and every record remains reachable.
- [x] The bounded connection list visibly communicates that more records
  continue below the initial viewport with a bottom fade that disappears when
  the user reaches the real bottom.

Non-functional:

- [x] Session-card typography consumes the existing explicit semantic preset
  tables; it does not introduce scaling formulas or duplicate platform
  presets.
- [x] The connection-list maximum is derived from semantic row metrics and
  spacing so it remains appropriate when the selected font-size preset
  changes.
- [x] The connection rows are built once and hosted in a plain natural-height
  container for up to three records or a scroll container for more than three
  records.
- [x] Expanded/collapsed state is local presentation state; connection
  persistence, focus, opening, closing, deletion, and transport ownership do
  not change.
- [x] Production accessibility identifiers support component and native
  geometry verification without introducing test-only behavior into the
  production component.
- [x] Tests derive expected typography and geometry thresholds from the active
  display preset and rendered layout instead of copying literal preset values.

#### Approach

Reopen 030 for the mobile session-card styles and tests. Preserve the mobile
card's current visual hierarchy by pairing `large`, `normal`, `small`, and
`tiny` font sizes with their matching line heights. Add stable identifiers for
the session ID and preview so tests can inspect both presentation branches.

Reopen 020 for the desktop session-card styles and the desktop Connections
panel. Increase desktop session title, subtitle/preview, and ID text to
`normal`, `secondary`, and `small`, retaining `tiny` metadata. Add a chevron to
the Connections header using its existing right-side composition point. Keep
the panel expanded by default and do not persist its disclosure state.

Build connection row elements once. For zero through three records, host them
in a plain `View` so the panel is content-sized and has no scroll semantics.
For more than three, host the same rows in a `ScrollView` with a
theme-derived maximum height equivalent to three standard rows. Render a
non-interactive bottom fade while additional content remains below the
viewport. Track scroll and content geometry so the fade disappears at the real
bottom and reappears when the user scrolls away from it. Retain the existing
saved-record count and normal vertical scroll indicator as secondary cues.

Reopen 010 only for the shared rich session-action typography. Add matching
line heights to the current-value label and explicit semantic size/line-height
metrics to its textual fallback. Vector icon dimensions remain unchanged.

Each reopened subtask owns its focused verification and documentation. There
is no separate verification or documentation subtask.

#### Implementation decisions and open questions

- Recommended interpretation: the new `normal`/`secondary`/`small`/`tiny`
  mapping is desktop-specific. Applying it to mobile would reduce the default
  mobile title from 16 to 14 points, which conflicts with retaining its current
  hierarchy. Mobile keeps the earlier approved
  `large`/`normal`/`small`/`tiny` mapping.
- Approved continuation affordance: use a three-row viewport with a bottom
  fade while more content remains. Remove the fade at the real bottom.
- The Connections disclosure is desktop-only. The full-screen mobile
  Connections list remains unchanged.
- Collapsing and reopening the desktop Connections panel returns its bounded
  list to the top; preserving scroll offset is not required.
- Typography tests must resolve expected metrics from
  `DISPLAY_TYPOGRAPHY_PRESETS` or the active themed preset. Native UI tests use
  relative rendered geometry and preset-derived thresholds, not copied point
  values.

#### Documentation

- 010 owns any shared-component documentation correction needed for rich
  session-action typography.
- 020 owns desktop documentation for session-card semantic roles and
  Connections-panel disclosure/bounded scrolling.
- 030 owns mobile documentation for session-card semantic roles and matching
  line heights.
- 040 owns the later Connections-screen gutter correction and its native
  alignment evidence.

#### Task checklist

- [x] Reopen and complete the shared rich-action follow-up in
  `tasks/20260827-cross-platform-markdown-and-mobile-connections/010-shared-markdown-display-contract.md`.
- [x] Reopen and complete the desktop session-card and Connections-panel
  follow-up in
  `tasks/20260827-cross-platform-markdown-and-mobile-connections/020-desktop-markdown-view-preferences.md`.
- [x] Reopen and complete the mobile session-card follow-up in
  `tasks/20260827-cross-platform-markdown-and-mobile-connections/030-mobile-global-settings-and-markdown.md`.
- [x] Reopen and complete the mobile Connections gutter follow-up in
  `tasks/20260827-cross-platform-markdown-and-mobile-connections/040-mobile-connection-actions-and-layout.md`
  without changing connection behavior.
- [x] Record focused verification and documentation in each owning reopened
  subtask.

#### Requirement verification

- Mobile component tests inspect title, subtitle, preview, session ID, and
  metadata styles under the default and largest presets and assert matching
  role-specific line heights.
- Shared component tests inspect rich list labels and textual fallbacks under
  a non-default theme and assert matching semantic metrics.
- Desktop style and component tests assert exact title, subtitle/preview,
  session ID, metadata, and Open-label metrics.
- Desktop connection component tests assert disclosure state and select a
  plain container for zero through three records versus a bounded
  `ScrollView` for more than three. They also assert that overflow controls the
  fade and reaching the bottom removes it.
- A production-component macOS XCTest harness runs one-, three-, and
  five-record scenarios. It verifies natural-height growth, absence of a
  scroll view for three or fewer records, a bounded viewport and actual row
  movement for five records, access to the last record, collapsed header-only
  geometry, and unclipped largest-preset geometry.
- The existing mobile native session-list scenario is extended to verify
  non-overlapping card field geometry at default and largest presets on iOS
  and Android using relative or preset-derived expectations.

#### Additional implementation verification

- Run the shared component suite and shared type check.
- Run complete mobile Jest and TypeScript checks plus the focused iOS and
  Android Detox session-list scenario.
- Run complete desktop Jest, the focused signed macOS XCTest, and a bundled
  macOS build.
- Report the known desktop full-TypeScript baseline separately and confirm
  that no touched follow-up file adds an error.

#### Implementation notes

- Completed the shared rich-action and mobile session-card follow-ups. Shared
  tests pass 42 cases; mobile passes 137 Jest tests and TypeScript.
- Fresh iOS and Android Detox builds and the focused session-list scenario
  pass on both platforms. Geometry assertions select the exported default or
  largest preset and compare relative bounds.
- Desktop session-card roles, disclosure, natural/scroll host split,
  theme-derived three-row cap, and bottom fade are implemented. Desktop Jest
  passes 120 tests.
- Removed stale copied typography tables from shared, mobile, and desktop
  tests. Consumer expectations now resolve from the maintained preset or
  markdown derivation.
- Added the production desktop Connections harness and focused XCTest. The
  macOS app and signed test bundle pass `build-for-testing`.
- After user confirmation, the focused desktop XCTest passed both tests with
  zero failures.
- A later mobile correction removed Connections' duplicate child-screen
  padding, added the visible Sessions title, and aligned Connections/Sessions
  titles, the Sessions search placeholder, and card titles to one optical left
  edge. Connections, Sessions, and Messages continue to share the outer gutter
  and compact top inset owned by `ConnectedRoot`.
- Complete mobile verification after the gutter correction passes 137 Jest
  tests and TypeScript. Fresh iOS/Android builds pass the two-test session-list
  Detox scenario and the Connections/Settings scenario on both platforms. The
  first Android Connections attempt was blocked before app readiness by an
  emulator `Activity.setTheme` ANR; a fresh-emulator retry passed.

#### Completion notes

- Completed the shared, desktop, mobile session-card, and mobile gutter
  follow-ups without creating another subtask.
- Desktop XCTest verified natural one-versus-three-record growth, no scroll
  view through three records, a theme-derived bounded five-record viewport,
  visible overflow fade, native scrolling, fade removal at the real bottom,
  final-row reachability, and collapse/expand behavior at the largest current
  preset.
- The first two desktop attempts exposed native-query assumptions and a stale
  LLDB-held app process. The final production test uses the actual native
  hierarchy, and the stale debugger session was removed before the clean
  successful run.
- Final planned evidence is complete across shared tests, mobile Jest and
  TypeScript, desktop Jest, fresh iOS/Android builds and Detox, bundled macOS
  build, and the focused signed macOS XCTest.

#### Post-completion verification follow-up

- The first full desktop Jest run after XCTest passed all 120 assertions but
  exited nonzero when an existing `DependencyFlatList` timer fired after Jest
  teardown. The focused owning suite then passed 4 tests, and a clean full
  retry passed all 23 suites and 120 tests with a successful exit.