# Test Markers, Env Loading, And Standard Runs

Define the concrete testing policy for the repo: marker taxonomy, standardized repo-root env loading, expected meaning of `not integration`, and simple standard test runs for core, application, and major provider plugin packages.

## Requirements checklist

- [x] Define the target marker taxonomy and how it should be used across core, application, and provider plugin packages.
- [x] Standardize how real-provider tests load repo-root `.env` values.
- [x] Identify which current tests need re-marking so `-m 'not integration'` behaves as intended.
- [x] Propose the standard developer test-run matrix for `core`, `application`, and `plugins`.
- [x] Identify concrete slow integration suites that should be separated and run selectively.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

## User intent that this subtask must preserve

- There should be a standard marker for hosted API tests instead of relying only on provider markers such as `openrouter`.
- There should be a separate standard marker for slow integration tests.
- `-m 'not integration'` should remain the quick verification filter that excludes real API tests.
- Some Ollama tests are acceptable in broader local verification because they are relatively fast and do not hit hosted APIs.
- Major changes should explicitly consider coverage in:
  - `plugins/openrouter`
  - `plugins/openai_responses`
  - `plugins/reference-openai-compatible-provider`

## Current marker and bootstrap state

### Existing package marker declarations

- `core/python/pyproject.toml:46-56`
  - Declares `integration`, `openrouter`, `ollama`
  - Excludes `integration` by default via `addopts`
- `application/python/pyproject.toml:53-60`
  - Declares `integration`, `docker`, `gemini`, `openai`, `ollama`, `openrouter`
  - No default addopts exclusion for integration
- `plugins/openrouter/pyproject.toml:37-43`
  - Declares `integration`, `openrouter`
  - No `api` or `slow` marker yet
- `plugins/openai_responses/pyproject.toml:40-46`
  - Declares `integration`, `openai`, `manual_integration`
  - No `api` or `slow` marker yet
- `plugins/reference-openai-compatible-provider/pyproject.toml:40-44`
  - Declares `integration`, `fireworks`, `zai`, `ollama`
  - No `api` or `slow` marker yet

### Real-provider examples currently missing `integration`

These files should be considered during any re-marking pass:

- `core/python/examples/tests/test_example5_project_plan_basic.py:54`
- `core/python/examples/tests/test_example6_project_plan_streaming.py:54`
- `core/python/examples/tests/test_example7_project_plan_tool_calls.py:52`
- `core/python/examples/tests/test_example8_project_plan_messages.py:51`
- `core/python/examples/tests/test_example9_project_plan_config_updates.py:52`
- `core/python/examples/tests/test_example11_openai_tools_file_reader.py:57`
- `core/python/examples/tests/test_example12_openrouter_tools_app.py:71`
- `core/python/examples/tests/test_example13_openrouter_tools_app_layer.py:76`

These example tests are important because the user specifically wants `not integration` to exclude real API work. Right now provider-backed example tests can slip through because they are not marked `integration`.

### Env loading is inconsistent

Representative patterns already found:

- Bare `load_dotenv()` from current working directory:
  - `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py:24-30`
  - `plugins/openrouter/tests/test_openrouter_reasoning_integration.py:12-18`
  - `core/python/examples/tests/test_example12_openrouter_tools_app.py:18-23`
  - `core/python/examples/tests/test_example13_openrouter_tools_app_layer.py:23-28`
- Explicit root `.env` loading:
  - `plugins/openai_responses/tests/test_openai_responses_tools_comprehensive_integration.py:23-29`
  - `application/python/tests/test_openai_responses_attachment_endpoints.py:195-201`
  - `application/python/tests/test_terminal_default_config_codex_view_image_real_api.py:41-59`
- Manual root `.env` parsing:
  - `application/python/tests/test_gemini_web_search_integration.py:33-45`
  - `application/python/tests/test_kimi_web_search_integration.py:21-31`
  - `plugins/reference-openai-compatible-provider/tests/hosted_test_utils.py:28-41`
- No loading at all, only `os.getenv(...)`:
  - `core/python/tests/test_application_layer_openrouter_multi_agent_tool_packages.py:18-24`
  - `application/python/tests/test_terminal_application_default_config_openrouter_integration.py:53-58`
  - `plugins/openrouter/tests/test_openrouter_usage_extension_integration.py:22-31`

## Proposed target marker model

This was the recommended structure during scoping and should be treated as the working proposal unless implementation uncovers a blocker:

- `integration`
  - Any test that depends on external services, multi-process tool chains, real network/provider calls, or realistic end-to-end flows that are slower/riskier than normal unit tests.
- `api`
  - Hosted, credentialed, potentially billable real-provider tests.
  - Add this alongside provider markers, not instead of them.
- `slow_integration`
  - Intentionally broad, matrix-heavy, long-running, expensive, or especially flaky integration tests that should be run selectively.
- Existing provider markers should remain:
  - `openrouter`
  - `openai`
  - `ollama`
  - `gemini`
  - `fireworks`
  - `zai`
  - existing `docker` and `manual_integration` where applicable

## Expected marker combinations

- Hosted OpenRouter tests:
  - `integration + api + openrouter`
- Hosted OpenAI `/responses` tests:
  - `integration + api + openai`
- Hosted Fireworks tests:
  - `integration + api + fireworks`
- Hosted Z.ai tests:
  - `integration + api + zai`
- Local Ollama integration tests:
  - `integration + ollama`
  - no `api`
- Manual auth/state tests:
  - `integration + api + manual_integration + openai` where appropriate

## Slow integration candidates already identified

### OpenRouter first-wave candidates

These were explicitly called out by the user and should be strong candidates for the new `slow_integration` marker:

- `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py`
  - Broad model matrix and streaming/non-streaming combinations; see `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py:1-150`
- `plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py`
  - Reasoning + tool loop integration across models; see `plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py:1-120`

### Good second-wave candidates to evaluate

- `plugins/openai_responses/tests/test_openai_responses_tools_comprehensive_integration.py`
  - Multiple tool scenarios and streaming variants; see `plugins/openai_responses/tests/test_openai_responses_tools_comprehensive_integration.py:1-150`
- `plugins/openai_responses/tests/test_openai_responses_reasoning_integration.py`
  - Reasoning + tools scenario; see `plugins/openai_responses/tests/test_openai_responses_reasoning_integration.py:1-140`
- `plugins/openai_responses/tests/test_openai_responses_native_compaction_integration.py`
  - Large provider-specific investigation surface
- `plugins/reference-openai-compatible-provider/tests/test_fireworks_tools_comprehensive.py`
- `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_tools_reasoning.py`
  - Fireworks reasoning/tool scenarios; see `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_tools_reasoning.py:69-80`
- `plugins/reference-openai-compatible-provider/tests/test_zai_integration_tools_reasoning.py`

## Recommended env-loading standard

The implementation should aim for one shared helper that:

- loads the repo-root `.env`
- does not overwrite already-exported environment variables
- can be reused from core/application/plugin test suites
- avoids depending on the current working directory

Preferred direction:

- Create a small shared Python helper for tests only, likely under a repo-level test utility path or another shared location accessible to Python suites.
- Use that helper from fixtures such as:
  - `ensure_openrouter_api_key`
  - `ensure_openai_api_key`
  - `ensure_fireworks_api_key`
  - `ensure_zai_api_key`
  - `ensure_gemini_api_key`
- Replace bare `load_dotenv()` and custom file parsing with the shared helper over time.

Important note:

- `plugins/openrouter` and `plugins/openai_responses` tests currently use `python-dotenv`, but their `dev` extras do not declare it:
  - `plugins/openrouter/pyproject.toml:17-21`
  - `plugins/openai_responses/pyproject.toml:17-21`
- A manual loader similar to the existing reference-provider helper may be simpler and more robust than adding more package-level test-only dependencies.

## Proposed standard developer test runs

These commands were the scoped recommendation and should be validated during implementation.

### Core work

- Unit only:
  - `pytest core/python/tests -q`
- Integration, non-API:
  - `pytest core/python/tests -m 'integration and not api and not slow_integration' -q`
- Hosted API integration, selective:
  - `pytest core/python/tests core/python/examples/tests -m 'integration and api and not slow_integration' -q`
- Slow integration, selective:
  - `pytest core/python/tests core/python/examples/tests -m 'slow_integration' -q`

### Application work

- Unit only:
  - `pytest application/python/tests -m 'not integration and not docker' -q`
- Integration, non-API:
  - `pytest application/python/tests -m 'integration and not api and not slow_integration and not docker' -q`
- Hosted API integration, selective:
  - `pytest application/python/tests -m 'integration and api and not slow_integration and not docker' -q`
- Slow integration, selective:
  - `pytest application/python/tests -m 'slow_integration and not docker' -q`

### Plugins work

- OpenRouter unit only:
  - `pytest plugins/openrouter/tests -m 'not integration' -q`
- OpenRouter hosted API:
  - `pytest plugins/openrouter/tests -m 'integration and api and not slow_integration' -q`
- OpenAI Responses unit only:
  - `pytest plugins/openai_responses/tests -m 'not integration and not manual_integration' -q`
- OpenAI Responses hosted API:
  - `pytest plugins/openai_responses/tests -m 'integration and api and not slow_integration and not manual_integration' -q`
- Reference provider unit only:
  - `pytest plugins/reference-openai-compatible-provider/tests -m 'not integration' -q`
- Reference provider local Ollama integration:
  - `pytest plugins/reference-openai-compatible-provider/tests -m 'integration and ollama and not slow_integration' -q`
- Reference provider hosted API integration:
  - `pytest plugins/reference-openai-compatible-provider/tests -m 'integration and api and not slow_integration' -q`

## Open questions the implementing agent should settle

- Should `application/python` and provider-plugin packages adopt default `addopts` that exclude `integration`, or should they keep broad defaults and rely on documented commands?
- Should every provider-backed example test receive both `integration` and its provider marker, or should examples remain a distinct category with updated docs only?
- Where should the shared env helper live so that all suites can import it cleanly without creating packaging churn?
- Should `slow_integration` be applied only to the most expensive hosted tests first, or more broadly to long-running Ollama/Docker suites too?

## Likely file touch points

- `core/python/pyproject.toml`
- `application/python/pyproject.toml`
- `plugins/openrouter/pyproject.toml`
- `plugins/openai_responses/pyproject.toml`
- `plugins/reference-openai-compatible-provider/pyproject.toml`
- real-provider and example tests across:
  - `core/python/examples/tests`
  - `application/python/tests`
  - `plugins/openrouter/tests`
  - `plugins/openai_responses/tests`
  - `plugins/reference-openai-compatible-provider/tests`

## Suggested first implementation slice

1. Finalize marker names and default semantics.
2. Introduce the shared env-loading helper.
3. Convert a representative set of hosted-provider fixtures to the shared helper.
4. Add `integration` to provider-backed example tests.
5. Add `api` to hosted-provider tests.
6. Add `slow_integration` to the first-wave OpenRouter cases.
7. Update package marker declarations to include the new markers.

## Execution plan

Added during task completion after user approval.

1. Finalize the marker policy in code and in the task notes for this subtask.
2. Add new shared markers where needed: `api` and `slow_integration`.
3. Keep existing provider markers in place: `openrouter`, `openai`, `ollama`, `gemini`, `fireworks`, `zai`, plus `docker` and `manual_integration`.
4. Introduce one shared repo-root env loader for Python tests in a neutral importable location, likely a small repo-level helper module rather than more ad hoc `load_dotenv()` usage.
5. Make that helper non-destructive: it should load the root `.env`, not depend on current working directory, and never overwrite already-exported env vars.
6. Convert the real-provider fixture/bootstrap paths in the main in-scope suites to the shared helper:
   - `core/python/examples/tests`
   - `application/python/tests`
   - `plugins/openrouter/tests`
   - `plugins/openai_responses/tests`
   - `plugins/reference-openai-compatible-provider/tests`
7. Re-mark provider-backed example tests so `-m 'not integration'` becomes truthful there too.
8. Add `api` to hosted-provider tests across OpenRouter, OpenAI Responses, Fireworks, Z.ai, and other hosted real-provider tests in application/core example coverage.
9. Add `slow_integration` to the first-wave heavy OpenRouter suites:
   - `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py`
   - `plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py`
10. Update package marker declarations in:
    - `core/python/pyproject.toml`
    - `application/python/pyproject.toml`
    - `plugins/openrouter/pyproject.toml`
    - `plugins/openai_responses/pyproject.toml`
    - `plugins/reference-openai-compatible-provider/pyproject.toml`
11. Record the standard run matrix in the task file as the approved target for later doc/command alignment:
    - core: unit, integration non-api, hosted api, slow integration
    - application: unit, integration non-api, hosted api, slow integration
    - plugins: same pattern, explicitly covering `openrouter`, `openai_responses`, and `reference-openai-compatible-provider`

## Completion Notes

Added during task completion.

- Implemented a shared repo-root env loader in `repo_test_env.py` and wired it into suite-level test bootstrap files so root `.env` values are loaded before test modules are imported.
- Added or updated test bootstrap files in:
  - `core/python/tests/conftest.py`
  - `application/python/tests/conftest.py`
  - `core/python/examples/tests/conftest.py`
  - `plugins/openrouter/tests/conftest.py`
  - `plugins/openai_responses/tests/conftest.py`
  - `plugins/reference-openai-compatible-provider/tests/conftest.py`
- Added `api` and `slow_integration` marker declarations to:
  - `core/python/pyproject.toml`
  - `application/python/pyproject.toml`
  - `plugins/openrouter/pyproject.toml`
  - `plugins/openai_responses/pyproject.toml`
  - `plugins/reference-openai-compatible-provider/pyproject.toml`
- Added `python-dotenv` to the `plugins/openrouter` and `plugins/openai_responses` dev extras because those suites still contain dotenv imports and were previously under-declared.
- Re-marked provider-backed example tests so they now participate in `integration` filtering, and OpenRouter example tests also participate in `api` filtering where appropriate.
- Added `api` markers across the main hosted-provider test surfaces in:
  - `application/python/tests`
  - `plugins/openrouter/tests`
  - `plugins/openai_responses/tests`
  - `plugins/reference-openai-compatible-provider/tests`
- Added first-wave `slow_integration` markers to:
  - `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py`
  - `plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py`
- Standardized several bespoke application env helpers to use the shared loader directly, especially in Gemini/Kimi and multiple application real-API tests.
- Updated the reference-provider hosted env helper to use the shared repo-root loader instead of its own manual `.env` parsing implementation.
- Left package-default pytest `addopts` behavior unchanged on purpose; that decision remains for `tasks/20260524-test-and-agents-cleanup/030-test-and-build-command-alignment.md`.
- Verification performed:
  - `pytest core/python/examples/tests --collect-only -q`
  - `pytest application/python/tests/... --collect-only -q` for the changed application files
  - `pytest tests --collect-only -q` in `plugins/openrouter`
  - `pytest tests --collect-only -q` in `plugins/openai_responses`
  - `pytest tests --collect-only -q` in `plugins/reference-openai-compatible-provider`
  - marker-targeted collection-only checks for `integration`, `api`, and `slow_integration`