# Duration Session Total

Extend `DurationExtension` with a cumulative LLM/provider-request duration for
the retained session history and expose that total through the same
message-metadata and status-bar pattern used by usage-cost plugins.

## Requirements checklist

- [x] Each duration-bearing response exposes a numeric and formatted cumulative
  session duration in core message metadata.
- [x] The cumulative session duration is the sum of LLM/provider-request
  durations in retained native history, including all requests in tool turns,
  and excludes unrelated tool, human, and session wall-clock time.
- [x] Cumulative duration metadata survives native-history persistence and
  reconstruction across requests.
- [x] The cumulative duration is available as a plugin-contributed chat status
  bar field and can be hidden independently from duration message footers.
- [x] Existing per-request duration, per-turn duration, and turn-TPS behavior
  remains compatible across chat-style and Responses-style native histories.

## Supporting details

### Current state

- `DurationExtension.initialize_request()` captures the request start time.
- `DurationExtension.finalize()` calculates `duration_ms` and
  `turn_duration_ms`, then stores them on one provider-native response owner.
- `DurationExtension.from_native_messages()` projects persisted timing fields
  into core message metadata.
- Cost plugins calculate cumulative cost before native-to-core conversion,
  persist the result in native `_metadata`, and expose the formatted cumulative
  value through a `status_bar` UI element.
- During an ordinary request, `from_native_messages()` receives the current
  native finals rather than the complete retained session history, so it is not
  the authoritative calculation boundary for a session total.

### Scope

- The total represents cumulative LLM/provider-request wall time.
- Session-level reporting under `session.metadata["stats"]`, session-list
  fields, project/user aggregation, tool execution timing, and human timing are
  excluded.
- Existing native history can contribute through its persisted individual
  duration fields; no separate migration is required.

## Execution plan

Status: Approved

Calculate the cumulative duration in `DurationExtension.finalize()`, where the
current measurement and complete retained native history are both available.
Sum individual duration measurements owned by the duration feature rather than
prior cumulative values, then add the current request exactly once. Persist
`total_duration_ms` and `total_duration_formatted` on the same native response
owner as the existing request and turn duration fields.

Extend `from_native_messages()` only as a projection boundary: copy the
precomputed total from native `_metadata` into core message metadata, including
the `native_indices` aggregation path used by Responses-style providers. A
rebuild fallback may derive the total from individual native durations only
when precomputed total metadata is absent; normal request calculation remains
in `finalize()`.

Expose `metadata.total_duration_formatted` through a `status_bar` element using
`Total duration: {{data}}`. Add
`duration_extension_show_status_total`, defaulting to true, so users can hide
the status total independently while the existing
`duration_extension_show_duration` setting continues to control message
footers.

Cover ordinary multi-turn history, multi-request tool turns, Responses-style
tool-only output ownership, persistence/rebuild projection, malformed metadata,
and independent UI controls. Preserve all existing public timing fields and
turn-TPS calculations.

### Implementation decisions and open questions

- **Decision — calculation boundary:** `finalize()` owns cumulative-duration
  calculation; `from_native_messages()` projects persisted values and may
  provide rebuild compatibility only.
- **Decision — public keys:** use `total_duration_ms` and
  `total_duration_formatted`, complementing `duration_ms` and
  `turn_duration_ms`.
- **Decision — accounting source:** sum individual request measurements, never
  previously stored totals, to prevent compounding or double counting.
- **Decision — duration ownership:** count only records attributable to
  `DurationExtension`, including Responses-style native items without an
  assistant role; do not count unrelated duration-bearing tool messages.
- **Decision — UI control:** cumulative status visibility is independent from
  duration footer visibility.
- No unresolved requirement or material implementation questions remain.

### Documentation

- Update `plugins/timestamp-extension/README.md` to describe per-request,
  per-turn, and cumulative session duration and clarify that the total measures
  LLM/provider-request wall time.
- Document the status-bar visibility configuration key.

### Task checklist

- [x] Add duration-owner-aware cumulative calculation in `finalize()`.
- [x] Persist and project numeric/formatted cumulative duration metadata.
- [x] Add the independently configurable status-bar declaration.
- [x] Add deterministic regression and UI-schema tests.
- [x] Update package documentation.
- [x] Run package-local and relevant application-level verification.
- [x] Commit the completed implementation.

### Requirement verification

| Requirement | Acceptance evidence |
|---|---|
| Numeric and formatted cumulative duration | Deterministic two-turn test asserts the latest core message total equals the sum of individual request durations and has the expected formatted value. |
| LLM-only accounting across tool turns | Tests cover multiple provider requests in one turn, Responses-style tool-only output, and unrelated duration-bearing native records without double counting. |
| Persistence and reconstruction | Native-history and `from_native_messages()` tests confirm total metadata survives projection and rebuild paths. |
| Status-bar exposure and independent control | UI-schema tests assert the status data path/template and independent footer/status visibility combinations. |
| Existing timing compatibility | Existing duration tests remain green and targeted provider-shape tests retain request, turn, and TPS assertions. |

### Additional implementation verification

- Run `pytest plugins/timestamp-extension/tests -q` after installing the local
  core SDK and timestamp plugin with development dependencies.
- Run targeted application UI-schema/status-bar tests if package-level schema
  tests do not exercise the production aggregation boundary.

## Implementation Notes

- `DurationExtension.finalize()` now sums prior individual request durations and
  adds the current measurement once, then persists `total_duration_ms` and
  `total_duration_formatted` on the selected native response owner.
- New records carry the private `_duration_extension_owner` marker. Retained
  records from older versions remain countable when they contain both
  `duration_ms` and `turn_duration_ms`. Records with only a generic
  `duration_ms`, such as tool timing, are excluded.
- `from_native_messages()` projects precomputed total fields for one-to-one and
  `native_indices`-aggregated provider outputs; it does not calculate normal
  request totals.
- `duration_extension_show_status_total` independently controls the
  `metadata.total_duration_formatted` status-bar declaration.
- Verification completed:
  - `pytest plugins/timestamp-extension/tests -q` — 12 passed.
  - `ruff check plugins/timestamp-extension/src plugins/timestamp-extension/tests`
    — passed.
  - `black --check` for the changed Python files — passed.
  - `git diff --check` — passed.
  - The tests import `timestamp_extension` from this worktree's editable
    checkout.
- The broader default-config application UI-schema integration slice was
  explicitly enabled but exceeded the 120-second command timeout without a
  result. Package coverage now exercises the production
  `AgentCore.get_ui_schema()` aggregation boundary directly, so no
  application-specific behavior remains unverified for this change.

## Completion Notes

- Completed the approved cost-style duration-total flow: calculation occurs in
  `finalize()`, durable values live in provider-native `_metadata`, and
  `from_native_messages()` projects them into core message metadata.
- `total_duration_ms` and `total_duration_formatted` now represent the sum of
  retained LLM/provider-request durations. An explicit private owner marker and
  legacy request-plus-turn fallback exclude unrelated generic duration fields.
- The formatted total is exposed through a plugin-contributed status bar and
  can be disabled independently with
  `duration_extension_show_status_total=false`.
- Existing request duration, turn duration, Responses-style owner selection,
  native-index projection, and turn TPS remain covered by the passing package
  suite.
- Requirement evidence:
  - Two-request core flow verifies session accumulation and turn reset.
  - Tool-turn and Responses-style tests verify all provider requests contribute
    once.
  - Unowned and malformed metadata tests verify accounting boundaries.
  - Native-history and `native_indices` tests verify persistence and
    reconstruction.
  - Core UI-schema aggregation verifies the status-bar declaration and plugin
    ownership.
- Verification: 12 timestamp-extension tests passed; Ruff, Black check, and
  `git diff --check` passed.
- The default-config application UI-schema integration attempt timed out after
  120 seconds without producing a result. No implementation was weakened or
  bypassed; the relevant production core aggregation boundary is covered
  deterministically.
- The implementation was committed in `57a4cad9`.
- No requirements were deferred and no scope changes were made.