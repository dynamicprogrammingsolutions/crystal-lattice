# Desktop native UI testing

Desktop unit and real-backend component tests verify data flow and routing.
XCUITest verifies native popovers, windows, and geometry that cannot be
reliably proven below the native boundary.

Run macOS UI tests and simulator UI automation sequentially to avoid focus
changes dismissing transient popovers. Their builds can run concurrently.

XCUITest must never terminate an already-running Crystal Lattice process.
A harness can coexist with the installed app when it uses a separate bundle
identifier. Debug and Release builds normally share the app's bundle identifier;
use an isolated identifier as in the action-display command below when the
installed app is running. If an existing Xcode test or Debug-harness session prevents
automation or a new harness launch, stop the run and report that specific
conflict to the user; do not terminate it automatically. Do not add
`forceTerminate`, `killall`, `pkill`, or equivalent process cleanup to XCTest
setup or test scripts.

Deterministic native harnesses are registered through `index.js` and selected
by `AppDelegate.mm` launch flags. The notification rail harness uses
authoritative fake backend snapshots plus the production application and
session notification hosts, asserts that the rail pushes message content down,
and attaches a screenshot.

The transcript-range harness mounts the production `ChatPane` with a
deterministic 200-message backend. Its focused XCUITest uses the production
Show older/newer controls and compares the selected overlapping message's
native frame before and after each range replacement:

```bash
npm run test:macos-ui:transcript-range
```

The Connections-panel harness mounts the production panel with deterministic
record counts and selects the default or largest current typography preset by
semantic name. Its focused XCUITest verifies natural height through three
records, bounded scrolling above that threshold, bottom-fade state, and the
disclosure control:

```bash
npm run test:macos-ui:connections
```

The action-display harness emits a direct modal response through the production
global display owner. Its focused XCUITest opens the native React window,
scrolls a 300-line compiled-message body, and verifies reopening with the same
display ID and body after both the card's Close button and the native window
close button:

```bash
npm run test:macos-ui:action-display
```

To run only the reopening regression alongside an installed app, use this
command from the desktop package directory. It gives the harness a separate
bundle identifier and build directory:

```bash
CLC_ENABLE_ACTION_DISPLAY_HARNESS=1 FORCE_BUNDLING=1 xcodebuild \
  -workspace macos/CrystalLatticeControlDesktopRN.xcworkspace \
  -scheme CrystalLatticeControlDesktopRN-macOS \
  -configuration Debug \
  -destination 'platform=macOS,arch=arm64' \
  -derivedDataPath build/action-display-reopen-derived-data \
  PRODUCT_BUNDLE_IDENTIFIER=com.dynamicprogrammingsolutions.crystallatticecontrol.macos.actiondisplayuitests \
  test \
  -only-testing:CrystalLatticeControlDesktopRN-macOSUITests/ActionDisplayWindowUITests/testLongDirectActionDisplayReopensAfterBothCloseMethods
```

The desktop-workspace harness mounts the production Home, History, activity
rail, and session tab strip with deterministic sessions. Focused methods in
`ConnectionsPanelUITests` verify preview promotion, activity-panel state,
request-status accessibility, Home navigation, real Watchlist mouse drag, and
real permanent-tab mouse drag. The same harness reports policy-derived sidebar
metrics so native tests can verify pointer and arrow-key resizing, bounds, and
main-workspace protection without copying dimensions. It also posts a native
middle-button click to prove tab close does not select or reorder the tab.
`MarkdownDisplayMenuUITests` verifies that the application Settings item opens
the separate keyed Settings window.

The rich-session-UI harness mounts the production `ChatPane` with portable
config-rich model selection plus session-header and composer action controls.
Its focused XCUITest verifies native popover selection and placed actions:

```bash
npm run test:macos-ui:rich-session-ui
```

It also mounts the production `MessageActionsBar` with shared menu-label
fixtures from `test/fixture/action-menu-labels.json`. The compaction label is
checked against the real plugin's HTTP schema by the frontend SDK integration
test; the longer synthetic label exercises wrapping only. The focused native
method `testMessageActionNamesWrapAndKeepPinsIndependent` checks popup width,
row height, pin behavior, dismissal, and attaches a review screenshot. The
mobile rich-session-UI Detox suite exercises the same production menu and
fixture and saves its screenshot under its `artifacts/detox/action-popup-review/`.
Both tests switch to an oversized action list and prove that the last pin
remains reachable by scrolling within the bounded popup. These are native UI
checks, not network end-to-end tests.

Harnesses report theme-derived values and measured frames. Native assertions
compare those values and relative geometry instead of copying display-preset
numbers, allowing preset tuning without rewriting native tests.

## Chat operations through HTTP

Run the focused production Chat workflow with:

```bash
npm run test:macos-ui:chat-operations
```

The host runner seeds sessions and a connection in a real temporary backend,
then launches the production desktop root with four permanent session tabs.
The forwarding HTTP proxy can interrupt send acknowledgement and delay edit
acknowledgement while preserving the actual backend response bytes. XCTest
drives request/tab eviction and return, main-composer editing, concurrent
actions, and recovery Resend/Cancel. It measures native transcript/status
frames and wheel movement. The runner applies a command-line bundle identifier
override only to its test build, so the installed desktop application can stay
open. It checks for an existing instance of that isolated test build and never
terminates it. The maintained application identifiers are unchanged.

The Debug bundle and DerivedData are built in `build/chat-operations`.
The runner writes its fixture to `build/chat-operations-fixture.json`; XCTest
resolves that path from its compiled source checkout. The fixture is removed
after the run. Direct HTTP inspection verifies the selected message changed
and retry did not duplicate the original user payload.
