# Simple YAML Page Content Baseline

Move existing Astro landing page content into simple page-level YAML files while preserving the current rendered site structure, copy, and section order.

## Requirements checklist

- [ ] Work in `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291` on branch `pr-10-cl-291`.
- [ ] Add simple YAML content files for each existing landing page.
- [ ] Refactor existing pages/components to receive content from YAML instead of owning hardcoded copy.
- [ ] Introduce or prepare the section-definition/component registry shape that subtask 020 will extend with parsers.
- [ ] Preserve current visible content, section order, and rendered page structure.
- [ ] Keep Astro component HTML readable, with clear placeholders such as `{section.title}`, `{item.body}`, and `{step.code}`.
- [ ] Run `npm run build` in `landing_page`.
- [ ] Note any unavoidable rendered markup differences in completion notes.

Parent Task: `tasks/20260611-landing-page-content-documents/000-main.md`

## Background

The current site is an Astro app under:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291/landing_page
```

Current page entry points:

```text
landing_page/src/pages/index.astro
landing_page/src/pages/mobile.astro
landing_page/src/pages/privacy.astro
landing_page/src/pages/terms.astro
```

Current content-heavy components:

```text
landing_page/src/components/Hero.astro
landing_page/src/components/Providers.astro
landing_page/src/components/Features.astro
landing_page/src/components/Quickstart.astro
landing_page/src/components/CTA.astro
landing_page/src/components/mobile/Hero.astro
landing_page/src/components/mobile/Features.astro
landing_page/src/components/mobile/Connect.astro
landing_page/src/components/mobile/Download.astro
```

At the time this task was created, `index.astro` hardcoded the section order by importing and rendering `Hero`, `Providers`, `Features`, `Quickstart`, and `CTA`. `mobile.astro` similarly rendered mobile-specific section components. The content inside those section components was hardcoded in each `.astro` file.

## Implementation Guidance

Create a simple YAML baseline before introducing a custom Markdown parser. Suggested files:

```text
landing_page/src/content/pages/home.yaml
landing_page/src/content/pages/mobile.yaml
landing_page/src/content/pages/privacy.yaml
landing_page/src/content/pages/terms.yaml
```

If legal pages are too prose-heavy to move cleanly in this first pass, document the reason and at least create content files for `home` and `mobile`; however, prefer covering all existing public pages so the architecture is consistent from the start.

Use a top-level shape that can evolve toward the later section parser:

```yaml
seo:
  title: "..."
  description: "..."

nav:
  - label: "..."
    href: "..."

sections:
  - type: hero
    id: hero
    eyebrow: "..."
    title: "..."
    body: "..."
    actions:
      - label: "..."
        href: "..."
        variant: primary
    command:
      language: bash
      code: |
        ...

  - type: featureGrid
    id: features
    eyebrow: "..."
    title: "..."
    body: "..."
    items:
      - icon: lock
        title: "..."
        body: "..."
```

Do not attempt to invent the future parser in this subtask. The aim is simply to centralize the current content and prove the renderer can consume structured page data.

However, do prepare the renderer-side architecture for the parser subtask. Keep
the Astro presentation components in the current `landing_page/src/components/`
structure. Put section-specific definition files in `landing_page/src/sections/`
as flat files such as `hero.ts`, `features.ts`, and `mobileHero.ts`. Put shared
wiring such as the registry and generic `SectionRenderer.astro` in a separate
directory outside `sections`, such as `landing_page/src/section-system/`.

The recommended v1 shape is:

```text
landing_page/src/sections/hero.ts
landing_page/src/sections/features.ts
landing_page/src/sections/mobileHero.ts
landing_page/src/section-system/registry.ts
landing_page/src/section-system/SectionRenderer.astro
landing_page/src/components/Hero.astro
landing_page/src/components/Features.astro
landing_page/src/components/mobile/Hero.astro
landing_page/src/components/mobile/Features.astro
```

In this subtask, a section definition may only need `type` and `Component`.
Subtask 020 will extend the same definition shape with a parser. Section
definitions should live as flat, shareable files under `src/sections/`; for
example, both home and mobile pages can reuse a generic `featureGrid.ts`
definition if the normalized section shape matches.

Example renderer-side definition for this subtask:

```ts
// landing_page/src/sections/features.ts
import Features from "../components/Features.astro";

export const featuresSection = {
  type: "features",
  Component: Features,
} as const;
```

Example registry:

```ts
// landing_page/src/section-system/registry.ts
import { heroSection } from "../sections/hero";
import { featuresSection } from "../sections/features";

export const sectionDefinitions = [
  heroSection,
  featuresSection,
] as const;

export const sectionDefinitionByType = new Map(
  sectionDefinitions.map((definition) => [definition.type, definition]),
);
```

Example generic renderer:

```astro
---
import { sectionDefinitionByType } from "./registry";

const { sections } = Astro.props;
---

{sections.map((section) => {
  const definition = sectionDefinitionByType.get(section.type);
  if (!definition) {
    throw new Error(`No section component registered for type "${section.type}"`);
  }
  const Component = definition.Component;
  return <Component section={section} />;
})}
```

This keeps the rendering architecture aligned with the later parser/compiler
architecture while leaving section parsing out of scope for this first task.

## Component Refactor Expectations

Keep section components readable. The desired pattern is:

```astro
---
const { section } = Astro.props;
---

<section class="features" id={section.id}>
  <div class="container">
    <div class="header">
      <p class="label">{section.eyebrow}</p>
      <h2>{section.title}</h2>
      <p class="desc">{section.body}</p>
    </div>

    <div class="grid">
      {section.items.map((item) => (
        <div class="card">
          <div class="icon" data-icon={item.icon}></div>
          <h3>{item.title}</h3>
          <p>{item.body}</p>
        </div>
      ))}
    </div>
  </div>
</section>
```

For icons, prefer semantic keys in YAML rather than embedding SVG path markup in the content file. It is acceptable to keep an icon map in component code during this stage.

Adapt existing Astro components in place under `landing_page/src/components/`.
The new `landing_page/src/sections/` area should contain only section-specific
definition files. The shared registry and generic renderer should live outside
`sections` in a dedicated wiring/runtime directory such as
`landing_page/src/section-system/`. This preserves the current component
structure while making the data-driven section system explicit.

## Preservation Requirement

This subtask is not a copywriting pass. Preserve the exact current text unless small formatting changes are required by YAML representation. Preserve:

- current page order
- current section order
- current headings and body copy
- current command snippets
- current calls to action
- current legal page content

## Testing

Run:

```bash
cd /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291/landing_page
npm run build
```

Recommended additional checks:

- Compare `dist/index.html`, `dist/mobile/index.html`, `dist/privacy/index.html`, and `dist/terms/index.html` before and after, ignoring expected build hashes/formatting if any.
- Manually inspect the rendered home and mobile pages in `npm run dev` or `npm run preview`.
- If a YAML loader or validation library is added, ensure it is included in `landing_page/package.json` and covered by the build.

## Completion Notes

Add notes here during completion: what content files were added, which components were refactored, build result, and any rendered-output differences.

## Execution plan

Added during completion planning after user approval.

1. Inspect the current Astro source and capture the existing route-to-section map:
   `/` renders `Hero`, `Providers`, `Features`, `Quickstart`, and `CTA`; `/mobile` renders mobile `Hero`, `Features`, `Connect`, and `Download`; `/privacy` and `/terms` render legal prose pages.
2. Add YAML content documents under `landing_page/src/content/pages/` for the current pages, preserving the current copy, headings, commands, CTA labels, and section order.
3. Add the renderer-side section architecture without moving Astro templates:
   section-specific definitions as flat files under `landing_page/src/sections/`, and shared wiring under `landing_page/src/section-system/` with `registry.ts` and `SectionRenderer.astro`.
4. Refactor existing Astro section components in place under `landing_page/src/components/` to accept `section` props while keeping their markup, styles, and class names stable.
5. Update page entry points to load their page YAML and render `page.sections` through the generic section renderer. Use the least disruptive approach for legal pages while centralizing their text.
6. Run `npm run build` in `landing_page`.
7. Inspect generated routes for `/`, `/mobile/`, `/privacy/`, and `/terms/`, and note any unavoidable non-semantic differences in completion notes.
