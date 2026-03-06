# Implement ToolPlugin Interception and Prompt Lifecycle Persistence (Spec 955, Core/Application, No Frontend)

Short description: Implement the interception-capable tool contract from spec `955` in core/application layers, including prompt lifecycle metadata persistence and tests, without the `956` handler/formatter upgrade.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/010-design-toolplugin-interceptor-contract-and-prompt-schema.md

## Scope

- Implement `ToolPlugin` protocol updates from `955` (`intercept_tool_call`, `intercept_tool_result`, optional `priority`).
- Update tool wrappers/adapters for optional interception hooks and deterministic ordering support.
- Keep current execution path (`execute_tool` / `stream_tool` + `format_tool_result` + `to_display_format`) and run interception around it.
- Implement tool-loop interception orchestration for both phases.
- Persist lifecycle metadata in message metadata using:
  - `interception_phases` append-only events (`prompt_response`, `plugin_response`),
  - `interception_current` current/final snapshot.
- Implement suspend/resume behavior tied to pending tool-call handling and prompt answers.
- Add backend/event/API plumbing required for listing pending prompts and submitting answers.
- Add core/application tests for ordering, directives, lifecycle, and resume semantics.

## Out Of Scope

- `956` handler/formatter upgrade (`can_handle_tool_call`, `handle_tool_call`, `intercept_tool_output`).
- Mobile UI rendering changes.
- Desktop UI rendering changes.
- Production policy plugins beyond test fixtures.

## Proposed Steps

1. Apply protocol/interface changes in `ToolPlugin` and adapter/wrapper layers with no-op defaults.
2. Extend tool loop to run:
   - call-phase interceptors before tool execution,
   - result-phase interceptors after tool execution.
3. Implement priority-based ordering (lower number first) and deterministic tie-break behavior.
4. Implement directive handling for `continue`/`prompt`/`respond` from `955`.
5. Implement metadata persistence model:
   - `interception_phases` append-only events,
   - `interception_current` snapshot,
   - no-op `continue` not persisted.
6. Wire prompt-response submission to re-enter the same phase with prior context and answer payload.
7. Implement pending-state handling so `decide later` style plugin logic can suspend without synthetic tool failures.
8. Add/adjust server endpoints and event shapes needed for non-UI consumers to list/respond pending prompts.
9. Add regression/integration tests across core + application layers and verify no behavior regression when interceptors are absent.

## Deliverables

- Updated tool runtime with interception support from `955`.
- Prompt lifecycle persistence in session/core message metadata.
- Suspend/resume behavior for pending intercepted tool calls.
- Automated tests covering core/application behavior changes.

## Success Criteria

1. Existing non-interceptor tools still run unchanged.
2. Interceptors execute in deterministic priority/order semantics.
3. Prompt response correctly re-enters the same phase with context.
4. Suspend/resume preserves pending tool calls without synthetic failures.
5. Tests cover ordering, directives, and metadata lifecycle persistence.
6. No `956`-only behavior is required for completion of this subtask.

## Context References

- `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/955-tool-interceptor-interface-proposal-metadata-array.md`
- `core/python/agent_core/types.py#L849`
- `core/python/agent_core/plugin/adapters.py#L526`
- `core/python/agent_core/plugin/tool.py#L15`
- `core/python/agent_app/tool_loop.py#L331`
- `core/python/agent_app/tool_loop.py#L458`
- `application/python/agent_terminal_app/server.py#L880`
- `application/python/agent_terminal_app/server.py#L2403`
- `core/python/tests/test_application_layer_tools.py`
- `application/python/tests/test_agent_terminal_app_server.py`