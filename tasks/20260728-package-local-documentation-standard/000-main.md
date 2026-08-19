# Package-Local Documentation and Specification Standard

Establish a repository-wide package-local documentation standard, extend the
existing documentation-site assembly pipeline, and migrate a bounded set of
ownership-clear documentation without turning the work into a project-wide
documentation rewrite or code archaeology exercise.

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Related Specification:
`maintainer/specifications/agent-evaluation-framework/index.md`

Requirements:
`maintainer/specifications/documentation-and-specification-standard/requirements.md`

## Requirements checklist

- [ ] User-facing documentation and specification guidance is split into
  reusable package-neutral standards and a concise Crystal Lattice repository
  policy that maps local paths, profiles, exceptions, and tooling.
- [ ] `maintainer/` provides a clear non-public home for specifications,
  evaluation tooling, and implementation material used to maintain standards
  and agent workflows.
- [ ] The repository defines a canonical package-local documentation structure
  and minimum documentation profiles for public packages, applications/services,
  small plugins, and internal packages.
- [ ] Package-local documentation is the source of truth, while
  `docs_site/prepared/` and `docs_site/dist/` remain generated outputs that must
  not be edited directly.
- [ ] Root `docs/` is reserved for repository-wide guidance, cross-package
  architecture, cross-package contracts, and documentation-site entry points.
- [ ] Root `AGENTS.md` contains concise documentation-routing and maintenance
  instructions and points to the full documentation and specification
  standards.
- [ ] Public/reusable packages have a clear README, package development entry
  point, documentation index, and user quickstart without requiring
  reconstructed long-form documentation.
- [ ] Small or implementation-only packages can use a reduced documentation
  profile, avoiding empty placeholder files and duplicated boilerplate.
- [ ] The standard defines distinct purposes and names for product
  specifications, technical specifications, requirements traceability, and
  architecture decision records.
- [ ] Specifications describe the intended target and may temporarily differ
  from implementation, while requirements track the live implementation,
  verification, and documentation state.
- [ ] Substantive feature work creates or updates its specification before
  implementation, with simple changes normally committed with the code or in
  the immediately preceding commit.
- [ ] Requirements use stable identifiers and can record implementation,
  verification, documentation, task, and delivery evidence without duplicating
  execution plans from `tasks/`.
- [ ] Public user documentation and implementation/maintainer documentation
  describe current behavior and do not become inconsistent with committed code.
- [ ] Important acceptance and contract tests can reference requirement
  identifiers, while ordinary low-level tests are not required to carry them.
- [ ] A maintainer-owned generic agent-evaluation kernel supports arbitrary
  programs, replaceable run environments, compatible state reuse, clean
  continuations, and concise/raw artifacts without hardcoding agent or
  evaluation semantics.
- [ ] The documentation-standard instructions have behavioral pytest consumers
  covering every `DOCGEN-*` and `DOCREP-*` requirement while preserving static
  and human verification as distinct evidence.
- [ ] Root `CONTRIBUTING.md` provides an easy-to-follow, risk-scaled
  AI-assisted development workflow with a clear distinction between human
  ownership, implementing-agent work, reviewing-agent work, and human approval.
- [ ] The contributor workflow uses a concise six-step structure, describes
  manual and AI work only where relevant, and includes short example prompts
  that rely on standing developer-message guidance instead of repeating it.
- [ ] Canonical and bundled `TASKS-v7` guidance is synchronized and explains
  how specifications, requirement IDs, task requirements, execution plans, and
  evidence relate without embedding the full contributor workflow.
- [ ] Task-guidance evaluation code, fixtures, documentation, and review
  tooling move from root shared-test locations into a coherent
  `maintainer/`-owned layout.
- [ ] The existing docs-site preparation pipeline supports explicitly
  registered package-local README and `docs/` sources.
- [ ] Package-local documentation changes trigger the documentation build
  workflow.
- [ ] Public documentation URLs affected by migration remain available through
  compatibility pages or redirects unless a breaking URL change is separately
  approved.
- [ ] A bounded set of existing pages is inspected, lightly verified, and
  either relocated, retained with rationale, or explicitly deferred.
- [ ] Migration does not require reconstructing undocumented behavior from
  large areas of unfamiliar code.
- [ ] The prepared site builds successfully, migrated links resolve, and the
  package assembly behavior has focused automated coverage.
- [ ] Deferred or uncertain legacy documentation is recorded in a concise
  migration inventory with likely ownership and rationale, without creating
  placeholder documentation.

## Specification and requirement mapping

The documentation meta-specification defines the documentation-system target.
The separate agent-evaluation specification defines its reusable framework.
Their requirements track live implementation and verification across this main
task and the subtasks:

| Workstream | Requirement IDs |
|---|---|
| Meta-specification bootstrap and task mapping | `DOCMETA-001`–`DOCMETA-003` |
| Generic reusable standards | `DOCGEN-001`–`DOCGEN-005` |
| Crystal Lattice repository policy and package profiles | `DOCREP-001`–`DOCREP-005` |
| Programmatic agent evaluation framework | `AEVAL-001`–`AEVAL-018` |
| Package documentation assembly, publication, navigation, and compatibility | `DOCPUB-001`–`DOCPUB-006` |
| Bounded Core/application/plugin/cross-package migration | `DOCMIG-001`–`DOCMIG-004` |
| Contributor workflow, task guidance, and maintainer-owned evaluation | `DOCFLOW-001`–`DOCFLOW-004` |
| Build, links, evidence, and final verification | `DOCVAL-001`–`DOCVAL-005` |

## Scope

This task establishes the structure and workflow first, migrates deliberately
limited documentation, and leaves a classified backlog for pages that would
require substantial reverse engineering.

The work includes:

1. A documented package-local documentation standard.
2. A concise documentation section in root `AGENTS.md`.
3. A root developer-documentation hub.
4. Target-state conventions for product specifications and technical
   specifications, live-state requirements tracking, and architecture
   decisions.
5. A practical root contributor guide for the recommended AI-assisted
   brainstorm-to-delivery workflow.
6. Aligned task-file guidance that keeps recurring developer-message content
   concise and synchronized with its bundled runtime copy.
7. Package profiles so small plugins are not forced to contain empty or
   duplicated documents.
8. An extension to the existing docs-site preparation script that assembles
   package-local sources into `docs_site/prepared/`.
9. A bounded first migration of existing documentation.
10. Verification for assembly behavior, links, navigation, and migrated claims.
11. A migration inventory for documentation deliberately left for future work.
12. A minimal programmatic agent-evaluation library whose first consumers
    verify the documentation-standard instructions.

## Non-goals

- Rewriting every README or long-form document.
- Making every package fully documented in this task.
- Creating empty `docs/` trees merely to satisfy a checklist.
- Auditing every historical task, plan, example, or design claim.
- Migrating `tasks/`, `plan/`, or `plans/` into package documentation.
- Turning all Markdown requirements into executable Gherkin.
- Requiring one implementation commit per requirement.
- Repeating the complete contributor workflow in every user prompt or in the
  task guidance appended to developer messages.
- Requiring every workflow step to contain both human and AI activity.
- Treating AI review as human approval or treating an AI-generated manual-test
  checklist as completed manual verification.
- Making all pre-existing MkDocs strict-mode warnings part of this task unless
  they are caused by the migration.
- Changing product behavior or public APIs.
- Reconstructing missing quickstarts for every plugin.
- Building a declarative evaluation language, benchmark service, leaderboard,
  or framework-owned reviewer/scoring model.

## Research and rationale

### Documentation taxonomy

The proposed structure borrows the useful distinction between tutorials,
how-to guides, explanation, and reference from Diátaxis, while treating those
as editorial roles rather than forcing every package to create all four
directory types immediately.

Reference:

- Diátaxis, "Start here":
  https://diataxis.fr/start-here/

### Specification-driven workflow

GitHub Spec Kit's `Spec -> Plan -> Tasks -> Implement` progression provides a
useful workflow model. This repository already has a substantial `tasks/`
system, so the standard adapts that progression instead of introducing another
parallel task mechanism:

- durable specifications describe intended behavior and design;
- requirements record durable outcomes and evidence;
- task files record execution planning, sequencing, dependencies, findings,
  and completion notes.

References:

- GitHub Spec Kit:
  https://github.github.com/spec-kit/index.html
- Spec Kit concepts:
  https://github.github.com/spec-kit/concepts/spec-persistence.html

### Requirements traceability

The requirements convention uses stable identifiers and explicit
implementation, verification, and documentation evidence. This adopts the
useful core of requirements-verification matrices without importing a
heavyweight systems-engineering process into every change.

Reference:

- NASA, "Appendix D: Requirements Verification Matrix":
  https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/

### Executable specifications

Important behavioral examples may be connected to executable tests. Cucumber
and Gherkin demonstrate the strongest form of plain-text executable
specification, but this task does not require Gherkin for ordinary library
code. It remains an optional tool for genuinely business-readable end-to-end
behavior.

References:

- Cucumber documentation:
  https://cucumber.io/docs/
- Gherkin reference:
  https://cucumber.io/docs/gherkin/reference/

### AI-assisted development and human review

The contributor workflow distinguishes persistent repository guidance from
task-specific prompts, keeps the human owner responsible for scope and
acceptance, and treats AI review as advisory.

Supporting references:

- OpenAI, "Introducing Codex":
  https://openai.com/index/introducing-codex/
- OpenAI, "Harness engineering":
  https://openai.com/index/harness-engineering/
- GitHub, "About customizing GitHub Copilot responses":
  https://docs.github.com/en/copilot/concepts/prompting/response-customization
- GitHub, "Responsible use of Copilot code review":
  https://docs.github.com/en/copilot/concepts/agents/code-review
- Google Engineering Practices, "What to look for in a code review":
  https://google.github.io/eng-practices/review/reviewer/looking-for.html
- Google Engineering Practices, "Small CLs":
  https://google.github.io/eng-practices/review/developer/small-cls.html
- NIST Secure Software Development Framework:
  https://csrc.nist.gov/pubs/sp/800/218/final

## Package documentation profiles

### Public package, SDK, application, or service

Required target structure:

```text
<package>/
├── README.md
├── AGENTS.md
└── docs/
    ├── index.md
    ├── quickstart.md
    ├── ...
    ├── development/
    │   ├── index.md
    │   └── ...
    └── reference/              # optional/generated
```

Examples include `core/python`, `application/python`, shared frontend SDK
packages, mobile and desktop applications, bridge services, cloud services,
and major provider packages.

### Small plugin or internal package

Minimum required structure:

```text
<package>/
└── README.md
```

The package may inherit development guidance from its nearest parent
`AGENTS.md`, such as `plugins/AGENTS.md`.

Add package-local `AGENTS.md` when development rules differ from the parent.
Add `docs/index.md` and `docs/quickstart.md` when README content is no longer
sufficient for package users.

### Shared documentation domain

A directory such as `plugins/docs/` remains the home for documentation shared
across many plugin packages. It is not treated as a distributable package
merely because it contains documentation.

## Documentation roles

| Artifact | Audience | Purpose |
|---|---|---|
| `README.md` | First-time package visitor | Shortest useful path: purpose, installation, basic use/build/test, and pointers |
| `AGENTS.md` | Agents and contributors | Development constraints, ownership boundaries, important files, verification commands, and documentation pointers |
| `docs/index.md` | Package users | Short documentation map that points to specific pages instead of reproducing them |
| `docs/quickstart.md` | Package users | Complete first-success workflow |
| `docs/*.md` | Package users | Guides, concepts, API behavior, configuration, recipes, and troubleshooting |
| `docs/development/index.md` | Package contributors | Map of architecture, testing, specifications, and maintenance documentation |
| `docs/development/*.md` | Package contributors | Internals, design constraints, development workflows, debugging, testing, and release behavior |
| `docs/reference/` | Package users or integrators | Generated API/type/reference material when useful |
| Root `docs/development/` | Repository contributors | Cross-repository standards and architecture |
| `docs_site/prepared/` | Build tooling | Generated site input only |

## Specification convention

For a substantive feature, use:

```text
<owning-package>/docs/development/specifications/<feature-slug>/
├── index.md
├── product-spec.md
├── technical-spec.md
├── requirements.md
└── decisions/                 # optional
    └── 0001-<decision-slug>.md
```

A small feature does not need all of these files. It may use a single
`index.md` or rely on its task file if no durable specification is needed.

### Product specification

`product-spec.md` defines what and why:

- problem and intended users;
- user-visible behavior and workflows;
- goals and non-goals;
- scope boundaries;
- compatibility expectations;
- acceptance examples;
- product questions and decisions.

It avoids implementation details unless they are externally visible
constraints.

### Technical specification

`technical-spec.md` defines how and under what constraints:

- ownership and affected components;
- architecture and data flow;
- public contracts, event shapes, schemas, and protocols;
- persistence and compatibility;
- failure behavior and recovery;
- security and privacy considerations;
- migration and rollout;
- verification strategy;
- material technical decisions.

### Requirements traceability

`requirements.md` provides normalized, traceable outcomes instead of repeating
the product and technical narratives. Unlike the specification, it tracks the
live state of implementation, verification, and documentation.

Recommended shape:

```markdown
# Requirements

Feature prefix: `EVT`

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| EVT-001 | Every external event has a stable type discriminator. | Implemented | Automated | Documented | `tests/...`, `docs/events.md`, task path, commit/PR |
| EVT-002 | Internal checkpoint payloads are not exposed over HTTP. | In progress | Unverified | Pending | task path |
```

Recommended implementation values:

- `Not started`
- `In progress`
- `Implemented`
- `Deferred`
- `Removed`

Recommended verification values:

- `Unverified`
- `Automated`
- `Human verified`
- `Not applicable`

Recommended documentation values:

- `Pending`
- `Documented`
- `Not applicable`

Requirement identifiers remain stable after acceptance and are not recycled.
Commit or PR evidence is added when delivery exists rather than guessed during
development.

### Relationship to task files

- Specifications describe the intended target behavior and design. They are not
  evidence that the implementation currently behaves that way.
- `requirements.md` records the live implementation, verification,
  documentation, and evidence state relative to that target.
- `tasks/` records execution planning, sequencing, dependencies, findings, and
  completion notes. Task files are the default location for approval of
  specification and requirement changes.
- A task links to relevant requirement identifiers.
- Requirements link to the implementing task and final delivery reference.
- Implementation steps are not copied into both artifacts.

### Tests against specifications

"Tests written against the specification" means:

- important acceptance tests reference requirement identifiers in names,
  docstrings, parametrization IDs, or nearby comments;
- machine-readable contracts such as schemas or API examples are validated
  directly when practical;
- documentation examples are sourced from tested examples when possible;
- Gherkin is optional for genuinely business-readable end-to-end behavior and
  is not mandatory for ordinary library code.

### Target and current-state model

The specification is the intended target. It may differ from current
implementation while work is in progress. The requirements record is the
authoritative tracking view for what is implemented, verified, and documented.

The default workflow is:

- **Small change:** update the specification first, then implement. Commit the
  specification with the code or in the immediately preceding commit so the
  target/current deviation is short and transparent.
- **New capability:** create the specification and requirements first. The
  requirements begin as not implemented and are updated as work completes.
- **Major change:** use the same simple workflow when it remains clear. Introduce
  an explicitly separate target version or change specification only when that
  materially improves readability.

Approval is tracked by the task file by default, not by a mandatory status
inside the specification. A particular specification may define additional
approval or status conventions when its domain needs them.

Public user documentation and implementation/maintainer documentation describe
current supported behavior. They may be edited first in the working tree, but
must be committed with the code change that makes their claims true.

Git history is the default explanation of ordinary specification evolution.
Avoid maintaining a second change log or elaborate status history for simple
changes.

Temporary progress tracking inside a specification or its index is optional.
Use it only when implementation is expected to span more than one commit and
the target/current difference would otherwise be confusing. The progress block
must link the active task and relevant requirement IDs, and should be removed
when all relevant requirements are verified.

For a major target that needs separate versions, use any clean structure that:

- identifies the active target;
- links the applicable requirements;
- prevents public/current documentation from presenting future behavior as
  available;
- preserves previous targets through Git history or explicit version links.

## Approved decision register

These decisions were approved by the user on July 28, 2026. They remain
explicit and inspectable so a later user-approved change can revise them
without silently rewriting the task's requirements or rationale.

| ID | Decision | Status | Rationale | Reconsider when |
|---|---|---|---|---|
| DOC-DEC-001 | Use package profiles instead of immediately requiring every manifest-backed package to contain all standard files. Major public packages use the full profile; small packages may remain README-only. | Approved | Avoids boilerplate, placeholders, and documentation reconstructed without active knowledge. | A package classification proves ambiguous or a stricter compliance requirement is requested. |
| DOC-DEC-002 | Do not publish `AGENTS.md` on the documentation site by default. Publish durable contributor guidance from `docs/development/`. | Approved | `AGENTS.md` is concise operational routing; durable explanation belongs in normal documentation. | Agent guidance becomes part of the intended public documentation product. |
| DOC-DEC-003 | Publish development documentation unless it contains security-sensitive or internal operational material. | Approved | Public development docs improve maintainability and package understanding. | A package has confidential or deployment-sensitive development information. |
| DOC-DEC-004 | Prefer `docs/index.md` as a package's public site landing page and use `README.md` as a fallback. | Approved | Avoids two competing package landing pages while preserving incremental adoption. | Site navigation or package publishing requirements need README to remain canonical. |
| DOC-DEC-005 | Use an explicit `docs_site/packages.toml` registry rather than blind manifest discovery. | Approved | Site identity, title, visibility, and ownership are policy decisions, not just filesystem facts. | Registry maintenance becomes materially burdensome or a reliable metadata source replaces it. |
| DOC-DEC-006 | Require the full product/technical/requirements specification set only for substantive, durable, or cross-package changes. | Approved | Keeps the process proportional and avoids unnecessary ceremony for small changes. | Small changes repeatedly expose missing durable design context. |
| DOC-DEC-007 | Normally attach requirement IDs to acceptance and contract tests, not every low-level test. | Approved | Preserves useful traceability without overwhelming implementation tests. | Regulatory, contractual, or safety requirements demand full traceability. |
| DOC-DEC-008 | Record a PR or completion commit for the feature; use per-requirement commit SHAs only when they add meaningful evidence. | Approved | File and test references are usually more stable and useful than manually maintained per-requirement commit lists. | Delivery or audit workflows require exact commit-level traceability. |
| DOC-DEC-009 | Specifications are living target-state documents. Material target or requirement changes require approval through the task workflow and remain visible in Git history. | Approved | The target should evolve with accepted design discoveries without being mistaken for evidence of current implementation. | A domain introduces separately baselined or externally approved specifications. |
| DOC-DEC-010 | Preserve moved public documentation URLs through compatibility pages or redirects for the initial migration. | Approved | Avoids breaking existing links while package-local ownership changes. | Redirect maintenance becomes permanent debt and a versioned URL-break policy is approved. |
| DOC-DEC-011 | Prefer generated site reference output with package-local mkdocstrings/JSDoc source directives; separately decide whether committed generated snapshots still provide value. | Approved | Separates authored inputs from generated output and reduces duplicate sources. | Offline snapshot use or release packaging requires committed generated Markdown. |
| DOC-DEC-012 | Require a successful normal docs build and no new warnings; global MkDocs strict-mode cleanup is separate unless migration fixes make strict mode practical. | Approved | Existing strict-mode warnings should not silently expand this migration into an unrelated cleanup project. | Strict mode already passes or remaining warnings are small and directly in scope. |
| DOC-DEC-013 | Use a concise six-step contributor workflow: shape, record/decompose, plan/approve, implement/verify, validate/review, and address findings/deliver. | Approved | A short workflow is easier to follow and can scale down for small changes. | Contributors repeatedly need a missing stage or the combined validation/review step becomes confusing. |
| DOC-DEC-014 | Define human owner, implementing agent, and reviewing agent once; identify only the relevant owner at each workflow step. | Approved | Not every stage requires both human and AI activity, and repeated role matrices would make the guide harder to scan. | Role ambiguity appears in real use or additional organizational roles become necessary. |
| DOC-DEC-015 | Keep example prompts short and task-specific. Standing rules belong in developer-message inputs, `AGENTS.md`, `TASKS-v7`, package docs, and specifications. | Approved | Developers should supply the current objective and new context without repeatedly copying repository rules. | A supported agent cannot reliably load the referenced standing guidance. |
| DOC-DEC-016 | Manual verification requires human performance or direct human confirmation; AI may prepare the checklist but cannot mark it complete. | Approved | Preserves the meaning of human acceptance evidence. | A separately approved trusted automation policy defines an equivalent non-human acceptance mechanism. |
| DOC-DEC-017 | AI review is advisory; final acceptance and delivery authorization remain human responsibilities. | Approved | AI review can supplement but not replace accountable human review. | Repository governance explicitly delegates approval to an automated policy. |
| DOC-DEC-018 | Keep `TASKS-v7` concise, establish a canonical authored source, and mechanically synchronize or verify the bundled developer-message copy. | Approved | The current repository and bundled copies differ, while the bundled copy is the runtime input. | Runtime loading changes to consume one canonical file directly. |
| DOC-DEC-019 | Treat the specification as the intended target, not as evidence of current implementation. Requirements track live implementation, verification, and documentation state. | Approved | Allows spec-first work without obscuring the current state. | A specific specification defines a stricter domain-specific tracking model. |
| DOC-DEC-020 | Track specification approval in task files by default rather than requiring lifecycle status inside every specification. | Approved | Approval already belongs to the planned and reviewable execution workflow; duplicate status adds maintenance burden. | A specification has external governance or an independently reviewed approval process. |
| DOC-DEC-021 | Keep simple specification evolution simple: update the spec first and normally commit it with the code or in the immediately preceding commit. | Approved | Git history makes target changes transparent without extra version/status machinery. | A major change spans enough commits that one target document becomes confusing. |
| DOC-DEC-022 | Public user docs and implementation/maintainer docs describe current behavior and must be committed together with the code that makes new claims true. | Approved | Readers and maintainers need reliable current-state documentation even while specifications describe a future target. | Versioned product documentation intentionally documents multiple released versions. |
| DOC-DEC-023 | Add temporary target-progress status only when work is expected to span multiple commits; link it to tasks and requirement IDs and remove it after all relevant requirements are verified. | Approved | Preserves clarity for long changes without turning every specification into a status dashboard. | Repeated long-running work needs a durable standardized roadmap format. |
| DOC-DEC-024 | Publish reusable package-neutral standards separately from Crystal Lattice repository policy. The repository layer extends and maps the generic rules without duplicating them. | Approved | Makes the core model reusable while keeping plugin, path, task-guidance, and docs-site rules explicit and easy to find. | The generic standard becomes an independently versioned product or the overlay no longer shares ownership and delivery. |
| DOC-DEC-025 | Use one meta-specification and requirements ledger for both output layers. | Approved | Generic and repository-specific outputs share one owner, approval path, delivery, and validation system. | The generic standard gains independent owners, releases, or multiple repository consumers. |
| DOC-DEC-026 | Use the simplified `maintainer/specifications/` path because the entire `maintainer/` domain is development-only; move standards-maintenance tooling such as task-guidance evaluation under the same domain through its owning subtask. | Approved | Avoids empty `maintainer/docs/development/` parent indexes while preserving a clear non-public maintenance boundary. | Maintainer content later needs a distinct user-documentation layer or publication profile. |
| DOC-DEC-027 | Build agent evaluation as a programmatic Python library rather than a declarative scenario language. | Approved | Ordinary Python and pytest keep programs flexible and readable while each run environment owns its runtime behavior. | Repeated consumers demonstrate a stable declarative subset with clear value. |
| DOC-DEC-028 | Keep `AgentEval.run()` minimal: name, arbitrary program callback, and optional run environment, parent run, workspace, and cache key. | Approved | Prevents prompt, guidance, tool-loop, reviewer, scoring, and presentation concepts from becoming mandatory kernel semantics. | A missing input recurs across independent consumers and cannot remain ordinary program/environment logic. |
| DOC-DEC-029 | Use a generic kernel with one broad `RunEnvironment` replacement seam; implement Crystal Lattice as the first rich environment with optional lower-level strategies. | Approved | Allows complete environment substitution while keeping tool-loop, snapshot, evidence, evaluation, and presentation customization close to the Crystal Lattice operations that use it. | Generic lifecycle and environment behavior no longer share a stable contract or several independent environment seams become necessary. |
| DOC-DEC-030 | Use pytest modules as the initial suites and runner, with real-model tests explicitly marked and excluded from normal defaults. | Approved | Reuses fixtures, parametrization, assertions, selection, and reporting without a second test language. | Saved-run operations, large resumable matrices, or non-test users justify a thin CLI. |
| DOC-DEC-031 | Use documentation-standard instruction tests as the first framework consumers; task-guidance migration remains owned by subtask 068. | Approved | Provides immediate requirement evidence while preserving the approved task-guidance scope and existing working evaluator. | Another consumer becomes a safer bootstrap or task-guidance dependencies require resequencing. |
| DOC-DEC-032 | Generate concise canonical artifacts for routine human/AI review and retain complete raw evidence separately. | Approved | Reviewers need useful outputs without multi-megabyte sessions and event streams, while diagnosis still needs provenance. | Storage, privacy, or external audit requirements demand a different retention model. |

## Open requirement questions

None at task creation. Any later answer that changes a required outcome or
constraint must be approved by the user and reflected in the requirements
checklist and execution plan.

## Current repository findings

### Existing assembly mechanism

- `docs_site/scripts/prepare_mkdocs_site.py` already assembles source material
  into ignored `docs_site/prepared/`.
- It currently copies root `docs/`, shared `plugins/docs/`, generated plugin
  README pages, and generated default configuration reference.
- `docs_site/mkdocs.yml` uses `prepared` as `docs_dir`.
- `docs_site/scripts/build_mkdocs_site.py` prepares, builds, and refreshes
  generated reference snapshots.
- `docs_site/scripts/refresh_reference_snapshots.py` currently writes generated
  Markdown snapshots back to root `docs/reference/`.

The implementation must extend this mechanism rather than create a competing
`docs_sites/` tree.

### Build workflow gap

`.github/workflows/deploy-static-sites.yml` currently watches:

- `landing_page/**`
- `docs/**`
- `plugins/docs/**`
- `docs_site/**`
- deployment files

It does not generally watch package-local README or `docs/` paths such as
`core/python/docs/**`, `application/python/docs/**`, or
`packages/*/docs/**`.

### Documentation ownership observations

- `docs/api/events.md` is primarily the public application event contract,
  owned by the application layer under `core/python/agent_app`, while it also
  points to terminal, bridge, and frontend consumers.
- `docs/api/core-sdk.md` is a large hand-written Core SDK guide and overlaps
  with `core/python/README.md` and generated API reference.
- `docs/plugins/application-config.md` describes application-level config and
  belongs with `application/python`.
- `docs/plugins/development.md` is explicitly described as the older/general
  shared plugin overview and belongs with `plugins/docs/`.
- `EXAMPLES.md` is generated by `scripts/generate_examples_md.py` from tested
  examples and has clear Core SDK ownership.
- `DEVELOPMENT.md` covers application and terminal development but currently
  sits at the repository root.
- `ARCHITECTURE.md` is cross-package architecture and is a likely root
  `docs/development/` page after bounded verification.
- `TYPES_AND_PROTOCOLS.md` contains both public contracts and development
  detail and may need relocation before any later split.
- `application/python/agent_terminal_app/server_endpoints_parity.md` is written
  as an active `NEW`/`EXISTING` plan and requires current-state classification.
- `docs/reference/tool-host-protocol.md` describes a cross-package Python/Node
  contract and needs an explicit contract owner before relocation.
- Mkdocstrings source directives live separately under
  `docs_site/source/reference/`, while generated snapshots live under
  `docs/reference/`.
- The OpenAI-compatible provider directive currently points at
  `plugins.openai_provider`, while the current first-party package is
  `reference_openai_compatible_provider`; this requires correction rather than
  a blind move.

## Proposed final source structure

```text
.
├── AGENTS.md
├── README.md
├── docs/
│   ├── index.md
│   ├── development/
│   │   ├── index.md
│   │   ├── standards/
│   │   │   ├── index.md
│   │   │   ├── documentation.md
│   │   │   └── specifications.md
│   │   ├── repository/
│   │   │   ├── index.md
│   │   │   ├── documentation.md
│   │   │   └── specifications.md
│   │   ├── specifications/
│   │   │   └── ...                         # cross-package targets only
│   │   └── architecture.md
│   └── reference/
│       └── ...                              # cross-package contracts only
│
├── core/python/
│   ├── README.md
│   ├── AGENTS.md
│   └── docs/
│       ├── index.md
│       ├── quickstart.md
│       ├── core-sdk.md
│       ├── events.md
│       ├── examples.md
│       ├── development/
│       │   ├── index.md
│       │   ├── architecture.md
│       │   ├── types-and-protocols.md
│       │   └── specifications/
│       └── reference/
│
├── application/python/
│   ├── README.md
│   ├── AGENTS.md
│   └── docs/
│       ├── index.md
│       ├── quickstart.md
│       ├── configuration.md
│       └── development/
│           ├── index.md
│           ├── terminal-and-http-runtime.md
│           └── specifications/
│
├── packages/<package-name>/
│   ├── README.md
│   ├── AGENTS.md
│   └── docs/
│       ├── index.md
│       ├── quickstart.md
│       ├── development/
│       └── reference/
│
├── plugins/
│   ├── AGENTS.md
│   ├── docs/
│   │   ├── index.md
│   │   └── ...
│   └── <plugin-name>/
│       ├── README.md
│       ├── AGENTS.md                        # only when package-specific
│       └── docs/                            # when README is insufficient
│
├── maintainer/
│   ├── README.md
│   ├── agent-evaluation/
│   │   ├── README.md
│   │   ├── pyproject.toml
│   │   ├── src/agent_eval/
│   │   ├── suites/
│   │   └── tests/
│   ├── specifications/
│   │   ├── agent-evaluation-framework/
│   │   └── documentation-and-specification-standard/
│   │       ├── index.md
│   │       ├── product-spec.md
│   │       ├── technical-spec.md
│   │       └── requirements.md
│   └── ...                                  # standards-maintenance tooling
│
└── docs_site/
    ├── README.md
    ├── mkdocs.yml
    ├── packages.toml
    ├── source/
    ├── scripts/
    ├── prepared/                            # generated, ignored
    │   ├── index.md
    │   ├── development/
    │   └── packages/
    │       ├── core-python/
    │       ├── application-python/
    │       ├── frontend-sdk/
    │       └── ...
    └── dist/                                # generated, ignored
```

## Migration inventory

### First-wave migration candidates

| Current page | Proposed owner/location | Verification boundary |
|---|---|---|
| `docs/api/events.md` | `core/python/docs/events.md` | Verify event names and external/internal distinction against `agent_app`, terminal server, frontend event types, and existing event tests. |
| `docs/api/core-sdk.md` | `core/python/docs/core-sdk.md` | Check imports, public method names, and examples already covered by core tests; do not rewrite the whole document. |
| `docs/plugins/application-config.md` | `application/python/docs/configuration.md` | Verify configuration keys and links against current config loading and default config. |
| `docs/plugins/development.md` | `plugins/docs/overview.md` | Preserve the general overview, update links to canonical shared plugin pages, and avoid duplicating detailed guides. |
| `DEVELOPMENT.md` | `docs/development/application-and-terminal.md` or `application/python/docs/development/terminal-and-http-runtime.md` | Decide whether it remains cross-package; spot-check referenced files and event terminology. |
| `EXAMPLES.md` | `core/python/docs/examples.md` | Change the generator output path and run existing example tests before regeneration. |

### Investigate and classify

| Current page | Likely destination | Required decision |
|---|---|---|
| `ARCHITECTURE.md` | `docs/development/architecture.md` | Cross-package ownership is clear, but major paths and architecture claims need a bounded spot-check. |
| `TYPES_AND_PROTOCOLS.md` | `core/python/docs/development/types-and-protocols.md` | Large document with both public contract and implementation material; may need a later split. |
| `application/python/agent_terminal_app/server_endpoints_parity.md` | `application/python/docs/development/specifications/http-api-parity/` or archive | Its `NEW`/`EXISTING` statuses may no longer reflect current endpoints. |
| `docs/reference/tool-host-protocol.md` | Root cross-package reference or `packages/tool-host-node/docs/protocol.md` | The protocol is shared by Python and Node; establish explicit ownership before moving it. |
| `docs/reference/agent_core/**` | `core/python/docs/reference/` or generated-only output | Normalize separate source directives and generated snapshots. |
| `docs/reference/providers/openai_provider.md` and directive | Owning provider package | Correct the stale import target before or during relocation. |

### Explicitly deferred

- `PROJECT_PLAN.md`
- Historical `plan/` and `plans/` documents
- Existing `tasks/`
- Bonjour implementation plans and summaries
- Deployment READMEs not touched by the package documentation pipeline
- Package READMEs that already provide sufficient usage information
- Missing long-form quickstarts for small plugins

## Subtasks

- [ ] `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- [ ] `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- [ ] `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`
- [ ] `tasks/20260728-package-local-documentation-standard/030-core-python-documentation-migration.md`
- [ ] `tasks/20260728-package-local-documentation-standard/040-application-and-plugin-documentation-migration.md`
- [ ] `tasks/20260728-package-local-documentation-standard/050-cross-package-and-reference-documentation-triage.md`
- [ ] `tasks/20260728-package-local-documentation-standard/060-navigation-compatibility-and-build-triggers.md`
- [ ] `tasks/20260728-package-local-documentation-standard/065-contributing-and-ai-assisted-development-workflow.md`
- [ ] `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- [ ] `tasks/20260728-package-local-documentation-standard/069-task-guidance-scope-and-decomposition.md`
- [ ] `tasks/20260728-package-local-documentation-standard/070-verification-and-deferred-migration-inventory.md`

## Execution plan

Status: Draft

This plan preserves the user-approved scope and decisions, but task creation
does not authorize implementation. Before execution, present this stored plan
and obtain explicit approval to begin.

The work is organized standards-first:

1. Subtask 010 creates the canonical documentation and specification standard
   plus agent routing.
2. Subtask 015 creates the minimal programmatic agent-evaluation library and
   uses the documentation-standard instructions as its first behavioral
   consumers. It can proceed in parallel with site assembly after 010.
   Remaining calibration, full-matrix execution, and framework refinements are
   explicitly non-blocking for 010 completion and for subtasks 020–070. Later
   guidance changes remain owned and evidenced by 015 without reopening
   completed downstream work unless they change an approved requirement.
3. Subtask 020 extends the existing site assembler and establishes package
   registration and focused tests.
4. Subtasks 030, 040, and 050 migrate or classify bounded documentation areas
   using the standard and assembly pipeline. They can proceed in parallel after
   010 and 020.
5. Subtask 060 updates navigation, compatibility paths, inbound links, and CI
   triggers after migration destinations are known.
6. Subtask 065 creates the concise contributor workflow after the terminology
   and artifact roles from 010 are established. It can proceed in parallel with
   most migration work.
7. Subtask 068 aligns and synchronizes `TASKS-v7` after the documentation
   standard and contributor workflow are defined. It may adopt the committed
   agent-evaluation framework while 015 continues non-blocking refinements, and
   it owns moving the existing task-guidance evaluator.
8. Subtask 069 uses the migrated evaluator to verify minimum sufficient
   requirements and coherent single-task/subtask decomposition. Guidance
   changes are baseline-first and preserve exact model/reasoning profiles.
9. Subtask 070 performs final verification after migration, contributor
   workflow, and task-guidance alignment are complete.

Existing content should be moved with minimal editorial changes. Verification
is bounded to claims, links, examples, and contracts directly touched by the
migration. If ownership or accuracy cannot be established without broad code
reconstruction, retain or defer the page with an explicit reason.

### Implementation decisions and open questions

The decisions in `## Approved decision register` are approved implementation
and process directions. They remain reviewable and may be changed later only
through an explicit user-approved update to this task and any affected
requirements or subtasks.

Subtask 015's remaining `AEVAL-017`/`AEVAL-020` work and calibration follow-ups
do not block 010, package-site assembly, migration, contributor workflow, task
guidance alignment, or final documentation verification. Each consuming
subtask uses the committed standards/framework state available when it starts
and records any material later integration follow-up explicitly.

There are no unresolved requirement questions at task creation.

Local reversible implementation choices not covered by the decision register
may be resolved during execution and recorded in `## Implementation Notes`.

### Documentation

Required new or updated documentation includes:

- `docs/development/index.md`
- `docs/development/standards/index.md`
- `docs/development/standards/documentation.md`
- `docs/development/standards/specifications.md`
- `docs/development/repository/index.md`
- `docs/development/repository/documentation.md`
- `docs/development/repository/specifications.md`
- `maintainer/README.md`
- `maintainer/specifications/documentation-and-specification-standard/*`
- `maintainer/specifications/agent-evaluation-framework/*`
- `maintainer/agent-evaluation/README.md`
- root `CONTRIBUTING.md`
- root `AGENTS.md`
- canonical and bundled `TASKS-v7` guidance plus synchronization/verification
  documentation where needed
- package-local `AGENTS.md`, `docs/index.md`, and `docs/quickstart.md` for the
  initial major packages where required by the approved profile
- `docs_site/README.md`
- migrated pages listed in the migration inventory
- compatibility pages or redirect configuration for moved public URLs
- a concise deferred migration inventory

### Task checklist

- [ ] 010: Establish documentation/specification standard and agent guidance.
- [ ] 015: Create the programmatic agent-evaluation library and documentation-standard consumers.
- [ ] 020: Extend package docs-site assembly and add focused tests.
- [ ] 030: Migrate and lightly verify Core Python documentation.
- [ ] 040: Migrate and lightly verify application and shared plugin documentation.
- [ ] 050: Triage cross-package architecture, protocol, parity-plan, and generated reference documentation.
- [ ] 060: Update navigation, compatibility paths, repository links, and build triggers.
- [ ] 065: Create the concise AI-assisted contributor workflow and prompt examples.
- [ ] 068: Align specifications/tasks guidance and synchronize canonical/bundled `TASKS-v7`.
- [ ] 069: Verify and refine task-guidance scope discipline and subtask decomposition.
- [ ] 070: Run final verification and record deferred migration inventory and evidence.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Canonical documentation structure and profiles | Root development documentation describes each artifact, package profile, ownership rule, and incremental adoption rule; initial package entry points conform without filler. |
| Agent routing and update behavior | Root `AGENTS.md` points to the full standard and clearly distinguishes README, user docs, development docs, specifications, root cross-package docs, and generated site output. |
| Specification and requirement conventions | Generic standard and repository policy define target product/technical specifications, live requirements, stable IDs, evidence fields, task-owned approval, current-doc behavior, package refinements, and proportional use. |
| Agent-evaluation framework | Deterministic package tests verify the minimal program/environment/run API, complete environment substitution, Crystal Lattice lower-layer customization, continuation, caching, workspace isolation, canonical/raw artifacts, and failure preservation without required evaluation-specific abstractions. |
| Documentation-standard behavioral evidence | Gated pytest consumers map every `DOCGEN-*` and `DOCREP-*` requirement to a neutral-seed continuation and preserve exact artifacts for separate human review. |
| AI-assisted contributor workflow | Root `CONTRIBUTING.md` presents the approved six-step, risk-scaled workflow; clearly separates human ownership, implementing-agent work, reviewing-agent work, manual verification, AI review, and delivery authorization; and includes concise example prompts. |
| Prompt/developer-message boundary | Contributor and agent guidance explains what belongs in standing developer-message inputs versus task prompts; prompt examples do not repeat generic repository rules. |
| Task-guidance alignment | Canonical and bundled v7 guidance match mechanically and describe specification/task relationships without duplicating the full contributor workflow. |
| Package-local source of truth | Site preparation tests and generated tree demonstrate package-local sources are copied without editing `docs_site/prepared/`; `AGENTS.md` is excluded by default. |
| Registered package assembly | Tests cover registry parsing, landing-page precedence/fallback, recursive docs copying, path errors, collisions, and link behavior. |
| Bounded migration | Every page listed in first-wave or investigate/classify tables has a recorded outcome, owner, verification performed, and compatibility treatment. |
| URL and navigation continuity | Old public paths resolve through compatibility pages/redirects; MkDocs nav and LLM sections point to canonical destinations. |
| Build integration | Package doc source paths trigger the docs workflow; preparation and normal MkDocs build complete without new warnings caused by this task. |
| Deferred work | A concise inventory records pages not migrated, likely owner, reason, and future trigger without inventing missing documentation. |

### Additional implementation verification

- Run focused unit tests for docs-site preparation.
- Run `python docs_site/scripts/prepare_mkdocs_site.py`.
- Inspect generated package destinations under `docs_site/prepared/packages/`.
- Run the normal MkDocs build from `docs_site/`.
- Compare build warnings with the pre-change baseline and confirm no new
  warnings originate from migrated pages.
- Check repository references to old paths and confirm each is updated or
  intentionally covered by compatibility behavior.
- Run existing example tests before regenerating or moving `EXAMPLES.md`.
- Run focused event/config/reference tests only where a migrated page's claims
  require them; do not expand into unrelated full-suite verification.
- Run deterministic task-guidance evaluation tests affected by the v7 changes.
- Run deterministic agent-evaluation package tests and the explicitly gated
  documentation-standard behavioral suite when enabled.
- Use the existing real-model task-guidance evaluation workflow for a
  representative review when practical, recording human inspection separately
  from deterministic acceptance evidence.
