# Scaffold OpenAI Responses Plugin Package

Short description: Create the new `plugins/openai_responses` package skeleton (provider + extensions + descriptor + packaging) with baseline loading tests.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/010-architecture-scope-and-boundaries.md`

## Implementation

1. Create plugin package directory:
- `plugins/openai_responses/pyproject.toml`
- `plugins/openai_responses/agent_plugin.json`
- `plugins/openai_responses/README.md`
- `plugins/openai_responses/src/openai_responses_plugins/__init__.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_verbosity_extension.py`
2. Add OpenAI SDK dependency to this plugin package (`openai`), without changing unrelated plugin packages.
3. Register all entries in `agent_plugin.json` with explicit `kinds` map.

## Tests (required in this step)

1. Plugin package import test (all entry classes importable).
2. Descriptor/entry load test via agent application loader path pattern.
3. Metadata sanity tests: names, versions, required tags skeletons.

## References

- `plugins/template-python-provider/*`
- `plugins/openrouter_responses/agent_plugin.json`
- `plugins/openrouter_responses/pyproject.toml`
- `plugins/openrouter_responses/tests/test_agent_application_openrouter_config_loads.py`

## Execution plan (added during completion)

1. Create `plugins/openai_responses/` scaffold with package metadata, plugin descriptor, README, and `src/openai_responses_plugins/*` module files.
2. Add `openai` SDK dependency in this plugin package only (`pyproject.toml`), alongside `agent-core`.
3. Implement minimal provider and extension skeleton classes with correct names/versions, basic schema/tag hooks, and explicit provider/extension boundaries through required tags.
4. Add baseline tests for:
- importability of all descriptor entry classes
- descriptor path + class loading via `AgentApplication`
- metadata sanity for names/versions and tag/required-tag skeletons
5. Run `pytest plugins/openai_responses/tests -q` and use those results to finish the subtask.

## Completion notes (added during completion)

### Changes made

1. Created new plugin package scaffold at `plugins/openai_responses/`:
- `plugins/openai_responses/pyproject.toml`
- `plugins/openai_responses/agent_plugin.json`
- `plugins/openai_responses/README.md`
- `plugins/openai_responses/src/openai_responses_plugins/__init__.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_verbosity_extension.py`

2. Added plugin-local test suite:
- `plugins/openai_responses/tests/conftest.py`
- `plugins/openai_responses/tests/test_openai_responses_imports.py`
- `plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py`
- `plugins/openai_responses/tests/test_openai_responses_metadata_sanity.py`

3. Added OpenAI SDK dependency only in this new plugin package:
- `openai>=2.0.0` in `plugins/openai_responses/pyproject.toml`.

4. Registered provider + extension entries in descriptor with explicit `kinds` map.

### Tests run

1. `pytest plugins/openai_responses/tests -q`

### Results

1. Passed: `5 passed`.

### Open issues

1. Provider and extension files are intentionally scaffold/minimal for this subtask; full transport/conversion/streaming/domain behaviors are deferred to subsequent subtasks (`030+`).
