# Documentation and specification standard product specification

## Purpose

The repository needs documentation, specification, requirements, and testing
guidance that is easy for humans to read and precise enough for agents to
apply. The public guidance should begin with a concrete structure, explain how
to write each useful file, adapt to work of different sizes, and avoid exposing
the internal machinery used to maintain the guidance.

## Users

### Contributors and agents applying the rules

These users need to:

- understand the available documentation structure before choosing files;
- write concise README, index, quickstart, user, developer, specification,
  requirements, testing, and reference content when each is useful;
- omit files and directories that do not improve the task;
- use concrete examples and observable results;
- decide whether a durable specification is justified;
- place documentation and specifications without learning unnecessary
  repository-ownership terminology;
- update a target specification before implementation;
- keep requirements concise and prevent discovered low-priority work from
  becoming an unapproved completion condition;
- choose tests that prove important behavior at the appropriate layer without
  duplicating or overspecifying implementation details;
- identify the primary evidence that validates each requirement;
- keep user and developer documentation aligned with available behavior;
- find the effective repository rules without reading implementation history or
  validation internals.

### Maintainers changing the rules

These users need to:

- keep the project-independent guide distinct from Crystal Lattice-specific
  paths and exceptions;
- change the guidance without duplicating rules between public pages;
- understand how AGENTS, task guidance, contributor guidance, publication, and
  validation fit together;
- trace output pages and files to requirements, tasks, tests, and delivery
  evidence;
- evaluate whether concise guidance produces useful agent behavior across
  different models and reasoning efforts.
- establish semantic targets across different project types, interpret
  requirement-quality evidence across models and efforts, and give humans a
  short assessment with optional access to the complete generated work.

## Target experience

An ordinary user starts from repository or package guidance and reaches one
documentation and specification guide plus a short Crystal Lattice addendum.
The user does not need to open `maintainer/` to apply the rules.

A maintainer changing the standards is explicitly routed to this
meta-specification, its requirements, and the owning task before editing the
user-facing pages or supporting tooling.

The project-independent guide does not label itself as a reusable standard or
mention Crystal Lattice. It begins with an annotated file tree, explains each
file role once, and then gives practical writing, requirements, testing,
placement, and generated-documentation guidance.

The Crystal Lattice addendum maps those roles to actual paths, shared plugin
documentation, cross-package specifications, tasks, AGENTS files, publication,
and migration. It does not repeat the general explanations or maintain a prose
inventory of every package.

Always-loaded root guidance reinforces the small set of requirement and testing
decisions that should affect ordinary work even when no task file is active and
the detailed documentation guide is not read. Requirements and testing have
separate concise sections so their core rules are not diluted by documentation
routing, task-file mechanics, marker catalogs, or package-specific test
conventions.

The structure is optional at every level. A task may correctly update one
existing page, add one standalone page, use an index and one child page, create
one specification file, or use a larger specification directory.

User and developer documentation is written for its readers and describes
available behavior. Planning and implementation tracking stays in
specifications, requirements, tasks, and temporary development notes.

A human contributor can begin with a rough description and use AI-assisted
brainstorming to research the repository, compare approaches, and shape the
change. Every change and follow-up receives a reviewed plan before
implementation; a small change may use a conversational plan while complex or
multi-part work uses task-owned staged plans.

The quick workflow mirrors the seven detailed steps: brainstorming, reviewing
specifications and tasks, approving a plan, supervising implementation,
questioning evidence, requesting independent AI review when useful, and
planning every follow-up. A three-scenario process table shows the normal task
and specification forms for small local changes, normal features or bug fixes,
and high-risk or cross-package changes.

The contributor workflow helps the human verify that applicable repository and
task guidance actually reached the model, review important specification and
task decisions, question planned and completed unit/integration/end-to-end
evidence, identify where human judgment is still useful, and explicitly
authorize delivery. Human review concentrates on requirements and outcomes,
scope and placement, design and complexity, verification, and current
documentation or remaining work. Stage-specific prompt examples appear where
they are used and assume standing instructions are already active.

The workflow calls out recurring agent mistakes such as missing or expanded
requirements, misplaced changes, unnecessary complexity, weak verification
boundaries, stale consumer documentation, and incomplete work presented as
complete. Independent AI review and follow-up planning are separate numbered
steps whose text makes clear when they apply.

When subtasks are proposed, the human checks that each one delivers a usable,
tested improvement or completes an isolated responsibility. Deliverable
iterations use subtasks, while partial implementation and approval checkpoints
remain stages inside one task.

Specification need is considered separately from immediate change size.
Existing specifications remain current whenever their target behavior or
design changes, large new features require specifications, and other work may
justify specifying an existing feature or durable contract. Current user
documentation is updated whenever delivered behavior affects a consumer.

## Specification and current state

Specifications describe intended targets and may temporarily differ from
implementation. Requirements track the live implementation, verification,
documentation, and evidence state.

Task files are the default approval and execution record. Public user
documentation and implementation/maintainer documentation describe current
behavior and normally remain consistent with committed code. A user may
explicitly request a different commit order.

Progress notes are allowed in specifications when they briefly clarify a
meaningful difference between the target and implementation. They point to
requirements rather than reproducing detailed status.

User documentation may be drafted before implementation on a development
branch. Target-only text is marked `Not implemented` while under review and is
not published as current guidance by default. If proposed user-facing text
must remain durable before implementation, it stays with the specification.

## Goals

- Replace the four substantive guidance pages with one project-independent
  guide and one concise Crystal Lattice addendum.
- Introduce the default structure and file roles before abstract placement or
  workflow rules.
- Treat every illustrated file and directory as optional according to need.
- Explain how to write each document type, including concrete examples and
  observable results.
- Allow any package to own specifications for behavior it defines, including
  package-specific refinements of broader contracts.
- Keep shared plugin-authoring rules explicit without making them universal
  package rules.
- Make every documentation page discoverable from an appropriate entry point.
- Keep user documentation, developer documentation, specifications,
  requirements, tasks, and maintainer material distinguishable in plain
  language.
- Keep requirements limited to necessary, traceable approved outcomes and
  constraints; group variants proportionately and surface unspecified public
  behavior as a question instead of silently selecting it. Recommendations
  remain outside the completion contract until approved.
- Put that minimum requirement contract in always-loaded root guidance as well
  as the detailed guide and task-file guidance, with each layer expressing only
  the detail appropriate to its role.
- Keep primary evidence concise and directly related to requirement
  validation.
- Give agents practical guidance for choosing the lowest-cost reliable test
  boundary, identifying important crossings, avoiding brittle
  implementation/source assertions outside the required contract, and
  distinguishing decisive evidence from supporting checks.
- Put the strategic test-selection rules first in root guidance and route
  package/runtime-specific test mechanics to the nearest applicable guidance
  when they remain discoverable.
- Make completion reports emphasize decisive acceptance evidence rather than
  routine quality-check counts.
- Preserve scope, ownership, source-of-truth, validation, and publication
  boundaries when a compliant workflow is unavailable.
- Use requirements as the live traceability record.
- Keep the process proportional and avoid placeholder documentation.
- Provide a human-led contributor workflow in which every change and follow-up
  is planned before implementation.
- Help humans verify effective instruction delivery and review AI-produced
  specifications, task plans, automated evidence, documentation, and delivery
  readiness through understandable decisions and focused follow-up questions.
- Keep specification decisions independent from immediate change size and
  require current user-documentation updates for consumer-affecting behavior.
- Make ordinary changes understandable primarily through Git history.
- Verify that representative agents can apply the authored instructions
  through maintainer-owned behavioral evaluation while keeping model
  judgment separate from static and human evidence.
- Evaluate abstract rule understanding rather than merely checking literal
  words repeated by the guidance.
- Exercise requirement restraint and testing choices across supported
  reasoning-effort settings.
- Compare requirement quality across several small tasks and model/effort
  profiles before using one passing scenario as complete guidance evidence.

## Non-goals

- Requiring any project or package to create the complete illustrated
  documentation structure.
- Requiring every change to have a full product/technical/requirements set.
- Requiring mandatory lifecycle status inside every specification.
- Banning useful temporary progress notes from specifications.
- Publishing target-only user documentation as current behavior.
- Treating a specification as evidence of current implementation.
- Publishing maintainer specifications or task-guidance evaluation internals
  as ordinary user documentation.
- Duplicating the project-independent guide in the Crystal Lattice addendum.
- Reconstructing undocumented behavior across the repository solely to fill a
  target directory shape.
- Selecting one mandatory versioning format for major specification changes.
- Requiring `testing-strategy.md` for ordinary low-risk changes.
- Maximizing test count or requiring the same behavior to be tested at every
  layer.
- Treating routine formatting and lint checks as the main verification result.
- Moving all maintainer tooling as part of creating this approval package.
- Treating one model response or reviewer score as sole evidence that the
  standards are correct or human verified.

## Acceptance examples

### Documentation adapted to size

A small package updates one README because it already provides the complete
first-use path. Another package adds an index and one focused page. A
substantial feature uses separate specification, requirements, and testing
strategy files because the additional separation makes review easier. None of
the omitted files are created as placeholders.

### Package-specific UX specification

A frontend package may define a substantial platform-specific UX specification
that refines broader cross-package behavior. The package specification links
the broader specification, adds package-owned requirements, and does not
silently weaken shared behavior.

### Requirements restraint

While planning a requested feature, an agent identifies worthwhile telemetry,
hardening, and future configuration. It records them as risks, recommendations,
or follow-ups instead of silently adding them to the required completion state.
Only user-approved outcomes and constraints become requirements.

When implementation requires a choice about a public API, persisted data,
compatibility, security, privacy, or user-visible behavior, the agent records a
question unless that class of decision is already authorized. Easy-to-reverse
code does not make the public contract a local implementation choice. A
recommendation may explain the tradeoff but does not become a requirement or
implementation decision until approved.

Requirement-quality evaluation uses several small tasks from different project
types. The implementing agent maps generated requirements to the approved
semantic targets and identifies omissions, unsupported additions, duplication,
and effort-related expansion. A human reviews the concise interpreted baseline;
complete outputs remain available when a finding needs investigation.

### Balanced testing strategy

Tests assert exact values, structures, ordering, or internal calls only when
those details are required behavior or part of a public, persisted, or
interoperability contract. For example, a plugin that returns UI configuration
as JSON should not receive an exact-key snapshot merely because the object is
easy to compare. If behavior crosses plugin, backend, transport, and frontend
boundaries, at least one test reaches the important real crossing rather than
replacing it with mocks.

Existing coverage is evidence only when it proves the required behavior. When
it does not, the plan identifies focused evidence or records the gap.
Representative checks are preferred over exhaustive operation-by-state
combinations, and unresolved behavior is not turned into a test target.

### Early user-documentation draft

An agent drafts a configuration guide before implementation on a development
branch. Target-only sections are marked `Not implemented`. Before publication,
the implementation is verified and the temporary marker is removed. If the
draft must remain before implementation, it is kept with the specification.

### Concise verification report

After completing a feature, the agent reports the few tests that directly
prove the requested behavior and any important manual or unverified boundary.
Formatting, lint, and broad passing-test counts are grouped as supporting
checks rather than obscuring the acceptance evidence.

### Blocked generated-documentation workflow

An agent finds a defect in generated documentation and corrects the authored
source. If the approved generator is absent or fails, the agent leaves generated
output unchanged, reports the blocker and remaining regeneration action, and
does not claim that publication output was refreshed.

The scenario first runs against the pinned pre-change guidance. Candidate
wording is evaluated only after the baseline exposes the boundary failure in at
least one representative model run. The same seed, task prompt, fixture, and
assertions are then reused to compare concise and, only when needed, expanded
guidance variants.

### Human-led AI-assisted change

A contributor describes a desired change in ordinary freehand language and
asks an agent to research and brainstorm it. The human reviews the proposed
scope, specification decision, requirements, test boundaries, user
documentation effects, and implementation plan before authorizing work.

After implementation, the human asks what unit, integration, and end-to-end
tests ran, what each one demonstrated, what user documentation changed, and
what remains unverified. Repeatable checkpoints with machine-observable
results become automated tests; human checkpoints focus on perception,
exploration, product judgment, or a real environment automation does not
faithfully represent. Findings return through planning before implementation,
and delivery occurs only after explicit human authorization.
