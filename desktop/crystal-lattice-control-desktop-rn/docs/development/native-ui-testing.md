# Desktop native UI testing

Desktop unit and real-backend component tests verify data flow and routing.
XCUITest verifies native popovers, windows, and geometry that cannot be
reliably proven below the native boundary.

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

The desktop-workspace harness mounts the production Home, History, activity
rail, and session tab strip with deterministic sessions. Focused methods in
`ConnectionsPanelUITests` verify preview promotion, activity-panel state,
request-status accessibility, Home navigation, real Watchlist mouse drag, and
real permanent-tab mouse drag.
`MarkdownDisplayMenuUITests` verifies that the application Settings item opens
the separate keyed Settings window.

The rich-session-UI harness mounts the production `ChatPane` with portable
config-rich model selection plus session-header and composer action controls.
Its focused XCUITest verifies native popover selection and placed actions:

```bash
npm run test:macos-ui:rich-session-ui
```

Harnesses report theme-derived values and measured frames. Native assertions
compare those values and relative geometry instead of copying display-preset
numbers, allowing preset tuning without rewriting native tests.