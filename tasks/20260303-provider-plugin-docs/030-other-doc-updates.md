# Subtask: Update other docs to point to new canonical provider doc

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

## Description

After `plugins/docs/provider-plugins.md` and `plugins/template-python-provider` are added, update other documentation to:

- Point provider authors to the new canonical doc.
- Fix known outdated/misleading provider-plugin guidance.

This subtask is explicitly intended to be completed by a different agent.

## Planned changes (targets)

1. `docs/plugins/development.md`
   - Keep as the general plugin development overview (it is readable and useful).
   - Add/update a pointer for provider authors to the new canonical provider guide:
     `plugins/docs/provider-plugins.md`.

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

---

## Handoff notes for the next agent (added 2026-03-03)

Subtasks 1 and 2 are complete.

New docs now live under `plugins/docs/`:

- `plugins/docs/provider-plugins.md` (canonical provider authoring guide)
- shared pages:
  - `plugins/docs/plugin-packaging-and-loading.md`
  - `plugins/docs/plugin-execution-order.md`
  - `plugins/docs/ui-elements.md`
  - `plugins/docs/testing-and-validation.md`

New template repo:

- `plugins/template-python-provider` (skeleton provider + tests)

Recommended edits for this subtask:

1) Update repo-level docs to point to the new guide
- `README.md`: add link to `plugins/docs/provider-plugins.md` (or wherever docs are rendered in your site build).
- `docs/plugins/development.md`: add a short “Provider plugins” pointer to the new guide (do not delete this file).

2) Fix stale statements
- `README.md` currently lists OpenRouter provider under `core/python/plugins` but in this repo it lives under `plugins/openrouter/...`.

3) Fix protocol / examples drift (targeted)
- Identify and fix any statements about provider method behavior that are now misleading.
- Consider updating example providers that demonstrate patterns that break native-history retention (or label limitations).

4) Search for old references

```bash
rg -n "docs/plugins/development\.md" -S
rg -n "provider plugins" -S README.md docs
```

---

## Execution plan (added during completion 2026-03-03)

1) Audit stale provider-plugin references and OpenRouter locations across repo docs/examples.
2) Update `README.md` to:
   - link to the canonical provider authoring guide: `plugins/docs/provider-plugins.md`
   - fix OpenRouter provider location/imports (now under `plugins/openrouter` / `openrouter_plugins`)
   - correct OpenRouter test-running guidance (plugin tests live under `plugins/openrouter/tests`)
3) Update `docs/plugins/development.md` (keep as general overview) to:
   - point provider authors at `plugins/docs/provider-plugins.md`
   - fix provider method return-order guidance/examples to match runtime
4) Fix protocol/example drift in key reference docs (targeted):
   - `core/python/agent_core/types.py`
   - `core/python/agent_core/plugin/provider.py` (docstring accuracy)
   - `core/python/README.md`
5) Update OpenRouter examples/config to match the new plugin location:
   - `core/python/examples/example12_openrouter_tools_app.py`
   - `core/python/examples/example13_openrouter_tools_app_layer.py`
   - `core/python/examples/example13_openrouter_tools_app_layer_config.json`
6) Run lightweight validation: import/compile checks + example test imports.

---

## Completion notes (added during completion 2026-03-03)

Updated repo docs/examples to use `plugins/docs/provider-plugins.md` as the canonical provider authoring guide and fixed drift around OpenRouter plugin location and provider return-order guidance.

Key changes:

- Canonical provider doc is now referenced from:
  - `README.md`
  - `docs/plugins/development.md`
  - `AGENTS.md`
  - `plugins/AGENTS.md`

- Fixed OpenRouter provider location/import drift:
  - `README.md` now uses `openrouter_plugins.openrouter_provider.OpenRouterProvider` and includes `python -m pip install -e plugins/openrouter`.
  - `core/python/examples/example12_openrouter_tools_app.py` imports `openrouter_plugins.*` and its docstring includes the install command.
  - `core/python/examples/example13_openrouter_tools_app_layer_config.json` now loads the OpenRouter bundle via `path:../../../plugins/openrouter`.
  - `core/python/examples/example13_openrouter_tools_app_layer.py` docstring updated to match.

- Fixed outdated/misleading provider-plugin method guidance:
  - `docs/plugins/development.md` provider example now returns `(final_messages, partial_messages, native_messages, state)` for `call_api` and appends the assistant message to native history.
  - `core/python/agent_core/types.py` docstrings updated for `call_api` return order and the provider extension `process_chunk` example signature.
  - `core/python/agent_core/plugin/provider.py` docstring corrected for wrapper `call_api` return ordering.
  - `TYPES_AND_PROTOCOLS.md` updated to match `call_api` return ordering.

- Updated example catalogue generation:
  - `scripts/generate_examples_md.py` note strings fixed/updated and `EXAMPLES.md` regenerated.

Validation:

- `python -m compileall -q core/python plugins scripts`
- `pytest core/python/tests -q`
- `pytest core/python/examples/tests -q`
