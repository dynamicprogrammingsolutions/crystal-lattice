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

### Plugin structure

1. Create `plugins/tool-duration-app/` (application plugin) with:
   - `agent_plugin.json` registering the plugin class.
   - `src/tool_duration_app/__init__.py` implementing `ToolDurationAppPlugin`.
   - `tests/` with unit and integration tests.
2. The plugin declares two actions:
   - `capture_tool_call_start` with `trigger: "tool_call_prepare"`.
   - `capture_tool_call_end` with `trigger: "tool_call_complete"`.

### Timing capture

1. In `capture_tool_call_start`, record `time.monotonic()` and `datetime.now(timezone.utc).isoformat()` keyed by `tool_call_id` in the plugin state dict.
2. In `capture_tool_call_end`, retrieve the start time by `tool_call_id`, compute `duration_ms = int((time.monotonic() - start) * 1000)`, and format it using the same `_format_duration_ms` helper as `DurationExtension`.
3. Return a `session_metadata` patch that stamps `duration_ms`, `duration_started_at`, `duration_finished_at`, `duration_formatted` onto the tool-result message's metadata. The framework applies this patch to the in-flight session.

### Turn and total accumulation

1. On `tool_call_complete`, scan the session's tool messages since the last turn separator (last user/system message or last assistant message without tool calls) to compute `turn_tool_duration_ms`.
2. Read the existing total from `session.metadata["stats"]["tool_duration_ms"]` (or 0 if missing), add the current call's duration, and write back the updated total.
3. Write `turn_tool_duration_ms` and `tool_duration_ms` (total) into `session.metadata["stats"]` via the `session_metadata` return.
4. Use `session_save_prepare` trigger to ensure stats are persisted on every save.

### UI elements

1. Expose a `message_footer` UI element: `{"ui_type": "message_footer", "data": "metadata.duration_formatted", "template": "tool duration: {{data}}"}`.
2. Gate it behind a config toggle `tool_duration_show_footer` (default true).
3. Expose `session_list_field` elements for `metadata.stats.tool_duration_ms` (total tool duration) if configured.

### Cross-provider verification

1. Test with `EchoOpenAILikeProvider` (core test provider).
2. Test with OpenRouter and OpenAI Responses provider test fixtures to verify native-history round-trip survival.

### Implementation decisions and open questions

- **State keying**: plugin state is per-request (short-lived). The `tool_call_id` is the natural key for matching start/end. If `tool_call_id` is missing (edge case), fall back to tool name + call index.
- **Metadata patch mechanism**: the `session_metadata` return from lifecycle actions merges into `session.metadata`. To stamp a specific tool-result *message*, the plugin needs to return a `final_messages` replacement or a message-targeted patch. *Open question*: does the existing lifecycle action contract support patching a specific message's metadata, or only session-level metadata? If only session-level, the plugin may need to return the modified tool-result message via `final_messages` and let the tool loop apply it. *Recommendation*: check the `response_finalize` contract in `core.py` for message-level patching; if unavailable, propose a minimal extension to the lifecycle return contract.
- **Turn boundary detection**: reuse the same turn-separator logic as `DurationExtension` (last user/system message or last assistant without tool calls).

### Documentation

- `plugins/tool-duration-app/README.md` describing the plugin, config toggle, and stats fields.
- Update `plugins/timestamp-extension/README.md` to cross-reference tool duration.

### Task checklist

- [ ] Create `plugins/tool-duration-app/` package structure
- [ ] Implement `capture_tool_call_start` / `capture_tool_call_end` actions
- [ ] Implement per-turn and total accumulation in session stats metadata
- [ ] Add `message_footer` UI element with config toggle
- [ ] Write unit tests (timing, turn accumulation, total accumulation)
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
| No `tool_loop.py` modification | Grep/diff verification that `tool_loop.py` source is unchanged (only the lifecycle dispatch from 010 touches it) |
| Cross-provider round-trip | Test with OpenRouter and OpenAI Responses fixtures that tool-result `duration_ms` survives `to_native_messages`/`from_native_messages` |