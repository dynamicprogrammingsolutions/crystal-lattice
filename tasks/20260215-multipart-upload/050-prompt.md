Implement provider-side mapping between core `{content, multipartContent}` and provider-native message formats, and back it with an OpenRouter integration test. Exact provider-native schemas will be provided by the user during task execution.

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/050-provider-mapping-multipartcontent.md`

2) Inspect current provider implementations and their conversion hooks:
- `core/python/plugins/openrouter_provider.py`
- `core/python/plugins/openai_provider.py` (if relevant)
- `core/python/agent_core/types.py` (ProviderPlugin protocol docs)
- `core/python/agent_core/core.py` (request flow calls to `to_native_messages` / `from_native_messages`)

3) Inspect existing OpenRouter integration tests to follow conventions:
- `core/python/tests/test_openrouter_basic_integration.py`
- Other `core/python/tests/test_openrouter_*` tests as needed

4) Identify what you need from the user to finalize the mapping:
- Sample provider-native content schema
- Expected core part shapes for `multipartContent` for at least one attachment type
- Model id(s) to use for integration test (and whether to gate via env var)

5) Share a plan with the user that includes:
- Which provider(s) will be updated
- How `multipartContent` will be mapped (high level)
- How to split back into core
- The exact new test file name and env var gates

Do not implement until user approves and provides the schema samples.

## Step 2 — Complete (after user approval)

1) Implement `to_native_messages` and `from_native_messages` changes for OpenRouter (and others if requested).

2) Add the new integration test:
- `core/python/tests/test_openrouter_multipart_integration.py`
- Mark with `@pytest.mark.integration` and `@pytest.mark.openrouter`.
- Skip when required env vars are missing.
- Use an env var (e.g. `OPENROUTER_MULTIPART_MODEL`) for the multimodal model id if needed.

3) Run the integration test locally (or at least ensure it imports and is properly gated).
