# Mobile global Settings and markdown preferences

Introduce persistent application-wide display settings on mobile, apply the
shared base/header contract to both mobile markdown implementations, and add
the production Connections-header entry point.

## Requirements checklist

### Functional requirements

- [x] Mobile markdown keeps its current 15-point default body size.
- [x] Global Settings opens in the same modal frame used by existing settings
  and presents Base font size and Markdown headers dropdowns.
- [x] The Connections header replaces its standalone New Connection button
  with a pinnable action bar where Global Settings and New Connection are
  pinned by default.
- [x] Selecting an option updates every visible markdown message immediately
  and persists across application reconstruction.
- [x] Both enriched/selectable markdown and the legacy markdown fallback
  implement the shared `Normal` and `Small` size profiles.

### Non-functional requirements

- [x] One mobile preference owner hydrates and writes AsyncStorage without
  mixing persistence into message renderers or the Settings modal.
- [x] Startup hydration avoids replacing a valid stored preference with
  defaults or visibly rendering the wrong setting before hydration completes.
- [x] Existing selection, links, list/table/task-list rendering, code blocks,
  markdown/raw toggles, and transcript scrolling remain intact.
- [x] The Settings modal reuses `PanelModalFrame` and established option-picker
  behavior with stable accessibility labels and test IDs.
- [x] Connections-header pin state uses the existing persistent pinnable-action
  model and stable action keys.

Parent Task: `tasks/20260827-cross-platform-markdown-and-mobile-connections/000-main.md`

Depends On: `tasks/20260827-cross-platform-markdown-and-mobile-connections/010-shared-markdown-display-contract.md`

## Execution plan
Status: Approved

Add a mobile preference hook/provider adapter that reads one versioned
AsyncStorage record, normalizes it through the shared contract, and persists
changes. Integrate hydration with the existing application loading boundary
and place the shared provider high enough to cover Connections, Sessions,
Messages, and overlays.

Create `GlobalSettingsModal` using `PanelModalFrame`. Render two compact
setting rows whose controls open `OptionsPickerModal`: one for the supported
base point sizes and one for Normal/Small headers. Selection should close the
picker, update context immediately, and leave the parent Settings modal open.

Update `SelectableMarkdownMessageContent` and the legacy
`MarkdownMessageContent` to consume shared derived sizes. Apply body size and
line height consistently to paragraph, list, table, blockquote, and inline
code; apply explicit H1–H6 styles for both profiles. Keep dedicated fenced-code
font sizing and existing renderer-specific layout tuning.

Expose modal visibility/callbacks from the connected application shell so the
Connections screen can open Global Settings. Replace the current standalone
New Connection button with `ActionsMenuBar` in this subtask, using
`globalSettings` and `newConnection` actions with both pinned by default.
Leave the current active-connection panel and existing connection-card layout
unchanged until 040.

Add focused header-action, modal, persistence, and renderer tests; run the
mobile package checks affected by this work and update mobile development
documentation before marking 030 complete. This makes the complete production
preference workflow independently testable without 040.

### Implementation decisions and open questions

- Proposed storage is one versioned JSON record, for example
  `clc_markdown_display_preferences_v1`, rather than separate keys.
- Invalid or partially valid records are normalized field by field.
- Settings are application-global rather than connection- or session-scoped.
- Connections-header pins are global and versioned independently from
  per-connection-card pins introduced by 040.
- Supported sizes, heading baseline, and fenced-code scope use the approved
  parent-task decisions.

### Documentation

- Document mobile display preference hydration, ownership, modal composition,
  renderer consumption, Connections-header entry point, pin persistence, and
  primary tests in package development docs.
- User-facing README changes are not planned because this is an in-application
  control, not setup or first-use behavior.

### Task checklist

- [x] Add AsyncStorage hydration/persistence adapter.
- [x] Wire the shared preference provider into mobile startup.
- [x] Build the Global Settings modal and both option pickers.
- [x] Replace the Connections-header button with the pinnable Settings/New
  Connection action bar.
- [x] Update enriched/selectable markdown styles.
- [x] Update legacy markdown fallback styles.
- [x] Add header-action, persistence, modal, and renderer tests.
- [x] Run relevant mobile package tests, TypeScript checking, and lint.
- [x] Update and index mobile development documentation for this work.
- [x] Record mobile verification evidence.

### Requirement verification

- Persistence tests cover no record, a complete valid record, partial/invalid
  records, updates, and reconstruction.
- Modal tests assert the established frame, current values, selectable options,
  immediate context updates, and accessibility/test identifiers.
- Connections-header tests assert default pins, pin updates/persistence,
  Global Settings routing, and unchanged New Connection routing.
- Renderer tests assert exact body/heading styles for every supported
  combination in both renderer implementations.
- A human compares representative content on iOS and Android and confirms no
  clipping or unusable transcript behavior at the largest size.

### Additional implementation verification

- Run focused mobile Jest tests and the full mobile Jest suite.
- Run `npm --workspace` or package-local mobile TypeScript checking and lint.
- Run existing ordered-list/selectable-code-block tests affected by markdown
  style changes.
- Run relevant transcript component and native UI regression slices.

## Implementation Notes

- Moved the Connections-header action bar into this subtask so the production
  Settings workflow is independently reachable before card redesign.
- Preference hydration participates in the existing application loading
  boundary, preventing a stored value from flashing as the default.

## Completion Notes

- Added persistent mobile preference ownership, the standard-frame Global
  Settings modal, both option pickers, and the pinned Settings/New Connection
  header actions.
- Updated enriched and legacy markdown renderers to consume shared semantic
  sizes while preserving dedicated fenced-code sizing.
- Mobile TypeScript passed. The full mobile Jest suite passed: 30 suites and
  124 tests, including persistence, modal, header routing, and renderer tests.
- Mobile lint could not run because the package has no ESLint configuration.
- Added and indexed mobile development documentation.
- Native visual checks on iOS and Android remain human checkpoints.

## Post-completion follow-up

- [x] Add a production-component Detox harness for Global Settings,
  preference persistence, and representative markdown geometry.
- [x] Pass the focused scenario on iOS.
- [x] Pass the focused scenario on Android.

Follow-up evidence:

- The first iOS run exposed that a nested native option-picker modal was not
  presented over Global Settings. The picker now renders as an overlay inside
  the established modal.
- The final production-component scenario passed on iPhone 17 Pro and
  Medium Phone API 36.1, including persisted 19/Small values and
  screenshot-derived rendered glyph geometry.