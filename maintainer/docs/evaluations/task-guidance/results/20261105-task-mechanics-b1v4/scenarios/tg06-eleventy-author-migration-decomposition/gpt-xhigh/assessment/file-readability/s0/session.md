# Session — tg06-eleventy-author-migration-decomposition · file-readability-assessment-gpt-xhigh-s0 · glm max

- Run: `20261102T111201.908121Z-task-guidance-file-readability-tg06-eleventy-author-migration-decomposition-gpt-xhigh-s0-6d0affe6`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `015b794fcc9295c1…`)
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

#### tasks/20261102-post-author-migration.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261102-post-author-migration.md — Requirements checklist | 87 | 0 | 0 | 4 | 23 | 0 | 0 | 0 | 1 |
| tasks/20261102-post-author-migration.md — Scope | 33 | 1 | 33 | 0 | 0 | 0 | 0 | 0 | 0 |
| tasks/20261102-post-author-migration.md — Questions and decisions | 163 | 0 | 0 | 4 | 45 | 0 | 0 | 0 | 3 |
| tasks/20261102-post-author-migration.md — Supporting details | 116 | 0 | 0 | 6 | 30 | 0 | 0 | 0 | 12 |
| tasks/20261102-post-author-migration.md — Implementation plan | 872 | 6 | 85 | 20 | 53 | 8 | 0 | 0 | 4 |

The produced task files:

### tasks/20261102-post-author-migration.md

````markdown
# Post Author Metadata Migration

Plan a compatibility-safe migration from the single `author` field to a structured form that supports multiple authors across post content and generated output.

## Requirements checklist

- [ ] Post metadata uses an agreed structured multi-author form, and the authoring tool emits that form.
- [ ] Post templates, archives, and feeds consume the new model and represent authors according to the approved rendering policy.
- [ ] Existing posts are migrated without losing their titles, bodies, or author names; legacy content remains buildable during the transition.
- [ ] Legacy `author` input is not rejected until generated-output and content evidence both show that repository content and output no longer depend on it.

## Scope

Keep this as one end-to-end task. The content schema, authoring tool, templates, archives, feed, and compatibility gate share one contract; separate tasks could leave a partially migrated site that cannot be accepted independently.

## Questions and decisions

- **Requirement question — metadata shape:** Should the canonical field be `authors: [{ name: "Ada Example" }]` or `authors: ["Ada Example"]`? Recommendation: use author objects, which make each author an explicitly structured record and leave room for later author attributes without changing the list shape.
- **Requirement question — archive output:** Should blog, tag, and home archive rows newly display every author, or should they remain title-only while being verified to work with the new metadata? Recommendation: display every author because archives are explicitly in scope.
- **Requirement question — legacy rejection:** After both evidence gates pass, should the build actively reject a legacy `author` field, or merely stop consuming it? Recommendation: reject it so future posts cannot silently regress to the old form.
- **Design decision:** Use a temporary compatibility normalization boundary so old and new post records can coexist while templates move to one canonical author list. Finalize the exact field and rendered markup only after the requirement questions are answered.

## Supporting details

- Two Markdown posts currently contain scalar `author` front matter; both use the same post layout.
- `scripts/new-post.js` emits scalar `author` front matter. No in-repository caller of its exported function was found.
- `_includes/layouts/post.njk` renders the scalar author. The feed emits it once per entry. `_includes/postslist.njk`, used by the blog, tag, and home views, currently renders titles only.
- `tests/author-output.test.js` and `tests/archive-output.test.js` contain comments but no assertions, so they do not currently verify generated output.
- `npm run build` invokes Eleventy and writes `_site`; `npm test` runs Node's test runner. The repository has no `docs/index.md` or authoring guide. `README.md` is the only package-level user documentation.
- The working tree was clean when this plan was drafted.

## Implementation plan

Status: Draft

### Design

Use a canonical plural author field in post front matter, with the precise value shape left open for the requirement decision above. While legacy posts may still exist, normalize both forms at one Eleventy boundary into a canonical iterable list; templates should not each implement their own legacy fallback. Update the post layout, shared listing template, and feed to consume that list. The authoring helper should emit only the approved new form. Convert existing post front matter while preserving all unrelated metadata and Markdown bodies.

During migration, keep the old field readable so mixed old/new content remains buildable. Add actual generated-output coverage for the post layout, archive paths, and feed, including a multi-author record processed by Eleventy with the project's templates. Add content checks over the repository's post front matter and record the evidence before removing compatibility or enabling rejection. The archive's visible author treatment and the final rejection behavior depend on the unresolved requirement decisions.

### Order and milestones

1. Resolve the metadata shape, archive rendering, and legacy rejection decisions. These define the persisted contract and visible output, so no content or template migration should precede them.
2. Add the shared compatibility normalization and move the post layout, archive listing, and feed to the canonical list. Keep old records accepted at this milestone; a build should still handle a mixed corpus.
3. Change the authoring helper to generate the new form and migrate the existing Markdown records, preserving titles, bodies, and names.
4. Add focused tests that exercise generated output through Eleventy and verify all migrated source front matter. Run a production build and inspect/assert post pages, archive output, and feed output before treating the evidence gate as passed.
5. Only after both generated-output and content checks pass, remove legacy handling and, if approved, add legacy-field rejection. Run the full build and tests again with that final policy active.
6. Update the README with the supported front-matter form and authoring contract once the schema and behavior are settled.

The safe stopping point after step 2 is a mixed-format build with old content still accepted. If migration or output checks fail, retain the compatibility path and correct the conversion or rendering before proceeding to the rejection gate.

### Risks and way back

- Front-matter conversion could lose a name or alter unrelated post content. Limit conversion to the author field and verify each migrated record's names, title, and body.
- Nunjucks escaping or multi-author formatting could change visible pages or produce incorrect feed XML. Assert real generated files for all affected output paths, including a multi-author case.
- Removing compatibility too early could break remaining or externally supplied legacy records. Make the source-content check and the generated-output check prerequisites to the removal; if either fails, keep or restore the compatibility boundary.
- The migration changes metadata only, not URLs or post bodies, so reverting the schema, templates, helper, and front matter together restores the prior behavior without data loss.

### Implementation decisions and open questions

The metadata shape, whether archive rows display authors, and whether legacy metadata is actively rejected remain unresolved requirement questions above. Execution must wait for those answers and approval of this plan. The compatibility boundary and staged order are the planned approach; adjust them only if the approved schema requires a different implementation.

### Documentation

Update `README.md` rather than create a new documentation structure. Document the final supported post-author front matter and the authoring helper's contract after the open schema and rendering decisions are resolved. Do not describe the temporary fallback as permanent supported authoring guidance.

### Task checklist

- [ ] Resolve the schema, archive-output, and legacy-rejection questions.
- [ ] Add shared compatibility handling and update every affected template.
- [ ] Update author generation and migrate all existing post metadata.
- [ ] Add generated-output and content evidence for the migration.
- [ ] Remove legacy support or enable rejection only after both evidence gates pass.
- [ ] Update the README and run final build and test checks.

### Requirement verification

- **Structured form and authoring output:** Test the helper's generated front matter and inspect every post's parsed front matter to confirm it uses the approved plural form; exercise a multi-author record through Eleventy to ensure the real templates receive multiple authors.
- **Templates, archives, and feed:** Run the production build and assert the generated post pages, blog/tag/home archive outputs, and feed contain the approved author representation without losing existing single-author names. If archives remain title-only by decision, verify their generated paths and contents still build correctly from posts carrying the new field.
- **Safe content migration and transition:** Check all post front matter for the new form and absence of legacy `author` keys, review that the conversion preserves post titles and bodies, and build a mixed legacy/new corpus before compatibility is removed. This does not establish that unknown external repositories have migrated.
- **Legacy rejection gate:** Require both the generated-output assertions and the complete post-content check to pass before enabling a legacy-field rejection rule. Verify the final production build and test suite with that rule active; if rejection is not approved, verify instead that old metadata is no longer consumed and document the retained policy.

### Additional implementation verification

Run `npm test` and `npm run build` after the final gate change. These are routine quality checks; they supplement but do not replace the generated-output and source-content evidence above.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg06-eleventy-author-migration-decomposition",
  "assessment": {
    "sections": {
      "tasks/20261102-post-author-migration.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fourth checklist item",
            "quote": "Legacy `author` input is not rejected until generated-output and content evidence both show that repository content and output no longer depend on it.",
            "why": "Densest item (23 words): a single sentence chains a negative condition onto two evidence sources, so it takes a beat to parse — but it remains one acceptance condition and does not require re-reading."
          }
        ]
      },
      "tasks/20261102-post-author-migration.md — Scope": {
        "grade": "readable",
        "findings": [
          {
            "where": "Scope paragraph",
            "quote": "The content schema, authoring tool, templates, archives, feed, and compatibility gate share one contract; separate tasks could leave a partially migrated site that cannot be accepted independently.",
            "why": "A six-item enumeration plus a semicolon-joined rationale in one sentence, but at 33 words for the entire section it is taken in with one breath and loses nothing."
          }
        ]
      },
      "tasks/20261102-post-author-migration.md — Questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "First bullet",
            "quote": "Should the canonical field be `authors: [{ name: \"Ada Example\" }]` or `authors: [\"Ada Example\"]`? Recommendation: use author objects, which make each author an explicitly structured record and leave room for later author attributes without changing the list shape.",
            "why": "Each of the four bullets packs two speech acts — the question and the recommendation — into one item of up to 45 words; the inline 'Recommendation:' label is the only separator, so a reader scanning for just the open questions must read past the answers."
          }
        ]
      },
      "tasks/20261102-post-author-migration.md — Supporting details": {
        "grade": "readable",
        "findings": [
          {
            "where": "Fifth bullet",
            "quote": "`npm run build` invokes Eleventy and writes `_site`; `npm test` runs Node's test runner. The repository has no `docs/index.md` or authoring guide. `README.md` is the only package-level user documentation.",
            "why": "One bullet mixes three unrelated facts (build/test commands, absent docs structure, README status), so a reader hunting a single fact must parse all three — though at 30 words the cost is small."
          }
        ]
      },
      "tasks/20261102-post-author-migration.md — Implementation plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Design, first paragraph",
            "quote": "While legacy posts may still exist, normalize both forms at one Eleventy boundary into a canonical iterable list; templates should not each implement their own legacy fallback.",
            "why": "The section's longest paragraph (85 words) carries five directives, and its load-bearing 'one normalization boundary' rule is embedded in a mid-paragraph semicolon clause; each sentence is a single move, so it stays parseable, but the constraint does not stand out."
          },
          {
            "where": "Requirement verification, third bullet",
            "quote": "Check all post front matter for the new form and absence of legacy `author` keys, review that the conversion preserves post titles and bodies, and build a mixed legacy/new corpus before compatibility is removed.",
            "why": "Verification bullets run to ~50 words chaining three actions before any sentence break; bold lead labels keep them navigable, but the action lists strain a single reading pass."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Implementation plan, first line",
          "quote": "Status: Draft",
          "why": "Plan status is present and sits directly under the Implementation plan heading, but it appears nowhere near the top of the file, so a reader scanning from the start must get roughly a third of the way in before learning the plan is a draft."
        },
        {
          "where": "Requirements checklist / Order and milestones / Task checklist",
          "quote": "- [ ] Add shared compatibility handling and update every affected template.",
          "why": "Remaining work is spread across three overlapping unchecked lists (4 requirements, 6 milestones, 6 tasks); each is findable by heading, but none is marked authoritative, so answering 'what is left' requires cross-checking three places."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Requirements checklist, Order and milestones, and Task checklist",
        "quote": "- [ ] Add shared compatibility handling and update every affected template.",
        "why": "The same work appears in three overlapping lists, all with unchecked boxes and none marked authoritative; redundancy makes the current status ambiguous and inflates the file a reader must reconcile."
      },
      {
        "where": "Implementation plan — Implementation decisions and open questions",
        "quote": "The metadata shape, whether archive rows display authors, and whether legacy metadata is actively rejected remain unresolved requirement questions above.",
        "why": "Heading/content mismatch: the heading promises decisions, but the subsection makes no new decisions — it restates the earlier Questions and decisions section and points back to it."
      },
      {
        "where": "Supporting details, fifth bullet",
        "quote": "`npm run build` invokes Eleventy and writes `_site`; `npm test` runs Node's test runner. The repository has no `docs/index.md` or authoring guide.",
        "why": "A list item mixing several facts from different topics (commands, absent docs structure, sole documentation) instead of splitting them into separate items."
      },
      {
        "where": "Questions and decisions, all four bullets",
        "quote": "Recommendation: display every author because archives are explicitly in scope.",
        "why": "Each bullet merges the open question and the proposed answer into one item; separating the two would let a reader scan the open questions alone without wading through recommendations."
      },
      {
        "where": "Requirement verification, third bullet",
        "quote": "This does not establish that unknown external repositories have migrated.",
        "why": "A load-bearing scope limitation of the evidence gate is buried as the last sentence of a dense three-action item rather than being given its own visible line."
      },
      {
        "where": "Implementation plan — Design, first paragraph",
        "quote": "normalize both forms at one Eleventy boundary into a canonical iterable list; templates should not each implement their own legacy fallback",
        "why": "The central architectural rule of the migration is a subordinate semicolon clause mid-paragraph rather than an isolated statement, so the most important design constraint is easy to skim past."
      }
    ],
    "summary": "A single ~1,250-word task file whose readability rests on short, heading-led sections: every top-level section is list-driven, and the one large section (Implementation plan, 872 words) is chunked into eight subsections with an ordered milestone list, so each part can be taken in with modest effort; the only strain is localized — an 85-word five-directive Design paragraph and ~50-word multi-action verification bullets. Navigation is heading-driven and reliable: the outcome (Requirements checklist), the constraint (Scope), and the open questions (Questions and decisions) are each one heading away, and 'Status: Draft' sits directly under the Implementation plan heading. The real costs are redundancy rather than density: remaining work appears in three overlapping unchecked lists, and the open questions are restated under 'Implementation decisions and open questions', whose heading promises decisions it does not contain. A few bullets also pack several facts (commands plus docs state; question plus recommendation), and one evidence-scope caveat is buried at the end of a dense verification item. Nothing forces re-reading; the indicated fixes are deduplication and splitting multi-fact bullets, not restructuring."
  }
}
```
