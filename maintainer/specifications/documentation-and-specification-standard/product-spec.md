# Documentation and specification standard product specification

## Purpose

The repository needs documentation and specification rules that are easy to
apply during ordinary work, precise enough for agents, reusable outside this
project, and maintainable without exposing internal workflow machinery to every
reader.

## Users

### Contributors and agents applying the rules

These users need to:

- decide where documentation belongs;
- identify each document's audience and avoid relying on context that audience
  cannot access or is not expected to know;
- decide whether a durable specification is justified;
- identify the package or shared scope that owns a contract;
- update a target specification before implementation;
- use requirements to understand live implementation and verification state;
- keep public and maintainer documentation aligned with committed behavior;
- preserve ownership, source-of-truth, validation, and audience boundaries when
  the normal workflow is blocked;
- find the effective repository rules without reading implementation history or
  validation internals.

### Maintainers changing the rules

These users need to:

- distinguish reusable concepts from repository-specific policy;
- change standards without duplicating rules between output pages;
- understand how AGENTS, task guidance, contributor guidance, publication, and
  validation fit together;
- trace output pages and files to requirements, tasks, tests, and delivery
  evidence;
- evolve the standards while preserving a clear user-facing result.

## Target experience

An ordinary user starts from repository or package guidance, reaches the
repository policy, and follows the linked generic standard. The user does not
need to open `maintainer/` to apply the rules.

A maintainer changing the standards is explicitly routed to this
meta-specification, its requirements, and the owning task before editing the
user-facing pages or supporting tooling.

The generic pages remain package-neutral and reusable. The repository pages
map those rules to actual packages, paths, plugin documentation, task files,
agent guidance, site assembly, and validation.

Every output document remains understandable within its own audience. An agent
may use broader repository context to make a decision, but does not copy task,
phase, requirement, approval, evidence, or maintainer context into a document
whose readers do not have that context.

A human contributor can begin with a rough description and use AI-assisted
brainstorming to research the repository, compare approaches, and shape the
change. Every change and follow-up receives a reviewed plan before
implementation; a small change may use a conversational plan while complex or
multi-part work uses task-owned staged plans.

The quick workflow mirrors the seven detailed steps: brainstorming, reviewing
specifications and tasks, approving a plan, supervising implementation,
questioning evidence, requesting independent AI review when useful, and
planning every follow-up. A three-scenario process table shows the normal task
and specification forms for small local changes, normal features or bug fixes,
and high-risk or cross-package changes.

The contributor workflow helps the human verify that applicable repository and
task guidance actually reached the model, review important specification and
task decisions, question planned and completed unit/integration/end-to-end
evidence, identify where human judgment is still useful, and explicitly
authorize delivery. Human review concentrates on requirements and outcomes,
scope and placement, design and complexity, verification, and current
documentation or remaining work. Stage-specific prompt examples appear where
they are used and assume standing instructions are already active.

The workflow calls out recurring agent mistakes such as missing or expanded
requirements, misplaced changes, unnecessary complexity, weak verification
boundaries, stale consumer documentation, and incomplete work presented as
complete. Independent AI review and follow-up planning are separate numbered
steps whose text makes clear when they apply.

When subtasks are proposed, the human checks that each one delivers a usable,
tested improvement or completes an isolated responsibility. Deliverable
iterations use subtasks, while partial implementation and approval checkpoints
remain stages inside one task.

Specification need is considered separately from immediate change size.
Existing specifications remain current whenever their target behavior or
design changes, large new features require specifications, and other work may
justify specifying an existing feature or durable contract. Current user
documentation is updated whenever delivered behavior affects a consumer.

## Specification and current state

Specifications describe intended targets and may temporarily differ from
implementation. Requirements track the live implementation, verification,
documentation, and evidence state.

Task files are the default approval and execution record. Public user
documentation and implementation/maintainer documentation describe current
behavior and normally remain consistent with committed code. A user may
explicitly request a different commit order.

Simple specification changes are normally committed with their implementation
or in the immediately preceding commit. Separate target versions are optional
for major changes when they materially improve clarity.

## Goals

- Establish a reusable generic documentation standard.
- Establish a reusable generic specification standard.
- Apply those standards through a concise repository-specific policy.
- Allow any package to own specifications for behavior it defines, including
  package-specific refinements of broader contracts.
- Keep shared plugin-authoring rules explicit without making them universal
  package rules.
- Make every documentation page discoverable from an appropriate entry point.
- Keep normative contracts, consumer guidance, implementation guidance, and
  standards-maintenance material distinguishable.
- Give every document or maintained file an audience and context boundary,
  define allowed reference directions among document and workflow roles, and
  translate rather than leak information when it crosses a boundary.
- Use concrete nouns for documentation, code, specifications, requirements,
  tasks, tests, and generated output rather than a generic umbrella label.
- Preserve scope, ownership, source-of-truth, validation, and publication
  boundaries when a compliant workflow is unavailable.
- Use requirements as the live traceability record.
- Keep the process proportional and avoid placeholder documentation.
- Provide a human-led contributor workflow in which every change and follow-up
  is planned before implementation.
- Help humans verify effective instruction delivery and review AI-produced
  specifications, task plans, automated evidence, documentation, and delivery
  readiness through understandable decisions and focused follow-up questions.
- Keep specification decisions independent from immediate change size and
  require current user-documentation updates for consumer-affecting behavior.
- Make ordinary changes understandable primarily through Git history.
- Verify that representative agents can apply the authored instructions
  through reusable maintainer-owned behavioral evaluation while keeping model
  judgment separate from static and human evidence.
- Demonstrate guidance improvements against the exact pre-change instructions
  before selecting the shortest general wording that corrects observed
  boundary failures.

## Non-goals

- Requiring every package to create the full documentation structure
  immediately.
- Requiring every change to have a full product/technical/requirements set.
- Requiring mandatory lifecycle status inside every specification.
- Treating a specification as evidence of current implementation.
- Publishing maintainer specifications or task-guidance evaluation internals
  as ordinary user documentation.
- Duplicating the full generic standard in the repository policy.
- Reconstructing undocumented behavior across the repository solely to fill a
  target directory shape.
- Selecting one mandatory versioning format for major specification changes.
- Moving all maintainer tooling as part of creating this approval package.
- Treating one model response or reviewer score as sole evidence that the
  standards are correct or human verified.

## Acceptance examples

### Package-specific UX specification

A frontend package may define a substantial platform-specific UX specification
that refines a broader portable behavior contract. The package specification
links the broader contract, adds package-owned requirements, and does not
silently weaken shared semantics.

### Small specification change

An agent updates a target specification, requirements, implementation, tests,
and current documentation. The spec and code are committed together or in two
adjacent commits, or in another order explicitly requested by the user, while
requirements show the live transition.

### Major multi-commit change

The target remains in one specification when clear. A separate target version
or change document is introduced only when it makes the intended result and
current implementation easier to distinguish. Temporary progress links the
task and affected requirement IDs and is removed after verification.

### Standards maintenance

An agent changing task guidance reads this meta-specification and requirements,
updates the approved task, modifies the user-facing rules and maintainer
tooling, and records evidence. An ordinary feature agent reads only the
effective generic and repository rules.

### Audience-bound consumer documentation

An agent implementing one phase of a multi-commit target may use tasks,
requirement IDs, and temporary progress while working. The package README
describes only current user-visible behavior in public vocabulary. It does not
mention internal phase names, requirement IDs, task paths, or future targets.
If a current limitation matters to users, it is translated into a
self-contained user-domain statement.

### Blocked generated-documentation workflow

An agent finds a defect in generated documentation and corrects the authored
source. If the approved generator is absent or fails, the agent leaves generated
output unchanged, reports the blocker and remaining regeneration action, and
does not claim that publication output was refreshed.

The scenario first runs against the pinned pre-change guidance. Candidate
wording is evaluated only after the baseline exposes the boundary failure in at
least one representative model run. The same seed, task prompt, fixture, and
assertions are then reused to compare concise and, only when needed, expanded
guidance variants.

### Human-led AI-assisted change

A contributor describes a desired change in ordinary freehand language and
asks an agent to research and brainstorm it. The human reviews the proposed
scope, specification decision, requirements, test boundaries, user
documentation effects, and implementation plan before authorizing work.

After implementation, the human asks what unit, integration, and end-to-end
tests ran, what each one demonstrated, what user documentation changed, and
what remains unverified. Repeatable checkpoints with machine-observable
results become automated tests; human checkpoints focus on perception,
exploration, product judgment, or a real environment automation does not
faithfully represent. Findings return through planning before implementation,
and delivery occurs only after explicit human authorization.

## Approved August 18 calibration extension

### Additional user needs

Contributors and agents applying the rules also need to:

- know when repository guidance requires reading the complete directly
  relevant routed standard pages before editing;
- make clear package-local placement decisions without burdening the user with
  internal ownership jargon or duplicate confirmation;
- honor an explicit approved documentation or specification layout when it
  preserves required content and repository boundaries.

### Additional target experience

A documentation task makes required reading proportionate and explicit. Agents
read the complete directly relevant routed pages before creating, moving, or
materially restructuring documentation or specifications, while a local
factual correction does not require unrelated standards research.

When placement is clear, the agent implements it without asking the user to
confirm an obvious package path or explaining internal ownership terminology.
When multiple materially different scopes remain plausible, the agent gives a
short recommendation and asks one focused question.

Recommended file layouts are defaults rather than mandatory schemas. An
explicit user- or work-item-approved alternative is honored unless it would
violate audience, authoritative-source, generated-output, discoverability, or
required-content boundaries.

### Additional goals

- Define explicit and proportional triggers for reading routed standards in
  full.
- Use clear placement and authoritative-source language without forcing users
  to discuss internal ownership mechanics for obvious tasks.
- Treat standard file layouts as recommended defaults and honor explicit safe
  alternatives.

### Additional non-goals

- Requiring one mandatory documentation or specification file layout.
- Requiring user confirmation for an obvious package-local documentation
  placement.

### Routed documentation reading

An agent asked to create a package documentation structure reads the root and
nearest package guidance, then reads the relevant repository-policy and generic
standard pages in full before editing. An agent correcting a factual typo in an
already-owned page does not load unrelated structure and specification rules.

### Clear package-local placement

An agent asked to document behavior defined by one package creates the
documentation with that package without asking the user to confirm the obvious
location or discussing an “honest normative owner.” Its response reports the
result and paths. If two materially different scopes remain plausible, it
recommends one and asks a focused question.

### Explicit layout override

An approved specification task requests one `decisions.md` file instead of a
`decisions/` directory. The agent follows that structure, links the file from
the specification index, preserves required decision content, and does not
create both forms or refuse merely because the standard shows a directory as
the default.