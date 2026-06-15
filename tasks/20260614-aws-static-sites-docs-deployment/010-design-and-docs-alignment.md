# Design And Docs Alignment

Align the public website and documentation site so they feel like one Crystal Lattice product while preserving the strengths of Astro for marketing pages and Material for MkDocs for documentation.

## Requirements checklist

- [x] Update landing page docs links to point to `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/` for the testing phase.
- [x] Update MkDocs metadata to Crystal Lattice branding and the temporary testing docs URL.
- [x] Add shared logo/favicon assets for the docs site.
- [x] Add a docs-specific CSS bridge that maps Material for MkDocs colors to the Crystal Lattice visual language.
- [x] Verify both dark and light docs palettes remain readable and accessible.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

## Repo References

- `landing_page/astro.config.mjs:5-10` currently sets the Astro site URL to `https://crystallattice.dev`; use `https://crystallattice.dev.dynamicprogrammingsolutions.com` during the testing phase.
- `landing_page/src/components/Nav.astro:6-10` uses the Crystal Lattice logo and brand label.
- `landing_page/src/components/Nav.astro:12-17` currently sends "Docs" to `https://github.com/dynamicprogrammingsolutions/crystal-lattice#readme`; change this to `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/` during the testing phase.
- `landing_page/src/components/Nav.astro:101-120` shows the website's compact sticky nav structure and sizing.
- `landing_page/src/styles/global.css` contains the website's theme tokens. Do not import this file directly into MkDocs; use it as a reference for docs theme variables.
- `mkdocs.yml:1-4` currently needs docs branding and production URLs.
- `mkdocs.yml:7-12` already uses the Material theme and some navigation features.

## Implementation Notes

Update `mkdocs.yml` roughly as follows:

```yaml
site_name: Crystal Lattice Docs
site_description: Plugin-driven AI agent platform documentation
site_url: https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/
repo_url: https://github.com/dynamicprogrammingsolutions/crystal-lattice

theme:
  name: material
  logo: assets/brand/icon.svg
  favicon: assets/brand/icon.svg
  features:
    - navigation.sections
    - navigation.tabs
    - content.code.copy
  palette:
    - scheme: slate
      primary: black
      accent: blue
      toggle:
        icon: material/weather-sunny
        name: Switch to light mode
    - scheme: default
      primary: white
      accent: blue
      toggle:
        icon: material/weather-night
        name: Switch to dark mode

extra_css:
  - assets/styles/crystal-lattice.css
```

Use the landing page icons as the source for docs brand assets:

- `landing_page/public/icon.svg`
- `landing_page/public/icon_dark.svg`

Potential docs asset locations:

- `docs/assets/brand/icon.svg`
- `docs/assets/brand/icon_dark.svg`
- `docs/assets/styles/crystal-lattice.css`

Use temporary testing domains during this task:

- Website: `https://crystallattice.dev.dynamicprogrammingsolutions.com`
- Docs: `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com`

Leave a clear follow-up note or configuration seam so the final domain switch can later update these to:

- Website: `https://crystallattice.dev`
- Docs: `https://docs.crystallattice.dev`

The CSS should override Material variables only. Keep it focused on:

- background and surface colors
- body and secondary text colors
- accent/link colors
- code block background and borders
- header/sidebar border tones
- small typography refinements if needed

Avoid global resets or Tailwind imports in MkDocs.

## Validation

Run:

```bash
python -m pip install -r docs/requirements.txt
mkdocs build --strict
mkdocs serve
```

Also run the landing page build:

```bash
cd landing_page
yarn install --frozen-lockfile
yarn build
```

Manual checks:

- Landing page "Docs" link opens `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/`.
- Docs header/sidebar use Crystal Lattice branding.
- Dark and light docs modes are readable.
- Code blocks, tables, admonitions, and nav remain usable.

## Execution plan

Added during completion after user approval.

This task is a contained design and linking pass. It should align the public website and the documentation site so they feel like parts of one Crystal Lattice product, while leaving AWS infrastructure, GitHub Actions deployment, copied plugin docs, and LLM-accessible docs to later subtasks.

Use the temporary testing domains during this implementation:

- Website: `https://crystallattice.dev.dynamicprogrammingsolutions.com`
- Docs: `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com`

The final production domains remain future cutover targets:

- Website: `https://crystallattice.dev`
- Docs: `https://docs.crystallattice.dev`

Execution approach:

1. Audit current website links and domain references in `landing_page/`, especially `astro.config.mjs`, `Nav.astro`, footer components, and YAML-driven CTA content. Keep GitHub repository links as GitHub links, but move docs-oriented labels such as "Docs" and "Read the docs" to the temporary docs domain.
2. Update Astro metadata so the landing site builds with the temporary website domain as its canonical site URL.
3. Update `mkdocs.yml` from generic AI Agent Platform metadata to Crystal Lattice Docs metadata, using the temporary docs URL for `site_url` and the Crystal Lattice repository for `repo_url`.
4. Add shared docs brand assets by copying the existing landing icons into the MkDocs docs tree. Configure Material for MkDocs to use those assets for logo/favicon.
5. Configure Material's built-in light/dark palette as the base docs theme. Keep the docs as a documentation site rather than duplicating the marketing-site layout.
6. Add a focused docs-only CSS bridge through `extra_css`. Use the landing page's theme tokens as a reference, but override Material variables directly instead of importing Astro/Tailwind CSS. Keep the CSS limited to colors, surfaces, borders, links, nav state, and code styling.
7. Verify locally with `mkdocs build --strict` and the Astro `yarn build`.
8. Run local preview servers and use headed Playwright screenshots, plus `view_image`, to inspect the website and docs in desktop and mobile sizes. Check dark and light docs modes, nav/header branding, code blocks, links, and overall readability.
9. Mark task 010 checklist items complete only after implementation and verification pass. Add completion notes summarizing files changed, verification commands, screenshots, and any remaining caveats.

## Completion Notes

Added during completion.

Implemented the design and docs alignment pass for the temporary testing domains:

- Website canonical URL now uses `https://crystallattice.dev.dynamicprogrammingsolutions.com`.
- Website docs links now point to `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/` from the nav and home CTA.
- Legal prose now names the temporary testing website domain and the later final website domain.
- MkDocs now uses `Crystal Lattice Docs` branding, the temporary docs `site_url`, a GitHub repo link, Material palette toggles, and Crystal Lattice logo/favicon assets.
- Added `docs/assets/brand/icon.svg`, `docs/assets/brand/icon_dark.svg`, and `docs/assets/styles/crystal-lattice.css`.
- Added `docs_site/` for docs-site-specific implementation notes and Material override icons.
- Replaced Material's default palette and GitHub/source icons with custom Crystal Lattice SVGs under `docs_site/overrides/.icons/crystal-lattice/`.
- Updated the docs home page title and introduction to Crystal Lattice wording.
- Adjusted the mobile landing nav so the header no longer clips at 390px.

Verification performed:

- `python -m pip install -r docs/requirements.txt` succeeded; dependencies were already installed.
- `yarn install --frozen-lockfile` in `landing_page/` succeeded with existing package warnings only.
- `yarn build` in `landing_page/` succeeded.
- `mkdocs build` succeeded.
- `mkdocs build --strict` was attempted but failed on existing repository docs warnings unrelated to this task: many pre-existing docs files omitted from nav, two old broken relative links in `docs/plugins/application-config.md`, existing griffe indentation warnings in `core/python/agent_core/core.py`, and an existing mkdocs-autorefs warning for `"content"`.
- Used headed Playwright with local preview servers and inspected screenshots with `view_image`.
- Verified docs header icon polish with headed Playwright: one active palette icon at a time, 15px palette SVG, and centered 16px GitHub/source SVG.

Local screenshot artifacts, ignored by git under `tmp/`:

- `tmp/screenshots/task-010/landing-desktop.png`
- `tmp/screenshots/task-010/landing-mobile.png`
- `tmp/screenshots/task-010/docs-dark-desktop.png`
- `tmp/screenshots/task-010/docs-light-desktop.png`
- `tmp/screenshots/task-010/docs-mobile.png`
- `tmp/screenshots/task-010/docs-code-dark.png`
- `tmp/screenshots/task-010/docs-header-polished-dark.png`
- `tmp/screenshots/task-010/docs-header-polished-light.png`

Visual findings:

- Website desktop and mobile layouts render cleanly after the mobile nav adjustment.
- Docs dark and light modes are readable and visually aligned with the Crystal Lattice website palette.
- Docs mobile layout is readable, with no header clipping.
- Code blocks on the plugin development guide remain readable in dark mode.
- Docs header icons now visually match the landing page proportions and alignment.
