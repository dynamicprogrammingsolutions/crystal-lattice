# 080 — Duration display and turn human time

Clarify duration status and report labels now that both LLM and tool time are
tracked, add compact independent display choices, and show the human-time
delta on each completed turn.

Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/025-tool-duration-store-totals.md
- tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md

## Requirements checklist

- [x] The duration status display offers three compact selects controlling
  the primary duration basis, separately shown tool/human fields, and
  count/average statistics without changing recorded facts.
- [x] LLM-only, tool-only, combined LLM + tool, and human-time values use
  unambiguous titles; the duration report likewise distinguishes LLM, tool,
  combined, and human time.
- [x] Combined session duration is stored as raw and formatted public message
  metadata derived from the existing LLM and tool totals without a database
  migration.
- [x] The final assistant message of each turn stores and displays the
  human-time increase since the previous turn-final message, while
  intermediate tool-call assistant messages do not.
- [x] Existing duration display configuration remains compatible when the new
  settings are absent.
- [x] Focused unit and application integration tests cover display selection,
  metadata projection, combined totals, human-time deltas, and tool-loop
  final-message behavior.
- [x] Duration-tracking documentation describes the new display choices,
  metadata, compatibility behavior, and snapshot timing semantics.

## Requirement questions

None. The user approved the three-control design and snapshot-based turn
delta on 2026-09-27.

## Supporting details

- `duration_session_total` is currently the LLM-only store total despite the
  status label `Total duration`.
- Tool totals are already independently stored and stamped, so combined
  duration is a derived sum and needs no schema change.
- Human time is uploaded asynchronously. The turn delta therefore represents
  cumulative human time available in the store when the final assistant
  message is finalized; an open or not-yet-uploaded frontend span is not
  retroactively added to that message.
- The timestamp duration feature already defines a turn-final assistant as an
  assistant message without tool calls. This follow-up uses the same boundary.

## Execution plan

Status: Approved (user, 2026-09-27)

Replace the single duration-breakdown presentation with three select
declarations:

- **Primary duration** — Hidden, LLM only, or LLM + tools.
- **Additional time fields** — None, Tools, Human, or Tools + human.
- **Duration statistics** — None, Counts, or Counts + averages.

Keep existing configuration keys as compatibility fallbacks when the new keys
are absent. The defaults preserve the current status content while clarifying
the LLM-only title: LLM-only primary, human additional field, and no
statistics. Selecting Human controls both the cumulative status field and the
per-turn human-time message footer.

Derive and stamp combined LLM + tool session totals alongside the existing
metadata. During finalization, identify the current assistant owner and the
previous turn-final assistant in native history. Stamp a raw and formatted
human-time delta only on the current assistant when it has no tool calls. Use
zero as the first-turn baseline; omit the delta when a prior final exists
without a usable human total or when the cumulative total regresses.

Clarify the report's summary and table labels while retaining the current
LLM-based top-session/project ordering. Add focused unit coverage and extend
the real application integration flow for two turns and a tool loop.

### Implementation decisions and open questions

- New config keys are authoritative when present; deprecated keys are read
  only as fallbacks.
- `duration_session_total` remains LLM-only for compatibility.
- New combined fields are
  `duration_session_combined_total` and
  `duration_session_combined_total_formatted`.
- New turn fields are `human_time_turn_delta` and
  `human_time_turn_delta_formatted`.
- Human display is one choice: when enabled it contributes both the cumulative
  status value and the completed-turn delta footer.
- Statistics are emitted for visible machine categories: LLM statistics when
  a primary LLM duration is visible, and tool statistics when tools are part
  of the primary total or separately visible.
- No open material decisions remain.

### Documentation

- Update the duration-tracking README and development overview.
- Document explicit labels, defaults, legacy fallback behavior, new metadata,
  and the uploaded-snapshot limitation of per-turn human time.

### Task checklist

- [x] Record the approved follow-up in the task hierarchy
- [x] Add new configuration schema and legacy fallback resolution
- [x] Add combined session-duration metadata and projection
- [x] Add final-turn human-time delta metadata and footer
- [x] Clarify status and report labels
- [x] Add focused unit and application integration coverage
- [x] Update documentation
- [x] Run package verification and record evidence

### Requirement verification

| Requirement | Evidence |
|---|---|
| Three independent display choices and clear titles | UI-element unit matrix covering defaults, each option, combinations, and old-key fallbacks |
| Combined duration metadata | Extension unit tests and public projection assertions |
| Final-turn human delta | Unit tests for first/subsequent turns, tool-loop intermediate/final messages, missing baseline, and regression |
| Real request behavior | Duration-tracking AgentApplication integration with uploaded spans between turns and a tool-loop final |
| Report clarity | App-plugin report tests asserting explicit LLM/tool/combined/human labels and columns |
| Documentation | README and development overview inspection |

### Additional implementation verification

- Run the complete duration-tracking plugin test suite.
- Run `git diff --check` and audit the worktree so unrelated changes remain
  untouched.

## Implementation Notes

- The feature contributes three compact config elements:
  `duration_primary`, `duration_additional_fields`, and
  `duration_statistics`. Defaults are supplied by the UI resolution rather
  than schema-injected values so an existing legacy setting can still be
  detected and translated when its replacement key is absent.
- Legacy `show_duration_status_total`, `show_human_time_status_total`, and
  `duration_breakdown` values remain runtime fallbacks but are no longer
  contributed as editable UI elements.
- Combined duration is derived during finalization from the existing
  store-backed LLM and tool totals and is projected through the existing
  `duration_session_` metadata path.
- Human turn delta scans native history for the immediately previous
  assistant message without tool calls. The current owner receives delta
  metadata only when it is also a completed assistant message without tool
  calls.
- The report response now includes `combined_total_ms`; its markdown uses
  explicit LLM/tool/combined labels and preserves LLM-based table ordering.
- No mobile or desktop implementation changes were needed because both
  clients already render generic select config declarations, status
  elements, and message footers.

## Completion Notes

Completed 2026-09-27.

- Added the approved three-dropdown duration presentation with explicit
  labels and legacy configuration fallback behavior.
- Added raw/formatted combined duration metadata and raw/formatted human-time
  delta metadata on completed turns.
- Intermediate tool-call assistant messages retain cumulative session totals
  but do not display a turn human-time delta.
- Clarified the duration report summary and table headings while retaining
  the existing ranking behavior.
- Updated the package README and development overview, including the uploaded
  snapshot limitation.
- Verification:
  - `pytest plugins/duration-tracking/tests -q`: 131 passed.
  - `ruff check plugins/duration-tracking/src plugins/duration-tracking/tests`:
    passed.
  - `git diff --check`: passed.
- The unrelated worktree changes in core, frontend SDK, cost tracking,
  reference-provider usage, other task files, and the reviewer CA deletion
  were left untouched.

## Post-completion follow-up

### 2026-09-27 — Use select controls for compact option sets

The user corrected the presentation type after completion: the three duration
settings have small fixed option sets and therefore use `select`, not
`dropdown`. Dropdowns remain intended for larger lists such as model ids.

- Updated all three duration config declarations to `type: "select"`.
- Updated the UI-element expectation and development documentation.
- Re-ran the complete duration-tracking suite: 131 passed.
- Ruff and `git diff --check` passed.