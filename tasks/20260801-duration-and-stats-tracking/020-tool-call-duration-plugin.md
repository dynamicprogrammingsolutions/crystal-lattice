Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

Depends On:
- tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md

# Tool Call Duration Plugin

A plugin that captures wall-clock duration for every tool call using the framework-provided lifecycle hooks, surfaces it on tool-result messages, and accumulates per-turn and total stats in the session stats metadata.

## Requirements checklist

- [ ] A plugin captures wall-clock duration for every tool call executed through the application tool loop.
- [ ] Per-tool-call duration is stored on the corresponding tool-result message metadata.
- [ ] Per-turn tool call duration (sum of tool-call durations within a turn) is computed and stored in the session stats metadata.
- [ ] Total tool call duration (sum across all turns in a session) is computed and stored in the session stats metadata.
- [ ] Tool call duration is tracked separately from LLM request duration; the existing `turn_duration_ms` (LLM-only) is preserved unchanged.
- [ ] Tool call duration is visible in the UI via a message footer on tool-result messages, gated by a config toggle.
- [ ] The plugin uses only framework-provided lifecycle hooks; it does not modify `tool_loop.py` or `AgentCore`.
- [ ] The plugin works across all providers (OpenRouter, OpenAI Responses, reference-compatible).

## Supporting details

### Current state

- Tool-result messages currently carry `metadata.tool_call_id`, `metadata.tool_name`, `metadata.tool_plugin` (see `core/python/agent_app/tool_loop.py::_apply_tool_calls`).
- `DurationExtension` stamps `duration_ms`, `duration_formatted`, `duration_started_at`, `duration_finished_at` on assistant messages. The same field names should be used on tool-result messages for consistency.
- `DurationExtension._sum_assistant_durations_since_turn_start` shows the pattern for scanning native history to compute turn totals; the same approach applies to tool messages.
- The session stats metadata key is configurable (default `stats`), defined in subtask 010.

### Constraints

- Tool-result messages must survive `to_native_messages`/`from_native_messages` round-trips with the new `duration_ms` metadata intact.
- The plugin must not modify `tool_loop.py` or `AgentCore` source files.
- The plugin must use the `tool_call_prepare` and `tool_call_complete` lifecycle triggers from subtask 010.
- Per-turn tool duration is separate from the existing LLM `turn_duration_ms`; do not merge them.

## Execution plan

Status: Draft

This plan intentionally defers the plugin-kind decision until subtask 010 has
verified both established lifecycle paths. The implementation may be an
application plugin or a feature plugin; it must not require a framework
contract change after that choice.

### Plugin-kind selection

1. Compare the two supported implementations against the completed 010
   infrastructure:
   - Application plugin: persistent application state is natural for matching
     start/end; the post action loads the completed session, rewrites the tool
     message and aggregate metadata with normal core helpers, rebuilds native
     history, and saves.
   - Feature plugin: the post action transforms complete `native_messages` and
     returns `session_metadata`; transient timing state uses the application
     `runtime_store` from lifecycle context.
2. Select the kind based on implementation simplicity, state cleanup,
   config/UI contribution, and cross-provider native-history behavior. Record
   the choice and evidence in this task before implementation.
3. Create the corresponding first-party package under `plugins/` with
   `agent_plugin.json`, source package, package-local tests, and README.
4. The selected plugin declares two actions:
   - `capture_tool_call_start` with `trigger: "tool_call_prepare"`.
   - `capture_tool_call_end` with `trigger: "tool_call_complete"`.

### Timing capture

1. In `capture_tool_call_start`, record `time.monotonic()` and
   `datetime.now(timezone.utc).isoformat()` keyed by
   `(session_id, request_id, tool_call_id)` in the selected plugin's supported
   transient state store.
2. In `capture_tool_call_end`, retrieve the start time by `tool_call_id`, compute `duration_ms = int((time.monotonic() - start) * 1000)`, and format it using the same `_format_duration_ms` helper as `DurationExtension`.
3. Transform the complete session through the selected established contract:
   - application path: load, immutably rewrite the matching tool message and
     session metadata, rebuild native history, and save;
   - feature path: return complete transformed `native_messages` plus
     `session_metadata`.
4. Stamp `duration_ms`, `duration_started_at`, `duration_finished_at`, and
   `duration_formatted` on the matching tool-result message.

### Turn and total accumulation

1. On `tool_call_complete`, scan the session's tool messages since the last turn separator (last user/system message or last assistant message without tool calls) to compute `turn_tool_duration_ms`.
2. Compute `tool_duration_ms` from duration-bearing tool messages across the
   complete session so the aggregate follows arbitrary history
   transformations and does not double-count lifecycle retries.
3. Write `turn_tool_duration_ms` and `tool_duration_ms` under the configurable
   session stats metadata key while preserving fields owned by other stats
   plugins.
4. Rely on the selected full-session lifecycle contract and 010's
   request-owned checkpoint/adoption behavior for persistence.

### UI elements

1. Expose a `message_footer` UI element: `{"ui_type": "message_footer", "data": "metadata.duration_formatted", "template": "tool duration: {{data}}"}`.
2. Gate it behind a config toggle `tool_duration_show_footer` (default true).
3. Expose `session_list_field` elements for `metadata.stats.tool_duration_ms` (total tool duration) if configured.

### Cross-provider verification

1. Test with `EchoOpenAILikeProvider` (core test provider).
2. Test with OpenRouter and OpenAI Responses provider test fixtures to verify native-history round-trip survival.

### Implementation decisions and open questions

- **Open material decision — plugin kind**: choose application or feature only
  after 010's equivalent-path tests pass. Application is likely simpler for
  transient state and UI; feature is likely simpler for native-history
  transformation. Neither is a framework requirement.
- **State keying**: use `(session_id, request_id, tool_call_id)`; if
  `tool_call_id` is missing, include tool name and call index.
- **No new mutation shape**: use only the established application full-session
  save contract or feature full-native-history return contract.
- **Turn boundary detection**: reuse the same turn-separator logic as `DurationExtension` (last user/system message or last assistant without tool calls).

### Documentation

- Package README describing the selected plugin kind, config toggle, state
  cleanup, and stats fields.
- Update `plugins/timestamp-extension/README.md` to cross-reference tool duration.

### Task checklist

- [ ] Evaluate application and feature implementations against completed 010
  fixtures and record the selected plugin kind
- [ ] Create the selected plugin package structure
- [ ] Implement `capture_tool_call_start` / `capture_tool_call_end` actions
- [ ] Transform the matching tool message through the selected established
  full-session contract
- [ ] Implement per-turn and total accumulation in session stats metadata
- [ ] Add `message_footer` UI element with config toggle
- [ ] Write unit tests (timing, state cleanup, turn accumulation, total
  accumulation)
- [ ] Write integration test with `EchoOpenAILikeProvider`
- [ ] Write cross-provider round-trip tests (OpenRouter, OpenAI Responses fixtures)
- [ ] Write `README.md`

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Per-tool-call duration captured | Unit test: after a tool call, tool-result message `metadata.duration_ms` is a non-negative int |
| Per-tool-call duration on message metadata | Unit test asserting `metadata.duration_ms`, `duration_formatted`, `duration_started_at`, `duration_finished_at` are present on the tool message |
| Per-turn tool duration in session stats | Unit test: after two tool calls in one turn, `session.metadata["stats"]["turn_tool_duration_ms"]` equals their sum |
| Total tool duration in session stats | Unit test: across two turns, `session.metadata["stats"]["tool_duration_ms"]` accumulates correctly |
| Separate from LLM duration | Test that `turn_duration_ms` (LLM-only) is unchanged and `turn_tool_duration_ms` is a distinct field |
| UI footer on tool messages | UI-schema test confirming `message_footer` element with `metadata.duration_formatted` is present when toggle is on, absent when off |
| Framework-only hooks | Diff verification that this plugin changes neither `tool_loop.py` nor `AgentCore` and uses only 010's established lifecycle dispatch |
| Cross-provider round-trip | Test with OpenRouter and OpenAI Responses fixtures that tool-result `duration_ms` survives `to_native_messages`/`from_native_messages` |