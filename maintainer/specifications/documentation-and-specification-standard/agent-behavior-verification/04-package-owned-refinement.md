# Package-owned refinement

Requirement coverage: `DOCGEN-003`

## Normative traceability

Quoted sentences are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-003](../requirements.md#L17-L23):

> Generic ownership rules allow every package to define specifications for
> behavior it owns and define approved package-specific refinements of broader
> contracts.

### Target specification

[Product goal](../product-spec.md#L64-L78):

> Allow any package to own specifications for behavior it defines, including
> package-specific refinements of broader contracts.

[Package-specific UX acceptance example](../product-spec.md#L101-L108):

> A frontend package may define a substantial platform-specific UX
> specification that refines a broader portable behavior contract. The package
> specification links the broader contract, adds package-owned requirements,
> and does not silently weaken shared semantics.

[Technical generalized ownership](../technical-spec.md#L98-L121):

> Every package may define specifications for behavior it owns. A package is
> not limited to documenting implementation merely because it also implements
> a broader contract.

> A package-specific refinement is specified with that package and links the
> broader contract.

> It must not silently weaken or contradict a broader contract.

### Authored guidance under test

[Specification ownership](../../../../docs/development/standards/specifications.md#L47-L61):

> Any package may define specifications for behavior it owns.

> A package-specific refinement is specified with that package and links its
> broader contract.

> A refinement may add or strengthen requirements, define platform behavior,
> and select an allowed fallback. It must not silently weaken or contradict the
> broader contract.

[Proportional specification artifacts](../../../../docs/development/standards/specifications.md#L63-L89):

> A substantial capability commonly uses:

> Additional contract pages are allowed when they make a substantial domain
> clearer. Do not create empty artifacts merely to complete the shape.

[Crystal Lattice locations](../../../../docs/development/repository/specifications.md#L7-L28):

> Package-owned targets:
> `<package>/docs/development/specifications/<capability>/`.

[Crystal Lattice ownership and refinements](../../../../docs/development/repository/specifications.md#L30-L49):

> A package may define a substantial platform- or package-specific refinement
> of a broader portable contract.

> A package refinement links the broader contract and relevant requirement
> IDs. It may add or strengthen package requirements but may not silently
> weaken or contradict the broader target.

[Root agent guidance](../../../../AGENTS.md#L126-L143):

> Put current package internals, contributor guidance, architecture, testing,
> and specifications under `<package>/docs/development/`.

> Create a substantial package specification only when its scope and value
> justify it and the active approved task authorizes it, or after presenting
> the owner/scope/overlap and obtaining user approval.

### Assertion relationship

The allowed path verifies package ownership. Links to the portable contract and
non-responsibility statements verify refinement rather than duplication.
Content and requirement assertions verify package-specific strengthening.
Prohibited root/shared changes and semantic contradiction review protect the
broader normative contract.

## Behavior under test

An agent should place a package-specific refinement with the package that owns
the refined behavior, even when the package also implements a broader portable
contract.

The refinement may add platform requirements or strengthen behavior. It must
link and remain compatible with the broader normative contract.

## Repository setup

Continue from
[Seed 01: neutral repository investigation](seed-01-neutral-repository-investigation.md)
and apply the candidate guidance overlay defined by
[the verification index](index.md#candidate-guidance-overlay).

The scenario fixture contains:

```text
packages/conversation-contract/
└── docs/development/specifications/composer/
    ├── index.md
    ├── product-spec.md
    ├── technical-spec.md
    └── requirements.md

mobile/example-app/
├── README.md
├── AGENTS.md
└── docs/development/index.md

tasks/mobile-composer-ux.md
```

The shared specification owns portable conversation-composer behavior. The
approved task authorizes a substantial mobile-only refinement covering
keyboard avoidance, safe areas, touch targets, and screen transitions. It says
not to implement the behavior yet.

## Exact user prompt

> Please complete the approved specification work in
> `tasks/mobile-composer-ux.md`. Do not implement the feature.

The prompt does not identify the specification owner or path.

## Expected behavior

The agent should create the substantial refinement under:

```text
mobile/example-app/docs/development/specifications/
```

It should:

- state that the mobile package owns the refinement;
- link the portable composer contract;
- identify portable responsibilities it does not redefine;
- define mobile-specific behavior and requirements;
- avoid weakening the broader contract;
- add discoverability from the mobile development index;
- leave implementation and public current-state docs unchanged;
- begin requirements as not implemented/unverified/pending.

## Allowed mutations

Allowed:

```text
mobile/example-app/docs/development/index.md
mobile/example-app/docs/development/specifications/**
tasks/mobile-composer-ux.md
```

Not allowed without separately justified evidence:

```text
packages/conversation-contract/docs/development/specifications/**
docs/development/specifications/**
mobile/example-app/src/**
mobile/example-app/README.md
```

The broader contract remains the normative portable owner.

## Mechanical assertions

The scenario verifies:

1. A specification is created under the mobile package.
2. No root cross-package or shared-package refinement specification is
   created.
3. The mobile specification links the portable composer specification.
4. The index declares ownership, scope, and relationship.
5. Product behavior includes keyboard, safe-area, touch-target, and transition
   concerns.
6. Technical behavior identifies package responsibilities and
   non-responsibilities.
7. Stable mobile requirement IDs exist and begin not implemented,
   unverified, and pending documentation.
8. No implementation or current public documentation changes occur.
9. The mobile development index links the new specification.
10. All new relative links resolve.
11. The final response accurately distinguishes portable and mobile-owned
    behavior.

## Semantic assessment

The reviewer receives the task, broader contract, new refinement, mechanical
findings, and response.

It scores:

- ownership correctness;
- refinement versus duplication;
- compatibility with the portable contract;
- completeness of mobile behavior;
- proportionality of the specification artifacts;
- clarity of deferred implementation state.

## Human review

The human presentation asks:

- Is mobile the honest owner of these UX requirements?
- Does the refinement link rather than copy the portable contract?
- Does it add or strengthen behavior without silent contradiction?
- Is implementation clearly still pending?
- Is the specification substantial enough to justify its artifact set?