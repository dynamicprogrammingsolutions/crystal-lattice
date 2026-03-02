# Implement Tool Handler and Formatter Upgrade (Spec 956)

Short description: Implement the post-955 runtime upgrade from spec `956`, introducing `can_handle_tool_call`/`handle_tool_call`, formatter ownership resolution, formatted-output interception, and deprecated compatibility fallback behavior.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/015-design-tool-call-handler-and-formatter-resolution-spec.md, tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/020-implement-toolplugin-interception-tool-loop-and-prompt-lifecycle-tests.md, tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/050-build-reference-interceptor-tool-plugin-scenario.md

## Scope

- Implement handler-selection and execution hooks from `956`:
  - `can_handle_tool_call`,
  - `handle_tool_call`.
- Implement stage-aware routing for handler/interceptor outputs:
  - pre-call interception,
  - handler output,
  - raw-result interception,
  - formatted-output interception.
- Implement `intercept_tool_output` hook.
- Implement formatter ownership resolution and optional `formatter_plugin` override.
- Implement deprecated compatibility fallback path for `format_tool_result` and `to_display_format`.
- Preserve `955` metadata persistence model while extending `stage` semantics where needed.
- Add tests for mixed output combinations (`prompt`, `tool_result`, `formatted_content`, `display`) and resume-stage routing.

## Out Of Scope

- Re-designing metadata model introduced in `955`.
- Mobile/Desktop UI implementation changes.

## Proposed Steps

1. Introduce optional handler/output hooks in types, adapters, and wrappers.
2. Implement first-meaningful-responder handler selection with deterministic ordering.
3. Implement common-response-envelope handling for handler terminal outputs.
4. Implement stage routing matrix from `956`:
   - formatted path,
   - raw-result path,
   - pre-call fallback path,
   - prompt+resume combinations.
5. Implement formatter ownership precedence and error fallback behavior.
6. Preserve/update metadata event recording with stage attribution (`plugin_response.stage`).
7. Add regression tests for compatibility wrappers and old plugins.
8. Update docs to mark legacy formatting hooks as deprecated compatibility path.

## Deliverables

- Runtime implementation of `956` handler/formatter upgrade.
- Tests covering stage routing, ownership rules, and compatibility fallback.
- Updated docs and migration notes for plugin authors.

## Success Criteria

1. `020` (`955`) behavior remains valid and backward-compatible after upgrade.
2. Handler selection and formatter ownership are deterministic and test-covered.
3. Prompt/result/formatted combinations route to the correct stage on first run and resume.
4. Existing plugins without new hooks still function correctly through compatibility wrappers.

## Context References

- `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/956-tool-handler-and-formatter-resolution-spec.md`
- `core/python/agent_core/types.py`
- `core/python/agent_core/plugin/adapters.py`
- `core/python/agent_core/plugin/tool.py`
- `core/python/agent_app/tool_loop.py`