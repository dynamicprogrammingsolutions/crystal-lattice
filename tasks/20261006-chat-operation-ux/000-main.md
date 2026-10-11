# Chat progress, composer editing, and send recovery

Correct desktop request progress after tab navigation, align action progress with mobile, and improve request, edit, and failed-send presentation in both applications. The user approved the plan and explicitly requested implementation on 2026-10-06.

## Requirements checklist

- [x] **R1 — Desktop request state:** Returning to a session after switching tabs updates the Send spinner to the actual request state without requiring Refresh.
- [x] **R2 — Desktop actions:** Actions show progress at the top, similar to mobile, and an action in progress does not disable all other actions.
- [x] **R3 — Ordinary requests:** Desktop and mobile show a top progress indicator for ordinary requests as well as actions.
- [x] **R4 — Composer editing:** Desktop and mobile load the selected message into the main composer instead of an inline editor. Warning-colored context above the composer identifies the message index, the send button changes its title, appropriate composer actions are disabled, and submitting the edit shows top progress plus a spinning send button until the edit finishes.
- [x] **R5 — Failed ordinary sends:** Desktop and mobile use a lean notification at the top, in the progress indicator's place, offering Resend and Cancel.
- [x] **R6 — Usable transcript:** During progress, editing, edit submission, and failed-send recovery, users can keep scrolling messages, hide the mobile keyboard, and retain a useful vertical message area.
- [x] **R7 — Isolated native verification:** Implementation and verification run from the separate worktree, with Detox and XCTest coverage of the new workflows, scrolling, keyboard dismissal where applicable, and transcript geometry.

## Approved UX decisions

The user approved all four recommendations on 2026-10-06. These decisions govern implementation and acceptance:

1. **Edit submission and controls:** Recommend **Save edit**, which uses the existing message-modification operation without starting a model response. Show **Editing message [index]**, using the existing canonical zero-based index, plus **Cancel edit**. Disable Append, Append as, Resend, and attachment mutations while editing; retain unrelated settings, actions, navigation, scrolling, and cancellation of an already-running request. The mobile icon button also needs a visible edit title, not only a changed accessibility label.
2. **Draft ownership:** Recommend keeping the ordinary text draft and composer attachments separate from the edit buffer, restoring them after save or cancellation, and retaining edit text on modification failure. Keep edit identity scoped to the connection/session across tab switches; do not introduce a disk-cache migration just for editing.
3. **Recovery Cancel:** Recommend Cancel abandons the local retry workflow and leaves the unsent draft available. It must not claim that an unacknowledged server request was cancelled. A request discovered through reconciliation uses the existing active-request presentation and hard/soft cancellation controls. Confirm this distinction before implementing the Cancel handler.
4. **Layout acceptance:** Recommend a status/recovery row bounded to at most two text lines plus theme padding, a single-line edit-context row, and a transcript minimum of 30% of the usable chat height after keyboard and navigation chrome on the smallest native test size. Preserve those bounds with longer failure text and the largest current typography preset. Confirm these quantitative targets before treating them as acceptance thresholds.

## Supporting details

### Workspace

- Worktree: `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20261006-chat-operation-ux`.
- Branch: `task/20261006-chat-operation-ux`.
- Base: committed `develop` HEAD `953bff41`.
- The original checkout has unrelated uncommitted embedded-runtime/provider-settings changes. They were not copied, modified, or committed.
- Planning left only task files. After approval, worktree-local JavaScript, Python, and native dependencies were provisioned and implementation began.
- Read-only toolchain inspection found Node 20.19.5, Xcode 26.1, and `adb`. Availability does not establish that this new worktree is ready to build.
- Current macOS Debug and Release build settings use the same application bundle identifier. Despite the native-testing page's coexistence claim, inspect running-app conflicts before launch; do not assume choosing Debug alone isolates an ordinary running application.

### Verified findings

- `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx` retains three MRU panes. All retained panes remain active for event polling; older panes unmount and later hydrate from cache.
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` starts with cached messages, cursor, and request ID. Its initial-load effect skips loading when messages or a cursor already exist. There is no corresponding fresh message-load reconciliation on every visible return. The spinner uses `sendInFlight || chatState.activeRequestId`.
- Desktop receives a separately polled `requestStatus`, but uses it only in the header status indicator, not to reconcile the controller's active request.
- `packages/frontend-sdk/src/chat/chatController.ts` has an expired-snapshot-cursor path that bootstraps from the latest event without reloading the request state. `PollingEventSource` also bootstraps from the latest event when started without a cursor. A missed completion can therefore remain absent from the reduced state. `hydrateFromCache` also uses nullish fallback for request IDs, so an explicitly null cached value cannot clear an existing ID.
- **Hypothesis:** stale cache plus missed lifecycle reconciliation explains the reported desktop spinner. The exact user's sequence has not been reproduced. Also test acknowledgement arriving after a completion event: `send` and `sendMessage` currently assign the response request ID without checking whether that request already finished.
- Desktop plugin actions use one `pluginActionRunning` Boolean, disable every header action through that Boolean, and do not render it in a top progress row.
- Mobile renders a top loading row for plugin actions, attachments, and recovery/loading, but ordinary request submission and `activeRequestId` are absent from that row. Mobile also globally disables header actions while a plugin action runs; composer eligibility is already more selective.
- Both apps edit user, assistant, and system content inside message bubbles. Tool results are not editable. Both submit through `ChatController.modifyMessage`, with no dedicated edit-in-flight UI.
- Mobile keeps composer text locally inside `ChatComposer`; its imperative handle currently only reads and clears text. Desktop uses a native `MacTextView` with `setText`, and persists ordinary draft changes through `usePersistedChatDraft`.
- Mobile's failed acknowledgement panel is below the transcript and above the composer. It includes full error text, explanatory implementation text, Check status, and Retry, with no Cancel. The failure also opens an alert. Retry already keeps the original idempotency key. Desktop uses an alert and does not retain an explicit failed-send retry operation.
- The REST adapter already supports caller-supplied idempotency keys. Keep a single key for an ordinary send and its retries.
- Message-list `active_request_id` is derived from the stored checkpoint, whereas `getSessionRequestStatuses` queries the application's current active-request registry. A fresh message snapshot alone is not always sufficient lifecycle authority.
- The optional status query is available in the shipped REST backend. Its authority is `derived_transient`, so it establishes current observed work rather than durable operation history.
- Existing native notification tests demonstrate reading actual native frames. Existing transcript tests demonstrate production list scrolling. They do not prove these requested workflows.

### Maintained references

- Desktop behavior: `desktop/crystal-lattice-control-desktop-rn/docs/development/session-chat-controls-and-actions.md`, `desktop/crystal-lattice-control-desktop-rn/docs/development/home-workspace-and-tabs.md`, and `desktop/crystal-lattice-control-desktop-rn/docs/development/native-ui-testing.md`.
- Mobile behavior: `mobile/crystal-lattice-control-rn/AGENTS.md`, `mobile/crystal-lattice-control-rn/docs/development/session-chat-composer-and-actions.md`, and `mobile/crystal-lattice-control-rn/docs/development/notification-presentation.md`.
- Shared contracts: `packages/frontend-sdk/docs/session-request-status.md`, `packages/frontend-sdk/docs/development/request-cancellation.md`, and `packages/frontend-rn-components/docs/development/theme-contract.md`.
- Real-backend harness: `packages/frontend-sdk/src/integration/harness.ts`. Its Python runner resolves core/application source from its own worktree. Native production-flow examples are desktop `__native__/humanTimeTelemetry.native.test.ts` and mobile `e2e/humanTimeTelemetry.e2e.test.ts`.

## Subtasks

- [x] `tasks/20261006-chat-operation-ux/010-request-and-action-progress.md` — R1, R2, R3; owns shared status presentation and native/HTTP test foundations.
- [x] `tasks/20261006-chat-operation-ux/020-composer-message-editing.md` — R4; depends on 010.
- [x] `tasks/20261006-chat-operation-ux/030-compact-send-recovery.md` — R5; depends on 010 and 020 so recovery composes with the final composer modes.

R6 and R7 are owned by the explicit combination of all three children. Each child must prove its own workflows at the native boundary; there is no separate testing or documentation child. Execute 010, then 020, then 030 because all change the same chat hosts and coordinated native suites.

## Execution plan
Status: Approved

### Design and ownership

The shared SDK controller owns request IDs, lifecycle reduction, cursor recovery, and reconciliation with current backend state. Desktop and mobile own visibility/resume policy, composer mode, draft ownership, action operations, and platform text/keyboard controls. A small shared React Native component presents a bounded top status row using the existing theme, while each host supplies its session-scoped activity and recovery data.

Use separate tracked activities for request submission, active generation, message modification, and application actions. Derive both the top row and send-button spinner from the same relevant activities. The send spinner covers request submission/generation and edit submission; unrelated plugin actions get top progress without falsely turning Send into a request spinner. Replace the single plugin-action Boolean with operation identities so one concurrent action finishing cannot hide another. Disable only the operation's duplicate trigger and existing contract-specific conflicts.

The top row is in normal layout above the transcript. It does not intercept transcript gestures or place a modal over the screen. Failed-send recovery uses that same slot. Multiple activities summarize into bounded text rather than stacking rows. Existing server/plugin notification rails keep their current ownership and dismissal semantics.

Preserve event polling for warm desktop tabs. Add visibility/remount reconciliation rather than extending every pane's lifetime or increasing the MRU bound. Reconcile fresh supported request-status data against the current controller generation/request identity so an old response cannot clear a newly started request. Keep cached messages visible and preserve history range, scroll affinity, read-only snapshots, and ordinary draft state during refresh. When a backend lacks optional status support, retain existing message/event recovery; do not infer completion from elapsed time or an unavailable read.

Use the existing modify endpoint for composer editing. The approved composer policy will decide which controls remain available. Do not replace role, metadata, or multipart content through an ordinary append/send path. Failed sends capture the exact original payload and idempotency key before submission, and retry through the production REST adapter.

No backend route, persisted storage schema, application identifier, release, hosted-provider requirement, or production-server change is proposed. If reproduction proves a backend defect or requires a new public shared interface, record it and obtain approval for that material change.

### Execution order and evidence

1. Resolve the four UX decisions above; mark the agreed parent and child plans Approved only after authorization to implement.
2. Provision dependencies and native build outputs in this worktree, using the package setup commands. Confirm Metro, TypeScript workspace resolution, Python imports, fixture paths, and bundled JavaScript all refer to this checkout. Do not reuse another checkout's app binary as acceptance evidence.
3. Execute each child with its component/controller regressions, real HTTP checks, native scenarios, and maintained documentation. Update checklists as each item gains evidence.
4. Run focused Detox suites on iOS and Android and the focused macOS XCTest suite sequentially for UI execution. Builds may run in parallel. Long builds/runners run in the background with captured logs and process IDs.
5. Record per-platform command, collected scenarios, result, screenshots, and any blocked evidence. A skipped, uncollected, or teardown-failing run is not a success. Do not waive HTTP or native coverage in favor of separate mocked tests.

Shared decisive test entry points to create:

```bash
# Workdir: packages/frontend-sdk
npx vitest run --config vitest.integration.config.ts src/integration/__tests__/chatRequestRecovery.integration.test.ts

# Workdir: desktop/crystal-lattice-control-desktop-rn
npm run test:integration -- --runTestsByPath __integration__/ChatOperations.realBackend.integration.test.tsx
npm run test:macos-ui:chat-operations

# Workdir: mobile/crystal-lattice-control-rn
npm run test:integration -- --runTestsByPath __integration__/ChatOperations.realBackend.integration.test.tsx
npx detox test -c ios.sim.release e2e/chatOperations.e2e.test.ts --cleanup
scripts/prepare_android_detox_emulator.sh
npx detox test -c android.emu.e2e e2e/chatOperations.e2e.test.ts --cleanup
```

The new desktop script will run `__native__/chatOperations.native.test.ts` through the existing native Jest configuration. That runner starts a real local backend and invokes the existing XCTest target, focused to a new `ChatOperationsUITests` class, using bundled Debug JavaScript and worktree-local DerivedData. Deterministic state may seed ordinary sessions, connection records, and temporary local plugins; request/edit operations must still traverse the production screen, controller, REST adapter, and public HTTP routes.

Use shared fixtures under `test/fixture/chat-operations/` only when both native hosts consume them. Delayed actions use an actual application-plugin action, not a fake action result in the screen. Network-failure fixtures use a host-side forwarding HTTP proxy to interrupt acknowledgement at the transport boundary while leaving backend operations real. Do not add a test-control shortcut to the application path.

### Implementation decisions and open questions

- All four UX decisions were approved on 2026-10-06 together with explicit implementation authorization.
- The spinner's exact triggering sequence remains uncertain. Test retained hidden panes, eviction after visiting at least three other sessions, missing/expired cursors, server restart/event retention, fast completion before acknowledgement, success, fatal error, and cancellation. Select the smallest correction supported by the failing regression.
- Request-status responses can race with sends, edits, and event delivery. The controller must reconcile current observations without clearing newer work or resurrecting completed work.
- Concurrent actions require independent identities. Keep backend-declared disabled states and request duplication guards; do not add a client-side global mutation lock.
- Editing and recovery must preserve the ordinary draft and attachments. Any need to persist new edit/recovery schemas is a material scope change.
- Existing macOS testing guidance prohibits terminating a running Crystal Lattice process. Use the existing Debug test application and inspect running-app conflicts before launch, including an ordinary Release instance because the build identifiers currently match. Report a specific conflict; do not kill the existing application. Native tests and simulator automation share focus and must execute sequentially.
- Human UX review remains separate from automated frame and interaction evidence. Only record human verification after confirmation.

### Documentation

Update the existing desktop controls/actions and tab-state developer pages, mobile composer/actions page, and both notification-presentation pages where changed behavior is owned. Document request reconciliation with the SDK if controller behavior changes and the new row contract with shared React Native components. Extend desktop native testing documentation and mobile test instructions with the focused commands and coverage limits. Use the existing pages; no new specification tree or documentation restructuring is proposed.

### Task checklist

- [x] Obtain decisions and explicit implementation authorization.
- [x] Mark approved execution plans and provision this worktree for testing.
- [x] Complete 010, including its HTTP/native evidence and documentation.
- [x] Complete 020, including its HTTP/native evidence and documentation.
- [x] Complete 030, including its HTTP/native evidence and documentation.
- [x] Confirm all three platform suites meet the approved geometry and interaction criteria.
- [x] Update parent requirements from evidence and record completion with remaining blockers or human review.

### Requirement verification

| Requirement | Owner and decisive evidence |
| --- | --- |
| R1 | 010: real HTTP/controller recovery regression plus macOS production tab-switch/eviction test, with no Refresh action. |
| R2 | 010: delayed real plugin action visibly in progress while another eligible production action works; macOS top-row visibility and transcript wheel interaction. |
| R3 | 010: ordinary submission and generation lifecycle through public HTTP and production adapters; Detox iOS/Android and XCTest verify top row plus spinner and automatic completion. |
| R4 | 020: native message-action → main composer → public modify route → updated transcript; index, warning context, visible title, approved disabled controls, progress, cancellation, and failure behavior. |
| R5 | 030: production send interrupted at HTTP acknowledgement → compact top recovery → Resend/Cancel; real backend verifies retry does not duplicate the original payload/request. |
| R6 | 010 + 020 + 030: actual mobile swipes and macOS wheel movement in each workflow, keyboard show/hide on iOS/Android, native frame bounds at small viewport/largest typography and with long error/edit text. |
| R7 | All children: successful focused Detox iOS/Android and XCTest commands built and run from this worktree, with collected scenarios and artifacts recorded. |

### Additional implementation verification

Run affected SDK/controller, shared component, and host Jest tests, plus each changed package's TypeScript checks. Re-run existing native transcript-range and rich-composer cases where the new row or editing changes affect their boundaries. Check scoped status isolation between two sessions and two connections, cache null precedence, read-only snapshot eligibility, ordinary draft persistence, and hard/soft cancellation eligibility. Broader provider or remote deployment suites are not needed for these frontend workflows unless a discovered change crosses those boundaries.

## Implementation Notes

- Implementation is in progress in the designated worktree. No commit was requested or created.
- Five controller regressions failed before correction: stale checkpoint state on resume, explicit-null hydration, both send acknowledgement/completion races, and a pending recovery query. Those five plus ten existing controller tests passed after correction. Two focused real-HTTP controller recovery tests also passed.
- A further desktop cache regression demonstrated that `updateMessagesCache` retains a completed request ID because it uses nullish fallback. Explicit null request IDs and cursors now replace previous values; all three cache-hook tests pass.
- Shared activity/edit-context components and a connection/session-scoped transient workspace now support request progress, independent action operations, composer edits, and original-payload send recovery. Workspace state stays above desktop pane eviction and mobile session switching; no persisted schema was added.
- Existing desktop rich-composer tests (4), desktop tab-stack tests (4), mobile rich-composer/transcript tests (6), and the focused controller/cache checks passed. New full host HTTP integration suites are being debugged and rerun; do not count them complete yet.
- Native builds started in the background: macOS build-for-testing PID 86333, iOS Detox build PID 86194, Android Detox build PID 86195. Logs are `/tmp/clc-chat-operations-desktop-build.log`, `/tmp/clc-chat-operations-ios-build.log`, and `/tmp/clc-chat-operations-android-build.log`.
- macOS XCTest launch remains blocked by the installed `/Applications/Crystal Lattice Desktop.app` process (observed PID 87823) sharing the target bundle identifier. It was not terminated. The new native runner reports the conflict before launching; compilation proceeds independently.
- macOS CocoaPods setup needed the worktree's Ruby 3.4.10 bundle and its installed Ruby pod script rather than the Homebrew shell wrapper. Pods are installed. Fixture plugin installation now copies the three maintained Python package inputs into a temporary directory per server to avoid concurrent setuptools builds writing to the same fixture source tree.
- Current verification: all 481 shared frontend fast tests pass; focused desktop host regressions (12) and mobile host regressions (22) pass; both hosts type-check. The full HTTP suites pass 4 desktop and 3 mobile cases, including edit cancellation, ordinary draft restoration, original-key retry, and metadata preservation. Multipart preservation was subsequently added and exposed the core issue below; its updated runs also pass.
- iOS Detox passes all three production HTTP/native workflows on iPhone 16e with the largest typography preset, physical transcript movement, Hide keyboard, and the 30% transcript floor.
- macOS build-for-testing succeeded, but the focused native runner was blocked before launch by the installed desktop process. An intermediate process-list interpretation incorrectly suggested that blocker cleared; the guarded runner established that it had not. The installed application was not terminated.
- Android API 36.1 repeatedly raised System UI ANRs. Two isolated AVDs were created without changing the shared device: `CLC_Chat_Operations_20261006` (API 36.1) and `CLC_Chat_Operations_API35`. The stable API 35 image is installed and the suite is running there. Android's real first-launch full-screen confirmation is dismissed through its UIAutomator-reported Got it button; Detox's `system` interaction API is unsupported on Android.
- The approved content-only edit preservation check exposed a core bug: `_modify_single_message_with_native` omitted the target's `multipartContent` when converting the edited message back to provider history. A two-line contract-preserving correction now includes that existing field. No backend route, public signature, persisted schema, or generation policy changed. Three role regressions failed before the fix and pass afterward; 44 focused core/history tests pass. Hosted-provider follow-up was considered: this correction preserves existing input to the unchanged provider converters, so the offline real echo/deterministic paths and retained-history checks are the selected evidence.
- Final geometry and native verification are still in progress. Do not mark desktop XCTest or Android Detox successful until their collected workflows exit successfully.
- The desktop native runner now uses a generated-test-build bundle identifier override and passes that identity to `XCUIApplication`. This is an operational isolation choice under the approved native testing scope; no maintained application identifier, user preferences domain, or production binary was changed. The installed process remains running and the actual desktop UI/HTTP test has launched alongside it. Native assertion issues are being resolved.
- Android native frame assertions normalize the inverted list's transformed origin and physical-pixel scale. Gestures target a visible production row. Long deterministic requests remain active through the interaction checks and are ended through the production Cancel control; iOS retains natural-completion coverage. The Android transport can retry disconnected sockets internally, so its recovery case injects a real HTTP 503 after backend acceptance while retaining the original key/payload.
- Android's activity already uses `adjustResize`; redundant chat keyboard-height padding was removed to retain the approved message area.
- Native macOS measurements exposed a real zero-height transcript at the approved small window size. The production pane now uses compact header/composer controls below 650 points, a bounded scrolling notification rail, and a transcript height reservation. Initial request/wheel/geometry checks advance beyond that failure; complete native workflows remain pending.
- Warm hidden desktop panes now use `display: none` while staying mounted and polling. This prevents hidden panes from exposing overlapping native accessibility controls; explicit accessibility hiding alone was insufficient on macOS.
- Native keyboard tests now explicitly show the keyboard and wait for the production Hide keyboard control to disappear after dismissal. The mobile control is visible only while the keyboard is shown, and its state clears on `keyboardDidHide`, avoiding gestures against a moving composer.
- Android native screenshots established that the immersive activity's declared `adjustResize` does not keep the composer above the IME. Both normal and expanded production composers now use Android keyboard avoidance by height; the native dismissal/scroll checks remain intact.
- The final stale-snapshot regression failed for both Send entry points: a message reload restored a checkpoint request ID already observed as completed, and the late acknowledgement correctly refused to restore it but left that stale reload value behind. Reloads now discard IDs in the controller's completed-request set. This extends the original spinner correction without changing the backend contract.

### Current verification — October 10, 2026

- All 481 shared frontend fast tests, 44 focused core/history tests, 12 desktop component tests, and 22 mobile component tests pass. Both hosts type-check; Ruff, the new Python test's Black check, and `git diff --check` pass.
- Both complete real-HTTP component suites pass (desktop 4, mobile 3). They include rejected-save retention, successful edit and cancellation, ordinary draft restoration, role/metadata/multipart preservation, original-key retry, recovery Cancel, and independent desktop action execution. The desktop retry needs an asynchronous React `act` boundary around the real acknowledgement; no backend success is mocked.
- The SDK HTTP suite passes all 3 cases after the completed-checkpoint reload correction. Both Send regressions failed before that correction, and the entire 380-test SDK suite passes afterward.
- Android previously passed all 3 complete native workflows on `CLC_Chat_Operations_API35`. The final controller change, edit-navigation assertions, and editor-specific keyboard dismissal need a final run against the rebuilt binary; prior results are not final evidence for those additions.
- iOS previously passed the original 3 workflows. The stricter final dismissal check exposed a keyboard that stayed open. Both editors now blur their own input explicitly; iOS uses the established touch-down dismissal pattern, and Hide keyboard is a separate toolbar control. The current focused iOS request case still fails waiting for dismissal. This remains unresolved; prior native success does not prove the final keyboard contract.
- macOS earlier reached and verified request completion while its pane was evicted, edit cancellation/restoration, edit retention across eviction, and pending-save progress/geometry. The complete XCTest workflow has not passed yet; wheel movement after restoration and remaining action/recovery cases still need a complete successful run.
- The latest macOS run failed before interactions because the host screen is locked (`CGSSessionScreenIsLocked = 1`) and XCTest cannot activate the isolated AUT. Final macOS verification requires an unlocked interactive desktop. The installed application was not terminated.
- Native builds must run sequentially when using the default Metro temporary cache: a simultaneous reset produced `ENOTEMPTY` during bundling. No shared cache cleanup was performed.
- Keep native requirements and completion checklists open until current binaries and complete collected commands pass. Human UX review has not been performed. No commit or deployment is authorized.
- The final Android rerun is also incomplete. An earlier revision passed all 3 workflows; the latest command fails keyboard-visible readiness and retry completion checks. Other retries encountered emulator setup overlays/ANRs. Diagnose the current failure from `/tmp/clc-chat-operations-detox-android.log`, keeping real gestures and the approved viewport checks.
- Temporary keyboard diagnostic logging was removed from production source. The latest iOS diagnostic binary needs rebuilding from the clean source before final acceptance. Both hosts' type checks and component checks pass after the UI changes; the real-HTTP suites remain passing.

### Verified native progress — October 10, 2026, evening

- The desktop is available again. `npm run test:macos-ui:chat-operations` passes the complete XCTest method, public-backend postconditions, and teardown (exit 0). Result: `desktop/crystal-lattice-control-desktop-rn/build/chat-operations/Logs/Test/Test-CrystalLatticeControlDesktopRN-macOS-2026.10.10_21-19-41-+0200.xcresult`. R1–R5 have decisive desktop native/HTTP evidence; R6/R7 still require final Android acceptance.
- The complete iOS Detox command passes all 3 workflows and teardown (exit 0) on iPhone 16e, including edit navigation retention, physical scrolling during saving, keyboard dismissal, retry/cancel, top placement, and the 30% transcript floor. Artifacts: `mobile/crystal-lattice-control-rn/artifacts/detox/ios.sim.release.2026-10-10 19-13-50Z/`.
- iOS `replaceText` produced inconsistent focus state. Native interaction now focuses the real editor and types through the keyboard; layout readiness uses repeated actual frame reads before measurements. The existing iOS text-editing overlay behavior permits a bounded second tap on the same production control. No fake acceptance or alternate backend path was introduced.
- Desktop small-pane composition uses a 48-point input cap with internal text scrolling and horizontal Send title/spinner layout. Recovery and saving meet the retained quantitative checks.
- Temporary accessibility/focus diagnostics are removed. Android's final suite is the remaining verification step; do not append completion notes until it exits successfully.

## Completion Notes

Completed on October 10, 2026 in the designated worktree. R1–R7 are verified
through the shared controller regressions, production app components and
adapters over public HTTP, and complete native commands. No commit, merge,
deployment, or production-server operation was performed.

| Evidence | Final result |
| --- | --- |
| Shared SDK / SDK React / RN component fast suites | 380 / 25 / 76 passed |
| Focused core/history suite, including retained multipart edits | 44 passed |
| Desktop / mobile component regressions | 12 / 22 passed |
| Desktop / mobile production HTTP component suites | 4 / 3 passed |
| SDK HTTP recovery and edit acknowledgement suite | 3 passed |
| macOS `npm run test:macos-ui:chat-operations` | 1 complete XCTest workflow, backend postconditions, and teardown passed; exit 0 |
| iOS `DETOX_IOS_DEVICE_ID=702458A4-A7AF-4116-9593-CBE1607C26BF npx detox test -c ios.sim.release e2e/chatOperations.e2e.test.ts --cleanup` | All 3 workflows passed; exit 0 |
| Android `DETOX_ANDROID_AVD=CLC_Chat_Operations_API35 npx detox test -c android.emu.e2e e2e/chatOperations.e2e.test.ts --cleanup` | All 3 workflows passed; exit 0 |
| Both app TypeScript checks; Ruff; new Python test Black check; diff whitespace check | Passed |

The native checks exercise actual wheel/swipe movement, production keyboard
dismissal, pending-save scrolling, navigation/eviction retention, compact
recovery, and the retained 30% transcript floor at the small viewport/largest
typography preset. Public backend inspection verifies content-only edits and
retry without duplicating the original payload. The ordinary desktop request
finishes while its pane is evicted, and returning clears progress without
Refresh. A second eligible desktop action works while another is pending.

Maintained documentation is updated in the owning SDK, shared component,
desktop, and mobile pages. The necessary core correction preserves existing
multipart data without changing routes, provider signatures, or persisted
schemas. Short desktop panes use compact chrome and bounded notification/text
scrolling; Android fullscreen composition uses keyboard avoidance. These are
in-scope corrections discovered by realistic native checks.

Failed/interrupted intermediate runs are not completion evidence. The Mac was
unlocked for final XCTest; installed applications were not terminated.
API 36.1 emulator ANRs required the isolated API 35 device. iOS typing follows
the real keyboard focus path, and native geometry reads wait for settled
frames. Temporary diagnostics are removed.

Native result: `desktop/crystal-lattice-control-desktop-rn/build/chat-operations/Logs/Test/Test-CrystalLatticeControlDesktopRN-macOS-2026.10.10_21-19-41-+0200.xcresult`.
The desktop review attachment is exported under
`desktop/crystal-lattice-control-desktop-rn/build/chat-operations-review/`.
Final command logs are `/tmp/clc-chat-operations-xctest.log`,
`/tmp/clc-chat-operations-detox-ios.log`, and
`/tmp/clc-chat-operations-detox-android.log`. Human UX review and iOS
three-finger editing gestures have not been claimed as verified. Hosted
provider/deployment suites were not needed for these frontend/local-history
changes.

## Post-completion follow-up

On October 11, 2026, the user authorized committing the completed changes,
merging them into `develop`, and removing the separate worktree. Integration
will preserve the newer `develop` changes and retain the available native
verification reports in the main checkout's ignored artifact directory.

The feature commit was rebased onto `develop` at `be152f84`. Two additive
desktop documentation conflicts preserve both the newer action-display
guidance and this task's Chat behavior. Integration also unifies the iOS
launch-properties dictionary with the newer embedded-provider harness and
supplies the newly required connection-wizard close callback in the Chat
native harness.

Merge-time verification in the worktree passes: shared SDK/SDK React/RN
component suites 387/25/76; focused core/history 44; desktop components 12;
mobile components including connected navigation 28; desktop/mobile public
HTTP component suites 4/3; both app TypeScript checks; Swift bootstrap syntax
parse; and diff whitespace checks. These are integration checks; the native
workflow evidence remains the completed October 10 runs above.

Available iOS native trace evidence and merge-time logs are retained at
`artifacts/chat-operation-ux-20261011/` in the main checkout (ignored).
The original `/tmp` logs and generated macOS result had already been removed
before this merge request; their verified outcomes remain in Completion Notes.