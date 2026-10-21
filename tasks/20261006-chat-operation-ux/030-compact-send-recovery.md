# Compact failed-send recovery

Replace ordinary-send failure alerts/panels with compact top recovery offering Resend and Cancel, integrated with the final composer modes.

Parent Task: tasks/20261006-chat-operation-ux/000-main.md
Depends On: tasks/20261006-chat-operation-ux/010-request-and-action-progress.md, tasks/20261006-chat-operation-ux/020-composer-message-editing.md

## Requirements checklist

- [x] **F1 (R5):** Failed ordinary sends show a lean top notification in the progress slot on desktop and mobile, offering Resend and Cancel.
- [x] **F2 (R6, R7):** Failure and recovery preserve scrolling, keyboard dismissal, and useful transcript height, proven through Detox iOS/Android and macOS XCTest from the worktree.

## Questions requiring approval

Parent decisions 3 and 4 were approved on 2026-10-06. Cancel dismisses local recovery while retaining the draft; it does not imply cancellation of server work.

## Supporting details

Mobile's existing `PendingRequestRecovery` captures the send kind, original payload, idempotency key, and error. Retry uses that same key; the panel currently includes full details plus Check status and Retry, and failure also opens an alert. Desktop retains the draft after an alert but lacks the explicit pending operation.

The REST adapter generates an idempotency key when callers omit it; safe retries need a captured caller-supplied key. A lost acknowledgement can occur after the real backend accepts and even finishes the request. Current request status is not durable idempotency-operation history.

## Execution plan
Status: Approved

### Design

Capture the original ordinary-send payload and idempotency key before submitting. Use equivalent recovery state in both hosts and share small recovery helpers in an appropriate frontend package when both consume them. Treat acknowledgement failure separately from a provider fatal error delivered for an accepted request.

Supply compact failure presentation to the shared top row from 010. Show a short bounded summary plus **Resend** and **Cancel**, without a second recovery panel or a blocking alert for this workflow. Long error detail cannot expand the row or place a touch surface over transcript content. Keep diagnostic detail out of the product's main flow.

Resend reuses the original payload and key, including multipart content and config overrides. It is independent of later draft changes and uses the existing production send method. Guard repeated retries; switch the top row into progress while retrying and return to recovery if acknowledgement fails again. If reconciliation discovers the accepted active request, use the normal request indicator and cancellation controls.

Implement Cancel according to the approved parent semantics. Keep recovery identity isolated by connection/session and ensure a late result cannot re-open a dismissed recovery, erase a newer draft, or clear another request. Do not use unrelated current work as proof that the original send succeeded.

Preserve normal draft/edit separation from 020. Retry must not submit an edit buffer as a new user message. Existing application/session notification rails retain their behavior. The recovery UI consumes the ordinary status slot even if unrelated actions are active, summarizing additional activity without growing vertically.

### Verification design

Run a real local backend behind a forwarding HTTP proxy. Cover connection failure before acceptance and acknowledgement interruption after acceptance, including a request that finishes before Resend is tapped. Drive the production send/retry UI and inspect public backend messages/events to prove that the original user payload and request are not duplicated on retry.

Use long error text and multipart content. Exercise Resend success, repeated failure, repeated Resend taps, the approved Cancel behavior, a newly discovered running request, later draft changes, and navigation away/back. Validate operation identity rather than merely checking that some `activeRequestId` exists.

In Detox and XCTest, verify the recovery row is above the transcript and the obsolete panel/alert is absent. Swipe/wheel over messages while failure is visible and retry is pending. Show/hide the mobile keyboard in both states. Measure row/composer/transcript native frames at the approved small size and largest typography preset, capturing review screenshots.

### Implementation decisions and open questions

- The local-recovery Cancel policy was approved with the parent plan. Existing hard/soft cancellation remains the operation for known accepted work.
- Keep the original idempotency key for retries. Never reconstruct a retry from current editor text.
- Do not claim that a non-running transient status proves whether an unacknowledged operation was accepted. Add only behavior justified by the approved cancellation policy and existing public APIs.
- If cross-navigation recovery needs a new persisted schema or backend idempotency-status lookup, return that material decision for approval.
- New shared helpers must have real desktop and mobile consumers. The proxy forwards ordinary public HTTP routes and must not synthesize success or inject internal backend state.

### Documentation

Update both hosts' existing notification-presentation and composer/actions pages with ordinary-send recovery, Resend, the approved Cancel meaning, and the distinction from active-request cancellation. Extend native test instructions with transport-failure cases and coverage boundaries.

### Task checklist

- [x] Confirm the parent Cancel and geometry decisions.
- [x] Add explicit pending ordinary-send identity/payload/key capture to desktop and align mobile state.
- [x] Replace recovery panel/ordinary-send alerts with the common compact top presentation.
- [x] Implement guarded Resend and approved Cancel with draft/edit/session isolation.
- [x] Add before-/after-acceptance HTTP proxy scenarios and real-backend duplication checks.
- [x] Extend and run Detox iOS/Android and XCTest failure/retry/cancel/navigation scenarios.
- [x] Record native scroll, keyboard, geometry evidence and update maintained documentation.
- [x] Update parent R5/R6/R7 evidence and finalize the combined workflow verification.

### Requirement verification

- **F1:** Both real-backend component suites and production native suites run the public send failure/retry path; native assertions verify top placement and Resend/Cancel. Real backend messages/events prove retry reuses the original operation without duplication.
- **F2:** Native failure and retry cases demonstrate physical transcript movement, approved viewport bounds, and mobile keyboard dismissal. Use the exact focused HTTP, Detox, and XCTest commands recorded in the parent.

### Additional implementation verification

Run affected send/recovery/controller tests and TypeScript checks. Verify ordinary request progress and edit save still work after recovery, simultaneous unrelated action activity remains visible, fatal provider errors retain their existing lifecycle semantics, and background test servers/proxies stop cleanly without timer or teardown errors.

## Implementation Notes

- Both hosts capture the original ordinary-send payload and caller-supplied idempotency key. The shared compact row supplies Resend and local Cancel; send failures no longer open a blocking alert or the old large mobile recovery panel.
- Retry clears the ordinary draft only when it still matches the retried payload. Later draft changes stay intact. Recovery is not discarded merely because an unrelated current request is observed.
- Host HTTP suites and native fault scenarios use an actual forwarding proxy, including before-acceptance disconnect and after-acceptance acknowledgement loss. Final retry/cancel verification remains in progress.
- Both complete host HTTP suites pass their retry/cancel cases, including a request completed before original-key retry. The iOS native recovery case also passes scrolling, keyboard interaction, top placement, and the 30% transcript floor. macOS and Android native evidence remain outstanding.
- Prior native passes cover earlier revisions. Current complete native acceptance remains open: the iOS dismissal assertion fails, Android final readiness/retry assertions need diagnosis, and macOS cannot activate the AUT while the host is locked. Public HTTP recovery checks pass without mocked backend success.
- Complete macOS and iOS native suites now pass the current recovery row, real scrolling, original-key retry, and local Cancel/draft retention. Final Android acceptance remains open before F2 and combined R6/R7 completion.

## Completion Notes

Completed October 10, 2026. F1–F2 and parent R5 are verified by the complete
macOS XCTest and all iOS/Android Detox workflows, each exiting 0. The
production recovery row remains above the scrollable transcript, offers
Resend/local Cancel, and stays within the approved height constraints.
Keyboard dismissal and physical scrolling work during recovery.

Both real-HTTP component suites and native backend postconditions verify
before-/after-acceptance faults, retry with the original payload/key without
duplication, and Cancel retaining the draft without claiming server
cancellation. Recovery uses normal public routes through the forwarding
proxy; no backend success is mocked. Owning notification/composer docs are
updated. Final commands/artifacts and automated-evidence limits are in
`tasks/20261006-chat-operation-ux/000-main.md`. No remaining required scope.