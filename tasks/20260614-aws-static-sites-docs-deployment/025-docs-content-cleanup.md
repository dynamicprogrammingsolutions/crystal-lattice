# Docs Content Cleanup

Clean up the MkDocs source tree so the published documentation site is focused on Crystal Lattice product and developer documentation, not local docs-running instructions, internal planning notes, or obsolete prompt/tool artifacts.

## Requirements checklist

- [x] Revise `docs/index.md` so it introduces Crystal Lattice and directs users to meaningful docs sections rather than explaining how to run MkDocs locally.
- [x] Remove or relocate obsolete files that should not be published as docs content, including `docs/PLUGIN_SYSTEM_DOCS_PLAN.md`.
- [x] Remove or relocate obsolete docs directories such as `docs/codex-tools/` and `docs/default-system-instructions/` if they are not intended for the public Crystal Lattice docs site.
- [x] Update `mkdocs.yml` navigation after cleanup so it reflects the intended docs information architecture.
- [x] Confirm cleanup does not delete source-of-truth content still needed elsewhere; move content to an appropriate non-MkDocs location if it remains useful.
- [x] Run MkDocs validation after cleanup and verify the published docs tree no longer emits warnings for obsolete unnaved files.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/010-design-and-docs-alignment.md`

Related To: `tasks/20260614-aws-static-sites-docs-deployment/020-plugin-docs-and-llm-access.md`

## Current Problem

The docs home page currently reads like a local build note:

- It mentions API documentation and MkDocs/mkdocstrings.
- It lists local commands such as `pip install -r docs/requirements.txt`, `mkdocs serve`, and `mkdocs build`.
- It does not introduce Crystal Lattice as a product or guide readers toward the core concepts, quickstart, plugin system, SDK/API reference, or application configuration.

The docs source tree also contains files and directories that appear obsolete or inappropriate for the public docs site, including:

- `docs/PLUGIN_SYSTEM_DOCS_PLAN.md`
- `docs/codex-tools/`
- `docs/default-system-instructions/`

These files currently contribute to MkDocs warnings because they exist under `docs/` but are not included in the nav. More importantly, they make the published docs source tree noisy and risk exposing internal planning or prompt/tool artifacts as public documentation.

## Implementation Notes

Start by deciding whether each obsolete-looking item should be deleted, moved outside `docs/`, or intentionally published.

Recommended direction:

- Replace `docs/index.md` with a public-facing Crystal Lattice overview.
- Keep public product/developer docs under `docs/`.
- Keep generated or copied docs under explicit generated directories such as `docs/plugin-development/`, `docs/built-in-plugins/`, and `docs/reference/default-config.md` as described in task 020.
- Move internal planning notes out of `docs/` if they are still useful, for example to `plans/`, `tasks/`, or another non-MkDocs location.
- Move prompt/tool artifact documentation out of the public MkDocs tree unless it is intentionally part of the public docs information architecture.

The revised docs index should probably include:

- What Crystal Lattice is.
- Key capabilities: local-first agent runtime, Python SDK, terminal/HTTP runtime, mobile/desktop clients, provider/plugin system.
- Pointers to quickstart/application configuration.
- Pointers to current plugin docs and built-in plugin docs.
- Pointers to API reference and tool host protocol.
- Links to GitHub and the main website.

Avoid putting local docs build instructions on the public home page. If local docs development instructions are still useful, move them to a contributor/development page outside the public landing flow or to a repository README.

## Validation

Run after cleanup:

```bash
mkdocs build --strict
```

If strict mode still fails, classify each remaining warning:

- expected generated-content warning to fix in task 020
- stale docs-tree content that should be removed/moved here
- real broken link or mkdocstrings/autorefs issue needing a separate fix

Manual checks:

- Docs home page reads like public Crystal Lattice documentation.
- No obsolete planning/prompt/tool directories are published accidentally.
- MkDocs nav remains coherent after files are removed or relocated.
- Cleanup does not remove content that task 020 expects to generate or include.

## Execution plan

Added during completion after user approval.

This task will clean the published MkDocs source tree while preserving useful
reference material next to the code that uses it.

Execution approach:

1. Replace `docs/index.md` with a public Crystal Lattice documentation overview.
   The page should describe the product and route readers to guides, current
   plugin docs, built-in plugin docs, API reference, the website, and GitHub.
   It should not include local MkDocs build instructions.
2. Move `docs/PLUGIN_SYSTEM_DOCS_PLAN.md` to `plans/plugin-system-docs.md`,
   because it is a planning/TODO artifact rather than public documentation.
3. Move `docs/codex-tools/` to
   `plugins/codex-tools/reference/codex-cli-tools/`, because those schemas and
   notes are reference material for the `codex-tools` plugin implementation.
4. Move `docs/default-system-instructions/` to
   `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/`,
   because those reconstruction/reference files support the bundled default
   system-message templates and default configuration.
5. Update direct code, test, and reference-file links affected by those moves:
   `core/python/tests/test_default_system_instructions_docs.py`,
   `application/python/agent_terminal_app/default_config/codex/README.md`,
   `plugins/codex-tools/src/codex_tools/shell_tool.py`,
   `plugins/codex-tools/src/codex_tools/shell_command_tool.py`, and explicit
   self-references inside the moved Codex tool reference files.
6. Leave historical task-file references alone unless documenting this task's
   own completion. Those are handoff/history records and should not create
   broad churn.
7. Review `mkdocs.yml` for stale nav entries. Keep the public docs nav focused
   on Crystal Lattice docs and do not publish the relocated reference archives.
8. Run `python docs_site/scripts/prepare_mkdocs_site.py`, `mkdocs build`, and
   `mkdocs build --strict`. The obsolete unnaved-file warnings from
   `docs/PLUGIN_SYSTEM_DOCS_PLAN.md`, `docs/codex-tools/`, and
   `docs/default-system-instructions/` should be gone. Any remaining
   mkdocstrings/autorefs strict warnings will be classified separately.
9. Run `pytest core/python/tests/test_default_system_instructions_docs.py -q`.
10. Update this task checklist, update the parent task checklist if validation
    passes, and append completion notes summarizing moved paths, validation
    results, and residual warnings.

## Completion Notes

Added during completion.

Implemented the docs content cleanup:

- Replaced `docs/index.md` with a public Crystal Lattice documentation overview.
- Moved `docs/PLUGIN_SYSTEM_DOCS_PLAN.md` to `plans/plugin-system-docs.md`.
- Moved the internal tool streaming/display note from `docs/plugins/tools.md` to
  `plans/tool-plugin-streaming-display-notes.md`.
- Moved `docs/codex-tools/` to
  `plugins/codex-tools/reference/codex-cli-tools/`.
- Moved `docs/default-system-instructions/` to
  `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/`.
- Updated direct references in Codex tool implementation docstrings, Codex
  reference README files, and
  `core/python/tests/test_default_system_instructions_docs.py`.
- Added `docs/api/core-sdk.md` and `docs/api/events.md` to the MkDocs nav and
  LLM docs sections, and moved the remaining internal unnaved page out of
  `docs/`.
- Updated a few public docs strings from old AI Agent Platform wording to
  Crystal Lattice wording.
- Updated stale cloud-script authoring assertions in
  `core/python/tests/test_default_system_instructions_docs.py` so the focused
  test matches the current default configuration text.

Validation performed:

- `python docs_site/scripts/prepare_mkdocs_site.py` succeeded.
- `mkdocs build` succeeded and no longer reports unnaved pages for obsolete
  docs-tree artifacts. After adding the API/event pages to nav and moving the
  internal plugin tooling note, it no longer reports any unnaved pages.
- `mkdocs build --strict` was attempted and still fails only on the existing
  four mkdocstrings/autorefs warnings from `core/python/agent_core/core.py`:
  three griffe indentation warnings around line 2991 and one unresolved
  cross-reference target for `"content"`.
- `pytest core/python/tests/test_default_system_instructions_docs.py -q`
  passed.