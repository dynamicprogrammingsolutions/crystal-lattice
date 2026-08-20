# Crystal Lattice Docs Site

This directory contains the Crystal Lattice documentation-site registry,
preparation tooling, tests, and MkDocs-specific assets. Authored documentation
lives under root `docs/`, registered package `README.md` and `docs/` trees, and
the shared plugin documentation sources described below.

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
- `docs_site/packages.toml` registers package documentation sources and public
  destinations.
- `docs/` contains repository-wide authored Markdown plus generated reference Markdown snapshots for inspection.
- `docs_site/source/` contains MkDocs-only source overlays such as static assets and mkdocstrings directive reference pages.
- `docs_site/prepared/` is the generated MkDocs `docs_dir` assembled before builds.
- `docs_site/dist/` is the final static documentation site.
- `docs_site/tests/` contains focused preparation tests and the local
  landing/docs Playwright smoke program.
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

- `docs_site/prepared/packages/index.md` from the package registry
- `docs_site/prepared/packages/<package-id>/` from each registered package
  README and `docs/` tree
- `docs_site/prepared/plugin-development/` from `plugins/docs/`
- `docs_site/prepared/built-in-plugins/` from `plugins/*/README.md` and public
  plugin-local `docs/` trees
- `docs_site/prepared/reference/default-config.md` from `application/python/agent_terminal_app/default_config/config.json`

These prepared paths are ignored by git. Keep source-of-truth plugin docs and
package README/docs content in their original repository locations.

Each built-in plugin keeps its README landing page at
`built-in-plugins/<plugin-id>/`. When the plugin has a `docs/` tree, preparation
copies it recursively beneath `built-in-plugins/<plugin-id>/docs/`, excludes
`AGENTS.md`, and links it from the landing page. An authored `docs/index.md`
remains authoritative; otherwise preparation generates a catalog index from
the copied Markdown headings.

## Package Documentation Registry

`docs_site/packages.toml` is the repository-owned publication registry. Each
`[[package]]` entry requires:

| Field | Meaning |
|---|---|
| `id` | Lowercase kebab-case public package identity |
| `title` | Display name used by the generated package catalog |
| `group` | Catalog section used to organize related packages |
| `summary` | One-sentence catalog description |
| `source` | Repository-relative package root |
| `destination` | Required public destination, `packages/<id>` |
| `include_readme` | Whether README may provide the package landing page |
| `include_docs` | Whether the package `docs/` tree is copied recursively |
| `publish_development` | Whether `docs/development/` is included |

The generated `/packages/` catalog groups entries by their first registry
appearance and lists packages in registry order within each group.
For each package, `docs/index.md` is the preferred
`packages/<id>/index.md`. When no package docs index exists, an enabled
`README.md` becomes that landing page. README is not also emitted as a
duplicate page.

Package docs preserve their relative directory structure and non-Markdown
assets. Markdown links to another published source become site-relative links;
links to repository files that are not published point to their GitHub source.
Files named `AGENTS.md` are excluded recursively. `docs/development/` is
excluded when `publish_development` is false.

Preparation rejects malformed or unknown registry fields, missing configured
inputs, duplicate identities/sources/destinations, path traversal, non-public
maintenance roots, and output collisions. Registry validation and all
generation happen before the existing prepared tree is replaced, so a failed
run leaves the previous prepared output intact.

The MkDocs **Packages** section mirrors the catalog groups and gives registered
package landing pages active navigation context. Shared plugin-authoring guides
live under **Plugin Development**. The generated built-in-plugin index remains
in that section, while individual generated plugin pages are reached from the
index instead of being enumerated in global navigation.

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

## Automated Verification

Install documentation development dependencies:

```bash
python -m pip install -r docs_site/requirements-dev.txt
python -m playwright install chromium
```

Run focused registry and assembly tests:

```bash
python -m pytest docs_site/tests/test_prepare_mkdocs_site.py -q
```

To smoke-test the website-to-documentation path, build both sites with matching
local public URLs:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=http://127.0.0.1:4321
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://127.0.0.1:8001
npm --prefix landing_page run build

python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

Start the landing preview and MkDocs server in separate terminals:

```bash
npm --prefix landing_page run preview -- --host 127.0.0.1 --port 4321
```

```bash
PUBLIC_CRYSTAL_LATTICE_SITE_URL=http://127.0.0.1:4321 \
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://127.0.0.1:8001 \
mkdocs serve -f docs_site/mkdocs.yml -a 127.0.0.1:8001
```

With both servers running, execute in another terminal:

```bash
python docs_site/tests/smoke_sites.py \
  --landing-url http://127.0.0.1:4321 \
  --docs-url http://127.0.0.1:8001
```

The smoke program verifies desktop and mobile landing-page Docs links, same-tab
cross-site navigation, documentation overview and search, generated package
catalog and navigation context, every registered package route, keyboard
activation of the mobile docs drawer, and a representative README-fallback
package page.

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
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com
```

## Development Notes

Keep package-visible documentation with its package, repository-wide guidance
under root `docs/`, and shared plugin-authoring guidance under `plugins/docs/`.
Keep the publication registry, MkDocs implementation assets, source-only theme
overrides, generated prepared inputs, and docs-site maintenance notes in
`docs_site/`.

When changing theme or icon behavior, use a local MkDocs server and inspect both dark and light modes. For visual changes, headed browser screenshots are preferred because header alignment and Material theme state can differ from static HTML inspection.
