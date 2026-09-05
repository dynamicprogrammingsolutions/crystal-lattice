# Contributing

Crystal Lattice is an early-stage project spanning Python, TypeScript, React
Native, Elixir, deployment tooling, documentation, and first-party plugins.
Focused fixes, tests, documentation improvements, and well-scoped feature
proposals are welcome.

This guide is for the human directing AI-assisted development. The agent may
prepare most of the research, plans, code, tests, documentation, and review
material; the human remains responsible for intent, important decisions,
human judgment, acceptance, and delivery authorization. An independent
reviewing agent can advise on the result, but the human decides whether its
findings are valid and whether the change is acceptable.

## Quick Workflow

1. **Brainstorm and shape:** Describe what you want in ordinary language, then
   use an agent to research the repository, test assumptions, and clarify the
   intended outcome.
2. **Decide and record:** Decide whether specifications or task files are
   needed, then review the resulting requirements, boundaries, and
   decomposition.
3. **Plan:** Have the agent investigate and propose the implementation,
   verification, and documentation plan; approve it before implementation.
4. **Implement:** Authorize the accepted plan and bring material discoveries
   back through planning.
5. **Verify and assess:** Ask what automated tests actually ran, complete
   useful human checkpoints, consider independent AI review, and evaluate the
   result.
6. **Resolve and deliver:** Plan accepted findings, reassess the result, and
   authorize a commit, pull request, merge, or deployment explicitly.

Every change follows this lifecycle. A small correction may use conversational
scope and a brief plan; complex work may use specifications, tasks, subtasks,
and staged plans.

## Before You Start

Short prompts work only when the model actually receives the applicable
project guidance. Before relying on an agent, make sure its developer/system
message—or, when necessary, its first user message—contains the relevant
`AGENTS.md` and task guidance.

See [Inspect Effective Instructions](#inspect-effective-instructions) for the
Crystal Lattice settings and a proxy-based method for inspecting other agents.

## What Humans Review

Five recurring concerns can help direct a review:

- **Requirements and outcomes:** Is the requested behavior present without
  important omissions or unapproved additions?
- **Scope and placement:** Does the work stay within the accepted boundary and
  belong in the component that owns the behavior?
- **Design and complexity:** Are important choices understandable, and is the
  solution no more complicated than the outcome requires?
- **Verification:** Do the planned or completed tests provide confidence at
  the real boundaries?
- **Documentation and remaining work:** Is consumer documentation current, and
  are limitations, deferred work, and unverified results visible?

Review what matters to your decision. Ask the implementing agent or an
independent reviewer to check detailed record or implementation consistency
when needed.

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
Useful follow-up questions include:

- What assumptions are being made, and what does the current implementation
  actually do?
- Which users, consumers, and parts of the system are affected?
- What alternatives have materially different outcomes or tradeoffs?
- What remains outside scope, what is already specified, and which decisions
  need human input?

### 2. Decide and Record the Work

Once the intended change is clear, decide which durable records will help
define, divide, and track it. Specification need and task structure are
separate decisions.

#### Decide About Specifications

- If the affected behavior already has a specification, update it whenever its
  intended behavior or design changes.
- A large new feature requires a specification.
- Other work may justify specifying an existing feature, durable behavior,
  public contract, or important design, regardless of the immediate change
  size.
- Do not create a new specification when no durable target would become
  clearer.

You may ask:

```text
Find the specifications governing this behavior. Tell me which existing
targets must change and whether a new specification would be useful or
required.
```

Current user documentation follows a different rule: whenever delivered
behavior affects a consumer, the owning user documentation must be updated.

#### Decide About Task Tracking

| Shape of the work | Recommended record |
|---|---|
| A small local change whose scope and decisions can remain clear in the conversation | No task file; keep the agreed scope in the conversation and prepare a conversational plan in stage 3 |
| One independently deliverable feature or correction with a coherent acceptance boundary | One task with its own requirements and implementation plan |
| Several independently deliverable features, or features with meaningful dependencies or separate approval points | A main task with one subtask for each independently deliverable feature or capability |

Skipping a task file does not skip planning. Updating or creating a
specification does not automatically require a main task with subtasks.

After accepting the record structure, ask the agent to create or update the
selected records:

```text
Create or update the agreed specifications, requirements, and tasks. Preserve
the accepted outcomes, boundaries, decomposition, and decisions for review.
```

Check that:

- intended outcomes are not missing;
- unrequested or redundant behavior was not added;
- requirements do not prescribe implementation choices unless those choices
  are necessary constraints;
- scope, affected consumers, non-goals, and decisions requiring human approval
  remain clear.

#### Check the Task Decomposition

Each task or subtask should produce an independently meaningful feature,
correction, enabling capability, or other acceptance outcome. It should
include the code, tests, documentation, and record updates required for that
outcome and leave the repository in a valid, useful state.

Avoid dividing one feature into technical touch points such as:

```text
010-backend-changes.md
020-frontend-changes.md
030-tests.md
040-documentation.md
```

Prefer independently deliverable boundaries:

```text
010-session-search-api-and-client-capability.md
020-saved-search-workflow.md
030-cross-device-search-synchronization.md
```

A shared technical capability can be a separate subtask when it has a stable
boundary, real consumers, and acceptance evidence of its own. Its location in
a shared package is not enough by itself.

When reviewing the proposed decomposition, check that:

- each task or subtask has an outcome that can be accepted independently;
- no subtask is merely the backend, frontend, test, or documentation phase of
  another feature;
- implementation, verification, and documentation remain with the outcome
  they support;
- dependencies represent genuine feature or capability ordering;
- completing one subtask does not leave an unusable partial feature that only
  becomes meaningful after another touch-point task.

#### Understand the Records

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
| Specification | What behavior and design the project is targeting |
| Requirements | Which completed outcomes matter and whether implementation, verification, and documentation are current |
| Task | What scope is accepted and tracked |
| Subtasks | Which independently deliverable features or capabilities are planned and reviewed separately |
| Execution plan | How the next concrete task will be implemented and verified |
| Current user documentation | What consumers can rely on in the delivered product |
| Current implementation documentation | How maintainers understand and operate the delivered implementation |

AI normally drafts and maintains these records. Review the intended behavior,
important boundaries, decisions, evidence, and remaining work. The agent
maintains their structure and consistency.

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

### 3. Plan the Implementation

The record choice made in stage 2 determines where the plan is reviewed:

- with no task file, prepare a brief conversational plan;
- with one task, write that task's execution plan;
- with subtasks, plan the next independently deliverable subtask rather than
  prematurely planning work that depends on earlier discoveries.

```text
Investigate and propose the implementation plan for <agreed change or task>.
Show how it covers the requirements, which parts of the system will change,
the important design choices and assumptions, and the planned verification and
documentation.
```

Before approving the plan, establish that:

- every accepted requirement is covered or explicitly deferred;
- each affected package or component needs to change and owns the behavior
  placed there;
- important alternatives and assumptions are visible;
- unnecessary abstractions, compatibility paths, configuration, duplication,
  or side changes are not being introduced.

A small experiment or real integration request may be more useful than
approving a detailed design built on an unverified provider, framework, native,
or external-service assumption.

#### Plan the Verification

AI will normally create and run the automated tests. Before approving the
plan, understand what confidence each layer will add:

| Evidence | Question for the plan |
|---|---|
| Unit tests | Which rules, edge cases, and failure behavior will they isolate? |
| Integration tests | Which real package, service, transport, persistence, provider, or native boundary will they cross, and through which production adapter or API? |
| End-to-end tests | Which public user or deployment journey will they exercise through production components? |
| Human checkpoint | What perception, exploration, product judgment, or real environment cannot be represented faithfully by an automated assertion? |

Not every change needs every kind of evidence. Also identify which current
user documentation changes for affected consumers and whether an existing
specification target changes.

### 4. Implement

Once you accept the plan, grant implementation authority plainly:

```text
I approve the implementation plan for <agreed change or task>. Proceed.
```

You do not need to direct every edit. For longer work, ask at a meaningful
checkpoint:

```text
Has implementation changed any accepted requirement, scope boundary,
important design assumption, verification plan, or documentation impact?
```

Return to stage 2 when a discovery changes requirements, specification targets,
scope, or task decomposition. Return to stage 3 when the required outcome
remains stable but the implementation or verification plan materially changes.

### 5. Verify and Assess the Result

Begin with a concise account of the result and its limits:

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
- Did the tests reach the production paths they claim to cover, or did setup,
  collection, harness selection, transport, or teardown prevent that?
- Is consumer documentation current, and is this the completion of the whole
  task, one stage, or a follow-up?

#### Choose Automated or Human Testing

- **Automate** repeatable procedures whose results an automated assertion can
  reliably observe, such as persisted settings, dialog content, simulator
  navigation, or service recovery.
- **Use a human checkpoint** for readability, usability, interaction quality,
  exploration, product meaning, or real environments the test setup does not
  faithfully represent.

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

- requirements and verification;
- scope and ownership;
- complexity and duplication;
- security, compatibility, persistence, native interaction, accessibility, or
  consumer documentation.

You can also request a narrow review:

```text
Review only requirement coverage and verification. Identify anything missing,
skipped, or supported by weaker evidence than the summary claims.
```

```text
Review the change for scope and design. Look for misplaced or duplicated
behavior and complexity the accepted requirements do not need.
```

Treat the findings as advice: the reviewer may miss problems or raise invalid
ones, and the acceptance decision remains yours.

### 6. Resolve Findings and Deliver

Decide which findings to accept, reject, or defer. Accepted findings use the
follow-up process below and return for assessment before delivery.

When the final result and evidence are acceptable, explicitly grant only the
delivery action you intend:

```text
Create a focused commit for the completed work in <task or agreed scope>.
```

Describing a commit, pull request, deployment, or merge as the next workflow
stage does not authorize it. The human grants that authority explicitly.

## Plan Every Follow-Up

A review finding, newly discovered bug, requested enhancement, or “while you
are there” improvement is another change. Its plan may be short, but it comes
before implementation.

```text
Investigate this follow-up and tell me whether it changes the recorded scope
or requirements, or only the implementation plan: <finding or requested
change>.
```

Before implementation, establish:

1. whether requirements, specification targets, scope, or task decomposition
   change;
2. which consumers, system boundaries, and current documentation are affected;
3. which automated evidence and human checkpoints must be added or repeated;
4. whether the work remains part of the current reviewable task.

Return to stage 2 for requirement, specification, scope, or decomposition
changes. Return to stage 3 when only the implementation or verification plan
changes. After approving and implementing the follow-up, reassess the affected
result before delivery.

## Inspect Effective Instructions

Short task prompts assume the agent already has the repository's standing
guidance. Confirm that the applicable developer/system message—or, when the
agent has no project-instruction mechanism, the first user message—contains:

- the relevant root and package `AGENTS.md` guidance;
- task guidance when task files are in use;
- the expected authority, safety, planning, testing, documentation, and
  delivery rules.

Asking the agent what it received is a useful first check, but inspecting the
effective message or outgoing request is stronger evidence.

### Crystal Lattice

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

### Other Agents

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

`--hide-headers` is recommended because authorization and other headers may
contain secrets. It suppresses header logging without removing headers from
the forwarded request. Request bodies may still contain private prompts,
source code, file paths, and conversation content. You are responsible for
the credentials, provider connection, terminal output, and retained logs on
your computer.

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

## Prepare and Review the Pull Request

When the implementation and evidence are ready for pull-request review,
explicitly ask the agent to prepare it:

```text
Open a pull request from the reviewed commits. Summarize the outcome, actual
scope, tests and human checkpoints completed, documentation updated, and
remaining limitations. Do not merge it.
```

Before accepting or merging it, check that:

- the pull request contains only the accepted scope and no unexplained
  changes;
- its description matches the accepted outcome;
- test and human-checkpoint claims are accurate;
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