# AGENTS And Testing Doc Guidance

Update the root testing guidance so it matches the actual repo: where tests live, how markers work, which suites are slow or billable, how env loading really works, and which provider plugin packages should be exercised after major changes.

## Requirements checklist

- [x] Update root `AGENTS.md` with accurate test locations and standard run guidance.
- [x] Document the new marker semantics and the practical meaning of `not integration`.
- [x] Clarify env-loading expectations for real-provider tests.
- [x] Explicitly list major provider plugin packages that should be exercised after significant changes.
- [x] Decide whether `.env.example` should be expanded in the same pass to reflect documented real-provider test needs.
- [x] Update affected package-local README files where test or env guidance would otherwise drift from the new defaults.

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

## Execution plan

Added during task completion after user approval.

1. Rewrite the root `AGENTS.md` testing guidance around run intent instead of a short directory list:
   - fast default verification
   - integration verification
   - hosted API verification
   - slow integration verification
   - provider-plugin follow-up coverage for major changes
2. Update root `AGENTS.md` so it documents the actual package-local pytest defaults now in effect for:
   - `core/python`
   - `application/python`
   - `plugins/openrouter`
   - `plugins/openai_responses`
   - `plugins/reference-openai-compatible-provider`
3. Document marker semantics in `AGENTS.md`, including:
   - `integration`
   - `api`
   - `slow_integration`
   - provider markers such as `openrouter`, `openai`, `ollama`, `gemini`, `fireworks`, `zai`
   - `docker`
   - `manual_integration`
   and explain that `not integration` is the practical quick filter, while still allowing intentionally fast local Ollama tests that are not marked `integration`.
4. Tighten the env-loading guidance in `AGENTS.md` so it reflects the shared repo-root `.env` bootstrap in the main Python suites without implying every suite in the repo auto-loads dotenv.
5. Expand `.env.example` to cover the main hosted-provider keys and the most relevant optional base URL overrides while keeping the file clearly placeholder-only.
6. Update affected package-local README files for consistency:
   - `application/python/README.md`
   - `plugins/openrouter/README.md`
   - `plugins/openai_responses/README.md`
   - `plugins/reference-openai-compatible-provider/README.md`
7. Leave `application/python/agent_terminal_app/AGENTS.md` unchanged unless a conflicting test/env statement is discovered, since the current file does not document package-local pytest commands.
8. Validate the docs pass by reading the updated sections back against the current package `pyproject.toml` defaults and checking for obvious command drift.

## Completion Notes

Added during task completion.

- Rewrote the root `AGENTS.md` testing guidance so it now documents:
  - the major Python test locations
  - package-local default pytest behavior
  - fast default verification commands
  - integration, hosted `api`, and `slow_integration` verification paths
  - provider follow-up expectations for major request-pipeline and default-config changes
- Updated `AGENTS.md` marker guidance so `integration`, `api`, `slow_integration`, provider markers, `docker`, and `manual_integration` are all described together, including the practical meaning of `not integration`.
- Tightened the root env-loading guidance to reflect the current shared repo-root `.env` bootstrap used by the main Python suites without claiming that every suite in the repository auto-loads dotenv.
- Expanded `.env.example` to include the main hosted-provider credentials and optional base URL overrides alongside the existing Ollama settings.
- Updated package-local README files for consistency:
  - `application/python/README.md`
  - `plugins/openrouter/README.md`
  - `plugins/openai_responses/README.md`
  - `plugins/reference-openai-compatible-provider/README.md`
- Left `application/python/agent_terminal_app/AGENTS.md` unchanged because the file does not currently document package-local pytest commands or conflicting env-loading behavior.
- Validation performed:
  - read-back comparison against current package `pyproject.toml` defaults
  - marker-targeted `pytest --collect-only` checks for the newly documented example, Docker, slow OpenRouter, manual ChatGPT, and Fireworks command slices
- No live provider tests were run for this docs task.