# Section Visual Guidance

This document describes reusable section primitives for the proposed rewrite.
Section components should be content-neutral. Page-specific copy, item labels,
media choices, code snippets, and explanatory text belong in YAML.

## `actionGuide`

For sections that combine explanatory text with a concrete sequence of actions.

Expected content fields:
- `eyebrow`
- `title`
- `body`
- `action.title`
- `action.steps[]`
- optional `note`
- optional `visual`

Desktop:
- Use a two-column layout.
- Put prose and notes in one column.
- Put ordered action cards, code blocks, and short UI steps in the other.
- If `visual` is present, render it as a supporting diagram or media panel.

Mobile:
- Stack title, body, action cards, and visual.
- Keep code blocks readable without horizontal page overflow.

## `featureMatrix`

For tabular comparisons whose columns and rows are fully defined by content.

Expected content fields:
- `eyebrow`
- `title`
- optional `intro`
- `columns[]` with `key` and `label`
- `rows[]` with values for those keys
- optional `visual`

Desktop:
- Render as a readable table or matrix.
- Keep columns exactly content-driven.
- Allow cells to contain short markdown-like inline formatting.

Mobile:
- Prefer row cards over a dense table.
- Each card should render the configured columns in order.

## `featureShowcase`

For a set of feature cards or media panels.

Expected content fields:
- `eyebrow`
- `title`
- `body`
- `items[]`
- optional item `media`

Desktop:
- Use cards, tabs, or a horizontal panel layout depending on item count and
  media density.
- Do not hardcode item labels, icons, or media assumptions in the component.

Mobile:
- Stack cards or use a horizontal carousel when media would dominate the page.

## `featureCodeShowcase`

For feature cards that include short code examples.

Expected content fields:
- `eyebrow`
- `title`
- `body`
- optional `note`
- `cards[]` with `title`, `description`, and optional `code`

Desktop:
- Use tabs or horizontally arranged cards.
- Code blocks should be visibly secondary to the card explanation unless the
  content marks the code as the primary artifact.

Mobile:
- Use stacked or horizontally scrollable cards.
- Provide expansion for longer code blocks.
- Preserve monospace rendering for all code.

## `screenshotGallery`

For sections where multiple screenshots or visual states explain one feature
cluster.

Expected content fields:
- `eyebrow`
- `title`
- `body`
- `gallery[]` with `title`, `description`, `src`, and `status`

Desktop:
- Use either a large active screenshot with selectable captions, or a horizontal
  gallery with clear captions.

Mobile:
- Use a horizontal screenshot carousel or stacked cards with image and caption.

## `promptBlock`

For copyable prompts with optional supporting snippets.

Expected content fields:
- `eyebrow`
- `title`
- `intro`
- `prompt`
- optional `configExample`

Desktop:
- Pair prose with a copyable prompt card.
- Show supporting snippets nearby but visually secondary.

Mobile:
- Stack prose, prompt, and supporting snippets.
- Add a visible copy action when implemented.

## `codeExample`

For sections where one code sample demonstrates a workflow.

Expected content fields:
- `eyebrow`
- `title`
- `body`
- `code.language`
- `code.value`
- optional `code.status`

Desktop:
- Pair explanatory copy with syntax-highlighted code.
- If `code.status` is present, render it as a small caveat or badge.

Mobile:
- Keep code readable and preserve monospace rendering.
- Use an expand affordance for long examples if needed.