Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCFLOW-001`, `DOCFLOW-004`

# Contributing and AI-Assisted Development Workflow

Create an easy-to-follow root `CONTRIBUTING.md` that explains a practical,
risk-scaled AI-assisted development workflow, clearly distinguishes human
ownership from AI implementation and review, and includes concise example
prompts that rely on standing repository guidance.

## Requirements checklist

- [ ] Root `CONTRIBUTING.md` is the concise contributor entry point for the
  recommended development workflow.
- [ ] The guide begins with a short six-step quick workflow that is easy to
  scan and follow.
- [x] The guide explains how to scale the process for small changes, normal
  features/bug fixes, and high-risk or cross-package changes.
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
- [x] The guide explains which instructions belong in the developer message,
  `AGENTS.md`, `TASKS-v7`, package docs, specifications, and task-specific user
  prompts.
- [x] The guide explains when a longer prompt is appropriate and discourages
  repeating standing repository rules in every prompt.
- [x] Concise example prompts cover brainstorming, specification/task creation,
  subtask planning, approved implementation, manual-test preparation,
  independent review, findings resolution, and authorized commit.
- [x] Example prompts assume repository guidance is already active and do not
  restate generic coding, testing, documentation, or task-file rules.
- [ ] Human plan-review and final-review checklists are concise and practical.
- [x] Commit authorization remains explicit; describing commit as the final
  stage does not grant an agent permission to commit.
- [x] The guide links to the documentation structure, specification standard,
  task guidance, and package-specific development entry points instead of
  duplicating all commands.
- [x] Supporting online references are preserved in a compact further-reading
  or rationale section without interrupting the main workflow.

## Supporting details

### Readability principle

The guide is practical documentation, not a formal process specification.

Prefer:

- a quick summary before detailed explanation;
- six major steps rather than a long sequence of micro-stages;
- roles defined once;
- short owner labels;
- optional or conditional activities called out as such;
- prompts collected in one section after the workflow;
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
3. Recommended AI-assisted workflow
4. How to prompt an agent
5. Example prompts
6. Human review checklists
7. Repository and pull-request essentials
8. Further reading
```

## Approved six-step workflow

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
