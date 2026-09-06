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
- [x] The guide is organized around what a human initiates, reviews, questions,
  decides, verifies, accepts, and authorizes when AI produces the detailed
  plans, code, tests, and documentation.
- [ ] The guide begins with a short six-step quick workflow that is easy to
  scan and follow.
- [x] Small, normal, and high-risk changes all follow planning,
  implementation, verification, and review, while the form and detail of the
  plan vary with the work.
- [x] Every initial change and follow-up is planned before implementation.
- [x] Specification need is considered independently from immediate change
  size: affected existing specifications are updated when their target
  changes, large new features require specifications, and other work may
  justify specifying an existing feature or durable contract.
- [x] Current user documentation is updated whenever a change affects a
  consumer.
- [x] The opening and relevant workflow stages distinguish AI preparation,
  independent AI advice, human decisions and acceptance, and explicit human
  delivery authorization without a standalone role section.
- [x] Each major workflow step identifies only the owner or collaboration
  relevant to that step; the guide does not force both human and AI work into
  every stage.
- [x] Human checkpoints are reserved for perception, exploration, product
  judgment, or real environments that automation cannot faithfully represent;
  repeatable procedures with machine-observable results become automated
  integration or end-to-end tests.
- [x] AI review is advisory and cannot complete a human-verification or
  acceptance requirement.
- [x] The guide distinguishes automated verification, human checkpoints,
  independent AI review, final human acceptance, and human delivery
  authorization.
- [x] The guide explains that applicable `AGENTS.md` and task guidance must
  actually reach the model through its developer/system message or first user
  message and shows humans how to inspect the effective instructions.
- [x] The guide explains which context belongs in the developer/system message,
  `AGENTS.md`, `TASKS-v7`, package docs, specifications, and task-specific user
  prompts.
- [x] Planning begins with a brainstorming process whose realistic freehand
  prompt combines intent, high-level context, requested research or
  suggestions, uncertainty, and additional details.
- [x] Inline workflow prompts cover brainstorming, specification/task
  creation, subtask planning, approved implementation, manual-test preparation,
  independent review, findings resolution, follow-up planning, and authorized
  commit.
- [x] Example prompts assume repository guidance is already active and do not
  restate generic coding, testing, documentation, or task-file rules.
- [x] Human review questions appear at the relevant workflow stages and focus
  on requirements and outcomes, scope and placement, design and complexity,
  verification, documentation, and remaining work without repeating those
  categories as a rigid template.
- [x] Human review can identify missing, expanded, redundant, skipped, or
  unverified requirements; unexpected scope or placement; unnecessary
  complexity; weak evidence; and incomplete documentation through direct
  inspection or focused follow-up questions.
- [x] The guide names common agent mistakes involving requirement drift,
  misplaced changes, unnecessary complexity or redundancy, weak verification
  boundaries, stale consumer documentation, and incomplete work presented as
  complete.
- [x] Result review asks whether a proposed human check is a repeatable
  mechanical check that should instead be automated.
- [x] Unit, integration, end-to-end, and human evidence are prominent; the
  guide assumes AI creates and runs automated tests while humans review the
  planned boundaries, production paths, reported results, and remaining need
  for human judgment.
- [x] The guide gives humans a clear conceptual model of specifications,
  requirements, tasks, current user documentation, and current implementation
  documentation, with the implementation plan explained as part of its task
  rather than as a separate record.
- [x] Independent AI review and `Plan Every Follow-Up` are separate numbered
  workflow steps, with their applicability explained by their text.
- [x] A separate follow-up section requires investigation, planning,
  specification reconsideration, consumer-documentation review, verification,
  and human approval before follow-up implementation and delivery.
- [x] Pull-request preparation and review remain a separate section and retain
  explicit merge/deployment boundaries without adding a redundant delivery
  workflow step.
- [x] The guide links to the documentation structure, specification standard,
  task guidance, and compact project-policy routes without duplicating package
  discovery or CI command catalogs.
- [x] Further Reading routes contributors to the most important maintained
  project source documents.
- [x] Independent AI review uses one short general prompt, optional
  task-specific focus phrases, and a few focused examples rather than one
  exhaustive checklist prompt.
- [x] Pull-request guidance assumes AI prepares the pull request and gives the
  human a concise review of outcome, scope, evidence, limitations, and delivery
  authorization.
- [x] The frontend and terminal setting paths for including task guidance are
  documented.
- [x] The system-message feature exposes a session action that compiles the
  effective developer/system message on demand and presents it in a dialog
  through supported frontends.
- [x] The mobile modal and desktop window keep lengthy compiled prompts
  readable in a bounded scrollable content area, with automated native or
  production-screen coverage of long-content scrolling.
- [x] The OpenAI inspection proxy supports an optional `--hide-headers` flag
  that suppresses all request-header logging without changing forwarding, and
  the guide recommends the flag while explaining that users remain responsible
  for secrets and sensitive request content on their own computers.
- [x] The system-message feature, affected frontend paths, and inspection proxy
  package documentation describe the new behavior.

## Supporting details

### Readability principle

The guide is practical documentation, not a formal process specification.

Prefer:

- a quick summary before detailed explanation;
- six major steps rather than a long sequence of micro-stages;
- responsibilities introduced in the opening and reinforced only where a
  stage needs them;
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

### Responsibility boundaries

The opening distinguishes AI preparation and independent advice from human
intent, decisions, acceptance, checkpoints, and delivery authority. Relevant
stages reinforce those boundaries without a standalone role catalog or a
repeated role matrix.

### Recommended document structure

```text
# Contributing

1. Quick workflow
2. Short instruction-delivery prerequisite
3. Five human-review concerns
4. Human-led workflow:
   - brainstorm and shape
   - decide and record specifications/tasks
   - plan
   - implement
   - verify and assess
   - resolve and deliver
5. Follow-up planning
6. Detailed instruction inspection
7. Pull-request review and project policies
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
  remained a later product stage at that checkpoint and required separate
  human confirmation.
  Target documentation may be drafted first, but product-dependent current
  claims must not be committed separately from the implementation that makes
  them true.
- September 5, 2026 documentation stage: Rewrote `CONTRIBUTING.md` around
  human decisions and supervision, moved all prompt examples into the
  workflow, separated specification need from planning depth, added explicit
  follow-up planning and human review of unit/integration/end-to-end/manual
  evidence, and preserved the prior public contribution policy.
- Drafted package-owned target documentation for the system-message inspection
  action, mobile/desktop/terminal task-guidance paths, and proxy
  `--hide-headers` behavior.
- Focused documentation verification passed: `git diff --check`; structural
  target assertions; local Markdown links and anchors across seven changed
  documents; Markdown rendering with fenced code and tables; and preservation
  checks for public CI, pull-request, security, licensing, participation, and
  truthful-test-reporting guidance. Human readability review remains pending.
- September 5, 2026 checkpoint commits: `4e55e170` records the task and
  requirements state; `755b5e3c` records the complete documentation draft.
  The human explicitly requested documentation-first commit ordering under the
  repository policy introduced by `a4adb728`; product implementation and
  verification remain pending.
- September 5, 2026 human-review consolidation: The human approved a final
  rewrite that retains five review concerns as a light conceptual model rather
  than repeated headings. Stage-specific questions will concentrate on
  requirements, scope/placement, design/complexity, verification, and
  documentation/remaining state only where each concern helps a realistic
  human decision. Task-file mechanics remain agent-owned. Manual checkpoints,
  independent-review prompts, and pull-request guidance will be simplified as
  described in the approved conversation plan.
- September 5, 2026 consolidated rewrite: Updated the documentation-standard
  product and technical targets, `DOCFLOW-006`, and `CONTRIBUTING.md`. The
  guide now introduces the five review concerns once, uses concise
  stage-specific questions, distinguishes automatable checks from human
  judgment, offers a short independent-review prompt with optional focus
  areas, and replaces repository command catalogs with compact pull-request
  guidance.
- Focused consolidation verification passed: `git diff --check`; structural
  assertions for the six stages, five one-time review concerns, prompt
  placement, removed sections, manual/automated boundary, and compact
  pull-request flow; local link and anchor validation across five changed
  documents; Markdown rendering with tables and fenced code; and preservation
  checks for instruction inspection, consumer-documentation obligations,
  project policy links, participation, and Further Reading. Human readability
  and product behavior remained pending at that checkpoint.
- September 5, 2026 product implementation: Added reusable
  `mutates_session: false` feature/provider-extension session actions; the
  application now skips writable-session gating, persistence, synthetic
  mutation IDs, and reload effects for those actions. Existing mutating actions
  retain their default rebuild/persistence behavior.
- Added `show_compiled_system_message` to `SystemMessageFeature`. It executes
  the existing request-initialization pipeline, supports top-level
  instructions and ordinary/Responses-style system messages, honors effective
  session overrides such as `include_tasks`, returns exact text in a direct
  modal display, leaves the session file unchanged, and suppresses the normal
  compiled-history stamp/log side effect during inspection.
- Mobile retains its standard action-result modal; mobile and desktop action
  cards now bound lengthy bodies to a scroll view. Desktop direct modal action
  responses route through the global display owner into a generic native React
  window. Desktop notification modal requests retain inline fallback.
- The local inspection proxy now supports `--hide-headers`, keeps default
  logging compatible, rejects invalid CLI input, and forwards hidden
  authorization/custom headers unchanged. Node unit/subprocess integration
  covers both modes.
- Verification completed:
  - core default suite: 481 passed, 26 deselected, 1 expected xfail;
  - focused core/application non-mutating action tests: 20 passed;
  - feature-system-message unit tests: 34 passed;
  - compiled-message application integration: 1 passed;
  - frontend SDK: 317 passed;
  - mobile: 163 Jest tests, TypeScript, 1 real-backend compiled-message modal
    integration, and focused 300-line scroll assertions passed;
  - desktop: 122 Jest tests and focused 300-line window scroll assertions
    passed;
  - proxy: 4 Node unit/subprocess integration tests passed;
  - Python Ruff/Black, JavaScript syntax, Swift parse, and focused Markdown
    checks passed.
- Verification limitations:
  - the complete application suite reported 368 passed and four reload-owner
    failures after a cached plugin loaded an AnyIO version requiring
    `typing_extensions.sentinel`; the same four tests passed in a fresh
    isolated process;
  - the complete feature package reported 40 passed and seven existing
    environment/fixture failures. The two legacy request tests fail on current
    session-conflict behavior, while five portable-default tests fail on stale
    mixin fixtures and the global `typing_extensions` version. The new action
    tests pass independently;
  - desktop TypeScript reaches existing URL, optional-string, and theme typing
    errors outside the changed lines;
  - macOS XCUITest is authored and registered, but did not run because the
    worktree lacked CocoaPods support files and `pod install` stopped on an
    existing Hermes local-podspec/lock mismatch. No Podfile or lockfile was
    changed.
- Final documentation preparation and MkDocs build passed with the existing
  navigation, absolute-link, Griffe indentation, and unresolved-reference
  warnings. Sixteen changed Markdown files rendered and passed local link and
  anchor validation. `git diff --check`, JavaScript syntax checks, Swift parse,
  Xcode project parsing, and the final focused long-content tests passed.
- September 5, 2026 final contributor-guide structure: Removed the standalone
  Roles and process-selection sections. Stage 2 now owns the independent
  specification and task-record decisions, explains no-task/single-task/main-
  and-subtask choices in a table, and requires each subtask to deliver an
  independently acceptable feature or capability rather than a backend,
  frontend, testing, or documentation slice. The record model now appears in
  stage 2, stage 3 plans the already selected unit of work, and stages 4–6 use
  direct action headings.
- The detailed instruction-inspection guide moved after the workflow while a
  short prerequisite and anchor remain near the beginning. Accepted findings
  now use the separate follow-up loop instead of duplicating it in stage 6.
  Terminology consistently distinguishes automated verification, human
  checkpoints, human assessment, and delivery authorization.
- Focused validation of the final structure passed: direct action-stage order;
  independent specification and task-record decisions; no-task/single-task/
  main-and-subtask table; record creation before decomposition review;
  feature-oriented subtask examples and touch-point counterexamples; separate
  stage-2 and stage-3 return paths; 14 actual prompt examples plus four
  commands, filename examples, or illustrations; Markdown rendering; local
  link and anchor checks; terminology and policy checks; and focused
  `git diff --check`. Human readability confirmation remains pending.
- September 6, 2026 final guide selection: The human selected the 18:47
  contributor-guide version later recorded in `3f2ac09` as the strongest
  baseline and restored it in `9a0d9670`. This decision supersedes the
  September 5 structural experiment that removed process selection, moved
  instruction inspection, embedded the records model in stage 2, and used
  direct action-stage headings.
- The final refinement removes only the standalone Roles and
  automated-versus-human-testing sections, adds one mechanical-check question
  to result review, makes independent review and `Plan Every Follow-Up`
  numbered workflow steps, removes the redundant Plan Findings stage, keeps
  the original follow-up wording with a prompt lead-in, renames the records
  reference to Specifications and Tasks, folds implementation planning into
  the Task row, and replaces external Further Reading with maintained project
  source documents.
- Focused final verification passed on September 6, 2026: `git diff --check`
  for the five changed documentation files; structural assertions for the
  seven numbered workflow sections, removed redundant sections, consolidated
  review paragraph, follow-up prompt lead-in, Specifications and Tasks model,
  and project-source Further Reading; Markdown rendering; and local link and
  anchor validation. Human readability confirmation remains pending.

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
- whether each integration or end-to-end harness reaches the real production
  component, schema, adapter, API, service, provider, or native path;
- which result still needs human perception, exploration, product judgment, or
  a real environment that automation cannot faithfully represent.

At implementation review, prompt the human to ask:

- which unit, integration, and end-to-end commands actually ran;
- what boundary each test crossed;
- whether any tests skipped, failed to collect, or ended with teardown or
  background-process errors;
- what remains unverified;
- whether test-only shortcuts weakened a claimed integration or end-to-end
  path.

Use a compact evidence table or equivalent visual to distinguish unit,
integration, end-to-end, and human evidence. If a proposed human checkpoint is
a repeatable sequence with a machine-observable result, direct it to automated
integration or end-to-end coverage. Do not tell humans to write tests or audit
task-file traceability. Suggest focused follow-up questions or an independent
review when detailed cross-checking is useful.

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
focuses on whether the intended outcomes, scope and placement, important
design choices, verification, consumer documentation, remaining work, and
unresolved decisions are understandable and acceptable. Agents own task-file
structure, traceability, links, status mechanics, and other record-maintenance
details.

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

### 8. Replace repository essentials with compact pull-request guidance

Remove package-discovery catalogs, reproduced public-CI commands, detailed
file-safety instructions, and repeated testing/documentation guidance that
agents receive elsewhere.

Add a natural prompt authorizing an agent to prepare a pull request from the
reviewed commits. Give the human a short final review covering:

- whether the pull request contains the reviewed outcome and scope;
- whether test and human-check claims are accurate;
- whether limitations, deferred work, and unresolved findings are visible;
- whether the target branch and requested delivery action are correct.

Retain concise routes to `SECURITY.md`, `SUPPORT.md`, `LICENSE`, and
`LICENSING.md`, the short participation statement, and Further Reading.

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
- introduce the five human-review concerns once and use only the relevant
  concern at each stage rather than repeating a fixed category template;
- use a short general independent-review prompt, optional focus phrases, and a
  few focused examples instead of one exhaustive reviewer prompt;
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
3. preserve the documentation draft in the user-requested checkpoint commits;
4. consolidate the human-review workflow and present it for human confirmation
   without implementing the action or proxy flag;
5. after separate confirmation, implement and verify the product changes.

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

The documentation and product stages are implemented. Final human
readability, practical-usefulness, and dialog acceptance remain pending.

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
- [x] Add and verify the system-message compiled-content session action and
  dialog presentation.
- [x] Document the terminal and frontend Session-settings paths.
- [x] Add and verify the proxy `--hide-headers` logging flag.
- [x] Draft and checkpoint the system-message, frontend, and proxy package
  documentation in the user-requested documentation-first order.
- [x] Rewrite the quick workflow and process-scaling model around human
  responsibility and planning for every change.
- [x] Remove the standalone Roles section while retaining the reviewed process
  selection, instruction-inspection, and workflow structure.
- [x] Remove the standalone automated-versus-human-testing subsection and add
  one result-review question that redirects mechanical checks to automation.
- [x] Make independent AI review and `Plan Every Follow-Up` separate numbered
  workflow steps.
- [x] Remove the redundant Plan Findings stage while preserving the original
  follow-up wording and adding a prompt lead-in.
- [x] Rename the records reference to Specifications and Tasks and explain the
  implementation plan within the Task row rather than as a separate record.
- [x] Replace external Further Reading with the most important maintained
  project source documents.
- [x] Separate the specification decision from change size.
- [x] Integrate realistic prompts into their workflow stages.
- [x] Add instruction-delivery and request-inspection guidance.
- [x] Consolidate stage-specific human review around requirements, scope and
  placement, design and complexity, verification, documentation, and remaining
  work without turning the categories into a repeated template.
- [x] Distinguish automatable integration/end-to-end procedures from human
  perception, exploration, product judgment, and real-environment checkpoints.
- [x] Replace the generic independent-review prompt with a short default,
  optional focus phrases, and focused examples.
- [x] Make human review of unit, integration, end-to-end, and human evidence
  prominent.
- [x] Explain specification, requirement, task, plan, and current-documentation
  roles for human reviewers.
- [x] Add the follow-up planning loop.
- [x] Replace repository essentials with compact AI-prepared pull-request
  guidance and human review.
- [x] Apply the final editorial and repetition cleanup.
- [x] Run focused structural, rendering, link, terminology, scope, and
  preservation verification.
- [x] Update task and specification evidence without claiming human
  readability verification.

### Requirement verification

| Requirement group | Planned acceptance evidence |
|---|---|
| Human focus | Human inspection can follow the complete workflow as actions, questions, decisions, and authorization owned by the human; detailed implementing-agent rules are not the organizing frame. |
| Planning | Structural inspection confirms every small, normal, and high-risk path includes planning before implementation, and the follow-up section repeats that gate. |
| Specification and documentation decisions | The guide treats specification need independently from immediate change size, requires affected existing targets to stay current, requires specifications for large new features, and requires user-documentation updates for every consumer-affecting change. |
| Integrated prompts | Every required prompt scenario appears at its workflow stage; the brainstorming example is realistic freehand context, while later prompts avoid repeating standing rules. |
| Instruction delivery | The guide explains how to ensure `AGENTS.md` and task guidance reached the model, documents terminal and frontend setting paths, and provides the on-demand Crystal Lattice dialog plus a verified proxy inspection path. |
| Human review | Requirements, scope and placement, design and complexity, verification, documentation, and remaining work guide the relevant stage without becoming a repeated template or a task-maintenance checklist for humans. |
| Test evidence | Unit, integration, end-to-end, and human boundaries are prominent at plan and completion review; deterministic machine-observable procedures become automated tests, and humans evaluate the remaining judgment boundary. |
| Record roles | Human inspection confirms that specifications, requirements, tasks, plans, and current docs are explained through decisions and review questions, with a compact worked example. |
| Pull request and policies | The agent-prepared pull-request prompt and compact human review cover outcome, scope, evidence, limitations, and delivery; security, support, licensing, participation, and further-reading routes remain discoverable. |
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

## Remaining product improvements execution plan

Status: Approved

The documentation workflow is committed through `3f2ac09c`. The remaining
work is limited to the two product improvements already required by this task:

1. expose the effective compiled developer/system message as a non-mutating
   session action and present its direct result in a dialog on mobile and
   desktop;
2. add optional request-header hiding to the local OpenAI inspection proxy
   without changing forwarded headers.

Ground-truth inspection found two shared contracts that must be addressed for
the documented system-message behavior to be true:

- core-side feature and provider-extension session actions are currently
  mutation-oriented: they must return full native history, are rebuilt and
  saved by the application, and report the session as updated;
- mobile honors direct `presentation: "modal"` displays, while desktop
  intentionally normalizes modal action responses to inline cards. Desktop
  already has native React-window infrastructure suitable for a real dialog.

The system-message feature already compiles message and top-level-instructions
forms during request initialization. `AgentCore.initialize_action_request()`
can execute the same provider/feature initialization path for an action
without sending a provider request. The product change should reuse that path
rather than add a second template renderer.

The proxy currently uses positional argument parsing, logs every incoming
request header, has no test script, and starts its server as soon as
`proxy.js` is loaded. The flag work therefore needs a small testable CLI/logging
boundary plus a subprocess integration check.

### 1. Update the related action specifications before code

Do not add these product contracts to the documentation-and-specification
standard.

Update the existing cross-package specifications that own them:

- extend `docs/development/specifications/sessions-actions/` with a
  read-only/non-mutating session-action contract;
- extend `docs/development/specifications/action-display/` so desktop direct
  action responses can honor `presentation: "modal"` through a standard
  action-display window, while application and session notification modal
  fallbacks remain inline;
- add stable requirements for both behaviors and leave them incomplete until
  implementation and verification are present.

The current task requirements already cover the system-message action,
frontend dialog, proxy flag, and package documentation. They do not need a
scope change unless terminal execution is added.

### 2. Add an explicit non-mutating session-action contract

Add an optional action-definition field such as:

```json
{
  "mutates_session": false
}
```

The default remains mutating for compatibility.

For a non-mutating action:

- `AgentCore` permits a display-only result without `native_messages` or
  `session_metadata`;
- the core returns the original `Session` object and rejects session-mutation
  fields from an action declared non-mutating;
- `AgentApplication` does not require a writable live-session view merely to
  execute the action, does not save the session, and does not synthesize
  `updated_session_ids` or reload effects;
- HTTP action envelopes remain unchanged apart from truthfully empty mutation
  and UI-effect sets when the plugin supplies them;
- existing mutating feature and provider-extension actions retain their
  current rebuild, persistence, conflict, and refresh behavior.

Keep this contract generic. Do not add a system-message-specific exception in
the application layer.

### 3. Add the compiled-system-message feature action

Extend `SystemMessageFeature` with:

- logical action ID `show_compiled_system_message`;
- one `session_action` UI element labelled **Show compiled system message**;
- `mutates_session: false`;
- no action inputs or confirmation dialog.

Action execution should call `AgentCore.initialize_action_request()` with the
provided native history, request runtime, and request context. This preserves:

- contributions from earlier provider/features;
- request-scoped `system_message_variables`;
- effective session overrides, including **Include TASKS Guidance**;
- ordinary provider-native system-message form;
- OpenAI Responses-style top-level `instructions`.

Extract the displayed text from initialized request state in this order:

1. non-empty top-level `request.instructions`;
2. the last system/developer message in request override messages;
3. the last system/developer message in initialized native messages.

Support both ordinary role/content messages and Responses-style input-message
items. Return a transient direct display with:

- `format: "text"` so inspection preserves exact text;
- title **Compiled system message**;
- `presentation: "modal"`;
- an informational, dismissible display;
- an understandable empty result when no effective message exists.

The action must not call the provider streaming/request API, append messages,
persist compiled metadata, update the session file, or change its modified
time. Keep normal request compilation and existing compiled-content metadata
behavior unchanged.

### 4. Present direct modal action displays on supported frontends

Mobile already has the required modal presentation in `SessionsScreen` and
`SessionChatScreen`. Add focused coverage using the real
feature-system-message backend path; avoid adding plugin-specific mobile UI.

For desktop, implement generic direct-action modal presentation:

- preserve `presentation: "modal"` for direct action responses in the shared
  frontend policy;
- continue normalizing modal application/session notifications to inline on
  desktop;
- route direct modal envelopes from Sessions and Chat through the existing
  desktop global display owner;
- add one reusable `ActionDisplayWindow` backed by
  `DesktopWindowManager.openReactWindow()` and the existing
  `ActionDisplayCard`;
- retain connection/session context, direct-display local dismissal, embedded
  forms, and generic follow-up actions;
- keep banner and inline presentation unchanged;
- close or replace the active modal predictably when a newer direct modal is
  presented.
- keep lengthy action-display bodies inside a bounded scrollable content area
  on mobile and desktop, and verify scrolling with a long compiled prompt.

Use the native React-window convention rather than relying on React Native
`Modal`, which the desktop window guidance currently treats as unreliable.
Do not add system-message-specific handling to `ChatPane`, `SessionsPanel`, or
the native window manager.

### 5. Add the proxy header-hiding flag

Refactor the proxy entrypoint only enough to test argument parsing and request
logging without starting a server on import.

Implement:

- optional `--hide-headers`, accepted after the required endpoint/port and
  optional base path;
- backward-compatible endpoint, port, and default-base-path behavior;
- clear failure for unknown flags or extra positional arguments;
- help/examples covering OpenAI-compatible and Anthropic use;
- a fixed hidden marker instead of serializing header names or values when the
  flag is active;
- unchanged forwarding of all original headers except the existing hop-by-hop
  removals.

Add a Node built-in test script. Cover the pure parser/logger and a subprocess
integration in which a local target receives authorization and custom headers
while the proxy output contains none of their names or values. Also prove that
the default mode still logs headers.

### 6. Reconcile package and contract documentation

The target documentation was committed before implementation at the human's
explicit request. Update it to match final verified behavior:

- `plugins/feature-system-message/README.md`;
- mobile instruction-inspection documentation and index;
- desktop README and window/action-display development guidance;
- terminal documentation, clarifying that the terminal exposes the task toggle
  but the compiled-message dialog is a mobile/desktop action unless terminal
  execution is separately approved;
- `tools/openai-proxy/README.md`;
- `plugins/docs/actions.md` for non-mutating session actions;
- `plugins/docs/notifications-and-action-displays.md`;
- action-display and sessions-action specifications and requirements.

Update `CONTRIBUTING.md` only if implementation changes a label, path, or
verified behavior already described there.

### Implementation decisions and open questions

1. **Approved — generic non-mutating session actions:** Use
   `mutates_session: false` as a reusable action-definition contract, with
   mutating behavior remaining the default. This is preferable to saving an
   unchanged session or adding a system-message-specific application bypass.
2. **Approved — desktop direct-action windows:** Use real
   desktop window presentation for all direct action displays requesting
   `modal`, while notification modal requests retain their current inline
   fallback. This is preferable to plugin-specific frontend logic, but it
   changes the presentation of other direct modal action results on desktop.
3. **Approved boundary — terminal execution:** Add no new terminal
   slash command or generic action browser in this task. Keep
   `/set include_tasks true` as the terminal setting path and describe the
   compiled-message dialog as available in mobile and desktop.
4. **Local implementation choices:** Exact icon, order, empty-state copy,
   desktop window dimensions, replacement behavior for two rapidly presented
   modals, helper filenames, and proxy module split do not require separate
   approval if they preserve the contracts above.

### Documentation

- Update the action-display and sessions-action specifications before their
  implementations.
- Reconcile the already committed feature, frontend, terminal, proxy, and
  contributor documentation with verified behavior.
- Update package development documentation for the read-only action path and
  desktop native action-display window.
- Do not add the side product contracts to the
  documentation-and-specification standard.

### Task checklist

- [x] Obtain approval for the two material recommendations and terminal
  requirement boundary.
- [x] Update action-display and sessions-action specifications/requirements.
- [x] Implement and verify non-mutating session actions.
- [x] Implement and verify the compiled-system-message feature action.
- [x] Verify the actual feature action through the HTTP/frontend SDK boundary.
- [x] Verify mobile action discovery, execution, and modal presentation.
- [x] Implement and verify generic desktop direct-action modal windows.
- [x] Implement and verify proxy `--hide-headers`.
- [x] Reconcile package and contract documentation.
- [x] Update task and requirement evidence.
- [ ] Complete applicable human dialog/readability verification.

### Requirement verification

| Requirement group | Planned acceptance evidence |
|---|---|
| Non-mutating action | Core/application tests prove `mutates_session: false` actions can return display-only results, work without a writable mutation path, do not save or change session files, and leave existing mutating actions compatible. |
| Compiled message | Plugin tests and application HTTP integration prove the action uses request initialization, includes request-scoped variables and task guidance, supports message/instructions forms, returns exact text, makes no model request, and leaves the session unchanged. |
| Mobile dialog | A production-screen component/integration path executes the real session action and presents the returned compiled text through the standard mobile action-result modal; a lengthy prompt remains bounded and scrollable. |
| Desktop dialog | Shared-policy and desktop tests prove direct modal action displays open the generic native React window with correct ownership/dismissal, while notification modal fallback and inline/banner behavior remain compatible; a lengthy prompt remains bounded and scrollable. |
| Proxy flag | Node unit/subprocess integration proves hidden mode logs no incoming header names or values, forwards headers unchanged, rejects malformed CLI input, and preserves default logging behavior. |
| Documentation | Package and cross-package docs describe the delivered action, setting paths, read-only action contract, desktop direct-modal behavior, proxy usage, and security limitations. |

### Additional implementation verification

- Run the feature-system-message default and application integration suites.
- Run focused core and application session-action suites plus the full default
  core/application suites because the mutation contract is shared.
- Run frontend SDK action runner/display policy tests and the full default
  frontend SDK suite.
- Run mobile component and real-backend integration tests, TypeScript, and a
  focused production-screen iOS/Android action-dialog scenario if the existing
  native harness can exercise the session action without a test-only UI path.
- Run desktop component/integration tests, TypeScript, and a focused macOS
  XCUITest that opens and closes the native action-display window.
- Run proxy Node tests against a local target process.
- Run documentation rendering/link checks and `git diff --check`.
- Record unavailable native or environment-gated checks as not run, not
  passed.
