# Task-file readability assessment

- Assessor: `glm-5.3-flash:cloud` (effort max) · run `20260928T215405.091255Z-task-guidance-file-readability-tg10-flask-vue-interface-copy-glm-max-s0-d4e13e32`
- Assessor config: [glm-assessor-max.json](../../../../shared/configs/glm-assessor-max.json)
- Assessor system message: [glm-assessor-3d0be6dc03e9.md](../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) (original SHA-256 `bc975faaebfbd0b2…`)
- First judgment's full transcript: [session.md](../../glm-max/assessment/file-readability/s0/session.md) — includes the exact prompt and the raw response; every judgment's transcript lives beside its subject (`<cell>/assessment/file-readability/…`)
- Reviewed target: [tg10-flask-vue-interface-copy](../../target.md)
- Rubric: every top-level section is graded (readable/partial/unreadable) plus whole-file navigation (navigable/partial/confusing), anchored on measured structure facts; findings required for non-top grades; presentation mistakes harvested.

## Judgments

### glm · max (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-books-interface-copy.md — Brief | partial | 2 |
| tasks/20260926-books-interface-copy.md — Facts verified in this workspace | readable | 2 |
| tasks/20260926-books-interface-copy.md — Open questions and decisions | readable | 1 |
| tasks/20260926-books-interface-copy.md — Requirements checklist | readable | 2 |
| tasks/20260926-books-interface-copy.md — Style checklist (the copy must pass every item) | readable | 0 |
| _navigation_ | navigable | 0 |

**Findings**

- tasks/20260926-books-interface-copy.md — Brief — Brief, item 2 (Book list empty state): The task's governing constraint on the deliverable — one string must serve both 'no books at all' and 'filter matches nothing' — is the tail of the second sentence of a 61-word list item, behind a semicolon-spliced causal chain; a reader can reach the end of the item without registering it as the binding requirement. (`splitting the cases would be a behavior change, so the approved copy must read c`)
- tasks/20260926-books-interface-copy.md — Brief — Brief, intro paragraph: Present-tense claim that collides with the items' repeated 'not placed in code by this task'; the reader must infer the intended meaning (these are on-page UI strings, not documentation) rather than take the sentence literally. (`All texts appear in the page, in English.`)
- tasks/20260926-books-interface-copy.md — Facts verified in this workspace — Facts verified in this workspace, bullet 2: One list item mixes three separate findings (file inventory, unused dependency, server scope) separated only by semicolons; each clause must be parsed individually to extract the facts. (`'client/src' contains only 'api/books.js', 'http.js', and 'components/Books.vue'`)
- tasks/20260926-books-interface-copy.md — Facts verified in this workspace — Facts verified in this workspace, bullet 1: A load-bearing scope ruling is tucked into a citation parenthetical inside a bullet that also carries a second string fact; a reader scanning for which strings are in play can miss it. (`the filter button labels 'all' / 'read' / 'unread' ('client/src/components/Books`)
- tasks/20260926-books-interface-copy.md — Open questions and decisions — Open questions and decisions, first decision bullet: The bullet runs ~72 words across a decision, its rationale, and a policy citation; the bold lead-in keeps the operative fact on a first pass, but the closing sentence is process detail a reader hunting for the decision itself must skim past. (`Recorded here rather than in a new documentation file per the smallest-documenta`)
- tasks/20260926-books-interface-copy.md — Requirements checklist — Requirements checklist, items 1–5: All five surface items repeat the same '(Brief)' tag that names the Brief section but not its item numbers (1–5), so checklist lines can only be matched to Brief entries by position. (`- [ ] Copy is written for the search no-results empty state (Brief).`)
- tasks/20260926-books-interface-copy.md — Requirements checklist — Requirements checklist, item 7: One checkbox bundles two artifacts — the component string replacement and the test assertion — so the reader completing it must treat a code edit and a test update as a single verifiable unit. (`The approved book-list empty-state copy replaces the placeholder in 'client/src/`)

**Mistakes**

- Brief, item 2 (Book list empty state): Buried load-bearing fact: the one requirement that most constrains the copy (one string must fit two distinct empty cases) sits mid-item in the longest entry (61 words) rather than being surfaced as its own constraint line. (`That single string currently covers every empty case ... so the approved copy mu`)
- Brief, intro paragraph: Reads as a present-tense claim about the current page, yet four of the five texts are drafted for surfaces that do not exist and are 'not placed in code by this task'; the sentence only makes sense as 'these are on-page UI strings, in English', which the reader must reconstruct. (`All texts appear in the page, in English.`)
- Facts verified in this workspace, bullet 2: List item mixes several facts — the file inventory, the unused vue-router dependency, and the server's API-only scope — in a single 28-word bullet. (`'client/src' contains only 'api/books.js', 'http.js', and 'components/Books.vue'`)
- Facts verified in this workspace, bullet 1: The 'out of scope' ruling is parenthetically attached to a file:line citation rather than stated as a fact of its own, so its effect on what the copywriter may touch is easy to overlook. (`('client/src/components/Books.vue:5', out of scope)`)

One well-ordered file: scope in the opening paragraph, then acceptance checklist, decisions, per-surface brief, style rules, and verified facts. Four of the five sections scan in a single pass — checklist items are short single-fact lines (longest 18–20 words) and every fact bullet carries a file:line anchor. The strain is concentrated in the Brief: item 2 is a 61-word entry whose second, semicolon-spliced sentence carries the task's binding constraint (the single empty-state string must read correctly for both 'no books at all' and 'filter matches nothing'), and the intro's present-tense 'All texts appear in the page' sits awkwardly against the items' repeated 'not placed in code by this task'. The two ~70-word decision bullets are dense but front-load their operative fact in bold stems, so they stay usable. Navigation works from structure alone: the outcome and code-impact statement open the file, plan status and the human-verification caveat live in the Requirements checklist, open questions are answered in the first line of their section, and the acceptance rules sit in two named checklists.


### gpt · high (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-books-interface-copy.md — Copy brief | readable | 1 |
| tasks/20260926-books-interface-copy.md — Execution plan | partial | 3 |
| tasks/20260926-books-interface-copy.md — Open requirement questions and decisions | readable | 1 |
| tasks/20260926-books-interface-copy.md — Requirements checklist | readable | 1 |
| tasks/20260926-books-interface-copy.md — Scope and constraints | readable | 1 |
| tasks/20260926-books-interface-copy.md — Style checklist | readable | 1 |
| tasks/20260926-books-interface-copy.md — Supporting facts | readable | 1 |
| _navigation_ | navigable | 1 |

**Findings**

- tasks/20260926-books-interface-copy.md — Copy brief — Copy brief, Loading failure and Saving failure items: Five items map one-to-one onto the five copy surfaces, which aids scanning, but the 'only when the existing UI already exposes it' condition recurs in three items with slightly different wording, making the reader verify the conditions are in fact identical. (`Give a recovery instruction only when the existing UI already exposes that recov`)
- tasks/20260926-books-interface-copy.md — Execution plan — Execution plan, opening paragraph: The 78-word paragraph stacks four distinct instructions (ownership, surface mapping, drafting, replacement scope) in prose and ends on this three-clause test rule; the reader must re-read to separate what is allowed from what is prohibited in testing. (`Existing transport or state setup may be used to reach a real UI state in tests,`)
- tasks/20260926-books-interface-copy.md — Execution plan — Execution plan › Requirement verification: Each of the seven items bundles verification method, assertion target, and a conditional fallback in one 25–40-word item; the blocking consequence for four of the surfaces sits at the tail of each item and is easy to miss on a first pass. (`Search no-results state: the owning production component test renders an existin`)
- tasks/20260926-books-interface-copy.md — Execution plan — Execution plan (intro paragraph, Task checklist, Requirement verification): The same review gate is restated three times within the section ('Obtain maintainer review against the full style checklist', 'Copy quality: maintainer sign-off records review against every item in the style checklist'), adding reading load without new information. (`The maintainer review is a completion gate`)
- tasks/20260926-books-interface-copy.md — Open requirement questions and decisions — Open requirement questions and decisions, first item: The section answers its own heading in the first three words and separates the one load-bearing scope decision into a clearly labeled second item, so a reader hunting for open questions is done immediately. (`Requirement questions: none.`)
- tasks/20260926-books-interface-copy.md — Requirements checklist — Requirements checklist, second item: The 8-item list keeps one requirement per item and scans easily; the only strain is this item's embedded conditional, which Supporting facts later reveals may be moot (the state itself may not exist), so the reader must cross-reference to know whether the clause applies. (`Replace the book-list empty-state placeholder with copy that describes the absen`)
- tasks/20260926-books-interface-copy.md — Scope and constraints — Scope and constraints, first paragraph: The 44-word sentence carries the deliverable plus five prohibitions in one breath; parallel structure keeps it listable on one read, but it is the densest sentence in the section. (`do not refactor the component, add new state, introduce retry or navigation acti`)
- tasks/20260926-books-interface-copy.md — Style checklist — Style checklist, seventh item: Nine single-rule items are easy to scan; this one restates the Copy brief's conditional as a style rule, so the reader must recognize it as the same constraint rather than an additional one. (`Do not promise an action, recovery, or result that the current UI does not suppo`)
- tasks/20260926-books-interface-copy.md — Supporting facts — Supporting facts, third bullet: The section is short and concrete, but this bullet — the task's biggest risk — is delivered as a peer of three routine facts with its consequence deferred to a trailing clause rather than given prominence. (`The compact fixture currently does not expose home-page, search, loading-failure`)
- navigation — Overall heading structure: Reader goals map one-to-one onto headings: outcome (title paragraph), constraints (Scope and constraints), open questions (Open requirement questions and decisions, answered 'none'), plan status (Execution plan, 'Status: Draft'), per-surface guidance (Copy brief), current state (Supporting facts), and verification (Execution plan › Requirement verification); the only friction is that verification criteria live inside the plan rather than as a sibling heading, though the subsection title makes them findable. (``)

**Mistakes**

- Supporting facts, third bullet: Buried load-bearing fact: the possibility that four of the five requested surfaces do not exist is the file's largest risk, yet it appears as the third of four peer bullets with the required response tacked on after a semicolon instead of being surfaced in the requirements or at the top of the plan. (`The compact fixture currently does not expose home-page, search, loading-failure`)
- Execution plan › Requirement verification, items 3–5: List items mix several facts: each packs the verification method, the assertion target, and a separate maintainer sign-off duty into one item, forcing the reader to parse compound sentences to tell automated checks from human sign-off steps. (`Loading failure: the owning production component test reaches the existing load-`)
- Requirements checklist item 8 / Scope and constraints paragraph 1 / Style checkl: The copy-only, no-new-behavior boundary is restated at least four times in different words with different enumeration lists ('do not refactor the component, add new state…', 'Do not promise an action…', 'must not supply the claimed copy or bypass rendering'); the reader must reconcile whether the lists differ in meaning, and the duplication risks divergence between sections. (`Make no behavior changes: preserve state transitions, search semantics, transpor`)
- Execution plan › Requirement verification: Verification criteria are written in the present tense as accomplished facts ('confirms', 'renders', 'asserts', 'sign-off records') while Status is 'Draft' and every checklist box is unchecked; a skimming reader can mistake the protocol for completed verification and must re-read to resolve the contradiction. (`Home introduction: a maintainer review confirms that the rendered introduction o`)

Six of seven sections are short, single-purpose lists or 1–2 brief paragraphs (46–164 words, longest item ~15 words) that a reader can scan and act on without re-reading. Navigation is strong because headings map directly onto reader goals and the plan status is explicit. The one partial section is the 456-word Execution plan: its opening 78-word paragraphs bundle ownership, mapping, and test rules into prose, and the seven Requirement-verification items pack method, assertion, and conditional blocking fallbacks into single items. Two presentation issues compound this: the file's biggest risk (four of five requested states may not exist in the fixture) is buried as the third bullet of Supporting facts, and the copy-only/no-behavior-change constraint is restated in at least four sections with differing enumerations.


### gpt · high (sample 1)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-user-facing-books-copy.md — Execution plan | readable | 2 |
| tasks/20260926-user-facing-books-copy.md — Requirement questions and decisions | readable | 1 |
| tasks/20260926-user-facing-books-copy.md — Requirements checklist | readable | 2 |
| tasks/20260926-user-facing-books-copy.md — Scope and copy brief | readable | 2 |
| tasks/20260926-user-facing-books-copy.md — Style checklist | readable | 1 |
| tasks/20260926-user-facing-books-copy.md — Supporting facts | readable | 1 |
| _navigation_ | navigable | 2 |

**Findings**

- tasks/20260926-user-facing-books-copy.md — Execution plan — Execution plan, status line and subsections: The 330 words are partitioned by a status line plus four subsections (decisions, documentation, a 6-item task checklist, 3 verification mappings), so a reader can jump to the part they need rather than re-reading prose to find plan status. (`Status: Draft`)
- tasks/20260926-user-facing-books-copy.md — Execution plan — Execution plan, opening paragraph: The measured longest paragraph (59 words) chains three reviewer actions in one sentence and ends on the vague phrase 'copy planning only'; it parses in one pass, but it is the section's highest-effort spot. (`A maintainer then checks every string against the brief and style checklist, rec`)
- tasks/20260926-user-facing-books-copy.md — Requirement questions and decisions — Requirement questions and decisions, opening paragraph: At 77 words total, the open-question answer is the first sentence and the three decisions follow as short one-line bullets; nothing needs re-reading to extract the state. (`There are no unresolved requirement questions.`)
- tasks/20260926-user-facing-books-copy.md — Requirements checklist — Requirements checklist, checkbox items: Eight checkbox items (measured longest item 13 words), each carrying exactly one requirement, so the whole acceptance surface is taken in on a single scan with no item needing re-reading. (`Provide a concise message for a failed book save.`)
- tasks/20260926-user-facing-books-copy.md — Requirements checklist — Requirements checklist, last item: The boundary constraint is given its own checkbox instead of being folded into another requirement, so the load-bearing restriction is not buried. (`Make no behavior changes as part of this task.`)
- tasks/20260926-user-facing-books-copy.md — Scope and copy brief — Scope and copy brief, context table: The five content contexts and their intent-plus-constraint pairs are held in one labeled 3-column table; a reviewer can verify row by row instead of parsing prose, and even the densest cells stay at one or two short sentences. (`| Loading a book list fails | Tell the user that the books could not be loaded. `)
- tasks/20260926-user-facing-books-copy.md — Scope and copy brief — Scope and copy brief, Current status column: All five rows carry the identical value, so the column adds table width without distinguishing anything; the same fact is restated in the paragraph below the table. (`Not implemented`)
- tasks/20260926-user-facing-books-copy.md — Style checklist — Style checklist, list items: Nine single-rule items (measured longest 11 words) let the maintainer work the review gate as a linear tick-list; no item bundles multiple rules, so each check is a one-line decision. (`Keep the empty library and no-search-results meanings distinct.`)
- tasks/20260926-user-facing-books-copy.md — Supporting facts — Supporting facts, list items: Four short bullets, each anchored to a code span naming its source file, so claims are checkable at a glance; the only wrinkle is that the fourth bullet is a scope decision rather than a repo fact, mixing claim types in one list. (`'client/src/components/Books.vue' currently renders the general empty-state plac`)
- navigation — Heading sequence, Requirements checklist through Execution plan: The six headings map one-to-one onto a maintainer's questions — what to produce (Scope and copy brief), what to check (Style checklist), open questions (Requirement questions and decisions), status ('Status: Draft' under Execution plan) — so each is reachable from structure alone. (`## Requirement questions and decisions`)
- navigation — Execution plan → Implementation decisions and open questions: The open-question answer lives under two different headings (here and under 'Requirement questions and decisions'), so a reader must check both places to be confident nothing is open. (`### Implementation decisions and open questions`)

**Mistakes**

- Recurring across Requirements checklist, Execution plan, Documentation, Task che: The copy-only/no-change constraint is restated five times within graded sections (six counting the intro) in shifting vocabulary (behavior / source / API / component logic), so the reader must diff every restatement to learn whether it adds a new nuance; one canonical statement with pointers would carry the same boundary. (`Make no behavior changes as part of this task. … no component logic, rendering c`)
- Execution plan, second paragraph: One paragraph bundles three distinct facts — deliverable portability, integration being out of scope, and the prohibited-changes list — leaving the load-bearing 'unless separately authorized' boundary buried mid-paragraph instead of standing alone. (`The copy should be written so it can later replace the relevant placeholders or `)
- Execution plan → Implementation decisions and open questions: The heading advertises 'open questions' but the subsection contains none and largely duplicates the closure already stated under 'Requirement questions and decisions', so a reader hunting for open items pays twice for one answer. (`The task remains Draft until execution is explicitly approved. Exact strings are`)
- Supporting facts, fourth bullet: A scope decision is filed in a list titled 'Supporting facts', mixing verified repo facts with a task decision so the reader cannot treat the bullets as one evidence class. (`No maintained user or developer documentation needs updating for this copy-only `)

A single, well-partitioned content-task file: every top-level section stays within easily held shapes (8–9 single-fact list items, one 5-row brief table, longest paragraph 59 words, four plan subsections), and the headings answer the maintainer's standard questions directly, so all six sections read cleanly and navigation is direct. The cost is redundancy rather than density: the copy-only/no-behavior-change boundary is restated five times in graded sections in shifting wording, one plan paragraph bundles portability, scope, and prohibited changes around a buried 'unless separately authorized' condition, and open-question status is split across two headings. Nothing forces re-reading; the reader's main work is reconciling repeated statements of the same constraint.
