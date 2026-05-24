# AGENTS And Testing Doc Guidance

Update the root testing guidance so it matches the actual repo: where tests live, how markers work, which suites are slow or billable, how env loading really works, and which provider plugin packages should be exercised after major changes.

## Requirements checklist

- [ ] Update root `AGENTS.md` with accurate test locations and standard run guidance.
- [ ] Document the new marker semantics and the practical meaning of `not integration`.
- [ ] Clarify env-loading expectations for real-provider tests.
- [ ] Explicitly list major provider plugin packages that should be exercised after significant changes.
- [ ] Decide whether `.env.example` should be expanded in the same pass to reflect documented real-provider test needs.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/010-test-markers-env-and-standard-runs.md`

## Current docs gaps already verified

### Root AGENTS testing commands are incomplete

Current root test guidance is in:

- `AGENTS.md:94-123`
- `AGENTS.md:187-203`

Problems already identified:

- It only partially describes the integration surface.
- It does not name `plugins/openai_responses/tests` or `plugins/reference-openai-compatible-provider/tests`.
- It documents `pytest core/python/examples/tests -qs`, which can run provider-backed examples that are currently not marked `integration`.
- It implies dotenv/config loading is common enough that missing credentials should be checked through documented loading paths, but actual suites are much more inconsistent.

### The current dotenv note is too optimistic

The note in `AGENTS.md:199-202` says many suites load `.env` automatically or can be run from a command that sources it. That needs tightening because the actual state is:

- no shared pytest bootstrap loads root `.env`
- some tests use bare `load_dotenv()`
- some use explicit root `.env`
- some parse `.env` manually
- some only check `os.getenv()` and skip

Representative references:

- `application/python/tests/conftest.py:1-20`
- `core/python/tests/conftest.py:1-8`
- `application/python/tests/test_gemini_web_search_integration.py:33-45`
- `plugins/openrouter/tests/test_openrouter_usage_extension_integration.py:22-31`
- `plugins/reference-openai-compatible-provider/tests/hosted_test_utils.py:28-41`

### Root `.env.example` is narrower than the real-provider test surface

- `.env.example:1-7` currently documents only:
  - `OPENROUTER_API_KEY`
  - `OLLAMA_HOST`
  - `OLLAMA_MODEL_QWEN3`

But real-provider tests also use:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `FIREWORKS_API_KEY`
- `ZAI_API_KEY`
- optional provider/base URL overrides such as `OPENAI_BASE_URL`, `OPENROUTER_BASE_URL`, `FIREWORKS_BASE_URL`, `ZAI_BASE_URL`

## Target doc updates

### Root AGENTS should explicitly document

- Standard run commands for:
  - core
  - application
  - plugins
- Run levels for:
  - unit tests only
  - integration tests
  - slow integration tests run selectively
- The meaning of:
  - `integration`
  - `api`
  - `slow_integration`
  - provider markers such as `openrouter`, `openai`, `ollama`, `gemini`, `fireworks`, `zai`
- Where the major Python integration suites live:
  - `core/python/tests`
  - `core/python/examples/tests`
  - `application/python/tests`
  - `plugins/openrouter/tests`
  - `plugins/openai_responses/tests`
  - `plugins/reference-openai-compatible-provider/tests`
- Which provider plugin packages should be exercised after major changes:
  - `plugins/openrouter`
  - `plugins/openai_responses`
  - `plugins/reference-openai-compatible-provider`

### Root AGENTS should also warn about

- broad commands that may run slow or billable tests
- the need to run hosted-provider tests selectively
- the difference between local Ollama integration and hosted API integration
- example tests that may hit real providers

## Recommended doc structure changes

The implementing agent should consider restructuring the root testing section into:

1. Fast default verification
2. Integration verification
3. Hosted API verification
4. Slow integration verification
5. Provider plugin coverage expectations for major changes

This is more actionable than the current mixed list of directory-specific commands.

## References to include in the doc update

Useful places to cite or mirror in wording:

- `core/python/pyproject.toml:46-56`
- `application/python/pyproject.toml:53-60`
- `plugins/openrouter/pyproject.toml:37-43`
- `plugins/openai_responses/pyproject.toml:40-46`
- `plugins/reference-openai-compatible-provider/pyproject.toml:40-44`

## Specific caution for future agents

- Do not leave root `AGENTS.md` saying "many suites load `.env` automatically" unless the code is changed to make that statement true.
- If `.env.example` is updated in this cleanup, keep the example values clearly placeholder-only and do not mirror any real credential names beyond the env keys themselves.
- The final docs should reflect the actual marker policy chosen in subtask 010, not a partially-implemented intermediate state.