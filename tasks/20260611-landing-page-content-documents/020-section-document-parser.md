# Section Document Parser

Implement the future-facing page document compiler: a readable Markdown-like source file with multiple typed sections, optional per-section YAML metadata, validation, and normalized section data for Astro renderers.

## Requirements checklist

- [ ] Work in `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291` on branch `pr-10-cl-291`.
- [ ] Build on the YAML content baseline from `tasks/20260611-landing-page-content-documents/010-simple-yaml-page-content.md`.
- [ ] Add a central parser/compiler for section page documents.
- [ ] Keep `type` required for every section in this version.
- [ ] Add section-specific validation with useful build-time error messages.
- [ ] Normalize parsed documents into the same renderer-facing structure used by the Astro section components.
- [ ] Preserve current visible content, section order, and rendered page structure when migrating page content.
- [ ] Add parser tests or equivalent build-time fixture tests.
- [ ] Run `npm run build` in `landing_page`.

Parent Task: `tasks/20260611-landing-page-content-documents/000-main.md`
Depends On: `tasks/20260611-landing-page-content-documents/010-simple-yaml-page-content.md`

## Goal

Introduce the final architecture for page content without changing the current page story. The source format should be readable as one page document, while Astro components should continue to receive structured section data.

This version should not infer section types. Future work may promote validation rules into duck typing. For this task, every section must explicitly declare `type`.

## Proposed Source Format

Use one document per page, for example:

```text
landing_page/src/content/pages/home.page.md
landing_page/src/content/pages/mobile.page.md
landing_page/src/content/pages/privacy.page.md
landing_page/src/content/pages/terms.page.md
```

Recommended section marker:

````md
--- page
title: Crystal Lattice
description: Model-native agents, reachable from anywhere.
---

--- section
type: hero
id: hero
eyebrow: Local-first agent platform
actions:
  - label: Install CLI
    href: "#install"
    variant: primary
---

# Model-native agents, reachable from anywhere.

Crystal Lattice runs agent sessions locally, exposes them through HTTP,
desktop, mobile, and terminal clients, and lets each model family use the
harness it was optimized for.

```bash
curl -fsSL https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh | bash
```

--- section
type: pluginPrompt
id: plugins
eyebrow: Plugins
---

## Replace the harness without waiting for upstream

Providers, tools, features, application actions, and UI elements are plugins.

```text
I want to build a Crystal Lattice plugin.

Please inspect:
- plugins/docs/index.md
- plugins/docs/tool-plugins.md
- plugins/docs/application-plugins.md
- plugins/docs/ui-elements.md
```
````

The exact file extension and marker syntax may be adjusted if Astro/Vite integration makes another form simpler, but keep the concept: one page document containing page metadata and multiple explicitly typed sections.

## Parser Architecture

Create a central parser/compiler module plus self-contained section
definitions, for example:

```text
landing_page/src/content/sectionDocument.ts
landing_page/src/content/pageTypes.ts
landing_page/src/sections/hero.ts
landing_page/src/sections/steps.ts
landing_page/src/sections/pluginPrompt.ts
landing_page/src/section-system/registry.ts
landing_page/src/section-system/SectionRenderer.astro
landing_page/src/components/Hero.astro
landing_page/src/components/Quickstart.astro
landing_page/src/components/mobile/Hero.astro
```

Expected pipeline:

1. Read a page document.
2. Split into page metadata and section blocks.
3. Parse each section's YAML metadata.
4. Parse each section's Markdown body into a simple intermediate representation.
5. Dispatch to a section parser by `type` through a registry.
6. Validate required fields and required Markdown structure.
7. Return a normalized `PageDocument`.

The renderer should not consume raw Markdown sections directly. It should receive normalized data such as:

```ts
type PageDocument = {
  seo: {
    title: string;
    description?: string;
  };
  nav?: Array<{ label: string; href: string }>;
  sections: Section[];
};
```

Section types, section parsers, and Astro section templates must be extensible.
Do not put every section parser into one large switch/file. Keep Astro
presentation components in the current `landing_page/src/components/`
structure, put section-specific definition files as flat files under
`landing_page/src/sections/`, and put shared wiring such as registry and
generic renderer files in a separate directory outside `sections`, such as
`landing_page/src/section-system/`. A section definition owns:

- the public section `type`
- the parser for that section type
- the normalized TypeScript shape for the section data
- the Astro component that renders that normalized section

The central registry should be the only place that maps a `type` string to a
section definition. The central page compiler should orchestrate parsing and
validation, but section-specific extraction rules should live with the section
definition. Section definitions should be shareable across pages and live in
flat files such as `src/sections/hero.ts`, `src/sections/featureGrid.ts`, and
`src/sections/pluginPrompt.ts`. Do not create one directory per section type as
part of this task.

Suggested contract shape:

```ts
export type MarkdownBlock =
  | { kind: "heading"; depth: number; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "code"; language?: string; code: string }
  | { kind: "list"; items: string[] };

export type RawSection = {
  filePath: string;
  index: number;
  meta: Record<string, unknown>;
  blocks: MarkdownBlock[];
  rawMarkdown: string;
};

export type SectionParseContext = {
  fail(message: string): never;
  warn?(message: string): void;
};

export type SectionParser<TSection> = {
  type: string;
  parse(raw: RawSection, context: SectionParseContext): TSection;
};

export type SectionDefinition<TSection extends { type: string }> = {
  type: TSection["type"];
  parser: SectionParser<TSection>;
  Component: unknown; // use the Astro component type available in the project
};
```

Example section definition module:

```ts
// landing_page/src/sections/pluginPrompt.ts
import PluginPrompt from "../components/PluginPrompt.astro";
import type { SectionDefinition, SectionParser } from "../content/pageTypes";
import { firstCodeBlock, firstHeading, paragraphsBeforeFirstCode } from "./helpers";

export type PluginPromptSection = {
  type: "pluginPrompt";
  id: string;
  eyebrow?: string;
  title: string;
  body?: string;
  prompt: {
    language?: string;
    code: string;
  };
};

const parser: SectionParser<PluginPromptSection> = {
  type: "pluginPrompt",
  parse(raw, context) {
    const id = typeof raw.meta.id === "string" ? raw.meta.id : `section-${raw.index + 1}`;
    const title =
      typeof raw.meta.title === "string"
        ? raw.meta.title
        : firstHeading(raw.blocks, 2)?.text;
    if (!title) {
      context.fail("pluginPrompt requires a title or first level-2 heading");
    }

    const code =
      typeof raw.meta.prompt === "object" && raw.meta.prompt !== null
        ? raw.meta.prompt
        : firstCodeBlock(raw.blocks);
    if (!code || typeof code.code !== "string" || !code.code.trim()) {
      context.fail("pluginPrompt requires a prompt/code block");
    }

    return {
      type: "pluginPrompt",
      id,
      eyebrow: typeof raw.meta.eyebrow === "string" ? raw.meta.eyebrow : undefined,
      title,
      body:
        typeof raw.meta.body === "string"
          ? raw.meta.body
          : paragraphsBeforeFirstCode(raw.blocks),
      prompt: {
        language: "language" in code ? code.language : undefined,
        code: code.code,
      },
    };
  },
};

export const pluginPromptSection = {
  type: "pluginPrompt",
  parser,
  Component: PluginPrompt,
} satisfies SectionDefinition<PluginPromptSection>;
```

Example registry:

```ts
// landing_page/src/section-system/registry.ts
import { heroSection } from "../sections/hero";
import { stepsSection } from "../sections/steps";
import { pluginPromptSection } from "../sections/pluginPrompt";
import { mobileHeroSection } from "../sections/mobileHero";
import { mobileFeaturesSection } from "../sections/mobileFeatures";

export const sectionDefinitions = [
  heroSection,
  stepsSection,
  pluginPromptSection,
  mobileHeroSection,
  mobileFeaturesSection,
] as const;

export const sectionDefinitionByType = new Map(
  sectionDefinitions.map((definition) => [definition.type, definition]),
);
```

The generic Astro renderer should use the same definitions:

```astro
---
// landing_page/src/section-system/SectionRenderer.astro
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

This keeps parser and renderer wiring aligned: one section definition provides
both the parser and the Astro template for a section type.

## Section Parsing Rules For V1

Keep these deliberately simple. YAML metadata should override inferred Markdown fields where both exist.

Suggested rules:

- `hero`
  - `title`: YAML `title` or first `h1`
  - `body`: YAML `body` or paragraphs after the title and before the first code block
  - `command`: YAML `command` or first code block
  - requires a title

- `steps`
  - `title`: YAML `title` or first `h2`
  - `body`: YAML `body` or paragraphs after the first `h2` and before the first `h3`
  - each `h3` starts a step
  - first code block under a step becomes `step.code`
  - requires a title and at least one step

- `featureGrid`
  - `title`: YAML `title` or first `h2`
  - `body`: YAML `body` or intro paragraphs
  - items may come from YAML `items` in v1
  - optional future enhancement: each `h3` becomes a feature item
  - requires a title and at least one item

- `pluginPrompt`
  - `title`: YAML `title` or first `h2`
  - `body`: YAML `body` or paragraphs before first code block
  - `prompt`: YAML `prompt` or first code block
  - requires a title and a code block/prompt

- `codeFeature` or `sdkExample`
  - `title`: YAML `title` or first `h2`
  - `body`: YAML `body` or paragraphs before first code block
  - `code`: YAML `code` or first code block
  - requires a title and code block

Only implement section types needed to preserve the current pages plus any obvious common sections from subtask 010. Avoid speculative section types unless they are needed by current content.

## Validation Requirements

Build-time errors should identify:

- page file path
- section index
- section id if available
- section type if available
- missing/invalid field

Examples:

```text
home.page.md section #4 "plugins" (pluginPrompt) requires a code block.
home.page.md section #2 is missing required field "type".
```

Do not silently drop invalid sections.

## Astro Integration

The page should remain thin, for example:

```astro
---
import Layout from "../layouts/Layout.astro";
import Nav from "../components/Nav.astro";
import Footer from "../components/Footer.astro";
import SectionRenderer from "../section-system/SectionRenderer.astro";
import { loadPageDocument } from "../content/sectionDocument";

const page = await loadPageDocument("home");
---

<Layout title={page.seo.title} description={page.seo.description}>
  <Nav items={page.nav} />
  <main>
    <SectionRenderer sections={page.sections} />
  </main>
  <Footer />
</Layout>
```

Section components should continue to be ordinary Astro components with clean HTML placeholders. The parser should not leak rendering concerns into content extraction.

Keep section definitions, shared wiring, and components separate:

```text
landing_page/src/sections/hero.ts
landing_page/src/sections/mobileHero.ts
landing_page/src/section-system/registry.ts
landing_page/src/section-system/SectionRenderer.astro
landing_page/src/components/Hero.astro
landing_page/src/components/mobile/Hero.astro
```

Shared parser helpers can live in `landing_page/src/sections/helpers.ts` or
`landing_page/src/content/markdownBlocks.ts`, but keep section-specific logic in
the section definition module. Do not move existing Astro components into
per-section definition folders as part of this task, and do not mix registry or
renderer wiring into the `src/sections/` directory.

## Testing

Run:

```bash
cd /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291/landing_page
npm run build
```

Add parser tests if the site already has a test runner or if adding a lightweight one is reasonable. If no test runner exists and adding one is out of scope, add a small build-time fixture validation script invoked by `npm run build` or a new package script.

Required test/fixture coverage:

- a valid page document with page metadata and two sections parses successfully
- `hero` extracts title, body, and first code block
- `steps` extracts a section title and multiple `h3` steps
- `pluginPrompt` extracts the first code block as prompt
- missing `type` fails validation
- missing required code block for `pluginPrompt` fails validation
- unknown `type` fails validation

Recommended output-stability check:

- Build before and after migration and compare generated HTML for existing routes, ignoring non-semantic differences if necessary.
- Manually preview `/`, `/mobile/`, `/privacy/`, and `/terms/`.

## Completion Notes

Add notes here during completion: parser files added, page documents migrated, validation behavior, tests added/run, build result, and any rendered-output differences.
