# Normative owner and discoverability

Requirement coverage: `DOCGEN-004`

## Normative traceability

Quoted sentences are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-004](../requirements.md#L17-L24):

> Generic rules define one normative owner, controlled summaries,
> current-versus-target separation, complete indexes, and two-link
> discoverability without requiring placeholder pages.

### Target specification

[Product goals](../product-spec.md#L64-L82):

> Make every documentation artifact discoverable from an appropriate entry
> point.

> Keep normative contracts, consumer guidance, implementation guidance, and
> standards-maintenance material distinguishable.

[Technical authority and duplication](../technical-spec.md#L146-L163):

> Each behavioral contract has one normative owner. Other pages may summarize
> for their audience, but identify the canonical contract and do not
> independently redefine complete lifecycle, compatibility, persistence, or
> protocol semantics.

> User guides teach current supported use. Target-only behavior remains in
> specifications and requirements until implementation is committed.

[Technical discoverability](../technical-spec.md#L165-L192):

> Every authored page is reachable within at most two documentation links from
> the nearest repository, package, or shared-domain entry point.

> Indexes remain concise but complete.

### Authored guidance under test

[Specifications and implementation pages](../../../../docs/development/standards/documentation.md#L118-L133):

> A specification describes an intended target. An implementation page
> describes current code.

> The specification may link primary user and implementation pages for
> discoverability.

[Avoid duplication](../../../../docs/development/standards/documentation.md#L135-L151):

> Give every contract one normative owner.

> Let other pages summarize only what their audience needs.

> Link lifecycle, compatibility, persistence, and protocol detail instead of
> independently redefining complete rules.

> Keep proposed behavior in target specifications, not in current user or
> implementation guides.

[Discoverability](../../../../docs/development/standards/documentation.md#L153-L176):

> Every authored page should be reachable in at most two documentation links
> from the nearest repository, package, or shared-domain entry point.

> Every multi-page documentation scope should have a short index. Every
> specification index should link all of its authored artifacts.

[Current-state documentation](../../../../docs/development/standards/documentation.md#L178-L185):

> Public user documentation and implementation/maintainer documentation
> describe current supported behavior.

> Target-only behavior remains in specifications and requirements until
> implementation is committed.

[Adoption](../../../../docs/development/standards/documentation.md#L212-L222):

> Do not create placeholder quickstarts or nearly empty indexes with no useful
> route.

[Repository discoverability](../../../../docs/development/repository/documentation.md#L163-L178):

> Every package development index must be linked from its README, AGENTS, or
> package docs index.

> Package indexes route to their user and implementation pages.

[Root agent guidance](../../../../AGENTS.md#L120-L140):

> Documentation is authored next to the package or subsystem that owns it.

> Public user documentation and implementation/maintainer documentation
> describe current committed behavior.

### Assertion relationship

The existing specification path and substantial-overlap checks preserve one
normative owner. User-page content assertions verify a controlled summary of
implemented behavior only. Link-graph assertions verify two-link
discoverability and complete indexes. Prohibited new pages verify that
discoverability does not produce filler.

## Behavior under test

An agent should make current behavior easy for package users to find without
creating a competing normative contract.

It should:

- preserve one normative owner;
- write audience-appropriate summaries and links;
- keep target-only behavior out of current user docs;
- update indexes so pages are reachable within two links;
- avoid placeholder pages and duplicated full contracts.

## Repository setup

Continue from
[Seed 01: neutral repository investigation](seed-01-neutral-repository-investigation.md)
and apply the candidate guidance overlay defined by
[the verification index](index.md#candidate-guidance-overlay).

The scenario fixture provides:

```text
packages/event-sdk/
├── README.md
├── docs/
│   ├── index.md
│   └── events.md
└── docs/development/
    ├── index.md
    └── specifications/events/
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
current-behavior explanation and link to the normative specification where
deeper contract detail is useful.

It should not:

- copy the complete normative lifecycle into a second authored page;
- present target-only replay behavior as supported;
- move the contract to root documentation;
- create empty or redundant entry points;
- rewrite untouched implementation material.

## Allowed mutations

Expected:

```text
packages/event-sdk/README.md
packages/event-sdk/docs/index.md
packages/event-sdk/docs/events.md
```

An index or specification backlink is allowed only when it improves the
two-link chain without redefining the contract:

```text
packages/event-sdk/docs/development/index.md
packages/event-sdk/docs/development/specifications/events/index.md
```

No root docs or new normative specification are allowed.

## Mechanical assertions

The scenario verifies:

1. The user-facing event page explains the implemented retry lifecycle.
2. The page links the existing normative specification.
3. The normative technical specification remains the sole complete contract.
4. User docs do not claim the unimplemented replay mode is available.
5. Requirements statuses remain unchanged unless correcting an identified
   factual error.
6. The event page is reachable within two links from README or package docs
   index.
7. No root documentation or duplicate specification is created.
8. No empty index or quickstart is created.
9. Relative links resolve.
10. The final response identifies current versus target behavior correctly.

Mechanical anti-duplication checks compare normalized headings and substantial
paragraph overlap, while semantic review handles meaning-level duplication.

## Semantic assessment

The reviewer receives original/final user docs, the normative specification,
requirements state, link graph, overlap findings, and response.

It scores:

- normative-owner preservation;
- usefulness of the user summary;
- current-versus-target accuracy;
- duplication avoidance;
- discoverability;
- proportionality of changed pages.

## Human review

The human presentation asks:

- Is there still one clear normative contract?
- Can a package user find and understand current retry behavior quickly?
- Did any target-only replay behavior leak into current docs?
- Are summaries appropriately scoped rather than duplicated?
- Is the link chain complete and easy to follow?