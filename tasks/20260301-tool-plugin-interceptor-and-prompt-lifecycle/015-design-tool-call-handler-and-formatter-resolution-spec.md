# Design Tool Call Handler and Formatter Resolution Spec

Short description: Define the post-interception tool handling model (`can_handle_tool_call` + `handle_tool_call`), formatter ownership rules, deprecated compatibility formatting path, and stage routing semantics for prompt/result/formatted-output combinations.

Parent Task: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/000-main.md
Depends On: tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/010-design-toolplugin-interceptor-contract-and-prompt-schema.md

## Status

- Completed.
- Final design outcomes for this subtask are documented in:
  - `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/955-tool-interceptor-interface-proposal-metadata-array.md` (baseline dependency)
  - `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/956-tool-handler-and-formatter-resolution-spec.md` (primary artifact)

## Scope

- Define `can_handle_tool_call` and `handle_tool_call` as the primary call-execution path after pre-call interception.
- Define a common response envelope shared by interceptors and handler terminal outputs.
- Define deterministic stage routing rules for responses that include prompts, raw `tool_result`, and/or `formatted_content`.
- Define formatter ownership precedence and explicit override behavior.
- Define how `format_tool_result` and `to_display_format` remain as deprecated compatibility-only fallback.
- Define compatibility wrapper behavior for existing tools that only implement `execute_tool`/`stream_tool`/`format_tool_result`.

## Out Of Scope

- Implementing runtime orchestration and adapters.
- Frontend rendering implementation details.

## Proposed Steps

1. Specify hook signatures and ordering for interception, handler selection/execution, raw-result interception, and formatted-output interception.
2. Specify the common response envelope and valid key combinations per stage.
3. Specify meaningful-handler rules and first-responder selection semantics.
4. Specify continuation/resume matrix for:
   - prompt only,
   - prompt + raw result,
   - prompt + formatted output,
   - raw-only,
   - formatted-only.
5. Specify formatter ownership precedence and fallback behavior on resolution/format errors.
6. Specify deprecation guidance for legacy formatting hooks and migration path for plugin authors.
7. Publish a final spec artifact aligned with `955` metadata model.

## Deliverables

- Approved handler/formatter resolution spec.
- Approved stage-routing matrix for prompt/result/formatted flows.
- Approved compatibility/deprecation behavior for legacy formatting hooks.

## Success Criteria

1. Handler and formatter ownership rules are deterministic and implementation-ready.
2. Stage routing for mixed prompt/result/formatted outputs is unambiguous.
3. Existing tool plugins have a documented compatibility path with no immediate breakage.
4. Spec remains consistent with `955` metadata persistence semantics.

## Context References

- `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/955-tool-interceptor-interface-proposal-metadata-array.md`
- `tasks/20260301-tool-plugin-interceptor-and-prompt-lifecycle/956-tool-handler-and-formatter-resolution-spec.md`