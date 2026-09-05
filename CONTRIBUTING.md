# Contributing

Crystal Lattice is an early-stage project spanning Python, TypeScript, React
Native, Elixir, deployment tooling, documentation, and first-party plugins.
Focused fixes, tests, documentation improvements, and well-scoped feature
proposals are welcome.

This guide is for the human directing AI-assisted development. The agent may
prepare most of the research, plans, code, tests, documentation, and review
material; the human remains responsible for intent, important decisions,
verification that requires human judgment, acceptance, and delivery
authorization.

## Quick Workflow

1. **Brainstorm and shape:** Describe what you want in ordinary language, then
   use an agent to research the repository, test assumptions, and clarify the
   intended outcome.
2. **Review the records:** Decide whether specifications are involved, review
   the proposed requirements and boundaries, and use tasks when durable scope
   or decomposition is useful.
3. **Approve a plan:** Require a plan before every implementation, then review
   its scope, decisions, tests, documentation, and human-verification needs.
4. **Supervise implementation:** Authorize the accepted plan and make sure new
   discoveries return to you when they change requirements or material
   decisions.
5. **Question and verify:** Ask what automated tests actually ran, complete
   applicable human checkpoints, consider independent AI review, and inspect the
   resulting change.
6. **Plan findings and deliver:** Treat every follow-up as another planned
   change. Commit, open a pull request, or merge only after explicit human
   authorization.

Every change follows this lifecycle. A small correction can move through it in
one short conversation; complex work benefits from durable specifications,
tasks, and staged plans.

## Before You Start: Check the Agent's Instructions

Short task prompts work only when the model actually receives the project's
standing guidance. A file existing in the repository is not enough by itself.

Before relying on an agent, make sure its developer/system message—or, if the
agent has no project-instruction mechanism, the first user message—contains:

- the applicable root and package `AGENTS.md` guidance;
- the repository's task guidance when task files are in use;
- the expected authority, safety, planning, testing, documentation, and
  delivery rules.

Asking the agent what it received is a useful first check, but inspecting the
effective message or outgoing request is stronger evidence.

### Inspect Instructions in Crystal Lattice

Task guidance is optional in Crystal Lattice sessions. Enable it before
planning or changing a tracked task:

- **Mobile:** open the active conversation in **Messages**, select the Settings
  gear, open **Session settings**, and enable **Include TASKS Guidance**.
- **Desktop:** open the active chat, select **Settings**, open the
  **Session settings** window, and enable **Include TASKS Guidance**.
- **Terminal:** run:

  ```text
  /set include_tasks true
  ```

From the session actions, select **Show compiled system message**. Crystal
Lattice compiles the current developer/system message on demand and displays it
in a dialog. Check that the expected `AGENTS.md` content and, when enabled,
task guidance are present. This inspection does not send a request to the
model or alter the conversation.

### Inspect Requests from Other Agents

For agents that let you override their provider base URL, the repository's
[OpenAI inspection proxy](tools/openai-proxy/README.md) can show the actual
outgoing JSON request.

Install its dependencies and start it for an OpenAI-compatible endpoint:

```bash
npm --prefix tools/openai-proxy ci
node tools/openai-proxy/proxy.js \
  https://api.openai.com/v1 \
  3000 \
  /v1 \
  --hide-headers
```

Point the agent's provider base URL at `http://127.0.0.1:3000/v1`, submit a
prompt, and inspect the proxy's request body and expanded `LONG_TEXT_*`
sections. The exact base-URL setting depends on the agent.

For an Anthropic endpoint:

```bash
node tools/openai-proxy/proxy.js \
  https://api.anthropic.com \
  3000 \
  /v1 \
  --hide-headers
```

`--hide-headers` is recommended when inspecting prompts because authorization
and other headers may contain secrets. It suppresses header logging; it does
not remove headers from the forwarded request. Request bodies may still
contain private prompts, source code, file paths, and conversation content.
You are responsible for the credentials, provider connection, terminal
output, and retained logs on your computer.

### Where Context Belongs

Use the inspected message to confirm that recurring rules are active. Keep the
task prompt focused on information that is new for the current conversation.

| Location | What it contributes |
|---|---|
| Developer/system message | Platform-wide behavior, authority, safety, and tool-use rules |
| Root and package `AGENTS.md` | Repository and package constraints, ownership, important paths, verification, and documentation routes |
| [`TASKS-v7`](agents/TASKS-v7.md) | Task creation, planning, approval, status, evidence, and completion rules |
| Package documentation | Current setup, supported behavior, architecture, testing, and maintenance guidance |
| Specifications and requirements | Intended behavior and design, completed outcomes, live state, verification, documentation, and evidence |
| Current user prompt | Your objective, new context, requested stage, decisions, concerns, and authority granted now |

## Choose the Working Process

Every level includes planning, implementation, verification, and review. The
working record and depth change; the lifecycle does not.

| Change | Plan before implementation | Implementation and review |
|---|---|---|
| Small, local correction | Ask for a brief plan in the conversation and confirm that it addresses the intended boundary | Let the agent implement after approval, run focused checks, and review the diff and reported evidence |
| Normal feature or bug fix | Use an investigated task plan when the work benefits from durable scope, decisions, or evidence | Review unit and integration coverage, applicable e2e or manual checks, consumer documentation, and the complete result |
| High-risk or multi-part work | Use staged plans, usually through a main task and reviewable subtasks | Approve one executable stage at a time; review integration, e2e, operational, migration, security, and human-verification evidence where relevant |

Risk increases when work affects public contracts, security or privacy,
persisted data, compatibility, migrations, deployment, multiple packages,
native platforms, or difficult-to-reverse operations.

### Decide About Specifications Separately

Do not use the size of the immediate edit as the only reason to create or skip
a specification.

- If the affected behavior already has a specification, ask the agent to
  update it whenever the intended behavior or design changes.
- A large new feature requires a specification.
- For other work, consider whether a specification would make an existing
  feature, durable behavior, public contract, or important design easier to
  understand and maintain.
- A small change can reveal that an existing feature should be specified.

Ask the agent to find the governing specifications before planning. If it
proposes no specification work, understand why the existing target remains
accurate or why no durable target is useful.

Current user documentation follows a different rule: whenever delivered
behavior affects a consumer, the owning user documentation must be updated.

## Roles

- **Human owner:** Owns intent, requirement decisions, plan approval,
  human verification, acceptance, and delivery authorization.
- **Implementing agent:** Researches, proposes records and plans, implements
  approved work, produces evidence, and reports discoveries for human review.
- **Reviewing agent:** Independently reports risks and findings for the human
  owner; it does not approve the change or satisfy human verification.

The same person may shape and finally review a small change, but those are
still distinct decisions.

## What Humans Review

Five recurring concerns can help you direct a review:

- **Requirements and outcomes:** Is the requested behavior present without
  important omissions or unapproved additions?
- **Scope and placement:** Does the work stay within the accepted boundary and
  belong in the parts of the system being changed?
- **Design and complexity:** Are important choices understandable, and is the
  solution no more complicated than the outcome requires?
- **Verification:** Do the planned or completed tests provide confidence at
  the real boundaries?
- **Documentation and remaining work:** Are consumer documentation,
  limitations, deferred work, and unverified results visible?

You do not need to perform every detailed check yourself. Inspect what matters
to your decision, ask the implementing agent focused questions, or request an
independent review. Task structure, links, identifiers, status fields, and
other record maintenance remain agent work.

## Human-Led AI-Assisted Workflow

### 1. Brainstorm and Shape the Change

Start with what you actually know. You do not need to turn an early idea into a
formal requirements document before speaking to an agent.

A useful initial description usually contains:

- what you want and why;
- enough product or technical context to explain the current situation;
- your initial idea, if you have one;
- uncertainties, constraints, examples, or user feedback;
- the kind of help you want now: suggestions, repository research, external
  research, alternatives, an outline, or a plan.

Real initial prompts are often one freehand paragraph:

```text
I want to <what I want to change> because <why it matters>. At the moment
<high-level context about the product, users, or implementation>, and my
initial thought is <possible direction>, but I am not sure about <important
unknown or tradeoff>. Please inspect the relevant parts of the repository,
research <anything that needs research>, suggest alternatives where useful,
and help me outline the intended behavior, boundaries, and a sensible plan.
Some additional details are <examples, constraints, compatibility needs, user
feedback, or non-goals>.
```

Treat the result as a conversation, not as an answer to approve immediately.
Ask follow-up questions until the important outcome and choices are
understandable.

Questions worth asking include:

- What assumptions did you make?
- What does the current implementation actually do?
- Which consumers and packages are affected?
- What alternatives have meaningfully different tradeoffs?
- What should explicitly remain out of scope?
- Is any important behavior already specified?
- Which decisions need me rather than the implementing agent?

### 2. Review Specifications, Requirements, and Tasks

Once the direction is clear, ask the agent what durable records are useful.
The agent can draft them; your job is to understand and accept the intended
outcomes, boundaries, and important decisions.

```text
Turn our agreed direction into the appropriate specifications, requirements,
and task structure. Bring back the important scope and design decisions for my
review.
```

Check first that the requirements represent what you meant:

- Are any requested outcomes missing?
- Did the proposal add behavior or constraints that you did not ask for?
- Are two requirements describing the same outcome?
- Does a requirement prescribe a class, component, mechanism, or file layout
  that belongs in the implementation plan instead?

Implementation constraints may be legitimate when they protect a public
contract, security boundary, compatibility guarantee, ownership boundary, or
persisted data. Ask why a specific mechanism must be part of the requirement
when that reason is not apparent.

Then review the proposed boundary:

- What is explicitly outside the work?
- Which consumers and major parts of the system are affected?
- Does the task combine capabilities that could be decided or delivered
  separately?
- Which product, compatibility, security, persistence, or migration decisions
  require your approval?

Useful follow-ups include:

```text
Summarize how the requirements cover what I asked for. Call out anything you
added, left out, or represented more than once.
```

```text
Which requirements prescribe implementation choices, and why are those
choices necessary constraints rather than plan details?
```

### 3. Review and Approve the Plan

Require a plan before implementation, including for a follow-up or a small
change. For tracked work:

```text
Investigate and propose the execution plan for <task path>. I especially want
to review <boundary, risk, test strategy, or decision>.
```

For a small conversational change:

```text
Before making the change, inspect the relevant code and give me a brief plan,
including the tests and documentation affected.
```

Start with requirement coverage:

```text
Map the plan to the accepted requirements and call out anything that is
deferred, only partially covered, or still depends on a decision.
```

Review unexpected scope or placement without trying to reconstruct the entire
architecture yourself:

- Which packages or major components will change, and why?
- Does each planned change support an accepted outcome?
- Is behavior being added at the part of the system that owns it?
- Is a related change being included that needs a separate decision?

Ask the agent to explain important design choices:

```text
Explain the main design choices, the assumptions they depend on, and any
simpler alternative that was rejected.
```

Pay particular attention to assumptions about provider behavior, native
platforms, external services, framework capabilities, or existing ownership.
A small experiment or real integration request may be more useful than
approving a detailed design built on an unverified assumption.

#### Review the Test Strategy

AI will normally create and run the automated tests. Before approving the
plan, understand what confidence each layer will add:

| Evidence | Question for the plan |
|---|---|
| Unit tests | Which rules, edge cases, and failure behavior will they isolate? |
| Integration tests | Which real package, service, transport, persistence, provider, or native boundary will they cross, and through which production adapter or API? |
| End-to-end tests | Which public user or deployment journey will they exercise through production components? |
| Human checkpoint | What perception, exploration, product judgment, or real environment cannot be represented faithfully by an automated assertion? |

Not every change needs every kind of evidence. The important point is to make
the boundary choice explicit before implementation. Also ask which current
user documentation changes for affected consumers and whether an existing
specification target changes.

### 4. Authorize and Supervise Implementation

Once you accept the plan, grant implementation authority plainly:

```text
I approve the plan in <task path>. Proceed with the implementation.
```

For a conversational plan:

```text
That plan looks right. Please implement it.
```

You do not need to direct every edit. For longer work, ask at a meaningful
checkpoint:

```text
Has implementation changed any accepted requirement, scope boundary,
important design assumption, verification plan, or documentation impact?
```

If the answer changes the required outcome, contract, ownership, persisted
data, security model, or another important decision, return to planning before
authorizing that work.

### 5. Question the Evidence and Review the Result

An implementation summary is the start of review. Begin with a concise account
of the result and its limits:

```text
Summarize what was delivered, what changed from the plan, which tests actually
ran, what remains unverified, and what documentation was updated.
```

Follow up where the answer affects acceptance:

- Which requirements are incomplete, skipped, or still unverified?
- Were unexpected files, packages, or behaviors changed, and do they belong
  there?
- Did the change introduce unnecessary or duplicated behavior, configuration,
  compatibility paths, fallbacks, or abstractions?
- Did the tests reach the production paths they claim to cover, or stop
  earlier in setup, collection, harness selection, transport, or teardown?
- Is consumer documentation current, and is this the completion of the whole
  task, one stage, or a follow-up?

#### Choose Automated or Human Testing

If a checkpoint is a repeatable sequence with a machine-observable result, ask
for an automated integration or end-to-end test. Examples include changing a
setting and checking persisted state, invoking an action and checking dialog
content, navigating a simulator flow, or restarting a service and checking
recovery.

Use a human checkpoint when it adds perception, exploration, product judgment,
or a real environment that automation cannot faithfully represent. Examples
include judging whether a long dialog is readable, whether a workflow is
understandable, how a gesture feels, or how the product behaves with real
hardware and services.

```text
Review the proposed human checkpoints. Which ones add real human judgment, and
which should become automated integration or end-to-end tests?
```

#### Request Independent AI Review

For normal, high-risk, or unfamiliar changes, another agent can inspect the
work independently:

```text
Independently review the current change against <task or specification>.
Focus on correctness, scope, verification, and unnecessary complexity. Report
concrete findings with file references.
```

Add a focus that matters to the task, such as:

- requirement coverage and verification;
- scope and ownership;
- complexity and duplication;
- security, persistence, or compatibility;
- native interaction, accessibility, or consumer documentation.

You can also request a narrow review:

```text
Review only requirement coverage and verification. Identify anything missing,
skipped, or supported by weaker evidence than the summary claims.
```

```text
Review the change for scope and design. Look for misplaced or duplicated
behavior and complexity the accepted requirements do not need.
```

The reviewing agent advises you. It may miss problems or report findings that
do not hold, so evaluate each finding before acting on it.

Use the findings as input. You decide whether the outcome was achieved and
whether the remaining gaps and risks are acceptable.

### 6. Plan Findings and Authorize Delivery

Decide which findings to accept, reject, or defer. Accepted findings still need
a plan:

```text
Assess the accepted findings <finding references> and propose the required
plan updates before changing the implementation.
```

After approving that plan:

```text
I approve the findings plan. Please implement it and report the affected
verification and documentation.
```

When the final result and evidence are acceptable, explicitly grant only the
delivery action you intend:

```text
Create a focused commit for the completed work in <task path>.
```

Describing a commit, pull request, deployment, or merge as the next workflow
stage does not authorize it. The human owner grants that authority explicitly.

## Plan Every Follow-Up

A review finding, newly discovered bug, requested enhancement, or “while you
are there” improvement is another change. Its plan may be short, but it comes
before implementation.

```text
I want to follow up with <finding or additional change>. First investigate how
it affects the accepted scope, specifications, tests, and consumer
documentation, then propose the updated plan.
```

Before approving the follow-up, decide:

1. Does it change accepted requirements or only implementation detail?
2. Does it change the target of an existing specification?
3. Does the discovery justify a new specification?
4. Which consumers and current user documentation are affected?
5. Which automated and human evidence must be repeated or added?
6. Is it still part of the same reviewable change?

Then repeat implementation, evidence review, applicable human testing, and
delivery authorization.

## Understand the Project Records

Specifications, requirements, tasks, plans, and current documentation answer
different questions. They work together; they are not interchangeable.

```text
rough intent
    ↓
specification target and requirements
    ↓
task scope and approved execution plan
    ↓
implementation and verification evidence
    ↓
current user and maintainer documentation
```

| Record | What it helps you decide |
|---|---|
| Specification | What behavior and design the project is aiming for |
| Requirements | Which completed outcomes matter and whether implementation, verification, and documentation are current |
| Task | What scope was approved, how work is divided, and what findings or completion evidence matter |
| Execution plan | How the next concrete task will be implemented and verified |
| Current user documentation | What consumers can rely on in the delivered product |
| Current implementation documentation | How maintainers understand and operate the delivered implementation |

AI normally drafts and maintains these records. Review the intended behavior,
important boundaries, decisions, evidence, and remaining work. The agent
maintains the record structure and consistency.

For the repository rules, see:

- [Specification standard](docs/development/standards/specifications.md)
- [Repository specification policy](docs/development/repository/specifications.md)
- [Task-file guidance](agents/TASKS-v7.md)
- [Documentation structure](docs/development/repository/documentation.md)

The
[application runtime reload specification](docs/development/specifications/application-runtime-reload/index.md)
is a compact example. Its product specification explains observable behavior,
its technical specification explains the implementation contract, and its
requirements show the live outcome set.

## Prepare and Review the Pull Request

After the commits have been reviewed, explicitly ask the agent to prepare the
pull request:

```text
Open a pull request from the reviewed commits. Summarize the outcome, actual
scope, tests and human checks performed, documentation updated, and remaining
limitations. Do not merge it.
```

Before accepting or merging it, check that:

- the pull request contains the work you reviewed;
- its description matches the accepted outcome and scope;
- test and human-check claims are accurate;
- deferred work, limitations, and unresolved findings are visible;
- the target branch, reviewers, and requested delivery action are correct.

Opening a pull request does not authorize a merge or deployment.

### Project Policies

Use [SUPPORT.md](SUPPORT.md) for issue and support routing and
[SECURITY.md](SECURITY.md) for sensitive security reports. Contribution terms
are defined by [LICENSE](LICENSE) and [LICENSING.md](LICENSING.md); the project
does not currently require a separate contributor license agreement or
Developer Certificate of Origin signoff.

Be respectful, constructive, and specific. Assume good faith, discuss the
technical or user outcome rather than the person, and make space for
maintainers and contributors with different levels of familiarity with the
repository.

## Further Reading

These references provide additional rationale and techniques. They are not
required reading for ordinary contributions.

- OpenAI, [Introducing Codex](https://openai.com/index/introducing-codex/)
- OpenAI,
  [Harness engineering](https://openai.com/index/harness-engineering/)
- GitHub,
  [About customizing GitHub Copilot responses](https://docs.github.com/en/copilot/concepts/prompting/response-customization)
- GitHub,
  [Responsible use of Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review)
- Google Engineering Practices,
  [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- Google Engineering Practices,
  [Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- NIST,
  [Secure Software Development Framework](https://csrc.nist.gov/pubs/sp/800/218/final)