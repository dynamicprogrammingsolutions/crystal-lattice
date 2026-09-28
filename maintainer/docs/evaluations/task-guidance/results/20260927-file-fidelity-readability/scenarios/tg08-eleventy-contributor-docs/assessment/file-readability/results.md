# Task-file readability assessment

- Assessor: `glm-5.3-flash:cloud` (effort max) · run `20260928T214648.703654Z-task-guidance-file-readability-tg08-eleventy-contributor-docs-glm-max-s0-c4c2b983`
- Assessor config: [glm-assessor-max.json](../../../../shared/configs/glm-assessor-max.json)
- Assessor system message: [glm-assessor-3d0be6dc03e9.md](../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) (original SHA-256 `b11a662234a3edff…`)
- First judgment's full transcript: [session.md](../../glm-max/assessment/file-readability/s0/session.md) — includes the exact prompt and the raw response; every judgment's transcript lives beside its subject (`<cell>/assessment/file-readability/…`)
- Reviewed target: [tg08-eleventy-contributor-docs](../../target.md)
- Rubric: every top-level section is graded (readable/partial/unreadable) plus whole-file navigation (navigable/partial/confusing), anchored on measured structure facts; findings required for non-top grades; presentation mistakes harvested.

## Judgments

### glm · max (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-contributing-guide-add-post.md — Execution plan | partial | 3 |
| tasks/20260926-contributing-guide-add-post.md — Open requirement questions | readable | 2 |
| tasks/20260926-contributing-guide-add-post.md — Requirements checklist | partial | 3 |
| tasks/20260926-contributing-guide-add-post.md — Supporting details | readable | 2 |
| _navigation_ | navigable | 3 |

**Findings**

- tasks/20260926-contributing-guide-add-post.md — Execution plan — Design paragraph: The plan's core artifact — the intended guide structure — is a ~120-word single sentence built from nested parentheticals; the bolded subsection names aid a skim, but the per-subsection detail must be re-read to hold. (`Design: one new file, 'CONTRIBUTING.md', containing one section ("Add a post") w`)
- tasks/20260926-contributing-guide-add-post.md — Execution plan — Ordered steps, step 4: Five commands and four distinct verification checks are chained in one list item; matching each check to its command takes parsing effort despite the arrow notation. (`Validate every documented step end-to-end in a temp copy: 'npm install'; create `)
- tasks/20260926-contributing-guide-add-post.md — Execution plan — Plan subsections (Implementation decisions / Documentation / Task checklist / Re: The rest of the section is well decomposed — five short labeled subsections with one-point bullets, and the status line placed directly under the heading — which keeps the plan workable despite the Design paragraph's density. (`Status: Draft`)
- tasks/20260926-contributing-guide-add-post.md — Open requirement questions — Draft framing item and closing line: Question, default answer with its caveat, alternative, and blocking status are delivered in three short nested bullets plus one line; the reader takes in the whole decision state in a single pass. (`**Recommendation:** document the no-config workflow — keep unfinished posts outs`)
- tasks/20260926-contributing-guide-add-post.md — Open requirement questions — Alternative bullet, trailing clause: A third option is appended to the bullet labeled 'Alternative', so two framings share one label; a minor wobble that does not force re-reading. (`— or defer hidden drafts entirely to a separate follow-up task`)
- tasks/20260926-contributing-guide-add-post.md — Requirements checklist — Drafts checklist item: One checkbox packs five distinct acceptance facts (framing dependency, no built-in support, keep-outside workflow, hidden-vs-public behavior, banned mechanisms) into a single multi-clause sentence; the load-bearing public-URL/sitemap caveat sits mid-item inside a parenthetical, so a reviewer must re-read to extract what to check. (`there is no built-in draft support; unfinished posts are kept outside 'content/p`)
- tasks/20260926-contributing-guide-add-post.md — Requirements checklist — Front matter checklist item: Bundles a convention requirement, a negative rendering claim, and its justification in one clause inside a long item; the 'no template consumes it today' limit decides what the guide may assert yet is easy to miss while scanning the field list. (`'description' is required by convention but the guide makes no claim about it re`)
- tasks/20260926-contributing-guide-add-post.md — Requirements checklist — Second checklist item (post location and tags): Three independently verifiable content requirements (file location, inherited layout/tag, custom-tag behavior) share one checkbox behind nested 'that' clauses with no visual separation. (`that 'layout' and the base 'posts' tag are provided by 'content/posts/posts.json`)
- tasks/20260926-contributing-guide-add-post.md — Supporting details — Verified draft behavior: One probe result per bullet, with the visible/hidden contrast stated once and anchored to a concrete file; the evidence is scannable and directly usable when writing the guide. (`A file outside 'content/posts/' (e.g., 'content/drafts/wip.md') is built to a pu`)
- tasks/20260926-contributing-guide-add-post.md — Supporting details — Repo facts, tag pages bullet: Two related facts share a bullet, but the semicolon split and inline *verified* anchor keep it one readable line; the section's one-fact-per-bullet pattern holds throughout. (`Tag pages are generated per custom tag at '/tags/<slug>/'; the built-in 'posts' `)
- navigation — Top-level heading sequence: The four things a maintainer looks for — acceptance gate, unsettled decision, evidence, plan status — each map to one H2 in reading order, and the intro paragraph states the deliverable (new 'CONTRIBUTING.md', docs-only, maintainer review) before any of it. (`## Requirements checklist → ## Open requirement questions → ## Supporting detail`)
- navigation — Supporting details sub-groups: Sub-groups are bold list lead-ins rather than headings, so they do not surface in heading-based navigation; a reader scanning headings sees only the generic 'Supporting details' and must open the section to discover it holds the verified evidence. (`**Repo facts** / **Verified draft behavior** / **Verified preview behavior** / *`)
- navigation — Requirements checklist vs Task checklist: Two similarly named checklists coexist (acceptance gate vs executor to-dos); the cross-reference 'mark the requirements checklist items with evidence' disambiguates only after reading, so a skimming reader can briefly act on the wrong list. (`## Requirements checklist ... ### Task checklist`)

**Mistakes**

- Execution plan, Design paragraph: Prose wall: ~120 words in one sentence carrying the entire intended guide structure as nested parentheticals instead of a short list; the single densest spot in the file. (`four subsections matching the request: **Create the post file** (...), **Front m`)
- Requirements checklist, drafts item: Wall-like list item mixing several facts, with the load-bearing 'drafts are not private on this site' caveat buried inside a mid-item parenthetical. (`it states plainly what that does and does not hide (absent from archive, feed, a`)
- Requirements checklist, front matter item: Buried load-bearing fact: the prohibition on claiming any rendering for 'description' rides inside a long item, so a reviewer skimming the field list could accept a guide that over-claims. (`'description' is required by convention but the guide makes no claim about it re`)
- Requirements checklist, second item: List item that mixes three separately verifiable content requirements behind nested 'that' clauses. (`that 'layout' and the base 'posts' tag are provided by 'content/posts/posts.json`)
- Execution plan, Ordered steps step 4: One list item chains five commands and four checks; as a single step it is hard to hold or tick off. (`'npm install'; create a post exactly as the guide says → confirm ...; run the do`)
- Open requirement questions, Alternative bullet: Item mixes two distinct options (add a marked target-state note; defer to a follow-up task) under one 'Alternative' label, so the reader must reconstruct that three framings actually exist. (`**Alternative:** additionally include a target-state note ... — or defer hidden `)
- Requirements checklist vs Execution plan → Task checklist: Near-colliding headings: the review gate and the executor to-do list differ by one word and sit far apart, inviting a reader to check off the wrong list. (`## Requirements checklist ... ### Task checklist`)

Navigation is this file's strength: the deliverable is stated in the opening paragraph, and the acceptance gate, the single open question, the verified evidence, and plan status each have an obvious heading-level home ('Open requirement questions', 'Supporting details', 'Status: Draft' under 'Execution plan'), with Supporting details delivering one verified fact per bullet. The strain concentrates in two areas: two wall-like acceptance items (drafts, front matter) that bundle several facts and bury the load-bearing caveat that drafts still build to a public URL and appear in the sitemap, and the Execution plan's ~120-word Design sentence plus the five-command step 4. Everything remains workable with reasonable effort; only the draft-framing answer blocks execution, and locating it is easy.


### gpt · high (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20260926-contributor-guide-posts.md — Execution plan | readable | 3 |
| tasks/20260926-contributor-guide-posts.md — Requirements checklist | readable | 2 |
| tasks/20260926-contributor-guide-posts.md — Research and supporting facts | readable | 2 |
| tasks/20260926-contributor-guide-posts.md — Unresolved requirement questions | readable | 1 |
| _navigation_ | navigable | 3 |

**Findings**

- tasks/20260926-contributor-guide-posts.md — Execution plan — Four subsections: Four labeled subsections of 3-6 short items each (measured longest item 15 words) break the section's 382 words into independently scannable chunks; a reader can jump straight to decisions, documentation scope, the task list, or the verification mapping. (`### Implementation decisions and open questions`)
- tasks/20260926-contributor-guide-posts.md — Execution plan — Intro paragraph 2: This prose paragraph restates the Unresolved requirement questions section almost in full, so the reader meets the same open decision twice within about 120 words. (`The draft behavior is the only material documentation decision still open: the i`)
- tasks/20260926-contributor-guide-posts.md — Execution plan — Requirement verification list: Six bullets mirror the Requirements checklist item-by-item; the mapping of requirement to acceptance method is useful, but the reader must diff two parallel lists by eye to confirm nothing was added or dropped. (`Post location and file creation: maintainer review confirms the guide names 'con`)
- tasks/20260926-contributor-guide-posts.md — Requirements checklist — Checklist item 4 (draft workflow): The densest item packs the workflow mechanics, the local-inspection requirement, the maintainer-approval constraint, and the no-unsupported-flag warning into two sentences; the reader slows here, but at ~44 words it still parses in one pass, so the section stays readable. (`Explain the repository-supported draft workflow, including how a draft is kept o`)
- tasks/20260926-contributor-guide-posts.md — Requirements checklist — Checklist items 1-3 and 5-7: Six of the seven items carry one requirement each at roughly 10-24 words, so the acceptance criteria scan as a single screen and can be re-checked item-by-item without re-reading. (`Give the exact local preview command, identify the local URL or output to inspec`)
- tasks/20260926-contributor-guide-posts.md — Research and supporting facts — Bullet 1: Six one-fact bullets with inline code spans make the repository evidence scannable and directly verifiable; this is the easiest section in the file to hold. (`The Eleventy input directory is 'content'; post files are currently stored in 'c`)
- tasks/20260926-contributor-guide-posts.md — Research and supporting facts — Bullet 5 (package.json): This bullet switches from stating a fact (no preview script) to issuing two instructions, so evidence and plan content mix in a section titled as research. (`The guide should use the local Eleventy CLI's serve mode and have the maintainer`)
- tasks/20260926-contributor-guide-posts.md — Unresolved requirement questions — The section's single bullet: The decision, both options, and a concrete example are compressed into one ~60-word bullet with the example buried mid-parenthetical; at 65 total words the reader recovers it in one pass, but this bullet is where the section's whole effort concentrates. (`a maintainer must approve either the current limitation and its contributor work`)
- navigation — Heading 'Unresolved requirement questions': The file's only open question has a dedicated, explicitly named section near the top, so a reader hunting for open questions finds it without scanning prose. (`What draft workflow should 'CONTRIBUTING.md' describe?`)
- navigation — Execution plan, opening line: Plan status is stated on its own line at the top of the plan, making the state of the work findable at a glance. (`Status: Draft`)
- navigation — Requirements checklist item 7: The outcome and the acceptance criterion sit in the first section, so a reader landing at the top of the file immediately learns what 'done' means and where the constraints live. (`Obtain maintainer review against every checklist item above; that review is the `)

**Mistakes**

- Requirements checklist item 4: One checkbox bundles four separable facts (exclusion mechanics, local inspection, approval dependency, no unsupported flags); splitting it would let a maintainer tick each acceptance condition independently instead of untangling one item during review. (`Explain the repository-supported draft workflow, including how a draft is kept o`)
- Unresolved requirement questions, Execution plan intro, Implementation decisions: The same pending draft-workflow decision is stated four times in different words ('What draft workflow should 'CONTRIBUTING.md' describe?', 'The draft behavior is the only material documentation decision still open', this bullet, and 'Resolve the draft-workflow question with a maintainer.'); the reader must collect all copies to be sure exactly one question is open, and future edits risk the copies diverging. (`Do not document 'draft: true' or any other draft flag as functional until a main`)
- Requirement verification list vs Requirements checklist: The acceptance criteria exist as two parallel lists that restate each other item-by-item; nothing ties a verification bullet to its checklist number, so the reader cross-checks by eye and must keep both lists synchronized in any future edit. (`Front matter: maintainer review confirms all four required fields are shown and `)
- Research and supporting facts, bullet 5: An action item directed at the maintainer sits in the evidence section (heading says 'facts'), duplicating the Task checklist's 'Verify the preview command against the local Eleventy installation.'; the reader meets the instruction in the wrong section first. (`The guide should use the local Eleventy CLI's serve mode and have the maintainer`)

A ~730-word task file that is easy to work with: all four sections are list-driven with short, code-anchored items (measured longest item 15 words), subsections in the Execution plan chunk its 382 words into labeled, independently scannable lists, and every reader goal has an obvious home — acceptance criteria in the Requirements checklist, the single open decision under Unresolved requirement questions, plan state in the 'Status: Draft' line. The residual costs are redundancy rather than density: the draft-workflow decision is restated in four places, Requirement verification mirrors the checklist as a second unlinked list, and two items (the drafts checklist entry, the package.json research bullet) bundle several facts where one-per-item would be easier to act on. A reader's effort goes to reconciling duplicates, not to re-reading prose.
