# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-max-s0 · glm max

- Run: `20261102T111508.912170Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-max-s0-98d47f7b`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `99e781b58a30e4c9…`)
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

#### tasks/20261101-post-author-metadata-migration.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261101-post-author-metadata-migration.md — Requirements checklist | 62 | 0 | 0 | 4 | 17 | 0 | 0 | 0 | 0 |
| tasks/20261101-post-author-metadata-migration.md — Questions and decisions | 119 | 0 | 0 | 3 | 44 | 0 | 0 | 0 | 2 |
| tasks/20261101-post-author-metadata-migration.md — Supporting details | 94 | 0 | 0 | 7 | 17 | 0 | 0 | 0 | 17 |
| tasks/20261101-post-author-metadata-migration.md — Implementation plan | 556 | 6 | 91 | 9 | 46 | 5 | 0 | 0 | 6 |

The produced task files:

### tasks/20261101-post-author-metadata-migration.md

````markdown
# Migrate Post Author Metadata

Safely move post author metadata from one legacy name to a structured form that supports multiple authors, preserving generated output during transition.

## Requirements checklist

- [ ] Posts support the approved structured multi-author metadata form.
- [ ] Existing post metadata is migrated without losing author names.
- [ ] Templates, archives, feeds, and post-authoring tools consume the new form while preserving intended generated author information.
- [ ] Legacy metadata is rejected only after repository content and production-generated output provide evidence that no dependency remains.

## Questions and decisions

- **Question — schema:** What is the structured author contract (for example, an ordered `authors` array of objects containing `name`, with any additional identity fields)? Recommendation: use an ordered array so multiple authors and their display order are explicit; settle object fields before implementation.
- **Question — output:** Should the public post byline and feed expose names only, or should the schema’s additional identity fields appear in generated output? Existing output uses a name on post pages and feed entries.
- **Decision needed — transition behavior:** Preserve legacy input as a compatibility fallback while migrating consumers, then reject it only after source and production-output checks pass. Confirm the intended enforcement boundary for rejection (authoring tool/schema validation versus build-time validation).

## Supporting details

- **Fact:** `content/posts/first.md` and `content/posts/second.md` currently provide one `author` string each.
- **Fact:** `_includes/layouts/post.njk` renders the `author` value; `content/feed.xml.njk` emits it in feed entries.
- **Fact:** `content/blog.njk` and `content/index.njk` share `_includes/postslist.njk`; that list currently renders titles and links, not author names.
- **Fact:** `scripts/new-post.js` generates front matter with a single `author` string.
- **Fact:** `tests/author-output.test.js` and `tests/archive-output.test.js` currently contain comments only; neither provides generated-output assertions.
- **Fact:** The production build is `npm run build`, and tests run through `npm test`.
- **Fact:** `README.md` is the only root-level user-facing project guide; there is no `docs/index.md`.

## Implementation plan

Status: Draft

Keep the migration as one end-to-end task: the metadata contract is shared by content, Eleventy templates, the feed, and the post-creation helper, so splitting these into independently executable children would permit incompatible intermediate states. The content moves to the approved structured contract, while templates and the feed adapt to that contract and the authoring helper generates it. During the transition, preserve legacy reads so old content can still build; only tighten validation after all source posts use the new form and a real production build demonstrates the intended generated author data.

Generated pages and feeds are the decisive compatibility boundary. Add build-backed assertions covering post bylines and feed entries, and check archive/index output for preservation of existing archive behavior and any approved author display. Inspect every generated output for stale/missing legacy author data before enabling rejection. Do not infer archive byline requirements: current archive lists show titles only, so archive author display depends on the schema/output decision above.

Sequence the work so the contract is decided first, then migration and consumer changes land together with build-backed regression coverage, and legacy rejection is last. This order avoids breaking production builds midway through content migration and makes the removal gate evidence-based. The blast radius is limited to post metadata, generated author rendering, feed entries, and authoring output. The way back is to restore the legacy compatibility read and revert the content migration together; do not reject legacy input before rollback is no longer needed.

### Implementation decisions and open questions

Resolve the author object fields, the public rendering of those fields, archive author display expectations, and the legacy-rejection enforcement boundary before execution. Keep authors ordered and support multiple entries; avoid adding identity fields or public output not approved by the user.

### Documentation

Update `README.md` only if its authoring guidance is expanded or the supported content contract changes what authors must do. Keep migration-only/internal transition details in this task rather than introducing a standalone documentation page.

### Task checklist

- [ ] Agree the structured author contract and output behavior.
- [ ] Add or update production-build coverage for post, archive, and feed output.
- [ ] Migrate existing posts and update templates and authoring output.
- [ ] Build and inspect generated author output for legacy dependencies.
- [ ] Reject legacy metadata after the evidence gate passes.
- [ ] Update maintained authoring guidance if applicable.

### Requirement verification

- Structured metadata and migrated content: inspect all post front matter and run the production build with build-backed checks confirming each author name is retained and multiple author entries render in approved order. This does not establish authoring-tool ergonomics by itself.
- Templates, archives, feeds, and authoring tools: invoke `scripts/new-post.js` in its focused test and run `npm run build`; assert post bylines and feed authors, and verify archive/index output against the approved display contract. This does not cover external consumers of the feed.
- Legacy rejection gate: with legacy compatibility still available, inspect repository post front matter and built `_site` output for legacy-only reads or missing author data; only then run the gated build validation that rejects legacy input. This deliberately does not claim compatibility with untracked external content.

### Additional implementation verification

Run `npm test` and `npm run build` after the focused checks. If a realistic legacy fixture is needed to verify the compatibility interval, keep it test-scoped and ensure the final rejection check separately demonstrates the configured failure for legacy metadata.
````


**Assistant** *(reasoning present)*

{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261101-post-author-metadata-migration.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "checklist item 3 (longest item)",
            "quote": "Templates, archives, feeds, and post-authoring tools consume the new form while preserving intended generated author information.",
            "why": "Even the longest item (17 words) is a single requirement in one sentence; all four boxes state one requirement each and scan in a single pass."
          }
        ]
      },
      "tasks/20261101-post-author-metadata-migration.md — Questions and decisions": {
        "grade": "partial",
        "findings": [
          {
            "where": "schema bullet",
            "quote": "What is the structured author contract (for example, an ordered `authors` array of objects containing `name`, with any additional identity fields)? Recommendation: use an ordered array so multiple authors and their display order are explicit; settle object fields before implementation.",
            "why": "One 44-word bullet packs the question, an inline worked example, a recommendation, and a sequencing instruction; the reader must separate these moves to extract what is actually open."
          },
          {
            "where": "transition-behavior bullet",
            "quote": "Preserve legacy input as a compatibility fallback while migrating consumers, then reject it only after source and production-output checks pass. Confirm the intended enforcement boundary for rejection (authoring tool/schema validation versus build-time validation).",
            "why": "A 44-word item folding a decision, its evidence gate, and a newly raised sub-question into one bullet; the bold label helps scanning but the item needs a second read to hold all three parts."
          }
        ]
      },
      "tasks/20261101-post-author-metadata-migration.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "whole section",
            "quote": "- **Fact:** `scripts/new-post.js` generates front matter with a single `author` string.",
            "why": "One fact per line, none over 17 words, with 17 code spans keeping every path and identifier unambiguous; seven items scan in seconds and no item mixes unrelated facts."
          }
        ]
      },
      "tasks/20261101-post-author-metadata-migration.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "opening paragraph",
            "quote": "Keep the migration as one end-to-end task: the metadata contract is shared by content, Eleventy templates, the feed, and the post-creation helper, so splitting these into independently executable children would permit incompatible intermediate states.",
            "why": "The longest paragraph (91 words) is three sentences each carrying one point (why one task, what moves where, the transition rule); dense prose but parseable in one read, not a wall."
          },
          {
            "where": "Requirement verification items",
            "quote": "This does not establish authoring-tool ergonomics by itself.",
            "why": "The three ~46-word bullets each mix requirement, verification method, and explicit limitation, but follow a consistent 'requirement: method. limitation.' shape, so items two and three are read against a learned pattern."
          },
          {
            "where": "Task checklist",
            "quote": "- [ ] Reject legacy metadata after the evidence gate passes.",
            "why": "Six unchecked boxes are short single-action items and the 'Status: Draft' line above explains why none are checked; this is not a wall of stale boxes."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "section order and status line",
          "quote": "Status: Draft",
          "why": "Sections run requirements → open questions → supporting facts → plan, and the plan opens with an explicit status line, so outcome, constraints, and plan state are each locatable from structure alone."
        },
        {
          "where": "open questions split across two locations",
          "quote": "### Implementation decisions and open questions",
          "why": "Open items live in two places with non-identical sets: the top 'Questions and decisions' lists schema/output/transition behavior, while this plan subsection lists object fields, public rendering, archive display, and the enforcement boundary; a reader cannot tell which list is authoritative without reading both."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Questions and decisions — schema bullet",
        "quote": "Recommendation: use an ordered array so multiple authors and their display order are explicit; settle object fields before implementation.",
        "why": "A recommendation and a deadline are appended inside a bullet labeled as a question, so one list item carries several distinct facts."
      },
      {
        "where": "cross-section (Requirements checklist, plan paragraphs 1–3, Task checklist, Requirement verification)",
        "quote": "Legacy metadata is rejected only after repository content and production-generated output provide evidence that no dependency remains. / only tighten validation after all source posts use the new form and a real production build demonstrates the intended generated author data",
        "why": "The central rejection gate is restated at least four times with shifting wording ('provide evidence that no dependency remains' vs 'all source posts use the new form and a real production build demonstrates…'), forcing the reader to reconcile whether these are one gate or several stacked conditions."
      },
      {
        "where": "Implementation plan, second paragraph",
        "quote": "Do not infer archive byline requirements: current archive lists show titles only, so archive author display depends on the schema/output decision above.",
        "why": "A load-bearing dependency — archive display is undecided and gates output work — is buried as the fourth sentence of a plan paragraph instead of sitting with the other open questions."
      }
    ],
    "summary": "A compact single-file task whose Requirements checklist and Supporting details are exemplary: one requirement or fact per short line with heavy code-span use for paths. The Questions and decisions section strains because both of its 44-word bullets fold a question or decision, an example or gate, a recommendation, and timing into single labeled items. The 556-word Implementation plan stays usable through five subsections, three-sentence paragraphs, and a consistent verification pattern, though it restates the legacy-rejection gate across most of the file with drifting wording. Navigation is sound overall — status, constraints, and plan are each findable — but open questions are split between two differently scoped lists that the reader must reconcile."
  }
}
