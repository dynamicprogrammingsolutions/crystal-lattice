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

The current notification XCUITest target builds, but execution remains
unverified because XCTest timed out while enabling macOS automation before app
launch. Human desktop verification remains a separate checkpoint.