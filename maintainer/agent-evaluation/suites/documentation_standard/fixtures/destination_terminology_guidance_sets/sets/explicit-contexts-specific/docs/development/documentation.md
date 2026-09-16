# Documentation and specification guide

Help a reader complete a task, understand current behavior, or make a durable
development decision. Start with the smallest structure that does that clearly.

## Start with the smallest useful structure

A repository, package, application, or component may use any subset of this
layout:

```text
README.md
AGENTS.md
docs/
├── index.md
├── quickstart.md
├── <user-topic>.md
├── development/
│   ├── index.md
│   ├── <developer-topic>.md
│   └── specifications/
│       └── <capability>/
│           ├── index.md
│           ├── product-spec.md
│           ├── technical-spec.md
│           ├── requirements.md
│           ├── testing-strategy.md
│           └── decisions/
└── reference/
```

Every entry is optional. This guide does not require empty directories or
placeholder pages.

- One existing README may be enough for a small package.
- One standalone page may be clearer than a new directory and index.
- An index and one focused page may be enough for a growing subject.
- A specification may be one file, or one file plus requirements.
- Separate product, technical, requirements, testing, and decision files help
  only when their separation makes substantial work easier to understand.

For a single-package repository, the repository root is the package location.

## Choose files by their role

Define each subject in one primary maintained place. Other pages may link to it
or summarize only what their readers need.

| File or page | Reader and purpose |
|---|---|
| `README.md` | Gives a first-time visitor the purpose, installation or setup, first successful use or build, and links to more detail. Keep it easy to scan. |
| `AGENTS.md` | Gives developers and automated contributors local instructions, important entry points, constraints, and verification commands. It is operational guidance, not a product manual or progress ledger. |
| `docs/index.md` | Maps a multi-page user-documentation area. Keep it short and link to focused pages instead of reproducing them. |
| `docs/quickstart.md` | Leads a new user through one complete successful path, including a concrete result when the behavior is observable. |
| User documentation | Explains available installation, configuration, concepts, workflows, recipes, and troubleshooting for someone using the package or product. |
| `docs/development/index.md` | Maps a multi-page developer area, including architecture, testing, specifications, and maintenance. |
| Developer documentation | Explains current internals, code entry points, architecture, debugging, testing, operations, and maintenance. |
| Specification | Describes intended behavior, constraints, and important design decisions. It may lead implementation. |
| `requirements.md` | Lists necessary outcomes and records their implementation, verification, and documentation state. |
| `testing-strategy.md` | Records important risks, selected test boundaries, manual or hosted checks, and deliberate exclusions when those choices need durable explanation. |
| Reference | Gives exact API, type, schema, command, or protocol details. It may be maintained by hand or generated from source declarations. |
| Decision record | Preserves one material choice among credible alternatives and the reason for it. |

Someone importing an SDK or implementing a supported extension is a package
user for that public interface, even if they are also a developer.

### README and quickstart

A README should answer, in order:

1. What is this?
2. Who should use it?
3. How do I install, run, import, or build it?
4. What is the shortest successful example?
5. Where do I go next?

Move detail into focused pages when the README becomes difficult to scan.

A quickstart is useful when first use needs more explanation than the README
can comfortably hold. Show the input, command, configuration, or code and the
result the user should observe. A later verification section does not replace a
clear result beside the first-use example.

### Index pages

Create an index when readers need a map across several pages. An index should
name the available subjects and help readers choose. It should not become a
second copy of those pages. If one page is already easy to find, an extra index
may add no value.

### User and developer documentation

User documentation teaches supported use without requiring readers to
understand implementation plans or repository maintenance. Developer
documentation can assume the reader is changing or operating the implementation
and may link to specifications, requirements, code, and tests.

Keep both aligned with available behavior. A specification can describe a
target that does not exist yet; ordinary user and developer documentation
should not present that target as available.

## Write pages readers can use

Requests and conversations describe outcomes; tasks record approved work;
specifications, requirements, and decisions define behavior and constraints;
code, tests, and documentation maintain the system.

Marked examples illustrate individual transfers, not a complete list.

1. Carry required behavior through records, but choose names and organization
   for the specification, requirement, decision, code, test, or documentation.
   Do not reuse wording merely because it appeared in an earlier record.

   *Example:* A request for “calmer retries” may mean two delayed attempts; it
   does not establish `calm_retry`.

2. When writing a specification, requirements, decisions, code, tests, or
   documentation from a task, keep the approved behavior and constraints
   without copying task-only grouping, ordering, or progress terminology.

   *Example:* A task may group work under “Follow-up workstream: storage
   migration.” The specification describes “Persisted record migration”
   without adopting the workstream label.

3. When changing existing code or documentation, review terminology and
   organization already present. Replace wording inherited from planning,
   tracking, or another record when it is not required or established for the
   people or interfaces that use it.

   *Example:* A user guide may contain an old “Release checkpoint” heading
   copied from progress tracking. When the page is updated, organize it around
   the supported capability instead.

4. Keep exact wording when it is required or established by the product,
   public interface, or relevant domain.

   *Example:* Documentation and tests retain an established `--dry-run` flag.

5. Otherwise explain or translate terminology into the behavior, component,
   condition, outcome, or relationship needed there.

   *Example:* Developer documentation may describe a write-ahead journal. User
   documentation says that queued work survives a restart unless the storage
   mechanism is itself part of the public interface.

### Apply the rules by context

| Context | Rule |
|---|---|
| Task | May retain conversational wording when defined and the task stands alone. Reference another task by title and full relative path. |
| Specification | Use product, interface, and domain terms, not task grouping or progress labels. Task references use title and path; other record references use description, ID, and link. |
| Requirements | State observable outcomes or constraints. Task organization, examples, quality descriptions, and implementation steps become requirements only when their observable meaning is required. Cross-record references use description, ID, and link. |
| Decisions | Name the material choice and tradeoff. Task references use title and path; other record references use description, ID, and link. |
| Source code and tests | Names describe behavior, interfaces, or domain concepts. A requirement ID supports traceability only when nearby text explains the behavior. Preserve established public names. |
| Developer documentation | Define specification terms and explain current implementation without requiring linked records. Links add detail. Generally omit requirement IDs; when needed, include description, ID, and link. |
| User documentation | Explain supported behavior and limitations in self-contained language. Developer links add detail. Remove inherited internal terms unless established for users. Generally omit task and requirement IDs. |
| Names and delivery records | Filenames, headings, generated labels, identifiers, test names, commit messages, and pull-request titles name behavior or components meaningful in their context. |

Reference examples:

- A task reference combines the descriptive title `Cache eviction` with the
  full relative path `../../tasks/cache-eviction.md`.
- A requirement reference combines
  `Expired entries are excluded (CACHE-004)` with
  `specifications/cache/requirements.md#cache-004`.
- `# CACHE-004: expired entries are excluded` explains the requirement traced
  by a test assertion.

Use verified examples when showing input and result clarifies installation,
configuration, an API, or recovery. Check them against current implementation
or tests.

Keep tracking in its owning records and translate current limitations when
users need them.

## Specifications, requirements, and tasks

These records answer different questions:

| Record | Question it answers |
|---|---|
| Specification | What behavior and design are we trying to establish? |
| Requirements | Which necessary outcomes currently exist, are verified, and are documented? |
| Task | What was approved, how will the work proceed, and what happened during execution? |
| User and developer documentation | What can readers use or maintain now? |

### When a specification helps

A durable specification is useful when a change introduces behavior or
decisions that future work must understand, such as:

- a public API, schema, protocol, or compatibility promise;
- persisted data or migration behavior;
- security, privacy, accessibility, concurrency, or failure handling;
- a user workflow with several related outcomes;
- coordination across independently maintained components;
- a material choice likely to be revisited.

Before creating a substantial new specification, check whether an active
approved task already authorizes it. If not, present why the specification is
useful, its proposed owning component or shared scope, behavior boundary,
smallest useful file set, and overlap with existing specifications, then obtain
approval before creating files. Existing task authorization is sufficient; do
not ask twice.

A straightforward local fix may need only its task, code, tests, and affected
documentation. Do not create a specification merely because the file layout
shows one.

Put a specification with the component that defines the behavior. A component
may define behavior consumed by several others. Use a shared location when
independently maintained components must coordinate and no single component
defines the complete behavior.

A package-specific specification may refine broader behavior by adding
platform, integration, or UX requirements. It should link the broader
specification and should not silently weaken it.

Specifications describe targets and may be updated before implementation.
Git history is normally enough to show ordinary changes. Use a separate target
version only when one evolving specification would be confusing.

Requirements are the detailed progress record. A specification may contain a
short implementation note when the difference between target and implementation
would otherwise confuse readers. Point to the relevant requirements instead of
copying their status table, and remove the note when it is no longer useful.

User documentation may be drafted before implementation on a development
branch. Mark target-only sections `Not implemented` while reviewing them.
Remove the marker only after the behavior exists and the text is verified.
Such sections should not reach published current documentation by default. If
proposed user-facing text must remain durable before implementation, keep it
with the specification.

### Write requirements as completion outcomes

A requirement states one necessary outcome or constraint. If it can fail while
the approved work is still complete, it is not a requirement.

Do not turn implementation steps, test-writing tasks, documentation tasks,
possible refactors, speculative hardening, or low-priority improvements into
requirements unless their resulting outcome was approved as necessary. Keep
useful discoveries as supporting details, questions, recommendations, or
follow-ups. More analysis may identify more possibilities; it does not enlarge
the approved completion state.

Use stable identifiers when requirements need durable tracking. Keep
implementation, verification, and documentation states separate. A concise
table can use:

```markdown
| ID | Requirement | Implementation | Verification | Documentation | Primary evidence |
|---|---|---|---|---|---|
| EVT-001 | External events have stable type identifiers. | Implemented | Automated | Documented | `tests/test_events.py::test_public_type` |
| EVT-002 | Internal checkpoints are not exposed publicly. | In progress | Unverified | Pending | — |
```

The primary evidence is the smallest direct reference supporting the state:
usually one focused test, one human confirmation, or one documentation page.
Record shared task, pull-request, or commit references once below the table
instead of repeating them in every row. Use a separate note keyed by
requirement ID only when a concise cell cannot explain important evidence.

A task owns approval, execution steps, findings, and completion notes. Link it
to requirements rather than copying the specification or turning the
requirements file into a second plan.

## Plan testing around risks and boundaries

Use the least expensive test that proves the requirement without mocking away
the important boundary.

| Test level | Use it for |
|---|---|
| Unit or component | Local calculations, transformations, state transitions, and rendering behavior that can be proved without another real component. |
| Integration | Contracts and failures that appear only when real components, storage, transports, processes, or adapters interact. |
| End-to-end, hosted, or native | A critical deployed path or environment that lower layers cannot represent faithfully. |
| Manual | Perception, exploration, product judgment, or a real environment for which reliable automation is not practical. |

Choose the layer from the failure you need to detect, not from a desire to use
every test type. Add integration coverage when an important requirement crosses
a real boundary. Do not substitute a mocked unit test that bypasses the
interaction being claimed.

Assert exact values, structures, ordering, or internal calls only when those
details are required behavior or part of a public, persisted, or
interoperability contract. Otherwise test the observable outcome and the
minimum stable properties needed to prove it. Avoid repeating the same
assertion at every layer without a distinct risk-based reason.

Record important exclusions. For example, say when a hosted test is omitted
because deterministic contract and local integration coverage already prove
the requirement, or when a manual check remains necessary because automation
cannot represent the visual result.

Create `testing-strategy.md` only when these choices deserve a durable record:
important layer crossings, expensive or manual checks, credible alternative
approaches, or exclusions that future work might otherwise reverse. A compact
strategy can contain:

```text
Behaviors and risks
Selected test boundary for each
Hosted, native, or manual checks
Tests intentionally omitted and why
Remaining verification
```

After implementation, report the few tests or observations that directly prove
the requested outcome and state what remains unverified. Formatting, lint,
compilation, and broad passing-test counts are supporting quality checks; group
or omit them unless they materially affect acceptance.

Manual verification is complete only when a human performs or directly
confirms it. An automated or AI-generated checklist is still a plan.

## Place, link, and generate documentation

Keep focused pages reachable from a nearby README or index.

Move a maintained page instead of copying it into two editable locations.
Update inbound links and preserve published addresses through the project's
normal compatibility mechanism. Verify the claims and examples touched by the
move; do not turn relocation into a reconstruction of unfamiliar behavior.

Generated documentation has a maintained source or generator. Change that
source, then run the normal generator when it is in scope. If generation is
unavailable or fails, leave the generated file unchanged, report what remains,
and do not claim it was refreshed.

Apply this guide as documentation is created or touched. Existing variations
do not require a mass rewrite, and a blocked workflow does not authorize a
competing source, weaker validation, or a broader task.