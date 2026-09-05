# Contributing

Crystal Lattice is an early-stage project spanning Python, TypeScript, React
Native, Elixir, deployment tooling, documentation, and first-party plugins.
Focused fixes, tests, documentation improvements, and well-scoped feature
proposals are welcome.

This guide describes the recommended human-led, AI-assisted development
workflow. Scale it to the change: a local correction should stay lightweight,
while a cross-package or high-risk change needs durable decisions and stronger
verification.

## Quick Workflow

1. **Shape the change:** Agree on the problem, outcome, scope, constraints, and
   important questions.
2. **Record and decompose it:** Create only the specifications, requirements,
   tasks, and subtasks justified by the change.
3. **Plan the next task:** Have the implementing agent investigate and propose
   a plan; the human owner approves material decisions before implementation.
4. **Implement and verify:** The implementing agent changes the code and
   documentation, runs appropriate automated checks, and reviews the full
   diff.
5. **Validate and review:** Perform applicable human testing, consider an
   independent AI review, and complete the final human review.
6. **Address findings and deliver:** Resolve accepted findings, rerun affected
   checks, and commit, open a pull request, or merge only with explicit human
   authorization.

## Choose the Appropriate Process

These are proportional defaults, not rigid bureaucracy.

| Change | Recommended process |
|---|---|
| Small, local change | Briefly clarify scope, implement and test, review the diff, then deliver |
| Normal feature or bug fix | Use a task and approved plan, implement, run automated verification and applicable manual testing, then review |
| High-risk or cross-package change | Use specifications and traceable requirements, decompose into reviewable tasks, verify integrations and manual boundaries, obtain independent AI review, then seek human acceptance |

A change becomes higher risk when it affects public contracts, security or
privacy, persisted data, compatibility, migrations, deployment, several
packages, native platforms, or difficult-to-reverse operations.

## Roles

- **Human owner:** Defines intent, resolves requirement questions, approves
  plans and material decisions, performs or directly confirms human
  verification, reviews the result, and authorizes delivery.
- **Implementing agent:** Investigates, plans, implements, runs automated
  verification, updates documentation and work records, self-reviews the
  complete change, and prepares evidence.
- **Reviewing agent:** Independently inspects the proposed change and reports
  findings. It advises the human owner; it does not approve or accept the
  change.

For small work, one person may be both the human owner and final reviewer.
Those activities remain distinct even when the same person performs them.

## Recommended AI-Assisted Workflow

### 1. Shape the Change

**Owner:** Human-led, with AI assistance.

Clarify:

- the problem and intended outcome;
- who is affected;
- goals and non-goals;
- constraints and compatibility expectations;
- unknowns and requirement questions;
- whether the change is small, normal, or high risk.

An agent can inspect relevant documentation and code, identify missing context,
and compare materially different approaches. It should not implement during
this step.

**Output:** An agreed problem statement, scope, and set of open questions.

This is the stage where a longer initial prompt is often useful. Product
context, external requirements, user feedback, and business or domain
constraints may not exist in the repository.

### 2. Record and Decompose the Work

**Owner:** The implementing agent drafts; the human owner approves material
scope and requirements.

Depending on the change:

- create or update product, technical, and requirements specifications;
- create one task or a main task with subtasks;
- link tasks to specification requirement IDs;
- record dependencies and responsibility boundaries;
- preserve unresolved requirement questions;
- defer detailed plans for later subtasks when they depend on earlier
  discoveries.

A small change with one straightforward outcome and no durable contract may
use a task or agreed conversational scope without a separate specification.
Substantive, compatibility-sensitive, or cross-package work generally benefits
from durable specifications and requirements.

See the
[specification policy](docs/development/repository/specifications.md) and
[task-file guidance](agents/TASKS-v7.md) for the repository's detailed rules.

**Output:** Durable specifications when justified and a reviewable
decomposition of the work.

### 3. Plan and Approve the Next Task

**Owner:** The implementing agent plans; the human owner approves.

For the next executable task, the implementing agent:

- reads the task, its parent and dependencies, linked specifications, and
  relevant package guidance;
- inspects the current implementation rather than planning from assumptions;
- writes a Draft execution plan;
- identifies implementation boundaries, risks, documentation, automated
  checks, and applicable human verification;
- waits for approval before implementation.

The human owner checks requirement coverage, scope, contracts, compatibility,
security, persistence, migration, test realism, and human-verification needs.

**Output:** An approved execution plan for the next task.

### 4. Implement and Verify

**Owner:** Implementing agent.

The implementing agent:

- implements the approved plan through coherent, reviewable checkpoints;
- adds or updates tests when behavior changes;
- runs focused checks while developing and the required package, integration,
  type, lint, or build checks before completion;
- updates current documentation and work records;
- updates specifications and requirements when implementation discoveries
  change the accepted design or live state;
- stops for human input when requirements or material decisions must change;
- reviews the complete diff before presenting the result;
- does not commit unless explicitly authorized.

Automated verification is evidence produced by tools such as tests, builds,
linters, type checkers, schema checks, and link checks. It does not replace
human testing of a meaningful visual, operational, accessibility, installation,
or real-device boundary.

Implementing-agent self-review is also distinct from independent review. Before
handoff, the implementing agent should inspect the complete diff for accidental
changes, missing requirements, weak tests, stale documentation, and avoidable
complexity.

**Output:** An implemented change with automated evidence, a self-reviewed
diff, and current documentation and work records.

### 5. Validate and Review

**Owner:** Depends on the activity. Not every change needs every activity.

#### Manual testing — human, when applicable

Use manual testing for meaningful user-visible or operational boundaries such
as UI behavior, CLI workflows, installation, upgrades, real-device behavior,
external service integration, accessibility, visual behavior, and recovery
procedures.

An agent may prepare the checklist, setup instructions, and expected results.
Manual verification is complete only when a human actually performs the work
or directly confirms it. An agent cannot turn a proposed checklist or its own
simulation into human-verification evidence.

When there is no meaningful manual boundary, record `Not applicable` with a
short reason.

#### Independent AI review — recommended for normal and high-risk changes

A reviewing agent can inspect the requirements, specifications, plan,
implementation, tests, evidence, security, compatibility, failure behavior,
documentation, and unnecessary complexity.

Independent AI review is advisory. The reviewer reports findings but does not
approve the change, satisfy a human-verification requirement, or make the final
acceptance decision. It may be skipped for a very small change when its cost
exceeds its likely value.

#### Final human review — required before acceptance

The human reviewer decides:

- whether the intended outcome was achieved;
- whether the implementation matches the accepted scope;
- whether the tests are meaningful and exercise the claimed boundaries;
- whether automated and manual evidence is sufficient;
- whether AI-review findings were evaluated and resolved appropriately;
- whether security, compatibility, and operational risks are acceptable;
- whether documentation and migration guidance are current;
- whether unrelated or accidental changes are present.

**Output:** Accepted or rejected findings and a human acceptance decision.

### 6. Address Findings and Deliver

**Owner:** The implementing agent addresses accepted findings; the human owner
authorizes delivery.

The implementing agent:

- fixes accepted findings;
- updates implementation, tests, documentation, specifications, requirements,
  and task evidence as needed;
- reruns affected verification;
- reports blocked checks and remaining limitations honestly;
- records completion evidence when the work is complete.

The human owner:

- confirms that unresolved findings are acceptable;
- completes any remaining human verification;
- explicitly authorizes a commit, pull request, or merge.

Describing delivery as the final stage does not grant an agent permission to
commit. A commit request must be explicit.

**Output:** A focused, reviewed change with final evidence and authorized
delivery.

## How to Prompt an Agent

### Put Standing Rules in Standing Guidance

Recurring instructions should live where they can be maintained once:

| Location | What belongs there |
|---|---|
| Developer message | Platform-wide agent behavior, authority, safety, and tool-use rules |
| Root and package `AGENTS.md` | Repository and package constraints, ownership, important files, verification, and documentation routes |
| [`TASKS-v7`](agents/TASKS-v7.md) | Task-file creation, planning, approval, status, evidence, and completion rules when task guidance is active |
| Package documentation | Package-specific setup, supported behavior, architecture, testing, and maintenance |
| Specifications and requirements | Durable target behavior, design decisions, live implementation state, verification, documentation, and evidence |
| Task-specific user prompt | The current objective, new context, requested stage, scope boundaries, and authority newly granted by the human |

Testing expectations, documentation placement, task structure, commit
authorization, security rules, and review standards should not be copied into
every prompt when standing repository guidance already supplies them.

### Use a Longer Prompt When the Context Is New

A longer prompt is appropriate when introducing:

- a new product idea or user need;
- external requirements or business/domain constraints;
- user feedback not recorded in the repository;
- desired behavior that cannot be inferred from current code or docs;
- a material scope or requirements change.

Even then, focus the prompt on the missing context and requested outcome. The
examples below are concise delegation examples, not complete instruction
templates; they assume the repository guidance is already active.

## Example Prompts

### Brainstorm a Change

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

### Create Specifications and Tasks

```text
Using the agreed scope, create the necessary specifications and task files.

Preserve unresolved questions, approved decisions, requirement IDs, and
supporting references. Do not implement the change.
```

### Plan a Subtask

```text
Prepare the execution plan for <task path>.

Inspect the relevant current implementation and update the task with a Draft
plan. Highlight material decisions, risks, and the verification boundary. Do
not implement until I approve the plan.
```

### Implement an Approved Subtask

```text
The plan in <task path> is approved. Implement the task and keep its state
current.

Run the relevant verification and update linked specifications when
implementation discoveries require it. Do not commit.
```

### Prepare Manual Testing

```text
Prepare a concise human test checklist for <task or requirement path>.

Include setup, actions, expected observable results, and the requirement IDs
covered. Do not claim that any manual step has been performed.
```

### Request an Independent AI Review

```text
Review the current changes against <task path> and its linked specifications.

Focus on correctness, requirement gaps, security, compatibility, failure
behavior, test validity, and documentation drift. Report findings by severity
with file references. Do not modify files or approve the change.
```

### Address Review Findings

```text
Address the accepted findings <finding references>.

Update the implementation, tests, documentation, task evidence, and linked
specifications where required. Rerun affected verification. Do not commit.
```

### Authorize a Commit

```text
Create a focused commit for the completed work in <task path>. Include only
the approved in-scope files and use the repository's commit-message
conventions. Record the commit SHA in the task and linked requirements
evidence.
```

This last prompt grants commit authority for the described completed work. A
request to implement, test, review, or prepare a change does not.

## Human Review Checklists

### Plan Review

- Does the plan satisfy the accepted requirements?
- Are scope and non-goals clear?
- Are public contracts and compatibility addressed?
- Are security, persistence, migration, and failure behavior covered where
  relevant?
- Will the proposed tests exercise the claimed boundaries?
- Is meaningful manual verification identified?
- Is the work divided into reviewable checkpoints?

### Final Review

- Does the result solve the intended problem?
- Does the diff match the approved scope?
- Are there unrelated changes?
- Are the tests meaningful, and would they detect the relevant regression?
- Did the required automated checks actually run?
- Was applicable manual testing performed or directly confirmed by a human?
- Were AI-review findings evaluated?
- Are current documentation and target specifications consistent with their
  respective roles?
- Are security, compatibility, and operational concerns acceptable?
- Is the change ready to commit or merge?

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

Search existing issues before opening a duplicate. A prior issue is useful for
large or user-visible changes but is not required for a small, focused fix.
See [SUPPORT.md](SUPPORT.md) for bug, feature, support, and sensitive-report
routing.

### Setup, Tests, and Documentation

Use the owning package's entry point for prerequisites, installation, and
ordinary test commands. For example, the Core/application development
environment is documented in the
[root Core development quickstart](README.md#core-development-quickstart);
plugin, frontend, native application, service, and site setup belongs to the
linked package guidance above.

For every change:

- start with focused tests for the boundary you changed;
- add or update tests for public behavior and bug fixes;
- run integration, hosted-API, Docker, native, or end-to-end checks when the
  change crosses those boundaries;
- do not treat a skipped or gated test as passed;
- report checks that could not run and why;
- update documentation owned by the changed package when installation,
  configuration, APIs, behavior, or contributor workflows change;
- do not edit generated documentation trees directly.

### Required Public Pull-Request Checks

Public pull requests run four credential-free checks:

- `Public CI / Repository checks`
- `Public CI / Python unit tests`
- `Public CI / Frontend package tests`
- `Public CI / Landing and docs build`

The
[Public CI workflow](.github/workflows/public-ci.yml) is the executable source
of truth. The following practical local commands cover its main validation
boundaries.

Repository checks:

```bash
git diff --check
python scripts/check_github_actions_security.py
```

If `actionlint` is installed, it is also a useful additional local workflow
check:

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
TestFlight, and deployment. Those checks still apply when a change crosses
their boundary; run and report them explicitly rather than treating their
absence from required CI as evidence that they are unnecessary.

### Pull Requests

Keep pull requests focused enough to review and validate. In the description:

- explain the outcome and affected boundary;
- link the relevant issue when one exists;
- list the tests and manual checks actually performed;
- identify public documentation, compatibility, security, privacy, deployment,
  or data-migration effects;
- call out meaningful deferred work or known limitations.

Do not claim that a skipped or gated test passed. Avoid unrelated formatting,
generated output, or cleanup in the same pull request.

### Sensitive and Local Data

Never commit credentials, tokens, private keys, personal data, private
conversations, runtime session data, unnormalized captured logs, local user
paths, build caches, or other machine-specific files.

Sanitize logs and screenshots before attaching them to issues or pull requests.
If you discover a possible vulnerability or exposed credential, follow
[SECURITY.md](SECURITY.md) instead of opening a public issue.

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