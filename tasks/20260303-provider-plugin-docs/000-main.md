# Provider plugin developer documentation + template

Create a complete, up-to-date provider plugin development guide and a provider plugin template repo.

This work has seven subtasks:

1. Create a new **provider plugin template repo** (modeled after `plugins/template-python-tools`) that includes:
   - a provider skeleton (`ProviderPlugin`)
   - a provider extension skeleton (`ProviderExtensionPlugin`)
   - a feature skeleton (`FeaturePlugin`)
   - tests living *inside the template package*

2. Create new documentation page `plugins/docs/provider-plugins.md` and link it from `plugins/docs/index.md`.
   - The doc should include quickstarts (non-streaming + streaming) that each include:
     - package creation (using the new template)
     - how to run tests
   - The doc should also include a more verbose “Complete guide” for building a full provider.
   - The doc should keep deep-dive sections for special cases, and the quickstarts/complete guide must link into those deep dives.

3. Update other docs to point to the new canonical provider plugin doc and fix any outdated/misleading provider-plugin guidance.
   - This will be executed by a different agent.

4. Improve the provider template tests to include integration-ready scaffolding (while keeping the template itself deterministic/offline).

5. Add a dedicated provider extension guide documenting tools + reasoning patterns.

6. Create a **reference provider implementation** that follows the new docs exactly (provider + extensions) and validates the workflow end-to-end against a real OpenAI-compatible endpoint (Ollama).

7. Update existing provider implementations (OpenRouter plugin bundle + Ollama/OpenAI-compatible core plugins) to match the finalized patterns from the docs and reference implementation.

## Goals

- Provide a single, current, complete provider plugin authoring doc.
- Provide a ready-to-copy template repo for provider/plugin development with tests.
- Reduce ongoing drift by referencing runtime code/docstrings and known reference implementations.

## Non-goals

- Rewriting all plugin documentation across the repo (only targeted updates in subtask 3).
- Implementing a real network provider in the template (template should be deterministic/offline).

## Success criteria

- `plugins/template-python-provider` exists, is editable-installable, and its tests pass:
  - `python -m pip install -e core/python`
  - `python -m pip install -e "plugins/template-python-provider[dev]"`
  - `pytest plugins/template-python-provider/tests -q`
- `plugins/docs/provider-plugins.md` exists and is linked from `plugins/docs/index.md`.
- Quickstarts in the doc include both packaging and testing steps.

## Subtasks

- [x] `tasks/20260303-provider-plugin-docs/010-template-python-provider.md`
- [x] `tasks/20260303-provider-plugin-docs/020-provider-plugins-doc.md`
- [x] `tasks/20260303-provider-plugin-docs/030-other-doc-updates.md`
- [x] `tasks/20260303-provider-plugin-docs/040-template-provider-tests.md`
- [x] `tasks/20260303-provider-plugin-docs/050-provider-extensions-doc.md`
- [x] `tasks/20260303-provider-plugin-docs/060-openai-compatible-reference-implementation.md`
- [x] `tasks/20260303-provider-plugin-docs/070-update-existing-provider-implementations.md`

---

## Implementation status (added 2026-03-03)

Completed:

- Subtask 1 (template): implemented `plugins/template-python-provider` with minimal skeleton code + passing offline tests.
- Subtask 2 (docs): implemented `plugins/docs/provider-plugins.md` and created additional shared docs under `plugins/docs/`.
- Subtask 4 (template tests): implemented integration-ready test scaffolding in `plugins/template-python-provider/tests/`.
- Subtask 5 (extension docs): implemented `plugins/docs/provider-extensions.md` and linked it from the provider guide and docs index.

Not started (assigned to another agent):

- Subtask 3 (other doc changes): update repo-wide docs to link to the new canonical provider docs and fix stale statements.

Not started:

- Subtask 6 (reference implementation): implement an OpenAI-compatible provider + extensions and run integration tests against Ollama.
- Subtask 7 (update existing providers): align OpenRouter + core Ollama/OpenAI-compatible implementations with the reference patterns.

### What was added/changed

New provider template repo:

- `plugins/template-python-provider/`
  - `pyproject.toml`, `agent_plugin.json`, `README.md`
  - `src/template_python_provider/`:
    - `provider.py`: skeleton provider + shared accumulator mixin + custom-streaming skeleton
    - `extension.py`: no-op extension skeleton
    - `feature.py`: no-op feature skeleton
  - `tests/`: test-only provider subclasses that implement deterministic behavior so the template tests pass out-of-the-box.

New docs directory:

- `plugins/docs/index.md`
- `plugins/docs/provider-plugins.md`
- Shared docs extracted from/overlapping with `docs/plugins/development.md`:
  - `plugins/docs/plugin-packaging-and-loading.md`
  - `plugins/docs/plugin-execution-order.md`
  - `plugins/docs/ui-elements.md`
  - `plugins/docs/testing-and-validation.md`

### How to verify locally

Template tests (offline):

```bash
PYTHONPATH=plugins/template-python-provider/src:core/python \
  pytest plugins/template-python-provider/tests -q
```

Or via editable installs:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/template-python-provider[dev]"
pytest plugins/template-python-provider/tests -q
```
