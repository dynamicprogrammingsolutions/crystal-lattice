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