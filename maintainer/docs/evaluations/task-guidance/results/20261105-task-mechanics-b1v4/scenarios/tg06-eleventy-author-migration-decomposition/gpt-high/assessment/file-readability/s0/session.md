# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-high-s0 · glm max

- Run: `20261102T110924.842080Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-high-s0-b713d350`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `6d6f107f5133fba0…`)
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

#### tasks/20261101-structured-post-authors.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261101-structured-post-authors.md — Requirements checklist | 93 | 0 | 0 | 5 | 21 | 0 | 0 | 0 | 0 |
| tasks/20261101-structured-post-authors.md — Questions and decisions | 80 | 0 | 0 | 2 | 44 | 0 | 0 | 0 | 0 |
| tasks/20261101-structured-post-authors.md — Supporting details | 115 | 0 | 0 | 6 | 24 | 0 | 0 | 0 | 12 |
| tasks/20261101-structured-post-authors.md — Implementation plan | 659 | 2 | 113 | 19 | 55 | 5 | 0 | 0 | 6 |

The produced task files:

### tasks/20261101-structured-post-authors.md

````markdown
# Structured post author migration

Move posts from one author-name string to structured multi-author metadata while keeping the production site and existing content working through a staged transition.

## Requirements checklist

- [ ] Posts use a structured author representation capable of identifying multiple authors.
- [ ] Existing post content and generated pages remain supported while content, templates, and authoring tools transition to the new representation.
- [ ] Post templates, archive output, feeds, and authoring tools consume the new author representation without losing existing author information.
- [ ] Existing posts are migrated without changing who is credited.
- [ ] The legacy single-name form is rejected only after repository content and production-generated output provide evidence that nothing still relies on it.

## Questions and decisions

- **Question — schema:** What is the exact structured author shape and required author fields? Recommendation: an ordered list of author records with a required display name; defer any identity, URL, or affiliation fields unless needed.
- **Question — archive presentation:** Should archive entries begin displaying author names, or should archives only be updated and checked for compatibility if they currently render author data? Existing post lists render titles only, so adding visible bylines would be a new user-facing behavior.

## Supporting details

- **Fact:** The Eleventy production build consumes Markdown under `content/posts/`, using `content/posts/posts.json` to apply the post layout and `posts` collection tag.
- **Fact:** Current post metadata is `author: "..."`; the post layout renders it, and the Atom feed copies it into each entry's `<author>` element.
- **Fact:** The shared post list powers the blog archive, home-page listing, and tag pages, but currently renders titles and URLs only.
- **Fact:** `scripts/new-post.js` generates the legacy single-name front matter. `tests/author-output.test.js` and `tests/archive-output.test.js` currently contain comments but no assertions.
- **Fact:** `npm run build` invokes Eleventy, and `npm test` runs Node's test runner over `tests/*.test.js`.
- **Fact:** No authoring guide exists; `README.md` is the only current user-facing site documentation.

## Implementation plan
Status: Draft

Treat this as one end-to-end content migration because the author schema is shared by Markdown, the post layout, the generated feed, the authoring helper, and the archive collection path. Keep a compatibility reader while both metadata forms exist; migrate the authored posts and the generator before making the new representation authoritative. The old form remains accepted during that overlap. After every consumer and source post uses the new form, verify the actual Eleventy build output and scan source content and templates for legacy dependencies. Only then add a rejection guard for legacy metadata and prove it through focused tests. The exact field shape and whether archive bylines become visible remain open until approved.

Execution order is intentional: establish output-level regression coverage and compatibility first; then update consumers and authoring; migrate source content; finally use build and repository evidence as the gate for rejecting the old form. This allows work to stop safely with both forms accepted if migration or generated-output checks expose a problem. The migration's blast radius is limited to post metadata and its presentation; rollback is to restore legacy content/consumer behavior while keeping the tests that reveal regressions.

### Implementation decisions and open questions

- Preserve author ordering and credited names through migration; do not infer identities or add author fields beyond the approved schema.
- Resolve the structured metadata contract before implementation. The recommendation is an ordered list of records with a required display name.
- Resolve whether archive entries gain bylines before implementation; do not silently change visible archive behavior.
- Transitional readers must tolerate both forms until the content and generated-output gate passes. Do not make rejection conditional on a test harness convenience.

### Documentation

- Update `README.md` with the supported author front matter and authoring guidance after the schema is approved and implemented.
- Keep documentation changes in the same implementation change as the behavior they describe; do not document target behavior as already supported during the transition.

### Task checklist

- [ ] Add meaningful generated-output tests that exercise a real Eleventy production build for post bylines and feed author elements, including multiple authors.
- [ ] Implement transitional reading/rendering for legacy and structured metadata across post pages, archive/collection surfaces, and feeds.
- [ ] Update the new-post authoring helper to generate only the approved structured form and test its generated front matter.
- [ ] Migrate all existing posts while preserving their credited names and author ordering.
- [ ] Build the site and inspect generated pages, archives, tags, and feed; scan repository content and consumer code for legacy-form use.
- [ ] Only after those checks pass, reject legacy metadata and add regression coverage for that rejection.
- [ ] Update maintained authoring documentation and run `npm test` and `npm run build`.

### Requirement verification

- **Structured author representation and authoring tools:** Test generated front matter from `scripts/new-post.js` against the approved schema. This does not by itself prove production rendering.
- **Transition compatibility and final post/feed output:** Build with Eleventy using representative legacy and structured posts during transition, then assert the rendered post page and Atom feed preserve each credited author. Do not use mocked template rendering as the decisive check.
- **Archive compatibility:** Assert actual generated blog, home, and tag archive outputs remain valid and render authors if visible archive bylines are approved. The current archive output has no bylines, so absent that approval this check proves no archive regression, not author display.
- **Safe content migration and legacy rejection gate:** Inspect every post's source front matter and assert production-generated output includes all migrated credits; scan the complete content/templates/tooling source for legacy-form dependencies before enabling the rejection test. The scan alone does not prove generated output, and the build alone does not prove no dormant source dependency remains.
- **Documentation:** Review the maintained authoring guidance against the implemented schema and generator behavior.

### Additional implementation verification

- Run `npm test` and `npm run build` after the focused migration checks to catch unrelated production-surface regressions; these checks do not replace the generated-output and source-content gate above.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261101-structured-post-authors.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Checklist item 3",
            "quote": "Post templates, archive output, feeds, and authoring tools consume the new author representation without losing existing author information.",
            "why": "One item carries four consumer surfaces plus a preservation condition, but at 21 words the measured longest item it stays within a single glance; the reader unpacks it without re-reading."
          }
        ]
      },
      "tasks/20261101-structured-post-authors.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Second bullet (the measured 44-word longest item)",
            "quote": "Should archive entries begin displaying author names, or should archives only be updated and checked for compatibility if they currently render author data? Existing post lists render titles only, so adding visible bylines would be a new user-facing behavior.",
            "why": "A single bullet mixes the question, a conditional alternative, and supporting evidence; at only two items and 80 total words the reader still holds it, but each bullet must be parsed sentence by sentence rather than scanned."
          }
        ]
      },
      "tasks/20261101-structured-post-authors.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fourth bullet",
            "quote": "`scripts/new-post.js` generates the legacy single-name front matter. `tests/author-output.test.js` and `tests/archive-output.test.js` currently contain comments but no assertions.",
            "why": "Two unrelated facts (the generator's output form and the tests' emptiness) share one bullet; a reader scanning for 'what do the tests cover' can skip past the second half."
          }
        ]
      },
      "tasks/20261101-structured-post-authors.md — Implementation plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Opening paragraph under 'Implementation plan' (the measured 113-word longest paragraph)",
            "quote": "Treat this as one end-to-end content migration... Only then add a rejection guard for legacy metadata and prove it through focused tests. The exact field shape and whether archive bylines become visible remain open until approved.",
            "why": "Six sentences of dense prose carry the sequencing strategy, the overlap policy, the rejection gate, and the open-question status; the reader must re-read to extract the order of operations, and the load-bearing 'open until approved' caveat is buried as the paragraph's last clause."
          },
          {
            "where": "Second paragraph under 'Implementation plan'",
            "quote": "Execution order is intentional: establish output-level regression coverage and compatibility first; then update consumers and authoring; migrate source content; finally use build and repository evidence as the gate for rejecting the old form.",
            "why": "Restates in prose the same execution order that the 'Task checklist' subsection then enumerates as seven items, so the reader meets identical sequencing twice in different shapes and must confirm they agree."
          },
          {
            "where": "'Requirement verification' subsection, 'Safe content migration and legacy rejection gate' item (the measured 55-word longest item)",
            "quote": "Inspect every post's source front matter and assert production-generated output includes all migrated credits; scan the complete content/templates/tooling source for legacy-form dependencies before enabling the rejection test. The scan alone does not prove generated output, and the build alone does not prove no dormant source dependency remains.",
            "why": "Each verification bullet packs the check, its method, and an evidentiary caveat into one run-on item; five such bullets at 40–55 words are held only with effort, straining the reader even though the bold lead-ins help."
          },
          {
            "where": "'Implementation decisions and open questions' subsection vs. top-level 'Questions and decisions'",
            "quote": "Resolve the structured metadata contract before implementation. The recommendation is an ordered list of records with a required display name.",
            "why": "The schema recommendation and the archive-byline question appear in both sections in slightly different wording; the reader must reconcile the duplicates to know which statement is current."
          }
        ]
      }
    },
    "navigation": {
      "grade": "partial",
      "findings": [
        {
          "where": "File structure: 'Questions and decisions', 'Implementation decisions and open questions', and the opening paragraph's final sentence",
          "quote": "The exact field shape and whether archive bylines become visible remain open until approved.",
          "why": "A reader looking for open questions finds them in three locations with no signal from the headings about which is authoritative."
        },
        {
          "where": "Rejection gate across 'Requirements checklist' item 5, opening paragraph, 'Implementation decisions' item 4, 'Task checklist' items 5–6, 'Requirement verification' item 4",
          "quote": "The legacy single-name form is rejected only after repository content and production-generated output provide evidence that nothing still relies on it.",
          "why": "The central constraint is stated in at least four places; it is easy to find but hard to pin to one authoritative wording, which is a structural cost rather than an aid."
        },
        {
          "where": "Line directly under the 'Implementation plan' heading",
          "quote": "Status: Draft",
          "why": "Plan status is present and near the top of the section, but as a bare unformatted text line it is easy to skim past; it is not a heading, badge, or labeled field."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Implementation plan, opening paragraph",
        "quote": "Treat this as one end-to-end content migration because the author schema is shared by Markdown, the post layout, the generated feed, the authoring helper, and the archive collection path. Keep a compatibility reader while both metadata forms exist; ...",
        "why": "Prose wall: a 113-word paragraph concentrates the migration's entire strategy, gate, and open status; converting the sequencing to a list would remove the re-reading burden."
      },
      {
        "where": "Implementation plan, second paragraph vs. 'Task checklist'",
        "quote": "Execution order is intentional: establish output-level regression coverage and compatibility first; then update consumers and authoring; migrate source content...",
        "why": "The same ordering appears twice — once as prose, once as seven checkboxes — inviting divergence and forcing the reader to diff the two versions."
      },
      {
        "where": "'Questions and decisions' heading",
        "quote": "## Questions and decisions",
        "why": "Heading/content mismatch: the section records questions and recommendations only; no decision is actually made anywhere in it, yet the heading promises decisions."
      },
      {
        "where": "'Task checklist' subsection",
        "quote": "- [ ] Only after those checks pass, reject legacy metadata and add regression coverage for that rejection.",
        "why": "Wall of seven unchecked boxes whose ordering dependencies live inside item prose ('Only after those checks pass') rather than in the list structure; the sequential nature is implicit and easy to misread as parallel work."
      },
      {
        "where": "'Requirement verification' subsection items",
        "quote": "**Archive compatibility:** Assert actual generated blog, home, and tag archive outputs remain valid and render authors if visible archive bylines are approved. The current archive output has no bylines, so absent that approval this check proves no archive regression, not author display.",
        "why": "Verification items embed conditional reasoning chains (what is proven if X is approved vs. not) inside single bullets, mixing the check definition with its interpretive caveat."
      },
      {
        "where": "Implementation plan, opening paragraph final sentence",
        "quote": "The exact field shape and whether archive bylines become visible remain open until approved.",
        "why": "Load-bearing status (the plan is blocked on two unresolved approvals) is buried as the last clause of the densest paragraph instead of being surfaced at the top or in the questions section it duplicates."
      }
    ],
    "summary": "The file's short sections are genuinely scannable: the 93-word requirements checklist and 115-word supporting-details list work as intended, and the two 80-word question bullets are parseable if dense. The weight sits in the 659-word Implementation plan, where two ~100+ word prose paragraphs carry the sequencing, overlap policy, rejection gate, and open status, followed by 19 list items across five subsections that restate much of that content — the execution order appears twice (prose and checklist), and the schema/byline open questions and the legacy-rejection gate each appear in three to five places. Nothing is unreadable; every part can be extracted with effort. The reader's cost is duplication and buried load-bearing clauses rather than absence: navigation is partial because structure alone cannot tell the reader which of the overlapping statements of the gate or the open questions is authoritative."
  }
}
```
