# Crystal Lattice — Landing Page

Static marketing site for Crystal Lattice. Built with Astro and deployed as a pre-rendered HTML + assets bundle served by nginx.

## Documentation

- [`docs/index.md`](docs/index.md) maps the package documentation.
- [`docs/development/index.md`](docs/development/index.md) routes current
  content-system documentation, product-website content targets, and research
  knowledge.
- [`docs/development/visual-content-and-screenshot-generation.md`](docs/development/visual-content-and-screenshot-generation.md)
  documents reproducible visual derivatives and browser review.
- [`AGENTS.md`](AGENTS.md) defines website-specific content, claim, research,
  visual, and verification boundaries.

Current public copy is authored under `src/content/`. Target content belongs in
the package-owned specification, research findings belong under
`docs/development/research/`, retained normalized research evidence belongs
under `research/`, and disposable output belongs under the ignored
`artifacts/` directory.

## Packages

| Package | Version | Purpose |
|---|---|---|
| `astro` | ^5.8 | Framework — renders each page to static HTML at build time |
| `tailwindcss` | ^4.3 | Utility CSS — available but most styling is done via CSS variables in `src/styles/global.css` |
| `@tailwindcss/vite` | ^4.3 | Vite plugin that wires Tailwind 4 into Astro's build pipeline |

## Folder structure

```
landing_page/
├── AGENTS.md
├── docs/                   # Package docs, development knowledge, specifications
├── research/               # Retained normalized website research evidence
├── artifacts/              # Ignored raw research, previews, and draft captures
├── visual_assets/          # Executable visual catalog and reviewed source masters
├── src/
│   ├── pages/              # One file = one route
│   │   ├── index.astro     # /
│   │   ├── mobile.astro    # /mobile
│   │   ├── privacy.astro   # /privacy
│   │   ├── support.astro   # /support
│   │   └── terms.astro     # /terms
│   │
│   ├── layouts/
│   │   └── Layout.astro    # HTML shell shared by all pages (head, theme init script)
│   │
│   ├── components/         # Sections used on the main page
│   │   ├── Nav.astro
│   │   ├── Hero.astro
│   │   ├── Providers.astro
│   │   ├── Features.astro
│   │   ├── Quickstart.astro
│   │   ├── CTA.astro
│   │   ├── Footer.astro
│   │   └── mobile/         # Sections used on /mobile
│   │       ├── Hero.astro
│   │       ├── Features.astro
│   │       ├── Connect.astro
│   │       └── Download.astro
│   │
│   └── styles/
│       └── global.css      # Theme tokens (CSS variables), reset, base styles
│
├── public/                 # Copied as-is to dist/
│   ├── icon.svg            # Favicon and nav logo (light theme)
│   └── icon_dark.svg       # Favicon and nav logo (dark theme)
│
├── Dockerfile              # Multi-stage build: Node (yarn build) → nginx:alpine
├── nginx.conf              # Serves dist/ with long-cache headers on /_astro/
├── astro.config.mjs
├── package.json
└── tsconfig.json
```

## Theme system

All colors are CSS variables defined in `src/styles/global.css`. Dark is the default (`:root`); light overrides via `[data-theme="light"]`. The palette matches the mobile and desktop app (`theme.ts`).

The active theme is stored in `localStorage` under `cl-theme` and applied by an inline script in `Layout.astro` before the page paints to prevent flash.

## Dev

```bash
yarn dev        # dev server at localhost:4321
yarn build      # outputs to dist/
yarn preview    # serves dist/ locally (same as production)
yarn visual-assets:list
yarn visual-assets:check
yarn test:visual
```

`yarn visual-assets:update` regenerates approved public image derivatives from
the reviewed source masters and executable asset catalog.
`yarn visual-assets:capture` and `yarn visual-assets:promote-source` provide an
explicit candidate-to-reviewed-source lifecycle for generated captures.
`yarn test:visual:headed` runs the same visual contracts with visible browser
windows.

## Public URL Configuration

The landing build reads these build-time environment variables:

- `PUBLIC_CRYSTAL_LATTICE_SITE_URL`: canonical website URL used by Astro.
- `PUBLIC_CRYSTAL_LATTICE_DOCS_URL`: docs URL used by website navigation and
  calls to action.

The visible desktop and mobile **Docs** navigation links use
`PUBLIC_CRYSTAL_LATTICE_DOCS_URL`, stay in the current tab, and do not link to
the repository README. The footer also provides a documentation route.

Both default to the future production domains:

```text
PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev
```

For the current AWS testing stack:

```bash
PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com \
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com \
yarn build
```

For local development with local docs links:

```bash
PUBLIC_CRYSTAL_LATTICE_SITE_URL=http://localhost:4321 \
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://localhost:8001 \
yarn dev
```

The reproducible two-site Playwright check is documented in
`../docs_site/README.md`. It builds and serves the landing and documentation
sites with matching local URLs, follows the visible Docs link, and verifies the
generated package catalog and package routes.

## Production (Docker + nginx)

```bash
docker build -t cl-landing .
docker run -p 8080:80 cl-landing
```

The build happens inside Docker so no local Node is required on the server.
