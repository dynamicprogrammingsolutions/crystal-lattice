# Normative owner and discoverability

Requirement coverage: `DOCGEN-004`, `DOCGEN-006`, `DOCREP-006`,
`DOCVAL-007`–`DOCVAL-008`

## Normative traceability

Quoted sentences are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-004](../requirements.md#L19-L24):

> Generic rules define one normative owner, controlled summaries,
> current-versus-target separation, complete indexes, and two-link
> discoverability without requiring placeholder pages.

[DOCGEN-006](../requirements.md#L26-L26):

> An artifact depends only on information available and appropriate to that
> audience; cross-audience information is translated into the destination
> role's vocabulary.

[DOCREP-006](../requirements.md#L31-L38):

> Repository policy maps generic audience roles to exact Crystal Lattice
> artifacts and defines normal, pointer-only, evidence-only, and prohibited
> reference directions.

[DOCVAL-008](../requirements.md#L80-L80):

> Candidate wording is evaluated only after representative baseline evidence
> exposes the targeted behavior.

### Target specification

[Product goals](../product-spec.md#L73-L90):

> Make every documentation artifact discoverable from an appropriate entry
> point.

> Keep normative contracts, consumer guidance, implementation guidance, and
> standards-maintenance material distinguishable.

[Technical audience boundary](../technical-spec.md#L150-L192):

> Consumer documentation normally depends only on other consumer documentation
> and public reference.

> Output artifacts do not inherit task, requirement, specification-progress, or
> maintainer context merely because the agent can read it.

[Technical authority and duplication](../technical-spec.md#L217-L238):

> Other pages may summarize only what their audience needs. A consumer page
> does not need to expose an internal target specification merely to preserve
> normative ownership.

[Technical discoverability](../technical-spec.md#L240-L267):

> Every authored page is reachable within at most two documentation links from
> the nearest repository, package, or shared-domain entry point.

> Indexes remain concise but complete.

### Authored guidance under test

[Audience and reference boundaries](../../../../docs/development/standards/documentation.md#L35-L58):

> A document may assume only concepts introduced in that document or available
> through documentation intended for the same audience.

> Consumer docs may rely on consumer docs and public reference. A development
> link is a labeled pointer, not required user context.

[Specifications and implementation pages](../../../../docs/development/standards/documentation.md#L147-L164):

> A specification describes an intended target. An implementation page
> describes current code.

> The specification may link primary user and implementation pages for
> maintainer discoverability. A consumer page does not need to expose an
> internal target specification.

[Avoid duplication](../../../../docs/development/standards/documentation.md#L166-L182):

> Give every contract one normative owner.

> Let other pages summarize only what their audience needs.

> Link lifecycle, compatibility, persistence, and protocol detail instead of
> independently redefining complete rules.

> Keep proposed behavior in target specifications, not in current user or
> implementation guides.

[Discoverability](../../../../docs/development/standards/documentation.md#L184-L207):

> Every authored page should be reachable in at most two documentation links
> from the nearest repository, package, or shared-domain entry point.

> Every multi-page documentation scope should have a short index. Every
> specification index should link all of its authored artifacts.

[Current-state documentation](../../../../docs/development/standards/documentation.md#L209-L221):

> Public user documentation and implementation/maintainer documentation
> describe current supported behavior.

> Current consumer documentation uses public, self-contained vocabulary and
> does not mention internal phases, requirement IDs, task paths, temporary
> progress, or future targets.

[Adoption](../../../../docs/development/standards/documentation.md#L260-L270):

> Do not create placeholder quickstarts or nearly empty indexes with no useful
> route.

[Repository audience mapping](../../../../docs/development/repository/documentation.md#L65-L102):

> Consumer documentation must stand alone for package users.

> A package user page does not link an internal target specification by
> default. The development specification may link the user page for maintainer
> discoverability.

[Repository discoverability](../../../../docs/development/repository/documentation.md#L214-L229):

> Every package development index must be linked from its README, AGENTS, or
> package docs index.

> Package indexes route to their user and implementation pages.

[Root agent guidance](../../../../AGENTS.md#L120-L149):

> Documentation is authored next to the package or subsystem that owns it.

> Public user documentation and implementation/maintainer documentation
> describe current committed behavior.

> Information available from tasks, specifications, requirements, commits,
> AGENTS files, or maintainer workflows does not automatically belong in
> another artifact.

### Assertion relationship

The existing specification path and substantial-overlap checks preserve one
normative owner. User-page content assertions verify a controlled summary of
implemented behavior only. Audience assertions ensure consumer docs do not
depend on an internal target specification or leak its requirement/progress
context. Link-graph assertions verify two-link consumer discoverability and
complete indexes. Prohibited new pages verify that discoverability does not
produce filler.

## Behavior under test

An agent should make current behavior easy for package users to find without
creating a competing normative contract.

It should:

- preserve one normative owner;
- write audience-appropriate summaries and consumer links;
- keep target-only behavior out of current user docs;
- keep internal specification, requirement, and progress terminology out of
  consumer docs;
- update indexes so pages are reachable within two links;
- avoid placeholder pages and duplicated full contracts.

## Repository setup

Continue from
[Seed 04: event-retry documentation investigation](seed-04-event-retry-documentation.md)
and apply the candidate guidance overlay defined by
[the verification index](index.md#candidate-guidance-overlay).

The scenario fixture provides:

```text
packages/event-sdk/
├── README.md
├── docs/
│   ├── index.md
│   └── publishing.md
└── docs/development/
    ├── index.md
    └── specifications/event-lifecycle/
        ├── index.md
        ├── technical-spec.md
        └── requirements.md
```

The normative event specification defines both:

- an implemented retry lifecycle;
- a target-only future replay mode whose requirement remains not implemented.

The package user page does not explain or link the implemented retry
lifecycle, making it difficult to discover.

## Exact user prompt

> Please make the existing event retry lifecycle easy for
> `packages/event-sdk` users to find and understand. Keep the scope to
> documentation.

The prompt does not identify the normative owner or warn about target-only
behavior.

## Expected behavior

The agent should update package user documentation and indexes with a concise
current-behavior explanation that stands alone for package users.

The internal development specification remains the normative owner, but the
consumer page should not depend on or directly link it because it contains
target-only behavior and internal tracking context. The specification index may
link the current consumer page for maintainer discoverability.

It should not:

- copy the complete normative lifecycle into a second authored page;
- present target-only replay behavior as supported;
- expose requirement IDs, target labels, task/progress language, or internal
  phase terminology;
- require package users to read the internal target specification;
- move the contract to root documentation;
- create empty or redundant entry points;
- rewrite untouched implementation material.

## Allowed mutations

Expected:

```text
packages/event-sdk/README.md
packages/event-sdk/docs/index.md
packages/event-sdk/docs/publishing.md
```

An internal specification backlink to the consumer page is allowed when it
improves maintainer discoverability without exposing the specification as a
consumer dependency:

```text
packages/event-sdk/docs/development/index.md
packages/event-sdk/docs/development/specifications/event-lifecycle/index.md
```

No root docs or new normative specification are allowed.

## Mechanical assertions

The scenario verifies:

1. README contains normal retry morphology (`retry`, `retries`, `retried`, or
   `retrying`) or directly links the retry page.
2. The package docs index names retry behavior and links the current user page.
3. The user-facing page explains the implemented `retrying` and `failed`
   lifecycle.
4. Consumer docs do not link or depend on the internal target specification.
5. The normative technical specification remains the sole complete contract.
6. User docs do not claim the unimplemented replay mode is available.
7. User docs contain no requirement IDs, target labels, task paths, internal
   phases, or temporary-progress terminology.
8. Requirements statuses remain unchanged unless correcting an identified
   factual error.
9. The event page is reachable within two links from README or package docs
   index.
10. No root documentation or duplicate specification is created.
11. No empty index or quickstart is created.
12. Relative links resolve.
13. The final response identifies current versus target and
consumer-versus-development boundaries correctly.

Mechanical anti-duplication checks compare normalized headings and substantial
paragraph overlap, while semantic review handles meaning-level duplication.

## Semantic assessment

The reviewer receives original/final user docs, the normative specification,
requirements state, link graph, overlap findings, and response.

It scores:

- normative-owner preservation;
- usefulness of the user summary;
- audience closure and translation into consumer vocabulary;
- current-versus-target accuracy;
- duplication avoidance;
- discoverability;
- proportionality of changed pages.

## Human review

The human presentation asks:

- Is there still one clear normative contract?
- Can a package user find and understand current retry behavior quickly?
- Does the user documentation stand alone without internal specification or
  requirement context?
- Did any target-only replay behavior leak into current docs?
- Are summaries appropriately scoped rather than duplicated?
- Is the link chain complete and easy to follow?