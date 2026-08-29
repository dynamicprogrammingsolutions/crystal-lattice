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