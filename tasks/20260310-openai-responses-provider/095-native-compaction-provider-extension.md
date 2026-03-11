# Native Compaction Provider Extension

Short description: Add native conversation compaction as a provider extension capability for Responses-based providers, so compaction is provider-owned and Responses-native rather than only an application-plugin range summarization flow.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/070-usage-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/090-integration-native-retention-and-regression-tests.md`

## Goal

Provide a provider-extension-level **native compaction** capability that can use the Responses API compact endpoint (or equivalent provider-native compact flow) so compaction becomes part of provider behavior, not only an application action plugin.

The important distinction from the existing summarize-range plugin is:

1. Existing `summarize_range` is an application-layer workflow that replaces a selected message range with a visible assistant summary message.
2. Native compaction is a Responses-native context compaction/checkpointing capability whose retained artifacts should remain provider-native as long as possible and be suitable for future Responses requests.
3. Application actions may trigger native compaction, but they should not own the compaction logic itself.

## Important scope note

This subtask includes a **prerequisite core capability addition** as part of the same subtask. The prerequisite is intentionally high-level in this task file and requires additional research, planning, and design decisions before implementation.

This is not just a straight port of `plugins/summarize-range-app` into a provider extension. The work must preserve the semantic difference between:

1. human-readable summarization inserted into core message history
2. provider-native compaction artifacts used to reduce future Responses context

## Main implementation intent

The main part of this subtask is to introduce a provider-owned native compaction mechanism for `openai_responses` that:

1. can be triggered from higher layers when the user wants to compact a conversation or range
2. keeps the actual compaction logic in provider/core/extension contracts rather than app-plugin business logic
3. preserves tool/reasoning/native-history continuity for future turns
4. does not collapse the design into "just create a plain assistant summary message"

## High-level prerequisite core capability (part of this subtask)

Before implementation details are chosen, this subtask must resolve the core capability questions below.

1. Define how core/provider/extension contracts can support provider-native compaction requests and compaction results.
2. Define how session or action triggers invoke provider-extension compaction without coupling the capability to one application plugin.
3. Define what session/core data model changes, if any, are needed to retain provider-native compaction artifacts safely.
4. Define invariants for:
- native history continuity
- correctness with tool calls and reasoning metadata
- compatibility with slice/fork/modify history operations
- behavior when reloading sessions across fresh `AgentCore` instances

The prerequisite output should be a design note and/or follow-up implementation breakdown, not premature low-level coding decisions.

## Design questions that must be answered

1. What is the externally visible user action?
- Does "Summarize range" become a trigger for native compaction, remain a separate human-readable summary flow, or coexist with a new native-compaction action?
2. What is stored in session history after compaction?
- provider-native opaque compaction items only
- provider-native items plus a visible assistant placeholder/summary
- or both, with clearly defined ownership
3. How should compaction interact with existing history-editing operations?
- slice
- delete
- modify
- join/fork
4. Which layer is responsible for translating a user-selected range into a provider-native compaction request?
5. How should native compaction interact with tools, reasoning items, usage metadata, and native index ownership?

## Implementation direction (high-level)

1. Introduce provider extension plugin for native compaction in the `openai_responses` bundle.
2. Add the prerequisite core capability needed to trigger and retain provider-native compaction safely.
3. Integrate compaction trigger path with existing app/session actions where needed, while keeping ownership in provider/core/provider-extension layers.
4. Ensure compatibility or deliberate coexistence with existing `summarize-range-app` workflows during migration.

## Deliverables

1. A clarified design for native compaction ownership and invocation.
2. Any required core/plugin protocol additions to support provider-native compaction.
3. An `openai_responses` native compaction extension implementation if the design is resolved within this subtask.
4. If the design is not fully resolvable in one pass, explicit follow-up tasks and decisions recorded in completion notes.

## Test expectations

1. Add tests that validate compaction correctness at provider-extension level.
2. Add regression tests for native-history integrity after compaction.
3. Add compatibility tests for tool/reasoning/usage metadata after compaction.
4. Add tests that make the semantic difference from app-layer summarize-range explicit, unless the approved design intentionally merges the two flows.

## References

- Existing app-layer summarize implementation:
- `plugins/summarize-range-app/src/summarize_range_app/__init__.py`
- `plugins/summarize-range-app/tests/test_summarize_range_app_plugin_unit.py`
- `plugins/summarize-range-app/tests/test_summarize_range_app_via_agent_application.py`
- Current application action protocol:
- `core/python/agent_app/app_plugins.py`
- `core/python/agent_app/application_future.py`
- Existing Responses-native provider/extension patterns:
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_tools_extension.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_reasoning_extension.py`
- Current `openai_responses` implementation to integrate with:
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`
- Core native-history editing behavior:
- `core/python/agent_core/core.py`
- Protocol/docs:
- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`
- `plugins/docs/plugin-execution-order.md`
