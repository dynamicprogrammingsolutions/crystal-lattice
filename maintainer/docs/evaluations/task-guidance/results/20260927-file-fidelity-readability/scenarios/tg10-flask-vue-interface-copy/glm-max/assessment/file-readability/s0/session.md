# Session — tg10-flask-vue-interface-copy · file-readability-assessment-glm-max-s0 · glm max

- Run: `20260928T215405.091255Z-task-guidance-file-readability-tg10-flask-vue-interface-copy-glm-max-s0-d4e13e32`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `bc975faaebfbd0b2…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

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

#### tasks/20260926-books-interface-copy.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-books-interface-copy.md — Requirements checklist | 174 | 1 | 27 | 9 | 18 | 0 | 0 | 0 | 2 |
| tasks/20260926-books-interface-copy.md — Open questions and decisions | 129 | 1 | 15 | 2 | 72 | 0 | 0 | 0 | 2 |
| tasks/20260926-books-interface-copy.md — Brief | 267 | 1 | 24 | 5 | 61 | 0 | 0 | 0 | 3 |
| tasks/20260926-books-interface-copy.md — Style checklist (the copy must pass every item) | 90 | 0 | 0 | 5 | 20 | 0 | 0 | 0 | 0 |
| tasks/20260926-books-interface-copy.md — Facts verified in this workspace | 129 | 0 | 0 | 6 | 28 | 0 | 0 | 0 | 21 |

The produced task files:

### tasks/20260926-books-interface-copy.md

````markdown
# Books interface copy: replace placeholder texts

Write final user-facing copy for the Books interface — the home page introduction, the empty states for the book list and for search with no results, and the messages shown when loading or saving a book fails. Copy follows the app's existing concise, plain tone; a maintainer reviews it against the brief and the style checklist in this task. No behavior changes: only the existing book-list empty-state string is replaced in code; copy for surfaces that do not exist yet is drafted and recorded in this task.

## Requirements checklist

- [ ] Copy is written for the home page introduction (Brief).
- [ ] Copy is written for the book list empty state (Brief).
- [ ] Copy is written for the search no-results empty state (Brief).
- [ ] Copy is written for the message shown when loading books fails (Brief).
- [ ] Copy is written for the message shown when saving a book fails (Brief).
- [ ] The copy follows the app's concise, plain tone; every text passes the Style checklist.
- [ ] The approved book-list empty-state copy replaces the placeholder in `client/src/components/Books.vue` (text-only change) and `client/tests/Books.spec.js` asserts the new text.
- [ ] Approved copy for the four surfaces with no current UI is recorded in this task for later implementation.
- [ ] A maintainer has reviewed the copy against the Brief and the Style checklist and approved it.

The maintainer-review item is human verification: leave it unchecked until a maintainer confirms. Mark the other items complete only with evidence (the diff, the updated test run).

## Open questions and decisions

No open requirement questions. Decisions made while creating this task — flag them if wrong:

- **Draft copy for surfaces that do not exist yet** (home page introduction, search no-results, load-failure message, save-failure message) is written and recorded in this task, not added to the code. The client has no home page, no search UI, and no error handling; adding any of them would be a behavior change, which the request excludes. Recorded here rather than in a new documentation file per the smallest-documentation-structure rule in `AGENTS.md`.
- **The book-list empty state is replaced in code.** That surface exists today, and swapping the placeholder string for approved copy is a text-only change, not a behavior change. `client/tests/Books.spec.js` asserts the old string, so it is updated in the same change.

## Brief

Audience: readers of the Books page. Tone: the app's existing concise, plain voice (Style checklist below). All texts appear in the page, in English.

1. **Home page introduction** — no home page exists yet (`client/src` has no entry component; the Flask server serves only the JSON API). Purpose: one or two short sentences telling a first-time reader what the Books app is and what they can do here. Drafted for the future home page; not placed in code by this task.
2. **Book list empty state** — exists today: `client/src/components/Books.vue:16` renders "No books found." whenever the list has no rows. That single string currently covers every empty case, including "no books at all" and "the selected read/unread filter matches nothing"; splitting the cases would be a behavior change, so the approved copy must read correctly for both. This text replaces the placeholder.
3. **Search with no results** — no search UI exists (the read/unread status filter is the only lookup today, and it shares the list empty state). Purpose: one short sentence telling the reader the search matched nothing. Drafted for the future search feature; not placed in code by this task.
4. **Loading fails** — no such message exists: no API call in `Books.vue` handles errors. Purpose: one short sentence telling the reader the books could not be loaded. Drafted for future error handling; not placed in code by this task.
5. **Saving fails** — no such message exists (same gap). Purpose: one short sentence telling the reader the book could not be saved. Drafted for future error handling; not placed in code by this task.

## Style checklist (the copy must pass every item)

- [ ] Sentence case; ends with a period; no exclamation marks; no emoji.
- [ ] Short: an empty state or error message is one sentence; the introduction is at most two.
- [ ] Plain everyday words; no jargon or internal terms (API, endpoint, JSON).
- [ ] From the reader's point of view: says what happened or what is shown, without blame, status codes, or technical detail.
- [ ] Uses the interface's own words — "book", "books", "search" — consistently; no synonyms like "item" or "record".

## Facts verified in this workspace

- Client user-facing strings today: the filter button labels `all` / `read` / `unread` (`client/src/components/Books.vue:5`, out of scope) and the empty-state text "No books found." (`Books.vue:16`).
- No home page surface: `client/src` contains only `api/books.js`, `http.js`, and `components/Books.vue`; `vue-router` is a declared dependency but unused; the Flask server (`server/app.py`) serves only the JSON API.
- The empty-state string renders whenever the book list has no rows (`v-if="books.length"` / `v-else`), so it currently covers both "no books at all" and "filter matches nothing".
- No error handling exists in `Books.vue`: `selectFilter`, `add`, `update`, and `remove` await the API without catching failures, and nothing renders failure messages.
- `client/tests/Books.spec.js:16` asserts the literal "No books found.".
- No maintained documentation (`README.md`, `docs/`) references these strings, so this task requires no documentation updates.
````


**Assistant** *(reasoning present)*

{
  "schema_version": 1,
  "scenario_id": "tg10-flask-vue-interface-copy",
  "assessment": {
    "sections": {
      "tasks/20260926-books-interface-copy.md — Requirements checklist": {
        "grade": "readable",
        "findings": [
          {
            "where": "Requirements checklist, items 1–5",
            "quote": "- [ ] Copy is written for the search no-results empty state (Brief).",
            "why": "All five surface items repeat the same '(Brief)' tag that names the Brief section but not its item numbers (1–5), so checklist lines can only be matched to Brief entries by position."
          },
          {
            "where": "Requirements checklist, item 7",
            "quote": "The approved book-list empty-state copy replaces the placeholder in `client/src/components/Books.vue` (text-only change) and `client/tests/Books.spec.js` asserts the new text.",
            "why": "One checkbox bundles two artifacts — the component string replacement and the test assertion — so the reader completing it must treat a code edit and a test update as a single verifiable unit."
          }
        ]
      },
      "tasks/20260926-books-interface-copy.md — Open questions and decisions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Open questions and decisions, first decision bullet",
            "quote": "Recorded here rather than in a new documentation file per the smallest-documentation-structure rule in `AGENTS.md`.",
            "why": "The bullet runs ~72 words across a decision, its rationale, and a policy citation; the bold lead-in keeps the operative fact on a first pass, but the closing sentence is process detail a reader hunting for the decision itself must skim past."
          }
        ]
      },
      "tasks/20260926-books-interface-copy.md — Brief": {
        "grade": "partial",
        "findings": [
          {
            "where": "Brief, item 2 (Book list empty state)",
            "quote": "splitting the cases would be a behavior change, so the approved copy must read correctly for both",
            "why": "The task's governing constraint on the deliverable — one string must serve both 'no books at all' and 'filter matches nothing' — is the tail of the second sentence of a 61-word list item, behind a semicolon-spliced causal chain; a reader can reach the end of the item without registering it as the binding requirement."
          },
          {
            "where": "Brief, intro paragraph",
            "quote": "All texts appear in the page, in English.",
            "why": "Present-tense claim that collides with the items' repeated 'not placed in code by this task'; the reader must infer the intended meaning (these are on-page UI strings, not documentation) rather than take the sentence literally."
          }
        ]
      },
      "tasks/20260926-books-interface-copy.md — Style checklist (the copy must pass every item)": {
        "grade": "readable",
        "findings": []
      },
      "tasks/20260926-books-interface-copy.md — Facts verified in this workspace": {
        "grade": "readable",
        "findings": [
          {
            "where": "Facts verified in this workspace, bullet 2",
            "quote": "`client/src` contains only `api/books.js`, `http.js`, and `components/Books.vue`; `vue-router` is a declared dependency but unused; the Flask server (`server/app.py`) serves only the JSON API.",
            "why": "One list item mixes three separate findings (file inventory, unused dependency, server scope) separated only by semicolons; each clause must be parsed individually to extract the facts."
          },
          {
            "where": "Facts verified in this workspace, bullet 1",
            "quote": "the filter button labels `all` / `read` / `unread` (`client/src/components/Books.vue:5`, out of scope)",
            "why": "A load-bearing scope ruling is tucked into a citation parenthetical inside a bullet that also carries a second string fact; a reader scanning for which strings are in play can miss it."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": []
    },
    "mistakes": [
      {
        "where": "Brief, item 2 (Book list empty state)",
        "quote": "That single string currently covers every empty case ... so the approved copy must read correctly for both",
        "why": "Buried load-bearing fact: the one requirement that most constrains the copy (one string must fit two distinct empty cases) sits mid-item in the longest entry (61 words) rather than being surfaced as its own constraint line."
      },
      {
        "where": "Brief, intro paragraph",
        "quote": "All texts appear in the page, in English.",
        "why": "Reads as a present-tense claim about the current page, yet four of the five texts are drafted for surfaces that do not exist and are 'not placed in code by this task'; the sentence only makes sense as 'these are on-page UI strings, in English', which the reader must reconstruct."
      },
      {
        "where": "Facts verified in this workspace, bullet 2",
        "quote": "`client/src` contains only `api/books.js`, `http.js`, and `components/Books.vue`; `vue-router` is a declared dependency but unused; the Flask server (`server/app.py`) serves only the JSON API.",
        "why": "List item mixes several facts — the file inventory, the unused vue-router dependency, and the server's API-only scope — in a single 28-word bullet."
      },
      {
        "where": "Facts verified in this workspace, bullet 1",
        "quote": "(`client/src/components/Books.vue:5`, out of scope)",
        "why": "The 'out of scope' ruling is parenthetically attached to a file:line citation rather than stated as a fact of its own, so its effect on what the copywriter may touch is easy to overlook."
      }
    ],
    "summary": "One well-ordered file: scope in the opening paragraph, then acceptance checklist, decisions, per-surface brief, style rules, and verified facts. Four of the five sections scan in a single pass — checklist items are short single-fact lines (longest 18–20 words) and every fact bullet carries a file:line anchor. The strain is concentrated in the Brief: item 2 is a 61-word entry whose second, semicolon-spliced sentence carries the task's binding constraint (the single empty-state string must read correctly for both 'no books at all' and 'filter matches nothing'), and the intro's present-tense 'All texts appear in the page' sits awkwardly against the items' repeated 'not placed in code by this task'. The two ~70-word decision bullets are dense but front-load their operative fact in bold stems, so they stay usable. Navigation works from structure alone: the outcome and code-impact statement open the file, plan status and the human-verification caveat live in the Requirements checklist, open questions are answered in the first line of their section, and the acceptance rules sit in two named checklists."
  }
}
