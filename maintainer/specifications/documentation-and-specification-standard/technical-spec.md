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
   - include concrete, verified examples and observable results;
   - keep one primary maintained explanation and use links or focused
     summaries elsewhere;
   - keep user and developer documentation aligned with available behavior.
4. **Specifications, requirements, tasks, and progress**
   - specifications describe intended behavior;
   - requirements track implementation, verification, and documentation;
   - tasks track approval and execution;
   - requirements are necessary and traceable to approved outcomes,
     preserved contracts, necessary consequences, or approved policies and
     decisions;
   - variants and examples remain grouped unless independent tracking adds
     value;
   - unresolved public, persisted, compatibility, security, privacy, or
     user-visible behavior remains a question unless the decision is
     authorized;
   - an approval-gated recommendation remains outside requirements and
     implementation until approved;
   - progress notes in specifications are allowed when they clarify a
     meaningful current/target difference and remain shorter than the
     requirements they reference.
5. **Testing and verification**
   - select the lowest-cost boundary that can reliably detect the required
     failure without mocking away the behavior;
   - distinguish unit/component, integration, end-to-end, hosted, and manual
     evidence by what each proves;
   - treat a mock that supplies or bypasses the claimed behavior as
     non-decisive evidence;
   - cite existing coverage only when it proves preserved behavior; otherwise
     plan focused evidence or record the gap;
   - avoid tests for unresolved behavior and duplicate coverage without a
     distinct risk-based reason;
   - distinguish requirement acceptance from additional lower-level
     implementation robustness checks;
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
being discussed. It does not teach concrete language by repeating a forbidden
umbrella word. User-documentation guidance similarly says to explain available
behavior in user language instead of listing forbidden planning terms.

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
testing explanations. It does not maintain a prose inventory of every package;
the package registry and package entry points provide the current inventory.

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

Unresolved material behavior remains a question. A recommendation may explain
tradeoffs, but it is not a completion obligation and does not authorize an
implementation choice.

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
- links to the two public guidance documents;
- the additional maintainer route used only when changing the rules.

It does not repeat file-role explanations, forbidden-word lists, reference
matrices, testing taxonomy, or migration procedures.

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
give the agent planning context inappropriate for user documentation, point the
request at generated output, request current documentation for an
unimplemented target, or make the normal generation or verification path
unavailable. The expected behavior preserves the underlying reader,
maintained-source, scope, verification, and completion boundaries.

Agent-visible candidate guidance states the desired general behavior without
enumerating the fixture's forbidden words. Test fixtures use held-out planning
vocabulary and varied examples. Deterministic token checks may remain narrow
backstops, but the primary assessment asks whether the produced page serves its
reader and whether headings name their actual contents.

Requirement-quality calibration uses three different small-project tasks and
seven producer profiles: GLM at low/high/max and GPT through ChatGPT login at
medium/high/xhigh/max. The primary scenarios cover a public static website, a
public REST API with a performance concern, and a full-stack web application.
Producing agents receive an evaluation-only requirement-minimal guidance
snapshot and no task guidance. The original Test 22 remains preliminary
evidence for translating already-classified scope; same-family package/API
scenarios remain optional controls.

Each scenario has an evaluator-only semantic target covering necessary
outcomes, compatibility constraints, acceptable grouping, supporting details,
and optional adjacent work. Scenario documentation establishes the actual
project purpose, users, architecture, current behavior, pinned source
revision, and relevant source subset.

Generated requirements are assessed semantically rather than through exact
keywords, row counts, headings, or file shapes. The implementing agent maps
every output to its target with producer model and effort visible, identifies
omissions and expansion trends, and prepares aggregate findings plus one
concise row per run. The human reviews that interpreted baseline and opens full
generated files or raw evidence only when needed.

Higher producer effort may identify more risks and improvements, but does not
silently promote them into completion requirements. Useful discoveries remain
visible as questions, recommendations, supporting details, or follow-ups.

After the direct baseline is accepted, a calibrated semantic evaluator may
compare requirement coverage, added obligations, grouping, public decisions,
wrong-record material, testing boundaries, and review burden. The evaluator is
calibrated against the accepted human interpretation before it is used on
candidate guidance.

The current task-guidance baseline reuses the same 21 project/model/effort
cells and asks only for one task file with a Draft plan. Standing task guidance
must elicit requirement verification without a testing instruction in the
prompt. The approved candidate changes general documentation guidance and
canonical task guidance together, then reruns the exact 21 cells and three
project-batched semantic evaluations before human review.

`agents/TASKS-v7.md` is the canonical task-guidance source. A repository sync
command generates
`application/python/agent_terminal_app/default_config/TASKS_v7.md`, and an
application-package test requires exact byte parity. Task-only planning may run
safe diagnostics but leaves only the requested task-file mutation.

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
