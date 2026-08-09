# Crystal Lattice specification policy

This page maps the
[reusable specification standard](../standards/specifications.md) to Crystal
Lattice paths, task files, agent guidance, requirements, and validation.

## Locations

Package-owned targets:

```text
<package>/docs/development/specifications/<capability>/
```

Cross-package targets with no honest package owner:

```text
docs/development/specifications/<capability>/
```

Standards and agent-workflow maintenance targets:

```text
maintainer/specifications/<capability>/
```

`maintainer/specifications/` intentionally omits `docs/development/` because
the whole maintainer domain is development-only.

## Ownership

The generic ownership rules apply to every package.

- A package may define a specification for behavior it owns.
- A package may define a substantial platform- or package-specific refinement
  of a broader portable contract.
- A package that defines a shared abstraction may own its canonical
  specification even when several packages consume it.
- Root cross-package specifications are reserved for coordination without an
  honest package owner.

Before creating a substantial specification, an agent presents the proposed
owner, scope, justification, relationship to existing contracts, and expected
artifacts. User approval is required unless the active approved task already
authorizes creation.

A package refinement links the broader contract and relevant requirement IDs.
It may add or strengthen package requirements but may not silently weaken or
contradict the broader target. Approved exceptions are linked from both scopes.

## Target, requirements, tasks, and current docs

Crystal Lattice uses:

| Artifact | Repository implementation |
|---|---|
| Specification | Package, root cross-package, or maintainer specification |
| Requirements | `requirements.md` with stable IDs and live state |
| Approval and execution | `tasks/` task and execution plan |
| Public current docs | Package/root user documentation |
| Current implementation docs | Owning package `docs/development/` |

Tasks are the default approval record. A task links the specification and
requirement IDs and does not silently paraphrase them into a competing
contract.

Specifications are targets. Requirements track what is implemented, verified,
and documented. Public and implementation documentation describe current
committed behavior.

Public current documentation does not inherit task, phase, requirement,
approval, or temporary-progress context. When a current limitation from a
specification matters to users, translate it into package-user vocabulary and
omit target-only plans and internal identifiers.

## Artifact set

A substantial specification normally uses:

```text
<capability>/
├── index.md
├── product-spec.md
├── technical-spec.md
├── requirements.md
└── decisions/                 # optional
```

The full set is proportional. Additional contract pages such as
`frontend-behavior.md`, `protocol.md`, or `persistence.md` are allowed when the
index declares their role.

Small changes may update an existing spec or remain task-only when no durable
target is justified.

## Requirement IDs

Use a stable, short capability prefix and sequence:

```text
EVT-001
NTF-014
DOCGEN-002
```

Prefixes may identify coherent subdomains in one requirements file. IDs remain
stable after acceptance and are not recycled.

Requirements track:

- implementation: `Not started`, `In progress`, `Implemented`, `Deferred`, or
  `Removed`;
- verification: `Unverified`, `Automated`, `Human verified`, or
  `Not applicable`;
- documentation: `Pending`, `Documented`, or `Not applicable`;
- evidence: tests, docs, tasks, review, and delivery references.

Before implementation, use `Not started` for implementation, `Unverified` for
verification, and `Pending` for documentation. `Pending` is not a verification
state.

Evidence may be in the table or a separate ID-keyed section. A status such as
`Automated` or `Documented` must eventually lead to concrete evidence.

Human verification remains incomplete until a human performs or directly
confirms it.

## Workflow

### Small change

Update the specification first. Implement, test, and update requirements and
current docs. Commit the spec with the implementation or in the immediately
preceding commit.

### New capability

Create the approved specification and requirements before implementation.
Requirements begin `Not started` and are updated as work progresses.

### Major change

Keep one target when it remains easy to understand. Use a separate version or
change spec only when the work spans enough design or commits that current and
target behavior would otherwise be confusing.

Temporary progress is added only for multi-commit work. It links:

- the active task;
- affected requirement IDs;
- the meaningful current/target boundary.

Remove temporary progress after all relevant requirements are verified.

## Tests and evidence

Important acceptance and contract tests may carry requirement IDs. Ordinary
low-level tests do not need them.

Test machine-readable contracts directly where practical. Validate
documentation examples through existing tests or focused examples where
possible.

Manual verification requires human performance or direct confirmation. AI
review is advisory and does not satisfy a human-verification requirement.

## Agent guidance

Root and package AGENTS files keep routing concise:

- ordinary specification work reads this repository policy, the generic
  standard, and the owning package entry points;
- work changing the standards, task guidance, publication rules, or validation
  additionally reads the relevant `maintainer/` specification and
  requirements.

`CONTRIBUTING.md` owns the broader human/AI workflow. Canonical `TASKS-v7` owns
task-file behavior injected into developer messages. Neither should duplicate
the full specification standard.

## Maintainer tooling

Task-guidance evaluation code, fixtures, review-bundle preparation, and related
documentation are standards-maintenance tooling. Their approved target owner is
under `maintainer/`, not the generic root test domain.

The owning task decides the exact layout, moves commands/imports/consumers, and
verifies existing evaluation scenarios. Production and package test suites
remain with their owning packages.

## Existing specifications

Existing root and package development specifications remain valid while the
standard is adopted. Do not mass-normalize them merely to match the target
shape.

When touched:

- preserve their target role;
- move live progress into requirements where practical;
- keep current implementation details in package maintainer pages;
- add missing ownership and index links;
- remove temporary progress once requirements are verified;
- correct contradictions discovered during the active work.

Larger cleanup is recorded as separately scoped migration rather than hidden
inside an unrelated feature.