# Docs Content Cleanup

Clean up the MkDocs source tree so the published documentation site is focused on Crystal Lattice product and developer documentation, not local docs-running instructions, internal planning notes, or obsolete prompt/tool artifacts.

## Requirements checklist

- [ ] Revise `docs/index.md` so it introduces Crystal Lattice and directs users to meaningful docs sections rather than explaining how to run MkDocs locally.
- [ ] Remove or relocate obsolete files that should not be published as docs content, including `docs/PLUGIN_SYSTEM_DOCS_PLAN.md`.
- [ ] Remove or relocate obsolete docs directories such as `docs/codex-tools/` and `docs/default-system-instructions/` if they are not intended for the public Crystal Lattice docs site.
- [ ] Update `mkdocs.yml` navigation after cleanup so it reflects the intended docs information architecture.
- [ ] Confirm cleanup does not delete source-of-truth content still needed elsewhere; move content to an appropriate non-MkDocs location if it remains useful.
- [ ] Run MkDocs validation after cleanup and verify the published docs tree no longer emits warnings for obsolete unnaved files.

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