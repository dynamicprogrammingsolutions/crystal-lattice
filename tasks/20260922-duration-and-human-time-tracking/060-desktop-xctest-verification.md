# 060 — Desktop human time XCTest verification

The native macOS UI-test tier for desktop human-time collection — the
Detox equivalent: the real desktop app against a real spawned backend,
real typing/sending and list activity landing as positive-duration rows
in the real duration-tracking plugin's SQLite store. Delegated as a
separate task because XCTest runs require the user's desktop approval
(standing directive: stop before the first XCTest invocation and ask). Keep
this to one focused native flow; scheduling, diagnostics, rejection isolation,
and warning classification belong to 050's deterministic tiers.

## Requirements checklist

- [ ] A native macOS UI test (XCUITest, following the existing
  `test:macos-ui*` suite conventions) drives the real desktop app
  through the production connection and settings flow against a real
  spawned backend and proves real UI activity lands as stored rows:
  session-attributed spans from composer typing and sending,
  session-less spans from list interactions, all with positive durations.
- [ ] The test uses one focused flow and closes spans deterministically by
  switching between session and session-less surfaces after at least two
  spaced activity events per surface; it does not add a long inactivity wait
  or duplicate unit/integration scenarios.
- [ ] The two verification layers touch at the stored rows: this tier
  proves UI activity → collector/cache/uploader → HTTP action → plugin
  rows; 050's Jest tier proves stored entries → transport → server →
  plugin → next-request surfacing.
- [ ] The suite is green via its package script, or the exact environment
  blocker is recorded (never silently skipped).
- [ ] The user's approval is obtained before the first `xcodebuild test`
  invocation.

Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/050-desktop-human-time-telemetry.md

## Open requirement questions

- None blocking. Use the production app flow, not a UI-copy harness. A
  host-side runner may pass the ephemeral server address and fixture paths as
  launch environment, but it must not bypass the production connection,
  settings, collector, cache, transport, or plugin paths.

## Supporting details

### Existing macOS UI-test infrastructure

- Scripts: `test:macos-ui`, `test:macos-ui:session-filters`,
  `test:macos-ui:rich-session-ui`, `test:macos-ui:connections`,
  `test:macos-ui:transcript-range`, `test:macos-ui:action-display` —
  all `FORCE_BUNDLING=1 xcodebuild -workspace
  macos/CrystalLatticeControlDesktopRN.xcworkspace -scheme
  CrystalLatticeControlDesktopRN-macOS -configuration Debug -destination
  'platform=macOS,arch=arm64' test -only-testing:CrystalLatticeControlDesktopRN-macOSUITests/…`.
- Existing suites: `SessionFiltersPopoverUITests`,
  `ConnectionsPanelUITests`, `TranscriptRangeNavigationUITests`,
  `ActionDisplayWindowUITests`; harness windows live under
  `src/testing/` and are enabled per suite via the env vars.
- A new focused suite needs its own script entry following the same
  pattern.

### What transfers from the mobile Detox tier (031, completed)

- The server config requirements: timestamp extension
  (`path:${env:REPO_ROOT}/plugins/timestamp-extension`) +
  duration-tracking plugin + `deterministic_stream` provider (the echo
  provider's streaming path hangs on the HTTP runner — pre-existing).
- Both database paths must point at the hermetic DB: the provider's
  `duration_tracking_db_path` AND the application plugin's
  `application.duration_tracking.db_path` — session-less spans follow
  the application plugin's path (this gap cost a debugging round on
  mobile).
- Set `application.duration_tracking.working_directory` explicitly to the
  hermetic test workspace. Production defaults it to `WORKING_DIR`, but the
  explicit fixture value makes the expected project attribution deterministic.
- The host-side SQLite query as the touch-point assertion: query the
  spawned server's store from the orchestration process and require
  positive-duration rows for both the seeded, UI-used session and
  `session_id: null`.
- Seed a target session and enough list rows through the production SDK before
  the UI flow. Session creation is not the behavior under test, and pre-seeding
  keeps the single native test focused.
- Use two spaced interactions followed by a surface switch to produce
  positive-duration closed spans. Allow the 2-second upload debounce and poll
  the SQLite store; a 30–45 second inactivity sleep is unnecessary.

### Desktop orchestration correction

- The TypeScript `startBackendServer` Jest harness cannot be called directly
  from Swift XCTest. Add a small host-side runner/script that owns server
  startup, SDK seeding, hermetic DB/config paths, `xcodebuild`, SQLite
  verification, cleanup, and failure propagation.
- XCTest owns only production UI interaction. The runner supplies the
  ephemeral endpoint as launch environment or fixture input; the app still
  connects through its ordinary connection UI and settings flow.
- The package script invokes that runner, so the approval gate applies to the
  script as a whole before its first `xcodebuild test`.

### What likely does not transfer

- The Detox idle-synchronization deadlock (a connected production app
  never goes idle, so Detox's sync blocks forever) is Detox-specific;
  XCUITest has no equivalent idle contract with the RN runtime. Expect
  instead: modal/animation timing races if the desktop uses animated
  transitions (use explicit visibility waits), and a busy run loop from
  the connected app's polling — keep assertions resilient.

### Standing constraints

- **Hard stop:** obtain the user's approval before the first XCTest run;
  Detox-style runs needed no confirmation, XCTest does.
- Commit only when the user explicitly requests it.
- The reviewer-CA pem deletion stays unstaged; other agents' in-flight
  work stays untouched.

## Execution plan

Status: Draft

1. Inspect the UITests target and one existing suite (e.g.
   `ConnectionsPanelUITests`) for launch/accessibility conventions and inspect
   the mobile real-backend fixture for config/SQLite assertions.
2. Add a host-side runner that starts the real backend with the same hermetic
   config as 050, seeds a session/list through the public SDK, passes the
   endpoint to XCTest, invokes the focused test, polls/asserts SQLite rows,
   cleans up, and preserves logs on failure.
3. Write one focused production-flow XCUITest: create/save/open the real
   connection, enable tracking in the real settings window, open the seeded
   session, perform spaced typing/send activity, switch to the session list,
   perform spaced list activity, and switch away to close that span.
4. Add the package script entry following the `test:macos-ui:*` naming
   convention but invoking the runner rather than bare `xcodebuild`.
5. **Stop and ask the user for approval before the first `xcodebuild
   test` invocation.**
6. After approval, iterate to green; record the evidence or the exact
   environment blocker; update the task records and the desktop docs'
   run commands.

### Implementation decisions and open questions

- Production flow is selected. Launch environment may carry only orchestration
  facts such as the ephemeral endpoint/fixture identifiers; do not add a
  test-only UI, endpoint, collector, upload path, or direct state injection.
- The XCTest approval gate is a hard process stop, not a design choice.

### Documentation

- The desktop dev-docs page (from 050) gains the native-tier run command
  and the two-tier description; the README test section lists the new
  script.

### Task checklist

- [ ] Existing UITests conventions inspected; flow approach decided
- [ ] Host-side backend/XCTest/SQLite runner implemented
- [ ] Focused collection UI test written
- [ ] Package script entry added
- [ ] User approval obtained before the first XCTest run
- [ ] Suite green or exact blocker recorded
- [ ] Docs + task records updated with evidence

### Requirement verification

| Requirement | Evidence |
|---|---|
| Real UI activity lands as stored rows (session + session-less, positive durations) | Runner-side SQLite assertions against the spawned server's store after the focused XCUITest |
| Real app + real server + real plugins, production flows | Runner spawn/config evidence + XCTest production connection/settings/session/list interactions; no test-only UI or endpoints |
| Two-layer touch at stored rows | This suite's store assertions + 050's landed Jest tier (4/4) cited together in the docs |
| Green or explicit blocker | The package script exits 0, or the completion notes contain the exact command output |
| Approval before the first XCTest run | The approval recorded in this task file before any `xcodebuild test` invocation |

### Additional implementation verification

- Scope audit: no production collector/plugin behavior changes from this
  task; if the test exposes a real collector defect, record it and
  return the plan to Draft rather than weakening the test.