# 031 — Human time telemetry Detox e2e completion

Complete the focused Detox e2e for human time span collection: real user
activity in the real app (typing, sending, session-list taps) must land as
rows in the real duration-tracking plugin's store. The backend (Phase A),
the mobile collector pipeline (Phase B chunks 1–4), and the jest
integration tier are done and green; only the Detox run remains, plus the
docs alignment for the two-layer test split.

Task relations: SPLIT FROM
`tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md`
(chunk 5, e2e Detox). The jest integration half of the split already
landed inside 030; this task owns the Detox half.

## Requirements checklist

- [ ] The focused Detox test proves real UI collection end to end: composer
  typing and sending produce spans attributed to the open session, and
  session-list row taps produce session-less spans, all recorded by the
  real duration-tracking plugin with positive durations.
- [ ] The test drives the real release app (no harness launch args, no
  test-only endpoints) against a real spawned backend
  (`startBackendServer` from the frontend-sdk integration harness) with
  the real plugins.
- [ ] The iOS suite passes green via `npm run detox:test:human-time:ios`.
- [ ] The Android script (`detox:test:human-time:android`) runs green, or
  the environment blocker is reported explicitly (not silently skipped).
- [ ] The two-layer verification stays coherent and touching: the jest
  integration tier proves transport → server → plugin → surfacing from
  stored entries; the Detox tier proves UI activity → stored rows. The
  stored SQLite rows are the shared touch point.
- [ ] Documentation matches the final two-layer design (mobile development
  doc, plugin overview frontend notes, e2e run instructions).
- [ ] No regressions: the mobile unit suite and `tsc --noEmit` stay green;
  the duration-tracking plugin package is not modified by this task.

## Open questions

- None blocking. Environment-dependent: whether the Android emulator
  toolchain is available on the receiving machine — run it if it is,
  otherwise report the blocker in the completion notes.

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

## Execution plan

Status: Draft

1. Add the settle delay after `global-settings-modal-close` and audit the
   remaining post-connect taps (agent picker modal, back navigation) for
   the same animation race; prefer a small `settleAfterModal()` helper
   over scattered sleeps.
2. Fix `listSessionIds` to exclude `.selected.json`.
3. Iterate the iOS run in the foreground until green
   (`npx detox test -c ios.sim.release e2e/humanTimeTelemetry.e2e.test.ts
   --cleanup`); keep the step logs while iterating.
4. Trim the debug step logs once green; re-run once to confirm.
5. Run the Android script if the emulator environment is available;
   otherwise record the blocker.
6. Update the docs to the two-layer design: the mobile
   `docs/development/human-time-telemetry.md` e2e section still describes
   the retired status-bar/warning e2e cases; the plugin overview's
   frontend-collection section and the e2e run instructions should match
   what landed.
7. Sweep: mobile unit suite, `tsc --noEmit`, and the integration tier
   (`npm run test:integration`-style run of the new file) stay green.
8. Update `030-human-time-telemetry.md`: mark its chunk 5 via this task
   (SPLIT INTO relation already recorded) and refresh its requirement
   table's e2e rows to the two-layer evidence.

### Implementation decisions and open questions

- Resolved (user, 2026-09-24): the test split — jest integration proves
  transport → server → plugin from stored entries; Detox proves real UI
  collection into the store; the layers touch at the stored rows.
- Resolved (user, 2026-09-24): Detox runs do not need per-run
  confirmation; any XCTest (native iOS test) run does — stop and ask.
- Implementation choice for the receiving agent: settle-delay helper vs
  inline sleeps; and whether to keep a reduced set of step logs.
- Open (environment): Android emulator availability.

### Documentation

- `mobile/crystal-lattice-control-rn/docs/development/human-time-telemetry.md`
  — rewrite the e2e section for the focused collection test + the jest
  integration tier; keep the run commands accurate.
- `plugins/duration-tracking/docs/development/overview.md` frontend
  collection section — verify it matches the landed behavior (it was
  written before the split; the collection facts still hold).
- `030-human-time-telemetry.md` — chunk 5 + requirement-table updates
  after this task lands.

### Task checklist

- [ ] Settle delay after the settings-modal close + tap audit
- [ ] `listSessionIds` excludes `.selected.json`
- [ ] iOS Detox suite green
- [ ] Debug logs trimmed (suite re-confirmed green)
- [ ] Android run green or blocker reported
- [ ] Docs updated to the two-layer design
- [ ] Sweeps green (unit, tsc, integration tier)
- [ ] 030 task file updated (chunk 5 + requirement rows)

### Requirement verification

| Requirement | Evidence |
|---|---|
| Real UI collection lands as stored rows (session + session-less, positive durations) | The Detox test's host-side SQLite assertions against the spawned server's store |
| Real app + real server + real plugins | The test's spawn config + production connect flow; no harness args, no test-only endpoints |
| iOS suite green | `npm run detox:test:human-time:ios` exit 0 with both store-row assertions passing |
| Android script | Script run exit 0, or the explicit environment blocker recorded |
| Two-layer coherence | Landed jest integration tier (3 green tests) + this suite's stored-row assertions; both cited in the docs |
| Docs match the landed design | Review of the updated mobile doc + plugin overview section |
| No regressions | Mobile unit suite + `tsc` + integration tier green; `git status` shows no plugin-package edits from this task |

### Additional implementation verification

- None beyond the above; the unit tiers (246 tests) already pin the
  tracker/cache/uploader/provider mechanics, and the integration tier
  pins the server-side contract.