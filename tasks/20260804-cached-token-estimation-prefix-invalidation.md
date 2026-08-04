# Cached-token estimation with prefix invalidation

Refine the history-based cached-token estimators so decreasing input counts are
treated as prefix invalidation and new user turns infer preserved versus
interleaved thinking from the relationship between current and prior input
counts.

## Requirements checklist

- [x] An input-token decrease within a user turn produces an estimated cached-token count of `0`.
- [x] On the first generation after a user message, preserved thinking is inferred when the current input exceeds the previous populated turn's last input, and that last input is used as the cached-token estimate.
- [x] On the first generation after a user message, interleaved thinking remains supported by using the previous populated turn's first input when it does not exceed the current input.
- [x] On the first generation after a user message, an interleaved-thinking candidate larger than the current input is treated as prefix invalidation and produces an estimate of `0`.
- [x] OpenAI Responses ChatGPT usage and the reference OpenAI-compatible provider apply the same estimation rules while preserving their existing provider-specific enablement and precedence policies.
- [x] Estimated cached-token metadata, cost calculation, formatted usage, and cumulative cached-token totals consistently reflect the corrected estimate without mutating raw provider usage.
- [x] User-facing provider documentation describes the corrected heuristic and its limitations.
- [x] Automated regression coverage verifies the corrected decisions and their usage-accounting effects in both provider packages.

## Scope

In scope:

- The ChatGPT-mode cached-token estimator in the OpenAI Responses usage
  extension.
- The opt-in cached-token fallback in the reference OpenAI-compatible usage
  extension.
- Provider-local tests and documentation for those estimators.

Out of scope:

- OpenRouter, which currently consumes provider-reported cached-token counts
  and does not synthesize this estimate.
- Request shaping, compaction behavior, reasoning-history serialization, auth,
  persistence, or new public metadata identifying an inferred reasoning mode.
- Changing the precedence of real provider-reported cached counts or
  provider-returned costs in the reference provider.

## Ground truth and current state

Fact: both estimators reduce history to user boundaries and usage-bearing
assistant/tool-call generations. Tool-result messages do not participate.

Fact: both implementations currently retain the previous populated turn's first
input and the current turn's most recent input. They do not retain the previous
turn's last input.

Fact: a later generation in the same turn currently reuses the immediately
previous input even when the current input is smaller. In OpenAI Responses this
can produce an estimated cached-token count larger than the current input. For
example:

```text
current input:    278,176
previous input:   371,326
current estimate: 371,326
correct estimate: 0
```

Fact: the reference provider currently clamps a history-derived estimate larger
than the current prompt input to the current input. That prevents negative
ordinary-input accounting but incorrectly treats the entire changed prefix as
cached. A history-derived candidate larger than current input is evidence of
prefix invalidation for this heuristic and must become `0`.

Fact: after a user message, both implementations currently always use the first
usage input from the preceding populated turn. This models interleaved thinking,
where prior-turn reasoning is not retained as reusable prefix context, but
undercounts preserved thinking.

Ground-truth inference rules:

| Position | Observation | Estimated cached tokens |
|---|---|---:|
| First generation without prior populated history | No prior candidate | `0` |
| Later generation in the same turn | Current input is greater than or equal to the previous input | Previous input |
| Later generation in the same turn | Current input is less than the previous input | `0` |
| First generation after a user message | Current input is greater than the previous turn's last input | Previous turn's last input |
| First generation after a user message | Current input is between the previous turn's first and last inputs, inclusive | Previous turn's first input |
| First generation after a user message | Current input is less than the previous turn's first input | `0` |

Explanation:

- Within one turn, the immediately previous request is the reusable-prefix
  candidate. If it is larger than the current request, compaction or another
  prefix change has occurred, so the estimate is zero.
- Across a user boundary, a current input larger than the preceding turn's last
  request indicates preserved thinking; the full previous request can be the
  cached prefix.
- Otherwise, the previous turn's first request is the conservative interleaved
  thinking candidate. If even that candidate exceeds current input, the prefix
  is considered invalidated.
- The inference is local to estimation. It does not persist or expose a
  preserved/interleaved classification and does not consult provider-specific
  reasoning configuration.

Baseline evidence before implementation:

- `python -m pytest plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py -q`
  passed with 29 tests.
- `python -m pytest plugins/reference-openai-compatible-provider/tests/test_usage_extension_unit.py -q`
  passed with 28 tests.

## Execution plan

Status: Approved

Implement the same small state-machine change independently in both provider
packages. Keeping the heuristic provider-local avoids adding a provider-specific
concept to the core SDK; matching decision-matrix tests and documentation will
guard parity.

1. Track both the first and last usage input for the previous populated turn in
   each estimator. At a user boundary, move both current-turn values into the
   previous-turn state without allowing empty/consecutive user turns to erase
   the most recent populated turn.
2. Apply the approved decision table:
   - within a turn, use the previous input only when it does not exceed current
     input; otherwise return zero;
   - after a user boundary, choose the previous last input for preserved
     thinking, the previous first input for interleaved thinking, or zero for
     invalidation.
3. Preserve provider-specific policy:
   - OpenAI Responses estimates only for effective ChatGPT auth and continues
     to keep raw usage unchanged while using the estimate for ChatGPT pricing;
   - the reference provider estimates only when explicitly enabled and no real
     cached-token count was reported;
   - existing real cached-count and provider-cost precedence remains unchanged.
4. Add mirrored estimator tests for first use, monotonic same-turn reuse,
   same-turn decrease, preserved thinking, interleaved thinking, new-turn
   invalidation, equality boundaries, ignored tool results, and empty user
   turns.
5. Add provider-level usage-accounting regressions proving invalidation yields
   estimated cached `0`, formatted `"0"`, no current cached-token discount or
   cumulative increment, and unchanged raw provider usage.
6. Update both provider READMEs to explain the corrected heuristic, strict
   preserved-thinking boundary, prefix invalidation, and the heuristic's
   non-billing-grade nature.
7. Run focused usage-extension tests followed by each package's full default
   test suite. Hosted/manual provider observations are optional because
   provider-controlled cache and compaction behavior is not deterministic
   enough to be an automated acceptance boundary.

### Implementation decisions and open questions

Decision: use a strict `current > previous_turn_last` test for preserved
thinking, matching the observed invariant that a new user message makes
preserved-thinking input higher. Equality follows the interleaved branch.

Decision: return `0` for an invalid history-derived candidate instead of
clamping it to current input. Defensive clamping of real provider-reported
cached counts remains unchanged.

Decision: do not add public metadata for the inferred preserved/interleaved
mode. The requested outcome is the corrected cached-token estimate.

Open questions: none.

### Documentation

Update the usage sections of:

- `plugins/openai_responses/README.md`
- `plugins/reference-openai-compatible-provider/README.md`

The audience is users configuring usage display/pricing and maintainers
interpreting estimated cached-token metadata.

### Task checklist

- [x] Record the approved task handoff and baseline evidence.
- [x] Implement the OpenAI Responses estimator change.
- [x] Implement the reference OpenAI-compatible estimator change.
- [x] Add and update OpenAI Responses regression tests.
- [x] Add and update reference provider regression tests.
- [x] Update both provider READMEs.
- [x] Run focused test verification.
- [x] Run package-level default test verification.
- [x] Record requirement evidence and completion notes.

### Requirement verification

- Same-turn prefix invalidation: verified by direct estimator tests using the
  reported `371,326 -> 278,176` shape and provider-level metadata/cost tests in
  both packages.
- Preserved/interleaved inference: verified by mirrored decision-matrix tests
  covering previous-turn first/last/current input relationships, including
  equality and invalidation boundaries.
- Provider-policy preservation: verified by existing and new usage-extension
  tests covering ChatGPT versus API behavior, opt-in estimation, reported
  cached-token precedence, provider-cost precedence, and raw usage
  preservation.
- Documentation: both README usage sections now match the approved decision
  table and describe the heuristic as non-billing-grade.
- Regression safety: focused suites passed. All unaffected default-suite tests
  passed; the complete package commands remain red only because of isolated,
  unrelated failures documented in Completion Notes.

### Additional implementation verification

- Confirm tool-result messages and empty/consecutive user turns do not alter
  populated-turn candidates.
- Confirm equality behavior at same-turn and user-boundary thresholds.
- Confirm no unrelated dirty-worktree files are modified.

## Implementation Notes

- Execution began immediately after task creation under the user's explicit
  approval.
- The worktree contains unrelated existing changes, including OpenAI Responses
  native-compaction files. The usage estimator, usage tests, and provider
  READMEs were clean at execution start and are the only provider files in
  scope for this task.
- Both estimators now retain the previous populated turn's first and last input
  counts. History-derived candidates larger than current input resolve to zero;
  the reference provider no longer clamps such a candidate to current input.
- Added mirrored decision-matrix coverage and provider-level cost/cumulative
  accounting regressions. Focused verification passed with 31 OpenAI Responses
  usage tests and 30 reference-provider usage tests.
- Complete package verification exposed failures outside the changed usage
  code. The OpenAI Responses failures reproduce in attachment-history tests and
  overlap unrelated existing native-compaction work. The reference-provider
  failures reproduce in rate-limit tests whose mocks patch `requests.post`
  while current provider code calls `Session.post`. No out-of-scope files were
  changed to address these failures.

## Completion Notes

- Corrected both cached-token estimators with the approved prefix-invalidation
  and preserved/interleaved-thinking inference rules.
- A same-turn reduction such as `371,326 -> 278,176` now yields an estimated
  cached count of `0`, not `371,326` or a clamp to `278,176`.
- After a user boundary, current input greater than the preceding populated
  turn's last input uses that last input; otherwise the first input is used only
  when it fits, with zero returned when even that candidate is too large.
- Raw OpenAI Responses usage remains unchanged. The reference provider retains
  its existing opt-in behavior and precedence for real cached counts and
  provider-returned costs.
- Added matching estimator and usage-accounting regressions in both provider
  packages and updated both provider READMEs.
- Verification completed:
  - OpenAI Responses focused usage suite: 31 passed.
  - Reference-provider focused usage suite: 30 passed.
  - OpenAI Responses default suite excluding the unrelated failing
    attachment-history file: 394 passed, 76 deselected. The isolated file had
    4 passed and 3 unrelated failures.
  - Reference-provider default suite excluding the unrelated failing
    rate-limit file: 76 passed, 61 deselected. The isolated file had 10 passed
    and 15 unrelated failures.
  - Ruff on all changed Python files: passed.
  - `git diff --check` on all task files: passed.
- Plan deviations: none in implementation direction. Full-package green status
  was blocked by pre-existing/out-of-scope failures; these were isolated and
  reported rather than repaired under this task.
- Deferred scope: attachment-history/native-compaction failures and stale
  reference-provider rate-limit mocks require separate ownership if they are
  not already being addressed by the existing worktree changes.

## Post-completion follow-up

- Black reformatted the two changed test files. The focused suites were rerun
  afterward with the same 31/30 passing results; Ruff, Black check, and
  `git diff --check` all passed.