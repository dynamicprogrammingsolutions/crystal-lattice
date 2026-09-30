# Website Content System

This page describes the current `landing_page` implementation. It does not
define the intended product message; that target belongs to the
[product website content specification](specifications/product-website-content/index.md).

## Authored Sources

Current page content is authored under:

```text
src/content/pages/
```

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

The product-page hero owns its installation choices as one `install` object in
the page content. That object defines the default method, tab labels, exact
commands, platform support text, manual-download action, and documentation
routes. `InstallationChooser.astro` renders the accessible selector, while the
later first-success guide links back to it instead of maintaining another
installer command.

## Current Section Types

The current registry includes general product sections, richer proof and
action sections, mobile-specific sections, and legal content. Examples
include:

- hero and call-to-action sections;
- provider or configured-agent strips;
- feature grids and matrices;
- action guides;
- feature/code showcases;
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
yarn build
yarn preview
```

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
