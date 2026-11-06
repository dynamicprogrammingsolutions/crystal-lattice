# Task-file readability assessment

- Assessor: `glm-5.3-flash` (effort max) · run `20261029T235235.900097Z-task-guidance-file-readability-tg08-eleventy-contributor-docs-glm-max-s0-0337ace7`
- Assessor config: [glm-assessor-max.json](../../../../shared/configs/glm-assessor-max.json)
- Assessor system message: [glm-assessor-c440c4f661a7.md](../../../../shared/system-messages/glm-assessor-c440c4f661a7.md) (original SHA-256 `6ec0e2a17759b0de…`)
- First judgment's full transcript: [session.md](../../glm-max/assessment/file-readability/s0/session.md) — includes the exact prompt and the raw response; every judgment's transcript lives beside its subject (`<cell>/assessment/file-readability/…`)
- Reviewed target: [tg08-eleventy-contributor-docs](../../target.md)
- Rubric: every top-level section is graded (readable/partial/unreadable) plus whole-file navigation (navigable/partial/confusing), anchored on measured structure facts; findings required for non-top grades; presentation mistakes harvested.

## Judgments

### glm · max (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20261029-contributing-post-authoring-guide.md — Execution plan | partial | 3 |
| tasks/20261029-contributing-post-authoring-guide.md — Requirement questions and decisions | readable | 1 |
| tasks/20261029-contributing-post-authoring-guide.md — Requirements checklist | readable | 2 |
| tasks/20261029-contributing-post-authoring-guide.md — Scope | readable | 1 |
| tasks/20261029-contributing-post-authoring-guide.md — Supporting facts (verified by reading the repo) | readable | 2 |
| _navigation_ | navigable | 2 |

**Findings**

- tasks/20261029-contributing-post-authoring-guide.md — Execution plan — Execution plan → Approach, verification strategy paragraph: Five ordered steps are chained with semicolons inside one ~62-word sentence (the measured longest paragraph), so extracting the sequence takes a re-read. The identical steps reappear as the Task checklist below, forcing the reader to diff two versions to learn which is authoritative. (`Verification strategy: after drafting, run 'npm run build' (expect a clean exit)`)
- tasks/20261029-contributing-post-authoring-guide.md — Execution plan — Execution plan → Approach, drafts bullet: The drafts guidance is specified here, in Requirements checklist item 4, and in Requirement questions and decisions, each with slightly different wording; the reader must cross-check all three to confirm they agree before acting on any one. (`*Drafts*: plain statement that there is no draft flag in this site; a file saved`)
- tasks/20261029-contributing-post-authoring-guide.md — Execution plan — Execution plan → Implementation decisions and open questions: An undecided item sits between two items explicitly marked "Decided"; the labels carry the distinction, but a reader scanning for the decisions must read each item to its tail to learn its status. (`Whether to include a short "checks before you push" line ('npm run build', 'npm `)
- tasks/20261029-contributing-post-authoring-guide.md — Requirement questions and decisions — Requirement questions and decisions, single item: The entire section is one ~70-word bullet carrying the decision, its derivation, its content consequence, and the escalation path. Nothing exceeds a reader's hold at this size, but there is no internal structure to scan. (`Decision (recorded, derived from "no product behavior changes" + current state):`)
- tasks/20261029-contributing-post-authoring-guide.md — Requirements checklist — Requirements checklist, item 4 (drafts): One checkbox item packs the current-state claim, the required phrasing, the practical consequence, and the marker rule — roughly double the load of its sibling items. Still parseable, but it is the one item a reviewer must slow down for. (`There is no draft mechanism implemented today; the text must say so plainly and `)
- tasks/20261029-contributing-post-authoring-guide.md — Requirements checklist — Requirements checklist, item 2: The colon promises a specification, then the sentence pivots to a second verb phrase ("and accurately describes"), so the requirement needs a second read to parse cleanly. (`The section documents creating a post file: Markdown files live in 'content/post`)
- tasks/20261029-contributing-post-authoring-guide.md — Scope — Scope, out-of-scope item: A seven-item exclusion list plus a second, more specific exclusion with a parenthetical rationale share one bullet, and "out of scope" is stated twice. At 60 words the section absorbs this, but the second sentence partially repeats the first instead of extending it. (`Out of scope: code, templates, config, 'package.json' scripts, existing posts, t`)
- tasks/20261029-contributing-post-authoring-guide.md — Supporting facts (verified by reading the repo) — Supporting facts, item 1: Six distinct facts (version plus five config settings) share one bullet — the densest line of the section. The code spans keep it lookup-friendly for a developer, but it is a fact pile rather than a statement. (`Eleventy 3 ('@11ty/eleventy ^3.0.0'). Config ('eleventy.config.js'): input 'cont`)
- tasks/20261029-contributing-post-authoring-guide.md — Supporting facts (verified by reading the repo) — Supporting facts, items 3, 4 and 8: Several bullets mix an observed fact with a writing directive ("must not contradict", "Do not repeat or extend those claims"), so a reader skimming for facts versus rules must separate two registers within the same list. (`Document 'description' as the required convention without claiming it is rendere`)
- navigation — Overall file structure: Headings are specific and match their content, the acceptance gate is bolded in the intro, and plan status sits directly under the Execution plan heading — outcome, constraints, facts, and status are each reachable from structure alone. (`Status: Draft`)
- navigation — Requirement questions and decisions heading: The heading promises questions, but the section holds only a recorded decision; the file's actual open question lives one level deeper under Execution plan → "Implementation decisions and open questions", so a reader hunting open questions must visit two headings. (`## Requirement questions and decisions`)

**Mistakes**

- Execution plan → Approach, verification strategy paragraph: Prose step-chain: a five-step ordered procedure compressed into one sentence with semicolons, then duplicated nearly verbatim as the Task checklist — the reader pays twice, once to parse it and once to reconcile it. (`Verification strategy: after drafting, run 'npm run build' (expect a clean exit)`)
- Requirements checklist item 4 / Requirement questions and decisions / Execution : The drafts rule — current state, consequence, and marker requirement — is stated in three sections with shifting wording; triplication invites divergence and makes the reader cross-check rather than trust any single statement. (`Any target-state draft workflow (e.g. upstream's 'draft: true') may appear only `)
- Requirements checklist, item 2: Broken parallelism after the colon makes a load-bearing accuracy requirement hard to parse on first read. (`The section documents creating a post file: Markdown files live in 'content/post`)
- Supporting facts, item 1: List item mixing several facts: six independent repo facts in one bullet, with no separation between what matters for the guide (output dir, input dir) and incidental detail (head filter, passthrough). (`Config ('eleventy.config.js'): input 'content/', includes '../_includes', output`)
- Requirement questions and decisions heading vs Execution plan → Implementation d: Heading-content mismatch by omission: the section titled for questions contains only a decision, so the file's one genuinely open question is filed under the Execution plan where a reader scanning for open questions may not look. (`Open question for maintainer review (not blocking): if a real draft workflow is `)
- Supporting facts, items 3, 4 and 8: Buried load-bearing rules: prohibitions and writing directives that shape the deliverable are embedded in a list the reader reads as reference facts, rather than surfaced in the requirements checklist where obligations live. (`Do not repeat or extend those claims in the guide; stick to post-authoring facts`)

The file is a competently structured task doc whose smaller sections — Requirements checklist, Scope, Requirement questions and decisions, Supporting facts — are all readable at their measured sizes: short bullets, code spans that aid lookup, and headings that match content. The strain concentrates in the Execution plan (655 words): the verification-strategy paragraph chains five ordered steps through one 62-word sentence and then repeats them as the Task checklist, and the drafts guidance is triplicated across three sections with shifting wording, so the reader must reconcile versions instead of trusting any one. Navigation stays navigable because every kind of content has an accurately labeled home; the only structural detour is that the file's open question sits under the Execution plan rather than in the section titled for questions.


### gpt · high (sample 0)

| Section | Grade | Findings |
|---|---|---:|
| tasks/20261029-add-post-contributor-guide.md — Execution plan | partial | 3 |
| tasks/20261029-add-post-contributor-guide.md — Requirements checklist | readable | 1 |
| tasks/20261029-add-post-contributor-guide.md — Scope | readable | 0 |
| tasks/20261029-add-post-contributor-guide.md — Supporting details | readable | 1 |
| _navigation_ | navigable | 2 |

**Findings**

- tasks/20261029-add-post-contributor-guide.md — Execution plan — Opening paragraph under 'Status: Draft': A 91-word paragraph (36% of the section per the measured facts) packs inspection, accuracy, writing, and scope directives into prose that must be re-read to extract discrete actions — all of which already exist as scannable bullets elsewhere in the file. (`Inspect the current Eleventy behavior and available commands before writing inst`)
- tasks/20261029-add-post-contributor-guide.md — Execution plan — Implementation decisions and open questions — second bullet: Restates the Supporting details caveat and the Task checklist's first item almost verbatim; the same draft-verification instruction recurs roughly five times within this section. (`Open investigation: Verify draft inclusion/exclusion behavior and the exact loca`)
- tasks/20261029-add-post-contributor-guide.md — Execution plan — Requirement verification — first bullet: Restates the acceptance criterion already attached to the Requirements checklist and appends the meta filler 'as requested', adding no new verification content. (`Requirements are accepted by maintainer review against the checklist at the top `)
- tasks/20261029-add-post-contributor-guide.md — Requirements checklist — Fifth checklist item: One checkbox bundles two distinct facts — a scope constraint and the acceptance mechanism — and both are restated later (Scope, Requirement verification), so no single statement reads as canonical. (`Make no product behavior changes; a maintainer review against this checklist is `)
- tasks/20261029-add-post-contributor-guide.md — Supporting details — Fourth bullet: The file's key accuracy caveat is a ~43-word bullet mixing an observation, an instruction, and a prohibition; it carries far more than its one-clause neighbors and is the easiest item to skim past despite being load-bearing. (`No draft behavior was evident in the initial inspection of the Eleventy configur`)
- navigation — Execution plan subsections: The file's only open question sits one heading level below the top-level sections, inside the plan; the explicit heading keeps it findable, but a reader scanning only top-level headings would not know it exists. (`### Implementation decisions and open questions`)
- navigation — Section headings: Two similarly named checklists coexist; the acceptance-bearing one self-identifies in its last item, but the near-duplicate naming costs the reader a moment of disambiguation. (`## Requirements checklist / ### Task checklist`)

**Mistakes**

- Execution plan — opening paragraph: Prose wall: a 91-word paragraph restates in running text what the Requirements checklist and Supporting details already express as bullets, so the reader meets the same instructions twice in different densities and must re-read to separate new information from repetition. (`Keep the guide aligned with supported behavior; if the repository has no draft w`)
- Supporting details / Execution plan intro / Implementation decisions / Task chec: The draft-behavior verification instruction appears roughly five times across the file; repetition dilutes a single load-bearing caveat into noise rather than reinforcing it. (`Verify current draft behavior and local preview command.`)
- Requirements checklist — last item: Checklist item mixes a scope rule with the acceptance mechanism; the same two facts reappear in Scope and Requirement verification, leaving three places that claim to state them. (`Make no product behavior changes; a maintainer review against this checklist is `)
- Requirement verification: Under a heading promising verification, the content is an unperformed to-do plus process restatement — the heading does not match action items that have not happened yet. (`Confirm documentation facts about draft behavior and preview invocation against `)

The task file is short and largely reader-friendly: Requirements checklist is a five-item checkbox list, Scope is a single sentence, and Supporting details are five mostly one-line factual bullets. The Execution plan is the weak spot — its 91-word opening paragraph (36% of the section) restates in dense prose what the checklists already say as bullets, and the draft-behavior caveat recurs about five times across four subsections, so the file never has one canonical statement of its key accuracy constraint. Navigation remains navigable because headings are conventional and self-describing; the redundancy costs re-reading, not getting lost.
