# Documentation and specification standard technical specification

## Guidance architecture

The target uses three layers:

| Layer | Purpose | Publication |
|---|---|---|
| Documentation and specification guide | Project-independent structure, writing, specification, requirements, testing, and verification guidance | Public |
| Crystal Lattice documentation conventions | Repository paths, shared domains, exceptions, task integration, publication, and migration | Public |
| Maintainer material | Specifications, requirements, evaluation tooling, and implementation details for evolving the guidance | Not public by default |

The two public documents do not explain the maintainer architecture or label
themselves as reusable standards. They are written for someone doing ordinary
documentation, specification, and verification work.

## Target source structure

```text
docs/
└── development/
    ├── index.md
    ├── documentation.md
    ├── crystal-lattice-documentation.md
    └── specifications/
        └── <capability>/

maintainer/
├── README.md
├── specifications/
│   └── documentation-and-specification-standard/
│       └── agent-behavior-verification/
└── <guidance-maintenance tooling and tests>
```

`docs/development/index.md` is a short router. The two substantive documents
are the only public guidance pages created by this work.

Existing routes under `docs/development/standards/` and
`docs/development/repository/` contain minimal non-authoritative compatibility
pointers. The navigation and compatibility workstream may later replace them
with redirects. They do not remain parallel editable sources.

## Documentation and specification guide

`docs/development/documentation.md` is independent of Crystal Lattice names,
paths, packages, tooling, and maintainer terminology. It starts with a concrete
default layout so readers understand the available file roles before reading
placement or workflow rules.

The layout is a menu, not a schema. No file or directory shown by the guide is
universally mandatory. Depending on the task, an existing README, one new page,
an index plus one page, one specification file, or a larger specification
directory may all be complete solutions. The guide tells readers to use only
the files that improve understanding.

The guide uses this order:

1. **Default structure and adapting it to size**
   - one annotated repository/package tree;
   - explicit examples of README-only, one-page, small multi-page, and
     substantial specification forms;
   - no package-profile taxonomy before the structure is understood.
2. **What each file is for and how to write it**
   - README;
   - AGENTS;
   - index;
   - quickstart;
   - user documentation;
   - developer documentation;
   - specification;
   - requirements;
   - optional testing strategy;
   - optional reference and decision records.
3. **Writing useful pages**
   - introduce terms before using them;
   - write for the reader of the page;
   - distinguish relevant source information from source wording, labels,
     examples, or organization that the destination should not inherit;
   - preserve exact requested and established terms while defining or
     translating other terms for the destination;
   - include concrete, verified examples and observable results;
   - keep one primary maintained explanation and use links or focused
     summaries elsewhere;
   - keep user and developer documentation aligned with available behavior.
4. **Specifications, requirements, tasks, and progress**
   - specifications describe intended behavior;
   - requirements track implementation, verification, and documentation;
   - tasks track approval and execution;
   - progress notes in specifications are allowed when they clarify a
     meaningful current/target difference and remain shorter than the
     requirements they reference.
5. **Testing and verification**
   - select the least expensive test that proves the requirement without
     mocking away the important boundary;
   - distinguish unit/component, integration, end-to-end, hosted, and manual
     evidence by what each proves;
   - record deliberate test exclusions and avoid duplicate coverage without a
     risk-based reason;
   - report decision-relevant verification before routine quality checks.
6. **Placement, links, and generated documentation**
   - place a page with the package or component whose behavior it explains;
   - use a shared location only when no single component provides a sensible
     home;
   - keep focused pages reachable from a nearby entry point;
   - edit the maintained source of generated documentation and report a failed
     refresh honestly.

The guide uses direct terms such as user documentation, developer
documentation, specification, requirements, task, testing strategy, reference,
and generated documentation. It avoids unexplained terms such as normative
owner, authoritative scope, meta-specification, reusable standard, or
current-state documentation.

The writing guidance is positive: name the page, file, test result, or output
being discussed. It does not teach terminology by listing prohibited words.
The source of a term may be a conversation, task, specification, requirement,
decision, existing file, example, review comment, or another maintained
record. Relevance of that source does not by itself make its wording suitable
for a destination.

## Source wording and destination terminology

The project-independent guide owns both the general rule and its concise
applications to the file roles it defines.

Before presenting the rule, the guide defines:

- **input material**: a request, conversation, existing file, specification,
  review note, or other information being adapted;
- **destination**: the maintained artifact being written.

A file can serve as input material in one change and as a destination in
another. The definition appears before either term is relied upon.

The general rule establishes four points:

1. A request or source can define an intended outcome without defining the
   names used in another maintained destination.
2. Wording, labels, examples, and organization from conversations and other
   records are source context.
3. Exact wording is retained when it is explicitly required or already
   established by the product, interface, or domain rather than merely present
   in a file.
4. Other terminology is introduced and explained or translated into the
   behavior, component, condition, outcome, or relationship meaningful to the
   destination.

Each point is followed by one explicitly marked portable example. Examples:

- use vocabulary distinct from held-out behavioral prompts;
- illustrate one transfer rather than enumerate destinations, permitted
  wording, or prohibited wording;
- avoid Crystal Lattice paths, task structure, and repository-specific terms;
- do not replace the destination-specific instructions below.

After the four rule/example pairs, a separate application section covers the
distinctions that readers cannot reliably derive from the general rule alone:

- a task's local wording remains local, illustrated with a different label
  from behavioral fixtures, while other records use its descriptive title and
  full path;
- specifications, requirements, and decisions use domain terms and descriptive
  links, and source descriptions become requirements only when their
  observable meaning is required;
- source and tests name behavior, with requirement IDs accompanied by an
  explanation of the invariant or assertion;
- developer documentation explains current implementation without requiring
  linked internal records;
- user documentation translates internal grouping into delivered
  capabilities, replaces inherited local labels, and omits internal future
  work without depending on developer context;
- headings, filenames, identifiers, and commit or pull-request titles name
  destination behavior instead of unexplained source labels.

A requirement or decision reference used outside its canonical record pairs
the stable identifier with a concise description and direct link. The
description gives local meaning without copying the full normative text.
Internal requirement identifiers do not appear in user documentation. Code and
tests may use them for traceability only when the surrounding comment,
docstring, parameter, or assertion explains the relevant behavior.

## Crystal Lattice documentation conventions

`docs/development/crystal-lattice-documentation.md` assumes the first guide has
already defined the file roles. It adds only Crystal Lattice-specific
information:

- package and root paths;
- the package-local default;
- root cross-package specifications;
- `plugins/docs/` as the shared plugin-authoring documentation domain;
- individual plugin documentation;
- the short `maintainer/` boundary;
- `tasks/`, requirements, and AGENTS integration;
- documentation-site sources, generated destinations, registry, and commands;
- migration and public-route compatibility.

It does not repeat the general writing, specification, requirements, or
testing explanations, including the project-independent terminology and
reference rules.
It does not maintain a prose inventory of every package; the package registry
and package entry points provide the current inventory.

A specification is named after the capability it defines. Cross-package
placement is a location decision, not a naming convention. Terms such as
“portable specification” are not added to titles or paths merely because
several packages implement the behavior.

A package may define a package-specific UX or platform specification when it
defines additional behavior. A root cross-package specification is used only
when independently maintained packages must coordinate and no package defines
the complete behavior.

## Specifications, requirements, and early documentation

A specification is a target and may lead implementation. Requirements track
the live implementation, verification, and documentation state. The task is
the normal approval and execution record.

Specifications do not ban progress information. Requirements remain the
detailed status record, while a specification may contain a short temporary
implementation note when the target/current difference would otherwise be
confusing. The note points to relevant requirements rather than copying their
status table.

User documentation may be drafted before implementation on a development
branch. Target-only sections are visibly marked `Not implemented` while under
review, and that marker is removed only after the behavior exists and the text
has been verified. Such a section does not reach published current
documentation by default. If proposed user-facing text must be retained before
implementation, it belongs with the specification until it can become current
documentation.

## Requirements and primary evidence

Each requirement states one necessary outcome or constraint. Failure of the
requirement means the approved task is incomplete. Supporting explanation,
implementation work, risks, suggestions, and possible follow-ups do not become
requirements unless the user approves that scope.

Requirements retain separate implementation, verification, and documentation
states. Their final column is `Primary evidence`, containing the smallest
direct reference that supports the status. Shared task, pull-request, or commit
references are recorded once below the table instead of repeated in every row.
Longer evidence notes are keyed by requirement ID only when one concise cell is
insufficient.

## Testing strategy and verification reporting

`testing-strategy.md` is optional. It is useful when behavior crosses important
layers, verification is expensive or manual, several approaches are credible,
or the reason for omitting plausible tests would otherwise be lost. Small work
keeps its test plan in the task or conversational plan.

A testing strategy identifies:

- the important behaviors and risks;
- the cheapest reliable layer for each;
- real boundaries that need integration or end-to-end coverage;
- manual, hosted, or native checks that cannot be represented faithfully at a
  lower layer;
- tests intentionally omitted and the reason.

Tests assert exact values, structures, ordering, or internal calls only when
those details are required behavior or part of a public, persisted, or
interoperability contract. For example, an implementation that returns UI
configuration as JSON does not receive an exact-key snapshot merely because
the object is easy to compare. Conversely, a change crossing a server,
transport, and frontend boundary does not rely only on isolated unit tests.

Completion reports lead with the few tests or observations that directly prove
the requested outcome. Formatting, lint, compilation, and broad test counts
are grouped as supporting checks or omitted unless they materially affect the
result.

## Root agent guidance

The root documentation section targets roughly 200–300 words. It contains only:

- the package-local default and cross-package exception;
- user versus developer documentation placement;
- specification, requirements, and task roles;
- the generated-documentation source rule;
- incremental adoption without invented baselines;
- a concise instruction to choose terminology and names for the destination
  rather than automatically reusing source wording;
- links to the two public guidance documents;
- the additional maintainer route used only when changing the rules.

It does not repeat file-role explanations, forbidden-word lists, reference
matrices, testing taxonomy, or migration procedures.

The terminology instruction is integrated by replacing less precise wording,
not by adding another root policy section. The complete root documentation
section remains approximately 200–300 words after reconciliation with the
separate root-guidance consolidation work.

The instruction includes one compact, explicitly marked portable example. It
does not reproduce the guide's complete example set or destination-specific
applications.

## Task guidance

Canonical task guidance contains only the task-specific application of the
project-independent rule. A task file may retain wording from its conversation
when doing so preserves meaningful intent, but it defines the term and remains
understandable without the conversation. Task titles and requirement,
decision, and execution-item wording use descriptive destination terms.
References to other tasks use full relative paths rather than unexplained
ordinal shorthand.

The project-independent guide owns the detailed destination rules. Task
guidance links or routes to that explanation instead of reproducing its table.
Canonical and bundled v7 task guidance are updated through the source and
synchronization mechanism owned by
[the task-guidance alignment work](../../../tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md).

## Maintainer boundary

`maintainer/` owns this specification, live requirements, agent-evaluation
tooling, fixtures, and review material used to evolve the guidance. It is not
required reading for ordinary package users or contributors applying the
public guide.

Production and package tests remain with their packages. `maintainer/` is not
a replacement for ordinary shared test infrastructure.

## Human-led contributor workflow

Root `CONTRIBUTING.md` is written for the human directing AI-assisted
development. A seven-step quick workflow mirrors the detailed workflow:
brainstorming and shaping, review of specifications, requirements, and tasks,
plan review and approval, implementation supervision, evidence and result
review, independent AI review, and follow-up planning. Independent review and
follow-up are numbered steps; their text makes clear that they apply when
useful or when additional work exists.

The process-selection table presents small local changes, normal features or
bug fixes, and high-risk or cross-package changes as three recognizable
scenarios. Separate columns summarize the normally applicable task-file and
specification forms without making specification need or task decomposition
automatic consequences of the process level.

Every initial change and follow-up has a plan before implementation. Planning
may remain a short conversation for a local change, use one task execution
plan for normal work, or use explicit approval checkpoints for high-risk and
cross-package work. Specification need remains a separate decision:

- update an affected existing specification when its target behavior or design
  changes;
- require a specification for a large new feature;
- for other work, consider whether a specification would clarify an existing
  feature, durable behavior, public contract, or important design.

During stage 2, the human reviews whether each proposed subtask delivers a
usable, tested improvement or completes an isolated responsibility. A minimum
working version and later independently valuable features may be separate
subtasks. Partial implementation and approval checkpoints remain stages within
one task, and implementation, tests, documentation, and evidence stay with
their owning outcome.

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
tests, and documentation. Five recurring concerns help humans direct review:
requirements and outcomes, scope and placement, design and complexity,
verification, and current documentation or remaining work. The guide uses
these concerns only where they help a stage; it does not repeat them as a
mandatory template. Humans may inspect the important result directly or ask
the implementing or reviewing agent focused follow-up questions. Agents remain
responsible for task-file structure, traceability maintenance, and other
record-consistency work.

The guide names common agent mistakes within those concerns: omitted,
expanded, duplicated, implementation-shaped, or unverified requirements;
changes outside the accepted scope or owning component; unnecessary
abstractions, compatibility paths, configuration, workarounds, duplication, or
tests; verification that does not cross the claimed production boundary; and
completion claims that hide remaining work or stale consumer documentation.

Unit, integration, end-to-end, and manual evidence are distinct. At plan
review, the human asks which boundaries each kind of evidence will cover. At
completion, the human checks what actually ran, what it demonstrated, what
failed or skipped, and what remains unverified. The guide asks whether
integration and end-to-end harnesses reached the claimed production path.
Repeatable procedures with machine-observable outcomes belong in automated
tests; human checkpoints are reserved for perception, exploration, product
judgment, or a real environment that automation does not faithfully
represent.

Independent AI review remains advisory. The guide provides a short general
review prompt, optional task-specific focus phrases, and a small number of
focused examples rather than one exhaustive prompt. Final acceptance and
delivery authorization remain human decisions.

Repository contribution guidance is compact. Package discovery, ordinary
commands, CI reproduction, detailed file-safety rules, and documentation
maintenance remain in agent and package guidance. `CONTRIBUTING.md` instead
provides a pull-request submission prompt and a short human review covering
outcome, scope, evidence, limitations, and the requested delivery action.
Security, support, licensing, and participation remain discoverable through
concise policy links.

The specific product features used to inspect messages are owned by their
packages. Their implementation, tests, and package documentation are not part
of this documentation-and-specification standard.

## Publication

Package-local authored files remain sources of truth. Prepared and built site
trees are generated and never edited directly.

The package registry declares public sources and destinations. `AGENTS.md` and
`maintainer/` are excluded by default. The documentation guide and Crystal
Lattice conventions are public development guidance unless a page contains
explicitly sensitive material.

Published user and developer documentation must match available behavior. A
development branch may draft target-only user text with a visible
`Not implemented` marker. The marker and target-only wording do not reach
published current guidance by default. A user may explicitly approve another
commit or publication order.

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

Deterministic validation should cover:

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

Behavioral instruction validation additionally exercises whether representative
supported agents can apply the guidance through the programmatic framework
specified in `maintainer/specifications/agent-evaluation-framework/`.

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
give the agent relevant source context whose wording, labels, examples,
organization, or references are unsuitable for one or more requested
destinations; point the request at generated output; request current
documentation for an unimplemented target; or make the normal generation or
verification path unavailable. The expected behavior preserves the underlying
reader, maintained-source, scope, terminology, reference, verification, and
completion boundaries.

Agent-visible candidate guidance states the desired general behavior without
enumerating the fixture's held-out words. Test fixtures vary source terms,
their intended meaning, and destination roles. Deterministic token and path
checks may remain narrow backstops, but initial assessment inspects complete
changed files, diffs, responses, tool behavior, and provenance and asks whether
each destination uses meaningful terminology and references without suppressing
an explicit or established term.

Before changing the guidance, the terminology follow-up samples:

- the retained Test 13 user-documentation boundary;
- source-to-task/specification/requirements/decision and filename boundaries;
- source-to-code/function/test/comment boundaries;
- specification-to-developer-documentation and
  developer-to-user-documentation boundaries;
- several source-term classes, including ordinal shorthand, sequence labels,
  and evaluative descriptions whose exact words are not agent-visible rules;
- supported models and reasoning efforts already shown to produce different
  outcomes.

Existing seeds and scenarios are reused when their facts and mutation
allowlists exercise the boundary with minimal change. A new seed is justified
only when reuse would make a source term an actual domain requirement, omit a
necessary destination, or require unrealistic fixture changes. Test 13 remains
unchanged. New or extended cases begin as observation runs: semantic and human
inspection precedes final deterministic assertions.

Candidate comparison separates the contribution of the guidance layers:

1. the first candidate adds only the four general rules to the
   project-independent guide and the concise recurring rule to root
   `AGENTS.md`;
2. the second candidate adds the short file-role applications after the
   general rules and the task-specific rule through canonical task guidance.

The same preserved scenarios are evaluated after each candidate. Simpler
terminology choices should follow the first candidate; cross-record reference,
self-containment, and task-handoff cases may require the second. Guidance is
expanded further only when repeated paired evidence identifies a remaining
shared misunderstanding.

Requirement-restraint scenarios run the same task across supported low,
medium, and high reasoning-effort settings. Higher effort may identify more
risks and improvements, but does not silently promote them into completion
requirements. Useful discoveries remain visible as questions,
recommendations, supporting details, or follow-ups.

Testing-strategy scenarios use paired pressures:

- an over-specification case where implementation details outside the required
  contract should not be frozen, initially illustrated by local UI
  configuration JSON keys;
- a feature crossing important production layers where isolated unit tests are
  insufficient.

Verification-report scenarios assess whether the final response foregrounds
the tests or observations that prove the requested behavior and keeps routine
formatting, lint, compilation, and broad counts secondary.

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
placement cases. Ordinary guidance changes run the routine group on the
lower-cost supported model plus a small second-model sentinel set. Material
changes and final verification run all scenarios on at least one model and use
additional cross-model or reasoning-effort coverage when observed variance
justifies it.

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
two public guidance documents are authored, this meta-specification is reviewed
against the result and adjusted through the task workflow if the approved
target changed.
