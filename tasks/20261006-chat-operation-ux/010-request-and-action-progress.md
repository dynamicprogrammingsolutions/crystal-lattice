# Request and action progress

Fix desktop request state on session return and provide shared, bounded request/action progress on desktop and mobile without disabling unrelated actions.

Parent Task: tasks/20261006-chat-operation-ux/000-main.md

## Requirements checklist

- [x] **P1 (R1):** Desktop Send progress reconciles automatically when returning to a session after tab switching.
- [x] **P2 (R2):** Desktop actions show top progress and leave unrelated eligible actions usable.
- [x] **P3 (R3):** Ordinary requests show top progress on desktop and mobile throughout submission and active generation.
- [x] **P4 (R6, R7):** These workflows retain native transcript scrolling, mobile keyboard dismissal, and useful transcript height, verified with Detox iOS/Android and macOS XCTest from the designated worktree.

## Open questions

The parent layout acceptance targets were approved on 2026-10-06. Exact reproduction of the intermittent spinner remains an investigation item; the known stale-cache/event-recovery paths establish a test direction, not a reproduced diagnosis.

## Supporting details

Desktop's three-pane MRU stack keeps retained hidden panes polling and remounts evicted panes from cache. A nonempty cache skips the fresh initial message load. The controller's expired snapshot cursor can restart at latest event without reconciling its request ID. Send acknowledgement can also overwrite lifecycle state after a fast completion.

The shipped REST request-status query can supply current active work. Message-list request IDs are checkpoint-derived. The separately polled desktop header status does not currently feed the Send spinner. Preserve optional backend compatibility.

Desktop plugin-action progress is currently a Boolean used as a global header-action disable condition. Mobile has a top action/loading row but also disables header actions through a global action Boolean. Both hosts already preserve many composer actions during ordinary active requests.

## Execution plan
Status: Approved

### Design

Correct request lifecycle and reconciliation in the shared controller using existing recovery APIs, event reduction, and optional fresh request-status reads. Desktop visibility/remount triggers recovery while retaining cached transcript content and scroll state. Use generation/request checks to keep delayed responses from clearing a newer request or recreating a completed one. Exercise the cache's explicit-null behavior only through a real consumer as well as focused controller coverage.

Introduce the shared themed top status row in `packages/frontend-rn-components`, consumed by `ChatPane` and `SessionChatScreen`. Inputs carry activity labels/counts and an optional recovery presentation to be used by 030. Request submission and generation derive from the same state as Send progress. Action activities use independently tracked operation tokens and labels; clear only the operation that finished.

Remove global plugin-action disable conditions from both hosts. Keep backend-disabled actions, duplicate request guards, and a duplicate trigger guard for the same action/context. Independent actions and ordinary reading/navigation remain available; do not create a queue or new backend concurrency policy.

This child owns the common real-backend/native fixtures, top-row layout, native test runner, and test-suite entry points listed in the parent. Children 020 and 030 extend these consumers and suites after this delivery.

### Verification design

First establish a failing regression through the real `ChatPaneTabStack` or shared controller. Then prove the correction through production HTTP adapters and macOS tab switching. Include a tab retained in the warm set and one evicted after at least three other tabs are visited. Complete the request while away and return without Refresh; verify no spinner or top-progress state remains after reconciliation. Repeat for a request still running, fatal error, and cancellation.

Test expired or missing cursors and completion before a delayed send acknowledgement at the HTTP boundary. A fake completion supplied directly to the UI is insufficient decisive evidence.

For action concurrency, use a local fixture application plugin reached through ordinary UI action discovery/execution. Hold one action long enough to observe its progress, invoke another eligible action, and verify that the first completion cannot clear the second activity. Use production settings/action controls and actual backend results.

Native scrolling checks use a gesture or wheel event over visible transcript content while work is active; verify message movement or a change in visible message identities. On iOS and Android, focus the composer, hide the keyboard through a production interaction, and verify the expanded transcript. Measure actual native bounds at the approved smallest viewport and typography preset, not just React style values.

### Implementation decisions and open questions

- Apply the approved parent top-row height and transcript floor. Multiple concurrent activities summarize in one bounded row.
- Keep lifecycle authority in the controller. A potentially stale header status prop alone must not clear request state.
- Retain existing no-status-support recovery behavior. Do not interpret missing capability, an unavailable query, or a timer as evidence that a request completed.
- Public API changes beyond existing recovery/status contracts or a backend fix require renewed approval.
- Native workflows run on production screens. Deterministic harnesses may prove local layout but do not replace the named HTTP/native flow.

### Documentation

Update desktop controls/actions and tab ownership, mobile composer/actions, SDK request reconciliation documentation where changed, shared component contract documentation, and both hosts' focused native-test instructions.

### Task checklist

- [x] Reproduce and record the lifecycle regression with failing focused evidence.
- [x] Fix controller reconciliation/acknowledgement and desktop visibility/remount recovery.
- [x] Add the common top row and independently tracked action activities in both hosts.
- [x] Remove global action disabling while retaining scoped guards.
- [x] Add real HTTP regressions and common production native-flow test fixtures/runners.
- [x] Run macOS request-return/action cases and Detox request/action cases on iOS and Android.
- [x] Record scroll, keyboard, geometry evidence and update maintained documentation.
- [x] Update parent R1–R3 and this child's R6/R7 contribution from evidence.

### Requirement verification

- **P1:** `chatRequestRecovery.integration.test.ts` through `FetchTransport`, `RestAgentBackend`, and `ChatController`; desktop `ChatOperations.realBackend.integration.test.tsx` through production `ChatPaneTabStack`; XCTest request-return scenarios through production tabs. Run the exact focused commands in the parent.
- **P2:** Delayed plugin action and independently completing second operation through public action HTTP routes; XCTest checks visible progress and usable unrelated action, supported by both hosts' component regressions.
- **P3:** Detox `e2e/chatOperations.e2e.test.ts` on iOS/Android and XCTest `ChatOperationsUITests` observe top status and Send spinner through submission/generation and their automatic removal.
- **P4:** Those native cases include physical transcript movement, mobile keyboard dismissal, and native frame measurements during request/action work.

### Additional implementation verification

Run SDK streaming reducer/controller and event-source tests, shared React/component tests, affected desktop tab-stack/rich UI tests, mobile rich UI tests, and TypeScript checks. Check two-session isolation, explicit-null cache handling, cursor expiry without an active request, non-tail history ranges, and read-only snapshots.

## Implementation Notes

- The shared controller now reconciles supported current request status on resume/cursor recovery and acknowledgement, remembers completed request IDs, and protects against older status responses clearing newer work. Desktop visible return initiates recovery, including remounted cached panes.
- Desktop cache updates now accept explicit null request IDs/cursors. A cache-hook regression failed before the fix and passes afterward.
- The top row and independently tracked application actions are implemented in both hosts. Native runners and HTTP fixtures exist; native compilation and host HTTP checks continue. Parent requirements remain unmarked until decisive verification completes.
- The complete SDK HTTP suite (3), desktop HTTP suite (4), and mobile HTTP suite (3) pass. A further terminal-checkpoint regression failed for both Send methods and now passes: message reloads cannot restore a controller-known completed ID.
- Native acceptance is still open. The latest macOS launch is blocked by a locked desktop; mobile final runs have unresolved keyboard/retry assertions. The parent's current-verification section is authoritative.
- Complete macOS XCTest plus backend postconditions and iOS Detox now pass (exit 0). Request completion while the desktop pane is evicted clears the spinner on return without Refresh; a second real action stays usable during a slow action. Final Android acceptance remains open.

## Completion Notes

Completed October 10, 2026. P1–P4 and parent R1–R3 are verified. Complete
macOS XCTest/HTTP postconditions and all 3 iOS plus 3 Android Detox cases
pass with exit 0 and clean teardown. Actual scrolling, keyboard dismissal,
top request/action status, and the approved geometry bounds are exercised.
Controller/cache regressions and all 481 shared frontend fast tests pass.
Maintained controls, tab-state, notification, SDK reconciliation, and focused
native-test documentation are updated. Final commands, artifacts, and
verification limits are recorded in
`tasks/20261006-chat-operation-ux/000-main.md`. No remaining scope or
authorization question; no commit or deployment performed.