# Build Reference Interceptor Tool Plugin Scenario (Bash Approval + Output Truncation)

Short description: Implement a test/fixture interceptor-enabled tool plugin that demonstrates the complete example flow for pre-tool approval and post-tool oversized-output handling.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/020-implement-toolplugin-interception-tool-loop-and-prompt-lifecycle-tests.md

## Scope

- Implement a reference test plugin fixture using the new interception contract.
- Cover both `tool_call` and `tool_result` interception phases.
- Implement plugin-defined pre-tool buttons: `allow once`, `always allow bash`, `deny`, `deny and stop`, `decide later`.
- Implement post-tool oversized-output policy: auto-truncate or user-prompted truncation with optional byte input.
- Add integration tests proving end-to-end behavior.

## Out Of Scope

- Encoding these button semantics in core enums/types.
- Frontend polish beyond testability needs.

## Proposed Steps

1. Create test fixture plugin combining interception and tool execution logic.
2. Implement pre-tool decision handling paths:
   - `allow once` -> execute current call.
   - `always allow bash` -> persist plugin-local policy and continue.
   - `deny` -> emit tool error and continue loop.
   - `deny and stop` -> emit tool error and stop loop.
   - `decide later` -> suspend and keep call pending.
3. Implement post-tool output threshold handling:
   - auto-truncate path.
   - prompt-for-truncation path with optional byte input.
4. Add tests for suspend/resume, deny/stop, and truncation behaviors.
5. Verify all semantics are plugin-owned and core remains generic.

## Deliverables

- Reference interceptor test plugin fixture.
- End-to-end tests for required example behavior.
- Short usage notes in test docs/comments.

## Success Criteria

1. Example scenario runs fully through the new interception flow.
2. All listed decision paths are validated by automated tests.
3. Core remains free of workflow-specific decision enums.

## Context References

- `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md`
- `core/python/tests/test_application_layer_tools.py`
- `application/python/tests/test_agent_terminal_app_server.py`
- `core/python/agent_app/tool_loop.py#L331`
