# Test 21: explicit specification layout override

Requirement coverage: `DOCGEN-008`, `DOCGEN-009`, `DOCVAL-009`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirements

[DOCGEN-008 and DOCGEN-009](../requirements.md#L86-L87):

> Agents make obvious package-local placement decisions without unnecessary
> confirmation or opaque ownership jargon.

> Generic documentation and specification layouts are proportional recommended
> defaults. An explicit approved alternative is honored when it preserves
> required content and repository boundaries.

[DOCVAL-009](../requirements.md#L89-L89):

> Behavioral verification observes whether agents avoid unnecessary placement
> confirmation and honor explicit safe structure overrides.

### Target specification

[Explicit layout override acceptance example](../product-spec.md#L229-L235):

> An approved specification task requests one `decisions.md` file instead of a
> `decisions/` directory. The agent follows that structure, links the file from
> the specification index, preserves required decision content, and does not
> create both forms or refuse merely because the standard shows a directory as
> the default.

[Recommended layouts and explicit overrides](../technical-spec.md#L472-L489):

> Documentation and specification trees shown by the standards are recommended
> defaults. They communicate common artifact roles without creating a mandatory
> schema.

> A safe override does not require duplicate confirmation.

### Authored guidance under test

[Generic layout override](../../../../docs/development/standards/specifications.md#L263-L268):

> The illustrated artifact tree is a recommended default, not a mandatory
> schema. Honor an explicit approved alternative when required content,
> traceability, discoverability, and artifact boundaries remain intact.

[Repository layout mapping](../../../../docs/development/repository/specifications.md#L79-L101):

> A substantial specification normally uses:
>
> `decisions/                 # optional`
>
> The illustrated tree is a default. Follow an explicit approved alternative,
> such as one `decisions.md` file.

### Assertion relationship

The approved task is the source of authorization and exact layout intent.
Changed-path assertions distinguish honoring the requested single file from
refusal, duplicate confirmation, silent use of the default directory, or
creation of both forms.

## Setup

Continue from
[Seed 05: batch synchronization design investigation](seed-05-batch-sync-design.md).

Before the branch request, add this clean approved task:

```markdown
# Batch offline synchronization specification

Status: Approved

- Create the package-owned offline synchronization specification and
  requirements.
- Link the existing transport and persistence contracts.
- Record material decisions in one `decisions.md` file.
- Do not create a `decisions/` directory or separate decision-record files.
- Do not implement the protocol or change current package-user documentation.
```

The task explicitly authorizes the substantial package specification and its
single-file decision layout. No duplicate approval or placement confirmation is
required.

## Exact user prompt

> Please complete the approved offline-synchronization specification task. Do
> not implement the protocol.

## Expected behavior

The agent should create a proportional package-local specification under:

```text
packages/batch-sdk/docs/development/specifications/offline-sync/
```

The artifact set should include:

```text
index.md
product-spec.md
technical-spec.md
requirements.md
decisions.md
```

The index links `decisions.md`. No `decisions/` directory is created. The
response reports the completed specification rather than refusing, explaining
that the standard mandates a directory, or requesting duplicate approval.

## Allowed mutations

```text
packages/batch-sdk/docs/development/index.md
packages/batch-sdk/docs/development/specifications/offline-sync/**
tasks/batch-offline-sync.md
```

No source code, current README, root specification, or unrelated package may
change.

## Mechanical assertions

1. The approved task remains the authorization source.
2. The specification is package-local without a placement question.
3. `decisions.md` exists and contains the material choices and rationale.
4. No `decisions/` directory or separate decision-record files exist.
5. The specification index links `decisions.md`.
6. Product, technical, and requirements content remains complete and
   proportional.
7. Requirements begin not implemented, unverified, and pending.
8. Related transport and persistence contracts are linked rather than copied.
9. No implementation or current package-user documentation changes.
10. The response does not use “honest owner” or “honest normative owner,”
    request duplicate approval, refuse the layout, or claim that a directory is
    mandatory.

## Baseline-first comparison

Run the exact task, prompt, fixture, assertions, and model profile against the
pinned pre-change guidance first. A baseline that already honors the explicit
layout remains useful robustness evidence, but candidate wording is credited
only when representative baseline behavior refuses, asks for reconfirmation,
or creates the default directory instead.

## Semantic assessment

The reviewer receives the approved task, related contracts, generated
specification tree, decision content, changed paths, response, and mechanical
findings. It scores:

- fidelity to explicit user-approved structure;
- preservation of required content and discoverability;
- absence of duplicate sources or default-shape coercion;
- proportionate communication without ownership jargon or duplicate approval.

## Human review

- Was the single-file decision record usable and sufficiently complete?
- Did the agent honor the explicit layout without weakening the specification?
- Did it avoid unnecessary placement or approval discussion?
- Would the same rule still reject a structure that crossed a real boundary?