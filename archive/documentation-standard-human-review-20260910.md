# Historical documentation-standard human review

Status: Superseded on September 11, 2026

This page preserves the useful content of an uncommitted September 10, 2026
human-review guide for the former seven-page documentation standard. It is not
current guidance. The review led directly to the shorter two-page structure now
maintained under `docs/development/`.

Current sources:

- `docs/development/documentation.md`
- `docs/development/crystal-lattice-documentation.md`
- `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/20260912-guidance-rewrite-results.md`

## Review decision that was requested

The original human decision was:

> Are the authored standards, Crystal Lattice policy, and recurring root agent
> guidance clear, coherent, proportionate, easy to scan, and pleasant enough
> to use during ordinary development?

Objective structure and existing agent-behavior evidence were separated from
that editorial judgment. Requirements tables, task history, complete behavior
tests, model transcripts, and generated site output were intentionally
excluded from the focused bundle.

## Completed objective review

The review covered:

- the root `AGENTS.md` documentation section;
- `docs/development/index.md`;
- the former generic documentation and specification pages;
- the former Crystal Lattice repository documentation and specification
  pages;
- preserved behavioral evidence from documentation-standard subtask 015.

No behavior suite was rerun for this review.

| Check | Historical result |
|---|---|
| Local links | No missing target in the seven authored pages |
| Index coverage | Both general and repository-specific documentation areas were linked |
| Discoverability | Each detailed page was reachable within two links from the development index |
| Generic/project separation | Generic rule bodies contained no Crystal Lattice package names, paths, or tooling assumptions |
| Project mapping | Repository pages linked the generic rules and added local paths, profiles, exceptions, and tooling |
| Competing explanations | No high-similarity long paragraph was found across the four substantive pages |
| Specification/current model | Specification, requirements, task, and current-documentation responsibilities were stated consistently |
| Package ownership | Every package could own behavior and package-specific refinements |
| Proportionality | Placeholder files, mandatory full trees, and unnecessary specification files were rejected |
| Generated output | Maintained sources, generated files, blocked generation, and honest completion were distinguished |
| Editorial corrections | “without an clear package home” was corrected and one paragraph break was added |

This was not a repository-wide audit proving that every existing package
document already followed the rules.

## Historical size

| Material | Words |
|---|---:|
| Root `AGENTS.md` documentation section | 575 |
| Generic documentation page | 1,718 |
| Generic specification page | 1,305 |
| Crystal Lattice documentation page | 1,567 |
| Crystal Lattice specification page | 933 |
| Three indexes | 303 |
| Total authored review material | 6,401 |

The first complete Kindle package contained 31 files and 33,609 words. It was
rejected as too long and as mixing agent-verifiable checks with human
questions. A second nine-file focused package contained 7,906 words. That
bundle made the structure reviewable, but the subsequent human review still
found the guidance repetitive, scattered, terminology-heavy, and difficult to
navigate.

## Historical agent-behavior evidence

The preserved suite then contained 21 scenarios:

- the complete GLM-5.2 candidate matrix passed 18 of 21;
- a focused GPT-5.6-luna set passed seven of eight effective boundaries;
- no complete GPT cross-product was run.

Strong results included:

- package-owned refinements without moving behavior to a hard-coded preferred
  package;
- one maintained source with audience-appropriate summaries and indexed
  routes;
- proportional substantial-specification approval and file selection;
- separation of unimplemented targets from current user behavior;
- maintained/generated boundaries when generation failed;
- shared plugin guidance without turning one plugin's behavior into a common
  contract;
- exclusion of guidance-maintenance internals from package-user documentation;
- routed guidance reads before structural edits.

Retained limitations included:

- GLM Test 01 omitted a literal input/expected-output pair;
- GPT Test 02 omitted the exact remaining regeneration action;
- GLM Test 13 copied internal planning labels into a public README;
- Test 21's later terminology assertion had not been rerun.

The newer GLM-5.3 comparison and revised semantic scenarios are recorded in the
current September 12 results linked above.

## Human questions from the focused review

### Clarity

After one reading, could the reviewer explain the relationship among
specifications as targets, requirements as live state, tasks as approval and
execution, and user/developer documentation as current behavior?

### Coherence

Did the generic rules and Crystal Lattice-specific rules feel like one system,
or did repository mapping create a second conceptual model?

### Proportionality

Could small packages realistically stay README-only? Were indexes,
quickstarts, substantial specifications, and larger file layouts optional in
practice rather than only in wording?

### Scannability

Could a reader quickly find how to place a package-user page, select package or
shared ownership, create or update a specification, handle target/current
differences, and report blocked generation honestly?

### Recurring agent context

Was the 575-word root documentation section short enough for ordinary agent
context, and did it contain only the safety-critical summary needed before
routing to longer pages?

### Terminology and tone

Did terms such as “authoritative source,” “audience boundary,” “package scope,”
“current documentation,” and “target specification” feel natural, or overly
formal and agent-specific?

## Historical focused-bundle contents

The second bundle contained:

1. the human-review guide;
2. an exact root `AGENTS.md` documentation excerpt;
3. `docs/development/index.md`;
4. the former standards index and two standards pages;
5. the former repository index and two repository-policy pages.

Those seven guidance pages were replaced by the current short index and two
maintained guidance pages. The old paths now contain compatibility pointers.