# Desktop markdown View preferences

Increase desktop markdown to the mobile default and add persistent macOS View
menu controls for base size and header profile.

## Requirements checklist

### Functional requirements

- [x] Desktop markdown prose defaults to 15 points.
- [x] The macOS View menu contains radio-style Markdown Font Size and Markdown
  Headers submenus with checked current values.
- [x] Selecting a menu value updates visible markdown immediately and persists
  for future launches and newly opened main windows.
- [x] Desktop `Normal` and `Small` headings match the shared cross-platform
  size contract.

### Non-functional requirements

- [x] Native persistence and change propagation extend the established
  AppDelegate/notification/`DesktopWindowManager`/initial-props route.
- [x] All open desktop windows converge on a changed preference, and later
  windows start with current persisted values.
- [x] Renderer styles derive from the shared preference hook and do not
  duplicate option parsing or heading-scale logic.
- [x] Markdown error fallback and existing syntax-highlighted code behavior
  remain functional.

Parent Task: `tasks/20260827-cross-platform-markdown-and-mobile-connections/000-main.md`

Depends On: `tasks/20260827-cross-platform-markdown-and-mobile-connections/010-shared-markdown-display-contract.md`

## Execution plan
Status: Approved

Add validated `NSUserDefaults` keys and menu items for base size and header
profile. Build both View submenus with explicit check-state updates. Include
the current values in initial props at first launch and in
`mainWindowInitialProps`, then post named notifications when a selection
changes.

Extend `DesktopMenuNotifications`, `DesktopWindowManager` supported events,
and the TypeScript native-event surface. `DesktopRoot` owns current values,
subscribes to both events, and supplies them to the shared preference provider.
Keep native validation and TypeScript normalization so corrupt defaults cannot
escape as unsupported values.

Replace the desktop markdown component's hardcoded 13-point body/inline-code
styles and single heading style with memoized styles built from the shared
body/heading size result. Preserve colors, margins, weighting, blockquote/list
layout, code-block rendering, and the error boundary.

Add focused renderer tests and native menu coverage. Include a native check
that menu selection persists/checks correctly and reaches React state; use
unit style assertions for exact font sizes. Run desktop package and native
checks and update desktop development documentation in this subtask before it
is marked complete.

### Implementation decisions and open questions

- Menu labels are `Markdown Font Size` with `13`, `15 (Default)`,
  `17`, `19`, and `Markdown Headers` with `Normal`, `Small`.
- Desktop native values use numeric point sizes and stable lowercase profile
  strings at the bridge boundary.
- Native notifications should update every observing React root, not only the
  key window.
- Existing dedicated fenced-code sizing remains unchanged under the proposed
  preference scope.

### Documentation

- Document current View-menu ownership, persistence, multi-window event flow,
  renderer consumption, and focused verification under the desktop
  development docs.
- Link any new page from
  `desktop/crystal-lattice-control-desktop-rn/docs/development/index.md`.

### Task checklist

- [x] Add native constants, validation, persistence, and initial props.
- [x] Add both View submenus and check-state updates.
- [x] Add native notifications and bridge events.
- [x] Add desktop root preference state/provider wiring.
- [x] Update desktop markdown body and heading styles.
- [x] Add renderer and native-menu regression coverage.
- [x] Update desktop development documentation.
- [x] Record build/test/manual evidence.

### Requirement verification

- Renderer tests assert default 15-point prose and exact styles for all
  supported preference combinations.
- Native/menu tests assert submenu presence, selection check state, persisted
  relaunch/new-window initial props, and change-event delivery.
- A human compares representative markdown at both header profiles and at
  least the default/smallest/largest base sizes on macOS.

### Additional implementation verification

- Run focused desktop Jest tests and the full desktop Jest suite.
- Run desktop lint.
- Run a focused macOS XCUITest or macOS build that compiles the Objective-C++
  bridge and exercises the View menu.
- Re-run relevant desktop transcript tests because line-height changes alter
  row geometry.

## Implementation Notes

- Extended the existing native preference/notification bridge rather than
  adding JavaScript-side desktop persistence.
- The desktop TypeScript command remains blocked by pre-existing SDK URL,
  ChatPane, and Theme errors; it reported no errors in the changed files.

## Completion Notes

- Added persistent radio-style View submenus, initial/new-window properties,
  cross-window events, shared provider state, and explicit desktop renderer
  mappings.
- Desktop Jest passed: 21 suites and 110 tests. The focused typography suite
  passed 5 tests.
- The unsigned macOS Debug build succeeded.
- The focused XCUITest compiled, but execution was blocked when the host timed
  out enabling macOS automation mode. Visual/menu interaction remains a human
  checkpoint.
- Added and indexed desktop development documentation.

## Post-completion follow-up

- [x] Add a production markdown geometry harness and XCTest assertions for
  Normal versus Small headings and 13 versus 19-point body height.
- [x] Run the updated XCTest only after the user confirms macOS automation is
  enabled.

Follow-up evidence:

- Added a production markdown geometry harness and assertions for Normal versus
  Small H1/H6 geometry and 13 versus 19-point body height.
- `xcodebuild ... build-for-testing` succeeded, compiling the application,
  harness, and XCTest source without launching XCTest or UI automation.
- Desktop TypeScript reports only the previously recorded SDK URL, ChatPane,
  and Theme baseline errors; the new geometry harness has no remaining type
  error.
- After desktop automation was enabled, the focused
  `MarkdownDisplayMenuUITests` class passed both tests with zero failures.
  Native persistence was verified across termination/relaunch, and
  production-derived React layout measurements verified Normal versus Small
  headings plus 13 versus 19-point body height.
- React Native macOS accessibility descendants were unavailable to XCTest, so
  geometry evidence uses the repository's established harness-state boundary:
  production `onLayout` measurements are serialized through
  `DesktopWindowManager` and polled by XCTest.

### Completed desktop semantic typography and code follow-up

- Desktop session cards, connection rows, tabs, the chat header, and related
  chrome were migrated to semantic theme typography and colors.
- Desktop non-markdown messages use the semantic `message` size and line
  height.
- Fenced code blocks use Menlo plus the semantic `code` size and line height.
- Desktop consumes
  `ferenci84/react-native-syntax-highlighter#feature/native-line-height`
  through a direct Git dependency. Fork commit
  `4602848d2271b4809257be81ae0308f562c99910` supplies native line-height
  handling.
- Focused desktop typography tests cover chrome, non-markdown messages, and
  code rendering. Expected semantic metrics come from the active theme rather
  than copied preset numbers.

### Session-card typography and bounded Connections panel

Status: Approved

This existing desktop subtask owns the desktop session-card typography and
Connections-panel layout portions of the follow-up recorded in the parent
task.

### Implementation decisions and open questions

- Use `normal` for the session title, `secondary` for subtitle/preview,
  `small` for the session ID, and `tiny` for metadata, with matching line
  heights.
- Keep the Connections panel expanded by default with non-persisted local
  disclosure state.
- Render zero through three connection records in a natural-height plain
  container. Render more than three in a bounded `ScrollView`.
- The bounded height is equivalent to three standard rows. A non-interactive
  bottom fade indicates overflow and disappears at the real bottom.
- Reopening a collapsed list starts it at the top.
- Component and native expectations use active theme metrics and relative
  rendered geometry rather than copied preset numbers.

### Documentation

- Update desktop development documentation with the delivered session-card
  roles, Connections disclosure behavior, natural-height threshold, bounded
  scrolling, and primary native verification.

### Task checklist

- [x] Update desktop session title, subtitle/preview, ID, and metadata styles.
- [x] Extend desktop semantic typography regression coverage to every card
  field and the Open label.
- [x] Add the accessible Connections disclosure chevron and local state.
- [x] Share one connection-row render path between natural and scroll hosts.
- [x] Derive the over-three maximum height from active theme metrics.
- [x] Add a bottom overflow fade driven by scroll/content geometry and remove
  it at the real bottom.
- [x] Add stable production identifiers and component coverage.
- [x] Add one-, three-, and five-record macOS geometry/scroll tests.
- [x] Run the focused macOS Connections-panel XCTest after user confirmation.
- [x] Run complete desktop Jest and a bundled macOS test build.
- [x] Update desktop development documentation.

### Requirement verification

- Style/component tests assert the exact semantic font-size and line-height
  role for every desktop session-card field.
- Zero through three connection records produce natural panel heights and no
  scroll container.
- More than three records produce a capped viewport, visible continuation
  fade, and reachable final record; the fade is absent at the real bottom.
- The disclosure control reports the correct accessibility label/state and
  hides/restores only the connection list.
- macOS XCTest verifies one-versus-three panel geometry, no scrolling at three,
  real row movement and final-row reachability at five, collapsed header-only
  geometry, and no clipping at the largest preset.

### Additional implementation verification

- Run the focused ConnectionsPanel and desktop chrome Jest suites.
- Run the focused signed macOS XCTest and report the existing desktop
  full-TypeScript baseline separately.

### Implementation Notes

- Desktop session rows now use `normal` titles, `secondary`
  subtitles/previews, `small` IDs, and `tiny` metadata with matching semantic
  line heights.
- The Connections disclosure is expanded by default. Zero through three
  records use a natural-height `View`; larger sets share the same row render
  path inside a theme-derived three-row `ScrollView`.
- Four surface-colored opacity bands form the bottom fade. Scroll/content
  geometry removes it at the real bottom and restores it when more content is
  below. The fade exposes a semantic continuation label while present.
- Added `DesktopConnectionsPanelHarness` and
  `ConnectionsPanelUITests`. The harness selects default/largest presets by
  semantic name and reports theme-derived metrics; XCTest contains no copied
  typography values.
- Desktop Jest passed 23 suites and 120 tests. The signed app and UI-test
  bundle completed `build-for-testing` with `TEST BUILD SUCCEEDED`.
- Desktop full TypeScript still reports only the previously documented SDK
  URL, ChatPane optional-string, and Theme `shadow` errors. No changed
  follow-up file appears in that output.
- After user confirmation, the focused XCTest passed both tests with zero
  failures.

### Completion Notes

- Completed desktop session-card typography and the collapsible, bounded
  Connections panel.
- Native evidence covers natural height and absence of scrolling through three
  records, the theme-derived five-record viewport, fade visibility/removal,
  actual native scrolling and last-row reachability, plus disclosure behavior
  at the largest current preset.
- Initial native runs exposed an unlabeled React Native macOS ScrollView and a
  stale LLDB-held app process. The final test queries the actual native scroll
  view, uses the fade's semantic label, and passed cleanly after removing the
  orphan debugger session.

### Post-completion verification follow-up

- The first full desktop Jest run after XCTest passed all assertions but
  exited nonzero on an existing post-teardown `DependencyFlatList` timer. Its
  focused 4-test suite passed, followed by a clean full retry of 23 suites and
  120 tests.