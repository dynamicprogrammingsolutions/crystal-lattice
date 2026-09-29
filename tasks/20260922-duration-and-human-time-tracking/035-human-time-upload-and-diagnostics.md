# 035 — Human time upload reliability and diagnostics

Simplify mobile human-time uploading so collected spans cannot remain pending
only because an agent request is active, flush durable spans when the app
returns to the foreground, and add compact user-facing diagnostics on both the
mobile and duration-report surfaces.

Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md
- tasks/20260922-duration-and-human-time-tracking/031-human-time-detox-e2e.md

## Requirements checklist

- [x] Closed human-time spans are persisted immediately and uploaded in
  debounced batches without deferring for active agent work.
- [x] Pending spans flush when their connection becomes usable and whenever
  the app returns to the foreground; transient failures retain the spans and
  retry on a simple fixed timer while the app can run.
- [x] The mobile Global Settings surface provides compact diagnostics showing
  collection state, the durable pending count, and the latest upload result,
  with Refresh and Upload now controls.
- [x] The existing user-facing Show duration report action includes a compact
  human-time diagnostics section covering session and application collection
  readiness, store alignment, stored totals, and the latest received upload.
- [x] A partially skipped ingestion batch is never silently reported as fully
  uploaded or removed from the frontend cache.
- [x] Verification stays focused on deterministic mobile/plugin tests and the
  existing real-backend integration boundary; no additional simulator matrix
  is introduced.

## Requirement questions

None. The user approved the simplified upload triggers, removal of the busy
condition, minimal diagnostics, and execution on 2026-09-24. The plugin-side
diagnostics are user-facing through the existing Show duration report action,
per the user's correction.

## Supporting details

- The current uploader already debounces for two seconds after a span closes,
  but rejects every flush while `isBusy()` is true. Only the connection-open
  path schedules a busy retry, so an ordinary close-time upload can remain
  pending.
- Backgrounding closes the current span. The current AppState listener does
  nothing on the later `active` transition, despite the uploader documentation
  claiming foreground flushes.
- The current five-minute age scheduler is compensating for missed triggers.
  A direct close-time flush, foreground/connection flushes, and fixed
  transient-failure retry make it unnecessary.
- Action execution returns ingestion counts under the successful response's
  `result`. The current uploader ignores those counts and removes the whole
  batch even when `skipped` is positive.
- The existing Show duration report is already a session action rendered as a
  user-facing modal. Extending it is smaller and more discoverable than adding
  another machine-only diagnostics action.

## Execution plan

Status: Approved

Replace the uploader's busy/max-age scheduler with four explicit triggers:
debounced span close, usable connection, app foreground, and a fixed retry
after transient failure. Keep the durable cache and stable content-derived
request IDs unchanged. Serialize foreground/manual flushes behind pending
cache writes so a just-closed background span is visible before upload.

Expose a small immutable diagnostics snapshot from the existing telemetry
provider. It will contain enabled/connected state, the open or most recently
collected span, pending count, and the latest upload attempt/result. Add a
collapsible diagnostics section directly below the telemetry plugin setting,
with Refresh and Upload now controls. Do not add a general event viewer,
persisted timeline, export flow, or native-only diagnostics surface.

Treat a successful action envelope containing skipped spans as a definitive
non-success and retain the batch. Make duration ingestion validate/resolve the
whole input before recording so configuration or malformed-span skips do not
partially commit a request that the frontend must retain.

Extend the existing duration report with a Human time diagnostics section.
Using the current session configuration and application-plugin configuration,
report whether session and session-less collection targets are ready, whether
they use the same store, current-session/application-target span totals, and
the most recent processed human-time request. Do not expose absolute database
paths in the display.

Keep verification below the native simulator layer: focused uploader/provider
and settings-component tests, duration-store/app-plugin tests, the existing
real-backend upload integration, package suites, and type/lint checks.

### Implementation decisions and open questions

- Approved: remove `isBusy` from the human-time provider/uploader contract and
  upload concurrently with ordinary agent work.
- Approved: foregrounding always attempts to flush durable pending spans after
  outstanding cache writes settle.
- Approved: replace max-age/busy timers with one fixed transient retry timer.
- Approved: mobile diagnostics are an inline Global Settings section rather
  than a new navigation screen.
- Approved: plugin diagnostics extend Show duration report rather than adding
  a second user action.
- Approved: ingestion resolves and validates the complete request before
  recording; a skipped input is a batch-level non-success, preventing silent
  partial cache deletion.
- No open material decisions remain.

### Documentation

- Update the mobile human-time development page with the simplified trigger
  and retry model plus the compact settings diagnostics.
- Update the duration-tracking README/development overview with the report
  diagnostics and all-or-none validation behavior.
- Correct subtask 030 and the parent requirement text to supersede the earlier
  busy/max-age upload requirement after verification exists.

### Task checklist

- [x] Add and pin simplified uploader scheduling behavior.
- [x] Add provider diagnostics state and foreground/manual flush behavior.
- [x] Add compact Global Settings diagnostics UI and component coverage.
- [x] Make skipped ingestion non-destructive and add store/action coverage.
- [x] Extend Show duration report with human-time diagnostics and tests.
- [x] Update owned documentation and task tracking.
- [x] Run focused and package-level verification.

### Requirement verification

- Upload triggers and retention: uploader/provider tests using fake timers,
  AppState transitions, durable cache assertions, and action call assertions.
- Mobile diagnostics: component test renders actual Global Settings/provider
  state, refreshes pending counts, and exercises Upload now.
- Plugin diagnostics: app-plugin report tests assert readiness, store
  alignment, totals, and latest-request output from real temporary SQLite
  stores.
- No silent partial success: store/action tests prove invalid or unresolved
  batches record nothing; uploader tests prove `skipped > 0` retains cache.
- Public cross-layer flow: existing real-backend Jest integration remains
  green with the simplified uploader and real duration plugin.

### Additional implementation verification

- Mobile unit suite and TypeScript check.
- Duration-tracking package tests plus focused Ruff formatting/lint checks.
- Diff/status audit preserving unrelated desktop-task files and CA deletion.

## Implementation Notes

- The provider serializes foreground and manual flushes behind its outstanding
  cache-write promise. This closes the background/foreground race without
  making collection block the UI.
- `isBusy`, the busy retry interval, and the max-age polling interval were
  removed. Transient action/network failures alone schedule a 30-second retry.
- The uploader reads the real action payload under `response.result`. A
  positive `skipped` count records a definitive diagnostic failure and leaves
  the complete batch in AsyncStorage.
- Store validation and app-plugin target resolution now reject the complete
  batch before writing. Rejected request IDs are not entered in the dedup
  table, so a corrected retry can reuse its stable frontend request ID.
- Global Settings remains the only mobile diagnostics surface. It shows
  enabled/connected state, open and last collected surfaces, pending count,
  latest upload status/counts, and errors; Upload now and Refresh are the only
  controls.
- The existing Show duration report now includes Human time diagnostics. It
  reports readiness, shared/separate storage, session/application totals, and
  the latest accepted request without showing database paths.

## Completion Notes

Completed 2026-09-24.

- Simplified uploading is implemented and verified: two-second close
  debounce, immediate connection/foreground flush, no agent-work gate, and a
  fixed transient retry.
- Compact mobile diagnostics and user-facing report diagnostics are
  implemented with focused component/store/action coverage.
- Partial ingestion is non-destructive at both boundaries: the plugin records
  none of an invalid/unresolved batch, and the mobile cache does not drain
  when the response reports skipped spans.
- Verification:
  - `npm test -- --runInBand`: 52 suites, 248 tests passed. Existing React
    `act(...)` warnings and MessageBubble logs remain non-failing.
  - `npm run tsc`: passed.
  - Focused real-backend Jest integration: 3 tests passed.
  - `pytest tests -q` in `plugins/duration-tracking`: 123 tests passed.
  - Black check and Ruff: passed for the duration-tracking package.
  - Pyright: 0 errors for `src/duration_tracking_plugins`.
  - `git diff --check`: passed.
- No Detox, emulator, or physical-device run was added or repeated; the
  previously completed focused collection scenario remains the native tier,
  as requested.
- The unrelated reviewer CA deletion and untracked desktop subtasks 050/060
  were preserved without modification.

## Post-completion follow-up

On 2026-09-24 the user requested three small extensions to the completed
diagnostics work:

- Default the application plugin's session-less working directory from the
  runtime `WORKING_DIR`, while preserving explicit configuration precedence
  and the existing shared default database.
- Add overall human time, the top 10 human-time sessions, and the top 3
  human-time projects to Show duration report; project rows include a separate
  session-less duration.
- Show the latest 10 collected spans in mobile diagnostics with upload status,
  session id, time, and duration.

Implementation and focused coverage were added in the duration store/report,
application-plugin initialization, uploader diagnostics events, telemetry
provider, and Global Settings diagnostics table.

Verification:

- Duration-tracking package: `125 passed`; Black, Ruff, and Pyright passed.
- Mobile package: `52` suites and `249` tests passed; TypeScript passed.
- Real-backend human-time integration: `3` tests passed.
- `git diff --check` passed.
- No additional simulator or Detox run was added.

On the same date, live-device diagnostics exposed a rejected span inside a
21-entry pending batch. The all-or-none server response caused the mobile
uploader to retain and label the complete batch failed, and the generic
definitive-failure path emitted an incorrect unavailable-plugin banner on each
application start.

The uploader now isolates a skipped batch into singleton requests, removes
confirmed spans by value, continues through later batches, and retains only
the rejected entries. Skipped span data is represented as a partial failure
in diagnostics and no longer invokes the unavailable-plugin warning path.
Focused cache/uploader/provider tests and the real-backend integration cover
the corrected behavior.

Latest verification after this correction:

- Mobile package: `52` suites and `252` tests passed; TypeScript passed.
- Real-backend human-time integration: `4` tests passed, including rejected
  span isolation through the production transport/server/plugin/store path.
- `git diff --check` passed.