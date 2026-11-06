# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-xhigh-s0 · glm max

- Run: `20261029T234522.856857Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-79ec8fc4`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `f6fe857a1d80cebb…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: 0 input · 0 cached · 0 output · provider cost $0.0000000

## Transcript

**User**

Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

# Eleventy author metadata migration decomposition

Partition a broad content/build migration by compatible working states rather than files and phases.

Category: decomposition

Measured structure facts (per file, per top-level section):

#### tasks/20261029-multi-author-post-metadata.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-multi-author-post-metadata.md — Requirements checklist | 105 | 0 | 0 | 5 | 12 | 0 | 0 | 0 | 0 |
| tasks/20261029-multi-author-post-metadata.md — Scope | 34 | 1 | 34 | 0 | 0 | 0 | 0 | 0 | 0 |
| tasks/20261029-multi-author-post-metadata.md — Open questions and decisions | 97 | 0 | 0 | 3 | 12 | 0 | 0 | 0 | 3 |
| tasks/20261029-multi-author-post-metadata.md — Research and supporting facts | 116 | 0 | 0 | 7 | 13 | 0 | 0 | 0 | 17 |
| tasks/20261029-multi-author-post-metadata.md — Execution plan | 514 | 2 | 78 | 19 | 13 | 6 | 0 | 0 | 1 |

The produced task files:

### tasks/20261029-multi-author-post-metadata.md

````markdown
# Migrate Post Author Metadata

Move post author metadata from the legacy scalar field to a structured form
that supports multiple authors, while preserving existing content and
generated output during the transition.

## Requirements checklist

- [ ] Represent each post's authors in a structured form that supports one or
  more authors.
- [ ] Migrate existing posts without losing or changing author names.
- [ ] Update the post layout, archive listings, feed, and post authoring helper
  to consume and produce the new form; show every post author in generated
  post and archive output and the feed.
- [ ] Keep mixed legacy and new-form content buildable during migration so
  existing content and generated pages continue to work.
- [ ] Do not reject the legacy form until source-content and generated-output
  evidence show that nothing still depends on it.

## Scope

One end-to-end task owns the schema transition, existing-content migration,
all affected consumers, and their production-path evidence. These changes
share one compatibility boundary and do not provide independently acceptable
sub-results that justify separate task files.

## Open questions and decisions

- **Design decision — front matter schema:** What exact collection and author
  object shape should posts use? Recommendation: `authors: [{ name: "..." }]`,
  with no additional fields unless required.
- **Design decision — feed representation:** How should multiple authors map
  to the existing feed's `<author>` element? Recommendation: emit one element
  per author while retaining the existing element and name representation
  for single-author posts.
- **Design decision — legacy policy:** Should the final state reject legacy
  `author` metadata after the required evidence, or retain compatibility?
  Recommendation: reject it only after both evidence checks pass; otherwise
  keep accepting it.

## Research and supporting facts

- `content/posts/first.md` and `content/posts/second.md` currently store one
  name each in the scalar `author` field.
- `_includes/layouts/post.njk` reads the scalar directly. The shared
  `_includes/postslist.njk` currently renders titles only and is used by the
  blog archive and tag pages.
- `content/feed.xml.njk` reads `post.data.author` directly into a singular
  `<author>` element.
- `scripts/new-post.js` emits scalar author front matter.
- `tests/author-output.test.js` currently contains only a comment; it does not
  assert generated output. `tests/archive-output.test.js` is present, but
  existing coverage does not establish multi-author behavior.
- `npm run build` invokes Eleventy and writes the production site to `_site`.
  The package test command is `npm test`.
- There is no `docs/index.md`; the maintained documentation entry point is
  `README.md`, and `docs/development/index.md` contains no authoring guidance.

## Execution plan

Status: Draft

### Design and compatibility

Treat author metadata as one canonical structured collection consumed by
templates, archives, and the feed. The authoring helper emits that canonical
form. During migration, accept legacy and canonical front matter through one
normalization boundary so individual templates do not duplicate compatibility
logic. Convert every existing post and verify its output before considering
legacy rejection. If rejection is approved, make it an explicit build-time
validation only after a complete content audit and production-output checks;
otherwise retain the compatibility path.

The archive currently omits author names, so include all authors in each
shared post-list entry; this covers the blog and tag archives. Preserve
single-author names and existing page/feed behavior while allowing the agreed
feed representation to encode every author. Exact front matter and feed
representations remain open decisions and must be resolved before
implementation.

### Ordered tasks

1. Resolve the author collection/object shape, feed representation, and
   whether legacy input will be rejected after evidence.
2. Add transitional normalization and update the authoring helper, post
   layout, archive listing, and feed to use the agreed structured model.
3. Migrate all current post front matter, preserving each existing name.
4. Add generated-output coverage using the real Eleventy production path for
   single- and multi-author post pages, blog and tag archives, and feed output.
   Also verify mixed legacy/new input while transitional compatibility is in
   place.
5. Audit all maintained post content and inspect asserted generated output.
   Only after both checks pass, enable legacy rejection if that policy was
   approved; otherwise keep the fallback.
6. Update the README with the supported authoring format and run the focused
   tests and production build.

### Implementation decisions and open questions

- The shared post-list template owns archive bylines because both the blog
  archive and tag pages use it.
- Transitional legacy handling belongs at one normalization boundary, not in
  each output template.
- Resolve the three design questions under “Open questions and decisions”
  before coding; changing the schema, feed contract, or legacy acceptance
  policy affects author-facing or generated-output behavior.

### Documentation

- Update `README.md` with the agreed front matter shape and authoring helper
  behavior. Do not document the target as currently supported until the
  implementation lands.

### Task checklist

- [ ] Agree the canonical author schema, feed representation, and legacy
  acceptance policy.
- [ ] Implement transitional normalization and update all author consumers.
- [ ] Migrate existing post metadata without changing names.
- [ ] Add real-build coverage for post pages, archives, feed, and mixed input.
- [ ] Audit source content and generated output before any legacy rejection.
- [ ] Document supported authoring and run tests plus the production build.

### Requirement verification

- Requirements 1–3: Run generated-output tests through Eleventy and inspect
  the built post pages, blog archive, tag pages, and feed; assert that every
  agreed author name appears in the expected output. Separately test that the
  authoring helper emits the agreed front matter.
- Requirement 4: Build representative legacy and new-form posts together
  through the production Eleventy path and assert both render correctly.
- Requirement 5: Before rejection, audit every maintained post source for the
  legacy key and run production-output assertions over migrated content. Do
  not enable rejection if either evidence check is incomplete.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261029-multi-author-post-metadata.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, third checkbox",
            "quote": "Update the post layout, archive listings, feed, and post authoring helper to consume and produce the new form; show every post author in generated post and archive output and the feed.",
            "why": "A semicolon fuses two distinct acceptance criteria (update four consumers; make every author visible in post, archive, and feed output) into a single checkbox, so the reader mentally splits one item into two — the only strain in an otherwise uniform, one-point-per-item list of five."
          }
        ]
      },
      "tasks/20261029-multi-author-post-metadata.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Scope, the single paragraph",
            "quote": "These changes share one compatibility boundary and do not provide independently acceptable sub-results that justify separate task files.",
            "why": "A 34-word paragraph that both states the scope (schema transition, migration, consumers, evidence) and justifies why it is not split; nothing here strains a reader."
          }
        ]
      },
      "tasks/20261029-multi-author-post-metadata.md — Open questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Open questions and decisions, all three items",
            "quote": "**Design decision — front matter schema:** What exact collection and author object shape should posts use? Recommendation: `authors: [{ name: \"...\" }]`",
            "why": "Three bold-labeled items each pair a question with a 'Recommendation:', which keeps the section scannable, but no item states whether its recommendation is adopted — the decided-vs-open status only becomes clear via a sentence buried in 'Execution plan'."
          }
        ]
      },
      "tasks/20261029-multi-author-post-metadata.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Research and supporting facts, fifth bullet",
            "quote": "`tests/author-output.test.js` currently contains only a comment; it does not assert generated output.",
            "why": "This bullet packs two files and two coverage gaps into one item, but every clause is short and anchored to a code span; the seven bullets stay individually scannable and each names its file up front."
          }
        ]
      },
      "tasks/20261029-multi-author-post-metadata.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Execution plan — Design and compatibility, first paragraph",
            "quote": "If rejection is approved, make it an explicit build-time validation only after a complete content audit and production-output checks; otherwise retain the compatibility path.",
            "why": "The migration's most load-bearing policy sits mid-paragraph as a doubly-conditional sentence, so the reader must re-read to unfold it; the surrounding 78-word paragraph mixes design, policy, and sequencing in prose while every sibling subsection uses scannable lists."
          },
          {
            "where": "Execution plan — Design and compatibility, second paragraph",
            "quote": "Preserve single-author names and existing page/feed behavior while allowing the agreed feed representation to encode every author.",
            "why": "Multiple constraints (single-author preservation, unchanged page/feed behavior, multi-author feed encoding) are compressed into one sentence, stacking on another dense sentence about open decisions; this prose is the section's strain point."
          },
          {
            "where": "Execution plan — Task checklist",
            "quote": "- [ ] Audit source content and generated output before any legacy rejection.",
            "why": "Six unchecked boxes paraphrase the six 'Ordered tasks' one-for-one in different wording, so the plan exists as two parallel lists the reader must diff to find any real difference; the list itself is short, but the duplication taxes anyone tracking plan status."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Execution plan, status line",
          "quote": "Status: Draft",
          "why": "Plan status is findable immediately under the 'Execution plan' heading, and the six named subsections (ordered tasks, decisions, documentation, checklist, verification) let a reader go straight to the thing they want."
        },
        {
          "where": "'Open questions and decisions' vs 'Execution plan — Design and compatibility'",
          "quote": "Exact front matter and feed representations remain open decisions and must be resolved before implementation.",
          "why": "What is actually still open cannot be determined from the questions section alone; the reader must combine its three recommendations with this sentence buried in plan prose to learn their status — structure points to both places but no single spot answers the question."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Execution plan — Design and compatibility, first paragraph",
        "quote": "If rejection is approved, make it an explicit build-time validation only after a complete content audit and production-output checks; otherwise retain the compatibility path.",
        "why": "Load-bearing policy delivered as dense nested conditional prose rather than a stated rule with its gate conditions listed."
      },
      {
        "where": "Legacy-rejection policy, stated in Requirements checklist item 5, Open questions item 3, Design and compatibility, Ordered task 5, Task checklist item 5, and Requirement verification item 5",
        "quote": "Do not reject the legacy form until source-content and generated-output evidence show that nothing still depends on it.",
        "why": "The same evidence-gated rejection policy is restated six times in varying wording; the reader must reconcile the variants, and future edits can let them drift apart."
      },
      {
        "where": "Execution plan — Task checklist vs Ordered tasks",
        "quote": "- [ ] Add real-build coverage for post pages, archives, feed, and mixed input.",
        "why": "An unchecked-box list duplicating the numbered plan nearly 1:1 in paraphrase gives the plan two parallel representations; diffing them is work the reader did not need, and it invites inconsistent status updates."
      },
      {
        "where": "Execution plan — Implementation decisions and open questions",
        "quote": "Resolve the three design questions under “Open questions and decisions” before coding",
        "why": "The heading promises open questions, but the bullets contain only decisions plus a pointer — the questions themselves live in another section, so the heading overstates its content."
      },
      {
        "where": "Requirements checklist, third checkbox",
        "quote": "Update the post layout, archive listings, feed, and post authoring helper to consume and produce the new form; show every post author in generated post and archive output and the feed.",
        "why": "One checkbox mixes a consumer-update requirement with an output-visibility requirement, hiding two acceptance criteria behind a single tick."
      },
      {
        "where": "Execution plan — Requirement verification, first bullet",
        "quote": "Requirements 1–3: Run generated-output tests through Eleventy and inspect the built post pages, blog archive, tag pages, and feed; assert that every agreed author name appears in the expected output. Separately test that the authoring helper emits the agreed front matter.",
        "why": "Three requirements plus an additional helper check share one bullet; the 'Requirements 1–3' label mitigates but the reader still unpacks four assertions from a single item."
      }
    ],
    "summary": "A compact, well-partitioned file: four of the five sections are short and list-shaped (a five-item checklist, a 34-word scope paragraph, three labeled decision items, seven file-anchored fact bullets) and read with little effort. All strain concentrates in 'Execution plan': its two 'Design and compatibility' paragraphs carry the migration's load-bearing policy as dense conditional prose, the legacy-rejection rule is restated in six places with differing wording, and a 'Task checklist' paraphrases 'Ordered tasks' almost one-for-one, giving the plan two parallel representations to keep in sync. Navigation is strong — headings map directly onto outcome, constraints, questions, and status ('Status: Draft') — with one caveat: whether the three design recommendations are actually decided or still open can only be assembled by cross-referencing the questions section against a sentence buried in the plan."
  }
}
```
