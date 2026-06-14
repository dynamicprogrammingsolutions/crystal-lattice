# Design And Docs Alignment

Align the public website and documentation site so they feel like one Crystal Lattice product while preserving the strengths of Astro for marketing pages and Material for MkDocs for documentation.

## Requirements checklist

- [ ] Update landing page docs links to point to `https://docs.crystallattice.dev/`.
- [ ] Update MkDocs metadata to Crystal Lattice branding and production docs URL.
- [ ] Add shared logo/favicon assets for the docs site.
- [ ] Add a docs-specific CSS bridge that maps Material for MkDocs colors to the Crystal Lattice visual language.
- [ ] Verify both dark and light docs palettes remain readable and accessible.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

## Repo References

- `landing_page/astro.config.mjs:5-10` sets the Astro site URL to `https://crystallattice.dev`.
- `landing_page/src/components/Nav.astro:6-10` uses the Crystal Lattice logo and brand label.
- `landing_page/src/components/Nav.astro:12-17` currently sends "Docs" to `https://github.com/dynamicprogrammingsolutions/crystal-lattice#readme`; change this to `https://docs.crystallattice.dev/`.
- `landing_page/src/components/Nav.astro:101-120` shows the website's compact sticky nav structure and sizing.
- `landing_page/src/styles/global.css` contains the website's theme tokens. Do not import this file directly into MkDocs; use it as a reference for docs theme variables.
- `mkdocs.yml:1-4` currently needs docs branding and production URLs.
- `mkdocs.yml:7-12` already uses the Material theme and some navigation features.

## Implementation Notes

Update `mkdocs.yml` roughly as follows:

```yaml
site_name: Crystal Lattice Docs
site_description: Plugin-driven AI agent platform documentation
site_url: https://docs.crystallattice.dev/
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

- Landing page "Docs" link opens `https://docs.crystallattice.dev/`.
- Docs header/sidebar use Crystal Lattice branding.
- Dark and light docs modes are readable.
- Code blocks, tables, admonitions, and nav remain usable.
