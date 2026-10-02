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
2. **Review specifications and tasks:** Decide whether specifications are
   involved, review the proposed requirements and boundaries, and use tasks
   when durable scope or decomposition is useful.
3. **Approve a plan:** Require a plan before every implementation, then review
   its scope, decisions, tests, documentation, and human-verification needs.
4. **Supervise implementation:** Authorize the accepted plan and make sure new
   discoveries return to you when they change requirements or material
   decisions.
5. **Question and verify:** Ask what automated tests actually ran, complete
   applicable human checkpoints, and inspect the resulting change.
6. **Request independent AI review:** For normal, high-risk, or unfamiliar
   changes, ask another agent to inspect the work and evaluate its findings.
7. **Plan every follow-up:** Treat every follow-up as another planned change
   before implementation.

Every change follows this lifecycle. A small correction can move through it in
one short conversation; complex work benefits from durable specifications,
tasks, and staged plans.

## Before You Start: Check the Agent's Instructions

Short task prompts work only when the model actually receives the project's
standing guidance. A file existing in the repository is not enough by itself.

Before relying on an agent, identify both the maintained source and how the
host delivered it:

- system or developer instructions carry the authority assigned to that
  instruction channel;
- root and package `AGENTS.md` may be automatically supplied by the host,
  explicitly injected, or merely available as repository files;
- task guidance should be delivered through the task-enabled developer
  instructions when task files are in use;
- package documentation may need to be discovered and read from the
  workspace.

A repository file being present does not prove that the agent read it, and
injecting a file's text as system/developer instructions is not the same test
as repository discovery.

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
Lattice compiles the current developer/system instructions on demand and
displays them in a dialog. Check which guidance text is present and which
instruction channel the runtime will use. Presence in that dialog proves
request-time instruction delivery; it does not prove that an ordinary
workspace page was independently discovered or read. This inspection does not
send a request to the model or alter the conversation.

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
| Developer/system instructions | Platform-wide behavior, authority, safety, and tool-use rules delivered through those instruction channels |
| Root and package `AGENTS.md` | Maintained repository and package guidance; verify whether the host supplied it as instructions or the agent read it as a file |
| [`TASKS-v7`](agents/TASKS-v7.md) | Maintained task rules delivered through the task-enabled developer-message layer |
| Package documentation | Current setup, supported behavior, architecture, testing, and maintenance guidance read from the workspace |
| Specifications and requirements | Intended behavior and design, completed outcomes, live state, verification, documentation, and evidence |
| Current user prompt | Your objective, new context, requested stage, decisions, concerns, and authority granted now |

## Choose the Appropriate Process

These are proportional defaults, not rigid bureaucracy.

| Change | Recommended process | Task file | Specification |
|---|---|---|---|
| Small, local change | Agree on a short plan, implement and test, then review the diff | Usually none | Update an existing specification if its target changes; create one only when a durable target is needed |
| Normal feature or bug fix | Use an approved plan, implement, verify, then review | One task by default; use subtasks for independently deliverable iterations or responsibilities | Update affected specifications; create one for a large feature or another durable behavior or contract |
| High-risk or cross-package change | Use explicit approval checkpoints, verify integrations and human boundaries, consider independent AI review, then seek human acceptance | One task for one coherent outcome; use a main task with subtasks for independently deliverable iterations or responsibilities | Update affected specifications; create one for a large feature or when the new contract, security, data, migration, or cross-package target needs to be maintained |

A change becomes higher risk when it affects public contracts, security or
privacy, persisted data, compatibility, migrations, deployment, several
packages, native platforms, or difficult-to-reverse operations.

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

### Common Agent Mistakes to Watch For

AI agents can produce convincing plans and completion summaries even after an
important boundary has drifted. Watch especially for:

- a requirement that was omitted, unnecessarily expanded, duplicated, turned
  into an implementation prescription, or left unverified;
- code or documentation changed outside the accepted scope or placed in a
  component that does not own the behavior;
- abstractions, compatibility paths, configuration, workarounds, duplicate
  behavior, or redundant tests that the accepted outcome does not need;
- unit, mocked, or test-only paths presented as integration or end-to-end
  evidence without exercising the real production boundary;
- a confident completion claim that hides skipped checks, unresolved findings,
  stale consumer documentation, remaining risk, or incomplete work.

You do not need to establish every point from the diff yourself. Inspect what
matters to your decision, ask the implementing agent to explain suspicious
changes, or request a focused independent review. Task structure, links,
identifiers, status fields, and other record maintenance remain agent work.

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

For consumer-facing or operational changes, ask whether privacy, rollout,
installation, upgrade, recovery, or accessibility behavior needs an explicit
requirement or non-goal. Include only the concerns affected by the change.

#### Review Task Decomposition

When subtasks are proposed, check that each one leaves a usable, tested
improvement or completes an isolated responsibility that can be accepted
separately. A minimum working version may be one subtask, with later subtasks
adding independently valuable features.

Use a subtask rather than an internal stage when completing it produces a
deliverable improvement. Keep partial implementation and approval checkpoints
as stages inside one task. Implementation, tests, documentation, and evidence
stay with the outcome they support rather than becoming separate phase
subtasks.

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
- Are you being asked to perform a repeatable mechanical check whose result an
  automated test could reliably observe? If so, ask the agent to automate it.
- Is consumer documentation current, and is this the completion of the whole
  task, one stage, or a follow-up?

Test names do not establish what a test verified. Ask which public path
actually ran and which boundaries were simulated.

Installation, upgrade, recovery, accessibility, and real-service workflows may
combine automated and human evidence. Automate repeatable state transitions
and machine-observable results; use a human checkpoint only for the perception,
exploration, or judgment the automated test cannot provide.

Before accepting the result, decide whether the remaining security, privacy,
compatibility, migration, data, deployment, and operational risks are
understood and acceptable. Passing tests or receiving a favorable AI review
does not make that decision.

### 6. Request Independent AI Review

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

### 7. Plan Every Follow-Up

A review finding, newly discovered bug, requested enhancement, or “while you
are there” improvement is another change. Its plan may be short, but it comes
before implementation.

For example:

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

## Understand Specifications and Tasks

Specifications, requirements, tasks, and current documentation answer
different questions. They work together; they are not interchangeable.

```text
rough intent
    ↓
specification target and requirements
    ↓
task scope, plan, and completion evidence
    ↓
implementation and verification evidence
    ↓
current user and maintainer documentation
```

| Record | What it helps you decide |
|---|---|
| Specification | What behavior and design the project is aiming for |
| Requirements | Which completed outcomes matter and whether implementation, verification, and documentation are current |
| Task | What scope was approved, how work is divided, how the next concrete task will be implemented and verified, and what findings or completion evidence matter |
| Current user documentation | What consumers can rely on in the delivered product |
| Current implementation documentation | How maintainers understand and operate the delivered implementation |

AI normally drafts and maintains these records. Review the intended behavior,
important boundaries, decisions, evidence, and remaining work. The agent
maintains the record structure and consistency.

For the repository rules, see:

- [Documentation and specification guide](docs/development/documentation.md)
- [Crystal Lattice documentation conventions](docs/development/crystal-lattice-documentation.md)
- [Task-file guidance](agents/TASKS-v7.md)

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

These maintained project documents provide the most useful next steps:

- [Project overview and development quickstart](README.md)
- [Development documentation](docs/development/index.md)
- [Documentation and specification guide](docs/development/documentation.md)
- [Crystal Lattice documentation conventions](docs/development/crystal-lattice-documentation.md)
- [Plugin documentation](plugins/docs/index.md)
- [Task-file and execution-plan guidance](agents/TASKS-v7.md)