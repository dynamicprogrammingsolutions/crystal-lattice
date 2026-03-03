# Provider plugin developer documentation + template

Create a complete, up-to-date provider plugin development guide and a provider plugin template repo.

This work has three subtasks:

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

- Template: `tasks/20260303-provider-plugin-docs/010-template-python-provider.md`
- Doc page: `tasks/20260303-provider-plugin-docs/020-provider-plugins-doc.md`
- Other doc changes: `tasks/20260303-provider-plugin-docs/030-other-doc-updates.md`
