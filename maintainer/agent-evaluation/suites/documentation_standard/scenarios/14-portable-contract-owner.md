# Portable contract owner

Requirement coverage: `DOCGEN-003`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-003](../../../../docs/development/specifications/documentation-guidance/requirements.md):

> Generic ownership rules allow every package to define specifications for
> behavior it owns and define approved package-specific refinements of broader
> contracts.

### Target specification

[Technical generalized ownership](../../../../docs/development/specifications/documentation-guidance/technical-spec.md):

> A shared abstraction is normally specified with the package that defines it,
> even when several packages consume it.

> A package-specific specification may add or strengthen requirements and
> define allowed platform behavior.

### Authored guidance under test

[Specification ownership](../../../../../docs/development/documentation.md#L47-L61):

> A shared abstraction is normally specified with the package that defines it,
> even when several packages use it.

> A package-specific refinement is specified with that package and links its
> broader contract.

[Repository ownership](../../../../../docs/development/crystal-lattice-documentation.md#L30-L49):

> A package that defines a shared abstraction may own its canonical
> specification even when several packages consume it.

### Assertion relationship

Shared-package mutations verify portable ownership. Prohibited mobile/root
specification creation distinguishes shared behavior from a package refinement
or ownerless cross-package contract.

## Setup

Continue from
[Seed 03: mobile composer contract investigation](seed-03-mobile-composer-refinement.md)
with candidate guidance added. The user clarification changes the requested
behavior from mobile-only to portable.

## Exact user prompt

> The composer behavior from the task should apply identically to every client,
> not only mobile. Please update the appropriate specification and
> requirements, but do not implement it.

## Expected behavior

- Update the shared portable composer specification and requirements.
- Treat the user message as authorization for the clarified target.
- Leave mobile package specification/docs and implementation unchanged.
- Begin portable requirements as not implemented/unverified/pending.

## Allowed mutations

```text
packages/conversation-contract/docs/development/specifications/composer/**
tasks/mobile-composer-ux.md
```

No mobile package specification, root cross-package specification,
implementation, or current user documentation may change.

## Mechanical assertions

1. Only shared-contract specification/requirements and necessary task links
   change.
2. No mobile refinement or root cross-package specification is created.
3. Portable requirements are pending and stable.
4. Current user docs and code remain unchanged.

## Semantic assessment

The reviewer receives the portable contract, mobile task/context, shared
specification diff, requirements, changed paths, and response. It scores
portable ownership, absence of package/root duplication, and pending-state
accuracy.

## Human review

- Is the behavior genuinely portable?
- Did the agent select the package defining the shared abstraction?
- Did it avoid both mobile duplication and unnecessary root ownership?