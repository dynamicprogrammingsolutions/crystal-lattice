# 070 - Core Rebuild After Native Initialize Changes

Short description: Fix the core request paths so that when `initialize_request` structurally changes provider-native history, the returned `Session.messages` are rebuilt from full retained native history instead of only appending final response messages.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/060-simplified-system-message-configs-and-minimal-dynamics.md`

## Why This Follow-up Exists

During follow-up review of subtask `060`, we found a core behavior bug rather than a `feature-system-message` bug.

The current `SystemMessageFeature` intentionally keeps the template form in retained native history. That part should stay as-is so users can edit the template system message rather than a compiled snapshot.

The actual problem is that the normal request-completion paths do not rebuild `Session.messages` when `initialize_request(...)` inserts or otherwise structurally changes native history. This means:

1. `session.metadata["native_messages"]` can contain a system message injected by the feature.
2. But `session.messages` may not reflect that inserted native message after the request.
3. Session-editing helpers like `add_message(...)` do rebuild from native history, so request execution and session mutation behave inconsistently.

The user explicitly called this out as the bug to fix.

## User Decision To Preserve

Do not change the `SystemMessageFeature` policy of retaining template content in native history.

The requested fix is:

1. in core request execution
2. based on detecting that `initialize_request(...)` returned a different native message array
3. using referential inequality as the change signal

Quote/paraphrase of the design guidance from the user:

1. The bug is in the core, not in `SystemMessageFeature`.
2. It is OK and intentional that the feature stores only the template in retained native messages.
3. What is wrong is that when the native message is added at the beginning of the array, the core rebuild is not run.
4. This can be detected because plugins should return a new array only when there is a real native-history change.

## Current State Summary

### Full-native rebuild exists, but only in edit/session-action flows

The core already has a full native-history rebuild helper:

- `core/python/agent_core/core.py:1532`

And it is already used by append/edit/session-action code paths, for example:

- `core/python/agent_core/core.py:177`
- `core/python/agent_core/core.py:282`
- `core/python/agent_core/core.py:405`
- `core/python/agent_core/core.py:2342`

That means the framework already has the machinery needed for the request-path fix.

### Request completion currently only appends finals

In `_pre_request(...)`, the provider/feature `initialize_request(...)` chain can modify full native history:

- `core/python/agent_core/core.py:1611`
- `core/python/agent_core/core.py:1680`
- `core/python/agent_core/core.py:1684`

But in `send_request(...)`, the returned session is built from existing `session.messages` plus converted finals only:

- `core/python/agent_core/core.py:1741`
- `core/python/agent_core/core.py:1773`
- `core/python/agent_core/core.py:1790`
- `core/python/agent_core/core.py:1796`

Likewise in `send_request_stream(...)`:

- `core/python/agent_core/core.py:1850`
- `core/python/agent_core/core.py:1894`
- `core/python/agent_core/core.py:1914`
- `core/python/agent_core/core.py:1917`

So the full retained native history is saved, but the visible core message list is not rebuilt when request initialization inserts a system message.

### The current system-message feature does structurally change native history

`SystemMessageFeature.initialize_request(...)` currently:

1. copies the incoming native array into `working_native`
2. prepends a synthetic native `system` message with template content when needed
3. renders compiled text only into `state["request"]["messages"]`
4. returns `working_native` as retained native history

Relevant code:

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:683`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:705`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:787`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:832`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:835`

Important nuance:

`SystemMessageFeature.initialize_request(...)` currently starts with `working_native = list(native_messages)` even for some no-op cases, so referential inequality is not yet a fully reliable change signal. The user still wants identity-based change detection, so this task may need minimal supporting adjustments in no-op paths to make that signal trustworthy.

## Concrete Goal

After this fix:

1. If `initialize_request(...)` changes native history structurally, the returned `Session.messages` from both `send_request(...)` and `send_request_stream(...)` should be rebuilt from the final retained native history.
2. If `initialize_request(...)` does not change native history, the current append-finals behavior should remain.
3. `final_core` should still represent only the new response messages for events/final yields.
4. Retained native history should continue to keep the template content for feature-inserted system messages.

## Expected Implementation Direction

### 1. Detect native-history changes during request initialization

Recommended approach:

1. Thread an extra boolean out of `_pre_request(...)`, such as `native_history_changed_during_initialize`.
2. Set it whenever the provider or any feature `initialize_request(...)` returns a different native-message array object.
3. Keep this detection narrow to actual request-initialize steps, not the earlier stateless `to_native_messages` transforms.

Possible implementation site:

- `core/python/agent_core/core.py:1611`

### 2. Rebuild returned session messages only when needed

In both request paths:

1. keep `final_core` as the converted finals used for streamed/final events
2. keep storing the full retained `native_messages`
3. when the new boolean is true, compute `all_messages_after` from `_rebuild_core_from_native(native_messages, config)` instead of `[ *session.messages, *appended ]`

Likely change sites:

- `core/python/agent_core/core.py:1703`
- `core/python/agent_core/core.py:1811`

### 3. Make identity-based detection dependable

The user wants referential inequality to be the signal. If current no-op paths defeat that assumption, make the minimal supporting adjustments required.

Things to inspect carefully:

1. provider wrapper/default-adapter behavior for `initialize_request(...)`
2. `SystemMessageFeature.initialize_request(...)` no-op paths
3. any built-in provider/feature that always returns `list(native_messages)` even on no-op

Do not broaden this into a larger refactor. The goal is only to make the identity signal meaningful enough for this bugfix.

## Acceptance Criteria

1. First request with a config-backed system message and no user `system` message produces a returned session whose `messages` include a `system` row rebuilt from native history.
2. The same is true for `send_request_stream(...)`.
3. Repeated requests do not duplicate that system message.
4. Retained native history still stores the template form, not the compiled prompt text.
5. Existing request-final event behavior remains unchanged: only actual new response finals are emitted as `final_core`.

## Tests To Add

### Core regression tests

Add focused regression coverage under `core/python/tests/` for both request paths.

Suggested test cases:

1. Non-streaming request rebuilds session messages when `initialize_request(...)` inserts a native system message.
2. Streaming request rebuilds session messages when `initialize_request(...)` inserts a native system message.
3. The rebuilt `session.messages` include exactly one `system` message after a second request.
4. The retained `session.metadata["native_messages"]` system message still contains the template text.

### Existing feature integration tests to update or extend

Existing relevant tests:

- `plugins/feature-system-message/tests/test_system_message_integration_with_echo.py`
- `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`

Add or adjust assertions so they prove the returned session now contains the rebuilt system message rather than checking only retained native history.

## Verification Required

The user asked that this bugfix be handled separately and that unit and integration tests run after the change.

At minimum, run:

1. `pytest core/python/tests -q`
2. `pytest plugins/feature-system-message/tests -q`
3. `pytest application/python/tests -q`

If additional touched suites become relevant during implementation, run them too.

## Commit Boundary Requested By User

This fix should be handled as its own change and should be landed in a separate commit from the later config/frontend follow-up.

## Non-goals For This Task

Do not include the later follow-up work here:

1. portable copied config under `default_config/`
2. compiled-system-message logging
3. `compiled_content` metadata/UI work
4. frontend collapsible rendering

Those belong in the next task file.

## Plan Added During Completion

Added during completion on approval.

1. Update `AgentCore._pre_request(...)` to track whether the provider/feature `initialize_request(...)` chain changed the native message array by identity.
2. Update `send_request(...)` and `send_request_stream(...)` to rebuild returned `Session.messages` from final retained native history when that flag is set, while leaving emitted `final_core` response finals unchanged.
3. Make the identity signal dependable by preserving native-message identity in default no-op `initialize_request(...)` paths and in no-op `SystemMessageFeature.initialize_request(...)` paths.
4. Add regression coverage for both non-streaming and streaming request paths, plus existing feature integration assertions showing the returned session now includes the rebuilt system message while retained native history still stores the template.
5. Run the requested unit and integration suites for the core, system-message feature, and application layers.

## Completion Notes Added During Completion

Implemented:

1. `AgentCore._pre_request(...)` now returns a `native_history_changed` flag and coalesces equal native-message lists back to the prior object so identity-based change detection remains meaningful even when plugins return shallow copies.
2. `send_request(...)`, `send_request_stream(...)`, and `send_request_stream_async(...)` now rebuild the returned `Session.messages` from retained native history when request initialization structurally changes native messages, while keeping emitted `final_core` response finals unchanged.
3. Provider/default `initialize_request(...)` no-op paths were adjusted to preserve native-message identity where possible, and `SystemMessageFeature.initialize_request(...)` no longer copies native history on no-op paths.
4. Added pure-core regression coverage in `core/python/tests/test_request_rebuild_after_initialize_change.py` for non-streaming and streaming rebuild behavior.
5. Updated `plugins/feature-system-message/tests/test_system_message_integration_with_echo.py` and `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py` so they assert the returned session now includes the rebuilt system message.
6. Updated private-helper tests that call `_pre_request(...)` directly to use the new 4-tuple shape.

Files touched:

1. `core/python/agent_core/core.py`
2. `core/python/agent_core/plugin/provider.py`
3. `core/python/agent_core/plugin/adapters.py`
4. `core/python/agent_core/types.py`
5. `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
6. `core/python/tests/test_request_rebuild_after_initialize_change.py`
7. `core/python/tests/test_request_options_feature.py`
8. `plugins/feature-system-message/tests/test_system_message_integration_with_echo.py`
9. `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`
10. `plugins/openrouter/tests/test_openrouter_reasoning_extension_unit.py`

Verification run:

Passing focused coverage:

1. `ruff check core/python/agent_core/core.py core/python/agent_core/plugin/provider.py core/python/agent_core/plugin/adapters.py core/python/agent_core/types.py plugins/feature-system-message/src/feature_system_message/system_message_feature.py core/python/tests/test_request_rebuild_after_initialize_change.py plugins/feature-system-message/tests/test_system_message_integration_with_echo.py plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`
2. `pytest core/python/tests/test_request_rebuild_after_initialize_change.py -q`
3. `pytest core/python/tests/test_request_options_feature.py -q`
4. `pytest plugins/feature-system-message/tests/test_system_message_integration_with_echo.py -q`
5. `pytest plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py -q`
6. `pytest plugins/feature-system-message/tests -q`
7. `pytest plugins/openrouter/tests/test_openrouter_reasoning_extension_unit.py -q`

Requested broad suite runs completed:

1. `pytest core/python/tests -q`
2. `pytest application/python/tests -q`

Broad-suite failures observed but not caused by this task's rebuild change:

1. Existing Ollama/integration behavior failures in `core/python/tests/test_application_layer_integration.py` and `core/python/tests/test_openai_tools_with_ollama_stream.py`
2. Existing Node tool JSON-serialization failures in `core/python/tests/test_application_layer_integration_node_tools_ollama.py` and `application/python/tests/test_agent_terminal_app_server_ollama_js_fs_tools.py`
3. Existing unrelated application failures in `core/python/tests/test_application_session_lifecycles.py`, `application/python/tests/test_openai_responses_attachment_endpoints.py`, `application/python/tests/test_openai_responses_session_asset_send_path.py`, and `application/python/tests/test_provider_extension_session_actions_endpoints.py`

Outcome:

The `070` bugfix itself is verified and the targeted system-message/native-history regression coverage passes. The broader requested suites were run and surfaced unrelated pre-existing failures outside this scope.
