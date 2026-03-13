# Cross-Provider Agent Switch Native Rebuild Regressions

Short description: Add an application-level integration test that proves a session can start on `openai_responses`, switch agents to `openrouter` chat completions, manually rebuild native history, and continue working through follow-up requests plus message delete/fork/edit operations.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/061-openai-responses-native-conversion-and-reasoning-followup-regressions.md`

## Problem summary

We now have coverage for OpenAI Responses native-history rebuilds and follow-up reasoning/tool flows, but we do not yet have a regression test for switching a live session between incompatible providers.

The current product expectation is intentionally manual:

1. Change the session's agent to one backed by a different provider.
2. Rebuild provider-native history from the visible core messages.
3. Continue the conversation using the new provider.

That manual flow is acceptable for now, but it is exactly the kind of cross-provider path that can regress silently. We need a real application-level test that proves the flow works with:

1. `openai_responses` as the original provider.
2. `openrouter` chat completions as the new provider.
3. A session shape that already includes at least two reasoning/tool turns before the switch.
4. Additional history-changing operations after conversion: delete, fork, and edit.

## What exists already

### OpenAI application-level reasoning test to copy/adapt

The best starting point is the test introduced by `061`:

- [plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py:17](plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py:17)

Useful pieces already present there:

1. Shared `reasoning_test` prompt helpers and expected-answer calculation.
2. `_make_config(...)` for an `AgentApplication` config.
3. `_run_request(...)` helper that captures checkpoints and persists the final session.
4. A proven two-turn scenario using `read_file` with reasoning + tool calls.

### Agent switch only changes runtime metadata

`AgentApplication.update_agent(...)` only swaps runtime/config context and updates `session.metadata["agent_id"]`. It does not automatically translate retained native history between providers.

- [core/python/agent_app/application_future.py:1476](core/python/agent_app/application_future.py:1476)

That means this task should explicitly test the manual rebuild step after switching agents.

### Rebuild-native application plugin already implements the manual step

The rebuild action is already implemented in the `rebuild-native-app` plugin and calls `core.rebuild_native_history(...)` using the effective config for the session.

- [plugins/rebuild-native-app/src/rebuild_native_app/__init__.py:105](plugins/rebuild-native-app/src/rebuild_native_app/__init__.py:105)

The test should use this application plugin path when possible, because that is the actual user-facing mechanism today.

### Core history-edit helpers that should survive the conversion

The core already has the native-preserving operations we want to validate after the provider switch:

- `modify_message(...)`: [core/python/agent_core/core.py:694](core/python/agent_core/core.py:694)
- `slice_session(...)` for message deletion/removal: [core/python/agent_core/core.py:775](core/python/agent_core/core.py:775)
- `fork_session(...)`: [core/python/agent_core/core.py:988](core/python/agent_core/core.py:988)
- `AgentApplication.fork_session(...)`: [core/python/agent_app/application_future.py:1435](core/python/agent_app/application_future.py:1435)

These flows are already meant to preserve or rebuild native history when possible. This task adds a cross-provider regression test to prove they still behave after a manual provider migration.

### OpenRouter app/config references

For the switched-to provider, use the regular OpenRouter chat-completions provider bundle, not `openrouter_responses`.

Relevant references:

- OpenRouter AgentApplication config pattern: [plugins/openrouter/tests/test_agent_application_openrouter_puzzle.py:62](plugins/openrouter/tests/test_agent_application_openrouter_puzzle.py:62)
- OpenRouter reasoning + `read_file` scenario using the same `reasoning_test` fixture: [plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py:56](plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py:56)

## Desired behavior to pin down

After a session has accumulated at least two completed OpenAI Responses reasoning/tool turns, we should be able to:

1. Switch the session to an OpenRouter-backed agent.
2. Rebuild native history under the OpenRouter config.
3. Send a third request successfully through OpenRouter.
4. Perform delete, fork, and edit operations on the converted session.
5. After each such operation, verify the core/native history shape is still coherent.
6. After each such operation, send another follow-up prompt and receive a valid provider response instead of a provider-side shape error.

This is not about automatic cross-provider migration during `update_agent(...)`. It is explicitly about protecting the current manual workflow.

## Recommended implementation plan

### 1. Extend the existing OpenAI AgentApplication reasoning test setup to include two agents

The easiest route is to reuse or lightly refactor the helpers in:

- [plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py:63](plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py:63)

Recommended config changes:

1. Keep the existing `openai_responses` provider entry.
2. Add a second provider entry for `openrouter` using the chat-completions provider.
3. Add two agents, for example:
   - `responses_agent` -> `openai_responses`
   - `chat_agent` -> `openrouter`
4. Load the OpenRouter provider + tools + reasoning extensions.
5. Load the rebuild-native application plugin.
6. Ensure `plugin_cache_dir` is present if the test uses `path:` plugin loading.

Likely plugin entries needed:

1. `openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider`
2. `openai_responses_plugins.openai_responses_tools_extension.OpenAIResponsesToolsExtension`
3. `openai_responses_plugins.openai_responses_reasoning_extension.OpenAIResponsesReasoningExtension`
4. `openrouter_plugins.openrouter_provider.OpenRouterProvider`
5. `openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension`
6. `openrouter_plugins.openrouter_reasoning_extension.OpenRouterReasoningExtension`
7. `plugins.request_options_feature.RequestOptionsFeature`
8. `plugins.file_reader_tool.FileReaderTool`
9. `rebuild_native_app.RebuildNativeAppPlugin` or a `path:` entry for `plugins/rebuild-native-app`

Use `OPENAI_API_KEY` and `OPENROUTER_API_KEY` from the repo root `.env`. This new test should skip unless both are available.

### 2. Build the baseline session on `openai_responses`

Start from the application-level reasoning test structure already in place.

Required baseline:

1. Create a session on the OpenAI Responses agent.
2. Run the first reasoning/tool turn with the default seed.
3. Run the second reasoning/tool turn with a different seed.
4. Assert the second turn completed successfully and appended fresh native history.

This baseline should intentionally mirror the real-world history shape that `061` stabilized.

### 3. Switch agents and rebuild native history explicitly

Use the application-level switch flow, then the rebuild-native app action.

Recommended sequence:

1. Call `app.update_agent("chat_agent", session)`.
2. Save the returned switched session.
3. Invoke the rebuild-native application action for that session id.
4. Reload the session from storage.
5. Confirm the reloaded session now has OpenRouter-compatible native history.

Important detail:

The rebuild action loads the session from the app store internally, so the switched session must be saved before the action is executed.

### 4. Prove the switched session can continue with a third request

After the rebuild, add a third user prompt with a fresh seed and send another request through the OpenRouter agent.

Success criteria:

1. The request completes without provider-format errors.
2. The tool loop still works under OpenRouter.
3. The final answer matches the expected label for the third seed.
4. Native history grows in the new provider's format after the follow-up.

### 5. Derive follow-up variants for delete, fork, and edit regressions

After the successful post-switch third turn, create separate branches from that converted session and test each operation independently.

Recommended branches:

1. Delete branch:
   - remove a coherent message slice using `core.slice_session(...)`
   - prefer deleting a full tail turn or another self-contained visible segment rather than a random single tool message
2. Fork branch:
   - use `app.fork_session(...)` or `core.fork_session(...)` to keep an early prefix of the converted session
3. Edit branch:
   - modify a user or assistant message using `core.modify_message(...)`

Using separate branches keeps the assertions legible and avoids conflating multiple mutations in one session.

## Assertions to add

For the rebuilt switched session itself, and again for each delete/fork/edit branch, add both structural assertions and behavioral assertions.

### Structural assertions

Verify both the core message list and the retained native history have a sane shape.

At minimum assert:

1. `session.metadata["native_messages"]` is a non-empty list.
2. `session.metadata["native_messages_integrity"]` exists.
3. Every visible message that carries `metadata.native_indices` has a list of valid integer indices within the current native history bounds.
4. The visible message roles remain coherent for a tool conversation, meaning there are no orphaned tool messages at the very end of the session and no obviously broken role ordering after rebuild.
5. The converted session still contains the expected high-level conversation shape: system/user/assistant turns plus tool messages for the tool turns.

Do not overfit the assertions to exact provider-native cardinality. The important contract is that the visible/core session remains coherent and the new provider can keep talking.

### Behavioral assertions

For each of the following, send another prompt after the operation and assert the provider responds successfully:

1. The rebuilt post-switch session.
2. The delete branch.
3. The fork branch.
4. The edit branch.

The follow-up prompt can reuse the reasoning fixture with another fresh seed so the provider has to perform a real next turn instead of echoing prior content.

If the native/core shape is wrong, OpenRouter is likely to reject the request. That makes the successful follow-up the most important end-to-end regression assertion.

## Suggested test placement

Prefer adding this near the existing OpenAI application-level reasoning coverage, either by:

1. Extending [plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py](plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py), or
2. Creating a focused sibling file such as `plugins/openai_responses/tests/test_agent_application_openai_responses_provider_switch.py`

If helper reuse starts to dominate, extract shared prompt/config/session helpers into a small local test helper module under `plugins/openai_responses/tests/`.

## Test marks and environment

This should be a live integration test and will require both providers.

Recommended marks:

1. `@pytest.mark.integration`
2. `@pytest.mark.openai`
3. `@pytest.mark.openrouter`

Skip unless both `OPENAI_API_KEY` and `OPENROUTER_API_KEY` are available.

## Notes for the implementing agent

1. Keep the task scoped to tests unless investigation exposes a real bug in the switch/rebuild/edit path.
2. The product behavior here is still manual. Do not turn this into an automatic rebuild-on-switch change as part of the test task.
3. If a structural assertion is hard to make provider-agnostic, prefer a weaker shape invariant plus a stronger behavioral follow-up request.
4. The highest-value regression is: OpenAI Responses two-turn history -> switch to OpenRouter chat -> rebuild native -> continue successfully.

---

## Execution plan added during task completion

1. Add a dedicated live integration test file under `plugins/openai_responses/tests/` for the cross-provider migration scenario instead of extending the existing OpenAI reasoning test inline.
2. Build a two-agent `AgentApplication` config that includes:
   - an `openai_responses` provider using `gpt-5-mini`
   - an `openrouter` provider using chat completions with `openai/gpt-5-mini`
   - the OpenAI/OpenRouter reasoning and tools extensions
   - `plugins.request_options_feature.RequestOptionsFeature`
   - `plugins.file_reader_tool.FileReaderTool`
   - the `rebuild_native` application plugin
   - `plugin_cache_dir` so the application plugin manager can load the rebuild plugin reliably
3. Skip the test unless both `OPENAI_API_KEY` and `OPENROUTER_API_KEY` are available.
4. Reuse the existing reasoning fixture inputs and expected-label calculation pattern so the test exercises the same real tool/reasoning workflow already covered in the OpenAI application-level test.
5. Create a baseline session on the OpenAI Responses agent, then run two completed reasoning/tool turns with distinct seeds and assert both turns succeed and grow retained native history.
6. Switch the live session to the OpenRouter-backed agent via `app.update_agent(...)`, save that switched session, execute the rebuild action through `app.execute_application_action("rebuild_native", "rebuild_native_history", {"session_id": ...})`, and reload the saved session from storage.
7. Assert the rebuilt switched session has coherent retained native history using provider-agnostic checks:
   - `session.metadata["native_messages"]` is a non-empty list
   - `session.metadata["native_messages_integrity"]` exists
   - any visible-message `metadata.native_indices` values are integer indices within the current native-history bounds
   - the visible transcript does not end in an orphaned tool message
8. Send a third prompt through the rebuilt OpenRouter session and assert the request completes, tool activity still occurs, the final assistant answer matches the expected label for that seed, and native history grows again.
9. Branch from the converted session into independent delete, fork, and edit scenarios:
   - delete: remove a coherent whole-turn tail slice rather than a single arbitrary tool message
   - fork: use `app.fork_session(...)` to keep a coherent prefix of the converted session
   - edit: use `core.modify_message(...)` on a visible non-tool message that has native mappings
10. After each branch mutation, save/reload as needed, rerun the same structural shape checks, then send another fresh-seed follow-up request and assert OpenRouter responds successfully. The successful follow-up is the main regression signal that native/core state is still compatible after migration and history edits.
11. Verify the new test directly with pytest using the combined integration marks, without broadening scope into product behavior changes unless the test exposes a genuine bug.

---

## Completion notes added during task completion

Implemented the task with a new live integration regression test at `plugins/openai_responses/tests/test_agent_application_openai_responses_provider_switch.py`.

What the new test covers:
1. Builds a two-agent `AgentApplication` config using `openai_responses` first and `openrouter` chat completions second.
2. Loads the OpenAI Responses provider bundle, the OpenRouter provider bundle, `RequestOptionsFeature`, `FileReaderTool`, and the `rebuild_native` application plugin through the application plugin manager.
3. Creates a baseline session on the OpenAI Responses agent and completes two reasoning/tool turns.
4. Switches the live session to the OpenRouter-backed agent, persists that switch, runs the `rebuild_native_history` application action, reloads the session, and verifies the rebuilt native/core shape.
5. Sends a successful third follow-up request through OpenRouter after the rebuild.
6. Creates separate delete, fork, and edit branches from the converted session and confirms each branch can still accept a fresh follow-up request after the mutation.

During implementation, the new regression test exposed two real bugs and both were fixed:
1. `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
   - `from_native_messages()` dropped native-index mapping whenever native history contained filtered items, which broke rebuilds with `RuntimeError: from_native_messages changed message count without providing native_indices mapping`.
   - Fixed by preserving the original native index on each reconstructed visible message.
2. `core/python/agent_core/core.py`
   - The rebuild/native-conversion helpers resolved the correct provider extension set but did not activate that filtered set on the provider wrapper before running provider init and native conversion/rebuild.
   - This allowed unrelated extensions from other providers to run during manual rebuilds, which polluted OpenRouter rebuild output with OpenAI Responses-style `function_call` items.
   - Fixed by calling `provider.set_active_extensions(enabled_extensions)` in both `_core_messages_to_native_for_config(...)` and `_rebuild_core_from_native(...)` before provider initialization/conversion.

Verification run:
1. `pytest plugins/openai_responses/tests/test_agent_application_openai_responses_provider_switch.py -q`
2. Result: passed.

Residual note:
1. The direct root-level pytest invocation emitted `PytestUnknownMarkWarning` for `@pytest.mark.openrouter` because that marker is not registered by the root test configuration in this workspace. The test itself passed end to end.