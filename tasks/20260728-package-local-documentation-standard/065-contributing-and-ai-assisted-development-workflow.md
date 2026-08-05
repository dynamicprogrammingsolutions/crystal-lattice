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
- [ ] The guide explains how to scale the process for small changes, normal
  features/bug fixes, and high-risk or cross-package changes.
- [ ] Human owner, implementing agent, and reviewing agent responsibilities are
  defined once near the beginning.
- [ ] Each major workflow step identifies only the owner or collaboration
  relevant to that step; the guide does not force both human and AI work into
  every stage.
- [ ] Manual verification is defined as work actually performed or directly
  confirmed by a human.
- [ ] AI review is advisory and cannot complete a human-verification or
  acceptance requirement.
- [ ] The guide distinguishes automated verification, manual testing,
  implementing-agent self-review, independent AI review, final human review,
  and human delivery authorization.
- [ ] The guide explains which instructions belong in the developer message,
  `AGENTS.md`, `TASKS-v7`, package docs, specifications, and task-specific user
  prompts.
- [ ] The guide explains when a longer prompt is appropriate and discourages
  repeating standing repository rules in every prompt.
- [ ] Concise example prompts cover brainstorming, specification/task creation,
  subtask planning, approved implementation, manual-test preparation,
  independent review, findings resolution, and authorized commit.
- [ ] Example prompts assume repository guidance is already active and do not
  restate generic coding, testing, documentation, or task-file rules.
- [ ] Human plan-review and final-review checklists are concise and practical.
- [ ] Commit authorization remains explicit; describing commit as the final
  stage does not grant an agent permission to commit.
- [ ] The guide links to the documentation structure, specification standard,
  task guidance, and package-specific development entry points instead of
  duplicating all commands.
- [ ] Supporting online references are preserved in a compact further-reading
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
  verification, updates artifacts, and prepares evidence.
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
7. Further reading
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

Root `AGENTS.md` should route agents to `CONTRIBUTING.md` for substantial
multi-stage work. `TASKS-v7` should contain only task/specification rules needed
when task guidance is injected.

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
Using the agreed scope, create the necessary specification and task artifacts.

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

## Execution plan

Status: Draft

1. Read the documentation/specification standard produced by subtask 010 and
   use its terminology consistently.
2. Inspect root README/AGENTS/development entry points so `CONTRIBUTING.md`
   links rather than duplicates package commands.
3. Write the short quick workflow and risk-scaling table first.
4. Add the six-step detailed workflow with concise owner labels.
5. Add the prompt/developer-message distinction.
6. Add the separate example-prompts section.
7. Add compact plan-review and final-review checklists.
8. Add further-reading references without interrupting the main workflow.
9. Update root README/AGENTS links as needed.
10. Review the rendered Markdown for scanability and remove unnecessary
    repetition.

### Implementation decisions and open questions

- The six-step structure, role definitions, conditional validation/review
  activities, prompt placement, and example prompts are approved.
- `CONTRIBUTING.md` is recommended guidance, not an invariant process for every
  one-line change.
- The exact heading wording and placement of the risk-scaling table are local,
  reversible choices as long as the approved structure remains easy to follow.
- No requirement questions are open.

### Documentation

- Root `CONTRIBUTING.md`
- Root README and `AGENTS.md` links
- Potential links from `docs/development/index.md`

### Task checklist

- [ ] Write quick workflow and process-scaling table.
- [ ] Define roles once.
- [ ] Write six-step workflow.
- [ ] Explain standing guidance versus task prompts.
- [ ] Add concise example prompts.
- [ ] Add human review checklists.
- [ ] Add compact research references.
- [ ] Link contributor guide from repository entry points.
- [ ] Review for readability and repetition.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Readability | Human inspection confirms the quick workflow, six major steps, short owner labels, conditional activities, and separate prompt section can be followed without reading the standards first. |
| Role separation | Human owner, implementing agent, and reviewing agent are defined once; manual verification, AI review, human acceptance, and delivery authorization remain distinct. |
| Prompt guidance | Examples contain current objectives and artifact references without duplicating standing repository rules; longer-prompt guidance is explicit. |
| Risk scaling | Small, normal, and high-risk paths are understandable and do not impose the full process on trivial work. |
| Review support | Compact plan and final human-review checklists cover requirements, contracts, test validity, manual evidence, security/compatibility where relevant, and readiness. |
| Integration | Root entry points link to `CONTRIBUTING.md`, which links onward to detailed standards and package guidance. |

### Additional implementation verification

- Render or preview the Markdown and inspect heading depth, table readability,
  and prompt blocks.
- Ask a human reviewer to locate the normal-feature path, plan-approval gate,
  manual-testing rule, AI-review role, and commit-authorization rule without
  using search.
- Check links to standards and package entry points.
