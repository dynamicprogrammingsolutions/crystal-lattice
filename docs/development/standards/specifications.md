# Specification-driven development

This standard defines a package-neutral model for target specifications,
live-state requirements, work tracking, current documentation, and evidence. A
repository policy should map these concepts to exact paths and local workflow.

## Four sources of truth

| Source | Responsibility |
|---|---|
| Specification | Intended target behavior and design |
| Requirements | Live implementation, verification, documentation, and evidence state |
| Work item | Approval, execution scope, plan, findings, and completion |
| User and implementation documentation | Current supported behavior and current implementation |

A specification is not evidence that its target currently exists. Requirements
bridge the target and the implemented system.

## When a durable specification is useful

Create or update a durable specification when work introduces meaningful
target behavior or decisions, including:

- user-visible workflows with several acceptance requirements;
- public APIs, schemas, protocols, or compatibility commitments;
- persisted data or migration behavior;
- security, privacy, concurrency, accessibility, or native-platform decisions;
- behavior spanning several components or packages;
- phased implementation or significant human verification;
- decisions likely to be revisited.

A small local change may use only its approved work item when it has one
straightforward outcome, no material design choice, and no durable contract
worth preserving.

Before creating a substantial new specification, the implementer should propose:

- its owning package or shared scope and behavior scope;
- why existing specifications are insufficient;
- whether it defines, refines, or implements another contract;
- the expected specification files and requirements;
- overlap and duplication risks.

Creation requires user approval unless the active work item already authorizes
the specification.

A direct request to create a substantial specification does not replace this
proposal and confirmation when its owning scope, behavior scope, and overlap
have not already been approved.

## Specification scope

Any package may define specifications for behavior it owns.

1. Package-owned behavior is specified with that package.
2. A package-specific refinement is specified with that package and links its
   broader contract.
3. A shared abstraction is normally specified with the package that defines it,
   even when several packages use it.
4. A cross-package specification is appropriate when independently owned
   packages must coordinate and no package provides a clear authoritative home.

A refinement may add or strengthen requirements, define platform behavior, and
select an allowed fallback. It must not silently weaken or contradict the
broader contract. Approved exceptions are linked from both scopes.

## Proportional specification files

A substantial capability commonly uses:

```text
<specification>/
├── index
├── product specification
├── technical specification
├── requirements
└── decisions/                 # optional
```

The set is proportional:

- The index defines scope, ownership, relationships, and links.
- A product specification explains the problem, users, user-visible target,
  goals, non-goals, and acceptance examples.
- A technical specification explains architecture, contracts, persistence,
  compatibility, failure behavior, security, migration, and verification.
- Requirements normalize target outcomes and track live state.
- Decision records preserve material choices among credible alternatives.

Additional contract pages are allowed when they make a substantial domain
clearer, such as frontend behavior, protocol, persistence, or migration. The
index declares their role. Do not create empty files merely to complete the
shape.

## Terminology in specification files

Follow the
[terminology rules for authored content](documentation.md#terminology-in-authored-content).

Name each source or record directly: specification, requirements, work item,
decision record, current documentation, source code, or test. Specification
indexes should label linked files by their purpose—for example,
“Specification documents”—rather than using a generic umbrella heading.

## Specification as target

Update the specification before implementation. It may intentionally differ
from current code while work is in progress.

### Small change

1. Update the target specification.
2. Update or add requirements.
3. Implement and verify.
4. Update current user and implementation documentation.
5. Commit the specification with the code or in the immediately preceding
   commit.

The target/current difference should be short and transparent in Git history.

### New capability

Create the specification and requirements first. Requirements begin as not
implemented and are updated as code, verification, and current documentation
are completed.

### Major change

Use the same simple workflow while one target remains clear. Introduce an
explicit target version or separate change specification only when it
materially improves understanding.

No single version-directory format is required. A versioned approach must:

- identify the active target;
- link applicable requirements;
- prevent current documentation from presenting future behavior as available;
- preserve previous targets through Git history or explicit links.

## Approval and progress

The repository's work item records approval by default.
Specifications do not require a mandatory approval or implementation status.
A domain may define stricter rules when external governance requires them.

Temporary progress inside a specification or its index is optional. Use it only
when implementation is expected to span more than one commit and the
target/current difference would otherwise be confusing.

When present, progress:

- links the active work item;
- lists the affected requirement IDs;
- distinguishes current from target behavior;
- is removed when all relevant requirements are verified.

Git history is the default explanation of ordinary specification evolution.

## Requirements

Requirements use stable identifiers and keep these dimensions separate:

- implementation;
- verification;
- documentation;
- evidence.

Recommended implementation values:

- `Not started`
- `In progress`
- `Implemented`
- `Deferred`
- `Removed`

Recommended verification values:

- `Unverified`
- `Automated`
- `Human verified`
- `Not applicable`

Recommended documentation values:

- `Pending`
- `Documented`
- `Not applicable`

Use `Unverified` when verification has not occurred. Reserve `Pending` for
documentation that has not yet been written. Do not use `Pending` as a
verification state.

Example:

```markdown
| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| EVT-001 | External events have stable type discriminators. | Implemented | Automated | Documented | test path, user-doc path, work item, delivery |
| EVT-002 | Internal checkpoints are not exposed publicly. | In progress | Unverified | Pending | active work item |
```

A common pre-implementation row is:

```text
Not started | Unverified | Pending | —
```

Identifiers remain stable after acceptance and are not recycled. Evidence may
appear in the table or in a separate section keyed by requirement ID when that
keeps the table readable.

A deferred requirement records its reason, dependency or revisit trigger, and
owning future work when known. It does not count toward the active work item's
completion unless that work explicitly requires the deferral record.

## Relationship to work tracking

- Specifications own target behavior and design.
- Requirements own live state and evidence.
- Work items own approval, execution plans, dependencies, findings, and
  completion.
- Work items link requirement IDs rather than creating a conflicting second
  contract.
- Requirements link the implementing work and final delivery evidence.
- Material target or requirement changes return through the repository's
  approval workflow.

## Verification

Important acceptance and contract tests may reference requirement IDs in names,
descriptions, parameter IDs, or nearby comments. Ordinary low-level tests do
not need requirement IDs.

Validate machine-readable schemas and protocol examples directly when
practical. Source documentation examples from tested examples when possible.

Manual verification is recorded only when a human performs or directly
confirms it. An agent may prepare the checklist but cannot convert planned
manual work into completed evidence.

Gherkin or another executable-specification format is optional for genuinely
business-readable behavior; it is not required for ordinary library code.

## Decisions and supersession

Use a decision record when a choice:

- selects among credible alternatives;
- affects a public contract, ownership boundary, persisted data, compatibility,
  security, privacy, or significant operational behavior;
- is likely to outlive the current work item.

Small reversible choices may remain in the work item or technical
specification.

When a target is replaced, link the superseding specification or version rather
than erasing historical rationale.

## Current documentation

Public user documentation and implementation/maintainer documentation describe
current behavior. They may be edited first in the working tree, but they are
committed with the code that makes new claims true.

Draft, deferred, or target-only behavior belongs in specifications and
requirements, not in current guides.

Current guides also exclude the specification's internal tracking vocabulary.
Do not copy phase names, requirement IDs, task paths, approval state, temporary
progress, or evidence notation into user documentation. Translate a necessary
current limitation into user-domain language and omit future plans.

## Layout defaults and explicit requests

The illustrated file layout is a recommended default, not a mandatory
schema. Honor an explicit approved alternative when required content,
traceability, discoverability, and audience, ownership, and source-of-truth
boundaries remain intact; do not request duplicate confirmation merely because
the requested shape differs.