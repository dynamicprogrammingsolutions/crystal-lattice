# Session — tg10-flask-vue-interface-copy · file-readability-assessment-glm-max-s0 · glm max

- Run: `20261030T000100.781729Z-task-guidance-file-readability-tg10-flask-vue-interface-copy-glm-max-s0-81e55f65`
- Model: glm-5.3-flash (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) — captured (original SHA-256 `979db0d72bb44481…`)
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
  "scenario_id": "tg10-flask-vue-interface-copy",
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

# Write the user-facing copy

Write the home introduction, empty states, and failure messages for the books app within its concise plain tone, accepted by brief and style review.

Category: kind
Task kind: content

Measured structure facts (per file, per top-level section):

#### tasks/20261029-books-interface-copy.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20261029-books-interface-copy.md — Requirements checklist | 162 | 0 | 0 | 7 | 12 | 0 | 0 | 0 | 2 |
| tasks/20261029-books-interface-copy.md — Requirement questions (open) | 105 | 0 | 0 | 2 | 14 | 0 | 0 | 0 | 5 |
| tasks/20261029-books-interface-copy.md — Writing brief | 131 | 0 | 0 | 6 | 15 | 0 | 0 | 0 | 1 |
| tasks/20261029-books-interface-copy.md — Style checklist (maintainer review criteria) | 106 | 0 | 0 | 8 | 12 | 0 | 0 | 0 | 0 |
| tasks/20261029-books-interface-copy.md — Supporting facts (verified in this workspace) | 141 | 0 | 0 | 6 | 11 | 0 | 0 | 0 | 18 |
| tasks/20261029-books-interface-copy.md — Execution plan | 426 | 2 | 34 | 20 | 14 | 5 | 0 | 0 | 16 |

The produced task files:

### tasks/20261029-books-interface-copy.md

````markdown
# Books interface copy

Write the user-facing copy for the Vue Books client, replacing the placeholder
texts: the home page introduction, the empty-state texts for the book list and
for search with no results, and the messages shown when loading or saving a
book fails. Copy-only work; no behavior changes.

## Requirements checklist

- [ ] Home page introduction: concise introduction copy is shown at the top of
      the Books page (`client/src/components/Books.vue`, the app's home view).
- [ ] Book-list empty state: new copy replaces the `No books found.`
      placeholder shown when the book list is empty.
- [ ] Search no-results state: copy exists for a search or filter that matches
      nothing and is distinct from the plain empty-list copy.
- [ ] Failure messages: copy exists for failing to load the books and for
      failing to save a book change (two messages).
- [ ] All copy satisfies the style checklist below and matches the app's
      concise, plain tone.
- [ ] A maintainer has reviewed the final copy against this brief and the
      style checklist and approved it (human verification).
- [ ] No behavior changes: copy/text only. Filtering, data flow, API calls,
      and routing logic are unchanged; the client test suite passes, with
      assertions updated only where they asserted replaced text.

## Requirement questions (open)

- Q1 (search no-results): The client has no search input. The closest state is
  the `all`/`read`/`unread` filter, which currently reuses the same
  empty-state paragraph for every empty result (`Books.vue:13-16`). Does this
  task also add the minimal template distinction so the no-results copy is
  displayed, or is the copy written now and wired in a later change?
- Q2 (failure messages): No failure UI exists; load/save calls are awaited
  without error handling (`Books.vue:26-41`), so a failed request currently
  surfaces nothing to the user. Showing the failure copy requires minimal new
  error display, which is new failure-path UI. In scope here, or draft-only
  for a later change?

## Writing brief

- Home introduction: 1–2 short sentences on what the page is for (browse the
  book list, filter by read status). No marketing language.
- Book-list empty state: state plainly that there are no books yet. Reference
  a next action only if the page actually offers it (it currently offers
  filtering only; there is no add-book form on the page).
- Search no-results: acknowledge that the current filter matched nothing and
  point to the way back to the full list (the `all` filter).
- Load failure: say the books could not be loaded and suggest trying again.
- Save failure: say the change could not be saved and suggest trying again.
- Error and empty states must be true of the actual UI; do not promise
  functions the page does not have.

## Style checklist (maintainer review criteria)

- [ ] Concise: shortest clear phrasing; no filler or marketing words.
- [ ] Plain: everyday words, active voice, no jargon.
- [ ] Consistent with existing terms: "books", "read", "unread".
- [ ] Sentence case; full-sentence messages end with a period; short labels
      do not.
- [ ] Each message states the situation and, where the UI offers one, the
      next step.
- [ ] No blame, humor, exclamation marks, or "Oops"/"Sorry" filler in error
      and empty states.
- [ ] No placeholder tokens (Lorem, TODO, "coming soon", "example").
- [ ] Each string stands alone, without referring to text that is not shown.

## Supporting facts (verified in this workspace)

- All UI copy lives inline in `client/src/components/Books.vue`; there is no
  copy or i18n module, no `App.vue`, and no HTML entry file. The Books page is
  the app's only view, so the home introduction belongs at its top.
- Current texts: filter labels `all`/`read`/`unread` (`Books.vue:5`); one
  shared empty-state paragraph `No books found.` (`Books.vue:16`).
- `client/tests/Books.spec.js:16` asserts the exact string `No books found.`,
  so replacing that copy requires updating the assertion in the same change.
- `getBooks`/`addBook`/`updateBook`/`deleteBook` (`client/src/api/books.js`)
  have no catch paths and no error surface anywhere in the component.
- `Books.vue` carries marked functional regressions ("regression: filter
  lost", lines 32/36/40). Out of scope; do not fix them in this task.
- Tone evidence: `No books found.` (short, declarative, terminal period),
  lowercase single-word filter labels, and the plain README description. The
  Flask server (`server/app.py`) returns JSON only and carries no user-facing
  copy.

## Execution plan

Status: Draft

Copy is drafted against the brief, applied to the single page component, and
reviewed by a maintainer before the copy requirements are marked complete.
Copy stays inline in `Books.vue`; no copy/i18n infrastructure is introduced.

1. Resolve Q1 and Q2 with the requester; scope the wiring accordingly.
2. Draft the five strings (introduction, empty list, no results, load
   failure, save failure) against the brief and style checklist.
3. Apply the introduction and empty-state copy in `Books.vue` (static
   template text only).
4. If Q1/Q2 put the wiring in scope: add the minimal template distinction for
   the filtered no-results state and the minimal error display for failed
   load/save; otherwise record the no-results and failure copy as drafted
   with placement deferred.
5. Update `client/tests/Books.spec.js` asserted strings to match shipped copy
   (assert new strings only if they are wired and rendered).
6. Run the client suite (`npm test` in `client/`) and keep it green.
7. Submit the applied copy to the maintainer with this brief and checklist;
   record the review outcome before ticking the review requirement.

### Implementation decisions and open questions

- Decision: copy remains inline in `Books.vue`; no new dependencies or
  copy-management modules, keeping the change copy-only and matching the
  current structure.
- Open: Q1 and Q2 above (wiring scope for no-results and failure copy).

### Documentation

No documentation changes. This is UI copy, not maintained documentation, and
no maintained docs describe the page text (`docs/development/index.md`
records that no book-discovery specification exists). No behavior changes, so
no documentation updates are triggered.

### Task checklist

- [ ] Q1/Q2 resolved with the requester
- [ ] Five strings drafted
- [ ] Introduction and empty-state copy applied to `Books.vue`
- [ ] No-results / failure wiring applied, or placement explicitly deferred
- [ ] `Books.spec.js` assertions match shipped copy
- [ ] Client suite green (`npm test` in `client/`)
- [ ] Maintainer review recorded against the brief and checklist

### Requirement verification

- Introduction / empty-state / no-results / failure copy shown as intended:
  render assertions in `client/tests/Books.spec.js` against the real component
  (the API is mocked at the transport boundary, which is acceptable here
  because the claim is the rendered text, not the transport). Applies to
  wired copy; draft-only copy is evidenced by the approved copy text recorded
  in this task plus the maintainer review.
- Tone/style and the review requirement: maintainer approval recorded in this
  task; human verification, left unchecked until confirmed.
- No behavior changes: diff inspection (copy, static template text, and
  asserted test strings only) plus the full client suite passing.

### Additional implementation verification

- Grep the client source for placeholder tokens (`Lorem`, `TODO`,
  `placeholder`, `coming soon`) and confirm none remain.
````


**Assistant** *(reasoning present)*

```json
{
  "schema_version": 1,
  "scenario_id": "tg10-flask-vue-interface-copy",
  "assessment": {
    "sections": {
      "tasks/20261029-books-interface-copy.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, item 4",
            "quote": "Failure messages: copy exists for failing to load the books and for failing to save a book change (two messages).",
            "why": "Each checkbox states one requirement with an explicit count and scope; a maintainer can scan all seven in one pass and know what 'done' means for each."
          },
          {
            "where": "Requirements checklist, item 7",
            "quote": "No behavior changes: copy/text only. Filtering, data flow, API calls, and routing logic are unchanged; the client test suite passes, with assertions updated only where they asserted replaced text.",
            "why": "One checkbox bundles four facts (scope limit, unchanged areas, green-suite criterion, assertion caveat); the load-bearing caveat is the trailing clause and easiest to miss."
          }
        ]
      },
      "tasks/20261029-books-interface-copy.md — Requirement questions (open)": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirement questions (open), Q1",
            "quote": "Does this task also add the minimal template distinction so the no-results copy is displayed, or is the copy written now and wired in a later change?",
            "why": "Both questions end in a crisp either/or, so the decision a reader must get from the requester is immediately actionable; the Q1/Q2 labels make them addressable from the plan and checklist."
          },
          {
            "where": "Requirement questions (open), Q2",
            "quote": "No failure UI exists; load/save calls are awaited without error handling (`Books.vue:26-41`), so a failed request currently surfaces nothing to the user.",
            "why": "Each bullet packs context, code line refs, and the question into one item, so it takes one slow read rather than a scan; acceptable at 105 words total but the densest reading per item in the file's front half."
          }
        ]
      },
      "tasks/20261029-books-interface-copy.md — Writing brief": {
        "grade": "readable",
        "findings": [
          {
            "where": "Writing brief, book-list empty state bullet",
            "quote": "Book-list empty state: state plainly that there are no books yet. Reference a next action only if the page actually offers it (it currently offers filtering only; there is no add-book form on the page).",
            "why": "A clean one-bullet-per-string mapping (five bullets for five strings), each with the constraint attached, so a writer can draft directly from the list."
          },
          {
            "where": "Writing brief, final bullet",
            "quote": "Error and empty states must be true of the actual UI; do not promise functions the page does not have.",
            "why": "The cross-cutting constraint is surfaced as its own item instead of being buried in one string's guidance; six short items hold without strain."
          }
        ]
      },
      "tasks/20261029-books-interface-copy.md — Style checklist (maintainer review criteria)": {
        "grade": "readable",
        "findings": [
          {
            "where": "Style checklist, sentence-case item",
            "quote": "Sentence case; full-sentence messages end with a period; short labels do not.",
            "why": "Eight parallel items, each one checkable criterion in ~10 words; a reviewer can tick through the whole list in a single read."
          },
          {
            "where": "Style checklist, standalone item",
            "quote": "Each string stands alone, without referring to text that is not shown.",
            "why": "No item mixes several style rules; the heading '(maintainer review criteria)' accurately matches the content, so the list's purpose is clear from structure alone."
          }
        ]
      },
      "tasks/20261029-books-interface-copy.md — Supporting facts (verified in this workspace)": {
        "grade": "readable",
        "findings": [
          {
            "where": "Supporting facts, current texts bullet",
            "quote": "Current texts: filter labels `all`/`read`/`unread` (`Books.vue:5`); one shared empty-state paragraph `No books found.` (`Books.vue:16`).",
            "why": "One verified fact per bullet with precise line anchors; 18 code spans make it reference-dense, but each span is a pointer a maintainer looks up, not prose to parse."
          },
          {
            "where": "Supporting facts, tone evidence bullet",
            "quote": "Tone evidence: `No books found.` (short, declarative, terminal period), lowercase single-word filter labels, and the plain README description.",
            "why": "Three evidence examples share one bullet, but the 'Tone evidence:' label groups them under a single purpose, so the reader holds them as one claim rather than three unrelated facts."
          }
        ]
      },
      "tasks/20261029-books-interface-copy.md — Execution plan": {
        "grade": "readable",
        "findings": [
          {
            "where": "Execution plan, subsection headers",
            "quote": "### Implementation decisions and open questions ... ### Documentation ... ### Task checklist ... ### Requirement verification ... ### Additional implementation verification",
            "why": "426 words stay navigable because the section is chunked into five short labeled subsections plus a numbered step list; the reader never faces an undifferentiated block."
          },
          {
            "where": "Execution plan, Requirement verification first bullet",
            "quote": "render assertions in `client/tests/Books.spec.js` against the real component (the API is mocked at the transport boundary, which is acceptable here because the claim is the rendered text, not the transport). Applies to wired copy; draft-only copy is evidenced by the approved copy text recorded in this task plus the maintainer review.",
            "why": "The densest item in the file: one bullet carries four copy targets, the evidence method, a defensive justification parenthetical, and a wired-vs-draft scope split; a reader will likely need a second pass to separate what is verified from why it counts."
          },
          {
            "where": "Execution plan, step 4",
            "quote": "If Q1/Q2 put the wiring in scope: add the minimal template distinction for the filtered no-results state and the minimal error display for failed load/save; otherwise record the no-results and failure copy as drafted with placement deferred.",
            "why": "One step carries both branches of two open questions; readable as a plan, but the reader must hold Q1 and Q2 outcomes to know which half applies."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Execution plan, opening line",
          "quote": "Status: Draft",
          "why": "Plan status sits on the first line of the plan section, exactly where a reader looking for status will scan; every major reader goal has an obvious heading (outcome = Requirements checklist, constraints = Writing brief + Style checklist, open questions = Requirement questions (open))."
        },
        {
          "where": "Execution plan, Task checklist vs Requirements checklist",
          "quote": "- [ ] Five strings drafted ... - [ ] Maintainer review recorded against the brief and checklist",
          "why": "Two overlapping seven-item checklists exist (requirements at the top, execution at the bottom); a reader ticking boxes must infer which list is authoritative, since neither cross-references the other."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Requirements checklist, item 7",
        "quote": "No behavior changes: copy/text only. Filtering, data flow, API calls, and routing logic are unchanged; the client test suite passes, with assertions updated only where they asserted replaced text.",
        "why": "List item mixing several facts: scope boundary, unchanged subsystems, test criterion, and the assertion caveat share one checkbox; the caveat is the load-bearing part and is trailing."
      },
      {
        "where": "Supporting facts, fifth bullet",
        "quote": "`Books.vue` carries marked functional regressions (\"regression: filter lost\", lines 32/36/40). Out of scope; do not fix them in this task.",
        "why": "Buried load-bearing fact: a binding do-not-touch constraint is placed inside a background facts list rather than in the requirements or brief, where a reader scoping the work would look first."
      },
      {
        "where": "Execution plan, Requirement verification first bullet",
        "quote": "Introduction / empty-state / no-results / failure copy shown as intended: render assertions in `client/tests/Books.spec.js` against the real component (the API is mocked at the transport boundary, which is acceptable here because the claim is the rendered text, not the transport).",
        "why": "Prose-density mistake at item level: claim, method, justification, and a two-case scope note compressed into one ~60-word bullet that must be re-read to act on."
      },
      {
        "where": "Requirements checklist item 3 / Writing brief bullet 3, read against Supporting facts",
        "quote": "Search no-results state: copy exists for a search or filter that matches nothing",
        "why": "Terminology mismatch: requirements and brief say 'search' while the facts state 'The client has no search input'; the discrepancy is only resolved by reading Q1, so a reader who skips that section is briefly misled about the UI."
      },
      {
        "where": "Execution plan, step 4 and Task checklist item 4",
        "quote": "If Q1/Q2 put the wiring in scope: add the minimal template distinction ... otherwise record the no-results and failure copy as drafted with placement deferred",
        "why": "A conditional step plus a checklist item ('No-results / failure wiring applied, or placement explicitly deferred') each pack both scope branches into one line; the reader needs Q1/Q2 in hand to know which half is their instruction."
      }
    ],
    "summary": "All six top-level sections are readable: each is short, single-purpose, and list-shaped, with one idea per item for the requirements, brief, style criteria, and facts; the plan's 426 words are held up by five labeled subsections and a numbered step list. Navigation is navigable from headings alone — outcome, constraints, open questions, and the 'Status: Draft' marker are all findable where a reader looks. The defects are localized, not structural: a few items bundle multiple facts (the no-behavior-change requirement, conditional step 4, the requirement-verification bullet), one binding constraint (do not fix the marked regressions) sits in background facts instead of requirements, 'search' is used for a UI that has only filters, and two parallel checklists leave authority ambiguous. None of these force a re-read of more than a single item."
  }
}
```
