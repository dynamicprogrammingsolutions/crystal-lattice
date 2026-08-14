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
- identify each artifact's audience and avoid relying on context that audience
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
- trace output artifacts to requirements, tasks, tests, and delivery evidence;
- evolve the standards while preserving a clear user-facing result.

## Target experience

An ordinary user starts from repository or package guidance, reaches the
repository policy, and follows the linked generic standard. The user does not
need to open `maintainer/` to apply the rules.

A maintainer changing the standards is explicitly routed to this
meta-specification, its requirements, and the owning task before editing the
user-facing artifacts or supporting tooling.

The generic pages remain package-neutral and reusable. The repository pages
map those rules to actual packages, paths, plugin documentation, task files,
agent guidance, site assembly, and validation.

Every output artifact remains understandable within its own audience. An agent
may use broader repository context to make a decision, but does not copy task,
phase, requirement, approval, evidence, or maintainer context into an artifact
whose readers do not have that context.

## Specification and current state

Specifications describe intended targets and may temporarily differ from
implementation. Requirements track the live implementation, verification,
documentation, and evidence state.

Task files are the default approval and execution record. Public user
documentation and implementation/maintainer documentation describe current
behavior and must remain consistent with committed code.

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
- Make every documentation artifact discoverable from an appropriate entry
  point.
- Keep normative contracts, consumer guidance, implementation guidance, and
  standards-maintenance material distinguishable.
- Give every artifact an audience and context boundary, define allowed
  reference directions among artifact roles, and translate rather than leak
  information when it crosses a boundary.
- Preserve scope, ownership, source-of-truth, validation, and publication
  boundaries when a compliant workflow is unavailable.
- Use requirements as the live traceability record.
- Keep the process proportional and avoid placeholder documentation.
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
adjacent commits, while requirements show the live transition.

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