# Normative owner and discoverability

Requirement coverage: `DOCGEN-004`

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

Use the common neutral seed and candidate guidance overlay.

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