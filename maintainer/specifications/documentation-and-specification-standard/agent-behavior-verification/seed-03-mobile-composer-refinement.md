# Seed 03: mobile composer contract investigation

## Purpose

This seed investigates one portable composer contract, one mobile package, and
one approved UX task. It gives branch tests the concrete contract and package
facts needed to evaluate ownership and refinement behavior.

## Repository setup

The clean fixture contains:

```text
packages/conversation-contract/
└── docs/development/specifications/composer/
    ├── index.md
    ├── product-spec.md
    ├── technical-spec.md
    └── requirements.md

mobile/example-app/
├── src/Composer.tsx
└── docs/development/index.md

tasks/mobile-composer-ux.md
```

The task requests keyboard avoidance, safe-area, touch-target, and screen
transition behavior without implementation.

## Exact seed prompt

> Please investigate `tasks/mobile-composer-ux.md`, the existing portable
> composer contract in
> `packages/conversation-contract/docs/development/specifications/composer/index.md`,
> `packages/conversation-contract/docs/development/specifications/composer/product-spec.md`,
> and
> `packages/conversation-contract/docs/development/specifications/composer/requirements.md`,
> plus
> `mobile/example-app/src/Composer.tsx` and
> `mobile/example-app/docs/development/index.md`. Report the portable behavior
> already defined and the mobile-specific facts and constraints in those
> files. Do not modify files and do not recommend where a new specification
> should be placed.

The seed does not choose package, shared, or root ownership and does not decide
whether the requested work is a refinement. Those are branch assertions.

## Seed assertions

1. No mutation occurs.
2. The portable contract and mobile package files are identified.
3. Existing portable behavior is reported accurately.
4. Mobile task constraints are reported without inventing implementation.
5. No specification path or ownership recommendation is made.
6. Candidate guidance is absent and continuation provenance is complete.

## Current branches

- [Package-owned refinement](04-package-owned-refinement.md): create the
  approved specification after candidate guidance is added.
- [Portable contract owner](14-portable-contract-owner.md): clarify that the
  requested behavior applies identically to every client and update the shared
  owner instead.

Future branches may ask for a desktop-specific refinement or an unapproved
mobile specification using the same contract investigation.