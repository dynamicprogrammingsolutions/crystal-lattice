# Implement ToolPlugin Interception and Prompt Lifecycle Persistence (Spec 955, Core/Application, No Frontend)

Short description: Implement the interception-capable tool contract from spec `955` in core/application layers, including prompt lifecycle metadata persistence and tests, without the `956` handler/formatter upgrade.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/010-design-toolplugin-interceptor-contract-and-prompt-schema.md

## Requirements checklist

- [x] `ToolPlugin` protocol, wrappers, and adapters were extended with interception hooks and `priority` support.
- [x] Call-phase interception orchestration was added around normal tool execution, including `continue` / `prompt` / `respond` handling.
- [ ] Result-phase interception supports full prompt suspend/resume semantics end-to-end, not just transform/respond behavior.
- [x] Prompt lifecycle metadata is persisted on existing assistant/tool messages using `interception_current` and `interception_phases`.
- [ ] Prompt submission persists answered state in a spec-aligned way at submit time and keeps retained native history synchronized before resume.
- [x] Backend/API plumbing was added to surface pending prompts and accept prompt responses.
- [ ] Prompt-response submission is strongly correlated to the exact message/phase/tool-call being answered and resumes with the original effective request context.
- [x] Core/application tests and a reference interceptor fixture were added for ordering, lifecycle, and suspend/resume behavior.

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

## Execution plan

Backfilled after implementation branch review.

1. Extend plugin protocols, adapters, and wrappers with interception hooks and `priority` support while preserving no-op defaults for existing tools.
2. Implement call-phase and result-phase interception orchestration in the application tool loop, including metadata persistence on assistant/tool messages and suspend/resume handling for prompt flows.
3. Add server/API/event/client plumbing for discovering pending prompts, submitting prompt answers, and rendering prompt state in the existing message UI.
4. Add a metadata preservation helper for native-history providers plus a reference interceptor plugin fixture that exercises prompt gating and result transformation.
5. Add core/application/integration tests around ordering, prompt lifecycle persistence, suspend/resume behavior, and provider-matrix end-to-end validation.

## Completion Notes

Backfilled after implementation branch review.

- Implemented interception hooks across tool, extension, and feature protocol/wrapper layers in `core/python/agent_core/types.py`, `core/python/agent_core/plugin/adapters.py`, `core/python/agent_core/plugin/tool.py`, `core/python/agent_core/plugin/extension.py`, and `core/python/agent_core/plugin/feature.py`.
- Implemented interception orchestration in `core/python/agent_app/tool_loop.py`, including:
  - call-phase prompt/continue/respond handling
  - `interception_current` / `interception_phases` metadata writes on assistant and tool messages
  - suspend/resume behavior using pending tool calls already present in session history
  - emitted `tool_interceptor_prompt` events for client reload/resume behavior
- Added prompt-response endpoints in `application/python/agent_terminal_app/server.py` and matching SDK/client plumbing in:
  - `packages/frontend-sdk/src/backend/backend.ts`
  - `packages/frontend-sdk/src/backend/restBackend.ts`
  - `packages/frontend-sdk/src/chat/chatController.ts`
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- Added native-history metadata preservation helper `core/python/plugins/tool_interceptor_metadata_preserver.py` and wired it into example/test config, plus a packaged reference plugin in `plugins/interceptor-tool`.
- Added tests and fixtures in:
  - `core/python/tests/interceptor_tool.py`
  - `core/python/tests/test_application_layer_tools.py`
  - `core/python/tests/test_tool_interceptor_metadata_preserver.py`
  - `application/python/tests/test_agent_terminal_app_server.py`
  - `packages/frontend-sdk/src/integration/__tests__/backend.tool_interceptor.integration.test.ts`

Later review against task `010` / spec `955` found follow-up gaps that should be addressed in a separate remediation pass:

- Prompt submission mutates message state directly in the server and can leave retained native history stale.
- V1 scope drifted beyond the original design by adding plugin-side schema/materialization APIs, extension/feature interception, and a separate prompt read endpoint.
- `tool_result`-phase prompting is not fully implemented, and prompt-answer correlation / resume context preservation are weaker than the spec intended.
- Native-history preservation still depends on manual config in some flows, and frontend convergence currently relies on dirty/reload behavior instead of message-history-only reconciliation.