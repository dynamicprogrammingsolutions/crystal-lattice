# Human time telemetry

The mobile app measures how long a person is actually active on a surface
and reports those durations to the duration-tracking plugin on the
connected backend. Collection is opt-in and off by default.

## What is collected

An activity burst opens a **span**; 30 seconds of inactivity closes it.
A span is `{sessionId: string|null, from: ISO-8601 UTC, to: ISO-8601 UTC}`
where `from` is the first and `to` the last activity of the burst — idle
gaps never enter a span, and switching surfaces closes the open span and
lets the next activity open a fresh one.

Activity sources:

- **Session surfaces** (span carries the session id): composer typing,
  transcript scrolling, and sending in a session chat.
- **Session-less surfaces** (span carries `null`): scrolling and row taps
  on the sessions list.

Leaving the foreground (app background) closes the open span.

## Settings

Both settings live in the global settings modal and persist through
`clc_mobile_global_preferences_v1`:

- `Time tracking` (`timeTrackingEnabled`, default off) — the opt-in
  toggle. Turning it off stops collection; pending spans stay cached and
  upload only while tracking is enabled.
- `Telemetry plugin` (`timeTrackingPluginId`, default
  `duration_tracking_app`) — the frontend-owned plugin id the uploads
  target. The app does not discover the plugin; a wrong id produces a
  one-time warning (below), not silent loss.

## Upload behavior

`src/humanTimeTelemetry/` owns the pipeline:

- `spanTracker.ts` — burst detection and span closing.
- `spanCache.ts` — durable per-connection AsyncStorage cache
  (`clc_human_time_spans_v1`, 5000-span soft cap). Spans persist until
  the backend confirms their batch, so restarts and failed uploads do
  not lose data.
- `uploader.ts` — batched drain over `executeAction`
  (`record_human_time_spans`, `actionOwner: "application"`, up to 100
  spans per call, content-derived `request_id` stable across retries).
  Flushes debounce 2s after a span closes, force-flush spans older than
  5 minutes, run when a connection becomes usable, and defer while a
  request is running on that connection (re-checked every 15s).
- `warning.ts` — the failure banner.
- `HumanTimeTelemetryProvider.tsx` — context + collectors wiring, mounted
  in `ConnectedRoot`.

Transient failures (network errors, HTTP 5xx) retain the spans for retry.
Definitive failures (HTTP 404/400, e.g. an unknown plugin id) also retain
the spans, and the app shows a one-time dismissible warning banner on the
connection banner rail; changing either setting re-arms the warning.

The backend resolves overlaps and dedups by request id; the session total
surfaces in the chat status bar (`Human time: …`) after the next request
finalizes. See `plugins/duration-tracking/docs/development/overview.md`
for the ingestion contract.

## End-to-end verification

Human time uses two touching verification tiers. Stored SQLite span rows
are their shared boundary.

The real-backend Jest tier starts a server with the deterministic stream,
timestamp, and duration-tracking plugins. It seeds deterministic spans
into the real frontend cache and uploads them through
`RestAgentBackend`/`FetchTransport`. It verifies cache draining, stored
session totals surfacing on the next request, request-id retry dedup, and
definitive-failure retention:

```bash
npm run test:integration -- \
  --runTestsByPath __integration__/humanTimeSpanUpload.realBackend.integration.test.ts
```

The focused Detox tier proves collection. It launches the real release
app without harness arguments, spawns the same real backend in a
hermetic workspace, connects through the production manual-address
flow, and enables tracking through the real settings UI. Composer typing
and sending exercise session activity; a real Sessions-list drag and row
tap exercise session-less activity. The host then queries the plugin's
SQLite store and requires positive-duration rows for both the UI-created
session and `session_id: null`.

Build a current release app when production mobile sources have changed,
then run the focused suite:

```bash
npm run detox:build:ios
npm run detox:test:human-time:ios

npm run detox:build:android
npm run detox:test:human-time:android   # prepares the emulator first
```

The frontend-sdk backend harness resolves Python from `PYTHON`, then the
repository `.venv`, then `python`. The local timestamp and
duration-tracking plugin checkouts must be loadable by that interpreter.