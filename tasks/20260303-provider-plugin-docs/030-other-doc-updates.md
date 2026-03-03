# Subtask: Update other docs to point to new canonical provider doc

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

## Description

After `plugins/docs/provider-plugins.md` and `plugins/template-python-provider` are added, update other documentation to:

- Point provider authors to the new canonical doc.
- Fix known outdated/misleading provider-plugin guidance.

This subtask is explicitly intended to be completed by a different agent.

## Planned changes (targets)

1. `docs/plugins/development.md`
   - Deprecate or convert to a short landing page that links to `plugins/docs/provider-plugins.md`.

2. `README.md`
   - Fix plugin location references that incorrectly claim OpenRouter provider is in `core/python/plugins` (it is under `plugins/openrouter/...`).
   - Update references to the new provider authoring doc.

3. `TYPES_AND_PROTOCOLS.md` and other protocol docs
   - Fix provider method descriptions that conflict with current runtime code/providers.
   - Remove or clarify ambiguous method-return descriptions.

4. `EXAMPLES.md` and provider examples
   - Ensure examples either follow native-history retention best practices or clearly label limitations.

5. Anywhere that currently links to `docs/plugins/development.md` for provider authoring
   - Update those references to `plugins/docs/provider-plugins.md`.

## Success criteria

- New doc becomes the canonical reference used by README and plugin development docs.
- Known incorrect references are corrected.
