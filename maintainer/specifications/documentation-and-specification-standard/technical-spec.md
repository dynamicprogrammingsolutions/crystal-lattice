# Documentation and specification standard technical specification

## Architecture

The target uses three documentation layers with distinct authority and
audiences:

| Layer | Purpose | Publication |
|---|---|---|
| Generic standards | Reusable, package-neutral documentation and specification concepts | Public |
| Repository policy | Crystal Lattice paths, profiles, exceptions, and tooling integration | Public |
| Maintainer material | Specifications, evaluation tooling, and implementation details for evolving the standards | Not public by default |

The generic standards and repository policy are output artifacts governed by
this meta-specification. They do not link back to the meta-specification.

## Target source structure

```text
docs/
└── development/
    ├── index.md
    ├── standards/
    │   ├── index.md
    │   ├── documentation.md
    │   └── specifications.md
    ├── repository/
    │   ├── index.md
    │   ├── documentation.md
    │   └── specifications.md
    └── specifications/
        └── <cross-package-capability>/

maintainer/
├── README.md
├── specifications/
│   └── documentation-and-specification-standard/
│       └── agent-behavior-verification/
└── <standards-maintenance tooling and tests>
```

`maintainer/specifications/` intentionally shortens the ordinary
`<package>/docs/development/specifications/` shape. The whole `maintainer/`
domain is development-only, so intermediate `docs/development/` indexes would
not distinguish another audience or source-of-truth boundary.

## Generic standard boundary

The generic pages use package-neutral terms such as:

- repository;
- package;
- documentation entry point;
- package user;
- package contributor;
- work-tracking artifact;
- documentation-site source and generated output.

They define:

- documentation profiles and artifact roles;
- normative contract, consumer guide, implementation guide, and generated
  reference distinctions;
- package-local ownership;
- generalized specification ownership and package-specific refinements;
- specifications as targets;
- requirements as live-state tracking;
- approval and execution through the repository's work-tracking mechanism;
- current-state public and maintainer documentation;
- proportional specification artifacts;
- anti-duplication and discoverability;
- evidence, verification, and optional decision records.

They do not name Crystal Lattice packages, `plugins/docs/`, `tasks/`,
`TASKS-v7`, `docs_site/prepared/`, or repository-specific test harnesses.

## Repository-policy boundary

The repository policy maps generic concepts to:

- root and package documentation paths;
- public-package, small-package, shared-domain, and maintainer profiles;
- root cross-package specifications;
- `plugins/docs/` as the shared plugin-authoring documentation domain;
- individual plugin package ownership;
- `tasks/` as approval and execution tracking;
- root and package `AGENTS.md`;
- `CONTRIBUTING.md`;
- canonical and bundled `TASKS-v7`;
- documentation-site registry, assembly, navigation, and deployment;
- compatibility behavior for relocated public pages;
- documentation and task-guidance validation.

Repository policy extends the generic rules and contains only local mappings,
exceptions, and operational requirements. It does not restate the complete
generic explanations.

## Generalized specification ownership

Every package may define specifications for behavior it owns. A package is not
limited to documenting implementation merely because it also implements a
broader contract.

Choose the narrowest authoritative scope:

1. Behavior owned by one package is specified with that package.
2. A package-specific refinement is specified with that package and links the
   broader contract.
3. A shared abstraction is normally specified with the package that defines
   it, even when several packages consume it.
4. A cross-package scope is used when independently owned packages must
   coordinate and no package is the honest normative owner.

A package-specific specification may add or strengthen requirements and define
allowed platform behavior. It must not silently weaken or contradict a broader
contract. Approved exceptions are linked from both scopes.

Before creating a substantial package specification, the agent proposes its
owner, scope, justification, relationship to existing contracts, and expected
artifacts. The user approves creation through the task workflow unless the
existing approved task already authorizes it.

## Target, requirements, task, and current documentation

| Artifact | Authority |
|---|---|
| Specification | Intended target behavior and design |
| Requirements | Live implementation, verification, documentation, and evidence state |
| Task | Approval, execution scope, plan, findings, and completion |
| Public user docs | Current supported behavior |
| Implementation/maintainer docs | Current implementation and maintenance behavior |

Specifications are updated before implementation. They are not proof that the
target is currently available.

For small changes, the specification is normally committed with the code or in
the immediately preceding commit. New capabilities begin with a specification
and requirements. Major changes introduce separate target versions only when
one evolving target would be confusing.

Temporary progress in a specification or its index is used only for work
expected to span more than one commit when target/current divergence would
otherwise be unclear. It links the task and affected requirement IDs and is
removed after all relevant requirements are verified.

## Documentation authority and duplication

Substantive pages fit one authority class:

- normative specification;
- consumer/user guide;
- implementation/maintainer guide;
- generated reference;
- repository or documentation infrastructure.

Each behavioral contract has one normative owner. Other pages may summarize
for their audience, but identify the canonical contract and do not independently
redefine complete lifecycle, compatibility, persistence, or protocol semantics.

Implementation mapping pages link their target specification and describe
current code, ownership, invariants, and tests. User guides teach current
supported use. Target-only behavior remains in specifications and requirements
until implementation is committed.

## Discoverability

Every page participates in an entry-point chain:

```text
repository docs index
  -> development index
    -> standards, repository policy, or cross-package specification index

package README/AGENTS/docs index
  -> package development index
    -> package specification or maintainer page

shared-domain index
  -> shared consumer guide
```

Every authored page is reachable within at most two documentation links from
the nearest repository, package, or shared-domain entry point.

Indexes remain concise but complete:

- every multi-page development scope has an index;
- every specification index links its authored artifacts;
- every package development index is linked by a package entry point;
- specification indexes link primary user guides and implementation mappings
  where useful;
- public package docs are registered for site assembly.

## Maintainer boundary

`maintainer/` is not a public documentation source. It owns:

- meta-specifications for standards and agent workflows;
- deterministic and real-model evaluation tooling for those workflows;
- fixtures and review-bundle preparation belonging to that tooling;
- future standards-maintenance utilities whose audience is the maintainers of
  the rules rather than ordinary package users.

Existing task-guidance evaluation under `test/task_guidance/` and its dedicated
fixtures are targeted for relocation under the reusable agent-evaluation
framework's `maintainer/`-owned domain. Subtask 015 creates the framework and
documentation-standard consumers. The task-guidance alignment subtask then
moves and adapts the existing task-guidance consumer, updates commands and
references, and verifies equivalent behavior.

Production/package tests remain with their owning packages. `maintainer/` is
not a replacement for ordinary shared test infrastructure.

## Agent routing

Root `AGENTS.md` distinguishes:

- **Applying the rules:** read repository policy, generic standards, and the
  owning package entry points.
- **Maintaining the rules:** additionally read this meta-specification,
  requirements, active task, and relevant maintainer tooling documentation.

Ordinary output pages do not expose task chronology, evaluation internals, or
links to this meta-specification.

## Publication

Package-local authored files remain sources of truth. Prepared and built site
trees are generated and never edited directly.

The package registry declares public sources and destinations. `AGENTS.md` and
`maintainer/` are excluded by default. Repository standards and policy are
public development guidance unless a page contains explicitly sensitive
material.

Public user and implementation/maintainer documentation must match committed
code. A working tree may stage documentation first, but it is committed with
the implementation that makes new current-state claims true.

## Migration

Adoption is incremental:

- do not create empty package trees or placeholder quickstarts;
- move ownership-clear pages with bounded verification;
- preserve public URLs through compatibility behavior during the initial
  migration;
- defer uncertain pages rather than reconstructing broad undocumented
  behavior;
- record deferred pages with likely owner, reason, and useful trigger.

The first migration covers Core Python, application configuration, shared
plugin overview, selected root architecture/protocol/reference pages, and
generated examples/reference ownership.

## Validation

Deterministic validation should cover, in stages:

- broken relative links;
- page reachability from owning indexes;
- specification indexes omitting authored artifacts;
- duplicate requirement IDs;
- invalid registry sources, IDs, destinations, and collisions;
- package docs assembly and source/output boundaries;
- canonical/bundled task-guidance parity;
- moved maintainer-tool commands and fixtures;
- public docs and navigation paths;
- normal MkDocs build and newly introduced warnings.

Behavioral instruction validation should additionally exercise whether
representative supported agents can apply `DOCGEN-*` and `DOCREP-*` rules
through the programmatic framework specified in
`maintainer/specifications/agent-evaluation-framework/`.

Detailed consumer scenarios are owned by
[agent-behavior verification](agent-behavior-verification/index.md). They
deliver the exact candidate AGENTS/routed files through normal agent
mechanisms, use short human-style task prompts, and assert on generated files,
mutations, provenance, and responses. They do not ask agents to author or
summarize the standards being tested.

Cached seed conversations are narrow factual investigations of a concrete
package, issue, task, or contract. A seed may feed several closely related
continuations and is reusable across candidate-guidance revisions because
guidance is added only after the continuation forks.

Behavioral model results supplement rather than replace:

- static checks of the authored pages;
- deterministic repository assertions;
- explicit human review.

Acceptance and contract tests may reference requirement IDs. Ordinary
low-level tests do not need them. Manual verification is recorded only when a
human performs or directly confirms it.

## Bootstrap

This meta-specification and requirements are created from the already approved
task decisions before the output standards exist. They are the target for the
remaining implementation.

The bootstrap does not claim that existing documentation conforms. After the
generic and repository pages are authored, this meta-specification is reviewed
once against the resulting standard and adjusted through the task workflow if
the approved target changed.