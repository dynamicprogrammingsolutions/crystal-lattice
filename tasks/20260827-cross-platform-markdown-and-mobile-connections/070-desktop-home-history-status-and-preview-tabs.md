# Desktop Home, activity panels, request status, and preview tabs

Extend the desktop application with a fixed Home workspace, a VS Code-like
activity rail and History panel, request-status presentation, draggable
session tabs, and one transient italic preview tab. Add a native macOS
Settings entry that opens desktop global settings in a separate window.

## Requirements checklist

### Functional requirements

- [x] The desktop tab strip always starts with a fixed Home tab represented
  only by a Home icon; it has an accessible Home label, cannot be closed or
  reordered, and selecting it displays Home in the main workspace.
- [x] Desktop Home presents an ordered, device-local Watchlist and a
  cross-connection session-history collection resolved from saved connections
  and cached session summaries.
- [x] Desktop Home, History, and Sessions expose one permanent desktop-local
  note per session ID. Equal session IDs intentionally share the note across
  connections, and removing Watchlist membership or a saved connection does
  not remove the note.
- [x] Watchlist membership and order remain independent from server-side
  session pinning, survive application reconstruction, and can be reordered
  with live destination preview plus deterministic accessible alternatives.
- [x] Selecting a Home, Sessions-panel, or History-panel session targets its
  exact `(connectionId, sessionId)` identity, opens a closed connection when
  needed, and cannot navigate from a stale superseded open attempt.
- [x] The macOS application menu's currently inactive Preferences/Settings
  item becomes `Settings…`, retains the standard Command-comma shortcut, and
  opens or raises one separate Settings window.
- [x] The Settings window exposes desktop-global font size, Markdown Headers,
  Recent Sessions scope, and session double-click action controls; changes
  apply immediately, remain synchronized with existing View-menu controls,
  reach every open main window, and persist across relaunch.
- [x] The desktop left side gains a narrow three-icon activity rail beside
  the content panel.
- [x] The Connections icon is placed at the top of the activity rail and
  independently shows or hides the Connections section.
- [x] Sessions and History icons are placed at the bottom of the activity
  rail and switch the lower panel between the existing Sessions panel and a
  new History panel.
- [x] The History panel presents the same cross-connection history collection
  and modified-descending `24h`, `3d`, or `1w` scope as Home in a compact
  side-panel treatment, without depending on the currently focused connection.
- [x] Derived request status appears on Home Watchlist/history entries, in the
  History panel, on rows in the existing Sessions panel, in every session tab,
  and in the Chat pane header beside the Online/Offline indicator.
- [x] Request status remains distinguishable without color alone. Home and
  panel surfaces show a text label; tab dots have an accessibility label/value;
  the Chat pane shows a colored dot with its status label.
- [x] The existing provisional states retain their current meanings:
  `Idle`, `Not started`, `In progress`, `Completed`, and `Interrupted`.
- [x] Permanent session tabs can be reordered with pointer dragging. During
  drag, surrounding tabs and a same-sized destination placeholder show the
  prospective order, and release keeps the settled order visible until the
  persisted order is authoritative.
- [x] A normal single-click on a Home, Sessions, or History item only selects
  the item and performs no connection or Chat-pane work.
- [x] A global `Double-click action` setting offers `Preview` and `Open`,
  defaults to `Preview`, and applies consistently to Home, Sessions, and
  History session items.
- [x] Every Home, Sessions, and History item shows the action complementary to
  the configured double-click action as an explicit button: `Open` when
  double-click previews and `Preview` when double-click opens permanently.
- [x] The Sessions-row Preview/Open button is rendered to the left of and
  vertically aligned with the pinnable session actions rather than offset
  beside them.
- [x] Previewing uses at most one italic preview tab placed after all
  permanent tabs. Previewing another non-permanent session replaces that slot
  rather than accumulating preview tabs.
- [x] Selecting a session that already has a permanent tab activates that tab
  and does not create a preview duplicate.
- [x] Double-clicking the preview tab promotes it to a normal permanent tab at
  the end of the permanent-tab order without remounting the active Chat pane.
- [x] Starting a request or another session mutation from the preview promotes
  it before the mutation begins.
- [x] Permanent tab order, preview identity, and active Home/permanent/preview
  workspace are restored after relaunch. The fixed Home tab is implicit and
  the preview remains uniquely classified rather than becoming an ordinary
  permanent tab.
- [x] A preview behaves like a normal selectable/closable session tab and
  remains shown until it is explicitly closed, promoted, or replaced by a
  different requested preview.
- [x] Selecting or opening any session tab attempts to reopen its owning
  connection when it is not open, while cached session and message content
  remains visible.
- [x] Startup performs the same reopen attempt for the restored active
  permanent or preview tab; startup does not require the user to reselect it.
- [x] Closing the active preview or permanent tab selects a deterministic
  neighboring permanent tab or Home, while closing an inactive tab does not
  change the active workspace.

### Non-functional requirements

- [x] Shared React Native ownership is introduced only for genuinely portable
  Home models/selectors, status presentation, and reorder geometry or content
  primitives. macOS activity-rail behavior, pointer/responder handling,
  native windows, and tab lifecycle remain desktop-owned.
- [x] Mobile continues to use its existing Home navigation and visual layout;
  extracting shared code does not change mobile Watchlist, Recent Sessions,
  notes, drag, status, or connection-opening behavior.
- [x] One pure, immutable desktop workspace reducer/model owns permanent-tab
  order, preview identity, active Home/session workspace, promotion, close,
  replacement, and reorder transitions.
- [x] The persisted tab format has a versioned migration from the existing
  all-permanent open-tabs record. Existing restored tabs remain permanent and
  keep their saved order and presentation.
- [x] Preview/permanent transitions retain stable composite tab identity and
  preserve the existing bounded warm Chat-pane stack, message cache, scroll
  anchors, drafts, range selection, and active request UI.
- [x] One desktop request-status controller unions only the explicit session
  IDs currently consumed by Home, visible side-panel rows, tabs, and the active
  Chat pane; it batches by connection, cancels stale work, polls only while
  needed, and never opens, focuses, repairs, or touches a connection.
- [x] Open connections use their existing backend for status reads. Supported
  closed records use one stateless HTTP read; unsupported records degrade
  quietly without stale `In progress` presentation.
- [x] Status vocabulary and visual tone mapping have one shared source and
  remain replaceable by the future durable request-operation/attention model.
- [x] Settings use native persisted authority and notifications rather than an
  unrelated JavaScript preference store, so View-menu check state, the
  Settings window, existing main windows, and newly created main windows
  converge.
- [x] Double-click interpretation is centralized and driven by the persisted
  global setting; individual Home, Sessions, and History surfaces do not
  duplicate timing or complementary-action rules.
- [x] Nested close/menu controls and ordinary horizontal tab-strip scrolling
  do not accidentally start a drag; tab dragging has a deliberate pointer
  threshold and supports edge auto-scroll for overflowed strips.
- [x] Every new entity and interaction has stable production accessibility
  identifiers suitable for component and macOS XCUITest verification.
- [x] Component/native geometry tests derive expected dimensions and status
  colors from the active theme or rendered layout and do not duplicate
  typography preset values.
- [x] The existing explicit-ID request-status API remains unchanged; this
  subtask introduces no durable request history, backend status vocabulary,
  connection-lifecycle expansion, login, or notification-attention behavior.

Parent Task:
`tasks/20260827-cross-platform-markdown-and-mobile-connections/000-main.md`

Depends On:

- `tasks/20260827-cross-platform-markdown-and-mobile-connections/020-desktop-markdown-view-preferences.md`
- `tasks/20260827-cross-platform-markdown-and-mobile-connections/060-mobile-home-watchlist-and-request-status.md`

## Scope

This subtask owns desktop Home and local Watchlist hosting, desktop session
history, desktop global Settings presentation, the activity rail and lower
panel switcher, desktop request-status consumption, and the session-tab
preview/reorder model.

It may extract portable state, geometry, and presentation from the completed
mobile Home implementation into the shared React Native package. Such
extraction must preserve the public behavior and persisted mobile data already
delivered by subtask 060.

This subtask consumes the existing explicit-ID derived-status endpoint and
frontend SDK types. It does not implement durable operation state, global
attention, multi-runtime mobile ownership, login, Quick Question, or a new
server status.

## Resolved requirement decisions

1. Desktop includes permanent local notes with the same session-ID-only
   identity semantics as mobile. Desktop storage remains independent from
   mobile and server data.
2. Desktop Home and History use the same bounded `24h`, `3d`, and `1w`
   modified-descending Recent Sessions collection as mobile.
3. A preview promotes before a request or other session mutation starts, as
   well as through explicit tab double-click.
4. Single-click remains selection-only. The global double-click action is
   `Preview` by default or `Open`; every session item exposes the other action
   as its button.
5. Startup restores the active workspace, including an active preview. The
   preview identity is persisted and remains visible like a normal tab unless
   closed, promoted, or replaced by a later preview request.
6. Selecting, opening, or restoring a session tab attempts to reopen its
   owning connection. Reopen is asynchronous and does not hide cached content.

## Supporting findings

- `DesktopRoot` currently owns one array of session tabs, persists every tab
  as permanent under `clc_open_tabs_v1`, and keeps the three most recently used
  Chat panes warm.
- The Sessions panel currently selects a row on single click and opens a tab
  through a rapid second click or the explicit Open control. There is no
  preview-tab state.
- `SessionTabs` is a horizontally scrollable strip but has no reorder model,
  pointer drag, Home item, request status, or tab-specific accessibility
  identifiers.
- `DesktopShell` currently reserves one fixed 340-point left column. That
  column stacks Connections and Sessions, which maps naturally to an
  independent Connections toggle plus a mutually exclusive Sessions/History
  lower panel.
- Desktop already caches session summaries by connection, persists multiple
  open backends, and can resolve cross-connection Home/history items without a
  new server listing API.
- The provisional status endpoint, normalized SDK projection, and
  `ConnectionSessionStatusReader` interface already exist. The polling hook
  and status badge are mobile-local and are candidates for portable
  extraction.
- Mobile Home's selectors and drag geometry are currently application-local.
  The pure collection/order/geometry layers can move without sharing the
  mobile PanResponder or full-screen layout.
- The macOS storyboard already contains a Command-comma `Preferences…` item
  with no action. `DesktopWindowManager.openReactWindow` already provides
  keyed single-instance React windows used by Server and Session Settings.
- Desktop display preferences are already authoritative in
  `NSUserDefaults`, propagate through native notifications, update all
  observing React roots, and seed newly created main windows. The Settings
  window should extend that route.
- `ChatPane` already renders an Online/Offline dot and label in its header.
  `SessionsPanel`, `SessionTabs`, and `ChatPaneTabStack` have direct seams for
  receiving one connection/session-scoped status projection.
- React Native macOS does not provide the same touch semantics as mobile.
  Shared reorder geometry is viable, but mouse capture, double-click
  recognition, horizontal strip auto-scroll, and nested control exclusion
  require desktop adapters and native verification.

## Execution plan
Status: Approved

### 1. Establish portable Home and status boundaries

Move or recreate the following portable pieces in the smallest appropriate
shared package:

- Watchlist identity, normalization, immutable movement, recent-history
  cutoff, and cached-summary collection derivation;
- measured-slot reorder and destination-placeholder geometry;
- request-status labels and semantic tone mapping;
- visual content primitives for a Watchlist item and compact history item
  where mobile and desktop can consume the same accessibility/content
  contract without sharing interaction hosts.

Keep persistence adapters and screen composition platform-owned. Mobile keeps
its existing storage keys and provider behavior. Desktop receives its own
versioned local Watchlist namespace. Share note normalization and its bounded
model while retaining platform-local storage.

Extract the polling state machine into a host-neutral React hook/controller
with an explicit `active` input rather than embedding mobile AppState policy.
Mobile supplies its current foreground state; desktop supplies main-window
activity. Keep connection-kind transport creation in platform readers unless
inspection identifies a safe SDK-level helper with no product-policy leakage.

### 2. Add native desktop global Settings authority and window

Enable and rename the existing application-menu item to `Settings…`, bind it
to a native action, and route that action to a keyed
`GlobalSettingsWindow` React root. Reuse the existing auxiliary-window
manager so repeated invocation raises the same window.

Extend the native preference module with typed read/write methods and
notifications for the approved history scope. The Settings window reads
authoritative native values and writes only through that bridge. Font-size and
Markdown-header changes continue to update existing View-menu check state,
all main windows, and new-window initial props. Add the history selector to
the Settings window; keep it out of the markdown-only shared preference
contract.

### 3. Introduce desktop Home workspace state and navigation authority

Add a desktop Home state owner above the shell. It hydrates Watchlist order
and permanent notes without startup overwrite, resolves entries against
`sessionsCache`, and derives one cross-connection `24h`/`3d`/`1w` history
collection.

Implement one current-intent session navigation command. It focuses/reuses an
already open connection or opens the exact saved record, refreshes its session
cache when possible, and opens the intended composite session only while that
intent remains current. Status polling must not call this command.

Render Home as main-workspace content selected by the fixed first tab.
Desktop Home uses the shared item content and status primitives but owns a
desktop responsive grid/list, hover/actions, pointer drag host, and window
spacing. Do not copy mobile's bottom navigation or mobile header menu.

### 4. Replace the left shell with an activity rail and switchable panels

Refactor `DesktopShell` into an activity rail, optional panel content, and main
workspace. The Connections icon independently toggles the existing
Connections section. Sessions and History are a mutually exclusive lower
panel selector. Initial state is Connections shown and Sessions selected.

The History panel consumes the same derived collection, note data,
status map, and session navigation command as Home, but uses a compact
single-column panel design. It does not change `focusedConnectionId` merely to
render cross-connection entries; opening an entry focuses the owning
connection as part of explicit navigation.

Keep panel selection and Connections visibility local to each main window for
the first implementation. This is a reversible presentation decision and
avoids adding native global settings that were not requested.

### 5. Add one desktop request-status controller

Create a desktop reader that prefers each open connection's existing backend
and otherwise performs the supported stateless explicit-ID HTTP request.
Unsupported records return quiet unavailable state. Use one controller above
Home/panels/tabs to union registered visible identities and batch one request
per connection.

Pass normalized status projections to:

- shared Home Watchlist and history items;
- compact History rows;
- Sessions rows for the focused connection;
- permanent and preview tabs;
- the active Chat pane through `ChatPaneTabStack`.

Use shared semantic tones: running uses primary, succeeded uses success,
interrupted uses warning, and idle/not-started use distinguishable neutral
presentation. Tabs render a dot plus semantic accessibility value. Chat adds
request status immediately after Online/Offline without conflating connection
and request state.

### 6. Replace the tab array with permanent/preview workspace state

Introduce a pure workspace reducer with:

- ordered permanent session tabs;
- at most one preview session;
- active workspace `home` or a composite session tab;
- commands for preview open/replace, permanent open, promote, select, close,
  update presentation, reconcile connections, and reorder.

Migrate persisted v1 tabs to a v2 record containing permanent order, optional
preview identity, and active Home/session workspace. Preserve tab identity
while promoting so `ChatPaneTabStack` does not remount the Chat pane. On every
session-tab selection and after hydration of an active session tab, request a
reopen of its owning connection without blocking cached presentation.

Centralize session-item click interpretation. Single click updates only local
selection. A same-item second click inside the tested double-click threshold
runs the global configured action. The explicit button runs the complementary
action and is positioned before the Sessions row's pinnable actions. New
session creation and actions that semantically require a durable workspace
continue to open permanent tabs.

Render Home first, permanent tabs next, and the optional italic preview last.
Double-clicking preview dispatches promotion. Existing permanent and preview
tabs select normally and trigger a connection reopen when needed. Closing and
connection deletion use reducer transitions rather than updating tab and
active state independently.

### 7. Add live draggable permanent tabs

Adapt the measured-slot drag model used by mobile Watchlist:

- capture only after a deliberate pointer movement threshold;
- snapshot measured permanent-tab frames;
- resolve target continuously and render a same-sized placeholder;
- keep the responder-owning tab stable while showing an elevated overlay;
- edge-scroll the horizontal strip when needed;
- on release, snap the overlay into the placeholder and retain that settled
  preview until reducer/persistence state reports the target order.

Home remains fixed. Preview remains fixed at the far right and is not
draggable until promoted. Close/menu controls stop propagation and do not arm
drag. Provide Move Left/Move Right accessibility actions as a deterministic
alternative.

### 8. Verify public behavior and document ownership

Add pure shared tests for collection/status/reorder contracts and pure desktop
tests for every reducer transition and v1 migration. Add desktop component
coverage for Home, activity-rail state, History navigation, status in all
requested consumers, Settings synchronization, preview replacement/promotion,
close selection, drag placeholder, and settled-order optimism.

Add a deterministic production-component macOS harness and focused XCUITest
coverage for:

- the Home icon and main workspace;
- all three activity icons and Connections/Sessions/History composition;
- opening the separate Settings window from Command-comma and changing a
  setting;
- one italic preview, replacement, double-click promotion, and fixed ordering;
- real horizontal tab drag with placeholder/final geometry;
- status label/dot presence and accessibility without copied theme values.

Use existing frontend SDK real-backend status coverage for the endpoint
boundary. Add a desktop integration only where needed to prove the production
reader and screen adapter use the real public backend method.

### Risks and mitigations

- **Double-click ambiguity:** React Native macOS has no established
  `onDoubleClick` use in this app. Keep immediate single-click preview behavior
  and recognize a second same-target click within a tested threshold for
  promotion.
- **Preview replacement during work:** replacing a preview that owns a draft
  or active request can hide important state. Promote before mutation and test
  that rule at the Chat-pane boundary.
- **Drag versus scroll/controls:** horizontal scrolling and nested close/menu
  controls can conflict with tab drag. Use movement thresholds, explicit
  responder ownership, stable keyed children, and native mouse tests.
- **Cross-window settings:** a separate React root cannot own authoritative
  preferences independently. Native read/write/notification authority keeps
  every root and menu synchronized.
- **Polling growth:** Home plus History plus tabs can request many IDs. Register
  only mounted/visible consumers, deduplicate by connection, respect endpoint
  bounds, and page visible history rather than issuing all cached IDs.
- **Shared-package regression:** desktop and mobile use adjacent but different
  React Native versions. Share pure contracts and content primitives, retain
  platform interaction adapters, and run both owning suites after extraction.
- **Existing tab/cache complexity:** changing tab identity can remount panes
  and lose drafts/scroll state. Promotion changes classification in place and
  warm-stack tests assert stable keys and cache continuity.

### Implementation decisions and open questions

- **Decision:** Home is a fixed, non-closable, non-draggable icon-only tab at
  the left edge. It is not stored in the session-tab record.
- **Decision:** the activity rail implements the user's asymmetric model:
  Connections is an independent top toggle; Sessions and History are a
  mutually exclusive bottom selection.
- **Decision:** Connections is visible and Sessions is selected for a newly
  created main window. Activity-rail selection is initially window-local and
  non-persistent.
- **Decision:** one preview slot follows all permanent tabs and uses italic
  title text plus an accessibility `Preview` description. It is not
  draggable; promotion makes it draggable as a permanent tab.
- **Decision:** permanent order, optional preview identity, and active
  workspace are persisted. Existing v1 tabs migrate as permanent.
- **Decision:** single click selects only. Double-click uses the global
  Preview/Open setting and the row/tile button always exposes the complement.
- **Decision:** the default is double-click Preview plus an explicit Open
  button.
- **Decision:** every session-tab selection and restored active session
  requests connection reopen while preserving cached presentation.
- **Decision:** Home/History are desktop presentations backed by shared
  collection and content contracts, not a direct copy of the mobile screen.
- **Decision:** request status augments but never replaces Online/Offline,
  session workflow status, cache freshness, or loading state.
- **Decision:** the current explicit-ID endpoint and five provisional states
  are sufficient; no server implementation change is planned.
- **Decision:** no standalone specification is proposed. This task plus
  current desktop/shared package documentation is proportional unless
  implementation exposes a new cross-package contract that cannot be
  documented in the owning package.
- **Decision:** all requirement questions are resolved and execution is
  approved.

### Documentation

- Add desktop user documentation under the desktop package for Home,
  Watchlist, History, request-status meaning, activity panels, preview versus
  permanent tabs, tab reordering, and Settings.
- Add desktop development documentation for Home/workspace ownership, local
  persistence, status registration/polling, activity-rail composition, the
  tab reducer/persistence migration, and native test entry points.
- Update desktop window conventions for the global Settings window and update
  frontend hosting for the single status controller.
- Update shared React Native development documentation for each extracted
  Home/status/reorder component or contract.
- Update mobile development documentation only where ownership paths move;
  user-visible mobile documentation should remain behaviorally unchanged.
- Do not duplicate the server status derivation documentation or describe the
  provisional projection as durable request history.
- Do not edit generated documentation-site outputs directly.

### Task checklist

- [x] Resolve the requirement questions and update the approved requirements
  and plan.
- [x] Extract and verify portable Home, status, and reorder boundaries.
- [x] Add desktop Home persistence, collection derivation, presentation, and
  exact cross-connection navigation.
- [x] Enable the native Settings menu item and implement the separate global
  Settings window with synchronized authority.
- [x] Implement the three-icon activity rail and Connections/Sessions/History
  panel composition.
- [x] Implement the desktop stateless status reader and single polling
  controller.
- [x] Add request status to Home, History, Sessions, tabs, and Chat.
- [x] Introduce the permanent/preview/Home workspace reducer and migrate
  persisted open tabs.
- [x] Implement preview replacement, promotion, deterministic close behavior,
  and any approved auto-promotion rules.
- [x] Implement measured live permanent-tab reordering and accessible move
  alternatives.
- [x] Add shared, desktop unit/component, real-backend, and macOS native
  verification.
- [x] Update owning desktop, shared, and affected mobile documentation.
- [x] Record implementation and completion evidence without modifying
  completed requirements before evidence exists.

### Requirement verification

- Home/Watchlist tests prove fixed icon placement, non-close/non-drag behavior,
  local persistence, exact cross-connection identity, reorder settlement, and
  closed-connection current-intent navigation.
- Settings tests prove Command-comma opens/raises one native window, each
  setting round-trips through native authority, View-menu check state follows,
  existing roots update, and new roots seed current values.
- Activity-panel tests prove exactly three icons, independent Connections
  visibility, mutually exclusive Sessions/History selection, and the expected
  initial composition.
- History tests prove Home/panel collection equivalence, approved range and
  ordering, cross-connection presentation, and compact panel navigation.
- Status tests prove per-connection deduplication/batching, open-backend and
  closed-stateless reads, cancellation/backoff, stale-running suppression, and
  label/dot rendering at every requested surface.
- Workspace reducer tests prove one preview, replacement, permanent
  deduplication, promotion at the permanent tail, v1 migration, persistence,
  close-neighbor behavior, connection deletion, active-preview restoration,
  and mutation/startup reopen semantics.
- Session-item interaction tests prove selection-only single click, both
  double-click setting values, the complementary button label/action, and
  left-aligned vertical button/action-bar geometry.
- Tab-drag tests prove threshold/control separation, measured target
  resolution, live placeholder order, edge scrolling, fixed Home/preview
  positions, one final persisted move, and no source-order flash during
  release handoff.
- Chat-stack tests prove preview promotion preserves stable keys, active
  request/draft/cache state, scroll anchors, and the existing bounded warm-pane
  behavior.
- Native tests exercise actual macOS menu/window, mouse click/double-click,
  pointer drag/scroll geometry, activity icons, and accessible status values
  through production components.

### Additional implementation verification

- Run `npm --workspace @crystal-lattice/frontend-rn-components test` and any
  affected shared type check.
- Run the frontend SDK and SDK React focused status tests plus the existing
  real-backend session-status integration when shared status ownership moves.
- Run complete mobile Jest and TypeScript checks after shared extraction.
- Run complete desktop Jest, desktop integration tests, lint, and TypeScript;
  report known baseline errors separately and confirm touched files add none.
- Build the bundled macOS app and XCUITest target, then run the focused new
  desktop Home/panels/tabs/Settings/status XCUITest class after macOS
  automation is available.
- Re-run focused desktop Chat-pane/tab-stack, Sessions-panel, connection,
  transcript persistence, and scroll tests because workspace identity and
  typography-aware geometry are affected.
- Run `git diff --check` and relevant documentation preparation/build checks.

## Implementation Notes

- Portable Watchlist/recent/note normalization, request-status presentation,
  and measured reorder geometry now live in
  `@crystal-lattice/frontend-rn-components`. Mobile consumes those exports
  through its existing local module names, retaining its storage keys and
  behavior.
- Host-neutral explicit-ID polling moved to
  `@crystal-lattice/frontend-sdk-react`. Mobile supplies AppState foreground
  policy; desktop supplies main-root activity and one desktop reader.
- Desktop open-tab persistence migrated in place from version 1 to version 2.
  Version 1 entries restore as permanent. Version 2 stores permanent order,
  optional preview identity, and active Home/session workspace.
- A session row/tile first click only updates selection. A same-identity second
  click dispatches the native global Preview/Open preference, and the explicit
  button dispatches its complement. The Sessions button is before and
  vertically centered with the pinnable action bar.
- The active restored permanent or preview session triggers the same
  idempotent connection reopen path as later tab selection. Cached content
  remains mounted while reopening.
- Permanent tab and Watchlist drag hosts retain stable responder children,
  render measured placeholders, snap overlays to the settled target, and wait
  for authoritative order before clearing.
- Shared React Native tests pass 49 cases; SDK React tests pass 20; desktop
  Jest passes 30 suites and 136 tests; mobile Jest passes 40 suites and 162
  tests; mobile TypeScript and targeted desktop lint pass. Desktop TypeScript
  reports only the existing SDK URL, ChatPane optional-string, and Theme
  `shadow` baselines, with no new-file error.
- The signed macOS app and XCUITest bundle completed `build-for-testing`.
  A final forced-bundle refresh after the accessibility and foreground-polling
  refinements also completed with `TEST BUILD SUCCEEDED`.
  Two initial execution attempts were blocked before test start by the host
  automation gate. After the user enabled automation, native execution exposed
  React Native macOS element-type assumptions and the fact that PanResponder
  does not receive AppKit mouse-pan movement. XCTest now queries stable
  identifiers across element types, and `MacDragView` adapts
  `NSPanGestureRecognizer` movement to the shared reorder hosts.
- The final focused macOS suite passes all three tests. Native evidence covers
  the separate Settings window, request-status accessibility, preview
  promotion, Home activation, panel switching, Connections visibility,
  Watchlist mouse reorder, permanent-tab mouse reorder, and authoritative
  final ordering.
- Shared RN and SDK React type checks, mobile TypeScript, targeted desktop
  lint with warnings only, Prettier checks, frontend SDK status tests,
  `git diff --check`, and documentation preparation pass.

## Completion Notes

- Delivered desktop Home as a fixed icon-only tab with a local two-column
  Watchlist, bounded Recent Sessions history, session-ID notes, request
  statuses, and exact cross-connection session opening.
- Delivered the three-icon activity rail with an independent Connections
  toggle and mutually exclusive Sessions/History lower panels.
- Delivered native global Settings in a separate keyed window with font size,
  Markdown Headers, Recent Sessions range, and Preview/Open double-click
  preferences synchronized through `NSUserDefaults` notifications.
- Delivered version-2 workspace persistence for permanent order, one italic
  preview, and active Home/session identity, including version-1 migration,
  preview promotion before mutation, and connection reopen on selection and
  startup restoration.
- Delivered shared portable Home/status/reorder contracts and host-neutral
  status polling without changing mobile behavior or the explicit-ID server
  endpoint.
- Delivered real macOS mouse reordering through a native pan-gesture adapter;
  measured placeholder geometry, settled overlay handoff, persistence, and
  accessible Move Left/Right or Move Earlier/Later alternatives remain in
  React/shared code.
- Verification passed:
  - desktop Jest: 30 suites, 136 tests;
  - mobile Jest: 40 suites, 162 tests;
  - shared RN: 49 tests;
  - SDK React: 20 tests;
  - focused frontend SDK status: 7 tests;
  - mobile, shared RN, and SDK React TypeScript;
  - targeted desktop lint with warnings only and no errors;
  - Prettier, `git diff --check`, and documentation preparation;
  - signed macOS build and focused XCUITest: 3 tests, zero failures.
- Desktop full TypeScript remains non-clean only in the pre-existing SDK URL,
  ChatPane optional-string, and Theme `shadow` baselines. No new task file is
  reported.
- No durable operation history, new backend status, login, Quick Question, or
  mobile navigation change was added. No task scope remains unresolved.