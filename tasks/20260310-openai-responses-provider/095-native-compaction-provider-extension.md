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

## Approved plan (added during completion)

1. Add a generic, session-scoped action contract for provider extensions.
- extend the provider-extension protocol with optional action methods that are not compaction-specific:
  - `get_actions(state) -> list[dict]`
  - `execute_action(action_id, session, native_messages, params, state) -> dict`
- these actions are single-session only and operate on provider-native history plus validated action params
- `get_ui_elements(...)` remains the place where extensions define their own `session_action` UI entries, but those entries will execute through the new generic extension-action path rather than an application plugin

2. Add generic core orchestration for extension session actions.
- add `AgentCore.get_session_actions(config)` to enumerate enabled extension-owned actions for the selected provider/config
- add `AgentCore.execute_session_action(session, config, plugin_id, action_id, params)` to resolve the selected provider/extensions, prepare current native history, validate and dispatch the action, rebuild canonical core messages from the returned native history, and persist updated native-history integrity metadata
- keep the core change generic so the core only knows that an extension can transform one session's provider-native history into another valid provider-native history

3. Preserve the existing frontend-facing action model and app/server integration shape.
- application actions and extension session actions remain separate in ownership, but they should be discoverable through the same app/server action discovery surfaces
- preserve current frontend-facing `session_action` UI patterns and existing action execution flow
- add only the minimal routing metadata needed for backend dispatch, such as an explicit action owner marker when useful

4. Use the new generic action contract to implement compaction as the first concrete action.
- add an `openai_responses` extension that defines a session action for native compaction
- implement it with the OpenAI Python SDK `client.responses.compact(...)`
- keep compaction ownership inside the extension while the generic core action path handles session rebuild and persistence

5. Add tests in the same change and run focused suites.
- core tests for action discovery, validation, dispatch, native-history rewrite, and integrity preservation
- `openai_responses` tests for compact-action SDK call shaping and post-action native-history continuity
- app/server tests that extension-defined `session_action` UI elements are discoverable and executable through the existing action endpoints
- a regression test showing `summarize_range` remains distinct from native compaction

## Completion notes (added during completion)

### What changed

1. Added a generic session-scoped action contract for provider extensions in the core/plugin layer.
- `ProviderExtensionPlugin` now supports optional `get_actions(state)` and `execute_action(action_id, session, native_messages, params, state)` hooks
- wrappers/adapters were extended so provider extensions can declare session actions without being mis-modeled as application plugins
- `AgentCore` now has generic `get_session_actions(config)` and `execute_session_action(session, config, plugin_id, action_id, params)` orchestration

2. Kept the action model frontend-facing shape compatible while routing through existing backend surfaces.
- extension-contributed `session_action` / `message_action` UI elements are automatically marked with `action_owner: "provider_extension"`
- the existing `POST /actions` path now dispatches either application actions or provider-extension session actions
- `AgentApplication` gained generic dispatch plus a provider-extension session-action execution path that loads the session, resolves effective config, saves the updated session, and returns standard mutation / reload metadata

3. Implemented native compaction as the first concrete `openai_responses` session action.
- added `OpenAIResponsesNativeCompactionExtension`
- it defines a `compact_native_history` session action and corresponding UI element
- it calls `client.responses.compact(...)` via the OpenAI Python SDK
- the action returns compacted provider-native history and intentionally preserves the visible transcript instead of replacing it with a summary message
- when transcript preservation is requested, the core now clears stale `native_indices` from visible messages while keeping the compacted native history for future Responses turns

4. Registered the new extension in the `openai_responses` bundle.
- updated `plugins/openai_responses/agent_plugin.json`
- updated `plugins/openai_responses/src/openai_responses_plugins/__init__.py`

5. Added test coverage for the generic mechanism and the OpenAI-specific action.
- core tests for session-action discovery, validation, action-owner normalization, and native-history rewrite behavior
- application/server tests for discovery through existing session UI schema plus execution through `POST /actions`
- `openai_responses` tests for SDK compaction call shaping, input sanitization, transcript preservation, and future-turn continuity through compacted native history

### Files touched

1. `core/python/agent_core/types.py`
2. `core/python/agent_core/plugin/adapters.py`
3. `core/python/agent_core/plugin/extension.py`
4. `core/python/agent_core/plugin/provider.py`
5. `core/python/agent_core/core.py`
6. `core/python/agent_app/application_future.py`
7. `application/python/agent_terminal_app/server.py`
8. `core/python/tests/dummy_provider_extension_session_action.py`
9. `core/python/tests/test_provider_extension_session_actions.py`
10. `application/python/tests/test_provider_extension_session_actions_endpoints.py`
11. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`
12. `plugins/openai_responses/src/openai_responses_plugins/__init__.py`
13. `plugins/openai_responses/agent_plugin.json`
14. `plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py`

### Tests run

1. `pytest core/python/tests/test_provider_extension_session_actions.py application/python/tests/test_provider_extension_session_actions_endpoints.py plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py -q`
- result: `8 passed`

2. `pytest application/python/tests/test_application_actions_endpoints.py application/python/tests/test_provider_extension_session_actions_endpoints.py core/python/tests/test_provider_extension_session_actions.py plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py -q`
- result: `18 passed`

3. `ruff check core/python/tests/dummy_provider_extension_session_action.py core/python/tests/test_provider_extension_session_actions.py application/python/tests/test_provider_extension_session_actions_endpoints.py plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py core/python/agent_app/application_future.py`
- result: `All checks passed`

### Outcomes

1. Subtask `095` completed with a generic provider-extension session-action mechanism rather than a compaction-only core hook.
2. Native compaction for `openai_responses` now exists as an extension-owned session action using the OpenAI SDK compact API.
3. The visible transcript remains separate from provider-native compaction artifacts, preserving the distinction from `summarize_range`.
4. Existing backend action execution shape is preserved through `POST /actions`; discovery uses existing session UI schema elements with the new `action_owner` marker.

### Open issues

1. Session actions are discoverable today through existing session UI schema (`/sessions/{id}/ui-schema`) and executable through the existing action endpoint, but they are not included in the global `/application/actions` or `/application/ui-schema` listings because those remain application-plugin scoped.
2. The real integration tests pass, but they emit SDK/Pydantic serialization warnings around OpenAI response model types during `model_dump` conversion; these warnings did not block functionality and were not addressed in this subtask.

## Follow-up approved plan (added during completion)

1. Make native-history rebuild mandatory after provider-extension session actions.
- remove the optional transcript-preservation path from the core session-action execution flow
- require session actions to return replacement native history and always rebuild visible `session.messages` from that native history

2. Represent compacted history explicitly in visible messages.
- map provider-native compaction artifacts to a visible assistant placeholder message with explanatory content
- store round-trip metadata on that placeholder so converting back to native messages remains lossless for future requests

3. Support prefix-slice compaction.
- update the native compaction action to accept an end index representing the slice `[:end]`
- enforce that compaction starts from the first message only
- replace only that prefix with the compacted representation while preserving the untouched suffix

4. Add integration coverage for both full and partial compaction.
- include a full-compaction integration test that sends another message afterwards
- include a partial-compaction integration test that sends another message afterwards
- if partial compaction fails for provider reasons that do not appear fixable in code, keep the failure visible and document it rather than hiding it

## Follow-up completion notes (added during completion)

### What changed

1. Made post-action rebuild mandatory again.
- `AgentCore.execute_session_action(...)` now always rebuilds visible `session.messages` from returned native history
- the temporary transcript-preservation path is gone

2. Added explicit visible compaction placeholders.
- `OpenAIResponsesNativeCompactionExtension` now maps compacted native segments to a regular assistant message with explanatory content
- placeholder metadata stores the underlying native segment under `metadata.openai_responses_compaction.native_segment`
- converting core messages back to native messages expands that placeholder back into the stored native compaction segment

3. Implemented prefix-slice compaction.
- `compact_native_history` now accepts optional `end_index` and interprets it as the exclusive slice end for `[:end_index]`
- the extension validates that the chosen visible prefix maps to a contiguous native prefix before calling `responses.compact(...)`
- only the selected prefix is compacted; the untouched suffix stays in native history and remains visible after rebuild

4. Fixed follow-up request compatibility after compaction.
- sanitized compacted native items before re-sending them to the Responses API
- stripped unsupported fields observed during real integration runs (`phase`, `annotations`, `logprobs`, `created_by` for compaction items, etc.)
- verified that both fully compacted and partially compacted sessions can send another message successfully with the real provider

5. Added and ran integration coverage for both full and partial compaction.
- new integration file: `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py`
- both tests compact, then send another message afterward to verify native-history validity survives the compaction step

### Additional files touched in the follow-up

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
2. `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py`
3. `plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py`

### Follow-up tests run

1. `pytest core/python/tests/test_provider_extension_session_actions.py application/python/tests/test_provider_extension_session_actions_endpoints.py plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py -q`
- result: `10 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py -q -m 'integration and openai'`
- first run failed with real-provider validation errors on replayed compacted items
- after sanitization fixes, rerun result: `2 passed`

3. `pytest application/python/tests/test_application_actions_endpoints.py application/python/tests/test_provider_extension_session_actions_endpoints.py core/python/tests/test_provider_extension_session_actions.py plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py -q`
- result: `21 passed`

### Updated outcome

1. The visible transcript is now always rebuilt from native history after compaction.
2. Compacted ranges are shown explicitly as assistant placeholder messages instead of silently preserving old visible messages.
3. Prefix-slice compaction `[:end_index]` works with the real OpenAI Responses provider in the tested scenarios.
4. Both full and partial compaction survived a follow-up turn in real integration tests.
