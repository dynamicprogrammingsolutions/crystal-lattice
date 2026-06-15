# Crystal Lattice Docs Site

This directory contains support files and working notes for the Crystal Lattice documentation site. The published documentation content lives under `docs/`; this directory is for MkDocs-specific implementation assets such as Material theme overrides.

## Quickstart

From the repository root, install the Python documentation dependencies:

```bash
python -m pip install -r docs_site/requirements.txt
```

Build the static docs site:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev
python docs_site/scripts/build_mkdocs_site.py
```

The convenience build script runs the three docs-site stages in order:

1. `python docs_site/scripts/prepare_mkdocs_site.py`
2. `cd docs_site && mkdocs build`
3. `python docs_site/scripts/refresh_reference_snapshots.py`

## Dev Command

Run the docs site locally with live reload for content, navigation, and theme changes:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=http://localhost:4321
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://localhost:8001
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs serve -a 127.0.0.1:8001)
```

Then open:

```text
http://127.0.0.1:8001/
```

For stricter validation before deployment, run:

```bash
(cd docs_site && mkdocs build --strict)
```

At the moment, strict mode may still fail on pre-existing documentation warnings until the follow-up cleanup and generated-docs tasks are complete.

## Project Layout

- `docs_site/mkdocs.yml` configures the MkDocs site, Material theme, navigation, plugins, and docs-specific theme overrides.
- `docs/` contains generic authored Markdown plus generated reference Markdown snapshots for inspection.
- `docs_site/source/` contains MkDocs-only source overlays such as static assets and mkdocstrings directive reference pages.
- `docs_site/prepared/` is the generated MkDocs `docs_dir` assembled before builds.
- `docs_site/dist/` is the final static documentation site.
- `docs_site/source/assets/styles/crystal-lattice.css` contains the Crystal Lattice Material theme polish.
- `docs_site/source/assets/brand/` contains docs-site logo/favicon assets copied from the landing page.
- `docs_site/scripts/prepare_mkdocs_site.py` assembles `docs_site/prepared/` from repo-local sources before MkDocs builds.
- `docs_site/scripts/refresh_reference_snapshots.py` copies generated reference Markdown from an existing `docs_site/dist/` build into `docs/reference/`.
- `docs_site/scripts/build_mkdocs_site.py` is an umbrella convenience script that prepares, builds, and refreshes reference snapshots in order.
- `docs_site/overrides/` is used by Material for MkDocs through `theme.custom_dir`.
- `docs_site/overrides/.icons/crystal-lattice/` contains custom SVG icons that Material inlines into the generated docs site.

## Generated Docs Content

Run the preparation script before every local or CI docs build:

```bash
python docs_site/scripts/prepare_mkdocs_site.py
```

The script generates:

- `docs_site/prepared/plugin-development/` from `plugins/docs/`
- `docs_site/prepared/built-in-plugins/` from `plugins/*/README.md`
- `docs_site/prepared/reference/default-config.md` from `application/python/agent_terminal_app/default_config/config.json`

These prepared paths are ignored by git. Keep source-of-truth plugin docs and
README content in their original repo locations.

Build MkDocs after preparation:

```bash
(cd docs_site && mkdocs build)
```

Refresh generated reference Markdown snapshots after a successful MkDocs build:

```bash
python docs_site/scripts/refresh_reference_snapshots.py
```

`refresh_reference_snapshots.py` depends on `docs_site/dist/reference/**/index.md`
from a prior MkDocs build. It does not generate reference Markdown by itself; it
only copies and reshapes the built Markdown into `docs/reference/` for human
inspection. Those files should not be used as MkDocs source input.

For convenience, run all three stages with:

```bash
python docs_site/scripts/build_mkdocs_site.py
```

## Theme Assets

The docs site uses custom SVG icons so the header matches the landing page:

- `sun.svg` matches the landing page dark-mode toggle display icon.
- `moon.svg` matches the landing page light-mode toggle display icon.
- `github.svg` matches the landing page GitHub button icon.

The rendered docs header icon sizes are adjusted in `docs_site/source/assets/styles/crystal-lattice.css`:

- theme toggle icons: 15px
- GitHub/source icon: 16px

## LLM Actions

The docs site adds a page-level LLM actions dropdown through
`docs_site/overrides/partials/actions.html`.

The dropdown actions are:

- Copy the current page as generated Markdown.
- Open the current page's generated Markdown file.
- Open `llms.txt`.
- Open `llms-full.txt`.

The client-side behavior lives in `docs_site/source/assets/javascripts/llm-actions.js`.
Generated Markdown files may download in local `mkdocs serve`; production AWS
deployment should upload `*.md`, `llms.txt`, and `llms-full.txt` with
`Content-Type: text/plain; charset=utf-8` so they open inline in browsers.

## Public URL Configuration

The docs build reads these build-time environment variables:

- `PUBLIC_CRYSTAL_LATTICE_SITE_URL`: website home URL used by the docs menu.
- `PUBLIC_CRYSTAL_LATTICE_DOCS_URL`: docs canonical URL used by MkDocs and
  generated LLM links.

Both default to the future production domains:

```text
PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev
```

Set them to the temporary AWS testing domains when building for the current test
stack:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://cl-static-test.dynamicprogrammingsolutions.com
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.cl-static-test.dynamicprogrammingsolutions.com
```

## Development Notes

Keep public authored documentation content under `docs/`. Keep MkDocs
implementation assets, source-only theme overrides, generated prepared inputs,
and docs-site maintenance notes in `docs_site/`.

When changing theme or icon behavior, use a local MkDocs server and inspect both dark and light modes. For visual changes, headed browser screenshots are preferred because header alignment and Material theme state can differ from static HTML inspection.
