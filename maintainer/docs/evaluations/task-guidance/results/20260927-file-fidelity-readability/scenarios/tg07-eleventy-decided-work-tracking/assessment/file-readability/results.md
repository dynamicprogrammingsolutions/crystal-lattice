# Task-file readability assessment

- Assessor: `glm-5.3-flash:cloud` (effort max) · run `20260928T214101.708863Z-task-guidance-file-readability-tg07-eleventy-decided-work-tracking-glm-max-s0-3cd1eea5`
- Assessor config: [glm-assessor-max.json](../../../../shared/configs/glm-assessor-max.json)
- Assessor system message: [glm-assessor-3d0be6dc03e9.md](../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) (original SHA-256 `8eb74d8935ed0d6b…`)
- First judgment's full transcript: [session.md](../../glm-max/assessment/file-readability/s0/session.md) — includes the exact prompt and the raw response; every judgment's transcript lives beside its subject (`<cell>/assessment/file-readability/…`)
- Reviewed target: [tg07-eleventy-decided-work-tracking](../../target.md)
- Rubric: every top-level section is graded (readable/partial/unreadable) plus whole-file navigation (navigable/partial/confusing), anchored on measured structure facts; findings required for non-top grades; presentation mistakes harvested.

## Judgments

### glm · max (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-blog-archive-fifteen-per-page.md — Facts and supporting details | readable | 2 |
| tasks/20260926-blog-archive-fifteen-per-page.md — Open requirement questions | partial | 2 |
| tasks/20260926-blog-archive-fifteen-per-page.md — Requirements checklist | readable | 2 |
| _navigation_ | navigable | 2 |

**Findings**

- tasks/20260926-blog-archive-fifteen-per-page.md — Facts and supporting details — Facts and supporting details, item 1: Items pack several facts each (about five in this one), but the 'Current archive:' / 'Interpretation of the request:' lead-ins plus 12 code spans make file references stand out, so a maintainer can scan to the relevant fact at 140 words / 4 items without re-reading. (`Current archive: 'content/blog.njk' (permalink '/blog/') renders the entire 'col`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Facts and supporting details — Facts and supporting details, item 3: The scope boundary gets its own 26-word labeled item, so a reader confirming what is excluded from the decision finds it at a glance. (`- Interpretation of the request: the change applies to the blog archive listing `)
- tasks/20260926-blog-archive-fifteen-per-page.md — Open requirement questions — Open requirement questions, list item: The entire section is one 61-word item; the two candidate answers sit mid-sentence after an em-dash inside the question, so the reader must parse a compound sentence instead of scanning to enumerate the options the design conversation must choose between. (`what does the archive do about posts beyond the first fifteen — omit them from t`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Open requirement questions — Open requirement questions, list item, closing sentence: The stakes and the resolution venue ride on the tail of the same item, so the load-bearing context is reached only after working through the options clause; separate bullets for question, options, and why-it-matters would remove the strain. (`The answer changes the required outcome and is to be resolved in the design conv`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Requirements checklist — Requirements checklist, item 1: All four items carry exactly one requirement each and top out at 22 words, so the decided outcome and its three constraints can be scanned and ticked off in a single pass. (`- [ ] The blog archive shows fifteen posts per page instead of one long list of `)
- tasks/20260926-blog-archive-fifteen-per-page.md — Requirements checklist — Requirements checklist, item 4: The scope boundary, its precise extent, and the deferral rationale are paired in one short item without any part burying another; the parenthetical earns its place. (`- [ ] Deeper pagination (archive pages beyond the first, and any navigation betw`)
- navigation — Section headings vs. content: Each heading literally names a thing a maintainer comes for — the outcome, the open question, the supporting facts — so every target is one heading away with no mismatch between title and body. (`## Requirements checklist / ## Open requirement questions / ## Facts and support`)
- navigation — File intro, second paragraph: Plan status, the most-queried fact in a tracking file, is stated in the second paragraph before any section begins, so the reader finds it without scanning the body. (`Planning is intentionally on hold: the execution plan is to be written after the`)

**Mistakes**

- tasks/20260926-blog-archive-fifteen-per-page.md — Open requirement questions: One list item mixes four distinct facts — question topic, the deferral constraint, both candidate answers, and stakes plus resolution venue — so none of them can be scanned; this single item is the only dense stretch in the file. (`Interim handling of older posts: with deeper pagination deferred, what does the `)
- tasks/20260926-blog-archive-fifteen-per-page.md — Facts and supporting details, : The load-bearing fact — today's fixtures cannot demonstrate the decided page size — is embedded mid-item between the file names and the design-conversation implication, so a scanning reader can miss the point the decision's validation depends on. (`Fact: current fixture content is two posts ('content/posts/first.md', 'content/p`)

A ~300-word tracking file that is easy to work with overall. The requirements checklist is four one-requirement items of at most 22 words, and the facts section is four labeled items whose 12 code spans keep file references findable; both grade readable. The one strain point is the open-question section, whose entire content is a single 61-word item packing the question, both candidate answers, the stakes, and the resolution venue — the source of both presentation mistakes. Navigation is direct from structure alone: the three headings name exactly what a reader comes for, and the plan status ('planning is intentionally on hold') is stated in the intro before any section.


### glm · max (sample 1)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-blog-archive-fifteen-per-page.md — Approved scope decision | readable | 1 |
| tasks/20260926-blog-archive-fifteen-per-page.md — Open questions (resolve in the scheduled design conversation) | readable | 2 |
| tasks/20260926-blog-archive-fifteen-per-page.md — Requirements checklist | readable | 2 |
| tasks/20260926-blog-archive-fifteen-per-page.md — Supporting details | readable | 2 |
| _navigation_ | navigable | 2 |

**Findings**

- tasks/20260926-blog-archive-fifteen-per-page.md — Approved scope decision — Approved scope decision, single bullet: The section's entire 41-word budget sits in one item carrying the decision, the prohibition, and the escalation path; it is the file's most bundled item but reads as one continuous rule in a single pass. (`Deeper pagination is deliberately deferred until we see how fifteen-per-page fee`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Open questions (resolve in the scheduled design conversation) — Open questions, first bullet: The section's 88 words concentrate in this multi-sentence item, which folds the question, both readings, the stakes, and the resolution rule into one block; it is the file's only read-don't-scan stretch, kept workable because the question is front-loaded and the rationale is exactly what the design conversation needs. (`"Fifteen per page" implies further pages, while deferring "deeper pagination" co`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Open questions (resolve in the scheduled design conversation) — Open questions, second bullet: Correctly scoped as a conditional follow-on, so the dependency between the two open items is explicit rather than implied. (`If older posts stay reachable: how readers navigate to them (URLs, links) is par`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Requirements checklist — Requirements checklist, items 1–3: One fact per short item across the section's 57 words and four parallel requirements; a maintainer takes in the whole outcome contract in a single pass. (`'/blog/' remains the archive entry point at the same URL.`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Requirements checklist — Requirements checklist, item 4: The longest item states the constraint and names both affected views in one line; the four unchecked boxes are genuinely pending work consistent with the status line's deferral, not a stale wall of boxes. (`Other consumers of the shared post-list partial ('content/index.njk' homepage, '`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Supporting details — Supporting details, bullet 2: One codebase fact per item with file paths as code spans, so a maintainer goes straight to the component that owns ordering without re-reading prose. (`Eleventy collections sort date-ascending, so the reverse is what produces newest`)
- tasks/20260926-blog-archive-fifteen-per-page.md — Supporting details — Supporting details, bullet 3: Restates checklist item 4 with the concrete per-view behavior (latest three via '| head(-3)', full list per tag); the repetition serves a different reading pass and obscures nothing. (`so the archive change must not leak into those views.`)
- navigation — Preamble status line, above the first heading: The file's most load-bearing instruction sits in the unheaded preamble, but at the top of a one-screen file it is the first thing read, so plan status is found immediately. (`do not plan or execute from this file until that conversation has happened and a`)
- navigation — Section headings: All four headings name their content — here even where the item gets resolved — so outcome (title line), constraints (checklist and scope decision), open questions, and status each have one obvious address. (`Open questions (resolve in the scheduled design conversation)`)

A one-screen tracking file: all four graded sections are short bullet lists (41–96 words per the measured facts) with headings that match their content, so a maintainer can take in the decided change, its guardrails, and its open questions in one pass. The only density is the first open-question item, where the section's words concentrate into a multi-sentence block; it stays readable because the question is front-loaded and its rationale is precisely what the deferred design conversation needs. Navigation is immediate: the 'do not plan yet' gate opens the file and every reader goal — outcome, constraints, open questions, plan status — has a named address. The explicit hunt for presentation mistakes (prose walls, multi-fact items, buried load-bearing facts, mismatched headings, walls of unchecked boxes) found nothing misrepresented; the four unchecked boxes accurately reflect work that has not started.


### gpt · high (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-blog-archive-pagination.md — Requirements checklist | readable | 2 |
| tasks/20260926-blog-archive-pagination.md — Supporting details | readable | 2 |
| _navigation_ | navigable | 2 |

**Findings**

- tasks/20260926-blog-archive-pagination.md — Requirements checklist — Requirements checklist, items 1–3: Three checkboxes of 5–8 words, one decided fact each (page size, entry URL, ordering), consistent with the measured 4 items and 11-word longest item; the reader absorbs the core decisions in a single pass with nothing to re-read. (`The blog archive displays fifteen posts per page. · '/blog/' remains the archive`)
- tasks/20260926-blog-archive-pagination.md — Requirements checklist — Requirements checklist, item 4: The load-bearing scope boundary is stated in place inside the checklist, where a reader looks for constraints, rather than buried in prose; it is the list's one multi-clause item (deferral + rationale + scope statement) and the only spot that breaks the one-fact-per-box rhythm, though it still reads in one glance. (`Deeper pagination is deferred until the team has observed how the fifteen-post a`)
- tasks/20260926-blog-archive-pagination.md — Supporting details — Supporting details, item 1: The framing that changes how the entire file is read (decision record vs. work order) is given its own short bullet instead of being folded into a paragraph, so the plan status is unambiguous immediately. (`This task records an approved product decision, not an implementation plan.`)
- tasks/20260926-blog-archive-pagination.md — Supporting details — Supporting details, item 2: Names the open question (representation beyond the initial page) and its home (the scheduled design conversation) in a single bullet; at 2 items / 33 words the section is short but loses nothing — brevity here is complete, not thin. (`Implementation design, including how pagination should be represented beyond the`)
- navigation — H2 headings: The two headings map directly onto a maintainer's likely questions — constraints under the first, status and open-question routing under the second — so the outcome, the scope constraint, and the plan status are each reachable from structure alone in a ~90-word file. (`## Requirements checklist / ## Supporting details`)
- navigation — Intro line under the H1: Answers 'is this work to do or a record?' before any section begins, which matters because the H1 ('Paginate the blog archive') on its own would read as an implementation task. (`Track the decided change to the blog archive for implementation after the schedu`)

**Mistakes**

- Requirements checklist, item 4: A decided scope exclusion is rendered as an unchecked requirement box: a maintainer ticking through the checklist sees a settled 'not in scope' as pending work, and the item mixes the deferral, its rationale, and the scope statement in one bullet. It would read unambiguously as a non-actionable statement under Supporting details, or as a plain unboxed scope note. (`Deeper pagination is deferred until the team has observed how the fifteen-post a`)

A ~90-word, two-section tracking record that is easy to work with. 'Requirements checklist' (54 words, 4 boxes, 11-word longest item) states one decision facet per checkbox — page size, entry URL, ordering, and the scope boundary stated in place — and 'Supporting details' (33 words, 2 bullets) front-loads the decision-not-plan framing and routes the open design question to the scheduled conversation. Nothing requires re-reading, so both sections are readable and navigation is direct. The single blemish is the scope-deferral statement dressed as an unchecked requirement in the checklist, which a reader working the boxes could mistake for pending work; it is the file's one mixed-fact, mismatched-item moment.
