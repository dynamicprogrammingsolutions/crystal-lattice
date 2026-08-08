Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`

Related Task:

- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- `tasks/20260721-task-guidance-evaluation-workflow.md`

Specification:
`maintainer/specifications/agent-evaluation-framework/index.md`

Requirement IDs:
`AEVAL-001`–`AEVAL-018`, `DOCGEN-001`–`DOCGEN-005`,
`DOCREP-001`–`DOCREP-005`, `DOCVAL-005`

# Programmatic Agent Evaluation Framework

Create a small generic evaluation kernel with one replaceable run-environment
boundary. Implement Crystal Lattice as the first rich environment, keeping its
tool-loop, configuration, snapshot, evidence, evaluation, and presentation
details customizable. Use the documentation-standard instructions as the first
behavioral consumers.

## Requirements checklist

- [x] A package under `maintainer/agent-evaluation/` exposes the approved
  generic `agent_eval` kernel.
- [x] `AgentEval.run()` accepts only a name, arbitrary program callback, and
  optional environment, parent run, workspace, and cache key.
- [x] The kernel owns run/workspace/cache/artifact/error lifecycle without
  hardcoding agent or evaluation semantics.
- [x] One `RunEnvironment` contract is the broad replacement seam for context
  creation, compatibility, restoration, snapshotting, and finalized
  observations.
- [x] `CrystalLatticeEnvironment` is the first complete environment and
  preserves direct access to application, core, session, configuration,
  workspace, and generic run services.
- [x] Crystal Lattice request/tool-loop execution, stopping, configuration
  changes, snapshots, observation, projections, evaluation, and presentation
  are replaceable at their point of use.
- [x] Alternate environments can bypass the Crystal Lattice lower-layer model
  while reusing the generic kernel.
- [x] Programs can perform one or several environment operations and return any
  Python value.
- [x] Runs can be cached and continued in compatible clean workspaces with
  exact environment, snapshot, repository, and parent provenance.
- [x] Canonical artifacts show useful program/environment results, changed
  paths, errors, and provenance without requiring routine inspection of raw
  evidence.
- [x] Complete raw evidence remains available separately and does not retain
  credentials or authentication state.
- [x] Deterministic package tests cover the generic kernel, environment
  substitution, Crystal Lattice customization, and failure behavior.
- [ ] Pytest is the initial suite runner, with explicit real-model markers and
  hosted-execution gates outside normal default tests.
- [ ] First-consumer tests exercise every `DOCGEN-*` and `DOCREP-*`
  documentation-standard instruction requirement using reusable narrow
  guidance-neutral task-specific base runs and clean continuations.
- [ ] Behavioral model results remain supporting evidence; static checks and
  explicit human review retain their distinct roles.
- [ ] After representative model runs, an evidence-backed calibration review
  proposes any seed/test cuts, replacements, or additions, and no such suite
  change is applied without user approval.
- [ ] Existing task-guidance evaluation remains operational and is not moved or
  rewritten by this subtask.

## Supporting details

### Approved architecture

The user approved a four-layer model:

```text
generic AgentEval kernel
    -> replaceable RunEnvironment
        -> environment-specific context
            -> optional lower-level operations and helpers
```

The proposed kernel call is:

```python
run = evaluation.run(
    "run-name",
    program,
    environment=environment,
    continue_from=previous_run,
    workspace=workspace_factory,
    cache_key="optional-cache-key",
)
```

The generic kernel owns:

- run identity;
- workspace preparation and cleanup;
- cache lookup/publication;
- parent-run linkage;
- generic artifacts;
- error preservation;
- returning `Run[T]`.

`RunEnvironment` owns:

- compatibility fingerprint;
- context construction and cleanup;
- restoration of a parent snapshot;
- final reusable snapshot;
- environment-specific normalized observation and raw evidence.

The first `CrystalLatticeEnvironment` owns:

- `AgentApplication` and `AgentCore` integration;
- session and request behavior;
- application configuration and plugins;
- default and custom request/tool-loop drivers;
- stop conditions and observers;
- default and custom snapshots;
- evidence projections;
- arbitrary evaluations/scoring;
- audience-specific presentation.

An alternate environment may ignore all Crystal Lattice lower-layer concepts.

Do not add required `Case`, `Suite`, `Check`, `Reviewer`, `Score`,
`InstructionLayer`, `RunPolicy`, or `Recipe` abstractions. If repeated consumer
code later justifies conveniences, implement them as optional layers.

### Existing validated prototype

The current task-guidance evaluator already demonstrates:

- a guidance-neutral investigation of one concrete modification;
- request-profile and repository fingerprints;
- immutable session hashing;
- imported-session compatibility checks;
- path rebasing into independent fork workspaces;
- compiled request capture;
- tool and mutation telemetry;
- deterministic assertions;
- separate empirical review;
- human-readable exported conversations and review bundles.

Relevant sources:

- `test/task_guidance/harness.py`
- `test/task_guidance/task_guidance_eval.py`
- `test/task_guidance/prepare_review_bundle.py`
- `test/task_guidance/README.md`
- `tasks/20260721-task-guidance-evaluation-workflow.md`

The specialized evaluator is a source of verified behavior, not the target
public API. A representative case stores tens of megabytes of workspace,
events, sessions, and compiled prompt while the useful response/assertion
material is only a small fraction.

### Boundary with subtask 068

This subtask creates:

- the generic kernel;
- the first Crystal Lattice environment;
- documentation-standard behavioral consumers.

Subtask 068 remains responsible for:

- moving task-guidance evaluation code, fixtures, and documentation under
  `maintainer/`;
- adopting the kernel and Crystal Lattice environment where appropriate;
- updating existing commands and consumers;
- preserving task-guidance-specific deterministic assertions and empirical
  review behavior;
- removing obsolete specialized infrastructure only after equivalent behavior
  is verified.

### First-consumer intent

The documentation-standard tests should establish whether supported agents can
apply the authored instructions, not whether a reviewer model generally likes
the resulting documentation.

The suite covers:

- package-neutral versus repository-specific guidance;
- specification target versus live requirements/current docs;
- package-owned specifications and package-specific refinements;
- substantial-specification approval boundaries;
- one normative owner, controlled summaries, and discoverability;
- root/package/shared-plugin ownership;
- proportional package profiles without filler;
- applying versus maintaining the standards.

Tests may vary user messages, configuration, plugins, skills, request drivers,
snapshots, evidence projections, evaluators, presentations, or models. They
should not require a particular instruction-injection, assertion, or
presentation mechanism.

## Implementation Notes

- August 6, 2026: The user approved the generic-kernel architecture and
  execution plan. The plan is `Approved`.
- August 6, 2026: Four mandatory review checkpoints were defined before
  implementation. Work started with Checkpoint 1 only.
- The existing root `evaluations/` package is a benchmark/CLI/scheduler system.
  It remains a separate owner and is not used as the implementation location
  for this small programmatic maintainer library.
- The existing `test/task_guidance` evaluator remains read-only reference
  material during Checkpoint 1.
- Checkpoint 1 implemented the generic package, exact kernel API,
  `RunEnvironment`, `RunServices`, arbitrary program values, immutable parent
  continuation, optional environment snapshot codecs, reusable Git workspaces,
  atomic locked cache, cached workspace/evidence restoration, canonical/raw
  artifacts, redaction, and inspectable failures.
- Checkpoint 1 verification:
  - 21 deterministic tests passed;
  - Ruff passed;
  - mypy passed for all 14 source/test files;
  - Python compilation passed;
  - wheel build passed;
  - `git diff --check` passed;
  - a persistent fresh/cache-hit/continuation sample under
    `tmp/agent-evaluation-checkpoint1/` produced 1.4–1.7 KB canonical Markdown
    files and required no environment execution for the cache hit.
- `pyright` was not installed in the current environment; mypy provided the
  checkpoint static type verification.
- Checkpoint 2 implemented `CrystalLatticeEnvironment` and
  `CrystalLatticeContext` over production `AgentApplication`/`AgentCore`
  boundaries, including ordinary configuration and plugin loading, default
  request/tool-loop execution, streaming, custom drivers, observers, stopping,
  mutation classification, JSON continuation snapshots, workspace rebasing,
  named snapshots, evidence projection, arbitrary evaluation, presentation,
  cache reuse, and application cleanup.
- Checkpoint 2 documentation followed the approved adjustment:
  - `README.md` is now a concise package entry point;
  - `AGENTS.md` contains development boundaries and pointers;
  - `docs/index.md` routes users to focused current-behavior pages;
  - quickstart, environment/customization, continuation/cache,
    artifact/evidence, and development pages contain the detailed guidance;
  - no placeholder pages were added.
- The proposed `application_tool_loop(...)` helper name was not implemented.
  Equivalent controls are direct `context.request(...)` inputs
  (`observers`, `stop_when`, `mutation_classifier`, `max_events`) or a complete
  custom `RequestDriver`; this keeps each abstraction optional.
- Checkpoint 2 verification:
  - 34 deterministic tests passed;
  - tests crossed real Core/Application construction, dotted plugin loading,
    streaming, and application tool-loop boundaries;
  - Ruff passed;
  - mypy passed for all 22 source/test files;
  - Python compilation passed;
  - all package Markdown links resolved;
  - all documented Python blocks parsed;
  - a persistent production tool-loop sample under
    `tmp/agent-evaluation-checkpoint2/` produced a 2.5 KB canonical Markdown
    result, a 342-byte manual-review projection, and separate raw session and
    event evidence.
- Checkpoint 2 review follow-up: the user found that the package documentation
  described APIs before establishing the basic mental model. The docs home now
  explains the purpose, lifecycle, main concepts, and their relationships.
  Focused pages now define environment/context, request/outcome,
  snapshot/continuation/cache, evidence/projection/artifact/evaluation, and
  presentation before using those terms.
- The same review found that `internal` evidence was still written into
  `raw/evidence.json`. The artifact renderer now omits internal evidence, with a
  regression test, matching the documented visibility contract.
- August 7, 2026: The user approved a standard-owned
  `agent-behavior-verification/` specification with one page per consumer test.
  The first six pages define `DOCGEN-*` behavior through ordinary repository
  tasks, exact AGENTS/routed guidance delivery, short human-style prompts,
  mechanical assertions, semantic projections, and human-review questions.
- The consumer-test design explicitly does not ask agents to author or
  summarize the standards. `DOCGEN-001` uses separate small-package and
  generated-output scenarios because those behaviors have different realistic
  tasks and assertions.
- The former Checkpoints 3 and 4 were merged. Test authoring, deterministic
  verification, real-model execution, artifact inspection, evidence updates,
  and human-review handoff now form one final checkpoint.
- August 7, 2026: Consumer-test specification naming was refined to
  two-digit test files and `seed-<number>-...` reusable setup files. The neutral
  cached investigation now has its own seed specification and every `DOCGEN-*`
  test records line-linked requirement, target-specification, authored-guidance,
  and assertion traceability with copied review excerpts.
- August 7, 2026: The seed design was corrected to match the original
  task-guidance evaluation intent. Seeds are now narrow factual investigations
  of a concrete package/task/contract, simple enough for a cheap model, shared
  only by closely related branches, and reusable across candidate-guidance
  revisions because guidance is added after continuation.
- August 8, 2026: The approved follow-up coverage was added. Seeds now also
  cover existing-contract and local bug fixes, a completed implementation
  awaiting documentation, and a partial major change. Consumer tests cover
  spec-only preparation, implementation from a prepared target, task-authorized
  specification creation, proportional bug fixes, documentation follow-up,
  partial multi-commit state, and portable-versus-package ownership.
- Seed 08 establishes an intentionally mutated code/test base. The seed
  contract therefore permits an exact verified mutation allowlist when the
  behavior under test is a continuation from completed work; candidate guidance
  remains absent until the follow-up branch.
- August 8, 2026: Merged Checkpoint 3 implementation started. The first
  executable vertical slice now includes explicit GLM/GPT profiles, hosted-run
  gating, pinned focused Git fixtures, exact prompt extraction from the
  approved scenario pages, candidate-guidance hashing/overlay, cached seeds,
  continuation branches, deterministic findings, semantic-assessment inputs,
  and manual-review artifacts for Tests 01–02.
- Package verification for the vertical slice has 40 passing default tests,
  two gated real-model tests collected only under `agent_eval`, and clean Ruff
  and diff checks. Package-local mypy imports currently expose pre-existing
  Core/Application typing failures when the repository dependency graph is
  followed; no new suite-specific mypy failure remains after the fixture
  annotation correction.
- The first GLM-5.2 seed attempts showed that raw application event count is
  unsuitable as a model-work budget because streaming/token events dominate
  it. The test-owned run strategy now uses a meaningful tool-event stop
  condition and leaves raw stream events uncapped.
- The GLM Seed 01 run completed after the workspace was narrowed to the target
  plugin and relevant shared docs. It produced a factual investigation with no
  repository mutation. Its first continuation exposed a generic restoration
  defect: workspace-path rebasing updates restored messages while retaining
  stale provider-native history, causing Core to reject the next request. A
  framework regression fix is in progress before additional consumer cases run.
- The continuation defect is fixed with regression coverage: rebased snapshots
  discard stale provider-native history so the next request rebuilds it, while
  same-workspace restoration preserves valid native history.
- The first completed GLM Test 01 branch changed only the package README and
  added supported configuration, first-use, verification, and shared-doc
  links. It failed the approved first-use assertion because the first-use
  section did not provide a concrete input plus expected uppercase output.
  This is retained as behavioral evidence rather than weakening the scenario.
- GLM Test 02 corrected the authored README but also directly edited
  `docs_site/prepared/`, explicitly acknowledging that the generated page
  should not be edited. The approved generated-output assertion therefore
  failed and is retained as guidance-clarity evidence.
- Initial GPT-5.6-luna execution authenticated successfully through the saved
  ChatGPT account but showed that raw `tool_event_count` is provider-dependent:
  streamed shell fragments exhausted the budget after only three completed
  commands. The strategy now counts unique completed tool-call IDs from
  `tool_results`; deterministic tests cover Codex and Claude event shapes.
- With the completed-call strategy, GPT-5.6-luna Test 01 passed. The seed made
  no mutations and completed in about 156 seconds; the branch changed only the
  package README, added concrete first-use input/output and verification, and
  completed in about 77 seconds. The complete pytest command took 258.65
  seconds.
- Tests 03–14 and Seeds 02–09 are now implemented with focused package/task
  fixtures and explicit Python assertions. All 14 DOCGEN consumers collect only
  under the gated marker. Deterministic prompt/fixture contracts, package tests,
  and lint currently pass with 47 default tests and 14 real-model tests
  deselected.
- GLM-5.2 Test 07 completed with only the existing product specification,
  technical specification, and requirements changed. It correctly avoided
  code, tests, and current user documentation, and it represented the future
  implementation/documentation state as pending. The deterministic scenario
  still failed because the requirements table used `Pending` for verification
  instead of the standard `Unverified` vocabulary. This is retained for the
  calibration review as a distinction between correct live-state meaning and
  exact status-convention compliance.
- GPT-5.6-luna Test 11 passed end to end in 220.18 seconds. The guidance-neutral
  seed made no changes. The continuation fixed the local cache-cleanup race,
  added a focused regression test, changed only code and tests, created no
  specification, left the README unchanged, and reported two passing tests
  plus a clean diff check.
- The targeted representative sample now exercises all nine seed families.
  GLM-5.2 Test 04 passed: the agent created a proportional mobile-owned UX
  refinement, linked rather than copied the portable contract, kept live state
  pending, and updated the package development index without implementing the
  UI.
- GPT-5.6-luna Test 10 passed: the agent treated the existing target as
  correct, fixed implementation and regression coverage, updated current user
  documentation and live evidence, and did not create or rewrite a
  specification.
- GLM-5.2 Test 05 completed with semantically strong discoverability changes
  but failed a lexical assertion because the README used `retried` while the
  assertion required the exact substring `retry`. The run is retained as a
  likely assertion false negative for the approval-gated calibration review.
- GPT-5.6-luna Test 12 passed: from an intentionally mutated seed, the agent
  left code/tests and the stable technical target unchanged while completing
  current README documentation and live requirement evidence.
- GLM-5.2 Test 06 failed the substantial-specification approval boundary on
  its first turn. It made no file changes and covered owner, scope, artifacts,
  transport, and persistence overlap, but produced a complete 9,448-character
  design instead of explicitly requesting approval. The approved continuation
  did not run because the first-turn assertion failed.
- GPT-5.6-luna Test 13 completed Phase 2 implementation, verification,
  requirements, task tracking, and temporary progress correctly, but failed
  because the current README mentioned target-only Phase 3 conflict
  resolution. The future-target leak is retained as a genuine current-versus-
  target documentation finding.
- The representative runs exposed fixture noise independent of the guidance:
  synthetic Python packages use hyphenated directories while their initial
  tests import underscore package paths. Models repaired imports or added path
  setup in Tests 10, 11, and 13. The fixture baseline should be runnable before
  the task, and fixture revisions must invalidate stale cached seeds.
- The fixture baseline defect is corrected. Six synthetic Python packages now
  use package-local test path setup and module imports that pass before any
  consumer task. Per-fixture revisions participate in workspace fingerprints
  and explicit seed/branch cache keys, preventing stale cached conversations
  from restoring the previous fixture contents. Verification passes with 49
  default tests, 14 gated tests deselected, clean Ruff, and clean diff checks.
- Because all seed families have now produced representative evidence and the
  sample found both a likely assertion defect and fixture noise, calibration
  should precede the complete cross-model matrix. The calibration proposal may
  recommend suite/specification changes, but none may be applied without user
  approval.

### Post-run calibration proposal

Status: Pending user approval

The representative sample covers every seed family and includes both models,
successful behavior, genuine guidance-consumer failures, one likely
deterministic-assertion false negative, and one corrected fixture defect. This
is sufficient to propose the first suite calibration without treating a single
model outcome as conclusive proof.

#### Keep and enforce

Keep the following scenario requirements and assertions unchanged:

- Test 01 concrete first-use input/output. GLM's plausible but incomplete
  README demonstrates that this assertion distinguishes a usable quickstart
  from a descriptive one.
- Test 02 authored/generated boundary. The absence of a local generator does
  not authorize direct edits to prepared output; the agent should change the
  source and report blocked regeneration.
- Test 06 explicit approval request before a substantial unapproved
  specification. A detailed design in chat is not a substitute for stopping at
  an owner/scope/overlap/artifact proposal and asking for approval.
- Test 07 exact requirements status vocabulary. `Pending` accurately conveyed
  future work but did not satisfy the standard's separate `Unverified`
  verification state. Keep this strict because deterministic live-state
  dimensions are intentional.
- Test 13 exclusion of target-only behavior from current public documentation.
  Requirements and temporary progress may describe Phase 3; the package README
  may describe only delivered behavior.

Keep all nine seeds and all fourteen scenario specifications. Each seed now
owns a distinct setup family, and the multi-branch seeds amortize their
investigation:

- Seed 02 distinguishes same-run implementation, specification-only
  preparation, and implementation from a prepared target.
- Seed 03 distinguishes package refinement from portable-contract ownership.
- Seed 05 distinguishes an unapproved substantial specification from one
  already authorized by a task.
- Seed 08 uniquely verifies a documentation/tracking follow-up after completed
  code and tests.

No seed or scenario should be deleted based on the current sample.

#### Replace one brittle assertion

Replace Test 05's exact substring assertion with a deterministic
discoverability assertion that accepts normal retry morphology:

- README contains `retry`, `retries`, `retried`, or `retrying`, or directly
  links the retry lifecycle page.
- The package docs index names retry behavior and links the current user page.
- The current user page still contains the `retrying` and `failed` states.
- Target-only replay behavior remains excluded.

This changes only how the approved discoverability behavior is detected. It
does not relax the requirement that users can find the lifecycle from both the
package root and docs index.

#### Cut the routine matrix without deleting coverage

Classify scenarios into two optional pytest groups:

- Routine guidance suite:
  Tests 01, 02, 03, 04, 05, 06, 07, 10, 11, and 13.
- Extended workflow suite:
  Tests 08, 09, 12, and 14, while also including the routine group when a full
  run is requested.

The extended-only cases are valuable but lower-frequency continuations or
reverse ownership checks:

- Test 08 implements from the prepared state created by Test 07.
- Test 09 repeats substantial-specification creation after authorization,
  complementing Test 06's approval boundary.
- Test 12 is a documentation-only follow-up after an intentionally mutated
  seed.
- Test 14 is the reverse ownership direction complementing Test 04.

This is a runtime cut, not deletion of specifications, seeds, or executable
tests. Every `DOCGEN-*` requirement remains covered in the routine group, and
the extended group preserves the broader workflow matrix.

#### Model execution policy

For ordinary changes to the guidance:

- run the routine group on GLM-5.2;
- run GPT-5.6-luna sentinels for Tests 01, 02, 04, 06, and 13.

For material changes to specification workflow, ownership, approval, current
documentation boundaries, or before declaring the standard behaviorally
verified:

- run all fourteen tests on at least one supported model;
- run the GPT sentinel set;
- use a full second-model matrix only when the change or observed variance
  justifies its cost.

The current sample shows that provider/model diversity matters, but raw full
cross-products are expensive: sampled GLM branches generally took about one to
two minutes, while sampled GPT seed/branch commands took about three to five
minutes.

#### Reruns after fixture correction

The corrected fixture revision invalidates affected caches. Before using those
runs as final requirement evidence:

- rerun Tests 10, 11, and 13 so model diffs no longer include import/path setup
  repairs;
- run Tests 03, 08, 09, and 14 at least once because they have no real-model
  result yet;
- run Test 06 on GPT to distinguish a GLM-specific approval failure from a
  cross-model guidance issue;
- run Test 07 on GPT to compare exact status-vocabulary compliance.

Test 05 does not require another model call solely to validate the corrected
assertion because its preserved canonical artifact is sufficient for
deterministic replay. It may still run as part of the routine matrix.

#### Repetition and new scenarios

Do not add random repetitions or new DOCGEN seeds yet. Cross-model sentinel
runs provide more useful information than repeated identical calls at the
current evidence volume.

Proceed separately with the required `DOCREP-*` scenarios. Their
repository-specific package profiles, root-versus-package ownership, shared
plugin domain, and applying-versus-maintaining boundaries are missing
requirement consumers rather than calibration additions to DOCGEN.

#### Approval boundary

Approval of this proposal would authorize:

- updating Test 05's specification and deterministic assertion;
- adding routine/extended pytest markers or equivalent selection;
- following the calibrated model/rerun matrix above.

It would not authorize removing seeds/tests, weakening Tests 01, 02, 06, 07,
or 13, or changing the documentation standard itself. Any later remove,
replace, or add proposal based on new evidence would require another approval.

## Execution plan

Status: Approved

The implementation should establish the generic kernel first, prove the
environment boundary with both a deterministic alternate environment and
Crystal Lattice, and then add the documentation-standard real-model consumers.
The existing task-guidance evaluator remains unchanged except for read-only
comparison and possible reuse of clearly generic implementation ideas.

### 1. Establish the package and generic kernel contract

1. Create the maintainer-owned Python package with an independently testable
   `pyproject.toml`, concise README, `src/agent_eval/`, package tests, and
   real-model suite directory.
2. Export only the approved initial kernel contract:
   - `AgentEval`;
   - `Run`;
   - `RunServices`;
   - `RunEnvironment`;
   - workspace factory type and optional `git_workspace()` helper.
3. Implement `AgentEval.run(name, program, *, environment=None,
   continue_from=None, workspace=None, cache_key=None)`.
4. Keep serialization, artifact, lock, cache, and workspace implementation
   details private.

### 2. Implement the run-environment lifecycle

1. Define the environment operations:
   - compatibility fingerprint;
   - open/restore context;
   - final snapshot;
   - finalized observation.
2. Make snapshots opaque to the kernel except for environment-supported
   serialization, hashing, and storage.
3. Permit environments without snapshots; those runs cannot be continuation
   parents.
4. Return program values and finalized observations without assigning a
   framework-owned verdict.
5. Preserve run/environment failures by phase.

### 3. Implement generic workspaces, continuation, cache, and artifacts

1. Accept existing paths and arbitrary workspace factories.
2. Add an optional Git helper using pinned revisions, reusable repository
   cache, detached clean workspaces, status, changed paths, and diff capture.
3. Restore parent snapshots only when environment and workspace compatibility
   checks pass.
4. Preserve immutable parent hashes and restore/rebase provenance.
5. Implement explicit versioned cache keys combined with environment,
   workspace, parent, and framework-schema fingerprints.
6. Use safe atomic cache writes and locking; reject incompatible, corrupt, or
   partial entries.
7. Write generic canonical Markdown/JSON and separate raw evidence for every
   success or failure.
8. Ensure generic and environment artifacts do not copy credentials or
   authentication state.

### 4. Prove environment substitution

1. Add a small deterministic replay or in-memory environment.
2. Verify fresh execution, arbitrary context API, custom return values,
   snapshots, continuation, finalized observation, cache reuse, and artifacts.
3. Confirm it does not implement or import Crystal Lattice request/tool-loop,
   evidence-projection, or presentation helpers.
4. Use this environment for fast kernel tests without pretending it replaces
   the real Crystal Lattice integration tests.

### 5. Implement the Crystal Lattice environment

1. Build on `AgentApplication` and `AgentCore` rather than reproducing provider
   behavior.
2. Support caller-owned application configuration, environment, and plugins.
3. Provide context conveniences for:
   - starting/selecting an agent;
   - adding arbitrary supported message roles/content;
   - issuing requests with ordinary Crystal Lattice overrides;
   - obtaining final assistant responses;
   - recording evidence and custom artifacts.
4. Preserve direct access to application, core, current immutable session, base
   configuration, workspace, and run services.
5. Supply a default request driver wrapping the production application
   tool-loop path.
6. Permit per-request custom drivers, stop conditions, and observers.
7. Supply a default restorable application/session snapshot while permitting
   custom named snapshotters.
8. Provide the evidence journal, projection, arbitrary evaluation, and
   presentation conveniences described by the specification.
9. Keep all these lower-layer operations optional and bypassable through direct
   application/core access.

### 6. Add deterministic framework tests

Cover:

1. Arbitrary program execution and return values.
2. Default and per-run environment selection.
3. Alternate environment substitution with no Crystal Lattice dependency.
4. Parent snapshot restoration and immutability.
5. Workspace creation, Git changes, cleanup, and reconstruction evidence.
6. Cache hit, miss, incompatibility, corruption, locking, and atomic writes.
7. Canonical/raw artifact shape.
8. Environment and program failure preservation.
9. Credential/auth-state exclusion.
10. Crystal Lattice application lifecycle and direct escape-hatch access.
11. Default and custom request driver behavior.
12. Default and custom snapshots.
13. Evidence projections, arbitrary evaluation results, and presentations.
14. At least one real Crystal Lattice consumer at the lowest practical
    non-provider boundary so integration does not only exercise mocks.

### 7. Add pytest documentation-standard consumers

1. Implement and maintain the standard-owned seed and scenario contracts under
   `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/`.
2. Register an `agent_eval` marker and exclude real-model suites from normal
   package tests.
3. Create session-scoped narrow scenario-family base runs using pinned
   baselines or clean fixtures that do not contain candidate instructions.
   Keep most read-only; allow exact verified mutations only when a completed
   state is the intended shared follow-up base.
4. Fork clean continuations covering all `DOCGEN-*` and `DOCREP-*`
   requirements.
5. Deliver the exact candidate AGENTS files and routed documentation through
   the normal agent mechanism. Keep scenario user prompts short and free of the
   rules being evaluated.
6. Leave room for configuration/plugin/skill instruction variants without
   kernel changes.
7. Use normal pytest assertions for objective path, content, mutation, and
   provenance outcomes.
8. Where semantic interpretation adds value, create explicit evidence
   projections and request test-owned structured scores or findings.
9. Create a separate compact human-review presentation rather than reusing the
   full raw or AI-assessment input.
10. Record exact environment/configuration, model, instruction hash, prompt,
   seed, tool, projection, evaluation, presentation, output, and error
   evidence.
11. Keep human-review requirements unverified until the user reviews the
   canonical artifacts.
12. After representative runs, prepare a separate calibration proposal covering
    redundant/low-value cases, excessive setup cost, observed variance, and
    missing guidance-clarity signals. Do not modify the approved scenario
    specification or suite from that proposal without user approval.

### 8. Verify and document

1. Run package deterministic tests in the normal fast path.
2. Run the documentation-standard real-model tests only with their explicit
   gate enabled.
3. Report skipped provider/model cases as not run.
4. Inspect canonical, AI-assessment, manual-review, and raw artifact
   boundaries.
5. Update `AEVAL-*` and `DOCVAL-005` evidence.
6. Present the behavioral results for human review of `DOCGEN-*` and
   `DOCREP-*`.

### Execution checkpoints

Implementation stops at each checkpoint for a progress report. A checkpoint
must leave its listed boundary complete, tested, documented where applicable,
and independently reviewable. Later checkpoints may build on it but should not
be required to understand whether the checkpoint succeeded.

#### Checkpoint 1: generic kernel and alternate environment

Complete plan sections 1–4 and the generic portions of section 6:

- package and public kernel contract;
- `RunEnvironment`, `RunServices`, and `Run`;
- workspace factories and Git helper;
- parent snapshots and continuation;
- compatible cache, atomic publication, and locking;
- generic canonical/raw artifacts and error preservation;
- deterministic alternate environment;
- deterministic kernel, cache, workspace, continuation, artifact, and failure
  tests;
- kernel and alternate-environment README/API examples.

Stop and report:

- exported API;
- implementation and test files;
- deterministic test results;
- representative canonical and raw artifacts;
- any deviations from the approved contract;
- remaining Crystal Lattice integration risks.

#### Checkpoint 2: Crystal Lattice environment

Complete plan section 5 and the Crystal Lattice portions of section 6:

- Core/Application lifecycle;
- direct application/core/session/configuration access;
- default production request driver;
- custom request drivers, stop conditions, and observers;
- default and custom snapshots;
- evidence journal integration and projections;
- arbitrary evaluation/scoring;
- audience-specific presentation;
- deterministic and lowest-practical real Crystal Lattice integration tests;
- Crystal Lattice usage and customization documentation.

Stop and report:

- concrete context API;
- production boundaries crossed by tests;
- test results;
- representative simple and customized artifacts;
- any behavior intentionally deferred to task-guidance adoption.

#### Checkpoint 3: documentation-standard behavioral verification and evidence handoff

Complete plan sections 7 and 8 as one reviewable outcome:

- complete standard-owned scenario contracts for every `DOCGEN-*` and
  `DOCREP-*` requirement;
- marker and explicit local/hosted gates;
- narrow guidance-neutral scenario-family base runs;
- exact candidate AGENTS/routed-file overlay and provenance;
- clean continuation fixtures;
- ordinary short task prompts that do not restate the rules;
- objective path, content, mutation, and provenance assertions;
- structured semantic-evaluation paths;
- separate human-review presentations;
- deterministic helper, collection, and gate tests;
- documented commands and prerequisites;
- at least one explicitly enabled supported real-model path across the full
  requirement matrix;
- canonical/raw artifact and size inspection;
- `AEVAL-*` and `DOCVAL-005` evidence updates;
- `DOCGEN-*` and `DOCREP-*` human-review handoff;
- explicit reporting of provider/model cases not run.
- post-run calibration proposal for seed/test retention and additional
  clarity coverage, awaiting user approval before any suite changes.

Stop and report:

- scenario matrix and requirement coverage;
- exact prompts and candidate guidance provenance;
- deterministic and real-model results;
- selected assertion, AI-assessment, and human-review projections;
- representative canonical and raw artifacts;
- provider/model paths run or not run;
- final implementation outcome and unresolved findings.

Do not mark `DOCGEN-*` or `DOCREP-*` human verified without explicit human
confirmation.

### Implementation decisions and open questions

- Approved: use a generic kernel rather than making `AgentEval` specific to
  Crystal Lattice.
- Approved: `RunEnvironment` is the one broad replacement seam.
- Approved: Crystal Lattice is the first complete environment and contains the
  finer-grained Option 3-style customization.
- Approved: alternate environments may bypass the complete Crystal Lattice
  lower-layer pattern.
- Approved: arbitrary program callbacks own all evaluation-specific behavior.
- Approved: pytest modules are the initial suites and runner.
- Approved: the first consumers verify documentation-standard instructions.
- Approved: task-guidance migration remains in subtask 068.
- Approved: use `maintainer/agent-evaluation/` as the distribution directory
  and `agent_eval` as the Python import.
- Approved: every `DOCGEN-*` and `DOCREP-*` requirement has at least one
  behavioral consumer, while one test may cover a coherent group.
- Approved: initial behavioral evidence requires one explicitly enabled
  supported real-model path; additional model families and repeated
  statistical thresholds remain optional until actual variance justifies
  them.
- Approved: documentation-standard behavior and scenario contracts are owned
  by the documentation-standard specification, while the framework
  specification owns execution mechanics.
- Approved: behavioral tests deliver exact AGENTS/routed files through normal
  agent mechanisms and use ordinary short task prompts rather than restating
  the rules under test.
- Approved: the final consumer-test implementation and real-model execution use
  one combined checkpoint.
- Approved: reusable cached/setup conversations have separate
  `seed-<number>-...` specifications, while behavioral tests use two-digit
  filenames.
- Approved: each seed investigates one concrete package, issue, task, or
  contract and supports closely related continuation branches; a generic
  repository survey is not an evaluation seed.
- Approved: a seed may perform one tightly constrained, fully verified base
  operation when later consumer tests need a completed follow-up state.
- Approved: candidate guidance is excluded from seed cache identity and added
  only to branch continuations so the seed can compare guidance revisions.
- Approved: every behavior-test specification links line ranges for its
  requirement, target meta-specification, and authored guidance and copies the
  relevant source sentences as non-normative review aids.
- Approved: representative runs are followed by a separate evidence-backed
  suite-calibration review; proposed seed/test changes require user approval
  before implementation or specification updates.
- Local reversible choices include internal module decomposition, snapshot
  codec implementation, JSON serialization, file locking, and canonical
  rendering details.
- No unresolved requirement question changes the required outcome.

### Documentation

- `maintainer/agent-evaluation/README.md`
- Public API docstrings and typing for the generic kernel and environment
  contract
- Crystal Lattice environment and customization documentation
- Pytest marker and real-model execution instructions
- Cache and artifact-layout guidance
- Complete simple, customized Crystal Lattice, and alternate-environment
  examples
- `maintainer/README.md` routing
- `maintainer/specifications/agent-evaluation-framework/*`
- `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/*`
- Updated evidence in both framework and documentation-standard requirements

### Task checklist

- [x] Create the maintainer package and generic kernel exports.
- [x] Implement `AgentEval.run()`, `Run`, and `RunServices`.
- [x] Implement `RunEnvironment` lifecycle and compatibility.
- [x] Implement workspace factories and optional Git helper.
- [x] Implement parent snapshot continuation.
- [x] Implement compatible caching and locking.
- [x] Implement generic canonical and raw artifacts.
- [x] Add the deterministic alternate environment.
- [x] Implement the Crystal Lattice environment and context.
- [x] Implement customizable request drivers and snapshots.
- [x] Implement evidence projection, evaluation, and presentation helpers.
- [x] Add deterministic kernel and alternate-environment tests.
- [x] Add deterministic Crystal Lattice environment tests.
- [x] Register the gated pytest real-model marker.
- [x] Specify the `DOCGEN-*` behavioral consumer scenarios.
- [x] Specify narrow scenario-family investigation seeds for current DOCGEN
  tests.
- [x] Specify proposed additional DOCGEN seeds and consumer-task branches.
- [ ] Specify the `DOCREP-*` behavioral consumer scenarios.
- [ ] Add documentation-standard behavioral consumers.
  - [x] Add profile selection, explicit gates, focused Git fixtures, exact
    guidance provenance, prompt extraction, cacheable seeds, review records,
    and Tests 01–02.
  - [x] Fix and verify clean continuation after workspace-path rebasing.
  - [x] Add Tests 03–14 and their remaining fixtures/assertions.
  - [ ] Add `DOCREP-*` consumers after their scenario contracts are approved.
- [x] Run deterministic tests.
- [ ] Run or explicitly report the gated real-model suite as not run.
  - [x] Run GLM-5.2 Seed 01 and preserve the completed seed artifact.
  - [ ] Complete GLM-5.2 consumer branches.
    - [x] Run Tests 01–02 and preserve their passing/failing findings.
    - [x] Run Tests 04–06 and preserve the ownership, discoverability, and
      approval-boundary findings.
    - [x] Run Test 07 and preserve its status-vocabulary finding.
  - [x] Run GPT-5.6-luna through ChatGPT account authentication.
    - [x] Run Test 01 and preserve its passing artifact.
    - [x] Run Test 10 and preserve its passing existing-target artifact.
    - [x] Run Test 11 and preserve its passing artifact.
    - [x] Run Test 12 and preserve its passing follow-up artifact.
    - [x] Run Test 13 and preserve its future-target leak finding.
    - [ ] Run the remaining implemented consumer cases.
- [x] Correct and verify synthetic fixture baseline test imports and fixture
  cache invalidation without changing approved scenario behavior.
- [ ] Update `AEVAL-*` and `DOCVAL-005` evidence.
- [ ] Present canonical behavioral artifacts for human review.
- [x] Prepare the post-run seed/test calibration proposal for user approval.
  - [ ] Obtain user approval before changing scenario specifications,
    assertions, or routine/extended selection.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Generic kernel (`AEVAL-001`–`AEVAL-003`, `AEVAL-007`–`AEVAL-008`) | Package import and API tests exercise the exact `AgentEval.run()` signature, arbitrary programs/return values, generic `RunServices`, `Run` fields, artifacts, and errors without agent-specific assumptions or a framework-owned verdict. |
| Environment replacement (`AEVAL-004`) | A deterministic alternate environment provides its own context, snapshot, and observation, supports continuation/cache, and imports no Crystal Lattice environment helpers. |
| Crystal Lattice environment (`AEVAL-005`–`AEVAL-006`) | Integration tests exercise Core/Application configuration, plugins, direct context access, default/custom request drivers, stop behavior, snapshots, evidence projections, arbitrary evaluation results, and presentations. |
| Continuation, cache, and workspace (`AEVAL-009`–`AEVAL-011`) | Deterministic tests show immutable parent restoration, compatible environment checks, clean fork workspaces, pinned Git evidence, cache reuse, and rejection of incompatible/corrupt entries. |
| Artifacts and safety (`AEVAL-012`–`AEVAL-013`) | Success/failure fixtures produce concise canonical output and separate raw evidence; tests confirm credential/auth files are not copied and custom projections/presentations use only selected inputs. |
| Deterministic quality (`AEVAL-014`) | Normal package tests pass kernel, alternate-environment, Crystal Lattice customization, continuation, cache, workspace, artifact, and failure coverage. |
| Pytest operation (`AEVAL-015`) | Marker registration and default configuration exclude real-model calls; explicitly gated invocation collects intended tests; disabled hosted cases are reported as not run. |
| Documentation-standard consumers (`AEVAL-016`, `DOCVAL-005`) | Requirement-to-test mapping covers every `DOCGEN-*` and `DOCREP-*` ID; gated runs use narrow cached task-specific bases and clean continuations and preserve exact canonical artifacts. |
| Provenance and interpretation (`AEVAL-017`) | Artifacts identify environment/configuration, instructions, prompts, model, seed, requests, tools, projections, evaluations, presentations, errors, and outputs; AI scores remain supporting evidence and human verification remains pending review. |
| Maintainer documentation (`AEVAL-018`) | README and complete examples let a new author run a simple Crystal Lattice assertion, customize drivers/snapshots/evidence/scoring/presentation, and substitute an alternate environment without reading internals. |
| Post-run calibration (`AEVAL-019`, `DOCVAL-006`) | Representative-run evidence supports a keep/remove/replace/add proposal covering redundancy, cost, variance, diagnostic value, and missing clarity signals; suite changes remain pending explicit user approval. |

### Additional implementation verification

- Compare canonical artifact size and review usefulness with a representative
  current `test/task_guidance` case.
- Verify a cache hit makes no environment execution.
- Verify a continuation never mutates the parent artifact or source snapshot.
- Verify custom Crystal Lattice plugins/configuration can vary instructions
  without changing the kernel.
- Verify an alternate environment can omit Crystal Lattice-specific lower
  operations.
- Run `git diff --check`, package lint/type checks, and package-local tests.
- If real-model tests run, record provider/model and exact gate used.