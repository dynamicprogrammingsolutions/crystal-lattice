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
5. **Question and verify:** Ask what automated tests actually ran, perform
   applicable human testing, consider independent AI review, and inspect the
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
The agent can draft them; your job is to review the decisions they express.

```text
Turn our agreed direction into the appropriate specifications, requirements,
and task structure. Bring back the important scope and design decisions for my
review.
```

Look for substance rather than mechanical perfection:

- Does the proposed behavior solve the problem you described?
- Are the affected users and observable workflows represented?
- Are boundaries and non-goals clear?
- Are important failure, compatibility, security, privacy, persistence,
  migration, and rollout concerns visible?
- Are unresolved requirement questions still presented as questions?
- Are the requirements understandable as outcomes that could be accepted?
- Is the task split useful for review, or does it fragment one coherent
  change?

The agent can audit requirement IDs, links, status fields, and other
consistency details. Ask for that audit when useful; you do not need to perform
it manually.

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

The plan should let you answer:

- What will change, and what will remain unchanged?
- Does it satisfy the accepted requirements?
- Does it preserve public contracts and compatibility?
- Are security, persistence, migration, failure, and operational behavior
  addressed where relevant?
- Which current user documentation will change for affected consumers?
- Does an existing specification need an update?
- What could cause the work to return for another decision?

#### Review the Test Strategy

AI will normally create and run the automated tests. Before approving the
plan, make sure the proposed evidence matches the behavior:

| Evidence | Question for the plan |
|---|---|
| Unit tests | Which rules, edge cases, and failure behavior will they isolate? |
| Integration tests | Which real package, service, transport, persistence, provider, or native boundary will they cross? |
| End-to-end tests | Which public user or deployment journey will they exercise without a test-only shortcut? |
| Manual testing | Which visual, accessibility, device, installation, upgrade, or operational result needs human observation? |

Not every change needs every kind of evidence. The important point is to make
the boundary choice explicit before implementation.

### 4. Authorize and Supervise Implementation

Once you accept the plan, grant implementation authority plainly:

```text
I approve the plan in <task path>. Proceed with the implementation.
```

For a conversational plan:

```text
That plan looks right. Please implement it.
```

You do not need to direct every edit. Watch instead for evidence that the work
has crossed an accepted boundary or encountered a new material decision.

Useful questions during a longer implementation include:

- Are you still within the approved scope?
- Did repository inspection change any assumptions?
- Has the implementation exposed a requirement or compatibility question?
- Is a planned test unable to exercise the real boundary?
- Has consumer or maintainer documentation impact changed?

If the answer changes the required outcome, contract, ownership, persisted
data, security model, or another important decision, return to planning before
authorizing that work.

### 5. Question the Evidence and Review the Result

An implementation summary is the start of review, not proof by itself. Ask for
the evidence at the level you need:

```text
Tell me which unit, integration, and end-to-end tests actually ran, what
boundary each one exercised, whether anything skipped or failed, what remains
unverified, and which documentation changed.
```

Check that:

- reported commands actually collected and completed the intended tests;
- a direct function test is not described as HTTP integration;
- a mocked frontend test is not described as backend integration;
- a simulator harness is not described as a network end-to-end test;
- skips, collection failures, teardown errors, open handles, and background
  failures are not counted as successful runs;
- test-only shortcuts do not hide the behavior the test claims to cover;
- documentation claims match the implemented behavior;
- unrelated changes are not mixed into the diff.

#### Prepare and Perform Human Testing

Use human testing when a meaningful result must be observed in a UI, terminal,
installation, upgrade, real device, external service, accessibility flow, or
operational procedure. An agent can prepare the steps:

```text
Prepare a short human test checklist for <change or requirement>, including
setup, actions, and expected observable results.
```

Human verification is complete only when a human performs the test or directly
confirms it. An AI-generated checklist, simulation, screenshot description, or
automated assertion does not become human evidence by being recorded in a
task.

#### Request Independent AI Review

For normal, high-risk, or unfamiliar changes, another agent can inspect the
work independently:

```text
Independently review the current change against <task or specification>.
Report concrete findings by severity and include file references.
```

The reviewing agent advises you. It does not accept the implementation,
resolve whether a risk is acceptable, or complete human verification.

Your final review decides whether:

- the intended outcome was achieved;
- the implementation stayed within accepted scope;
- test and documentation evidence is sufficient;
- applicable human testing was completed;
- review findings were evaluated;
- security, compatibility, and operational risks are acceptable.

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
delivery action you intend. For example:

```text
Create a focused commit for the completed work in <task path>.
```

Or:

```text
Open a pull request for the reviewed commits and summarize the verified
boundaries and remaining limitations.
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

AI normally drafts and maintains these records. Review the product meaning and
material decisions; ask an implementing or reviewing agent to check mechanical
consistency.

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

## Repository and Pull-Request Essentials

### Find the Owning Package

Start with the README and public development documentation for the package or
subsystem that owns the behavior:

- Repository-wide:
  [development documentation](docs/development/index.md),
  [documentation structure](docs/development/repository/documentation.md), and
  [architecture](ARCHITECTURE.md)
- Core SDK:
  [package README](core/python/README.md) and
  [development index](core/python/docs/development/index.md)
- Terminal/server application:
  [package README](application/python/README.md),
  [documentation index](application/python/docs/index.md), and
  [feature-development guide](application/python/docs/development/terminal-and-http-features.md)
- Plugins:
  [shared plugin-authoring documentation](plugins/docs/index.md) and the
  individual plugin's README
- Shared frontend:
  [frontend SDK](packages/frontend-sdk/README.md),
  [React bindings](packages/frontend-sdk-react/README.md), and
  [React Native components](packages/frontend-rn-components/README.md)
- Applications:
  [mobile](mobile/crystal-lattice-control-rn/README.md) and
  [desktop](desktop/crystal-lattice-control-desktop-rn/README.md)
- Services:
  [bridge](bridge-elixir/README.md) and
  [cloud orchestrator](cloud-orchestrator/README.md)
- Sites:
  [landing page](landing_page/README.md) and
  [documentation site](docs_site/README.md)

Ask the agent to search existing issues before opening a duplicate. A prior
issue is useful for large or user-visible changes but is not required for a
small, focused fix. See [SUPPORT.md](SUPPORT.md) for bug, feature, support, and
sensitive-report routing.

Use the owning package's entry point for prerequisites, installation, and test
commands. The Core/application environment starts with the
[root Core development quickstart](README.md#core-development-quickstart).

### Verify Tests and Documentation

Before accepting a change, ask the agent:

- which focused checks and package suites ran;
- which integration, hosted-API, Docker, native, or e2e checks applied;
- which applicable checks could not run and why;
- whether any test skipped or failed before or after its assertions;
- which consumer and maintainer documentation changed;
- whether generated documentation was regenerated through its owning process
  rather than edited directly.

If consumer behavior changed, user documentation must change with it. If
implementation, architecture, testing, or maintenance behavior changed, the
owning development documentation must stay current.

### Required Public Pull-Request Checks

Public pull requests run four credential-free checks:

- `Public CI / Repository checks`
- `Public CI / Python unit tests`
- `Public CI / Frontend package tests`
- `Public CI / Landing and docs build`

The
[Public CI workflow](.github/workflows/public-ci.yml) is the executable source
of truth. These practical local commands cover its main validation boundaries.

Repository checks:

```bash
git diff --check
python scripts/check_github_actions_security.py
```

If `actionlint` is installed, it is a useful additional local workflow check:

```bash
actionlint .github/workflows/*.yml
```

Python unit tests:

```bash
python -m pip install \
  -e "core/python[dev]" \
  -e application/python \
  -e "plugins/openai_responses[dev]" \
  -e plugins/tool-compat-shared \
  -e plugins/mcp-shared \
  -e plugins/web-fetch-shared
pytest core/python/tests -q -m "not integration"
pytest application/python/tests -q -m "not integration and not docker"
```

Shared frontend package tests:

```bash
npm ci
npm --workspace @crystal-lattice/frontend-sdk test
npm --workspace @crystal-lattice/frontend-sdk-react test
npm --workspace @crystal-lattice/frontend-rn-components test
```

Landing-page and documentation builds:

```bash
yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

Required public CI intentionally excludes hosted-provider tests, Docker/cloud
integration, mobile/desktop native builds, native UI tests, signing,
TestFlight, and deployment. Their absence from required CI does not make them
unnecessary when a change crosses those boundaries.

### Review the Pull Request

Make sure the pull-request description:

- explains the outcome and affected boundary;
- links the relevant issue when one exists;
- lists the tests and human checks actually performed;
- identifies user-documentation, compatibility, security, privacy,
  deployment, and data-migration effects;
- calls out meaningful deferred work or known limitations.

Do not accept a claim that a skipped or gated test passed. Keep unrelated
formatting, generated output, and cleanup out of the same pull request unless
they are part of the accepted scope.

### Sensitive and Local Data

Never commit credentials, tokens, private keys, personal data, private
conversations, runtime session data, unnormalized captured logs, local user
paths, build caches, or other machine-specific files.

Sanitize logs and screenshots before attaching them to issues or pull
requests. If you discover a possible vulnerability or exposed credential,
follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

### Contribution License

Contributions are accepted under the license that applies to the file or
subtree being changed. Most original Crystal Lattice material is Apache-2.0,
while more specific license and notice files may apply within a subtree. See
[LICENSE](LICENSE) and [LICENSING.md](LICENSING.md) before contributing.

By intentionally submitting a contribution for inclusion, you agree that it
may be distributed under the applicable project or subtree license. The
project does not currently require a separate contributor license agreement or
Developer Certificate of Origin signoff.

### Participation

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