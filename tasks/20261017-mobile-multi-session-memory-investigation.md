# Mobile multi-session memory investigation

Investigate whether rendering a heavy mobile chat session leaves memory retained
after the actual application shell navigates to another session with its normal
50-message history window.

## Requirements checklist

- [x] Exercise the production mobile application shell, session navigation,
      message-cache ownership, transcript list, message bubbles, and configured
      renderers rather than a standalone transcript substitute.
- [x] Use at least three representative heavy sessions selected read-only from
      the current project's `.crystal/sessions` directory without committing
      their private contents.
- [x] Automate a fresh-session control and an A-heavy → B-default → C-heavy
      multi-session sequence on the iOS Simulator using Detox.
- [x] Capture synchronized process-memory samples, transcript/session phase
      metrics, and an Instruments allocation trace where the local tooling
      permits it.
- [x] Compare the fresh B baseline with B after heavy sessions and report
      whether memory, mounted rows, or cached data remain elevated across
      session-screen unmounts.
- [x] Keep the work diagnostic: do not change production memory behavior or
      claim physical-device jetsam safety from Simulator results.
- [ ] Provide selectable `simple-reload`, `mobile-anchor-v1`, and
      `single-flight-anchor` transcript range-navigation strategies.
- [ ] Make `single-flight-anchor` the product default, retain
      `simple-reload` as an immediate kill switch, and expose
      `mobile-anchor-v1` only as a development diagnostic.
- [ ] Guarantee that the corrected anchor controller has at most one active
      retry chain, cancels all work on replacement/user navigation/unmount, and
      stops within bounded attempts and time before falling back safely.
- [ ] Persist the selected strategy in Development Settings and make the
      strategy selectable by the deterministic range-navigation harness.
- [ ] Add focused unit/component and production-path tests that distinguish the
      three strategies and prevent retry re-entry regressions.

## Scope

The first investigation covers upward transcript traversal and repeated
multi-session navigation. Streaming, renderer matrices, production fixes, and
physical-device validation are follow-up work unless the initial run cannot
produce interpretable evidence.

## Supporting details

- The source session store is `.crystal/sessions`; it is local runtime state and
  must be inspected read-only.
- The existing plain-text transcript harness does not exercise production
  message rendering or application-shell cache ownership.
- The existing chat-operations E2E path already demonstrates production
  `ConnectedRoot`, `SessionChatScreen`, `RestAgentBackend`, and public HTTP
  integration, but its test harness currently owns a simplified in-memory
  cache.
- The decisive comparison is session B opened directly in a fresh process
  versus the same 50-message B view after session A has rendered a much larger
  history in the same process.

## Execution plan

Status: Approved

Use a local, deterministic HTTP fixture service to expose three selected real
session histories through the production frontend backend contract. Launch the
normal mobile shell in a narrowly scoped investigation mode that supplies this
local connection while preserving the app-owned providers, navigation, message
cache, and screen lifecycle.

Run two automated scenarios against the same fixture set:

1. A cold control that opens session B directly at the default 50-message
   range, settles, and records its memory and row metrics.
2. A same-process investigation that opens A, traverses a large older history,
   opens B at the default range, then exercises C and returns to A/B.

Record explicit phase markers and sample the Simulator application process at a
fixed interval. Attach `xctrace` with the Allocations template after launch when
possible and finalize the trace after the Detox sequence. Prefer settled-memory
comparisons and growth slopes over absolute Simulator thresholds.

Interpret app-owned cached message bytes separately from mounted native row
state. A session switch should reduce mounted rows to the new session's render
window even when its previous message data remains intentionally cached.

### Implementation decisions and open questions

- Decision: selected real sessions are copied or transformed only into ignored
  runtime artifacts; no private transcript content is committed.
- Decision: the test uses the actual app shell and public HTTP backend adapter,
  with only deterministic connection/bootstrap injection for the investigation.
- Decision: the first run is evidence-producing rather than a hard pass/fail
  memory gate.
- No unresolved requirement questions remain.

### Documentation

- Keep operational instructions with the investigation runner or task notes.
- Do not add user-facing documentation because no supported product behavior is
  changing.

### Task checklist

- [x] Inspect session shapes and select three representative heavy sessions.
- [x] Add a deterministic local fixture backend and app-shell investigation
      bootstrap.
- [x] Add the multi-session Detox scenario and phase metrics.
- [x] Add process-memory sampling and `xctrace` orchestration.
- [x] Run focused static/unit checks.
- [x] Build and run the iOS Simulator investigation.
- [x] Analyze artifacts and record findings.

### Requirement verification

- Requirements 1–3: inspect and run the Detox trace showing production shell
  navigation through A, B, and C with the selected session metadata.
- Requirement 4: verify the run produces timestamped memory/phase artifacts and
  a readable allocation trace, or record the exact profiling-tool blocker.
- Requirement 5: calculate and report fresh-B versus B-after-A/C settled memory,
  mounted-row, and loaded/cached-message comparisons.
- Requirement 6: inspect the diff and task completion notes to confirm no
  production memory policy or physical-device claim was introduced.

### Additional implementation verification

- Run TypeScript validation for the mobile package.
- Run focused Jest coverage for any new fixture-selection or metric helpers.
- Confirm selected real session contents remain absent from tracked files.

## Implementation Notes

- Selected the three largest eligible regular session files below 64 MiB. They
  contain 567, 540, and 642 messages respectively. A 325 MiB outlier was
  intentionally excluded from the first controlled run.
- The investigation uses the ordinary `App` entrypoint and automates the
  production manual-connection wizard. No substitute React shell or simplified
  message cache is used.
- The fixture service starts the real Python HTTP application against temporary
  transformed copies. Only investigation metadata such as title, archived
  state, status, notifications, and overrides is normalized; messages remain
  intact and source files remain read-only.
- The Detox scenario records a fresh B control, traverses older A and C history
  windows, and compares B after A and after A+C. It records one-second process
  RSS, explicit phase snapshots, and attempts a separate Allocations trace for
  each scenario.
- Mounted-row instrumentation was not added to production components in this
  first pass. Loaded range and message counts are recorded; native allocation
  ownership is available from the Allocations trace.
- The first long Allocations attempt caused a host watchdog panic before the
  first heavy-session phase marker. The panic report shows `xctrace` at about
  12.1 GiB resident, the Simulator app at about 454 MiB, compressor pages at
  98% of limit, compressor segments at 100%, and 43 swap files. The completed
  30-second fresh-B trace remains readable; the interrupted 2.5 GiB
  multi-session trace did not finalize.
- Long stress runs now use only the one-second RSS/phase sampler. `xctrace` is
  opt-in and capped to a maximum of two minutes with a bounded end window; the
  default capture is 45 seconds with a 20-second window.
- Session A traverses six windows covering roughly 300 messages. Session C
  traverses three windows covering roughly 150 messages; a fourth C window was
  excluded after the production viewport-anchor retry path accumulated a large
  main-queue backlog and timed out despite falling process RSS.
- The successful RSS-only run used the fresh-install renderer defaults:
  React Native Markdown Display for markdown and selectable-native code blocks.
- Fresh B settled at 507.8 MiB median RSS. B after A settled at 600.5 MiB
  (+92.7 MiB), and B after A+C settled at 591.0 MiB (+83.2 MiB). Reopening A
  and waiting another ten seconds dropped RSS to 444.1 MiB, so the evidence is
  delayed retention and high transient working-set pressure rather than proof
  of an irreversible process-lifetime leak.
- The cached A, B, and C message windows serialize to about 0.94, 1.16, and
  1.26 MiB respectively. Their roughly 3.36 MiB total payload is far smaller
  than the observed 83–93 MiB retained-process delta.
- Normal A traversal did not rise monotonically in every run. The successful
  run peaked at 700.1 MiB overall. A separate stalled anchor-navigation run
  peaked at 846.7 MiB with many 50 ms timers, 85 queued main-thread work items,
  and 19 delayed selectors while no new messages were added.
- Commit `1f527f11` (`Preserve transcript viewport across range navigation`,
  August 14, 2026) introduced the mobile anchor retry. Its `[rows]` effect can
  re-enter `retryAnchorRef.current()` while an animation-frame, measurement, or
  timeout retry is already in flight, while only one timeout handle is tracked.
  The desktop implementation uses a single guarded recursive chain with
  bounded attempts and diagnostics instead of the mobile `[rows]` re-entry.

## Completion Notes

- Outcome: implemented and ran a production-shell, public-HTTP, multi-session
  memory investigation using three real local sessions with 567, 540, and 642
  messages. The final RSS-only Detox run passed in 308 seconds.
- Decisive artifacts:
  - `mobile/crystal-lattice-control-rn/artifacts/detox/memory-investigation/rss-full6-20261018/summary.json`
  - `mobile/crystal-lattice-control-rn/artifacts/detox/memory-investigation/rss-full6-20261018/control-b/process-memory.csv`
  - `mobile/crystal-lattice-control-rn/artifacts/detox/memory-investigation/rss-full6-20261018/multi-session/process-memory.csv`
  - `mobile/crystal-lattice-control-rn/artifacts/detox/memory-investigation/rss-full6-20261018/multi-session/phases.jsonl`
- The valid 30-second fresh-B Allocations trace was moved outside the indexed
  repository workspace to
  `/Users/ferenci84/Library/Caches/CrystalLatticeMemoryInvestigation/full-20261017/control-b-allocations.trace`.
  The interrupted multi-session trace is preserved beside it as
  `multi-session-incomplete-allocations.trace`.
- Verification performed:
  - `npx tsc --noEmit`
  - Prettier checks for all new TypeScript files
  - `npm run detox:build:ios` (`BUILD SUCCEEDED`)
  - Direct real-backend checks confirmed three listed sessions and correct
    final 50-message ranges.
  - Final Detox command completed with one passing test using the dedicated
    iPhone 17 Pro simulator, five A expansions, two C expansions, ten-second
    settle periods, and Allocations disabled.
  - `xcrun xctrace export --toc` confirmed the short control trace is readable.
- Profiling deviation: a long Allocations recording was abandoned after it
  caused a macOS watchdog panic. The panic report recorded `xctrace` at about
  12.1 GiB resident, compressor pages at 98% of limit, compressor segments at
  100%, and 43 swap files. Long runs now default to RSS-only; opt-in traces are
  time- and window-capped.
- Finding: the original cross-session hypothesis is supported for at least a
  ten-second post-switch interval, but the later drop below the control
  baseline means this run does not establish a permanent leak. The clearest
  actionable suspect is the mobile range-navigation anchor retry introduced in
  `1f527f11`, which reproducibly creates retry storms and large transient memory
  growth.
- Deferred scope: no production fix, renderer matrix, physical-device jetsam
  validation, or full-day on-device telemetry was implemented.

## Post-completion follow-up

Status: Approved

The investigation identified the mobile viewport-anchor retry as the clearest
actionable cause. Implement a selectable strategy boundary so the corrected
controller can be compared against both the pre-August simple reload and the
current mobile retry implementation without removing range navigation.

The corrected strategy will port the desktop controller's single-operation
lifecycle rather than copying macOS measurement code. Rows/layout changes may
notify an existing operation, but must never start another animation-frame,
measurement, or timeout chain. Failure must terminate and leave the newly
loaded range at its natural FlatList position.

### Implementation decisions and open questions

- Decision: `single-flight-anchor` is the default.
- Decision: `simple-reload` keeps range loading enabled but performs no explicit
  anchor capture or restoration.
- Decision: `mobile-anchor-v1` preserves the existing implementation for
  diagnostics but is not the default.
- Decision: strategy selection is persisted with existing Development Settings
  and can be supplied directly to the deterministic range-navigation harness.
- Decision: a failed corrected restoration stops without jumping to the visual
  bottom.
- No unresolved requirement questions remain.

### Documentation

- Update mobile development documentation to describe the diagnostic selector,
  safe default, and intended A/B use.
- Keep the setting out of normal user-facing Settings.

### Task checklist

- [ ] Add strategy types, persistence, and Development Settings controls.
- [ ] Route the selected strategy through the production chat/list boundary.
- [ ] Extract the pre-August simple range-loading path.
- [ ] Preserve the current mobile v1 controller behind its diagnostic mode.
- [ ] Implement the bounded single-flight controller and diagnostics.
- [ ] Extend unit/component and Detox coverage for all strategies.
- [ ] Re-run the range-navigation and multi-session memory investigation.
- [ ] Update completion evidence and document follow-up findings.

### Requirement verification

- Strategy selection: persisted-setting tests plus UI component coverage prove
  all three values and the corrected default.
- Simple reload: deterministic range-navigation coverage proves older/newer
  ranges load without invoking explicit anchor restoration.
- Current v1: diagnostic harness coverage proves the current controller remains
  selectable without becoming the default.
- Single-flight: fake-timer/component coverage proves no re-entry under repeated
  row changes, replacement and unmount cancel outstanding work, and timeout or
  max-attempt failure leaves no pending timer.
- Production path: Detox range-navigation coverage proves viewport preservation
  under `single-flight-anchor`; the real-session memory harness compares it
  against the baseline strategies.

### Additional implementation verification

- Run mobile TypeScript and focused Jest suites.
- Build the Release iOS Simulator app.
- Use RSS-only profiling for long stress runs; any Allocations trace remains
  explicitly opt-in and bounded.