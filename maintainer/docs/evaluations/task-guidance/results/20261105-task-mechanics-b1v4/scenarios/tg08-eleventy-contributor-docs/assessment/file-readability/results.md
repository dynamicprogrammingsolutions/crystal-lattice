# Task-file readability assessment

- Assessor: `glm-5.3-flash` (effort max) · run `20261102T112225.993008Z-task-guidance-file-readability-tg08-eleventy-contributor-docs-glm-max-s0-76233dcd`
- Assessor config: [glm-assessor-max.json](../../../../shared/configs/glm-assessor-max.json)
- Assessor system message: [glm-assessor-c440c4f661a7.md](../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) (original SHA-256 `beebc670f6138d47…`)
- First judgment's full transcript: [session.md](../../glm-max/assessment/file-readability/s0/session.md) — includes the exact prompt and the raw response; every judgment's transcript lives beside its subject (`<cell>/assessment/file-readability/…`)
- Reviewed target: [tg08-eleventy-contributor-docs](../../target.md)
- Rubric: every top-level section is graded (readable/partial/unreadable) plus whole-file navigation (navigable/partial/confusing), anchored on measured structure facts; findings required for non-top grades; presentation mistakes harvested.

## Judgments

### glm · max (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20261102-contributor-post-guide.md — Implementation plan | partial | 4 |
| tasks/20261102-contributor-post-guide.md — Questions and decisions | readable | 2 |
| tasks/20261102-contributor-post-guide.md — Requirements checklist | partial | 3 |
| tasks/20261102-contributor-post-guide.md — Supporting details | readable | 3 |
| _navigation_ | navigable | 2 |

**Findings**

- tasks/20261102-contributor-post-guide.md — Implementation plan — 'Risks and the way back' paragraph: Five distinct facts (primary risk, its mitigation, secondary risk, blast radius, rollback path) are compressed into a semicolon-chained prose paragraph; the reader must re-read to separate risk from mitigation from rollback, the clearest prose wall in the file. (`the main risk is documenting target behavior as current (mitigated by the truthf`)
- tasks/20261102-contributor-post-guide.md — Implementation plan — Verification strategy paragraph vs. Task checklist vs. Requirement verification: The same build/serve/diff verification is spelled out three times in near-identical wording (strategy paragraph, the 'Verify every claim' checkbox, and the 'Claim accuracy' bullet under Requirement verification); the reader must reconcile duplicates to find the authoritative steps, and none of the three adds what the others lack. (`runs 'npx @11ty/eleventy --serve' to confirm the documented preview command work`)
- tasks/20261102-contributor-post-guide.md — Implementation plan — Opening paragraph: This 79-word paragraph restates what Requirements 3-4 and Questions and decisions already establish, spending the section's densest prose on framing rather than new information; the two shorter paragraphs that follow (status line excluded) carry similar per-sentence loads. (`the design constraint shaping the writing is truthfulness: the section covers al`)
- tasks/20261102-contributor-post-guide.md — Implementation plan — 'Additional implementation verification' subsection: A dedicated five-word subsection heading introduces a single footnote-sized item that overlaps the verification content above it, costing the reader a scan for one sentence that could live in the strategy paragraph. (`Run 'npm test' after drafting to confirm the existing archive test is unaffected`)
- tasks/20261102-contributor-post-guide.md — Questions and decisions — First bullet: The question, both options, and its non-blocking status sit in one ~40-word sentence, but the lead-in label and the explicit cross-reference to Requirement 3 let a reader resolve it in a single pass. (`Requirement question (settles framing, not blocking): should 'description' be pr`)
- tasks/20261102-contributor-post-guide.md — Questions and decisions — Whole section: Three bullets, each anchored by a label ('Requirement question', 'Decision', 'Decision'), give the open question and the two scope decisions in 110 words with nothing buried. (`Decision (from "no product behavior changes"): preview is documented with the ex`)
- tasks/20261102-contributor-post-guide.md — Requirements checklist — Checklist item 3 (Front matter): One checkbox chains three separately reviewable claims (title/date, tags, description) plus the marker rule, with a parenthetical nested inside another parenthesis earlier in the same item ('explains 'tags' (the 'posts' tag comes from directory data; extra tags...)'). A maintainer ticking it must hold several conditions at once, and a partially met item cannot be recorded. (`treats 'description' truthfully — no template or the feed consumes it today, so `)
- tasks/20261102-contributor-post-guide.md — Requirements checklist — Checklist item 2 (Creating a post file): Four distinct facts ride in a single ~40-word checkbox; the topic label ('Creating a post file:') keeps it findable, but the multi-claim bundling strains the review-by-item flow the file itself promises ('reviewable item by item without tooling'). (`documents 'content/posts/*.md' as the post location, that posts are Markdown, th`)
- tasks/20261102-contributor-post-guide.md — Requirements checklist — Whole section: The colon lead-ins map cleanly onto the four requested topics, so the 7-item, 281-word checklist remains scannable at the heading level; the strain is inside items 2-4, not in the section's shape. (`- [ ] A new root 'CONTRIBUTING.md' contains a writing-a-post section... - [ ] Cr`)
- tasks/20261102-contributor-post-guide.md — Supporting details — Drafts bullet: This is the densest of the eight bullets, stacking the repo-search result, upstream doc status, the standard pattern, and the site's non-implementation into one sentence; it still parses in one pass because each clause advances the same point. (`Eleventy has no built-in 'draft' key either (its drafts doc pages return 404), s`)
- tasks/20261102-contributor-post-guide.md — Supporting details — Third bullet (post surfaces): The bullet's load-bearing conclusion arrives only after a four-item enumeration of surfaces ('the archive 'content/blog.njk'..., the home page latest list..., the feed..., and — for any additional tag — a generated page'), so a skim for the conclusion can miss it. (`There is no state in which a merged post is hidden.`)
- tasks/20261102-contributor-post-guide.md — Supporting details — Whole section: One fact-cluster per bullet with dated provenance ('source read on 2026-11-02') makes this a reference list a maintainer can quote from directly; the 39 code spans aid precision rather than hurt scanning. (`Posts live in 'content/posts/'. Directory data file 'content/posts/posts.json' s`)
- navigation — Section headings: Each reader goal has an obvious host heading: the outcome in the title and intro ('Create a root 'CONTRIBUTING.md''), the constraints under Requirements checklist, the open question under Questions and decisions, and plan status in the literal 'Status: Draft' first line of Implementation plan. (`## Requirements checklist / ## Questions and decisions / ## Supporting details /`)
- navigation — Implementation plan, 'Implementation decisions and open questions' subsection: The one open question is cross-referenced rather than re-argued, so a reader landing in the plan is pointed back to the authoritative section instead of finding two competing statements. (`Open (review-time framing): 'description' as recommended-but-unused versus targe`)

**Mistakes**

- Requirements checklist, item 3 (Front matter): List item mixing several facts: a semicolon chain makes one checkbox responsible for three independent reviewable claims, so the checklist cannot express partial compliance. (`documents 'title' and an explicit 'date' as what every post needs; explains 'tag`)
- Implementation plan, 'Risks and the way back' paragraph: Prose wall: rollback, execution order, and blast radius are packed into consecutive semicolon-heavy sentences with no list structure, forcing a re-read to extract the actual way back. (`Blast radius is one new untracked file; rolling back is deleting 'CONTRIBUTING.m`)
- Implementation plan (Verification strategy, Task checklist, Requirement verifica: Buried/duplicated load-bearing content: the authoritative verification steps appear three times in slightly different words, so no single location is clearly the checklist a maintainer executes. (`inspect '_site' for the post URL, archive entry, feed entry, and a tag page; run`)
- Implementation plan, 'Additional implementation verification' subsection: Heading does not match its weight: a standalone subsection heading delivers one sentence that duplicates verification content already stated twice above it. (`Run 'npm test' after drafting to confirm the existing archive test is unaffected`)
- Supporting details, third bullet: Buried load-bearing fact: the bullet's conclusion (no merged post can be hidden) follows a four-surface enumeration instead of leading it. (`There is no state in which a merged post is hidden.`)

One file with four conventional sections whose headings match their content; a maintainer can reach the outcome, the constraints, the open question, and the plan status from structure alone, so navigation is clean. Effort concentrates where items are overloaded: three of the seven requirement checkboxes each bundle several verifiable claims into a single tick (front matter alone chains title/date, tags, and description with nested parentheticals), and the Implementation plan is the heaviest section at 508 words, with a 79-word opening paragraph restating settled framing, a five-fact 'Risks and the way back' prose paragraph, and the build/serve/diff verification steps stated three times in near-identical wording. Supporting details is the strongest section — one dated fact-cluster per bullet, directly quotable — and Questions and decisions needs nothing. Splitting the bundled checkboxes and collapsing the duplicated verification text into one authoritative list would lift both partial sections to readable.


### gpt · high (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20261101-add-post-contributor-guide.md — Requirements checklist | readable | 3 |
| tasks/20261101-add-post-contributor-guide.md — Supporting details | readable | 3 |
| _navigation_ | navigable | 3 |

**Findings**

- tasks/20261101-add-post-contributor-guide.md — Requirements checklist — whole section (6 items, longest 14 words): Each of the 82 words sits in a one-requirement-per-item checkbox with parallel phrasing; the section scans in a single pass with nothing to re-read. (`Document the required post front matter fields: 'title', 'date', 'description', `)
- tasks/20261101-add-post-contributor-guide.md — Requirements checklist — item 5: The acceptance condition is its own short item, so the definition of done is visible inside the list rather than buried in preamble prose. (`A maintainer reviews the section against this checklist and accepts it.`)
- tasks/20261101-add-post-contributor-guide.md — Requirements checklist — item 3, cross-referencing Supporting details item 4: The one risky requirement self-flags its verification condition, so the load-bearing caution detailed later is anchored from the checklist too, not only from the details section. (`Explain how drafts work, based on verified current site behavior.`)
- tasks/20261101-add-post-contributor-guide.md — Supporting details — items 1–3: All paths, field names, and script names are code spans (10 across 65 words), so the concrete facts pop out of the bullets without sentence-level parsing. (`'package.json' defines 'build' and 'test' scripts; it does not define a local pr`)
- tasks/20261101-add-post-contributor-guide.md — Supporting details — item 2: Current-state facts map one-to-one onto checklist requirements, letting the maintainer verify each claim against reality without hunting. (`The examples currently show 'title', 'date', and 'tags', but not 'description'.`)
- tasks/20261101-add-post-contributor-guide.md — Supporting details — item 4: The file's only caution is also its densest line at 24 words, packing gap, directive, and prohibition into one bullet; it is still held in a single read, but it strains more than anything else in the file. (`The inspected post examples and configuration do not establish draft behavior. V`)
- navigation — H1 + opening line: The outcome is stated in the first sentence, before any section begins. (`Write a contributor guide section that helps new contributors add and preview a `)
- navigation — section headings: Two accurately labeled H2s cover everything a maintainer needs; at 147 words total, any target — outcome, constraint, open question, acceptance — is at most one heading plus one short list deep. (`## Requirements checklist / ## Supporting details`)
- navigation — checklist item 6 and Supporting details item 4: The scope constraint sits in the checklist where acceptance happens and the sole open question (unverified draft behavior) is the final bullet of the details; both are findable from structure alone. (`Make no product behavior changes.`)

**Mistakes**

- Supporting details, item 4: The single most important constraint is compressed into a three-clause compound bullet; separating the gap, the required verification, and the prohibition would remove the file's only parse-twice sentence at a cost of two lines. (`The inspected post examples and configuration do not establish draft behavior. V`)
- Supporting details, items 1 and 3: Both items join two facts with a semicolon, a denser granularity than the one-fact-per-item checklist above; impact is low because each stays under 20 words. (`Post source files are under 'content/posts/'; the existing examples are 'content`)

A 147-word, two-section task file. The checklist is six uniform checkboxes of at most 14 words with the acceptance gate stated in-list, and Supporting details is four bullets whose paths, fields, and scripts all surface as code spans. The only strain is the final 24-word compound bullet carrying the draft-behavior caution — the file's load-bearing constraint — which is denser than its surroundings but graspable in one pass. Navigation is trivial from structure: the H1 states the deliverable, the two H2 headings are accurate, and the constraint and open question are each one short list deep.
