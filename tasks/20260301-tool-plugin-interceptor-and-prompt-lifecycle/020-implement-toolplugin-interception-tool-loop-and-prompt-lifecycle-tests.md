# Implement ToolPlugin Interception, Tool Loop Orchestration, and Prompt Lifecycle Persistence (Core/Application, No Frontend)

Short description: Implement the new interception-capable tool contract and runtime behavior in core/application layers, including prompt lifecycle persistence as core messages and comprehensive tests, without frontend changes.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/010-design-toolplugin-interceptor-contract-and-prompt-schema.md

## Scope

- Implement `ToolPlugin` protocol updates and default behavior.
- Update tool wrappers/adapters for optional interception hooks and `priority` handling.
- Implement tool-loop interception orchestration for both phases.
- Persist prompt request/response lifecycle as core messages with metadata.
- Implement suspend/resume behavior tied to pending tool-call handling.
- Add backend/event/API plumbing required for prompt submit/resume flows.
- Add core/application tests for ordering, directives, lifecycle, and resume semantics.
- Keep frontend behavior unchanged in this subtask.

## Out Of Scope

- Mobile UI rendering changes.
- Desktop UI rendering changes.
- Production policy plugins beyond test fixtures.

## Proposed Steps

1. Apply protocol/interface changes in `ToolPlugin` and adapter/wrapper layers with no-op defaults.
2. Extend tool loop to run call-phase interceptors before execution and result-phase interceptors after execution.
3. Implement priority-based ordering (lower number first) and deterministic tie-break behavior.
4. Add generic directive handling path for transform/block/suspend/stop/continue.
5. Add prompt lifecycle core messages (`prompt_requested`, `prompt_answered` metadata model).
6. Wire prompt-response submission to re-enter the same interception phase with prior context and answer payload.
7. Implement pending-state handling so `decide later` style plugin logic can suspend without fabricating tool errors.
8. Add/adjust server endpoints and event shapes needed for non-UI consumers to list/respond pending prompts.
9. Add regression/integration tests across core + application layers and verify no behavior regression when interceptors are absent.

## Deliverables

- Updated tool plugin runtime with interception support.
- Prompt lifecycle persistence in session/core messages.
- Suspend/resume behavior for pending intercepted tool calls.
- Automated tests covering core/application behavior changes.

## Success Criteria

1. Existing non-interceptor tools still run unchanged.
2. Interceptors execute in deterministic priority order.
3. Prompt response correctly re-enters same phase with context.
4. Suspend/resume preserves pending tool calls without synthetic failures.
5. Tests cover ordering, directives, and lifecycle persistence.

## Context References

- `core/python/agent_core/types.py#L849`
- `core/python/agent_core/plugin/adapters.py#L526`
- `core/python/agent_core/plugin/tool.py#L15`
- `core/python/agent_app/tool_loop.py#L331`
- `core/python/agent_app/tool_loop.py#L458`
- `application/python/agent_terminal_app/server.py#L880`
- `application/python/agent_terminal_app/server.py#L2403`
- `core/python/tests/test_application_layer_tools.py`
- `application/python/tests/test_agent_terminal_app_server.py`
