# Website Content System

This page describes the current `landing_page` implementation. It does not
define the intended product message; that target belongs to the
[product website content specification](specifications/product-website-content/index.md).

## Authored Sources

Current page content is authored under:

```text
src/content/pages/
```

Variant-owned homepage content is authored under:

```text
sites/production/content/pages/home.yaml
sites/staging/content/pages/home.yaml
```

The page loader checks the active variant first and falls back to
`src/content/pages/` for shared pages. Production is the default variant.

The production homepage source is the exact `d3fe28a6` historical baseline.
`sites/production/content/sections/getting-started.yaml` is inserted after its
hero at load time. Keeping the addition separate lets validation compare the
baseline file byte-for-byte with Git history while reviewing the added section
independently.

`sites/production/content/home-adjustments.yaml` records the one approved
historical deviation: remove the now-redundant hero installation chooser and
retarget the hero primary action to `#getting-started`. The historical
**Computer to phone** section and all other baseline content remain unchanged.

Accepted public release metadata used by shared website controls is authored
under:

```text
src/content/releases/
```

The desktop release document owns the exact versioned DMG URL, version/build,
minimum macOS version, universal architectures, and SHA-256 checksum used by
the shared header download link. Update it only from independently verified
public release evidence.

Long-form Markdown used by pages is authored under:

```text
src/content/markdown/
```

Current top-level routes are implemented by Astro page files under
`src/pages/`. The main product, mobile, privacy, support, and terms routes load
their corresponding content documents instead of embedding full page copy in
the route component.

## Rendering Flow

The current page flow is:

```text
src/content/pages/<page>.yaml
        ↓
src/content/loadPage.ts
        ↓
src/section-system/preparePage.ts
        ↓
src/section-system/SectionRenderer.astro
        ↓
src/section-system/registry.ts
        ↓
src/sections/<section>.ts
        ↓
src/components/<Section>.astro
        ↓
pre-rendered HTML
```

`src/content/pageTypes.ts` defines the TypeScript shapes consumed by section
components. Section definitions may prepare source content before rendering,
including loading and transforming referenced Markdown.

The product-page hero may optionally render installation content, but the
current homepage owns its canonical installation choices in Getting Started
step 1. That `install` object defines the default method, tab labels, exact
commands, platform support text, manual-download action, and documentation
routes. `InstallationChooser.astro` renders the accessible selector; installer
commands are not duplicated elsewhere on the page.

The `gettingStarted` section is a semantic ordered workflow with bounded step
kinds for the current onboarding path: installation chooser, command,
release-backed Desktop download, Desktop connection, mobile availability, and
mobile connection. The Desktop download reads maintained release metadata
rather than embedding a second artifact URL.

Feature-showcase sections may opt into card or editorial presentation and
attach review status to the section or individual items. The homepage
uses prominent, unframed feature titles attached directly to the hero.
Each image owns its card, using the provider-example treatment. Missing proof
can render as a clearly labeled placeholder
only in an explicitly approved local structural prototype. Draft labels and
placeholder panels are not publication-ready product evidence.

The homepage keeps all six features in one `featureShowcase.items` list.
Their list order is their reading order. An optional item
`layout: full-width` spans the desktop columns and uses a 16:9 image frame;
omitting it (or using `compact`) uses the normal column and a 3:4 frame.
All items use 3:4 frames on phones, below the existing 760px breakpoint.
The selected layout starts with four end-user features, followed by the
plugin and transparency features for deeper inspection.

To restore option A, reorder the same items to model families, plugins,
transparency, work from anywhere, vibe-anything, and session workspaces, then
remove the two `layout: full-width` settings. No component change or duplicate
feature content is needed. The six-feature group still precedes Getting
Started in either arrangement.

`ProofImage` owns the inset screenshot canvas, border, and light/dark background.
It fits the complete screenshot inside the canvas. `FeatureMedia` gives each
highlight image a card with optional `assets[].label` and
`assets[].description` displayed above the screenshot. Feature-level copy
stays outside the image card. Standard provider examples already own an image
card, so they omit the additional media wrapper to avoid nested outer cards.

`FeatureMedia` supplies
native horizontal scrolling and a small custom element that synchronizes
side chevron overlays and dots below the card with scroll position. Chevron
position follows the actual screenshot center, independently of caption height.
It handles resized
frames and removes its listeners/observer when Astro navigation removes the
element. Single images have no controls. Only pagination follows the image
card; no text link, caption, or scroll hint is added beneath it.

Shared grid rows align each compact pair's feature copy, image captions, and
screenshot canvases without fixed
text heights. At one column every item has independent rows; browsers without
subgrid retain ordinary vertical item flow. Screenshot galleries also reuse
the common image frame and keep titles/descriptions above it.

The former extra transparency and plugin-action galleries were folded into
their owning highlights. The `session-workbench` fragment identifies its
workspace highlight rather than a second lower-page pitch.

### Responsive proof sources and local candidates

An image asset can additionally define `srcCompact`, `srcCompactDark`,
`widthCompact`, and `heightCompact`. `ProofImage` uses that source in compact
feature placement at every viewport size. In expanded placement, `ThemedImage`
uses a `<picture>` source below the existing 760px breakpoint and the wide
image above it. Theme changes update both the image and source URLs. Existing
assets retain their original fields and behavior; the section layout is
independent of the source variants.

The Session actions candidate is available through an explicit local build:

```bash
CRYSTAL_SESSION_ACTIONS_PREVIEW=1 yarn build
CRYSTAL_SESSION_ACTIONS_PREVIEW=1 yarn preview --host 0.0.0.0 --port 4182
```

This applies the candidate to the first plugin-highlight image while retaining
its existing title/description and neighboring placeholders. It builds the
actual site under `artifacts/plugin-session-actions-site/` and copies only the
four generated candidate derivatives into that output. It does not change
authored homepage YAML, reviewed source masters, or `public/`. A normal build
continues to show the maintained placeholder.

Generate the required candidates through the catalog workflow documented in
[Visual Asset Processing Pipelines](../visual-assets.md). The preview is for
contextual review and is not final asset acceptance.

The complete plugin/transparency batch uses the same page and renderer:

```bash
CRYSTAL_PROOF_BATCH_PREVIEW=1 yarn build
CRYSTAL_PROOF_BATCH_PREVIEW=1 yarn preview --host 0.0.0.0 --port 4182
```

This flag overlays two images in `feature-plugins`, two images in
`feature-transparency`, and the Vibe workflow image. The session-list and former
separate financial report candidates remain
retained outside the homepage preview. Recipe-owned wide/portrait and light/dark derivatives
are copied into the ignored site output. The combined financial report caption
adds **Sample data** and its illustrative $550 weekly assumption. Candidates
with missing derivatives or a changed capture configuration retain their
authored placeholder instead of showing stale screenshots. Authored YAML and
reviewed public assets remain the normal
build's content source. There is no separate gallery.

The page loader passes the landing package root explicitly to the candidate
freshness check. During Astro's build, the module's bundled `import.meta.url`
does not identify the maintained source directory; using that location would
leave placeholders despite valid captures. Browser checks require the selected
candidate images to load. Missing/stale candidates keep their authored
placeholder.

The active clear-product-overview candidate uses an explicit local-only build:

```bash
yarn review:product-overview
CRYSTAL_PRODUCT_OVERVIEW_PREVIEW=1 yarn build
CRYSTAL_PRODUCT_OVERVIEW_PREVIEW=1 yarn preview --host 0.0.0.0 --port 4184
```

This mode inserts the `productOverview` section after a plain-language hero.
Four stories explain one agent session, persistent workspace organization,
per-session configuration, and cross-device continuity. All stories remain in
ordinary document order at every width; the section has no tabs, carousel,
autoplay, swipe requirement, or hidden primary content.

Each story owns direct visitor copy and one or two images. Every image has one
interface-oriented title, one source set with optional compact variants,
useful alt text, and a short caption describing the relationship to notice.
The configuration story is the only current two-image comparison because the
Agent picker and provider-contributed controls establish different necessary
relationships.

The preview removes the unfinished six-highlight block. It reuses the
configured-agent and provider-controls evidence inside the overview and places
the Vibe workflow after Getting Started so its secondary role can be judged in
context. Connection setup remains in Getting Started rather than becoming a
fifth overview story.

The candidate source/copy contract lives in
`scripts/visual-assets/product-overview-preview.mjs`; composition lives in
`scripts/visual-assets/product-overview-composition.mjs`. Missing candidates
fail the explicit build. Browser review is gated by
`CRYSTAL_PRODUCT_OVERVIEW_PREVIEW=1` and writes screenshots under
`artifacts/product-overview-review/`. Normal authored content, reviewed public
sources, and `public/` remain unchanged until human approval and explicit
source promotion.

## Current Section Types

The current registry includes general product sections, richer proof and
action sections, mobile-specific sections, and legal content. Examples
include:

- hero and call-to-action sections;
- provider or configured-agent strips;
- feature grids and matrices;
- ordered getting-started workflows;
- action guides;
- feature/code showcases;
- static screenshot-led product overviews;
- screenshot galleries;
- prompt and code examples;
- mobile hero, feature, connection, and download sections;
- legal content.

Section type names are implementation details. Public content should use the
plain-language purpose of a section rather than explain its YAML or component
identity.

## Markdown

Markdown sources are loaded through the content helpers and transformed into
section data where a section definition supports them. Use Markdown when
structured prose is easier to maintain outside YAML. Keep page layout and
section ordering in YAML.

## Public Files

Files under `public/` are copied into the built site and referenced from page
content with root-relative paths.

- Draft screenshots, browser captures, and generated previews belong under
  ignored `artifacts/`.
- Only approved, sanitized production files belong under `public/`.
- Missing production images must fail validation or be omitted from the public
  page. Planning placeholders must not be rendered as product proof.

Theme-aware screenshots use one rendered image element with `src` and
`srcDark` content fields. The active theme source is selected by the layout
theme script, and below-the-fold proof remains lazy-loaded. The maintained
programmatic asset catalog, source lifecycle, deterministic derivative
commands, and browser checks are documented in
[Visual Asset Processing Pipelines](../visual-assets.md).
Framework users should start with
[Using the Visual Asset Framework](../visual-asset-framework.md), while
framework maintainers should use
[Visual Asset Framework Architecture](visual-content-and-screenshot-generation.md).

## Adding a Page

The current pattern is:

1. Add the authored page content under `src/content/pages/`.
2. Add an Astro route under `src/pages/`.
3. Load and prepare the page through the shared content helpers.
4. Render its sections through `SectionRenderer`.
5. Add navigation and footer links when the route should be publicly
   discoverable.
6. Verify responsive, accessible, link, and production behavior.

## Adding a Section Type

When existing sections cannot represent approved content clearly:

1. Add or extend the TypeScript content type in `src/content/pageTypes.ts`.
2. Add a section definition under `src/sections/`.
3. Add a content-neutral Astro component under `src/components/`.
4. Register the section in `src/section-system/registry.ts`.
5. Add focused content preparation or component tests where practical.
6. Exercise the section through a real page.

Do not add a new section type merely to encode page-specific styling or copy
that belongs in content.

## Source Boundaries

- `src/content/` is current public content.
- `visual_assets/` contains the executable visual catalog and reviewed source
  masters used to reproduce optimized public derivatives.
- This development page documents the current authoring and rendering system.
- The product website content specification defines intended communication
  outcomes.
- Research pages preserve supporting knowledge and uncertainty.
- Package-owned product behavior remains authoritative in the package that
  implements it.
- Generated `dist/` output is not edited.

## Build and Preview

From `landing_page/`:

```bash
yarn build:production
yarn build:staging
yarn preview:production
yarn preview:staging
```

The builds write to `dist/production/` and `dist/staging/`. Staging includes a
visible preview marker, no-index/no-follow metadata, no production analytics,
and a disallowing `robots.txt`; production remains indexable.

The package README documents public URL variables and the combined
landing/documentation-site smoke path.

For substantive content-system changes, verify:

- every content document loads;
- every registered section renders;
- public assets resolve;
- desktop and mobile layouts remain usable;
- keyboard and semantic accessibility;
- navigation and footer links;
- visual-asset catalog and theme-source behavior when public screenshots
  change;
- the production build;
- the landing-to-documentation browser smoke flow when applicable.
