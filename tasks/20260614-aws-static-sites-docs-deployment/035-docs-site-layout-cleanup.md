# Docs Site Layout Cleanup

Separate authored documentation, MkDocs-specific source files, generated
inspection artifacts, prepared build inputs, and final static build output.

## Task checklist

- [x] Move MkDocs configuration and dependency files under `docs_site/`.
- [x] Create `docs_site/source/` for MkDocs-specific source overlays such as assets and mkdocstrings directive pages.
- [x] Move MkDocs-only reference directive files from `docs/reference/` to `docs_site/source/reference/`.
- [x] Keep `docs/` as the canonical location for generic authored Markdown and generated reference Markdown that humans can inspect.
- [x] Update docs preparation so it assembles `docs_site/prepared/` from `docs/`, `docs_site/source/`, `plugins/docs/`, plugin READMEs, and generated config docs.
- [x] Ensure generated or inspection-only `docs/` paths do not feed back into prepared MkDocs inputs.
- [x] Update the final MkDocs build output from root `site/` to `docs_site/dist/`.
- [x] Generate inspectable reference Markdown from the built MkDocs Markdown output back into `docs/reference/`.
- [x] Update AWS static-site sync and deployment documentation to use `docs_site/dist/`.
- [x] Update task `040` handoff notes so GitHub Actions builds and deploys from the new docs layout.
- [x] Verify normal docs build, generated `llms.txt`, generated reference Markdown, and the live AWS testing docs deployment.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/030-aws-static-hosting-infra.md`

Blocks: `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`

## Implementation Notes

Use `docs_site/source/` as the MkDocs-specific source overlay name. It is clearer
than `mkdocs` because the directory will contain source material consumed by
MkDocs, not the generated final site.

Target layout:

```text
docs/
  index.md
  api/
  plugins/
  reference/                  # generated Markdown reference snapshots for inspection

docs_site/
  mkdocs.yml                  # MkDocs configuration
  requirements.txt            # docs Python dependencies
  source/                     # MkDocs-only source overlay
    assets/
    reference/                # mkdocstrings directive pages
  prepared/                   # generated MkDocs docs_dir, ignored
  dist/                       # final static site output, ignored
  overrides/
  scripts/
```

The build should run from the repository root, but it should use
`docs_site/mkdocs.yml`:

```bash
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

Keep `prepare_mkdocs_site.py`, `cd docs_site && mkdocs build`, and
`refresh_reference_snapshots.py` separable so callers can choose when to run
each side-effecting stage. Also provide `docs_site/scripts/build_mkdocs_site.py`
as a convenience wrapper that runs the full sequence in order.

Generated reference Markdown should be copied from built Markdown outputs under
`docs_site/dist/reference/**/index.md` back into `docs/reference/**/*.md` so
humans can inspect the resolved mkdocstrings output in the repo workspace.

Update `.gitignore` so prepared and final site outputs are ignored:

```text
/docs_site/prepared/
/docs_site/dist/
/docs/plugin-development/
/docs/built-in-plugins/
```

Keep `docs/reference/` available as generated Markdown snapshots for inspection.
The preparation script must exclude `docs/reference/` from `docs_site/prepared/`
so the MkDocs-specific source overlay keeps precedence.

## Execution plan

Added during completion after user approval.

This cleanup should happen before GitHub Actions task `040`, so the workflow can
target the final docs layout instead of root `site/`.

Execution approach:

1. Add this task file and insert it before `040` in the parent task checklist.
2. Move MkDocs-only files into `docs_site/`: `mkdocs.yml`,
   `requirements.txt`, static assets, and reference source pages containing
   mkdocstrings directives or other MkDocs reference source content.
3. Replace the docs preparation script so it assembles `docs_site/prepared/`
   from authored `docs/`, `docs_site/source/`, current plugin docs, built-in
   plugin README pages, and generated default config reference docs.
4. Add a separate reference snapshot refresh script that copies built Markdown
   from `docs_site/dist/reference/**/index.md` into `docs/reference/**/*.md`.
5. Add a docs build wrapper that runs preparation, builds MkDocs with
   `docs_site/mkdocs.yml`, outputs to `docs_site/dist/`, and then refreshes
   generated reference Markdown snapshots under `docs/reference/`.
6. Update ignores so prepared inputs, final docs output, and generated
   inspection-only docs are not accidentally committed as source.
7. Update AWS sync, docs-site README, AWS README, and task `040` handoff notes to
   use `docs_site/dist/` and `docs_site/requirements.txt`.
8. Verify the build, generated reference snapshots, generated LLM files, sync
   script, live docs URLs, and inline content types.

## Completion Notes

Added during completion.

Implemented the docs layout cleanup:

- Moved MkDocs config to `docs_site/mkdocs.yml`.
- Moved docs Python dependencies to `docs_site/requirements.txt`.
- Created `docs_site/source/` for MkDocs-specific source overlays.
- Moved docs assets to `docs_site/source/assets/`.
- Moved source reference pages to `docs_site/source/reference/`.
- Removed generated `docs/plugin-development/`, `docs/built-in-plugins/`, and
  old generated `docs/reference/` source inputs.
- Updated `docs_site/scripts/prepare_mkdocs_site.py` to assemble
  `docs_site/prepared/` from `docs/`, `docs_site/source/`, `plugins/docs/`,
  plugin READMEs, and generated default config docs.
- Added `docs_site/scripts/refresh_reference_snapshots.py`, which copies
  generated reference Markdown from an existing `docs_site/dist/` build into
  `docs/reference/`.
- Added `docs_site/scripts/build_mkdocs_site.py`, which is an umbrella
  convenience script that prepares, builds with `docs_site/mkdocs.yml`, outputs
  `docs_site/dist/`, and then refreshes inspectable generated Markdown snapshots
  under `docs/reference/`.
- Updated `.gitignore` for `docs_site/prepared/`, `docs_site/dist/`,
  `docs/plugin-development/`, and `docs/built-in-plugins/`.
- Updated `deploy/aws-static-sites/sync.sh` to deploy `docs_site/dist/`.
- Updated `docs_site/README.md`, `deploy/aws-static-sites/README.md`, and task
  `040` to use the new layout.

Verification performed:

- `python -m pip install -r docs_site/requirements.txt` succeeded; dependencies
  were already installed.
- `PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com python docs_site/scripts/build_mkdocs_site.py` succeeded.
- The build produced `docs_site/prepared/` and `docs_site/dist/`.
- The build refreshed generated reference Markdown under `docs/reference/`; for
  example `docs/reference/agent_core/plugin/provider.md` now contains resolved
  Markdown output rather than `::: agent_core.plugin.provider`.
- `bash -n` passed for the AWS static-site scripts.
- `python -m py_compile` passed for the docs preparation/build/reference refresh
  scripts.
- `ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/sync.sh --stack-name crystal-lattice-static-sites-test --region us-east-1` succeeded and deployed from `docs_site/dist/`.
- Live checks passed for the docs homepage, `Website Home` link, canonical URL,
  `llms.txt`, and `reference/agent_core/plugin/provider/index.md`.
- S3 `head-object` confirmed generated Markdown and `llms.txt` are served as
  `Content-Type: text/plain; charset=utf-8`.

Known caveat:

- MkDocs still emits the pre-existing griffe docstring indentation warnings and
  one mkdocs-autorefs warning for `"content"`. In this worktree, griffe reports
  the source path from the currently installed editable Python package, which
  points at another local worktree. The normal build succeeds; strict mode is
  still expected to fail until those documentation warnings are cleaned up.