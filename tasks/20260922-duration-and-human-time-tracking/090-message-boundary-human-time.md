# 090 — Message-boundary human time

Limit human-time message data to completed assistant turns and split frontend
human-time spans when users submit composed messages without delaying the
message operation.

Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/070-session-presence-and-inactivity-semantics.md
- tasks/20260922-duration-and-human-time-tracking/080-duration-display-and-turn-human-time.md

## Requirements checklist

- [x] Human-time session totals and turn deltas are attached and displayed
  only on completed assistant messages without tool calls; intermediate
  tool-call assistant messages retain their machine-duration metadata but no
  human-time metadata.
- [x] Desktop Send, Append, and Append As close the current session span and
  immediately start a replacement span at the same boundary without waiting
  for cache persistence or upload before continuing the message operation.
- [x] The replacement desktop span follows the configured inactivity
  semantics, so submission alone records up to one maximum-inactivity interval
  unless later activity extends it or another close condition ends it earlier.
- [x] Mobile Send, Append, and Append As close the current foreground-session
  span and immediately continue tracking the same eligible foreground session,
  without waiting for cache persistence or upload.
- [x] Closed spans continue through the existing durable, debounced,
  best-effort upload pipeline; uploader ordering, retry, warning, and failure
  behavior are unchanged.
- [x] Focused deterministic tests cover final-message filtering, desktop and
  mobile span splitting, and non-blocking composer submission without adding
  native simulator, Detox, or XCTest scenarios.

## Requirement questions

None. The user approved best-effort non-blocking span splitting on 2026-09-27.
A fast assistant response may still finalize before the asynchronously
uploaded span is visible; avoiding that race at the cost of delaying Send is
explicitly out of scope.

## Supporting details

- The duration-tracking extension currently suppresses the turn delta on a
  tool-call assistant but still stamps cumulative human-time fields on every
  assistant round.
- Desktop already treats Send as activity, while mobile tracks foreground
  session presence. Both providers already persist closed spans asynchronously
  and notify the same debounced uploader.
- Send and append validation must run before splitting so rejected empty,
  offline, snapshot, attachment, or duplicate operations do not create an
  artificial boundary.
- Resend and pending-request recovery do not submit newly composed content and
  remain outside this follow-up.

## Execution plan

Status: Approved (user, 2026-09-27)

Refine duration finalization so human-time store totals are queried and stamped
only when the current duration owner is an assistant without tool calls.
Project human-time metadata only for the same completed-turn shape and add an
explicit assistant/no-tool-call condition to the `human time` message footer.
Machine-duration and tool-duration recording and metadata remain unchanged on
intermediate rounds.

Add one non-blocking composed-message boundary operation to each frontend
telemetry provider. At one timestamp it closes the current eligible span,
queues the existing asynchronous persistence/upload work, and immediately
opens the replacement span. Desktop schedules the normal inactivity deadline
from that boundary; mobile continues foreground-session presence. Composer
handlers invoke the operation after validation and immediately continue to
their existing Send, Append, or Append As call without awaiting telemetry.

Keep the current uploader untouched. Add provider and composer-focused tests
that prove splitting and call ordering, then update the two frontend telemetry
development pages and duration-tracking documentation.

### Implementation decisions and open questions

- A composed-message boundary is best-effort and must never postpone or fail a
  user message operation.
- Desktop and mobile use the same close/reopen timestamp to avoid gaps or
  overlap introduced solely by splitting.
- Submission opens the replacement desktop activity span even when no earlier
  span was open, because submission itself is an activity.
- Mobile reopens only when tracking remains enabled and the same session is
  active in the foreground.
- Append As is included for every role because the human action is composing
  and submitting the message, independent of the appended role.
- No uploader API, debounce interval, backend action, or database schema
  changes are required.
- No open material decisions remain.

### Documentation

- Update duration-tracking docs to state that human metadata belongs only to
  completed no-tool-call assistant messages.
- Update desktop and mobile human-time development pages with the
  message-boundary split and non-blocking upload semantics.

### Task checklist

- [x] Record the approved follow-up in the task hierarchy
- [x] Restrict human-time metadata and footer visibility to completed turns
- [x] Add non-blocking desktop composed-message span splitting
- [x] Add non-blocking mobile composed-message span splitting
- [x] Add focused deterministic coverage
- [x] Update documentation
- [x] Run package verification and record evidence

### Requirement verification

| Requirement | Evidence |
|---|---|
| Human time only on completed turns | Duration extension unit tests, UI-element condition assertion, and tool-loop application integration |
| Desktop boundary and inactivity continuation | Desktop provider fake-timer test covering pre-submit close and post-submit inactivity deadline |
| Mobile boundary and foreground continuation | Mobile provider fake-timer/lifecycle test covering pre-submit close and replacement foreground span |
| Non-blocking Send/Append | Focused composer tests proving chat-controller calls are not gated on telemetry persistence or upload |
| Existing upload behavior preserved | Existing cache/uploader suites plus inspection that no uploader contract changed |
| No native test expansion | Verification report records no simulator, Detox, or XCTest invocation |

### Additional implementation verification

- Run the complete duration-tracking plugin suite and Ruff.
- Run focused shared, desktop, and mobile Jest suites plus package type checks
  where practical, reporting unrelated baseline failures separately.
- Run `git diff --check` and audit the final worktree so unrelated changes and
  the reviewer CA deletion remain untouched.

## Implementation Notes

- Duration finalization now keeps machine totals on every measured assistant
  round but queries and stamps human totals only when the owner is an
  assistant without tool calls. Public projection also strips any stale human
  fields from tool-call assistant messages, and the footer declaration
  independently checks role and empty tool calls.
- Desktop exposes a synchronous `splitForComposedMessage` operation. It closes
  the tracker at one timestamp and records submission as the first activity of
  the replacement span at that same timestamp, retaining the configured
  inactivity deadline.
- Mobile exposes the equivalent synchronous operation over its foreground
  presence state. It reopens only when the submitted session is still the
  active foreground session and tracking remains enabled.
- A shared `runComposedMessageSubmission` helper invokes the telemetry
  boundary, ignores telemetry exceptions, and immediately starts the supplied
  chat operation. Desktop and mobile use it for Send, Append, and Append As.
- Span persistence and `notifySpanClosed` remain asynchronous. The uploader,
  debounce, retries, warnings, action contract, and storage schema were not
  changed.
- Existing unrelated range-fallback edits in desktop `ChatPane.tsx`, mobile
  `SessionChatScreen.tsx`/`ConnectedRoot.tsx`, and the rest of the dirty
  worktree were preserved.

## Completion Notes

Completed 2026-09-27.

- Human-time totals and the `human time` turn footer now appear only on final
  assistant messages without tool calls. Intermediate tool-call assistants
  retain LLM/tool duration metadata but no human-time metadata.
- Desktop and mobile now split their current session span on validated Send,
  Append, and Append As actions and immediately continue tracking without
  waiting for cache persistence or upload.
- Desktop submission starts a fresh inactivity-governed activity span; mobile
  submission starts a fresh foreground-presence span.
- The existing best-effort upload behavior remains unchanged, so a fast
  response can still finalize before the closed span is uploaded.
- Documentation was updated for duration tracking and both frontend
  collection models.
- Verification:
  - `pytest plugins/duration-tracking/tests -q`: 132 passed.
  - `ruff check plugins/duration-tracking/src plugins/duration-tracking/tests`:
    passed.
  - `npm --workspace @crystal-lattice/frontend-rn-components test`: 8 files /
    76 tests passed.
  - Mobile Jest: 53 suites / 255 tests passed.
  - Desktop Jest: 41 suites / 194 tests passed.
  - Mobile `npx tsc --noEmit`: passed.
  - Desktop `npx tsc --noEmit`: still reports the same 19 pre-existing URL,
    ChatPane declaration/optional-value, and theme errors; no new telemetry
    error was reported.
  - `git diff --check`: passed.
- No Detox, simulator, XCTest, or other native test was run.