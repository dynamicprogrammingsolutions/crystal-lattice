# Agent-behavior verification

## Purpose

These tests verify that supported agents understand and apply the authored
documentation and specification guidance when performing ordinary repository
work.

They test agents as consumers of the guidance. They do not ask an agent to
write, summarize, or restate the standard being evaluated.

Latest comparison:

- [September 14, 2026 guidance follow-up results](20260914-guidance-followup-results.md)
- [September 12, 2026 guidance rewrite results](20260912-guidance-rewrite-results.md)
- [September 15, 2026 example-backed terminology results](20260915-example-backed-terminology-results.md)

Several scenarios deliberately create boundary pressure. The agent may have
internal context unavailable to the destination audience, receive a request
that names generated output, be asked to document an approved but unimplemented
target, or encounter an unavailable compliant workflow. The evaluation checks
whether document, audience, ownership, source-of-truth, validation, and
completion-honesty boundaries survive that pressure.

The evaluation pattern follows the validated task-guidance tests:

1. Prepare a realistic repository state.
2. Deliver the exact candidate `AGENTS.md` files and routed documentation
   through the normal agent instruction and filesystem mechanisms.
3. Give the agent a short task resembling a human request.
4. Let the agent inspect and modify the repository normally.
5. Assert on changed files, file contents, tool behavior, provenance, and the
   final response.
6. Prepare separate semantic-assessment and human-review results.

User prompts do not repeat the rules under test. If a prompt explains where
documentation belongs or which files to create, the evaluation cannot show
that the authored guidance caused that behavior.

## Static and behavioral verification

Some requirements combine properties of the authored standard with behavior
expected from agents.

Static verification checks the authored files directly, including:

- the project-independent page contains no Crystal Lattice paths or package
  names;
- word budgets, required links, and compatibility pointers are valid;
- project-specific rules remain in the Crystal Lattice addendum;
- generated output is not edited as a maintained source.

Behavioral verification checks whether an agent applies those rules to a real
task. A model is not asked to generate package-neutral guidance merely to prove
that the guidance itself is package-neutral.

## Traceability convention

Each test page shows:

```text
requirement
  -> target meta-specification
    -> authored guidance page
      -> behavioral assertion
```

Links use source line ranges for quick review. Relevant source sentences are
also copied beside the links so a reviewer can understand the test without
opening every file. Those excerpts are non-normative review aids; the linked
source remains authoritative and must be consulted when wording changes.
Changes to a linked requirement, specification, or guidance passage must update
the affected line range, copied excerpt, and behavioral assertion in the same
work.

Seed pages use the `seed-<number>-<name>.md` convention. Test pages use
two-digit numbers such as `01-<name>.md`. These names distinguish reusable
conversation/setup state from behavioral assertions without adopting the
three-digit task-file convention.

## Common setup

### Scenario-family seeds

A seed is a narrow, concrete factual investigation for a family of closely
related branch tasks. It is not a general repository survey.

The seed should:

- name the package, issue, task, or contract being investigated;
- ask only for facts needed by its branch tasks;
- be simple enough for the inexpensive subject model to complete quickly;
- avoid ownership, file-layout, workflow, or approval decisions controlled by the
  candidate guidance;
- omit candidate guidance;
- support multiple clean continuation prompts with small behavioral
  differences;
- remain reusable while candidate guidance revisions or delivery mechanisms
  change.

Most seeds are read-only investigations. A seed may instead establish a
tightly constrained completed base operation when the consumer scenario is a
follow-up task. Such a seed defines an exact mutation allowlist, verifies its
result, and still excludes the candidate guidance.

Current seeds:

| Seed | Narrow investigation | Current branches |
|---|---|---|
| [Seed 01](seed-01-js-single-file-tool-documentation.md) | Compare one plugin README with its code and shared Node-tool facts | Tests [01](01-small-package-documentation.md), [02](02-generated-output-correction.md), [16](16-failed-generated-refresh.md), [18](18-shared-plugin-authoring-boundary.md), and [28](28-small-package-proportionate-documentation.md) |
| [Seed 02](seed-02-report-export-row-limit.md) | Inspect one approved row-limit task and its current spec/code/test/doc state | Tests [03](03-target-specification-workflow.md), [07](07-approved-task-specification-only.md), [08](08-approved-specification-implementation.md), [15](15-premature-current-documentation.md), and [29](29-early-user-documentation-is-explicit.md) |
| [Seed 03](seed-03-mobile-composer-refinement.md) | Inspect one portable contract, mobile package, and approved UX task | Test [04](04-package-owned-refinement.md) |
| [Seed 04](seed-04-event-retry-documentation.md) | Compare implemented retry, target-only replay, user docs, and link paths | Tests [05](05-normative-owner-and-discoverability.md), [17](17-public-package-profile.md), [19](19-apply-versus-maintain-boundary.md), [20](20-routed-guidance-reading.md), and [27](27-routed-current-guidance.md) |
| [Seed 05](seed-05-batch-sync-design.md) | Inspect one package and related persistence/transport contracts | Tests [06](06-substantial-specification-approval.md), [09](09-task-authorized-new-specification.md), [21](21-explicit-specification-layout-override.md), [26](26-explicit-optional-layout.md), and [30](30-source-terms-in-specification-records.md) |
| [Seed 06](seed-06-existing-contract-bugfix.md) | Reproduce one public bug against an already-correct target contract | Test [10](10-bug-fix-with-existing-specification.md) |
| [Seed 07](seed-07-local-bugfix.md) | Reproduce one internal race with no durable public contract | Test [11](11-local-bugfix-without-durable-specification.md) |
| [Seed 08](seed-08-completed-small-implementation.md) | Complete one code/test-only change whose target already exists | Test [12](12-documentation-follow-up-after-implementation.md) |
| [Seed 09](seed-09-partial-major-change.md) | Inspect one approved partially implemented multi-commit target | Test [13](13-partial-major-change.md) |
| [Seed 10](seed-10-requirement-scope.md) | Distinguish approved batch-enqueue outcomes from explicitly unapproved ideas | Test [22](22-requirement-scope-restraint.md) at three reasoning efforts |
| [Seed 11](seed-11-testing-strategy.md) | Distinguish contracted option behavior, implementation detail, and delivery boundaries | Tests [23](23-testing-without-overspecification.md) and [24](24-testing-important-layer-crossing.md) |
| [Seed 12](seed-12-status-label-naming.md) | Inspect an established status API and a pending behavior whose public function name is unspecified | Test [31](31-source-terms-in-code-and-tests.md) |

Each seed page owns its exact fixture, prompt, request profile, assertions,
cache identity, provenance, and current/planned branches.

### Candidate guidance overlay

Before a scenario request begins, its clean continuation workspace receives
the exact current candidate guidance needed by the normal routing chain:

```text
AGENTS.md
docs/development/index.md
docs/development/documentation.md
docs/development/crystal-lattice-documentation.md
```

Package- or shared-domain scenarios additionally receive the exact applicable
nearest `AGENTS.md`, such as:

```text
plugins/AGENTS.md
plugins/docs/AGENTS.md
```

The setup records path, content hash, and overlay source for every candidate
file. The request artifacts must prove that the intended `AGENTS.md` revision
was delivered and that routed pages were available. The user prompt contains
only the ordinary task.

Candidate guidance hashes are branch fingerprints, not seed-cache
fingerprints. This allows one factual investigation to be reused when comparing
guidance revisions, AGENTS compilation, configuration injection, plugins, or
skills.

Maintainer specifications are not supplied for ordinary application of the
rules. They are relevant only to work maintaining the guidance.

Test 27 uses a routing-only variation of this overlay. It injects applicable
AGENTS content but leaves the two guidance pages to be read from their normal
workspace paths, so the test can observe whether routing instructions were
followed before editing. Legacy Test 20 retains the former four-page route only
for the direct pre/post comparison.

### Execution controls

Each scenario defines:

- allowed mutation paths;
- mutation-call budget;
- request/tool-loop limits;
- whether code changes are permitted;
- objective assertions;
- semantic-assessment input;
- human-review presentation.

Read-only repository investigation is not constrained beyond ordinary request
limits. Unexpected writes fail the scenario.

Boundary-pressure scenarios additionally define:

- the tempting boundary-breaking action;
- the compliant safe partial result;
- the blocker or audience context that must be reported or translated;
- prohibited claims of completion;
- whether a boundary-changing workaround requires user approval.

## Baseline-first guidance comparison

The direct previous/new comparison uses the exact committed `develop` guidance
preceding the rewrite:

```text
f81f36326b58268297ba59c1cacbcda604257c27
```

The earlier `3a62b6fc` baseline remains available for historical calibration.
The `develop` source uses the former guidance paths; the `candidate` source
uses the two current guidance pages. Every comparison preserves the same
guidance-neutral seed, task prompt, fixture, assertions, and model profile.

A candidate is improvement evidence only after representative baseline
artifacts show the targeted undesirable behavior. A case that always passes may
remain a robustness test but does not justify more guidance. Candidate wording
starts with the shortest general rule; longer wording or examples are tried
only when paired results show the concise rule is insufficient. Prompts and
assertions are not weakened between variants.

Baseline files are restored only in isolated evaluation workspaces or through
an explicit guidance-source overlay. The uncommitted main-worktree draft does
not need to be reverted.

### Evidence separation

Deterministic assertions operate on repository state and explicit provenance.

An optional assessment model receives only a scenario-owned projection:

- requirement IDs;
- exact task prompt;
- candidate guidance hashes;
- relevant original and generated files;
- changed paths;
- mechanical assertion results;
- final assistant response.

It does not receive the complete event stream or unrelated repository context.

Human review receives a separate compact presentation with focused questions.
AI assessment is supporting evidence and does not satisfy human verification.

## Consumer summary

| Test | Seed | Ordinary branch task | Primary coverage |
|---|---|---|---|
| [Small-package documentation](01-small-package-documentation.md) | Seed 01 | Legacy-only README mutation restriction | Superseded by Test 28 |
| [Generated-output correction](02-generated-output-correction.md) | Seed 01 | Fix a reported typo in a branch-specific prepared page | `DOCGEN-001`, `DOCGEN-007`, `DOCREP-006`, `DOCVAL-007`–`DOCVAL-008` |
| [Target specification workflow](03-target-specification-workflow.md) | Seed 02 | Implement an approved small capability | `DOCGEN-002` |
| [Package-owned refinement](04-package-owned-refinement.md) | Seed 03 | Complete approved mobile-only specification work | `DOCGEN-003` |
| [Normative owner and discoverability](05-normative-owner-and-discoverability.md) | Seed 04 | Make implemented retry behavior easy for users to find without leaking internal target context | `DOCGEN-004`, `DOCGEN-006`, `DOCREP-006`, `DOCVAL-007`–`DOCVAL-008` |
| [Substantial specification approval](06-substantial-specification-approval.md) | Seed 05 | Request a substantial durable specification without prior authorization | `DOCGEN-005`, `DOCVAL-008` |
| [Approved task: specification only](07-approved-task-specification-only.md) | Seed 02 | Prepare an approved target and pending requirements without implementation | `DOCGEN-002`, `DOCVAL-008` |
| [Implement prepared specification](08-approved-specification-implementation.md) | Test 07 continuation | Implement, verify, document, and complete live tracking | `DOCGEN-002` |
| [Task-authorized new specification](09-task-authorized-new-specification.md) | Seed 05 | Create a substantial package specification without duplicate approval | `DOCGEN-002`, `DOCGEN-003`, `DOCGEN-005` |
| [Bug fix with existing specification](10-bug-fix-with-existing-specification.md) | Seed 06 | Fix implementation against an already-correct target | `DOCGEN-002` |
| [Local bug fix without durable specification](11-local-bugfix-without-durable-specification.md) | Seed 07 | Keep an internal bug fix proportional and code/test-local | `DOCGEN-002`, `DOCGEN-005` |
| [Documentation follow-up](12-documentation-follow-up-after-implementation.md) | Seed 08 | Finish live tracking and current docs after code/tests | `DOCGEN-002`, `DOCGEN-004` |
| [Partial major change](13-partial-major-change.md) | Seed 09 | Implement one phase while preserving honest partial state and audience boundaries | `DOCGEN-002`, `DOCGEN-006`, `DOCREP-006`, `DOCVAL-007`–`DOCVAL-008` |
| [Portable contract owner](14-portable-contract-owner.md) | Seed 03 | Move clarified portable behavior to the shared contract owner | `DOCGEN-003` |
| [Premature current documentation](15-premature-current-documentation.md) | Seed 02 | Legacy-only prohibition on every early user-doc edit | Superseded by Test 29 |
| [Failed generated refresh](16-failed-generated-refresh.md) | Seed 01 | Report a prepared-page defect when the approved generator exists but fails | `DOCGEN-007`, `DOCREP-006`, `DOCVAL-007`–`DOCVAL-008` |
| [Public package profile](17-public-package-profile.md) | Seed 04 | Legacy-only full-profile requirement | Superseded by optional structure guidance |
| [Shared plugin-authoring boundary](18-shared-plugin-authoring-boundary.md) | Seed 01 | Improve reusable Node-tool guidance and one plugin's usage docs | `DOCREP-002` |
| [Apply versus maintain boundary](19-apply-versus-maintain-boundary.md) | Seed 04 | Ask a package README to expose standards-maintenance and evaluation provenance | `DOCREP-005`–`DOCREP-006`, `DOCVAL-007` |
| [Routed guidance reading](20-routed-guidance-reading.md) | Seed 04 | Legacy-only four-page route | Superseded by Test 27 |
| [Explicit specification layout and terminology](21-explicit-specification-layout-override.md) | Seed 05 | Legacy-only layout plus literal terminology assertion | Superseded by Test 26 |
| [Requirement-scope restraint](22-requirement-scope-restraint.md) | Seed 10 | Create approved requirements without promoting later ideas | `DOCGUIDE-005`, `DOCVAL-010` |
| [Testing without overspecification](23-testing-without-overspecification.md) | Seed 11 | Plan focused local tests without freezing implementation details | `DOCGUIDE-006`, `DOCVAL-010` |
| [Testing an important crossing](24-testing-important-layer-crossing.md) | Seed 11 | Plan real integration coverage across plugin, endpoint, and frontend adapter | `DOCGUIDE-006`, `DOCVAL-010` |
| [Focused verification report](25-focused-verification-report.md) | Seed 08 | Report decisive evidence and remaining work concisely | `DOCGUIDE-006`, `DOCVAL-010` |
| [Explicit optional layout](26-explicit-optional-layout.md) | Seed 05 | Honor one approved `decisions.md` without requiring a full tree | `DOCGUIDE-002`, `DOCLOCAL-001`, `DOCVAL-010` |
| [Routed current guidance](27-routed-current-guidance.md) | Seed 04 | Read the two current guidance pages before editing | `DOCAGENT-001`, `DOCLOCAL-001`, `DOCVAL-010` |
| [Proportionate small-package documentation](28-small-package-proportionate-documentation.md) | Seed 01 | Improve a small package without requiring README-only or creating filler | `DOCGUIDE-002`–`DOCGUIDE-003`, `DOCVAL-010` |
| [Explicit early user documentation](29-early-user-documentation-is-explicit.md) | Seed 02 | Permit only clearly marked branch-only target documentation | `DOCGUIDE-004`, `DOCVAL-010` |
| [Source terms in specification records](30-source-terms-in-specification-records.md) | Seed 05 | Create an approved specification while source-local task, sequence, and evaluative wording is present | `DOCGUIDE-007`–`DOCGUIDE-008`, `DOCVAL-011` |
| [Source terms in code and tests](31-source-terms-in-code-and-tests.md) | Seed 12 | Implement a pending API while choosing source, test, evidence, and developer-documentation terminology | `DOCGUIDE-007`–`DOCGUIDE-008`, `DOCVAL-011` |

## Execution groups

The direct comparison runs all legacy Tests 01–21 against `develop` and
`candidate`. Tests 01, 15, 17, 20, and 21 are reported as obsolete for the new
target but remain executable so their old/new behavior can be inspected.

The revised suite excludes those five tests and adds Tests 22–29. Test 22 has
three parametrized branches for low, high, and max reasoning effort.

- **Revised routine:** retained routine Tests 02–07, 10, 11, 13, and 18, plus
  Tests 22–25 and 28–29.
- **Revised extended:** retained Tests 08, 09, 12, 14, 16, and 19, plus Tests
  26–27 and 30–31. Tests 30–31 each have three source-wording variants.

All GLM runs target `glm-5.3-flash:cloud`. Model availability is checked before
execution and a resolution failure is reported rather than silently
substituting another model. Focused source-wording comparisons run GLM and GPT
at low, high, and max reasoning effort as defined by their scenario plan.

## Cross-test invariants

Every implemented test must verify:

- its narrow parent seed had no candidate guidance and only its declared seed
  mutations;
- the continuation used a fresh workspace;
- parent snapshot and artifacts were not modified;
- exact candidate guidance hashes were recorded;
- the final prompt equals the scenario specification;
- changed paths stay within the scenario allowlist;
- generated files and responses are retained in canonical artifacts;
- skipped gated tests are reported as not run;
- human verification remains pending until explicitly confirmed.
- destination documents use only context available and appropriate to their
  audience;
- blocked workflows do not expand mutation scope or weaken completion
  criteria;
- safe partial work, blockers, and remaining actions are distinguished in the
  final response.
- required routed pages are read before the first mutation when the scenario
  declares a routing-read contract;
- obvious placement does not trigger duplicate confirmation or opaque
  ownership jargon;
- explicit approved structure overrides are honored unless a substantive
  boundary prevents them.

## Implementation ownership

This specification owns expected standard-consumer behavior. The
[agent evaluation framework specification](../../agent-evaluation-framework/index.md)
owns execution, caching, evidence, and artifact mechanics.

The implemented pytest suite belongs under `maintainer/agent-evaluation/`.
Package documentation explains how to run and inspect it without duplicating
the scenario contracts defined here.