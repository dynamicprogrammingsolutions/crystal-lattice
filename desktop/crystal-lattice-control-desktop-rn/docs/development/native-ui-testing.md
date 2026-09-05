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

The action-display harness emits a direct modal response through the production
global display owner. Its focused XCUITest opens the native React window,
scrolls a 300-line compiled-message body, and closes the window:

```bash
npm run test:macos-ui:action-display
```

Harnesses report theme-derived values and measured frames. Native assertions
compare those values and relative geometry instead of copying display-preset
numbers, allowing preset tuning without rewriting native tests.