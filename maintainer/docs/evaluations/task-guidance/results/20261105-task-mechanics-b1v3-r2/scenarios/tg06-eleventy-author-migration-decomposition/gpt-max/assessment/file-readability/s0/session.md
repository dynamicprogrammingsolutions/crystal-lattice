# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-max-s0 · glm max

- Run: `20261029T234749.790648Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-max-s0-d6ce66fa`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `e82cf229c995b743…`)
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

#### tasks/20261029-structured-post-authors.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-structured-post-authors.md — Requirements checklist | 81 | 0 | 0 | 5 | 20 | 0 | 0 | 0 | 0 |
| tasks/20261029-structured-post-authors.md — Unresolved questions | 41 | 0 | 0 | 2 | 22 | 0 | 0 | 0 | 1 |
| tasks/20261029-structured-post-authors.md — Supporting details | 106 | 0 | 0 | 7 | 19 | 0 | 0 | 0 | 14 |
| tasks/20261029-structured-post-authors.md — Execution plan | 570 | 1 | 110 | 25 | 37 | 7 | 0 | 0 | 4 |

The produced task files:

### tasks/20261029-structured-post-authors.md

````markdown
# Migrate Posts to Structured Authors

Replace the single-name post author field with a structured multi-author model while keeping existing content and generated pages working through the migration.

## Requirements checklist

- [ ] Posts support the approved structured representation of one or more authors.
- [ ] Existing posts and generated public pages remain compatible while content and consumers transition.
- [ ] Templates, archive output, feeds, and the new-post authoring tool consume the structured model.
- [ ] Existing post content is migrated without losing author information.
- [ ] The legacy author form is rejected only after generated-output and content evidence confirms no supported path still depends on it.

## Unresolved questions

- What exact structured author schema is required (for example, strings in an `authors` list versus objects with name and optional metadata)?
- What public output should represent multiple authors in post pages, archives, and feed entries, and in what order/format?

## Supporting details

- **Fact:** `content/posts/first.md` and `content/posts/second.md` currently use a single `author` string.
- **Fact:** `_includes/layouts/post.njk` renders `author`; `content/feed.xml.njk` emits `post.data.author`. The shared archive list currently renders titles only.
- **Fact:** `scripts/new-post.js` generates the legacy front matter.
- **Fact:** The test files are currently comment-only; `tests/author-output.test.js` describes generated-output coverage but contains no executable assertions.
- **Fact:** `package.json` provides `npm run build` and `npm test`; `eleventy.config.js` uses the production content tree and writes `_site`.
- **Constraint:** Keep migration evidence with this capability; test through the actual production build/output path, not only template mocks.
- **Assumption:** Preserve all names from existing content and avoid changing unrelated page content or URLs.

## Execution plan

Status: Draft

### Design

Treat this as one end-to-end migration because source front matter, authoring, templates, and generated output jointly define the author contract and do not have independent acceptance boundaries in this compact site. First settle the structured schema and public rendering contract. Then add temporary compatibility so legacy content and new structured content both produce correct pages while the content and authoring tool move. Migrate the existing posts, verify the rendered post pages, archive surfaces, and feed from a production build, and only then remove legacy handling and enforce the structured form. The legacy rejection gate must use both a content-tree check and generated-output evidence; a unit-level check alone is not sufficient.

### Ordered steps

1. Resolve and record the structured schema and output conventions before implementation.
2. Add dual-form handling to relevant templates and authoring paths so old and new content can coexist.
3. Migrate existing posts and update the new-post tool to emit the approved structured form.
4. Add production-build assertions for post pages, archive output where authors are displayed, and feed entries; verify both legacy and structured fixtures during the transition.
5. Inspect all supported content for legacy fields and generated output for remaining legacy-dependent results.
6. Remove legacy support and add a guard that rejects the old form only after those checks pass.
7. Run the focused author-output tests, full test suite, and production build; update maintained user/developer guidance for the supported format.

### Implementation decisions and open questions

- Schema and public author formatting are unresolved requirement questions above; do not encode a guessed schema or output contract before approval.
- Keep the transition tolerant until migrated-content and generated-output evidence supports the final rejection gate.
- Do not split authoring, content, templates, tests, or documentation into separate tasks: each only completes this shared migration.

### Documentation

- Update the maintained project guidance (likely `README.md`, subject to audience fit) to describe the approved current authoring format and transition completion.
- Do not publish target-only behavior as current guidance before implementation; if guidance is added earlier, mark it as not implemented.

### Task checklist

- [ ] Confirm structured schema and rendered author conventions.
- [ ] Implement and verify temporary compatibility.
- [ ] Migrate existing post front matter and authoring tool.
- [ ] Verify generated pages, archive surfaces, and feed through production build.
- [ ] Establish content and output evidence before rejecting legacy form.
- [ ] Remove legacy support, run checks, and update guidance.

### Requirement verification

- Structured author support and authoring tool: exercise the new-post generator and build generated posts using the approved structured form; verify rendered names and ordering in production output.
- Transition compatibility: build with both legacy and structured post fixtures and assert expected author output on post pages and feed before removing compatibility.
- Content migration: inspect every post under `content/posts` for retained legacy-only metadata and verify migrated names against rendered output.
- Archive behavior: assert author output in every archive surface where the approved design displays authors; the current shared archive list only shows titles, so preserve that behavior unless the resolved output contract says otherwise.
- Legacy rejection: run the production build and content scan after migration, then verify a legacy-only post is rejected by the supported validation path. The gate must not be enabled until the content and generated-output checks pass.

### Additional implementation verification

- Run `npm test` and `npm run build` after focused production-output assertions pass.
- Confirm generated output has no missing or malformed author fields and no unintended URL/content changes.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261029-structured-post-authors.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole section (5 checkbox items, 81 words, longest 20)",
            "quote": "- [ ] Posts support the approved structured representation of one or more authors.",
            "why": "Each item states a single requirement in under 21 words; the whole section fits in one glance and each box is independently checkable."
          },
          {
            "where": "Item 5",
            "quote": "The legacy author form is rejected only after generated-output and content evidence confirms no supported path still depends on it.",
            "why": "The longest item packs a condition and gate rule into one sentence, but it parses in one pass and is restated in the Execution plan, so nothing is lost."
          }
        ]
      },
      "tasks/20261029-structured-post-authors.md — Unresolved questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole section (2 items, 41 words)",
            "quote": "What exact structured author schema is required (for example, strings in an `authors` list versus objects with name and optional metadata)?",
            "why": "Two items, each a single self-contained question with a concrete example in a code span; the open decisions are immediately visible."
          }
        ]
      },
      "tasks/20261029-structured-post-authors.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Whole section (7 labeled items, longest 19 words)",
            "quote": "- **Fact:** `scripts/new-post.js` generates the legacy front matter.",
            "why": "The bold Fact/Constraint/Assumption labels plus code spans for file paths make each item scannable and verifiable against the repo."
          },
          {
            "where": "Item 2 (second Fact)",
            "quote": "`_includes/layouts/post.njk` renders `author`; `content/feed.xml.njk` emits `post.data.author`. The shared archive list currently renders titles only.",
            "why": "One item merges three independent consumer facts; the archive-titles-only clause is a load-bearing current-state fact that resurfaces in Requirement verification, yet sits as a trailing sentence here."
          }
        ]
      },
      "tasks/20261029-structured-post-authors.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Subsection Design",
            "quote": "Migrate the existing posts, verify the rendered post pages, archive surfaces, and feed from a production build, and only then remove legacy handling and enforce the structured form.",
            "why": "The entire design rationale, the four-phase sequence, and the rejection-gate evidence rule are compressed into one 110-word paragraph of long compound sentences; a first pass does not reliably hold the ordering, and the same sequence is already given scannably in Ordered steps."
          },
          {
            "where": "Subsection Requirement verification, item 'Archive behavior'",
            "quote": "Archive behavior: assert author output in every archive surface where the approved design displays authors; the current shared archive list only shows titles, so preserve that behavior unless the resolved output contract says otherwise.",
            "why": "A single ~40-word item mixes a verification instruction, a current-state fact, and a conditional decision rule; the reader must untangle which part is the action."
          },
          {
            "where": "Subsection Requirement verification, item 'Legacy rejection'",
            "quote": "Legacy rejection: run the production build and content scan after migration, then verify a legacy-only post is rejected by the supported validation path. The gate must not be enabled until the content and generated-output checks pass.",
            "why": "Two sentences chaining timing, method, and a blocking condition in one item; the gating rule is important enough that it deserves its own line rather than an item tail."
          },
          {
            "where": "Subsection Ordered steps, step 4",
            "quote": "Add production-build assertions for post pages, archive output where authors are displayed, and feed entries; verify both legacy and structured fixtures during the transition.",
            "why": "One step bundles three output targets plus fixture verification (37 words); each target is distinct work, though the semicolon split keeps it followable."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Heading structure (Requirements checklist / Unresolved questions / Supporting details / Execution plan with 7 named subsections)",
          "quote": "## Unresolved questions",
          "why": "Open questions, constraints, and the plan each live under a descriptive heading, so a reader can jump straight to the thing they want."
        },
        {
          "where": "Execution plan, first line",
          "quote": "Status: Draft",
          "why": "The plan status is findable in one hop from the Execution plan heading, though as a plain unlabeled line it carries no visual emphasis."
        },
        {
          "where": "Legacy-rejection gate statements",
          "quote": "The legacy author form is rejected only after generated-output and content evidence confirms no supported path still depends on it.",
          "why": "The key constraint appears in five places (checklist, Design, Implementation decisions, Task checklist, Requirement verification), so it cannot be missed — at the cost of repetition within one page."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Execution plan — Design",
        "quote": "Treat this as one end-to-end migration because source front matter, authoring, templates, and generated output jointly define the author contract and do not have independent acceptance boundaries in this compact site.",
        "why": "A 110-word single-paragraph prose wall carries rationale, sequencing, and the gate rule together; the sequencing content is duplicated in Ordered steps, so the paragraph could shrink to the rationale alone."
      },
      {
        "where": "Requirement verification — Archive behavior / Legacy rejection items",
        "quote": "the current shared archive list only shows titles, so preserve that behavior unless the resolved output contract says otherwise",
        "why": "Verification items interleave actions with current-state facts and conditional policy; separating the fact and the rule from the assertion instruction would make each item one thing to do."
      },
      {
        "where": "Supporting details — second Fact item",
        "quote": "The shared archive list currently renders titles only.",
        "why": "A load-bearing current-state fact (it conditions the Archive-behavior verification later) is buried as the tail sentence of a multi-fact list item instead of standing alone."
      }
    ],
    "summary": "A compact, well-signposted task file. The first three top-level sections are short labeled lists (5–7 items, ≤22 words each) that scan effortlessly; Unresolved questions isolates the open decisions and Supporting details grounds them in concrete file paths. The only strain is the Execution plan: its Design subsection compresses rationale, sequencing, and the rejection-gate rule into a 110-word paragraph, and two Requirement verification items (~40 words each) mix action, fact, and conditional policy in single bullets, while the migration sequence is repeated across Ordered steps, Task checklist, and Requirement verification. Navigation is direct — every kind of content (outcome, constraint, open question, status) sits under an explicit heading — so a maintainer can find and act on what matters with modest re-reading confined to the Design paragraph and the longest verification items."
  }
}
```
