Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCFLOW-001`, `DOCFLOW-004`–`DOCFLOW-006`

# Contributing and AI-Assisted Development Workflow

Create an easy-to-follow root `CONTRIBUTING.md` that explains a practical,
risk-scaled AI-assisted development workflow, clearly distinguishes human
ownership from AI implementation and review, and includes concise example
prompts that rely on standing repository guidance.

## Requirements checklist

- [ ] Root `CONTRIBUTING.md` is the concise contributor entry point for the
  recommended development workflow.
- [ ] The guide is organized around what a human initiates, reviews, questions,
  decides, verifies, accepts, and authorizes when AI produces the detailed
  plans, code, tests, and documentation.
- [ ] The guide begins with a short six-step quick workflow that is easy to
  scan and follow.
- [ ] Small, normal, and high-risk changes all follow planning,
  implementation, verification, and review, while the form and detail of the
  plan vary with the work.
- [ ] Every initial change and follow-up is planned before implementation.
- [ ] Specification need is considered independently from immediate change
  size: affected existing specifications are updated when their target
  changes, large new features require specifications, and other work may
  justify specifying an existing feature or durable contract.
- [ ] Current user documentation is updated whenever a change affects a
  consumer.
- [x] Human owner, implementing agent, and reviewing agent responsibilities are
  defined once near the beginning.
- [x] Each major workflow step identifies only the owner or collaboration
  relevant to that step; the guide does not force both human and AI work into
  every stage.
- [x] Manual verification is defined as work actually performed or directly
  confirmed by a human.
- [x] AI review is advisory and cannot complete a human-verification or
  acceptance requirement.
- [x] The guide distinguishes automated verification, manual testing,
  implementing-agent self-review, independent AI review, final human review,
  and human delivery authorization.
- [ ] The guide explains that applicable `AGENTS.md` and task guidance must
  actually reach the model through its developer/system message or first user
  message and shows humans how to inspect the effective instructions.
- [ ] The guide explains which context belongs in the developer/system message,
  `AGENTS.md`, `TASKS-v7`, package docs, specifications, and task-specific user
  prompts.
- [ ] Planning begins with a brainstorming process whose realistic freehand
  prompt combines intent, high-level context, requested research or
  suggestions, uncertainty, and additional details.
- [ ] Inline workflow prompts cover brainstorming, specification/task
  creation, subtask planning, approved implementation, manual-test preparation,
  independent review, findings resolution, follow-up planning, and authorized
  commit.
- [ ] Example prompts assume repository guidance is already active and do not
  restate generic coding, testing, documentation, or task-file rules.
- [ ] Human review questions appear at the relevant workflow stages and focus
  on scope, decisions, evidence, and remaining uncertainty rather than
  mechanical bookkeeping.
- [ ] Unit, integration, end-to-end, and manual evidence are prominent; the
  guide assumes AI creates and runs automated tests while humans review the
  planned boundaries and reported results.
- [ ] The guide gives humans a clear conceptual model of specifications,
  requirements, tasks, execution plans, current user documentation, and current
  implementation documentation, with links and a compact worked example.
- [ ] A separate follow-up section requires investigation, planning,
  specification reconsideration, consumer-documentation review, verification,
  and human approval before follow-up implementation and delivery.
- [x] Commit authorization remains explicit; describing commit as the final
  stage does not grant an agent permission to commit.
- [x] The guide links to the documentation structure, specification standard,
  task guidance, and package-specific development entry points instead of
  duplicating all commands.
- [x] Supporting online references are preserved in a compact further-reading
  or rationale section without interrupting the main workflow.
- [ ] The frontend and terminal setting paths for including task guidance are
  documented.
- [ ] The system-message feature exposes a session action that compiles the
  effective developer/system message on demand and presents it in a dialog
  through supported frontends.
- [ ] The OpenAI inspection proxy supports an optional `--hide-headers` flag
  that suppresses all request-header logging without changing forwarding, and
  the guide recommends the flag while explaining that users remain responsible
  for secrets and sensitive request content on their own computers.
- [ ] The system-message feature, affected frontend paths, and inspection proxy
  package documentation describe the new behavior.

## Supporting details

### Readability principle

The guide is practical documentation, not a formal process specification.

Prefer:

- a quick summary before detailed explanation;
- six major steps rather than a long sequence of micro-stages;
- roles defined once;
- short owner labels;
- optional or conditional activities called out as such;
- prompt examples placed at the workflow stages where a human uses them;
- compact human review checklists;
- links to detailed standards instead of repeating them.
- enough explanation, examples, illustrations, and code blocks to make the
  workflow easy for a human to understand and apply. Focus and perceived
  reading effort matter more than minimizing the source line count.

Avoid:

- a role matrix under every step;
- requiring both human and AI work in every stage;
- presenting optional AI review or manual testing as mandatory for a trivial
  change;
- burying the workflow under research citations;
- prompts that repeat the full developer message.

### Roles

Define these once near the beginning:

- **Human owner:** Defines intent, resolves requirement questions, approves
  plans, performs human verification, reviews the result, and authorizes
  delivery.
- **Implementing agent:** Investigates, plans, implements, runs automated
  verification, updates documentation and work records, and prepares evidence.
- **Reviewing agent:** Independently inspects the proposed change and reports
  findings. It does not approve the change.

The same human may be both owner and reviewer for small work. The activities
remain distinct even when performed by one person.

### Recommended document structure

```text
# Contributing

1. Quick workflow
2. Choose the appropriate process
3. Make sure the agent received the project instructions
4. Human-led AI-assisted workflow with inline prompts
5. Planning and reviewing follow-up changes
6. Understand specifications, tasks, plans, docs, and evidence
7. Repository and pull-request essentials
8. Further reading
```

## First implementation workflow reference

The following workflow records the direction used for checkpoint
`4c476620377343fbc93401f2493becafe9684d75`. Human review superseded its
agent-centric presentation, detached prompt catalog, and size-linked
specification framing. The current target is defined by the requirements near
the top of this task and the Draft follow-up execution plan below. Retain this
section only as context for comparing the first checkpoint with the follow-up;
do not use it as the current writing direction.

### 1. Shape the change

**Owner:** Human-led, with AI assistance.

Clarify:

- the problem and intended outcome;
- who is affected;
- goals and non-goals;
- constraints and compatibility expectations;
- unknowns and requirement questions;
- whether the change is small, normal, or high-risk.

The agent may inspect relevant documentation and code, identify missing
context, and compare materially different approaches. It does not implement
during this step.

**Output:** An agreed problem statement, scope, and set of open questions.

This is the workflow stage where a longer initial prompt is often appropriate
because the human may need to provide product or domain context that is not in
the repository.

### 2. Record and decompose the work

**Owner:** AI drafts; human approves material scope and requirements.

Depending on the change:

- create or update product, technical, and requirements specifications;
- create a single task or a main task with subtasks;
- link tasks to specification requirements;
- record dependencies and ownership;
- preserve unresolved questions;
- avoid detailed plans for distant subtasks whose implementation depends on
  earlier discoveries.

Small changes may skip durable specifications and use only a task or agreed
conversational scope.

**Output:** Durable specifications when needed and a reviewable task
decomposition.

### 3. Plan and approve the next subtask

**Owner:** AI plans; human approves.

The implementing agent:

- reads the task, parent, dependencies, and linked specifications;
- inspects the relevant current implementation;
- writes a Draft execution plan for one executable subtask;
- defines implementation boundaries, risks, documentation, automated tests,
  and applicable manual verification;
- does not implement before approval.

The human reviews requirement coverage, scope, contracts, compatibility,
security, persistence, migration, testing realism, and human-verification
needs.

**Output:** An approved execution plan for the next subtask.

### 4. Implement and verify

**Owner:** Implementing agent.

The agent:

- implements the approved plan through coherent checkpoints;
- adds or updates tests as behavior changes;
- runs focused verification during implementation;
- runs required package, integration, type, lint, and build checks before
  completion;
- updates task state and implementation notes;
- updates living specifications when discoveries change the design;
- stops for human input if requirements or material decisions must change;
- reviews the complete diff before presenting the result;
- does not commit unless explicitly authorized.

A checkpoint is a coherent implementation and verification state. It does not
necessarily imply a Git commit.

**Output:** An implemented change with automated verification evidence and
updated task/specification state.

### 5. Validate and review

**Owner:** Depends on the activity.

This step contains distinct activities. Not every change requires all of them.

#### Manual testing — human, when applicable

Use manual testing for meaningful user-visible or operational boundaries such
as UI behavior, CLI workflows, installation, upgrades, real-device behavior,
external service integration, accessibility, visual behavior, or recovery
procedures.

The agent may prepare the checklist. Only a human can record the step as
manually verified.

For changes without a meaningful manual boundary, record `Not applicable` with
a short reason.

#### Independent AI review — recommended for normal and high-risk changes

A reviewing agent inspects requirements, specifications, plan, implementation,
tests, evidence, security, compatibility, failure behavior, documentation, and
unnecessary complexity.

It reports findings but does not approve the change. Independent AI review may
be skipped for very small changes when its cost exceeds its value.

#### Final human review — required before acceptance

The human reviewer evaluates:

- whether the intended outcome was achieved;
- whether implementation matches accepted scope;
- whether tests themselves are meaningful;
- automated and manual evidence;
- AI-review findings and their disposition;
- security, compatibility, and operational risk where applicable;
- documentation and migration guidance;
- unrelated or accidental changes.

**Output:** Accepted/rejected findings and a human acceptance decision.

### 6. Address findings and deliver

**Owner:** AI addresses accepted findings; human authorizes delivery.

The implementing agent:

- fixes accepted findings;
- updates tests, documentation, specifications, and task evidence;
- reruns affected verification;
- reports limitations or blocked checks;
- adds completion notes when the task is complete.

The human:

- confirms unresolved findings are acceptable;
- completes remaining human-verification requirements;
- authorizes a commit, PR, or merge.

The agent may commit only when explicitly authorized.

**Output:** A focused, reviewed change with final evidence and delivery
references.

## Risk-scaled process

Include a compact table:

| Change | Recommended process |
|---|---|
| Small, local change | Brief scope clarification -> implement and test -> review diff -> deliver |
| Normal feature or bug fix | Task and approved plan -> implementation -> automated verification -> applicable manual testing -> review |
| High-risk or cross-package change | Specifications and traceable requirements -> subtasks -> staged implementation -> integration/manual verification -> independent AI review -> human acceptance |

Make clear that this is guidance rather than rigid bureaucracy.

## Prompt and developer-message model

### Standing guidance

Rules that apply repeatedly belong in:

- the developer message;
- root and package `AGENTS.md`;
- `TASKS-v7` when task files are active;
- package development documentation;
- specifications and requirements;
- reusable review instructions or skills.

Examples include testing expectations, documentation placement, task-file
structure, commit authorization, security rules, and review standards.

`CONTRIBUTING.md` is written for human contributors and does not need to be
linked from root `AGENTS.md`. `TASKS-v7` should contain only the
task/specification rules needed when task guidance is injected; its downstream
alignment task owns any concise routing needed for task-enabled agents.

### Task prompts

A developer normally provides only:

- the current objective;
- new context not in the repository;
- relevant task, specification, or requirement paths;
- request-specific scope boundaries;
- the requested stage: brainstorm, plan, implement, review, or prepare manual
  tests;
- authority newly granted by the human.

Developers should not copy all repository rules into every prompt.

Long prompts are appropriate when introducing a product idea, external
requirement, business/domain constraint, user feedback, behavior not represented
in the repository, or material scope change.

Example prompts are concise delegation examples, not complete instruction
templates. They assume repository guidance is active.

## Required example prompts

Keep these together after the workflow.

### Brainstorm

```text
I want to add <capability> because <problem or user need>.

Known context:
- <important fact>
- <external constraint>
- <desired behavior>

Help me refine the goal, scope, non-goals, requirements, and important
questions. Inspect the repository where useful. Compare materially different
approaches, but do not implement anything yet.
```

### Create specifications and tasks

```text
Using the agreed scope, create the necessary specifications and task files.

Preserve unresolved questions, approved decisions, requirement IDs, and
supporting references. Do not implement the change.
```

### Plan a subtask

```text
Prepare the execution plan for <task path>.

Inspect the relevant current implementation and update the task with a Draft
plan. Highlight material decisions, risks, and the verification boundary. Do
not implement until I approve the plan.
```

### Implement an approved subtask

```text
The plan in <task path> is approved. Implement the subtask and keep its task
state current.

Run the relevant verification and update linked specifications when
implementation discoveries require it. Do not commit.
```

### Prepare manual testing

```text
Prepare a concise human test checklist for <task or requirement path>.

Include setup, actions, expected observable results, and the requirement IDs
covered. Do not claim that any manual step has been performed.
```

### Independent AI review

```text
Review the current changes against <task path> and its linked specifications.

Focus on correctness, requirement gaps, security, compatibility, failure
behavior, test validity, and documentation drift. Report findings by severity
with file references. Do not modify files or approve the change.
```

### Address review findings

```text
Address the accepted findings <finding references>.

Update the implementation, tests, documentation, task evidence, and linked
specifications where required. Rerun affected verification. Do not commit.
```

### Authorized commit

```text
Create a focused commit for the completed work in <task path>. Include only
the approved in-scope files and use the repository's commit-message
conventions. Record the commit SHA in the task and linked requirements
evidence.
```

## Human review checklists

### Plan review

- Does the plan satisfy the accepted requirements?
- Are scope and non-goals clear?
- Are public contracts and compatibility addressed?
- Are security, persistence, migration, and failure behavior covered where
  relevant?
- Will proposed tests exercise the claimed boundary?
- Is meaningful manual verification identified?
- Is the work divided into reviewable checkpoints?

### Final review

- Does the result solve the intended problem?
- Does the diff match the approved scope?
- Are there unrelated changes?
- Are tests meaningful, and would they detect the relevant regression?
- Did required automated checks actually run?
- Was applicable manual testing performed by a human?
- Were AI-review findings evaluated?
- Are documentation and specifications current?
- Are security, compatibility, and operational concerns acceptable?
- Is the change ready to commit or merge?

## Research references

Preserve these under a compact "Further reading" or rationale section:

- OpenAI, "Introducing Codex":
  https://openai.com/index/introducing-codex/
- OpenAI, "Harness engineering":
  https://openai.com/index/harness-engineering/
- GitHub, "About customizing GitHub Copilot responses":
  https://docs.github.com/en/copilot/concepts/prompting/response-customization
- GitHub, "Responsible use of Copilot code review":
  https://docs.github.com/en/copilot/concepts/agents/code-review
- Google Engineering Practices, "What to look for in a code review":
  https://google.github.io/eng-practices/review/reviewer/looking-for.html
- Google Engineering Practices, "Small CLs":
  https://google.github.io/eng-practices/review/developer/small-cls.html
- NIST Secure Software Development Framework:
  https://csrc.nist.gov/pubs/sp/800/218/final

## Implementation Notes

- September 5, 2026: The user approved the execution plan and directed
  implementation in the separate `main` worktree. The worktree was clean,
  checked out on `main`, and synchronized with `origin/main` before the task
  edit.
- The approved scope keeps `CONTRIBUTING.md` human-focused and does not add a
  route from `AGENTS.md`. Root README and development-index routing also remain
  unchanged because README already links the contributor guide.
- The pre-existing contributor guide was treated as maintained source.
  Repository-wide welcome, testing/documentation principles, public-CI
  boundaries, pull-request expectations, evidence integrity, sensitive-data
  handling, security reporting, licensing, and participation guidance were
  preserved or consolidated.
- Detailed ordinary setup and package-test catalogs were replaced by routes to
  Core, application, plugin, frontend, native application, service, landing,
  and documentation-site entry points. Repository-wide public-CI command
  examples remain.
- The guide now leads with the approved quick workflow, risk-scaling table,
  roles, six detailed stages, standing-guidance model, eight example prompts,
  and human review checklists.
- The public CI section now identifies
  `.github/workflows/public-ci.yml` as the executable source of truth and
  labels `actionlint` as an additional local check rather than a current CI
  command.
- Preliminary verification passed for local link targets, changed-file scope,
  concrete terminology, semantic preservation of the existing contributor
  policy, `git diff --check`, and Markdown rendering with tables and fenced
  code. Human readability confirmation and final evidence updates remain.
- Focused structural assertions passed for all six quick and detailed workflow
  stages, all three risk levels and roles, all eight prompt scenarios, the
  distinct manual/automated/self/independent/final-review boundaries, standing
  guidance locations, review checklists, and explicit commit authorization.
- Markdown rendering produced the expected two tables, eight prompt blocks,
  five shell-command blocks, one page title, and nine major sections. Every
  local file and Markdown anchor linked from `CONTRIBUTING.md` exists.
- Direct external checks returned HTTP 200 for the two GitHub, two Google
  Engineering Practices, and NIST references. The two approved OpenAI
  references returned HTTP 403 to automated requests; they remain preserved,
  but this run does not claim they were mechanically reachable.
- September 5, 2026 follow-up: Human review changed the contributor guide's
  point of view, prompt placement, planning model, instruction-inspection
  guidance, test-evidence emphasis, and specification/task explanation. The
  accepted requirement direction is recorded in this task and the
  documentation-standard specification; the rewrite remains in a separate
  Draft follow-up plan.
- The same review approved two bounded side product improvements that remain
  outside the documentation-standard specification: an on-demand compiled
  system-message action presented through frontend dialogs and an optional
  proxy flag that suppresses request-header logging. Their implementation,
  tests, and package documentation are part of the follow-up task scope.
- September 5, 2026 approval: The human approved the follow-up plan and
  authorized the documentation stage. The system-message action and proxy flag
  remain a later product stage that requires separate human confirmation.
  Target documentation may be drafted first, but product-dependent current
  claims must not be committed separately from the implementation that makes
  them true.

## Execution plan

Status: Approved

This subtask will restructure the existing root `CONTRIBUTING.md` into the
human-facing entry point for the approved AI-assisted development workflow. It
will preserve the useful public-contribution guidance already present while
putting the six-step workflow, risk scaling, role boundaries, prompt examples,
and human review aids first.

The work changes documentation and its task/requirements evidence only. It
does not change product code, runtime agent instructions, task-guidance
injection, CI behavior, package documentation, or documentation-site
publication.

### 1. Preserve the current public-contribution baseline

Treat the existing `CONTRIBUTING.md` as maintained source rather than replacing
it with the task's workflow text wholesale.

Preserve or carefully consolidate its current guidance for:

- finding the package or subsystem that owns a change;
- package-specific development entry points;
- development setup and boundary-appropriate verification;
- required public pull-request checks;
- focused pull requests and truthful verification reporting;
- sensitive and local data;
- contribution licensing;
- respectful participation.

Preserve the opening context, repository-wide testing/documentation principles,
pull-request expectations, evidence-integrity rules, sensitive-data warning,
security route, license summary, no-CLA/DCO statement, and participation
expectations in `CONTRIBUTING.md`.

Where package or repository documentation already owns detailed setup and
ordinary package-test commands, link to that maintained guidance instead of
reproducing a broad command catalog:

- Core/application environment setup and ordinary tests route to their package
  READMEs and development indexes;
- plugin setup routes to shared plugin-authoring guidance and individual
  plugin READMEs;
- frontend, mobile, desktop, bridge, cloud, landing-page, and docs-site setup
  route to their owning package entry points.

Most of this content is already present at those destinations, so the change
removes duplicate detail rather than creating a second documentation move.
Package-specific prerequisites that are not yet clear in their package docs
remain a concise contributor-level pointer rather than expanding this subtask
into unrelated package documentation.

Retain root-level public CI information and useful local command blocks because
they help contributors prepare a pull request. Treat
`.github/workflows/public-ci.yml` as the executable source of truth. Reconcile
the current guide's `actionlint` command with the actual workflow: label it as
an optional additional local check if retained, and do not imply that it is one
of the commands currently executed by public CI. Do not duplicate the
workflow's implementation-only YAML/manifest parsing scripts merely to make
the guide line-for-line identical.

### 2. Lead with the human-readable workflow

Reorganize the guide so a contributor first encounters:

1. a short six-step quick workflow;
2. a compact small/normal/high-risk process-scaling table;
3. one definition each for the human owner, implementing agent, and reviewing
   agent;
4. the six detailed workflow steps with only the owner or collaboration
   relevant to each step.

Keep the document focused and easy to navigate, but do not optimize for source
line count. Explanations, examples, prompt blocks, tables, and other visual
aids may make the file longer while reducing perceived reading effort.

The detailed workflow will distinguish:

- automated verification;
- manual testing actually performed or directly confirmed by a human;
- implementing-agent self-review;
- optional independent AI review;
- required final human review and acceptance;
- explicit human authorization to commit, open a pull request, or merge.

Manual testing and independent AI review remain conditional and
risk-proportional. AI review is advisory and cannot satisfy human verification
or acceptance.

### 3. Explain standing guidance and task-specific prompts

Add a human-oriented explanation of where recurring and task-specific
instructions belong:

- the developer message for platform-wide behavior and safety;
- root and package `AGENTS.md` for repository and package agent guidance;
- `TASKS-v7` for task-file behavior when task guidance is active;
- package documentation for package-specific setup, behavior, architecture,
  and verification;
- specifications and requirements for durable targets and live evidence;
- the current user prompt for the objective, new context, requested stage,
  scope boundaries, and newly granted authority.

Explain that longer prompts are useful when the repository does not contain
the product context, external constraints, user feedback, or scope change.
Discourage copying standing repository rules into every prompt.

This subtask will not add a link from `AGENTS.md` to `CONTRIBUTING.md`.
`CONTRIBUTING.md` is a human-facing guide. Canonical and bundled `TASKS-v7`
alignment, including any concise task-agent routing, remains owned by subtask
068.

### 4. Add practical examples and human review aids

Keep the eight approved prompt scenarios together and present them as concise
delegation examples:

- brainstorming;
- specification and task-file creation;
- subtask planning;
- approved implementation;
- manual-test preparation;
- independent AI review;
- accepted-findings resolution;
- explicitly authorized commit.

Use concrete terms such as documentation, specifications, task files, tests,
and evidence rather than using “artifact” as a generic label.

Retain compact plan-review and final-review checklists. They should help a
human evaluate scope, contracts, risk, test validity, manual evidence,
documentation, AI-review findings, unrelated changes, and delivery readiness
without turning the guide into a formal process specification.

### 5. Finish with contributor essentials and further reading

Place the retained repository and pull-request essentials after the main
workflow so they remain available without interrupting the workflow's
progression.

Keep the supporting OpenAI, GitHub, Google Engineering Practices, and NIST
links in a compact further-reading section. These references provide rationale
and optional depth; the main workflow must remain understandable without
opening them.

### 6. Update state and evidence

After implementation and focused verification:

- update this task's checklist and implementation notes;
- update `DOCFLOW-001` implementation, documentation, and evidence in the
  documentation-standard requirements;
- leave human-verification claims incomplete until a human performs or
  directly confirms the readability review;
- do not claim completion of the broader `DOCFLOW-004` task-guidance
  evaluation, which remains owned by subtasks 068 and 070.

### Implementation decisions and open questions

- The six-step structure, role definitions, conditional validation/review
  activities, prompt placement, and example prompts are approved.
- `CONTRIBUTING.md` is recommended guidance, not an invariant process for every
  one-line change.
- `CONTRIBUTING.md` is human-focused and will not be linked from `AGENTS.md`.
- Readability means focused organization and low perceived effort, not minimum
  source length. Useful examples, code blocks, tables, and illustrations do
  not count against that goal merely because they add lines.
- Existing security, licensing, participation, pull-request, and public-CI
  guidance remains in scope and must not be lost during restructuring.
- Detailed package setup and ordinary package-test commands are consolidated
  into links to their owning documentation. Public-CI reproduction commands
  remain because they are repository-wide contributor guidance.
- `.github/workflows/public-ci.yml` is authoritative for public-CI behavior;
  `CONTRIBUTING.md` provides a readable summary and practical local commands
  without presenting `actionlint` as a current CI step.
- The exact heading wording and placement of the risk-scaling table are local,
  reversible choices as long as the approved structure remains easy to follow.
- No requirement questions are open.

### Documentation

- Restructure root `CONTRIBUTING.md` for human contributors while preserving
  applicable existing contribution policy.
- Do not change root `AGENTS.md`, root `README.md`, or
  `docs/development/index.md`. The README already links the contributor guide,
  and no additional agent or site-navigation link is required by this
  subtask.
- Update the maintainer requirements record and this task only for accurate
  live state and evidence; they are not part of the public guide.

### Task checklist

- [x] Preserve applicable existing public-contribution guidance.
- [x] Write quick workflow and process-scaling table.
- [x] Define roles once.
- [x] Write six-step workflow.
- [x] Explain standing guidance versus task prompts.
- [x] Add concise example prompts.
- [x] Add human review checklists.
- [x] Add compact research references.
- [x] Link to maintained standards, task guidance, and package development
  entry points without duplicating broad command catalogs.
- [ ] Review for human readability, navigation, consistency, and unnecessary
  repetition.
- [x] Update `DOCFLOW-001` and task evidence without claiming downstream
  `DOCFLOW-004` verification.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Readability | Rendered-document inspection confirms that the quick workflow, process-scaling table, six major steps, short owner labels, conditional activities, examples, and separate prompt section are easy to navigate without reading the standards first. Human confirmation remains required for final readability acceptance. |
| Role separation | Human owner, implementing agent, and reviewing agent are defined once; manual verification, AI review, human acceptance, and delivery authorization remain distinct. |
| Prompt guidance | All eight scenarios use concise, stage-specific prompts and concrete document/work terms without duplicating standing repository rules; longer-prompt guidance is explicit. |
| Risk scaling | Small, normal, and high-risk paths are understandable and do not impose the full process on trivial work. |
| Review support | Compact plan and final human-review checklists cover requirements, contracts, test validity, manual evidence, security/compatibility where relevant, and readiness. |
| Existing contributor contract | Diff inspection confirms that current security, licensing, participation, pull-request, public-CI, and truthful-verification guidance is retained or consolidated without changing its meaning. |
| Integration | The existing root README link remains valid; `CONTRIBUTING.md` links onward to the documentation structure, specification standard, task guidance, and relevant package development entry points. No `AGENTS.md` link is added. |

### Additional implementation verification

- Validate every local Markdown link changed or retained in
  `CONTRIBUTING.md`.
- Render or preview the Markdown and inspect heading depth, table readability,
  prompt blocks, code blocks, and section navigation.
- Search the guide for all six workflow stages, three risk levels, eight prompt
  scenarios, the human-manual-verification rule, advisory AI-review boundary,
  and explicit commit authorization.
- Confirm the guide does not use “artifact” as a generic label.
- Run `git diff --check`.
- Review the complete diff against the pre-change `CONTRIBUTING.md` so public
  contribution obligations are not accidentally removed.
- Ask a human reviewer to locate the normal-feature path, plan-approval gate,
  manual-testing rule, AI-review role, and commit-authorization rule without
  using search.

## Follow-up execution plan

Status: Approved

Commit `4c476620377343fbc93401f2493becafe9684d75` is the first
implementation checkpoint. Human review found that the guide still reads too
much like instructions for an implementing agent. This follow-up will rewrite
it as a guide for the human who shapes, supervises, questions, accepts, and
authorizes AI-produced work.

The six-stage workflow, separation of human and AI roles, manual-verification
boundary, advisory AI review, explicit delivery authorization, existing public
contribution policy, and compact further reading remain. The information
architecture, point of view, prompt placement, planning model, instruction
inspection, testing discussion, and specification/task explanation will
change materially.

The task and documentation-standard requirements have been updated to the
approved target. Approval authorizes the documentation rewrite first. The
system-message action and proxy flag must not be implemented until the human
confirms the product stage.

### 1. Reframe the complete guide around human responsibility

Rewrite the opening and six-step quick workflow so each stage tells the human
what to initiate, understand, review, question, approve, verify, or authorize:

1. brainstorm and shape the change with an agent;
2. review any proposed specifications, requirements, and task decomposition;
3. review and approve the implementation plan;
4. authorize and supervise AI implementation against that plan;
5. question the evidence, perform applicable human testing, and review the
   result;
6. plan and resolve findings before explicitly authorizing delivery.

Keep the three role definitions short. Use the rest of the guide to explain
human decision points rather than repeating rules an implementing agent should
already receive through its instructions.

Every change requires planning before implementation. The amount of detail and
whether the plan is recorded only in conversation or in a task vary with the
work:

- a small local change may use a short conversational plan;
- a normal feature or bug fix normally uses an investigated task plan;
- high-risk or multi-part work normally uses staged plans approved one
  executable task at a time.

The small, normal, and high-risk paths will show the same
planning-to-implementation-to-verification lifecycle. Avoid repeatedly using
“proportionate” or another abstract process label; name the concrete planning
form instead.

### 2. Treat specification need as a separate decision

Do not derive specification need from the size of the immediate change.
Explain these rules independently from the process-scaling table:

- when the affected behavior already has a specification, update that
  specification whenever its target behavior or design changes, even for a
  small implementation change;
- a large new feature requires a specification;
- for other work, explicitly consider whether a new specification would
  clarify an existing feature, durable behavior, public contract, or important
  design;
- a small change may therefore be the trigger for specifying an existing
  feature.

At brainstorming, specification review, planning, and final review, give the
human useful questions about existing targets, intended behavior, design
boundaries, non-goals, failure cases, compatibility, security, persistence,
migration, and unresolved decisions.

Current user documentation must be updated whenever a change affects a
consumer. This obligation is independent of change size and of whether a new
specification is created. The guide will tell the human to identify affected
consumers during planning and to ask which user documentation changed and how
its claims were checked when reviewing the completed work.

### 3. Integrate realistic prompts into the workflow

Remove the standalone example-prompt catalog. Put each prompt at the stage
where a human would use it.

Start planning with an explicitly named brainstorming process. Its example
will be one realistic freehand paragraph containing:

- what the human wants to do;
- relevant high-level context and an initial idea;
- uncertainty or constraints;
- what help is requested, such as research, suggestions, comparison, an
  outline, or a plan;
- additional product, user, compatibility, or operational details.

The remaining prompts will be short because standing project and task
instructions should already be active. They will communicate only the current
stage, relevant paths or findings, human concerns or decisions, and newly
granted authority.

Place the existing required scenarios within the workflow:

- brainstorming in shape/planning;
- specification and task preparation in record/decompose;
- subtask planning in plan review;
- approved implementation in implementation supervision;
- manual-test preparation and independent review in validation;
- accepted-findings resolution and commit authorization in delivery.

Add a follow-up-change prompt in the separate follow-up loop. Remove prompt
sentences that merely restate generic agent testing, documentation,
task-maintenance, or no-commit rules already supplied by standing
instructions.

### 4. Teach humans to verify instruction delivery

Replace the current “standing guidance is maintained once” framing with the
operational requirement that project guidance must actually reach the model.

Explain that the human should confirm, before relying on short prompts, that:

- the applicable root and package `AGENTS.md` content is present in the
  developer/system message or first user message;
- task guidance is present when task files are active;
- the selected agent receives the expected planning, authority, testing,
  documentation, task, and safety rules.

Document both Crystal Lattice setting paths for enabling task guidance:

- terminal: `/set include_tasks true`;
- mobile: open the active conversation in **Messages**, use the Settings gear
  to open **Session settings**, and enable **Include TASKS Guidance**;
- desktop: open the active chat, use its Settings action to open the
  **Session settings** window, and enable **Include TASKS Guidance**.

Verify these labels and paths against the production frontends during
implementation before publishing them.

Add a side product improvement to `feature-system-message`: a session action
that compiles the effective developer/system message on demand and presents it
in a dialog. The action should:

- be available from the normal session-action surface when the feature is
  active;
- use the effective session configuration and applicable system-message
  template rather than requiring an LLM request first;
- include conditional task guidance and current `AGENTS.md` content exactly as
  the normal compilation path would;
- work when the provider sends the result as a native system message or as
  top-level instructions;
- return the existing native history unchanged and avoid changing the session
  merely to inspect the message;
- show an understandable empty/error state when no effective message can be
  compiled;
- use the standard action/display contracts and present the result as a
  dialog in supported mobile and desktop frontends.

Prefer extracting one pure compilation helper shared by request initialization
and the inspection action so the displayed text cannot drift from the text
sent to a provider. Add plugin unit tests, application-level action tests, and
frontend tests that cover action discovery, execution, dialog presentation,
task-guidance inclusion, and providers using top-level instructions.

Use existing action and display contracts rather than silently broadening
generic action-display behavior. If a supported frontend cannot present this
action in a dialog without changing that cross-package contract, pause and
propose the required update to the owning action-display specification before
changing the contract.

For another coding agent, document the request-inspection flow through
`tools/openai-proxy/proxy.js`. Add an optional universal `--hide-headers` flag
to the proxy:

- the flag suppresses logging all incoming request headers;
- it affects logging only and does not remove or change headers forwarded to
  the target;
- existing behavior remains available when the flag is absent;
- usage/help output shows the flag for OpenAI-compatible and Anthropic paths.

Add focused proxy tests for argument parsing and request logging with and
without the flag. Create package-owned proxy documentation with startup,
base-URL, inspection, and security guidance.

Recommend `--hide-headers` when inspecting prompts because authorization and
other headers may contain secrets. Present this as a warning and
recommendation, not a ban: users control their own computers, provider
connections, credentials, terminal output, and retained logs. Also explain
that request bodies can contain private prompts, source, and conversation
content even when headers are hidden.

### 5. Make automated test evidence prominent

Explain that AI normally creates and runs automated tests while the human
decides whether the planned and reported evidence is convincing.

At plan review, prompt the human to ask:

- which behavior belongs in unit tests;
- which package, service, transport, persistence, provider, or native boundary
  needs integration testing;
- which public user or deployment journey needs end-to-end testing;
- which visual, accessibility, device, installation, upgrade, or operational
  behavior needs human testing.

At implementation review, prompt the human to ask:

- which unit, integration, and end-to-end commands actually ran;
- what boundary each test crossed;
- whether any tests skipped, failed to collect, or ended with teardown or
  background-process errors;
- what remains unverified;
- whether test-only shortcuts weakened a claimed integration or end-to-end
  path.

Use a compact evidence table or equivalent visual to distinguish unit,
integration, end-to-end, and manual evidence. Do not tell humans to write the
tests or manually audit mechanical requirement/test linkages. Suggest asking
the implementing or reviewing agent for a focused audit when detailed
cross-checking is useful.

### 6. Explain specifications, requirements, tasks, plans, and current docs

Add a high-level specification-driven-development section under repository
essentials. Explain the records by the decisions they help a human make:

- a specification describes intended behavior and design;
- requirements make the intended completed outcomes and live state visible;
- a task records approved scope, decomposition, findings, and completion;
- an execution plan explains how the next concrete task will be implemented
  and verified;
- current user documentation explains what consumers can rely on now;
- current implementation documentation explains delivered maintainer
  behavior.

Make clear that AI normally drafts and updates these documents. Human review
focuses on whether the problem, intended behavior, boundaries, non-goals,
risks, alternatives, failure behavior, compatibility, security, persistence,
migration, and unresolved decisions are understandable and acceptable.
Mechanical consistency checks may be delegated to an implementing or reviewing
agent.

Link the documentation and specification standards, `TASKS-v7`, and a compact
worked example. The recommended example is
`docs/development/specifications/application-runtime-reload/`: its index,
product specification, technical specification, and requirements total about
62 lines and visibly separate the document roles.

### 7. Add an explicit follow-up planning loop

Add a separate section explaining that a review finding, discovered bug,
requested enhancement, or “while you are there” change is new work:

1. ask the agent to investigate its effect on accepted scope and design;
2. plan the follow-up before implementation;
3. update affected existing specifications;
4. consider whether the discovery justifies a new specification;
5. include user-documentation changes whenever consumers are affected;
6. approve the revised plan;
7. implement, rerun affected evidence, and repeat human review.

This loop applies even when the follow-up looks small. It prevents findings
resolution from becoming an unreviewed expansion of the approved change.

### 8. Rewrite repository and pull-request essentials from the same viewpoint

Preserve package routes, public CI commands, pull-request expectations,
sensitive-data and security guidance, licensing, participation, and further
reading.

Recast testing and documentation statements as things the human confirms in
the plan or asks the agent to report after implementation. Keep commands where
they are useful for understanding or reproducing repository-wide CI, but do
not imply that humans normally write the code, tests, or documentation
themselves.

### 9. Apply smaller editorial adjustments

After the structural rewrite:

- remove the detached example-prompts and human-checklists sections after
  integrating their useful content into the relevant workflow stages;
- replace agent-protocol labels such as repeated `Owner` and `Output` blocks
  with human-oriented headings such as “What to decide” and “Questions to
  ask” where they improve the flow;
- remove repeated descriptions of how well an implementing agent should code,
  test, document, or self-review;
- keep role and authorization distinctions without forcing both human and AI
  activity into every paragraph;
- use concrete descriptions such as conversational plan, task plan, staged
  plan, integration test, or end-to-end test;
- review the complete document for navigation, perceived reading effort,
  duplicate advice, and realistic prompts.

### 10. Update requirements, state, and evidence after approval

The human approved this follow-up's requirement direction and resolved its
material questions. Before rewriting the guide:

1. revise the task requirements before rewriting the guide;
2. update the task's supporting details that currently require prompts in a
   separate section or describe the workflow from the implementing agent's
   viewpoint;
3. update the parent task's affected workflow decision/supporting text only
   where it would otherwise contradict the approved follow-up;
4. set `DOCFLOW-001` back to `In progress` while the rewrite is underway;
5. update the documentation-standard specification and requirements to capture
   the revised contributor-workflow outcomes without making the
   system-message action or proxy flag part of that specification;
6. preserve commit `4c476620377343fbc93401f2493becafe9684d75` as the first
   implementation/review checkpoint;
7. rerun structural, rendering, local-link/anchor, terminology, scope, and
   prior-policy-preservation checks;
8. add focused assertions for inline prompts, planning at all change levels,
   follow-up planning, specification rules, mandatory consumer-documentation
   updates, instruction-inspection guidance, and unit/integration/e2e/manual
   evidence;
9. leave final readability and practical-usability requirements incomplete
   until human confirmation.

Execution is staged:

1. commit the approved task and documentation-standard specification changes;
2. draft the contributor guide and related package documentation, including
   the intended product-assisted inspection workflow;
3. present the documentation for human confirmation without implementing the
   action or proxy flag;
4. after separate confirmation, implement and verify the product changes;
5. commit product-dependent current documentation only with the implementation
   that makes its claims true.

### Implementation decisions and open questions

Decided by the human review:

- The guide is a human supervision and decision-making guide, not an
  implementing-agent handbook.
- Every change and follow-up is planned before implementation.
- Planning depth and specification need are separate decisions.
- An affected existing specification is updated whenever its target behavior
  or design changes, even for a small change.
- A large new feature requires a specification; other changes may justify
  specifying an existing feature regardless of immediate size.
- Current user documentation is updated whenever consumers are affected.
- Prompt examples appear inside the workflow and do not repeat standing agent
  rules.
- Automated tests are prominent, including integration and end-to-end tests;
  AI normally creates/runs them and the human evaluates the plan and evidence.
- Avoid repeated use of “proportionate.”
- The guide documents terminal and frontend Session-settings paths for
  including task guidance.
- The system-message feature gains an on-demand session action whose effective
  compiled message is presented in a dialog through supported frontends.
- The proxy gains an optional universal `--hide-headers` logging flag. The
  contributor guide recommends it and warns about header/body sensitivity
  while leaving credential and local-computer responsibility with the user.
- The application-runtime-reload specification is the accepted compact worked
  example.
- “Large feature” remains a principle-based judgment without line, file, or
  task-count thresholds.

No requirement questions or material design decisions remain open. Exact
action identifiers, icon choice, dialog copy, helper extraction boundaries,
test-file placement, and CLI parser structure are local implementation choices
within the approved behavior.

The system-message action and proxy flag are side product improvements. They
are task requirements and require package-owned tests and documentation, but
they are not requirements of the documentation-and-specification standard and
must not be added to its product or technical target.

The documentation stage is authorized. The product stage remains blocked on
separate human confirmation.

### Documentation

- Rewrite root `CONTRIBUTING.md`.
- Update this task's requirements, supporting details, plan state,
  implementation notes, and evidence after approval.
- Update the documentation-standard product/technical target and requirements
  only for the human-led contributor workflow.
- Update affected parent-task workflow decisions/supporting text only where
  necessary to avoid contradiction.
- Update `plugins/feature-system-message/README.md` for the inspection action
  and effective-message behavior.
- Update the mobile and desktop package documentation with the frontend
  Session-settings path and compiled-message action path.
- Create package-owned `tools/openai-proxy/README.md` documentation for the
  proxy flag, startup, configuration, and security considerations.
- Do not update `AGENTS.md`, `TASKS-v7`, or the worked example specification.

### Task checklist

- [x] Obtain approval for the revised task/specification requirements and open
  decisions.
- [x] Update the accepted requirements/specification and set live state to
  `In progress`.
- [ ] Add and verify the system-message compiled-content session action and
  dialog presentation.
- [ ] Document the terminal and frontend Session-settings paths.
- [ ] Add and verify the proxy `--hide-headers` logging flag.
- [ ] Update the system-message, frontend, and proxy package documentation.
- [ ] Rewrite the quick workflow and process-scaling model around human
  responsibility and planning for every change.
- [ ] Separate the specification decision from change size.
- [ ] Integrate realistic prompts into their workflow stages.
- [ ] Add instruction-delivery and safe request-inspection guidance.
- [ ] Make human review of unit, integration, end-to-end, and manual evidence
  prominent.
- [ ] Explain specification, requirement, task, plan, and current-documentation
  roles for human reviewers.
- [ ] Add the follow-up planning loop.
- [ ] Reframe repository and pull-request essentials around human supervision.
- [ ] Apply the smaller editorial and repetition cleanup.
- [ ] Run focused structural, rendering, link, terminology, scope, and
  preservation verification.
- [ ] Update task and specification evidence without claiming human
  readability verification.

### Requirement verification

| Requirement group | Planned acceptance evidence |
|---|---|
| Human focus | Human inspection can follow the complete workflow as actions, questions, decisions, and authorization owned by the human; detailed implementing-agent rules are not the organizing frame. |
| Planning | Structural inspection confirms every small, normal, and high-risk path includes planning before implementation, and the follow-up section repeats that gate. |
| Specification and documentation decisions | The guide treats specification need independently from immediate change size, requires affected existing targets to stay current, requires specifications for large new features, and requires user-documentation updates for every consumer-affecting change. |
| Integrated prompts | Every required prompt scenario appears at its workflow stage; the brainstorming example is realistic freehand context, while later prompts avoid repeating standing rules. |
| Instruction delivery | The guide explains how to ensure `AGENTS.md` and task guidance reached the model, documents terminal and frontend setting paths, and provides the on-demand Crystal Lattice dialog plus a verified proxy inspection path. |
| Test evidence | Unit, integration, end-to-end, and manual boundaries are prominent at plan and completion review; humans evaluate evidence without being assigned mechanical test-authoring or traceability work. |
| Record roles | Human inspection confirms that specifications, requirements, tasks, plans, and current docs are explained through decisions and review questions, with a compact worked example. |
| Existing contributor policy | Diff inspection confirms package routes, public CI, pull-request, security, sensitive-data, licensing, participation, and further-reading guidance remains accurate and discoverable. |
| System-message inspection side change | Plugin and application integration tests confirm the action compiles the effective message without an LLM request or session mutation and supported frontends present it in a dialog; package docs explain the action and setting paths. |
| Proxy inspection side change | Focused Node tests confirm `--hide-headers` suppresses all logged request headers without changing forwarded headers, default behavior remains compatible, and package docs present the flag as a recommendation with header/body sensitivity warnings. |

### Additional implementation verification

- Validate all changed local Markdown links and anchors.
- Render the Markdown with tables and fenced code enabled.
- Check that the quick workflow still has six stages and that prompts are
  nested under the corresponding detailed stages.
- Check that each process-scaling row includes planning before implementation.
- Check for explicit existing-specification, large-feature-specification,
  follow-up-planning, and consumer-documentation rules.
- Check for explicit unit, integration, end-to-end, and manual evidence.
- Run focused feature-system-message unit and application integration tests.
- Run focused frontend action discovery/presentation tests on mobile and
  desktop and the relevant shared frontend package tests when shared behavior
  changes.
- Run the proxy's focused Node tests with and without `--hide-headers`.
- Check that proxy guidance recommends `--hide-headers`, warns that request
  bodies may still be sensitive, and leaves local credential/log responsibility
  with the user.
- Compare retained public-contribution sections with commit `4c476620`.
- Run `git diff --check`.
