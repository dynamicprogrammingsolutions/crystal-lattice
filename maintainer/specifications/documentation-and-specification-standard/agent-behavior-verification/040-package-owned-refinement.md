# Package-owned refinement

Requirement coverage: `DOCGEN-003`

## Behavior under test

An agent should place a package-specific refinement with the package that owns
the refined behavior, even when the package also implements a broader portable
contract.

The refinement may add platform requirements or strengthen behavior. It must
link and remain compatible with the broader normative contract.

## Repository setup

Use the common neutral seed and candidate guidance overlay.

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