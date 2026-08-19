# Documentation structure

This standard defines package-neutral rules for organizing durable
documentation. A repository policy should map the concepts to exact paths,
filenames, package profiles, publication rules, and local exceptions.

## Principles

- Author documentation beside the package or subsystem that owns it.
- Choose location by audience, authority, and the package or shared scope that
  defines the behavior, not by who happened to implement the current change.
- Keep one authoritative source for each behavioral contract.
- Keep public/user and implementation/maintainer documentation aligned with
  current committed behavior.
- Treat generated documentation as output, not a competing authored source.
- Adopt the structure incrementally. Do not create empty pages or reconstruct
  unfamiliar systems merely to complete a directory shape.

## Documentation authority

Classify a substantive page before choosing its location.

| Class | Purpose |
|---|---|
| Normative specification | Defines intended required behavior, constraints, compatibility, or design |
| Consumer guide | Teaches supported installation, configuration, API use, operation, or extension |
| Implementation or maintainer guide | Explains current internals, ownership, invariants, debugging, and verification |
| Generated reference | Presents API, type, schema, or protocol information generated from maintained inputs |
| Repository or documentation infrastructure | Explains repository-wide workflow or documentation tooling |

A reader being a software developer does not make a page implementation
documentation. Someone importing an SDK or authoring an extension is a package
user when the page teaches the supported public contract.

## Audience and context boundaries

Every document or maintained file has an intended audience and role. A
document may assume only concepts introduced in that document or available
through documentation intended for the same audience.

Broader repository context may guide the author, but does not become reader
context. When information crosses an audience boundary, include only what the
destination needs, translate it into that audience's vocabulary, and omit
source-specific phases, IDs, progress, approval, evidence, and workflow.

Treat the destination audience as a write boundary. If requested content is
not appropriate or available to that audience, do not add it or invent a link;
report the conflict before editing and offer an audience-compatible translation
or location.

- Consumer docs may rely on consumer docs and public reference. A development
  link is a labeled pointer, not required user context.
- Development docs may map current code to specifications and requirements;
  specifications may link related targets and affected current docs;
  requirements may link implementation and evidence.
- Agent guidance, tasks, and maintainer material may route broadly within their
  scope, but their context does not flow into destination documents or files.
  Generated output depends on its maintained source or generator.

A contract intended for package users may be public reference even when it is
called a specification. A target specification containing unimplemented
behavior, requirement progress, task links, or design alternatives remains
development material regardless of its filename.

## Package profiles

### Public package, application, SDK, or service

The target profile provides:

- a concise package entry point;
- package-specific contributor or agent routing;
- a short documentation index;
- a first-success quickstart;
- detailed user documentation as needed;
- a development index and current maintainer documentation;
- optional generated reference.

The exact filenames belong to repository policy.

When package behavior has an observable result, the first-success path shows a
concrete input and expected result. A later verification section does not
substitute for an understandable first-use outcome.
Before finishing, compare each documented expected result with the current
implementation or a test and resolve any contradiction.

### Small package or implementation-only component

A concise package entry point may be sufficient when it already covers:

- purpose;
- supported use;
- installation or loading;
- basic verification;
- links to inherited contributor guidance.

Add package-local agent guidance only when the package differs from its parent.
Add a documentation index and quickstart when the package entry point can no
longer provide a clear first-use path.

### Shared documentation domain

A repository may maintain documentation shared by many related packages. The
shared domain should have:

- a clear audience and scope;
- a short index;
- explicit ownership;
- rules preventing one package's private behavior from becoming a universal
  contract by accident.

### Maintainer-only domain

Standards, evaluation tooling, fixtures, and implementation material used to
maintain the documentation or agent workflow may use a non-public maintainer
domain. This material should not be required reading for ordinary users of the
standards.

## Documentation roles

| Concept | Responsibility |
|---|---|
| Package entry point | Purpose, installation, first use/build/test, and links |
| Agent/contributor routing | Local constraints, ownership, important files, verification, and documentation routes |
| Documentation index | Short map to detailed pages; it does not reproduce them |
| Quickstart | Complete first-success workflow for a package user, including a concrete input and expected result when behavior is observable |
| User pages | Supported guides, concepts, configuration, recipes, and troubleshooting |
| Development index | Short map to internals, testing, specifications, and maintenance pages |
| Development pages | Current architecture, ownership, debugging, testing, and release behavior |
| Reference | Generated or maintained API/type/schema/protocol details |

Keep package entry points concise. Move detail into focused pages once the
entry point becomes difficult to scan.

## Terminology in authored content

Name the concrete item being discussed: document, page, file, specification,
requirement, work item, task, source code, test, generated output, or
evaluation result.

Do not use “artifact” as an umbrella label for documentation, code,
specifications, requirements, tasks, or tests. Reserve it for established
technical terms such as build, release, test, evaluation, or provider-native
artifacts and literal paths or APIs such as `artifacts/` or
`upload-artifact`.

## Choose the documentation scope

Choose the narrowest authoritative scope.

1. Content about one package's supported behavior belongs with that package.
2. Current implementation details belong with the package that owns the code or
   runtime boundary.
3. A shared abstraction normally belongs with the package that defines it, even
   when several packages consume it.
4. A cross-package scope is appropriate when independently owned packages must
   coordinate and no package provides a clear authoritative home.
5. A shared user-documentation domain is appropriate when the audience consumes
   a common extension or integration surface across many packages.
6. Generated documentation belongs with the maintained source that produces
   it; the generated destination remains output.

If ownership is uncertain, record the question or defer the move. Do not place
the page at repository root merely because that is convenient.

## Specifications and implementation pages

A specification describes an intended target. An implementation page describes
current code.

When a package implements a specified behavior, its implementation page should:

- link the normative specification;
- say that it maps the implementation rather than redefining the contract;
- identify maintainer entry points;
- explain package-owned responsibilities and non-responsibilities;
- identify important invariants and verification boundaries.

The specification may link primary user and implementation pages for
maintainer discoverability. A consumer page does not need to expose an internal
target specification merely to preserve authority. Output pages do not need to
link internal meta-specifications used to develop the standards themselves.

## Avoid duplication

- Give every contract one authoritative source.
- Let other pages summarize only what their audience needs.
- Link audience-compatible lifecycle, compatibility, persistence, and protocol
  detail instead of independently redefining complete rules.
- Extract a shared concept when three or more consumers would otherwise repeat
  the same explanation.
- Keep proposed behavior in target specifications, not in current user or
  implementation guides.
- Prefer tested or generated examples when the same contract appears in code
  and documentation.
- Use Git history rather than maintaining duplicate narrative change logs for
  ordinary edits.

When a normative contract changes, review its linked user guides and
implementation mappings for stale summaries.

## Make documentation discoverable

Every authored page should be reachable in at most two documentation links from
the nearest repository, package, or shared-domain entry point.

Typical chains are:

```text
repository documentation index
  -> development index
    -> standard or cross-package specification

package entry point
  -> package documentation/development index
    -> focused page

shared-domain index
  -> shared consumer guide
```

Every multi-page documentation scope should have a short index. Every
specification index should link all of its authored pages and files. A package
development index should be linked from a package entry point rather than being
discoverable only from a task or search.

## Current-state documentation

Public user documentation and implementation/maintainer documentation describe
current supported behavior.

They may be edited before code in the working tree, but new claims must be
committed with the code that makes them true. Target-only behavior remains in
specifications and requirements until implementation is committed.

Current consumer documentation describes delivered behavior directly in
public, self-contained vocabulary. Do not copy task/specification phase names,
requirement IDs, progress labels, or internal target links. Translate a
necessary current limitation into user-domain language and omit future plans.
Internal phases are omitted even when labeling delivered or unimplemented work.
Rewrite delivered capabilities in product terms and omit phase labels entirely.

## Moving existing pages

1. Establish the page's audience, authority, and owner.
2. Verify only the claims and examples touched by the move.
3. Move the authored source rather than copying it into two editable locations.
4. Preserve public URLs through repository-approved compatibility behavior.
5. Update owning indexes and inbound links.
6. Defer pages that require broad reconstruction, recording the likely owner
   and a useful future trigger.

Migration should improve ownership without silently becoming a full rewrite.

## Generated output

Repository policy must identify:

- authored sources;
- generated reference inputs;
- prepared documentation-site inputs;
- final built output;
- whether generated snapshots are committed.

Generated output is never edited directly. If a generated page is wrong,
change its maintained source or generator.

A request to correct generated output includes updating its maintained source
and running the approved generator unless the user narrows scope. If generation
is unavailable or fails, leave generated output unchanged and report the
failure and remaining action without claiming a refresh.

## Preserve boundaries when blocked

A blocker does not broaden scope or authorize bypassing ownership,
source-of-truth, audience, validation, or publication boundaries. Complete safe
in-scope work, report what is blocked and what remains, and ask before a
boundary-changing workaround. Do not weaken validation or claim incomplete work
as complete.

## Adoption

Apply the standard prospectively and when documentation is touched. Existing
packages remain valid while migration is incomplete.

Do not create:

- placeholder quickstarts;
- nearly empty indexes with no useful route;
- copied boilerplate that claims unsupported behavior;
- speculative package baselines reconstructed from unfamiliar code.

## Placement decisions and layout defaults

Choose an obvious package or shared scope without asking the user to confirm
routine placement or explaining internal ownership terminology. If materially
different scopes remain plausible, recommend one and ask one focused question.

Document profiles and file trees are recommended defaults. Honor an explicit
approved alternative when it preserves required content, audience, authority,
discoverability, generated-output, and source-of-truth boundaries.