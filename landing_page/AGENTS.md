# Landing Website Guidelines

This directory owns the Crystal Lattice product website, its authored public
content, and package-local website development knowledge.

## Start Here

Before changing the website, read:

- `README.md`
- `docs/index.md`
- `docs/visual-asset-framework.md`
- `docs/visual-assets.md`
- `docs/development/index.md`
- `docs/development/content-system.md`
- `docs/development/specifications/product-website-content/index.md`

For positioning or research work, also read:

- `docs/development/research/index.md`
- `docs/development/research/positioning-and-product-baseline.md`
- `docs/development/research/research-method.md`

## Content Boundaries

- `src/content/` contains current public website content. It describes
  delivered behavior only.
- `docs/development/specifications/product-website-content/` defines intended
  communication outcomes. A target in the specification is not a current
  product claim.
- `docs/development/research/` contains supporting knowledge, hypotheses,
  findings, uncertainty, and recommendations. Research does not become public
  copy automatically.
- `research/` contains retained normalized evidence, manifests, datasets, and
  review records when research tasks create them.
- `artifacts/` contains disposable raw responses, caches, browser output,
  previews, and intermediate screenshots. The directory is ignored.
- `visual_assets/` contains the executable visual catalog and reviewed,
  sanitized source masters used to reproduce public derivatives.
- `public/` contains approved files shared by both website variants.
- `sites/staging/public/` contains staging-only review assets. The staging
  build copies them into its output; the production build must not contain
  them.

Do not copy task phases, requirement IDs, approval state, research confidence
labels, or internal progress into public website content.

## Claim and Source Rules

- Use plain product language before internal terms such as provider-native,
  bridge, application plugin, or content section type.
- Distinguish Crystal Lattice configured-agent compatibility profiles from the
  official Codex, Claude Code, Gemini, Qwen, Kimi, Grok, or other products.
- Distinguish current, optional, partial, experimental, planned, unsupported,
  and not-applicable behavior where the difference matters.
- Do not redefine provider, plugin, bridge, mobile, desktop, or CLI behavior in
  this package. Summarize the user-relevant fact and retain evidence pointing
  to its owning package documentation, source, test, or release metadata.
- Do not publish placeholder screenshots, planning labels, or example APIs
  known to be unverified.
- Public release URLs, versions, checksums, architectures, and store states
  must come from maintained release inputs rather than duplicated prose when
  practical.

## Research and Privacy

- Preserve source URL, date, query or discovery route, source facts, inferred
  fields, confidence, and review state for retained evidence.
- Keep source facts separate from interpretation.
- Retain only bounded excerpts needed for analysis.
- Do not commit private interview recordings, full transcripts, personal
  profiles, credentials, complete downloaded pages, browser state, or raw API
  caches.
- Store disposable research output under `artifacts/`, not in documentation or
  public assets.

## Visual Content

- Use sanitized, deterministic product states for production screenshots and
  recordings.
- Keep draft captures under `artifacts/`; move only approved production files
  to `public/`.
- Follow
  `docs/visual-asset-framework.md` when adding framework assets, commands,
  lifecycle callbacks, pipelines, custom rules, or catalog commands.
- Follow
  `docs/visual-assets.md` when selecting or changing concrete image, capture,
  fixture, derivative, or website-presentation processing.
- Follow
  `docs/development/visual-content-and-screenshot-generation.md` when changing
  catalog dispatch, runtime services, lifecycle composition, mutation safety,
  or other visual-asset architecture.

## Verification

From `landing_page/`:

```bash
yarn build:production
yarn build:staging
yarn preview:production
yarn preview:staging
```

For substantive content or route changes, also verify:

- desktop and mobile viewport behavior;
- keyboard and semantic accessibility;
- all public links and downloads;
- current product and release claims against their owning sources;
- absence of visible placeholders or internal planning language;
- compatibility with the landing-to-documentation Playwright smoke flow when
  documentation navigation changes.
