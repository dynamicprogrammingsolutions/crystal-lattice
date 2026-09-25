# Human-time telemetry

The macOS desktop app can measure active human time and upload spans to the
duration-tracking application plugin. Collection is opt-in and disabled by
default.

## Collection and connection ownership

The first activity in a session opens a span. Further activity moves its
inactivity deadline. If no earlier close occurs, the span ends at the last
activity plus the configured maximum inactivity interval. Switching away from
the session, changing connection, backgrounding the app, disabling tracking,
or selecting **Upload now** closes it earlier at that transition time.

Selecting a tab does not open a span by itself. The next composer edit, send,
or user-initiated transcript scroll opens the span. Desktop currently creates
session-attributed spans only; session-list, connection-list, Home, and
History interactions do not create session-less spans.

## Settings and persistence

Global Settings contains:

- **Time tracking**, the opt-in toggle;
- **Telemetry plugin**, defaulting to `duration_tracking_app`;
- **Maximum inactivity**, defaulting to 30 seconds;
- **Show diagnostics**, the compact operational view.

The native settings authority persists all three collection settings so every
desktop window observes the same values. Changing maximum inactivity closes
an open span under the previous value and applies the new value to subsequent
activity.

Closed spans are stored in the shared AsyncStorage cache
`clc_human_time_spans_v1`, partitioned by connection. They survive application
restarts and remain cached until the server confirms them.

## Upload behavior

The shared uploader calls `record_human_time_spans` through `executeAction`
with `actionOwner: "application"`. Batches contain at most 100 spans and use a
content-derived request id stable across retries.

Upload starts:

- two seconds after a span closes;
- when its connection becomes usable;
- when the application returns to the foreground;
- when the user selects **Upload now**.

Uploads do not wait for agent work or network idleness. Transient failures
retain spans and retry after 30 seconds. A definitive plugin/action failure
retains spans and emits one warning per connection/settings arm cycle.

If the server reports skipped span data, the uploader isolates the batch into
single-span requests. Valid neighbors continue uploading and are removed by
value; rejected spans remain pending. Data rejection does not produce the
unavailable-plugin warning.

## Diagnostics

The Global Settings window is a separate React Native root. The main
application coordinator publishes a serializable diagnostics snapshot through
the desktop in-process diagnostics bridge.

The view aggregates all saved connections and shows:

- enabled and connected-server state;
- open and most recently collected spans;
- total pending uploads;
- latest upload result and error/counts;
- the ten latest entries with status, connection, session, end time, and
  duration;
- **Upload now** and **Refresh** actions.

Pending entries are restored from durable storage. Uploaded-entry history is
limited to the current application run.

## Verification

Shared behavior is covered by the shared package tests. Desktop component tests
cover multi-connection routing, foreground upload, warning behavior, settings,
surface collectors, and the diagnostics window.

The real-backend tier starts the deterministic provider with the timestamp and
duration-tracking plugins. It verifies upload and next-request surfacing,
request-id deduplication, definitive-failure retention, and rejected-span
isolation:

```bash
npm run test:integration -- \
  --runTestsByPath __integration__/humanTimeSpanUpload.realBackend.integration.test.ts
```

## Native collection verification

The focused native tier uses one production-flow XCUITest. A Jest host runner
starts the same hermetic backend, seeds sessions through the public SDK, passes
a temporary fixture to XCTest, and verifies a positive session SQLite row
after the UI flow:

```bash
npm run test:macos-ui:human-time
```

The ordinary Jest, integration, and TypeScript configurations explicitly
exclude `__native__`; only the focused script can invoke this test.

The focused native runner uses the Release configuration so React Native
development loading and warning overlays cannot cover the bottom composer. Its
deterministic launch fixture provides one isolated namespaced connection,
preloaded backend sessions, tracking enabled for that fixture, and the target
session as the active tab. The shared native macOS text view exposes its real
editable `NSTextView` using the React Native test ID and accessibility label,
and mirrors `editable` into its accessibility-enabled state.

The existing native flow types and sends through the production composer,
switches to Home to close the session span, opens production diagnostics, and
invokes **Upload now**. Its session-only expectation is aligned with the
current collection model; this follow-up does not add another native scenario.
