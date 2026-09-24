# 031 — Human time telemetry Detox e2e completion

Complete the focused Detox e2e for human time span collection: real user
activity in the real app (typing, sending, session-list taps) must land as
rows in the real duration-tracking plugin's store. The backend (Phase A),
the mobile collector pipeline (Phase B chunks 1–4), and the jest
integration tier are done and green; only the Detox run remains, plus the
docs alignment for the two-layer test split.

Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Task relations: SPLIT FROM
`tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md`
(chunk 5, e2e Detox). The jest integration half of the split already
landed inside 030; this task owns the Detox half.

## Requirements checklist

- [x] The focused Detox test proves real UI collection end to end: composer
  typing and sending produce spans attributed to the open session, and
  session-list row taps produce session-less spans, all recorded by the
  real duration-tracking plugin with positive durations.
- [x] The test drives the real release app (no harness launch args, no
  test-only endpoints) against a real spawned backend
  (`startBackendServer` from the frontend-sdk integration harness) with
  the real plugins.
- [x] The iOS suite passes green via `npm run detox:test:human-time:ios`.
- [x] The Android script (`detox:test:human-time:android`) runs green, or
  the environment blocker is reported explicitly (not silently skipped).
- [x] The two-layer verification stays coherent and touching: the jest
  integration tier proves transport → server → plugin → surfacing from
  stored entries; the Detox tier proves UI activity → stored rows. The
  stored SQLite rows are the shared touch point.
- [x] Documentation matches the final two-layer design (mobile development
  doc, plugin overview frontend notes, e2e run instructions).
- [x] No regressions: the mobile unit suite and `tsc --noEmit` stay green;
  the duration-tracking plugin package is not modified by this task.

## Open questions

- None. Android was attempted with current APKs; the environment blocker
  is recorded in the completion notes.

## Supporting details

### Test split (user decision, 2026-09-24)

The original single e2e (happy path through the status bar + warning path)
was split because too many layers made it unwieldy:

- **Jest integration tier (done, green)**:
  `mobile/crystal-lattice-control-rn/__integration__/humanTimeSpanUpload.realBackend.integration.test.ts`
  — deterministic pre-generated spans seeded into the real span cache,
  uploaded through the real `RestAgentBackend`/`FetchTransport` against a
  spawned real server; asserts flush + drain, the session total stamped at
  the next request finalize (`human_time_session_total` 60000 → "1m"),
  request-id retry dedup (total unchanged after a re-upload of the same
  batch), and definitive-failure classification + span retention for an
  unknown plugin id.
- **Detox tier (this task)**: only the collection side — real UI actions →
  spans → stored rows, asserted by querying the plugin's SQLite store from
  the host.

### Detox + the real connected app (the central discovery)

- After a real backend connects, the production app polls continuously
  (sessions, request statuses, events), so Detox's idle-based
  synchronization never sees a quiet moment. Every action — and even
  `waitFor` checks — blocks forever. The harness-based e2e suites never hit
  this because they never connect a real backend. **Fix (in place):**
  `await device.disableSynchronization()` immediately BEFORE tapping
  `manual-connect-button`.
- With synchronization disabled, iOS drops taps that land while a modal
  presentation/dismissal is animating. **Fix (partly in place):** a ~600ms
  settle delay after modal-opening taps. The CURRENT failure is exactly
  this class: the `sessions-tab` tap fires while the settings modal's
  dismissal fade (a `UIView` with `alpha=0` + opacity/spring animations)
  still covers the screen.
- The connect wizard is NOT auto-shown on a fresh install: Connections tab
  → `connections-new-connection` → `connection-method-manual` → manual
  inputs → connect. After connecting, the tab stays on Connections; tap
  `home-tab` to reach the settings entry.
- The manual port input defaults to `8080` and Detox `typeText` appends:
  `clearText()` before `typeText()` on both inputs (in place).
- The settings modal's Time tracking toggle sits below the fold on small
  screens: the test scrolls `global-settings-scroll` until the toggle is
  visible (retry loop, in place).
- The test timeout is raised to 300s (the flow includes an inherent 45s
  inactivity wait).

### Server config requirements (all in place in the test)

- The duration-tracking feature needs the timestamp extension — without
  `path:${env:REPO_ROOT}/plugins/timestamp-extension` the feature's
  finalize finds no duration source and silently stamps nothing.
- Use `deterministic_stream` (`plugins.deterministic_stream_provider.DeterministicStreamProvider`),
  NOT the echo provider: the echo provider's streaming path hangs on the
  HTTP runner (its `stream_api` is untested; the Python integration tests
  use `stream=False`). Pre-existing issue, out of scope — reported, not
  fixed.
- The agent config needs `working_directory` + `allowed_paths`; the
  provider config needs `duration_tracking_db_path` (else spans key to an
  unpredictable default); `application.duration_tracking.working_directory`
  keys session-less spans (without it they are skipped).
- The workspace is a per-run `mkdtempSync` dir referenced through
  `${env:TEST_WORKSPACE}` placeholders.

### Uploader contract fixes (landed during e2e debugging, unit-tested)

- Wire format: the ingestion contract is snake_case — the uploader now
  converts `{sessionId, from, to}` → `{session_id, from, to}` at the
  boundary and hashes the converted batch for the request id.
- Action-level failures: the action protocol reports unknown
  plugin/action as HTTP 200 with `{status: 'error', error_type}` (not an
  HTTP error). The uploader now classifies
  `unknown_action|unknown_plugin|ambiguous_action|validation|not_found`
  as definitive (one-time warning, spans retained) and other error types
  as transient. 13 uploader unit tests + 5 provider tests green.

### Known latent bug in the test (fix before relying on it)

`listSessionIds` filters `endsWith('.json')`, which also matches
`<id>.selected.json` snapshot markers in the sessions root. Exclude
`.selected.json` (only bites when snapshots were selected, but fix it).

### Environment quirks

- Run Detox in the FOREGROUND from
  `mobile/crystal-lattice-control-rn` — background invocations start at
  the repo root (`npm run` fails with "Missing script") and jest output
  buffers invisibly.
- The iOS release binary is built and current (includes every testID the
  test uses); rebuild only if app sources change:
  `npm run detox:build:ios` (~10 min).
- The e2e currently carries `console.log` step markers (`CONNECT:`,
  `STEP:`) from debugging — useful while iterating; trim at the end.

### Working-tree constraints (standing directives)

- The duration-tracking plugin package has ANOTHER agent's uncommitted
  in-flight changes (tool-loop dedup migration in `duration_store.py` +
  tests). Do not touch, revert, or stage them; the landed tests run green
  against them.
- Never stage the unrelated deletion
  `mobile/crystal-lattice-control-rn/ios/CrystalLatticePythonRuntime/Resources/reviewer-proxy-ca.pem`.
- `tasks/20260923-tool-interop-cleanup/` belongs to another agent.
- Commit only when the user explicitly requests it.

## Implementation Notes (current state at handoff)

**Done and green:**

- Phase A backend (committed `72bf88c8`).
- Phase B chunks 1–4: span tracker, AsyncStorage cache, uploader,
  opt-in settings + warning banner, provider + collectors wiring
  (`src/humanTimeTelemetry/`, `HumanTimeTelemetryProvider` mounted in
  `ConnectedRoot`, collectors in `SessionChatScreen`/`SessionsScreen`).
  Mobile unit suite: 246 tests green; `tsc --noEmit` clean.
- Jest integration tier: 3 tests green (see the split section above).
- The Detox test file `e2e/humanTimeTelemetry.e2e.test.ts` is fully
  written (config, connect with clearText + sync-disable, settings with
  scroll-into-view, session creation, typing + send, row-tap cycles, 45s
  wait, host-side SQLite query, assertions) plus
  `detox:test:human-time:ios`/`:android` scripts in `package.json`.
- Production testIDs added for the flow: `connection-method-manual`,
  `manual-host-input`, `manual-port-input`, `manual-connect-button`,
  `sessions-header-action-new-session`, `messages-back-to-sessions`,
  `session-status-bar` (no longer used by the refocused test, kept as a
  stable identifier).

**Exact current failure (last run, 2026-09-24 14:03):** the flow is green
through launch → connect → settings → toggle enabled ("STEP: tracking
enabled" prints), then `element(by.id('sessions-tab')).tap()` fails with
"View is not hittable … Hit: `<UIView … alpha=0 … animations =
{UIPacingAnimationForAnimatorsKey, opacity=CASpringAnimation}>`" — the
settings modal's dismissal fade still covers the screen because, with
synchronization disabled, the tap fires immediately after
`global-settings-modal-close`. **First fix:** add the same ~600ms settle
delay after the close tap (and audit every tap that follows a modal
open/close for the same pattern — the agent picker modal and the chat
navigation are the next candidates).

**Debug history (so it is not repeated):** with sync enabled the run
hung indefinitely after connect (Detox busy-report: a pending main-queue
work item + 0ms/1s JS timers that never settle — the polling app never
goes idle). Moving `disableSynchronization()` earlier step by step
progressed the run each time: after the connect tap → still hung at the
tap's post-action idle wait; before the connect tap → connect works.
Then modal-fade taps needed settle delays (menu item, settings modal).
Each fix moved the failure forward; the modal-close fade is the current
frontier.

**Reassessment (2026-09-24):**

- The uncommitted mobile scope is limited to the focused e2e file and its
  two package scripts. `npx tsc --noEmit --pretty false` is currently
  clean with that file included.
- The settings-close race and `.selected.json` filter bug are both
  present exactly as described above.
- The agent picker is also a React Native `Modal` with
  `animationType="fade"`; because synchronization remains disabled, both
  its presentation before the agent tap and its dismissal before typing
  need the same explicit transition settle. The subsequent back/row-tap
  sequence changes ordinary screens without a modal and should continue
  to use visibility waits rather than unconditional delays.
- The mobile development doc is stale: it says the e2e uses the echo
  provider and asserts the status bar plus warning banner. The actual
  focused suite uses `deterministic_stream` and asserts session-bearing
  and session-less SQLite rows; the jest real-backend tier owns
  surfacing, retry dedup, and definitive-failure retention.
- The Android SDK, `adb`, and configured
  `Medium_Phone_API_36.1` AVD are available. The existing Android e2e
  APKs predate the telemetry implementation, so Android requires
  `npm run detox:build:android` before its focused script. The iOS
  release app postdates the production telemetry sources and only needs
  rebuilding if execution changes production app code.
- Files currently modified under `plugins/duration-tracking`, the
  reviewer CA deletion, and the 010/parent follow-up edits are other
  agents' work. This task must preserve them and make no plugin-package
  edits.

**Execution finding (2026-09-24):** the Sessions list had no stable
identifier, and a Detox drag targeted at a child row did not reach the
FlatList's `onScrollBeginDrag` collector. A selector-only production
change adds `testID="sessions-list"` to the existing FlatList so the e2e
can drive the real scroll surface directly. This does not change
collector behavior, but it requires rebuilding both platform apps before
their final runs. The focused test timeout is 600s because one iOS
simulator launch consumed nearly four minutes on this machine.

The first full SQLite assertions also exposed a test-config gap:
session-bearing spans follow the session/provider
`duration_tracking_db_path`, while session-less spans use the application
plugin's `application.duration_tracking.db_path`. The test supplied the
application working directory but not its database path, so valid
session-less rows landed in the default duration store instead of the
hermetic database being queried. The final config points both plugin
roles at `${env:TEST_WORKSPACE}/human_time.sqlite`.

## Execution plan

Status: Approved (user, 2026-09-24)

Finish the already-written focused suite without changing the production
collector or duration-tracking plugin. Stabilize only native modal
transition boundaries after synchronization is disabled, retain
visibility waits for ordinary screen navigation, and use the real
production connection flow and spawned backend throughout.

1. In `humanTimeTelemetry.e2e.test.ts`, introduce one small
   `settleAfterModalTransition()` helper and use it at the existing
   menu/settings presentation boundaries, immediately after closing
   global settings, after the agent picker becomes visible, and after
   choosing the agent before interacting with chat. Do not add harness
   arguments, test endpoints, or production timing hooks.
2. Correct `listSessionIds` so `<id>.selected.json` markers cannot be
   mistaken for sessions. Keep the host-side lookup and SQLite query
   scoped to the spawned server's hermetic workspace.
3. Run the focused iOS script in the foreground and iterate only on
   observed failures. Keep the temporary `CONNECT:`/`STEP:` diagnostics
   while locating the last race. Once green, remove the debug logs and
   run `npm run detox:test:human-time:ios` again as the final iOS
   evidence.
4. Build a current Android e2e app with
   `npm run detox:build:android`, then run
   `npm run detox:test:human-time:android`. Fix portable test-flow issues
   within this task; if the installed toolchain still fails outside the
   suite, preserve the exact command/output as the explicit environment
   blocker rather than skipping the requirement.
5. Align documentation with the final split:
   the mobile telemetry development page explains the focused UI-to-store
   Detox tier and the seeded-span transport-to-surfacing jest tier,
   including exact commands and the deterministic-stream backend; the
   mobile README adds the focused e2e run commands. Inspect the existing
   duration-tracking overview's frontend notes for accuracy, but do not
   edit the plugin package because its working tree is owned by another
   task and already describes the landed collector behavior.
6. Run the focused real-backend integration test, the complete mobile
   unit suite, and TypeScript checking. Then perform a scope/diff check
   confirming that this task touched only its mobile test/scripts/docs
   and task records.
7. Update task tracking after evidence exists: revise 030's chunk 5 and
   verification table to describe the two touching tiers, mark 031 in
   the parent subtask list complete, and add this task's completion notes
   with iOS/Android results and any blocker.

### Implementation decisions and open questions

- Resolved (user, 2026-09-24): the test split — jest integration proves
  transport → server → plugin from stored entries; Detox proves real UI
  collection into the store; the layers touch at the stored rows.
- Resolved (user, 2026-09-24): Detox runs do not need per-run
  confirmation; any XCTest (native iOS test) run does — stop and ask.
- Resolved (implementation): use one 600ms modal-transition helper at
  native fade-modal boundaries. Remove ad hoc step logs after the suite
  first reaches green.
- Resolved (environment inspection): the configured Android emulator
  toolchain is available, so the Android build and run are expected, not
  pre-classified as blocked.
- No requirement or material design questions remain. If a Detox failure
  exposes a production collector defect instead of test timing, record
  the finding and return the plan to Draft before expanding into
  production behavior changes.

### Documentation

- `mobile/crystal-lattice-control-rn/docs/development/human-time-telemetry.md`
  — replace the retired combined-e2e claims with the focused collection
  tier, the real-backend integration tier, their shared SQLite boundary,
  exact commands, and the deterministic-stream provider.
- `mobile/crystal-lattice-control-rn/README.md` — add the focused iOS and
  Android commands to the Detox run instructions and point to the
  telemetry development page for prerequisites and coverage boundaries.
- `plugins/duration-tracking/docs/development/overview.md` — inspection
  only; its current frontend collection facts are accurate and the
  package is outside this task's write scope.
- `tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md`
  and `000-main.md` — update split-task status and evidence after the
  runs succeed.

### Task checklist

- [x] Reassess the partial implementation and dirty-worktree ownership
- [x] Confirm the uncommitted e2e type-checks
- [x] Settle delay after the settings-modal close + tap audit
- [x] `listSessionIds` excludes `.selected.json`
- [x] iOS Detox suite green through the package script
- [x] Debug logs trimmed and iOS suite re-confirmed green
- [x] Current Android e2e app built
- [x] Android script green or exact environment blocker recorded
- [x] Docs updated to the two-layer design
- [x] Sweeps green (focused integration, mobile unit suite, TypeScript)
- [x] 030 and parent task records updated
- [x] Completion notes added with final evidence and scope audit

### Requirement verification

| Requirement | Evidence |
|---|---|
| Real UI collection lands as stored rows (session + session-less, positive durations) | The Detox test's host-side SQLite assertions against the spawned server's store |
| Real app + real server + real plugins | The test's spawn config + production connect flow; no harness args, no test-only endpoints |
| iOS suite green | `npm run detox:test:human-time:ios` exit 0 with both store-row assertions passing |
| Android script | Current APK built, then `npm run detox:test:human-time:android` exits 0; otherwise completion notes contain the exact environment failure |
| Two-layer coherence | `npm run test:integration -- --runTestsByPath __integration__/humanTimeSpanUpload.realBackend.integration.test.ts` exits 0 and the focused Detox store assertions exit 0; docs identify SQLite rows as the touch point |
| Docs match the landed design | Review of the updated mobile development page and README plus inspection of the plugin overview's frontend notes |
| No regressions; plugin package untouched | `npm test -- --runInBand` and `npm run tsc` exit 0; final path-scoped diff confirms no changes by this task under `plugins/duration-tracking` |

### Additional implementation verification

- Run `git diff --check` on this task's paths and inspect final
  `git status --short` so the reviewer CA deletion, plugin implementation
  changes, fixtures, and 010 follow-up remain untouched.
- Reuse the current iOS release build while only test/docs files change.
  If an observed defect requires a production mobile source edit after
  plan re-approval, rebuild iOS before accepting its Detox result and
  rebuild Android again before its final run.

## Completion Notes

- Outcome: the focused production-app Detox flow now connects to a real
  spawned backend, enables tracking through global settings, creates a
  session through the production UI, types and sends through the real
  composer, drives the real Sessions list and rows, waits for natural
  inactivity upload, and asserts positive-duration session-bearing and
  session-less rows in the duration-tracking plugin's SQLite store.
- Implementation details: modal fade boundaries use one 600ms settle
  helper after synchronization is disabled; session discovery excludes
  `.selected.json`; the test leaves and reopens chat to dismiss the
  multiline iOS keyboard while preserving the draft; seeded sessions
  created through the production SDK make the real list scrollable; the
  FlatList has the stable `sessions-list` test id; and application-plugin
  `db_path` plus provider `duration_tracking_db_path` point to the same
  hermetic database.
- iOS evidence: `npm run detox:test:human-time:ios` passed after debug
  logs were removed (1 suite, 1 test). A current Release simulator app
  was rebuilt successfully with direct `xcodebuild`; runtime preparation
  was deliberately not rerun so the unrelated reviewer CA deletion
  remained untouched.
- Android evidence/blocker: `npm run detox:build:android` passed
  (`BUILD SUCCESSFUL`, 739 actionable tasks). The required
  `npm run detox:test:human-time:android` was then run and exited 1 before
  any assertion: the configured `Medium_Phone_API_36.1` emulator launched
  the current app, but Espresso could not obtain a focused/stable root,
  Detox reported repeated application nonresponsiveness in
  `RootViewPicker`/`Choreographer` framework code, teardown timed out,
  and Jest reported 0 completed tests. Artifacts are under
  `mobile/crystal-lattice-control-rn/artifacts/detox/android.emu.e2e.2026-09-24 13-18-07Z/`.
  This is the explicit environment blocker allowed by the requirement,
  not a skipped or passing Android result.
- Two-layer evidence: the focused real-backend integration command passed
  3/3 tests for upload/surfacing, retry dedup, and definitive-failure
  retention. Its stored entries and Detox's host-side SQLite assertions
  are documented as the shared touch point.
- Regression evidence: `npm test -- --runInBand` passed 52 suites / 246
  tests (with existing React `act(...)` warnings), `npm run tsc` passed,
  and `git diff --check` passed on the task paths.
- Documentation: the mobile telemetry development page and mobile README
  now describe the deterministic-stream backend, exact commands, and
  two-tier coverage. The duration-tracking overview's existing
  frontend-collection notes were inspected and remain accurate; no file
  under `plugins/duration-tracking` was changed by this task.
- Plan deviations and findings: a selector-only production test id and
  current platform rebuilds were needed because child-row drags did not
  reach the list collector. The application plugin's separate database
  path was the reason valid null-session rows initially appeared outside
  the queried hermetic store. No production collector or plugin behavior
  was changed.
- Unresolved/deferred: rerun the Android script on a responsive Android
  emulator/Detox environment. No feature behavior is deferred.