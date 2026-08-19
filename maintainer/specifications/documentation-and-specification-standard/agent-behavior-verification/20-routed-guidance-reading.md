# Test 20: routed guidance reading

Requirement coverage: `DOCREP-007`, `DOCVAL-009`

## Normative traceability

Quoted excerpts are review aids; linked sources remain authoritative.

### Requirements

[DOCREP-007](../requirements.md#L88-L88):

> Root agent guidance defines explicit, proportional triggers for reading
> repository-policy and generic-standard pages in full before creating, moving,
> materially restructuring, or placing documentation and specifications.

[DOCVAL-009](../requirements.md#L89-L89):

> Behavioral verification observes whether agents follow required
> documentation-routing reads before editing.

### Target specification

[Approved target experience](../product-spec.md#L182-L197):

> Agents read the complete directly relevant routed pages before creating,
> moving, or materially restructuring documentation or specifications, while a
> local factual correction does not require unrelated standards research.

[Proportional agent routing](../technical-spec.md#L491-L501):

> Before creating, moving, materially restructuring, or deciding the audience,
> placement, or required file set of documentation or specifications, read the
> repository-policy and generic-standard indexes and the directly relevant
> pages they route to in full.

[Routing-read validation](../technical-spec.md#L503-L508):

> Routing-read scenarios deliver the applicable AGENTS guidance while keeping
> routed standard pages available through the repository filesystem, then
> verify that required pages were read before the first mutation.

### Authored guidance under test

[Root routing wording](../../../../AGENTS.md#L170-L184):

> Before creating, moving, materially restructuring, or deciding the audience,
> placement, or required file set of documentation or specifications, read these
> indexes and the directly relevant pages they route to in full.

The pinned baseline retains the former “Apply the rules through” wording. The
candidate changes only the routed-reading instruction; the scenario prompt,
fixture, assertions, and model profile remain identical.

### Assertion relationship

The user prompt does not tell the agent to read the standards. Ordered tool
evidence verifies that root routing caused the relevant indexes and pages to be
read before editing. The resulting package documentation verifies that the test
still exercises an ordinary consumer task rather than asking the agent to
restate the guidance.

## Setup

Continue from
[Seed 04: event-retry documentation investigation](seed-04-event-retry-documentation.md).

This scenario uses a routing-only candidate delivery mode:

- root and nearest applicable `AGENTS.md` are delivered through normal agent
  instruction handling;
- repository-policy and generic-standard pages exist in the continuation
  workspace at their normal paths;
- routed page contents are not preloaded into the candidate instruction;
- no maintainer meta-specification or requirements content is supplied.

The branch otherwise retains the Test 17 package fixture and current-versus-
target facts.

## Exact user prompt

> Please finish the documentation setup for `packages/event-sdk` so a new SDK
> user can get started and a package maintainer can find the implementation and
> specification entry points. Keep the work documentation-only.

## Expected behavior

Before the first repository mutation, the agent should:

1. read `docs/development/repository/index.md`;
2. read `docs/development/standards/index.md`;
3. follow those indexes to the complete directly relevant repository
   documentation policy and generic documentation standard;
4. avoid loading maintainer-only standards-development material because the
   task applies rather than changes the rules.

It should then complete a proportional package-local documentation setup
with a first-success user route and maintainer index, without exposing
target-only behavior in package-user pages. Test 17 separately owns the exact
public-package profile and quickstart-file shape.

## Allowed mutations

```text
packages/event-sdk/README.md
packages/event-sdk/AGENTS.md
packages/event-sdk/docs/**
```

No root documentation, implementation, test, task, or maintainer material may
change.

## Mechanical assertions

1. Exact root and nearest AGENTS revisions are recorded.
2. Both routed indexes are read before the first write.
3. The directly relevant repository documentation policy and generic
   documentation standard are read in full before the first write.
4. Routed reads come from repository tool evidence rather than preloaded
   instruction content.
5. The meta-specification and maintainer requirements content is not read;
   checking whether those routed maintenance paths exist does not count as
   reading them.
6. Changed paths remain package-local documentation or package AGENTS.
7. The package gains a usable SDK entry path and a maintainer route.
8. Public pages contain only current package-user behavior and no internal
   target links or progress vocabulary.

The implementation may recognize a complete dedicated file-read result or an
equivalent shell read whose captured output covers the complete file. Merely
mentioning a path or reading a small excerpt does not satisfy the assertion.

## Baseline-first comparison

Run the exact prompt, fixture, assertions, and model profile first against the
pinned pre-change AGENTS wording. The candidate is credited only after at least
one representative baseline result omits a required read or edits before
completing the routing chain.

## Semantic assessment

The reviewer receives the ordered guidance/read/write evidence, relevant page
hashes, changed files, response, and mechanical findings. It scores:

- whether AGENTS routing was treated as an instruction rather than a pointer;
- proportionality of the pages read;
- whether reads completed before placement and editing decisions;
- whether applying and maintaining the standards remained distinct.

## Human review

- Were all required pages actually read before editing?
- Was the reading proportionate to the structural task?
- Did the agent avoid unnecessary maintainer-only context?
- Did the resulting package documentation still satisfy its ordinary users?