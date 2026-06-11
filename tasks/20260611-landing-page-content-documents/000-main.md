# Landing Page Content Documents

Create a content-document architecture for the Astro landing page so page copy and section ordering can be edited from a small number of page-level files while preserving the current rendered website.

## Task checklist

- [ ] `tasks/20260611-landing-page-content-documents/010-simple-yaml-page-content.md`
- [ ] `tasks/20260611-landing-page-content-documents/020-section-document-parser.md`

## Context

The relevant website branch is checked out in a separate worktree:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291
branch: pr-10-cl-291
```

The site source is under `landing_page/`. Current source files inspected:

```text
landing_page/src/pages/index.astro
landing_page/src/pages/mobile.astro
landing_page/src/pages/privacy.astro
landing_page/src/pages/terms.astro
landing_page/src/components/Hero.astro
landing_page/src/components/Features.astro
landing_page/src/components/Providers.astro
landing_page/src/components/Quickstart.astro
landing_page/src/components/CTA.astro
landing_page/src/components/mobile/Hero.astro
landing_page/src/components/mobile/Features.astro
landing_page/src/components/mobile/Connect.astro
landing_page/src/components/mobile/Download.astro
```

The current page content is scattered across Astro components and page files. The goal is to make page content and ordering visible/editable from page-level content documents while keeping Astro components as clean renderers with placeholders.

Important product/content constraint: this task must use the existing page content. Do not rewrite the landing page message, reorder sections, redesign sections, or materially alter the rendered page structure as part of these implementation tasks. Content strategy changes will be handled separately.

## Desired Direction

Subtask 010 should establish a simple content-data baseline using YAML page files, one for each current page. This should remove hardcoded content from components/pages as much as practical while keeping the existing rendered HTML structure and ordering.

Subtask 020 should add the final-direction section document parser: one readable page document can contain multiple typed sections, each with optional YAML metadata and Markdown content. In this first implementation, `type` remains required. The parser should validate required section structure and normalize parsed sections into the same kind of data model used by the Astro renderers.

Future idea, not part of these subtasks: validation rules may later become sophisticated enough to infer section types by duck typing. For now, keep `type` explicit and required.

## Testing Expectations

Both subtasks should keep the existing page output stable unless a small markup difference is unavoidable and justified. Run the landing page build after each implementation stage:

```bash
cd /Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291/landing_page
npm run build
```

If practical, add automated tests for the parser introduced in subtask 020. At minimum, include fixture coverage for:

- splitting a page document into typed sections
- extracting titles/content/code blocks for supported section types
- rejecting a section with missing `type`
- rejecting a section missing required structure, such as a prompt section without a code block
