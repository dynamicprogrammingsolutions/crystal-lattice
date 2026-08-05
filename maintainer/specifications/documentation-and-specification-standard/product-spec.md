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
- decide whether a durable specification is justified;
- identify the package or shared scope that owns a contract;
- update a target specification before implementation;
- use requirements to understand live implementation and verification state;
- keep public and maintainer documentation aligned with committed behavior;
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
- Use requirements as the live traceability record.
- Keep the process proportional and avoid placeholder documentation.
- Make ordinary changes understandable primarily through Git history.

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