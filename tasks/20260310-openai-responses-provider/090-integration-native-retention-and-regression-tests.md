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
