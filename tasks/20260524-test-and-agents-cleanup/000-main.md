# Test And AGENTS Cleanup

Create a coordinated cleanup plan for root `AGENTS.md`, Python test structure and markers, env-loading behavior for real-provider tests, and standard developer test/build commands. This task is meant to give a future agent enough context to continue planning and implementation without rediscovering the repo state from scratch.

## Task checklist

- [x] `tasks/20260524-test-and-agents-cleanup/010-test-markers-env-and-standard-runs.md`
- [ ] `tasks/20260524-test-and-agents-cleanup/020-agents-and-testing-doc-guidance.md`
- [x] `tasks/20260524-test-and-agents-cleanup/030-test-and-build-command-alignment.md`
- [ ] `tasks/20260524-test-and-agents-cleanup/040-follow-on-test-cleanup-backlog.md`

## Why this cleanup exists

Recent review found that the documented testing guidance in the root `AGENTS.md` only partially matches the actual Python test surface:

- Root test guidance currently lives in `AGENTS.md` under development workflow and testing principles; see `AGENTS.md:94-123` and `AGENTS.md:187-203`.
- `core/python` already excludes `integration` by default via `addopts = "-v --cov=agent_core --cov-report=term-missing -m 'not integration'"`; see `core/python/pyproject.toml:46-56`.
- `application/python`, `plugins/openrouter`, `plugins/openai_responses`, and `plugins/reference-openai-compatible-provider` define markers but do not currently exclude integration suites by default; see:
  - `application/python/pyproject.toml:53-60`
  - `plugins/openrouter/pyproject.toml:37-43`
  - `plugins/openai_responses/pyproject.toml:40-46`
  - `plugins/reference-openai-compatible-provider/pyproject.toml:40-44`
- Provider-backed example tests in `core/python/examples/tests` currently hit real providers or local Ollama but are not marked `integration`. Examples:
  - `core/python/examples/tests/test_example5_project_plan_basic.py:54`
  - `core/python/examples/tests/test_example11_openai_tools_file_reader.py:57`
  - `core/python/examples/tests/test_example12_openrouter_tools_app.py:71`
  - `core/python/examples/tests/test_example13_openrouter_tools_app_layer.py:76`

The result is that "simple" commands can still run slow or billable suites, and the current dotenv guidance is more optimistic than the actual test bootstrap behavior.

## Repo facts already verified

### Test locations relevant to this cleanup

- `core/python/tests`
- `core/python/examples/tests`
- `application/python/tests`
- `plugins/openrouter/tests`
- `plugins/openai_responses/tests`
- `plugins/reference-openai-compatible-provider/tests`

### Integration-file counts observed during scoping

These counts came from marker searches and are approximate planning inputs for the cleanup:

- `core/python/tests`: 11 integration-marked files
- `application/python/tests`: 20 integration-marked files
- `plugins/openrouter/tests`: 15 integration-marked files
- `plugins/openai_responses/tests`: 18 integration-marked files
- `plugins/reference-openai-compatible-provider/tests`: 17 integration-marked files

### Real-provider example tests not marked `integration`

The following eight example tests currently use provider or Ollama markers without `integration`, which weakens the intended meaning of `-m 'not integration'`:

- `core/python/examples/tests/test_example5_project_plan_basic.py`
- `core/python/examples/tests/test_example6_project_plan_streaming.py`
- `core/python/examples/tests/test_example7_project_plan_tool_calls.py`
- `core/python/examples/tests/test_example8_project_plan_messages.py`
- `core/python/examples/tests/test_example9_project_plan_config_updates.py`
- `core/python/examples/tests/test_example11_openai_tools_file_reader.py`
- `core/python/examples/tests/test_example12_openrouter_tools_app.py`
- `core/python/examples/tests/test_example13_openrouter_tools_app_layer.py`

### Env-loading inconsistency already confirmed

There is no shared Python test bootstrap that globally loads the repo-root `.env`.

- `core/python/tests/conftest.py:1-8` only resets runtime overlay state after each test.
- `application/python/tests/conftest.py:1-20` only adjusts `sys.path` and resets runtime overlay state.
- OpenRouter tests often use bare `load_dotenv()` relative to the current working directory:
  - `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py:24-30`
  - `plugins/openrouter/tests/test_openrouter_reasoning_integration.py:12-18`
- OpenAI Responses tests often use explicit `REPO_ROOT / ".env"` loading:
  - `plugins/openai_responses/tests/test_openai_responses_tools_comprehensive_integration.py:23-29`
  - `plugins/openai_responses/tests/test_agent_application_openai_responses_reasoning.py:25-30`
- Reference provider tests already have a manual root-env helper:
  - `plugins/reference-openai-compatible-provider/tests/hosted_test_utils.py:28-41`
- Some application tests parse `.env` manually instead of using a shared loader:
  - `application/python/tests/test_gemini_web_search_integration.py:33-45`
  - `application/python/tests/test_kimi_web_search_integration.py:21-31`

### Root `.env` and `.env.example`

The repo-root `.env` was checked and contains the main credentials used by real-provider tests, including:

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `FIREWORKS_API_KEY`
- `ZAI_API_KEY`
- `OLLAMA_HOST`
- `OLLAMA_MODEL_QWEN3`

However, `.env.example` is currently sparse and only documents OpenRouter + basic Ollama setup; see `.env.example:1-7`.

## Target outcomes for the full cleanup

- Define a consistent marker model across core, application, and major provider plugin packages.
- Standardize repo-root `.env` loading for real-provider tests.
- Add a standard `api` marker for hosted real-provider tests.
- Add a standard `slow_integration` marker for intentionally heavy integration suites.
- Preserve the current meaning that `-m 'not integration'` is the fast/offline quick filter, while still allowing some relatively fast Ollama tests to remain in the broader "not api" world where appropriate.
- Document standard test commands for:
  - core work
  - application work
  - plugins work
- Explicitly call out the provider plugin packages that should be exercised after major changes:
  - `plugins/openrouter`
  - `plugins/openai_responses`
  - `plugins/reference-openai-compatible-provider`

## Important policy constraints from the user

- Keep frontend out of scope for this cleanup.
- Standard runs should be simple and practical for daily use.
- Separate guidance for:
  - unit tests only
  - integration tests
  - slow integration tests run selectively
- Some Ollama tests are intentionally acceptable in broader local verification because they are relatively fast and do not call hosted APIs.
- "Not integration" should remain the important quick filter to exclude real API tests.
- Future cleanup areas should be recorded but not folded into the first implementation pass:
  - SDK e2e tests
  - terminal/server tests
  - tests around the default config

## Recommended execution order

1. Finish marker/env/test-run policy and identify the concrete files to touch.
2. Update docs in `AGENTS.md` and adjacent testing docs to match the new policy.
3. Align package-level pytest markers and default commands with the documented workflow.
4. Capture deferred cleanup areas with enough detail to split into follow-up tasks later.

## Notes for the next agent

- The first subtask is the highest-value implementation target and contains the detailed findings needed for planning.
- When changing pytest marker declarations, remember that the marker sets are currently duplicated across multiple `pyproject.toml` files.
- When standardizing env loading, prefer one shared helper over more ad hoc `load_dotenv()` usage.
- Be careful with broad default commands in `application/python` and provider plugin packages; they currently risk running slow or billable tests unintentionally.