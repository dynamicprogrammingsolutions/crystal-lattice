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

Requests, conversations, tasks, specifications, existing files, and review
comments can define required behavior without defining the terminology or
organization used in another maintained file.

1. Use source information to determine required behavior, then choose names and
   organization for the maintained file. Do not introduce a phrase as a
   maintained name merely because it appeared earlier.

   *Example:* A request for “gentler backoff” may mean two delayed retries; it
   does not establish `gentle_retry`.

2. When creating a specification, requirement, decision, source file, test, or
   documentation page from a task, preserve approved behavior and constraints
   without copying task-only grouping, ordering, or progress terminology.

   *Example:* A task may group work under “Follow-up group: journal
   conversion.” The specification describes persisted record migration without
   adopting the group label.

3. Existing wording is separate scope. If an edit encounters unexplained
   wording that may be internal and cleanup is unauthorized, make no change to
   that file until the user chooses removal, translation, or retention.
   Explain the reader concern, recommend one choice, and ask a focused
   question; do not silently decide.

   *Example:* A user guide may contain an old “Launch packet” heading. Treat
   its presence as evidence to investigate, not authorization to preserve it;
   pause the page and ask before editing.

4. Retain exact wording when it is required or established by the product,
   public interface, or relevant domain.

   *Example:* Documentation and tests retain an established `--dry-run` flag.

5. Otherwise explain or translate terminology into the behavior, component,
   condition, outcome, or relationship meaningful to the maintained file.

   *Example:* Developer documentation may describe a write-ahead journal. User
   documentation says that queued work survives a restart unless the storage
   mechanism is itself part of the public interface.

### Apply the rules by context

| Context | Rule |
|---|---|
| Task | May retain conversational wording when it is defined and the task remains understandable without the conversation. Reference another task by descriptive title and full relative path. |
| Specification | Use product, interface, and domain terms rather than task grouping or progress labels. Reference a task by title and path without appending a local number, stage, or nickname. Other record references use description, stable ID when useful, and link. |
| Requirements | State observable outcomes or constraints. Task organization, examples, quality descriptions, and implementation steps become requirements only when their observable meaning is required. Cross-record references use description, stable ID, and link. |
| Decisions | Name the material choice and tradeoff. Task references use title and path; other record references use description, stable ID, and link. |
| Source code and tests | Names describe behavior, interfaces, or domain concepts. A requirement ID supports traceability only when nearby text explains the behavior. Preserve established public names. |
| Developer documentation | Define specification terms and explain current implementation without requiring linked records. Links add detail. Generally omit requirement IDs; when needed, include description, ID, and link. |
| User documentation | Explain supported behavior and limitations in self-contained language. Developer links add optional detail. Generally omit task and requirement IDs. Pause the affected file and ask before changing internal-looking wording when cleanup is unauthorized. |
| Names and delivery records | Filenames, headings, generated labels, identifiers, test names, commit messages, and pull-request titles name behavior or components meaningful in their context. |

Reference examples:

- A requirement reference combines
  `Expired entries are excluded (CACHE-004)` with
  `specifications/cache/requirements.md#cache-004`.
- `# CACHE-004: expired entries are excluded` explains the requirement traced
  by a test assertion.

Write for the intended reader, keep tracking in its owning records, and
translate current limitations when users need them.

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
approved task already authorizes it. A direct request to create one does not by
itself approve the proposed ownership, scope, overlap, or file set. Unless an
active approved task already provides that authority, present why the
specification is useful, its proposed owning component or shared scope,
behavior boundary, smallest useful file set, and overlap with existing
specifications, then obtain approval before creating files. That approval must
be explicit. Do not ask twice when the active task already authorizes it.

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

### Write necessary, traceable requirements

Requirements are the minimum approved outcomes and constraints needed for the
target to be complete. Before adding one, ask:

> If this requirement were removed, would an explicit user need, approved
> quality target, preserved contract, or necessary consequence of the target
> remain unsatisfied?

A requirement belongs when it traces to the request, a preserved contract, a
necessary consequence, an approved policy, or an approved design or quality
decision. Other ideas remain supporting details, questions, recommendations,
or follow-ups.

When useful, distinguish behavioral outcomes, approved assessable qualities,
and approved solution constraints. Implementation, testing, documentation,
refactoring, and verification work stays in plans or evidence unless its
outcome is independently required.

Use one requirement per independently meaningful outcome. Group variants,
operations, boundaries, and examples without hiding an approved condition,
unless separate acceptance, ownership, or status adds value.

Ask before resolving unspecified public, persisted, compatibility, security,
privacy, or user-visible behavior unless that decision is authorized.
Do not invent fallback or error behavior for unspecified inputs.
Easy-to-reverse code does not make a public contract a local choice.
A recommendation may explain the tradeoff, but it stays outside requirements
and implementation until approved.

More analysis may discover more relevant considerations; it does not enlarge
the approved completion state.

Use stable identifiers when durable tracking helps. Keep implementation,
verification, and documentation states separate. A concise table can use:

```markdown
| ID | Requirement | Implementation | Verification | Documentation | Primary evidence |
|---|---|---|---|---|---|
| EVT-001 | External events have stable identifiers. | Implemented | Automated | Documented | `test_public_type` |
| EVT-002 | Internal checkpoints stay private. | In progress | Unverified | Pending | — |
```

Use the smallest direct evidence for each state. Record shared delivery
references once below the table; longer ID-keyed notes are exceptional.

## Plan testing around risks and boundaries

Use the least expensive test that proves the requirement without mocking away
the important boundary.

| Test level | Use it for |
|---|---|
| Unit or component | Local calculations, transformations, state transitions, and rendering behavior proved without another real component. |
| Integration | Contracts and failures that appear only when real components, storage, transports, processes, or adapters interact. |
| End-to-end, hosted, or native | Critical deployed paths or environments lower layers cannot represent faithfully. |
| Manual | Perception, exploration, product judgment, or a real environment for which reliable automation is impractical. |

Choose the layer from the failure that must be detected, not from a desire to
use every test type. Add integration coverage when an important requirement
crosses a real boundary. A mock that supplies or bypasses the claimed behavior
is not decisive evidence.

Cite existing coverage only when it actually proves preserved behavior.
Otherwise plan focused evidence or record the gap. Do not test unresolved
behavior.

Assert exact values, structures, ordering, markup, calls, or source identity
only when they are approved contract details. Otherwise test the observable
outcome and its minimum stable properties.

Avoid repeating the same assertion at every layer without a distinct
risk-based reason. Record important exclusions and remaining verification.

Create `testing-strategy.md` only when important crossings, expensive or manual
checks, credible alternative approaches, or durable exclusions need more
explanation.

After implementation, report the few tests or observations that directly
prove the requested outcome and state what remains unverified. Routine
formatting, lint, compilation, and broad test counts are supporting checks.

Manual verification is complete only when a human performs or confirms it; a
generated checklist remains a plan.

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