# Integration Native Retention And Regression Tests

Short description: Add full-stack integration and regression coverage for the new `openai_responses` bundle, including tool loop continuity, slice/fork safety, and extension isolation.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/050-tools-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/060-reasoning-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/070-usage-extension-responses-api.md`
- `tasks/20260310-openai-responses-provider/080-verbosity-extension-responses-api.md`

## Implementation

1. Add integration suite guarded by `OPENAI_API_KEY` (and optional expensive marker/env gate where needed).
2. Cover non-streaming + streaming for plain chat.
3. Cover tools+reasoning multi-turn continuity scenario.
4. Cover usage and verbosity in end-to-end requests.
5. Add native-history retention regression tests (including cross-core continuity).
6. Add slice/fork/session-modification regression tests if response-segment ownership metadata is used.
7. Add provider/extension isolation tests (ensure `openai_responses` extensions do not activate with other providers and vice versa).

## Environment note

1. `OPENAI_API_KEY` is expected from repo root `.env` during local execution.
2. Tests must read the env var and skip cleanly when it is missing.

## Tests (this subtask is test-focused)

1. New unit/integration tests as above.
2. Keep markers and environment requirements explicit.
3. Ensure new suite is runnable independently from existing OpenRouter suites.

## References

- `plugins/openrouter_responses/tests/test_openrouter_tools_reasoning_integration.py`
- `plugins/openrouter_responses/tests/test_openrouter_responses_slice_integration.py`
- `plugins/openrouter_responses/tests/test_openrouter_provider_isolation.py`
- `core/python/tests/test_native_retention_across_core_instances.py`

## Approved plan (added during completion)

1. Complete the prerequisite application-layer fix from `tasks/20260307-native-history-preservation-and-single-provider/020-application-single-provider-core-selection.md` as part of this subtask.
- narrow operation/session cores to exactly one selected provider when the effective config already identifies one provider
- keep the fix in the application/core-selection layer rather than in the `openai_responses` provider

2. Add core-level regression tests.
- cover `AgentCore` native-history continuity for `openai_responses`
- cover cross-core retention and slice/fork safety for response-segment `native_indices`
- use scripted providers where possible for deterministic regression coverage

3. Add application-level tests.
- verify JSON config loading for the full `openai_responses` bundle remains valid
- add regression coverage that application-built cores no longer carry multiple providers for delete/modify/fork paths when one provider is explicitly selected

4. Add at least one end-to-end FastAPI test in `application/python/tests/`.
- exercise the HTTP API in a multi-provider-loaded environment
- select the `openai_responses` agent/provider via config
- perform a mutation path such as delete or fork and verify native-history-preserving behavior survives through the server layer

5. Add or extend live OpenAI integration tests guarded by `OPENAI_API_KEY` from the repo root `.env`.
- cover non-streaming and streaming plain chat
- cover a tools + reasoning continuity scenario
- assert usage metadata is present and a verbosity-enabled request succeeds
- skip cleanly when `OPENAI_API_KEY` is absent

6. Keep provider/extension boundaries strict and validate with tests.
- provider remains transport/native-history focused
- tool/reasoning/usage/verbosity behavior stays in extensions

7. Run focused pytest targets, then broader relevant suites, and append completion notes to this task file when done.

## Completion notes (added during completion)

### What changed

1. Added application-layer single-provider narrowing in `core/python/agent_app/application_future.py`.
- `_build_core_with_enabled_ids(...)` now accepts an effective provider config and narrows enabled providers to the single selected provider class
- provider identity matching now mirrors core-side selection semantics closely enough for app-layer use, including class-name and fully-qualified-name matches
- `load_session(...)` now resolves the effective config from stored session overrides plus optional request overrides before building the per-session core
- `create_session_ephemeral(...)` and `update_agent(...)` now also build a single-provider core aligned with the selected provider

2. Updated request/session callers so the narrowed core is used in real app flows.
- `application/python/agent_terminal_app/server.py` now passes request overrides into `_load_session_ctx_for_send(...)`
- `application/python/agent_terminal_app/terminal_app.py` now refreshes the active core after override updates so the in-memory terminal state stays aligned with the selected provider

3. Added application/core regression coverage for the prerequisite bug class.
- new test file `core/python/tests/test_application_single_provider_selection.py`
- verifies single-provider narrowing on create/load
- verifies stored session overrides and request-time overrides can switch the selected provider cleanly
- verifies unknown provider selection fails explicitly

4. Added end-to-end server regression coverage in `application/python/tests/test_agent_terminal_app_server.py`.
- exercises the HTTP route layer in a multi-provider-loaded environment
- seeds provider-native history and verifies `DELETE /sessions/{id}/messages` preserves native history now that the application builds a single-provider core

5. Expanded `openai_responses` application/config coverage.
- `plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py` now verifies the JSON config can create a session and that the built core contains exactly one `OpenAIResponsesProvider` with the expected extension bundle attached

6. Added `openai_responses` regression and isolation coverage.
- new `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`
  - cross-core native-history continuity with preserved reasoning items
  - slice/fork response-segment ownership regression coverage
- new `plugins/openai_responses/tests/test_openai_responses_provider_isolation.py`
  - verifies `openai_responses` tags do not cross-activate unrelated provider extensions
- new `plugins/openai_responses/tests/test_openai_responses_stack_integration.py`
  - live `OPENAI_API_KEY`-guarded tool + reasoning + usage + verbosity integration

7. Added one provider-side transport/native-history fix in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`.
- SDK input preparation now strips output-only fields such as `id`, `status`, and `namespace` before replaying stored native history back into the Responses API
- this keeps the provider in transport/native-history scope while fixing a real multi-turn tool-loop regression discovered by the new live integration test

8. Added a unit regression test for that transport fix in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`.

### Files touched

1. `core/python/agent_app/application_future.py`
2. `application/python/agent_terminal_app/server.py`
3. `application/python/agent_terminal_app/terminal_app.py`
4. `core/python/tests/test_application_single_provider_selection.py`
5. `application/python/tests/test_agent_terminal_app_server.py`
6. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
7. `plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py`
8. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
9. `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`
10. `plugins/openai_responses/tests/test_openai_responses_provider_isolation.py`
11. `plugins/openai_responses/tests/test_openai_responses_stack_integration.py`
12. `tasks/20260310-openai-responses-provider/090-integration-native-retention-and-regression-tests.md`

### Tests run

1. `pytest core/python/tests/test_application_single_provider_selection.py core/python/tests/test_application_layer_plugins.py -q`
- result: `10 passed`

2. `pytest application/python/tests/test_agent_terminal_app_server.py -q -k 'multiple_loaded_providers'`
- result: `1 passed`

3. `pytest application/python/tests/test_terminal_application.py -q -k 'override or fork_session or modify_message or delete_messages'`
- result: `3 passed`

4. `pytest plugins/session-actions-app/tests/test_session_actions_app_plugin_unit.py -q -k 'fork_session_at or delete_messages'`
- result: `2 passed`

5. `pytest plugins/openai_responses/tests -q`
- result: `69 passed`

### Outcomes

1. Subtask `090` completed with the prerequisite application-layer provider-selection fix included.
2. The application no longer builds a multi-provider core for session operations when the effective config already identifies one provider.
3. `openai_responses` now has regression coverage for cross-core native retention, slice/fork response ownership, provider isolation, and a live multi-turn tools/reasoning/usage/verbosity flow.

### Open issues

1. `ruff check` on some long-standing server test files still reports unrelated pre-existing issues outside this subtask's new logic, so lint was not used as the final gate here.
