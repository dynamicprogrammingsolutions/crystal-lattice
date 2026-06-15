# Crystal Lattice Docs Site

This directory contains support files and working notes for the Crystal Lattice documentation site. The published documentation content lives under `docs/`; this directory is for MkDocs-specific implementation assets such as Material theme overrides.

## Quickstart

From the repository root, install the Python documentation dependencies:

```bash
python -m pip install -r docs/requirements.txt
```

Build the static docs site:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev
python docs_site/scripts/prepare_mkdocs_site.py
mkdocs build
```

## Dev Command

Run the docs site locally with live reload for content, navigation, and theme changes:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=http://localhost:4321
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://localhost:8001
python docs_site/scripts/prepare_mkdocs_site.py
mkdocs serve -a 127.0.0.1:8001
```

Then open:

```text
http://127.0.0.1:8001/
```

For stricter validation before deployment, run:

```bash
mkdocs build --strict
```

At the moment, strict mode may still fail on pre-existing documentation warnings until the follow-up cleanup and generated-docs tasks are complete.

## Project Layout

- `mkdocs.yml` configures the MkDocs site, Material theme, navigation, plugins, and docs-specific theme overrides.
- `docs/` contains the Markdown and static assets published as documentation content.
- `docs/assets/styles/crystal-lattice.css` contains the Crystal Lattice Material theme polish.
- `docs/assets/brand/` contains docs-site logo/favicon assets copied from the landing page.
- `docs_site/scripts/prepare_mkdocs_site.py` generates publishable docs content from repo-local sources before MkDocs builds.
- `docs_site/overrides/` is used by Material for MkDocs through `theme.custom_dir`.
- `docs_site/overrides/.icons/crystal-lattice/` contains custom SVG icons that Material inlines into the generated docs site.

## Generated Docs Content

Run the preparation script before every local or CI docs build:

```bash
python docs_site/scripts/prepare_mkdocs_site.py
```

The script generates:

- `docs/plugin-development/` from `plugins/docs/`
- `docs/built-in-plugins/` from `plugins/*/README.md`
- `docs/reference/default-config.md` from `application/python/agent_terminal_app/default_config/config.json`

These generated paths are ignored by git. Keep source-of-truth plugin docs and README content in their original repo locations.

## Theme Assets

The docs site uses custom SVG icons so the header matches the landing page:

- `sun.svg` matches the landing page dark-mode toggle display icon.
- `moon.svg` matches the landing page light-mode toggle display icon.
- `github.svg` matches the landing page GitHub button icon.

The rendered docs header icon sizes are adjusted in `docs/assets/styles/crystal-lattice.css`:

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

The client-side behavior lives in `docs/assets/javascripts/llm-actions.js`.
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

Keep public documentation content under `docs/`. Keep MkDocs implementation assets, source-only theme overrides, and docs-site maintenance notes in `docs_site/`.

When changing theme or icon behavior, use a local MkDocs server and inspect both dark and light modes. For visual changes, headed browser screenshots are preferred because header alignment and Material theme state can differ from static HTML inspection.
