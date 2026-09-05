# Documentation and specification standard technical specification

## Architecture

The target uses three documentation layers with distinct authority and
audiences:

| Layer | Purpose | Publication |
|---|---|---|
| Generic standards | Reusable, package-neutral documentation and specification concepts | Public |
| Repository policy | Crystal Lattice paths, profiles, exceptions, and tooling integration | Public |
| Maintainer material | Specifications, evaluation tooling, and implementation details for evolving the standards | Not public by default |

The generic standards and repository policy are output pages governed by
this meta-specification. They do not link back to the meta-specification.

## Target source structure

```text
docs/
└── development/
    ├── index.md
    ├── standards/
    │   ├── index.md
    │   ├── documentation.md
    │   └── specifications.md
    ├── repository/
    │   ├── index.md
    │   ├── documentation.md
    │   └── specifications.md
    └── specifications/
        └── <cross-package-capability>/

maintainer/
├── README.md
├── specifications/
│   └── documentation-and-specification-standard/
│       └── agent-behavior-verification/
└── <standards-maintenance tooling and tests>
```

`maintainer/specifications/` intentionally shortens the ordinary
`<package>/docs/development/specifications/` shape. The whole `maintainer/`
domain is development-only, so intermediate `docs/development/` indexes would
not distinguish another audience or source-of-truth boundary.

## Generic standard boundary

The generic pages use package-neutral terms such as:

- repository;
- package;
- documentation entry point;
- package user;
- package contributor;
- work item;
- documentation-site source and generated output.

They define:

- documentation profiles and document roles;
- audience and context boundaries for every document role;
- normal, pointer-only, evidence-only, and prohibited reference directions;
- normative contract, consumer guide, implementation guide, and generated
  reference distinctions;
- package-local ownership;
- generalized specification ownership and package-specific refinements;
- specifications as targets;
- requirements as live-state tracking;
- approval and execution through the repository's work-tracking mechanism;
- current-state public and maintainer documentation;
- proportional specification files;
- anti-duplication and discoverability;
- boundary preservation and honest partial completion when a compliant
  documentation workflow is blocked;
- evidence, verification, and optional decision records.

They do not name Crystal Lattice packages, `plugins/docs/`, `tasks/`,
`TASKS-v7`, `docs_site/prepared/`, or repository-specific test harnesses.

## Concrete terminology

The generic documentation standard owns the reusable terminology rule for
authored content. The generic specification standard links that rule and
applies it to specification indexes, requirements, work items, decisions,
current documentation, source code, and tests.

Documentation and guidance name the concrete item being discussed. They do not
use “artifact” as an umbrella label for documentation, code,
specifications, requirements, tasks, or tests. The term remains available when
it is an established technical concept, including build, release, test,
evaluation, or provider-native artifacts and literal paths or APIs such as
`artifacts/` or `upload-artifact`.

## Repository-policy boundary

The repository policy maps generic concepts to:

- root and package documentation paths;
- public-package, small-package, shared-domain, and maintainer profiles;
- root cross-package specifications;
- `plugins/docs/` as the shared plugin-authoring documentation domain;
- individual plugin package ownership;
- `tasks/` as approval and execution tracking;
- root and package `AGENTS.md`;
- `CONTRIBUTING.md`;
- canonical and bundled `TASKS-v7`;
- documentation-site registry, assembly, navigation, and deployment;
- compatibility behavior for relocated public pages;
- documentation and task-guidance validation.

Repository policy extends the generic rules and contains only local mappings,
exceptions, and operational requirements. It does not restate the complete
generic explanations.

Within the shared plugin-authoring domain, a focused page is linked from
`plugins/docs/index.md`. When it refines one canonical plugin guide, that guide
also links the focused page so authors encounter the refinement in the ordinary
topic flow.

## Generalized specification ownership

Every package may define specifications for behavior it owns. A package is not
limited to documenting implementation merely because it also implements a
broader contract.

Choose the narrowest authoritative scope:

1. Behavior owned by one package is specified with that package.
2. A package-specific refinement is specified with that package and links the
   broader contract.
3. A shared abstraction is normally specified with the package that defines
   it, even when several packages consume it.
4. A cross-package scope is used when independently owned packages must
   coordinate and no package provides a clear authoritative home.

A package-specific specification may add or strengthen requirements and define
allowed platform behavior. It must not silently weaken or contradict a broader
contract. Approved exceptions are linked from both scopes.

Before creating a substantial package specification, the agent proposes its
owning scope, behavior scope, justification, related contracts, and expected
specification files. The user approves creation through the task workflow
unless the existing approved task already authorizes it.

A direct request to create a substantial specification is not by itself
approval of an owner/scope/overlap proposal that has not yet been presented.

## Target, requirements, task, and current documentation

| Source | Authority |
|---|---|
| Specification | Intended target behavior and design |
| Requirements | Live implementation, verification, documentation, and evidence state |
| Task | Approval, execution scope, plan, findings, and completion |
| Public user docs | Current supported behavior |
| Implementation/maintainer docs | Current implementation and maintenance behavior |

Specifications are updated before implementation. They are not proof that the
target is currently available.

For small changes, the specification is normally committed with the code or in
the immediately preceding commit. New capabilities begin with a specification
and requirements. Major changes introduce separate target versions only when
one evolving target would be confusing.

Temporary progress in a specification or its index is used only for work
expected to span more than one commit when target/current divergence would
otherwise be unclear. It links the task and affected requirement IDs and is
removed after all relevant requirements are verified.

## Audience and context boundaries

Every document or maintained file has an intended audience and role. A
document may assume only concepts introduced in that document or available
through documentation intended for the same audience.

Access to broader repository context does not transfer that context to the
document's readers. Information from tasks, specifications, requirements,
implementation notes, agent instructions, commits, or maintainer material may
be used to decide what to write, but it is not copied into another document
unless the destination audience is expected to know it and the destination
role owns it.

Cross-audience information is translated into the destination audience's
vocabulary. Internal phases, requirement IDs, task paths, approval state,
temporary progress, evidence notation, and maintainer workflow are excluded
from consumer documentation unless a term is itself a public contract,
introduced for the reader, and necessary to use the product.

Reference relationships have four forms:

- **normal dependency:** the destination may rely on the referenced material;
- **labeled pointer:** navigation is allowed, but the main content remains
  understandable without the other audience's context;
- **evidence reference:** allowed for live-state or delivery traceability;
- **not allowed by default:** requires an explicitly justified public contract
  or governance exception.

The generic standard defines reference rules among package entry points,
consumer guides, public reference, development guides, specifications,
requirements, agent/contributor guidance, tasks, maintainer material, and
generated output. Repository policy maps those roles to exact paths.

Consumer documentation normally depends only on other consumer documentation
and public reference. A clearly labeled development pointer is allowed, but
installation, supported use, and troubleshooting do not depend on internal
specifications, requirements, tasks, AGENTS files, or maintainer material.

Development documentation may map current implementation to specifications and
requirements. Specifications may link related targets, requirements, and
affected current docs. Requirements may use code, tests, docs, tasks, reviews,
and commits as evidence. Tasks and maintainer specifications may refer broadly
within their scope, but output documents do not inherit their context.

## Boundary preservation under blockers

A blocked operation does not expand task scope, change document ownership, or
authorize bypassing a source-of-truth, audience, validation, or publication
boundary. These constraints remain part of the required outcome when the normal
mechanism is unavailable.

When a compliant workflow is blocked, an agent:

1. completes only safe work that remains within scope and ownership;
2. does not directly edit derived output, substitute another owner, weaken
   requirements or validation, or create an alternate production path;
3. reports what was completed, what is blocked, why it is blocked, and the
   exact remaining action;
4. requests direction before a workaround that changes scope, ownership,
   source of truth, validation, public behavior, or persisted state;
5. does not mark the task or requirement complete while a required step remains
   blocked.

A request to correct generated output includes updating its maintained source
and attempting the approved generator unless the user narrows scope. The agent
does this before reporting the refresh as blocked.

Equivalent local commands and reversible in-scope implementation details do not
require escalation. A workaround becomes approval-relevant when it crosses an
established document, ownership, production, or evidence boundary.

## Documentation authority and duplication

Substantive pages fit one authority class:

- normative specification;
- consumer/user guide;
- implementation/maintainer guide;
- generated reference;
- repository or documentation infrastructure.

Each behavioral contract has one normative owner. Other pages may summarize
only what their audience needs and do not independently redefine complete
lifecycle, compatibility, persistence, or protocol semantics. A consumer page
does not need to expose an internal target specification merely to preserve
normative ownership; the specification may link the current consumer page for
maintainer discoverability.

Implementation mapping pages link their target specification and describe
current code, ownership, invariants, and tests. User guides teach current
supported use using public concepts that stand alone for their audience.
Target-only behavior, internal phase names, requirement IDs, task paths, and
temporary progress remain in specifications, requirements, and work tracking.

## Discoverability

Every page participates in an entry-point chain:

```text
repository docs index
  -> development index
    -> standards, repository policy, or cross-package specification index

package README/AGENTS/docs index
  -> package development index
    -> package specification or maintainer page

shared-domain index
  -> shared consumer guide
```

Every authored page is reachable within at most two documentation links from
the nearest repository, package, or shared-domain entry point.

Indexes remain concise but complete:

- every multi-page development scope has an index;
- every specification index links its authored pages and files;
- every package development index is linked by a package entry point;
- specification indexes link primary user guides and implementation mappings
  where useful;
- public package docs are registered for site assembly.

## Maintainer boundary

`maintainer/` is not a public documentation source. It owns:

- meta-specifications for standards and agent workflows;
- deterministic and real-model evaluation tooling for those workflows;
- fixtures, review-bundle ordering, and preparation belonging to that tooling;
- future standards-maintenance utilities whose audience is the maintainers of
  the rules rather than ordinary package users.

Existing task-guidance evaluation under `test/task_guidance/` and its dedicated
fixtures are targeted for relocation under the reusable agent-evaluation
framework's `maintainer/`-owned domain. Subtask 015 creates the framework and
documentation-standard consumers. The task-guidance alignment subtask then
moves and adapts the existing task-guidance consumer, updates commands and
references, and verifies equivalent behavior.

Production/package tests remain with their owning packages. `maintainer/` is
not a replacement for ordinary shared test infrastructure.

## Agent routing

Root `AGENTS.md` distinguishes:

- **Applying the rules:** read repository policy, generic standards, and the
  owning package entry points.
- **Maintaining the rules:** additionally read this meta-specification,
  requirements, active task, and relevant maintainer tooling documentation.

Ordinary output pages do not expose task chronology, evaluation internals, or
links to this meta-specification.

## Human-led contributor workflow

Root `CONTRIBUTING.md` is written for the human directing AI-assisted
development. Its six-stage workflow covers brainstorming, review of durable
records and decomposition, plan approval, implementation supervision,
verification/review, and findings resolution/delivery.

Every initial change and follow-up has a plan before implementation. Planning
may remain a short conversation for a local change, use one task execution
plan for normal work, or use staged task plans for high-risk and multi-part
work. Specification need is a separate decision:

- update an affected existing specification when its target behavior or design
  changes;
- require a specification for a large new feature;
- for other work, consider whether a specification would clarify an existing
  feature, durable behavior, public contract, or important design.

Current user documentation changes whenever delivered behavior affects a
consumer.

The workflow places realistic, stage-specific prompt examples where the human
uses them. The initial brainstorming example may carry substantial new product
or domain context. Later prompts remain short because applicable project and
task guidance should already be supplied through the developer/system message
or first user message.

The guide tells humans how to verify that applicable `AGENTS.md` and task
guidance reached the model by inspecting the effective compiled or outgoing
instructions through available development surfaces. It explains where
standing and task-specific context belongs without embedding the full
contributor workflow in agent instructions.

AI normally drafts specifications, requirements, tasks, plans, code, automated
tests, and documentation. Human review focuses on outcomes and material
decisions: scope, boundaries, non-goals, alternatives, compatibility, failure
behavior, security, persistence, migration, consumer impact, and remaining
uncertainty. Mechanical traceability or consistency checks may be delegated to
an implementing or reviewing agent.

Unit, integration, end-to-end, and manual evidence are distinct. At plan
review, the human asks which boundaries each kind of evidence will cover. At
completion, the human checks what actually ran, what it demonstrated, what
failed or skipped, and what remains unverified. AI review remains advisory;
manual verification and final acceptance remain human responsibilities.

The specific product features used to inspect messages are owned by their
packages. Their implementation, tests, and package documentation are not part
of this documentation-and-specification standard.

## Publication

Package-local authored files remain sources of truth. Prepared and built site
trees are generated and never edited directly.

The package registry declares public sources and destinations. `AGENTS.md` and
`maintainer/` are excluded by default. Repository standards and policy are
public development guidance unless a page contains explicitly sensitive
material.

Public user and implementation/maintainer documentation must match committed
code. A working tree may stage documentation first, but it is committed with
the implementation that makes new current-state claims true.

Observable examples include a concrete expected result. Before completion,
each documented result is compared with the current implementation or a test,
and contradictions are resolved rather than copied into both first-use and
verification sections.

## Migration

Adoption is incremental:

- do not create empty package trees or placeholder quickstarts;
- move ownership-clear pages with bounded verification;
- preserve public URLs through compatibility behavior during the initial
  migration;
- defer uncertain pages rather than reconstructing broad undocumented
  behavior;
- record deferred pages with likely owner, reason, and useful trigger.

The first migration covers Core Python, application configuration, shared
plugin overview, selected root architecture/protocol/reference pages, and
generated examples/reference ownership.

## Validation

Deterministic validation should cover, in stages:

- broken relative links;
- page reachability from owning indexes;
- specification indexes omitting authored pages or files;
- duplicate requirement IDs;
- invalid registry sources, IDs, destinations, and collisions;
- package docs assembly and source/output boundaries;
- canonical/bundled task-guidance parity;
- moved maintainer-tool commands and fixtures;
- public docs and navigation paths;
- normal MkDocs build and newly introduced warnings.

Behavioral instruction validation should additionally exercise whether
representative supported agents can apply `DOCGEN-*` and `DOCREP-*` rules
through the programmatic framework specified in
`maintainer/specifications/agent-evaluation-framework/`.

Detailed consumer scenarios are owned by
[agent-behavior verification](agent-behavior-verification/index.md). They
deliver the exact candidate AGENTS/routed files through normal agent
mechanisms, use short human-style task prompts, and assert on generated files,
mutations, provenance, and responses. They do not ask agents to author or
summarize the standards being tested.

Cached seed conversations establish narrow concrete task-specific bases. Most
are read-only factual investigations of a package, issue, task, or contract. A
seed may instead perform one tightly constrained operation when its completed
state is the shared base for follow-up tasks. A seed may feed several closely
related continuations and is reusable across candidate-guidance revisions
because guidance is added only after the continuation forks.

Behavioral model results supplement rather than replace:

- static checks of the authored pages;
- deterministic repository assertions;
- explicit human review.

Behavioral validation deliberately creates boundary pressure. Scenarios may
give the agent internal context unavailable to the destination audience, point
the user request at derived output, request current documentation for an
unimplemented target, or make the compliant generation/verification path
unavailable. The expected behavior preserves audience, ownership,
source-of-truth, scope, validation, and completion-honesty boundaries rather
than optimizing for apparent completion.

New guidance-clarity scenarios use a baseline-first comparison:

1. Pin the exact committed guidance from before the proposed wording change.
2. Run the ordinary task against that baseline before changing the prompt,
   assertion, fixture pressure, or expected destination behavior.
3. Confirm that at least one representative model run exhibits the targeted
   behavior. A case that always passes may remain a robustness check but is not
   evidence that new wording fixed a regression.
4. Reuse the same cached seed, prompt, fixture, assertions, and model profile
   with candidate guidance variants.
5. Start with the shortest general rule. Add detail or examples only when
   paired evidence shows the concise wording is insufficient.
6. Preserve instruction hashes, paired evaluation results, failures, and mixed
   outcomes.
   Do not make a candidate pass by weakening the task or assertions.

Baseline guidance is restored only inside isolated evaluation workspaces or an
explicit guidance-source overlay. The main working tree may retain the
uncommitted review draft.

The calibrated suite has a routine group for frequent high-signal guidance
checks and an extended group for lower-frequency continuations and reverse
ownership cases. Ordinary guidance changes run the routine group on the
lower-cost supported model plus a small second-model sentinel set. Material
changes and final verification run all scenarios on at least one model and use
additional cross-model coverage when observed variance justifies it.

After representative runs, a separate calibration review evaluates whether the
initial seed/test matrix is proportionate and informative. It may recommend
cutting redundant cases or adding cases that expose missing clarity signals,
but the approved verification specification and suite change only after user
approval.

Acceptance and contract tests may reference requirement IDs. Ordinary
low-level tests do not need them. Manual verification is recorded only when a
human performs or directly confirms it.

## Bootstrap

This meta-specification and requirements are created from the already approved
task decisions before the output standards exist. They are the target for the
remaining implementation.

The bootstrap does not claim that existing documentation conforms. After the
generic and repository pages are authored, this meta-specification is reviewed
once against the resulting standard and adjusted through the task workflow if
the approved target changed.

## Approved August 18 calibration extension

The generic standards additionally define:

- recommended layout defaults and explicit approved structure overrides;
- clear documentation-scope and authoritative-source terminology;
- proportionate agent-routing read triggers.

### Placement decisions and user communication

Documentation placement is normally an implementation decision derived from
audience, behavior scope, and the authoritative source.

When one package or shared domain is the clear home, the agent:

- chooses that location without asking for confirmation;
- does not describe the choice using opaque phrases such as “honest owner” or
  “honest normative owner”;
- reports the created or changed paths and only includes placement rationale
  when it helps the user understand a material boundary.

When multiple materially different scopes remain plausible, the agent states
the ambiguity briefly, recommends one option with its reason, and asks one
focused question before making a boundary-changing choice.

Approval to create a substantial specification remains separate from routine
file placement. Existing task or conversational authorization is not repeated
merely to confirm an obvious package-local path.

### Recommended layouts and explicit overrides

Documentation and specification trees shown by the standards are recommended
defaults. They communicate common document roles without creating a mandatory
schema.

An explicit user- or work-item-approved layout is followed when it preserves:

- required content and traceability;
- audience and authoritative-source boundaries;
- discoverability from the relevant index or entry point;
- generated-output and maintained-source boundaries;
- one maintained source rather than duplicate editable forms.

A safe override does not require duplicate confirmation. If a requested layout
would omit required information, create competing sources, hide material
decisions, or cross an audience, ownership, or source-of-truth boundary, the
agent explains the conflict and recommends the smallest compatible
alternative.

### Proportional agent routing

Before creating, moving, materially restructuring, or deciding the audience,
placement, or required file set of documentation or specifications, root
AGENTS guidance requires the repository-policy and generic-standard indexes and
the directly relevant pages they route to be read in full.

A local factual correction to an existing page does not require unrelated
standards reading when the destination audience, maintained source, and
placement are already clear. Standards-maintenance work additionally reads the
meta-specification, requirements, active task, and relevant maintainer tooling.

### Behavioral verification extension

Routing-read scenarios deliver applicable AGENTS content while keeping routed
standard pages available through the repository filesystem, then verify that
required pages were read before the first mutation. They do not preload routed
page contents into the instruction merely to make the behavior pass.

Behavioral validation also covers interaction quality and explicit safe
overrides. Obvious package-local placement does not trigger an ownership
lecture or confirmation question. A task-approved file shape that differs from
the recommended default is followed unless it violates a substantive boundary.