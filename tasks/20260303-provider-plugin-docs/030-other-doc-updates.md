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
