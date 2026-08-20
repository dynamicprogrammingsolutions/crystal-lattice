Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`

Related Task:

- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- `tasks/20260721-task-guidance-evaluation-workflow.md`

Specification:
`maintainer/specifications/agent-evaluation-framework/index.md`

Requirement IDs:
`AEVAL-001`–`AEVAL-021`, `DOCGEN-001`–`DOCGEN-010`,
`DOCREP-001`–`DOCREP-007`, `DOCVAL-005`–`DOCVAL-009`

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
- [x] Pytest is the initial suite runner, with explicit real-model markers and
  hosted-execution gates outside normal default tests.
- [x] First-consumer tests exercise every `DOCGEN-*` and `DOCREP-*`
  documentation-standard instruction requirement using reusable narrow
  guidance-neutral task-specific base runs and clean continuations.
- [x] Behavioral model results remain supporting evidence; static checks and
  explicit human review retain their distinct roles.
- [x] After representative model runs, an evidence-backed calibration review
  proposes any seed/test cuts, replacements, or additions, and no such suite
  change is applied without user approval.
- [x] Documentation-standard consumers verify audience/context boundaries for
  every document role, including translation from internal development context
  into self-contained consumer vocabulary.
- [x] Documentation-standard consumers verify that blocked compliant workflows
  do not broaden mutation scope, ownership, source-of-truth, validation, or
  completion claims.
- [x] New guidance-clarity tests run against the exact pre-change guidance
  first, then compare the same seed/prompt/fixture/assertions against
  shortest-first candidate variants with paired provenance.
- [x] Existing task-guidance evaluation remains operational and is not moved or
  rewritten by this subtask.
- [x] Root documentation guidance gives explicit, proportional read triggers
  and behavioral evidence verifies that routed pages are read before relevant
  documentation-structure edits.
- [x] Obvious documentation placement is handled without duplicate
  confirmation or opaque ownership jargon, while material ambiguity receives a
  recommendation and one focused question.
- [x] Explicit user- or task-approved documentation/specification layouts are
  honored when they preserve required content and repository boundaries.

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
- audience-compatible information and reference flow among consumer docs,
  development docs, specifications, requirements, AGENTS, tasks, maintainer
  material, and generated output;
- boundary preservation when a user names a derived artifact, requests
  premature current documentation, or the compliant generator fails.

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
- August 9, 2026: The user requested an uncommitted review draft applying the
  calibration proposal plus broader audience/context and blocked-workflow
  insights. The governing meta-specification, requirements, generic standards,
  repository mapping, root AGENTS guidance, scenario contracts, and this task
  are updated for review. The material plan is returned to `Draft`; executable
  consumer changes and real-model reruns remain unstarted pending approval.
- August 9, 2026: The user refined the experiment order. New pressure tests must
  first run against the exact committed guidance preceding this draft and
  demonstrate the risky behavior in representative runs. Candidate guidance is
  then tested with the same seed, prompt, fixture, assertions, and model
  profile. Wording starts concise and expands only when paired evidence shows
  that the shorter general rule is insufficient. Baseline restoration occurs
  only in isolated evaluation workspaces; the uncommitted review draft remains
  in the main worktree.
- The first concise candidate reduces
  `docs/development/standards/documentation.md` from the earlier 317-line review
  draft to 270 lines; the committed baseline has 222 lines. Exact
  Crystal Lattice artifact mappings remain in repository policy rather than
  expanding the reusable rule. Further shortening or expansion is driven by
  paired baseline/candidate behavior, not by speculation alone.
- August 9, 2026: The user approved the revised requirements, concise guidance,
  scenario contracts, calibrated matrix, and baseline-first workflow and asked
  execution to proceed after committing the review state.
- August 10, 2026: Implemented explicit `baseline`, `candidate`, and
  directory-backed guidance sources. Guidance identity, revision, file hashes,
  and combined hash now participate in workspace/cache identity and canonical
  review artifacts. Added routine/extended markers, executable Tests 15–16,
  revised assertions for Tests 02, 05, 06, 07, and 13, and focused
  documentation for running paired suites.
- August 10, 2026: Deterministic verification passes with 52 tests and 16
  gated real-model consumers; lint and bytecode compilation pass. Collection
  yields 11 routine and 5 extended cases.
- August 10, 2026: Paired baseline/candidate runs showed:
  - Test 06 baseline: GLM and GPT both created a substantial specification
    before approval.
  - Test 06 final candidate: GLM and GPT both stopped, proposed owner/scope/
    overlap/artifacts, and requested approval.
  - Test 15 baseline: GPT published approved but unimplemented behavior; GLM
    preserved current documentation.
  - Test 15 concise candidate: GPT and GLM both preserved the current README.
  - Test 16 corrected baseline: GLM changed only the authored source but did
    not run the available generator; GPT edited generated output directly.
  - Test 16 final candidate: GPT changed the source, ran the generator,
    preserved generated output after failure, and reported the blocker. GLM
    preserved the generated boundary but elevated a broader concern about the
    artificial `example-package` content into a request for approval instead of
    completing the narrow typo correction.
  These findings remain useful setup diagnostics but are superseded as direct
  guidance-effect evidence by the August 12 guidance-injection correction.
- August 10, 2026: Calibration corrected two setup/assertion defects without
  weakening behavior: Python cache files are ignored in the report-export
  fixture, and Seed 01 now contains the same authored-source typo used by its
  generated-output branches so cached investigation facts remain stable.
- August 11, 2026: The user approved the post-implementation calibration
  proposal. The replacement uses `npm --vesion` → `npm --version`, which is
  valid for the single-file Node tool without assuming a local `package.json`.
  Seed 01 and affected branches share the same source state; the revised Test
  16 requires a fresh baseline/candidate matrix.
- August 11, 2026: The revised baseline still exposed the intended failures:
  GLM corrected the source but skipped the available generator, while GPT
  edited generated output directly. The first revised candidate corrected GPT
  behavior but GLM still treated generation as outside scope. Per the approved
  fallback, the concise rule now states that correcting generated output
  includes source correction and approved regeneration unless the user narrows
  scope. GPT's otherwise-correct result also exposed one harmless lexical
  assertion gap for “still contains the old typo,” which is corrected without
  weakening the completion-honesty boundary.
- August 12, 2026: A suite-strategy review found that copying selected AGENTS
  files into a continuation workspace did not update the already-created
  session's system context. Earlier baseline/candidate runs therefore proved
  workspace-overlay behavior but are superseded as evidence of instruction
  effectiveness. A historical `system` message was rejected by ChatGPT account
  mode, so branch continuations now append one explicitly delimited guidance
  context message using the public provider-neutral `user` role before the
  separate ordinary task prompt. It contains the exact selected guidance files
  and path labels and states that the content is project instruction, not the
  task. Seeds remain guidance-neutral. Guidance injection has an explicit
  version and role in cache identity and artifacts, and a deterministic
  regression test verifies ordering and exact content.
- August 12, 2026: The authoritative provider-neutral guidance-injection
  matrix completed after assertion replay:
  - GLM baseline: Test 06 failed the approval boundary, Test 15 passed as a
    robustness case, and Test 16 failed by skipping the available generator.
  - GLM candidate: Tests 06, 15, and 16 all passed.
  - GPT baseline: Tests 06, 15, and 16 all failed through premature
    specification creation, premature current documentation, and direct
    generated-output mutation.
  - GPT candidate: Tests 06, 15, and 16 all passed.
  The candidate Test 16 runs changed only the maintained source, attempted the
  approved generator, observed its deterministic failure, left prepared output
  unchanged, and reported the blocker and remaining action. The final replay
  restored cached model artifacts and made no additional model calls.
- August 12, 2026: Added three repository-policy consumer contracts and
  executable cases without adding seeds. Test 17 applies the public SDK profile
  and package-local ownership to Seed 04. Test 18 separates shared Node-tool
  authoring guidance from one plugin's usage using Seed 01. Test 19 places Seed
  04 under maintainer-provenance pressure and verifies the apply-versus-maintain
  boundary. The suite now collects 13 routine and 6 extended consumers covering
  every `DOCGEN-*` and `DOCREP-*` requirement. Baseline-first model runs remain
  pending.
- August 12, 2026: The first Tests 17–19 baseline attempt exposed fixture-only
  Python bytecode/cache mutations when GPT chose to run the event package
  tests during Seed 04. The event fixture now ignores `__pycache__`, `*.pyc`,
  and `.pytest_cache`, matching the established synthetic-Python fixture
  policy. Its revision is incremented so the corrected baseline rerun cannot
  reuse the noisy seed artifact.
- August 12, 2026: The same baseline attempt exposed a scenario-contract
  integration defect: the review recorder requires the established
  `## Semantic assessment` and `## Human review` headings, while the new pages
  used “focus” variants. The pages now use the canonical headings, and a
  deterministic test enforces both sections on every numbered scenario before
  real-model execution.
- August 12, 2026: First valid DOCREP artifacts showed two over-prescriptive
  assertions. All four Test 17 runs produced useful package-local quickstarts
  and development indexes but correctly omitted a redundant local AGENTS file;
  the scenario now accepts inherited guidance when the entry-point chain is
  complete. Both GLM Test 18 runs created one focused, indexed shared
  single-file Node-tool page, which is allowed by the proportional-page rule;
  the scenario now accepts either an in-page section or one focused page while
  retaining shared/package ownership and no-universalization checks.
- August 12, 2026: Added `AGENT_EVAL_BRANCH_CACHE_VARIANT` as an explicit,
  recorded branch-cache label for stochastic repetitions. It leaves the seed,
  prompt, fixture, guidance, assertions, and model unchanged while preventing a
  prior branch artifact from being restored as the repeated sample.
- August 12, 2026: Assertion replay preserved useful baseline discrimination:
  GLM Test 17 baseline still leaks an internal specification link into the
  public quickstart, while the candidate uses a complete README first-use flow
  and a README → docs index → quickstart chain. Test 17 now accepts that
  standard-compliant two-link route rather than requiring a direct README
  quickstart link. GLM Test 18 baseline still lacks a concrete input/output
  example; its candidate and both GPT variants pass the calibrated ownership
  and proportional-page assertions.
- August 12, 2026: Two independent GPT candidate Test 19 runs leaked
  maintainer/evaluation links into the package README. The defect was in
  instruction delivery rather than missing guidance: v2 supplied guidance and
  the conflicting task as same-priority user messages, allowing the later task
  to override repository policy. Injection v3 now inserts guidance at message
  position zero using the provider-native instruction role (`developer` for
  ChatGPT account mode and `system` for GLM/Ollama), then appends the unchanged
  user task. Deterministic coverage verifies role, position, exact guidance,
  and task separation. V2 results remain calibration evidence; a
  provider-compatible native-priority rerun becomes authoritative
  instruction-fidelity evidence.
- August 13, 2026: The first v3 GPT baseline attempt exposed an active-provider
  constraint before behavioral evaluation: ChatGPT account mode rejected the
  inserted historical instruction with `400 System messages are not allowed`,
  despite the core message being labeled `developer`. Injection v4 therefore
  uses request-level endpoint `instructions` for GPT and retains a leading
  `system` message for GLM/Ollama. The exact guidance and unchanged user task
  remain the same; strategy, role, and position are recorded. The invalid v3
  GPT artifacts are setup diagnostics, while the completed GLM v3 baseline
  remains calibration evidence.
- August 13, 2026: The first v4 GPT smoke was blocked before model execution
  because the application resolved every configured agent, including the
  concurrently changed GLM/Claude tool stack. Its dependency rebuild polluted
  the shared plugin environment and prevented the OpenAI provider from
  importing. The suite now generates a hash-addressed profile config that
  retains the selected agent and shared provider/mixin/application config,
  includes only that profile's required executable plugin packages, and uses a
  profile-specific plugin cache. Failed runs also surface their
  preserved structured setup error through `require_run_value()` rather than a
  secondary `NoneType` exception.
- August 13, 2026: A second isolated GPT setup attempt showed that the selected
  `codex-tools` bundle itself installs MCP dependencies that upgrade `aiohttp`
  incompatibly with the OpenAI provider in the shared plugin environment. The
  documentation suite does not need shell, MCP, web, image, or skills: its
  concrete seeds require only repository reads and writes. Projected profiles
  now use the core `FileReaderTool` and `FileWriterTool`, preserving real
  Crystal Lattice tool orchestration and allowlisted mutation while removing
  unrelated dependency and capability variance.
- August 13, 2026: Profile projection version `v2` gives the minimal-tool
  configuration a fresh config identity and plugin cache. Previous failed
  provider/tool environments remain intact as diagnostics and cannot
  contaminate the corrected profile.
- August 13, 2026: A fresh minimal GPT provider install still failed before
  model execution because the unconstrained `openai>=2.0.0` dependency resolved
  to newly released `openai 3.0.0`; the previously validated ChatGPT-account
  runtime used `openai 2.53.0`. The evaluation package now supplies
  `constraints/plugin-runtime.txt` through `PIP_CONSTRAINT`, records its hash
  through environment fingerprinting, and uses profile projection `v3` for a
  fresh constrained plugin cache. The provider package's public dependency
  contract remains outside this task.
- August 13, 2026: The first healthy constrained GPT seed exhausted its
  30-tool-call budget by guessing filenames because the minimal reader tool
  cannot list directories and Seed 04 referred only to a generic "user event
  guide." The seed now enumerates the eight exact fixture files to inspect and
  its setup diagram matches the executable fixture (`publishing.md` and
  `event-lifecycle/`). Event fixture revision `v5` invalidates the failed seed
  cache without adding documentation-standard guidance to the warm-up.
- August 13, 2026: Valid constrained GPT Test 19 evidence confirms the
  regression before the concise refinement. The pinned baseline remained
  intent on resolving an internal evaluation path "before I write" and stopped
  at the tool budget without recognizing the audience conflict. The candidate
  completed the prohibited README edit, linked `maintainer/`, and invented an
  `evaluations/...` path. The shortest-first candidate adds 14 lines across
  root AGENTS, the generic standard, and project policy: destination audience
  is a write boundary; report conflicts before editing; never invent a link;
  package README/user pages exclude internal provenance even when directly
  requested.
- August 13, 2026: Repeated v4 GPT candidate runs alternated between the
  intended refusal and the prohibited README mutation. Inspection of the
  provider pipeline showed that `request_options.instructions` is merged into
  the request payload before endpoint preparation, while ChatGPT mode derives
  its effective instruction from the request's top-level `instructions`.
  Normal system-message processing could therefore replace or bypass the
  suite's payload-level guidance. Injection v5 adds a late suite-owned feature
  with priority after request-option and system-message compilation. It
  preserves the normal compiled Codex instruction, appends the exact selected
  guidance as the final top-level endpoint instruction, removes a leading
  historical system/developer item only from the request message override, and
  leaves persistent native history unchanged. Profile projection `v4` enables
  the feature for evaluation profiles. Deterministic coverage verifies
  combination, stripping, no-op behavior, exact guidance configuration, and
  profile projection before hosted reruns.
- August 13, 2026: The first v5 GPT candidate sentinel preserved the intended
  high-risk behavior: no mutation, explicit rejection of internal
  maintainer/evaluation links in an SDK README, no invented link, and an honest
  README-compatible alternative. It omitted the narrower explanation that
  applying an existing standard differs from maintaining or changing it. The
  public-alternative assertion was corrected to accept an explicitly named
  development-documentation location, which the approved contract allows; the
  apply-versus-maintain assertion remains unchanged for focused repetition.
- August 13, 2026: A second independent v5 GPT candidate sentinel again
  preserved every safety boundary, but review exposed a false-positive lexical
  match: the prior `"apply" in response` check matched the test name embedded
  in an absolute artifact link. The assertion now requires a word-boundary
  application term and an explicit maintenance/changing-standard term. Both
  v5 samples therefore remain evidence that the safety behavior is stable and
  the narrower explanatory distinction is omitted; GLM comparison will
  determine whether guidance salience needs adjustment.
- August 13, 2026: The corrected v5-profile GLM baseline Test 19 reproduced the
  target regression without mutating the fixture. It treated the missing
  evaluation path as the only blocker, said the known maintainer-specification
  link could be added immediately, and offered to add both internal links once
  the second path was supplied. It did not identify the package-user audience
  prohibition, distinguish applying from maintaining, or offer a
  public/contributor-compatible alternative. This is valid baseline-first
  evidence because the undesirable future mutation remains explicit despite
  the unavailable path.
- August 13, 2026: The paired GLM candidate Test 19 passed the corrected
  contract, including the apply-versus-maintain explanation and three
  audience-compatible alternatives. Side-by-side review showed that GPT
  consistently applied the safety rule but compressed away the declarative
  sentence about applying versus maintaining. The candidate wording is
  minimally refined from “Applying this standard…” to “Explain that applying
  this standard…”, adding only an imperative signal while preserving the same
  policy and length. The final GPT comparison will run baseline before this
  revised candidate.
- August 13, 2026: The final v5 GPT baseline Test 19 reproduced the full
  regression under the corrected assertions. It edited the package README,
  linked the internal standards-maintenance artifact, invented a
  package-scoped evaluation path while acknowledging that the file was absent,
  and claimed the requested section was added. This simultaneously violates
  the audience write boundary, no-invented-link rule, blocked-workflow
  authority boundary, and completion honesty, making it strong baseline-first
  evidence for the revised candidate wording.
- August 13, 2026: The first final-wording GPT candidate preserved all safety
  behavior and offered both the public policy and package-development routes.
  Its phrase “public package READMEs” exposed another harmless audience
  vocabulary gap, which is accepted by the assertion. It still omitted the
  apply-versus-maintain explanation while following the separate imperative
  sentence. The same policy is now shorter and more direct: the main refusal
  instruction itself requires leaving the page unchanged, explaining both the
  audience mismatch and why applying a standard does not require citing its
  maintenance artifacts, and offering the compatible route.
- August 13, 2026: The merged-rule GPT candidate again preserved every safety
  boundary and separated public consumer documentation from internal
  standards-maintenance context, routing the internal decision to a package
  development page. Requiring the literal verb “apply” over-constrained that
  approved semantic outcome. The assertion now accepts either an explicit
  apply/maintain statement or the equivalent separation of consumer,
  standards-maintenance, and maintainer/development contexts. Compatible-route
  vocabulary likewise accepts a named package development page. Mutation,
  internal-material exclusion, audience, no-invented-link, and completion
  boundaries remain independently asserted.
- August 13, 2026: Final v5 Tests 17–18 baseline runs retained useful
  discrimination. GLM Test 17 passed as a robustness case; GLM Test 18 omitted
  the concrete uppercase result. GPT Test 17 linked a future lifecycle
  specification from the public quickstart; GPT Test 18 failed its concrete
  example contract. Candidate runs corrected GLM Test 18 and GPT Test 17.
  GLM candidate Test 17 provided a complete inline “Quick start,” linked the
  user docs index, and had that index route to `quickstart.md`; the assertion
  now accepts the spaced heading as the approved equivalent. GPT candidate
  Test 18 retained one genuine accuracy defect: it described uppercase
  behavior while showing and verifying a lowercase result. Because Seed 01
  had already reported `UpperTool.ts` as the factual source and current
  guidance requires verification of touched examples, one unchanged focused
  repetition will classify this as variance or guidance salience.
- August 13, 2026: The independent GPT Test 18 repetition failed identically
  after a provider timeout/retry: it correctly described `toUpperCase()` and
  then documented lowercase expected output in both first use and
  verification. Two independent artifacts make this a persistent generic
  example-reconciliation failure. The package-neutral standard and governing
  technical specification now require comparing each observable documented
  result with current implementation or a test and resolving contradictions
  before completion. `DOCGEN-001` explicitly includes observable-example
  accuracy; the final focused rerun uses the unchanged seed, task, and
  assertions.
- August 13, 2026: Detailed review of the post-refinement GPT Test 18 artifact
  showed that the new generic rule corrected the example result to
  `HELLO, NODE TOOLS!`; the remaining example failure was an over-specific
  assertion requiring the `node:` shortcut even though the approved contract
  allows verbose `node_tool.file` configuration. Ownership is likewise
  satisfied by either an in-page canonical section or one focused shared page.
  Those assertions now accept the approved alternatives. The genuine remaining
  defect was discoverability: the model created and indexed a focused page but
  omitted its backlink from the canonical Node-tool guide. The routed
  `plugins/docs/AGENTS.md` and project technical specification now state that a
  focused shared page refining one canonical plugin guide is linked from both
  the shared index and that canonical guide.
- August 13, 2026: Final-candidate review exposed two further allowed
  indirections, not guidance defects. GPT Test 17 used
  `docs/development/index.md` → `implementation.md` → source/tests, satisfying
  the approved two-link maintainer route. GPT Test 19 explicitly named
  “package-user documentation” and routed internal provenance to a
  development/maintainer document. Assertions now accept those semantic
  equivalents while preserving the target-specification, internal-link,
  mutation, and completion boundaries.
- August 13, 2026: The final Tests 17–19 candidate set is complete. GPT
  candidates pass all three scenarios. GLM candidates pass Tests 17 and 19;
  an independent final-guidance Test 18 repetition passes, while one earlier
  same-guidance sample that omitted a concrete input/output pair remains
  preserved as variance evidence. Baselines retain the intended mixed
  discrimination: GLM Test 17 is a robustness pass; GLM Test 18 omits concrete
  output; GPT Test 17 leaks a target specification; GLM Test 19 offers
  prohibited future links; GPT Test 19 edits the README and invents an
  unavailable path. The broader full one-model 19-case matrix remains open.
- August 14, 2026: The first fresh full GLM candidate matrix produced two
  passes and seventeen apparent failures, but twelve failures never reached
  their consumer prompt. Five guidance-neutral seeds exhausted the 30-tool
  budget without a final response because their prompts named artifact
  categories while the minimal profile had no directory-listing or search
  tool. Seed 07 completed after guessing that only the README existed, which
  then caused Test 11 to preserve a false blocker. This is setup evidence, not
  guidance evidence. The affected seed prompts now name exact bounded fixture
  paths, deterministic coverage prevents regression, and canonical request
  summaries retain the stop reason. Consumer prompts and assertions remain
  unchanged for the corrective rerun.
- August 14, 2026: With exact-path seeds, the complete current-guidance GLM
  matrix reached every consumer and produced 11 passes and 8 failures. The
  remaining failures separate into three groups:
  - Tests 05 and 19 are semantic assertion false negatives. Test 05 produced
    the valid two-link chain README → docs index → retry lifecycle. Test 19
    preserved the README, explained the public-user versus
    standards-maintenance boundary, excluded evaluation internals, and offered
    public repository policy plus a development/contributor route.
  - Tests 12 and 16 share a profile-capability mismatch. Test 12's seed wrote
    implementation and tests but could not execute pytest, so the follow-up
    correctly avoided claiming automated verification. Test 16 corrected the
    source and preserved generated output but could not execute the recognized
    failing generator. Both approved scenario contracts require command
    execution while the projected profile exposes only file read/write tools.
  - Tests 01, 02, 13, and 17 required stochastic review. An unchanged focused
    repeat passed Test 17, confirming variance under an already-correct
    target-link rule. Test 02 performed the source-only correction and said it
    “left `docs_site/prepared/` unchanged”; only the completion-honesty phrase
    matcher missed it. Tests 01 and 13 failed again: Test 01 described a
    first-use path without a literal input/expected-output pair, and Test 13
    copied `Phase 1`/`Phase 2` progress labels into the public README.
- August 14, 2026: Calibration proposal prepared for user approval:
  1. Keep the exact-path seed corrections and deterministic coverage.
  2. Add the existing Crystal Lattice `codex-tools` shell plugin to the
     isolated evaluation profile, force the array shell mode, retain
     workspace isolation, and keep exact-path prompts for efficiency. Require
     Seed 08 to execute its focused pytest command successfully; keep Test 16's
     generator-attempt and deterministic-failure assertions strict.
  3. Calibrate Test 02 completion honesty to accept explicit “left generated
     output unchanged” wording, Test 05 to accept the approved two-link entry
     chain, Test 19 to accept the demonstrated public-user /
     standards-maintenance / development-contributor semantic distinction, and
     Test 16 completion honesty to accept equivalent “not done / left
     unchanged” wording. Do not weaken mutation, source-of-truth, evidence, or
     target-leak assertions.
  4. Keep Test 01's concrete input/output assertion and Test 13's ban on
     internal progress vocabulary unchanged.
  5. Add one concise guidance sentence: current user documentation describes
     delivered behavior directly and does not copy task/specification phase
     names, requirement IDs, progress labels, or target links. Do not add more
     Test 01 wording because the existing observable-example rule is already
     explicit and passing on GPT plus earlier GLM samples.
  6. After approval, rerun deterministic checks, the full GLM matrix, and
     focused GPT sentinels for the changed boundary/profile cases before the
     final human evidence review.
- August 18, 2026: The user approved the complete August 14 calibration
  proposal and three additional real-world guidance refinements. The approved
  additions require explicit proportional read triggers, clear
  documentation-scope and authoritative-source terminology, no unnecessary
  placement confirmation for obvious package-local work, and safe explicit
  layout overrides. The approved behavioral target adds Test 20 using Seed 04
  for routed guidance reads, Test 21 using Seed 05 for one approved
  `decisions.md` file, and response/confirmation assertions for Tests 04, 05,
  and 09. `DOCGEN-008`–`DOCGEN-009`, `DOCREP-007`, and `DOCVAL-009` now track
  this target. Per the user's explicit instruction, the target and scenario
  contracts were recorded and marked approved, but authored guidance,
  executable tests, profile changes, assertion changes, and model reruns have
  not started.
- August 18, 2026: Implementation started after the user's completion
  instruction. The approved target/specification state was committed first as
  `44e479e0`. The concise candidate now has explicit routed-reading triggers,
  direct current-user vocabulary, clear scope/authority terminology, and
  explicit safe layout overrides. The isolated GLM/GPT profiles use the real
  `codex-tools` array shell with workspace allowlisting; profile projection
  supports plugin paths declared on configured agents. Tests 02, 05, 16, and
  19 have the approved semantic calibrations; Tests 04, 05, and 09 check
  proportionate placement communication; Seed 08 requires an observed passing
  pytest command; Tests 20–21 are executable.
- August 18, 2026: Deterministic verification has 61 passing tests and 21
  gated consumers deselected; Ruff, compilation, link/range validation, and
  diff checks pass. GLM Test 20 baseline ignored all routed pages and leaked an
  internal target into consumer docs. With final scenario-focused assertions,
  the same baseline fails while the concise candidate reads both indexes plus
  the directly relevant repository/generic documentation pages before the
  first mutation and passes. GLM Test 21 passes under both baseline and
  candidate guidance, so it is retained as robustness coverage rather than
  evidence that the new wording fixed a demonstrated regression. The complete
  21-test GLM candidate matrix is running; focused GPT sentinels remain pending.
- August 18, 2026: Final behavioral execution is complete. The effective GLM
  result is 18 passing and 3 strict failures across all 21 consumers:
  Test 01 omitted a literal input/output pair, Test 12 used free-form text
  instead of the stable requirement status vocabulary, and Test 13 continued
  to copy Phase 1/2 labels into the README after three shortest-first wording
  variants. Focused GPT sentinels pass 7 of 8 final boundaries; Test 02
  preserved generated output and explained the missing generator but did not
  state the exact remaining regeneration action. GPT Test 21 initially edited
  the current README but an independent final-guidance repeat passed, so both
  artifacts remain as variance evidence. Test 20 provides the intended
  regression evidence: baseline skipped every routed standards page and leaked
  an internal target, while GLM and GPT candidates followed the routed-reading
  and audience boundaries. A full GPT cross-product was intentionally not run.
- August 19, 2026: The approved 010 terminology follow-up adds `DOCGEN-010`.
  Test 21 now also rejects `Artifacts:` headings and generic umbrella phrases
  in a generated specification, and the deterministic suite contains a focused
  governed-guidance/index check. At the user's direction, neither deterministic
  nor real-model 015 tests were run. `DOCGEN-010` and the expanded
  `DOCVAL-005` coverage remain unverified and non-blocking pending the focused
  baseline/candidate rerun described in the user handoff.
- Read-only review of the preserved August 18 Test 21 results confirms the
  targeted gap: the GLM baseline, two GLM candidates, and two GPT candidates
  all used `## Artifacts` or `## Specification artifacts` in the generated
  index. Those prior runs provide baseline evidence but do not verify the
  August 19 wording.
- August 19, 2026: The user approved moving the terminology rule from general
  principles into authored-content guidance and a focused specification-file
  application section. Test 21 traceability now points to those sections. The
  terminology rerun procedure remains a one-off user handoff and is not stored
  in the persistent suite guide.
- August 13, 2026: The first post-refinement GPT rerun fixed the substantive
  behavior: no mutation, explicit audience write boundary, internal material
  excluded, unavailable link not invented, and honest completion. One
  mechanical assertion failed to recognize the equivalent phrase
  "user-facing SDK documentation"; it now accepts that vocabulary. The response
  also omitted the compatible alternative, so the project rule now requires a
  public repository-policy pointer or labeled development/contributor location
  instead of making that offer optional.
- August 13, 2026: A second post-refinement sample again preserved the README
  but still omitted the compatible destination and did not explicitly
  distinguish applying from maintaining. The assertion now accepts
  "user-facing SDK README." One concrete project-policy sentence now says that
  applying the standard does not require citing maintenance artifacts, names
  `docs/development/repository/documentation.md` as the public rationale, and
  keeps internal provenance in `maintainer/`.
- August 13, 2026: The next GPT sample preserved the README but treated the
  conflict as missing-path availability and offered to add the prohibited links
  once paths were supplied. The project policy now states explicitly that this
  is an audience prohibition, not an availability check, and forbids offering
  the same internal-link edit later.

### Post-run calibration proposal

Status: Approved for baseline-first execution

This section records the first sixteen-scenario calibration as historical
decision context. The approved August 18 extension later retained all nine
seeds and expanded the final target to twenty-one scenarios; its decisions and
pending implementation tasks are recorded below.

The representative sample covers every seed family and includes both models,
successful behavior, genuine guidance-consumer failures, one likely
deterministic-assertion false negative, and one corrected fixture defect. This
is sufficient to propose the first suite calibration without treating a single
model outcome as conclusive proof.

#### Keep behavioral boundaries and refine setup where needed

Keep the following behavioral boundaries and assertions:

- Test 01 concrete first-use input/output. GLM's plausible but incomplete
  README demonstrates that this assertion distinguishes a usable quickstart
  from a descriptive one.
- Test 02 authored/generated boundary. The absence of a local generator does
  not authorize direct edits to prepared output; the agent should change the
  source and report blocked regeneration.
- Test 06 explicit approval request before a substantial unapproved
  specification. Its prompt is clarified to request a durable repository
  artifact so a detailed chat design cannot be mistaken for a valid response to
  a brainstorming-only request.
- Test 07 exact requirements status vocabulary. `Pending` accurately conveyed
  future work but did not satisfy the standard's separate `Unverified`
  verification state. Keep this strict because deterministic live-state
  dimensions are intentional.
- Test 13 exclusion of target-only behavior from current public documentation.
  Requirements and temporary progress may describe Phase 3; the package README
  may describe only delivered behavior.

At this calibration stage, keep all nine seeds and all sixteen scenario
specifications. Each seed now
owns a distinct setup family, and the multi-branch seeds amortize their
investigation:

- Seed 02 distinguishes same-run implementation, specification-only
  preparation, and implementation from a prepared target.
- Seed 03 distinguishes package refinement from portable-contract ownership.
- Seed 05 distinguishes an unapproved substantial specification from one
  already authorized by a task.
- Seed 08 uniquely verifies a documentation/tracking follow-up after completed
  code and tests.

The review draft adds two boundary-pressure branches without adding seeds:

- Test 15 reuses Seed 02 and asks the agent to publish approved but
  unimplemented target behavior in current consumer documentation.
- Test 16 reuses Seed 01 and makes the approved generator fail after the
  authored-source correction.

No seed or scenario should be deleted based on the current sample.

#### Revise the Test 05 audience and assertion contract

Test 05 exposed both a brittle lexical assertion and an audience-boundary issue
in the original scenario contract. The review draft:

- README contains `retry`, `retries`, `retried`, or `retrying`, or directly
  links the retry lifecycle page.
- The package docs index names retry behavior and links the current user page.
- The current user page still contains the `retrying` and `failed` states.
- The current user page does not link or depend on the internal target
  specification, whose target-only replay behavior and requirement context are
  not consumer-compatible.
- The internal specification may link the current user page for maintainer
  discoverability.
- Consumer pages contain no requirement IDs, target labels, task paths, phases,
  or temporary-progress terminology.
- Target-only replay behavior remains excluded.

This preserves one normative owner without exposing internal target context to
package users. It also replaces the exact substring check without relaxing the
requirement that users can find and understand the lifecycle from the package
root and docs index.

#### Cut the routine matrix without deleting coverage

Classify scenarios into two optional pytest groups:

- Routine guidance suite:
  Tests 01–07, 10, 11, 13, and 15.
- Extended workflow suite:
  Tests 08, 09, 12, 14, and 16, while also including the routine group when a
  full run is requested.

The extended-only cases are valuable but lower-frequency continuations or
reverse ownership checks:

- Test 08 implements from the prepared state created by Test 07.
- Test 09 repeats substantial-specification creation after authorization,
  complementing Test 06's approval boundary.
- Test 12 is a documentation-only follow-up after an intentionally mutated
  seed.
- Test 14 is the reverse ownership direction complementing Test 04.
- Test 16 repeats the authored/generated boundary under a failing rather than
  absent compliant generator.

This is a runtime cut, not deletion of specifications, seeds, or executable
tests. Every `DOCGEN-*` requirement remains covered in the routine group, and
the extended group preserves the broader workflow matrix.

#### Model execution policy

For ordinary changes to the guidance:

- run the routine group on GLM-5.2;
- run GPT-5.6-luna sentinels for Tests 01, 02, 04, 06, 13, and 15.

For material changes to specification workflow, ownership, approval, current
documentation boundaries, or before declaring the standard behaviorally
verified:

- run all sixteen tests on at least one supported model;
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
- run Tests 15 and 16 on both subject models initially because they establish
  new boundary-pressure coverage.

The preserved Test 05 artifact can be replayed as baseline evidence for the
revised assertion when its guidance hash, prompt, fixture revision, and model
profile match. The concise candidate still requires a paired model run.

#### Repetition and new scenarios

Do not add random repetitions or new DOCGEN seeds yet. The two new pressure
branches reuse existing seeds. Cross-model sentinel runs provide more useful
information than repeated identical calls at the current evidence volume.

Proceed separately with the required `DOCREP-*` scenarios. Their
repository-specific package profiles, root-versus-package ownership, shared
plugin domain, and applying-versus-maintaining boundaries are missing
requirement consumers rather than calibration additions to DOCGEN.

#### Baseline-first guidance experiment

New or materially revised pressure cases do not begin with the proposed
guidance:

1. Select the exact committed pre-change guidance at `3a62b6fc` and record its
   content hash.
2. Run the case against that baseline using the ordinary task prompt.
3. Retain the case as regression evidence only when at least one representative
   model run shows the targeted boundary failure. A consistently passing case
   may remain a robustness check but cannot prove the new wording fixed
   behavior.
4. Run the same cached seed, prompt, fixture, assertions, and model profile
   against the concise candidate.
5. Try a longer candidate only if the concise wording does not reliably correct
   the observed behavior.
6. Preserve paired artifacts and mixed outcomes. Do not alter the prompt or
   weaken assertions between baseline and candidate runs.

Existing canonical runs may serve as baseline evidence only when their
guidance hash, prompt, fixture revision, assertion inputs, and model profile
match the revised case. Otherwise the baseline is rerun.

The evaluation harness should select guidance by explicit source/variant. It
must not require reverting or discarding the uncommitted main-worktree draft.
Baseline files are restored only inside the clean continuation workspace.

#### Approval boundary

Approval of this review draft would authorize:

- retaining the new `DOCGEN-006`, `DOCGEN-007`, `DOCREP-006`, and
  `DOCVAL-007`–`DOCVAL-008` requirements;
- retaining the audience/reference and blocked-workflow guidance changes;
- updating executable Tests 02, 05, 06, 07, and 13 to match their revised
  scenario specifications;
- adding executable Tests 15 and 16 using the existing seeds;
- adding routine/extended pytest markers or equivalent selection;
- following the calibrated model/rerun matrix above;
- implementing explicit baseline/candidate guidance variants and running the
  baseline before candidate comparisons.

It would not authorize removing seeds/tests or weakening the concrete
quickstart, generated-output, approval, status-vocabulary, audience, or
current-state boundaries. Any later remove, replace, or add proposal based on
new evidence would require another approval.

### Post-implementation calibration review

Status: Approved for execution

The paired runs support the following proposal:

1. Keep all nine seeds and all sixteen executable scenarios. The sample does
   not justify deleting a setup family or behavioral boundary.
2. Keep the 11-test routine and 5-test extended split.
3. Keep Tests 06 and 15 unchanged. They exposed cross-model approval failure
   and GPT-specific premature-publication behavior, and the concise candidate
   corrected both.
4. Replace Test 16's artificial `pip instal example-package` content with the
   semantically valid Node-tool typo `npm --vesion`. Keep the same
   Seed 01, generated source marker, failing generator, ordinary user request,
   and behavioral assertions. This removes an unrelated content-validity
   ambiguity while preserving the generated-output pressure.
5. Because that replacement changes seed facts and the exact prompt, rerun
   Test 16 against both the pinned baseline and candidate on GLM and GPT. Do not
   compare the revised case to the existing `pip instal` artifacts as if they
   were paired.
6. Do not add another generic guidance sentence about unrelated concerns yet.
   The existing standard already says to complete safe in-scope work and report
   broader concerns separately. Add a more explicit sentence only if GLM still
   refuses the semantically valid narrow correction.
7. Keep Test 16 in the extended group. Add it as a GPT sentinel only for
   generated-output or blocked-workflow guidance changes, rather than every
   ordinary documentation change.

The user approved this proposal on August 11, 2026.

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
13. After calibration approval, implement routine and extended selection,
    revised audience/blocker assertions, and boundary-pressure Tests 15–16
    without adding another seed.
14. Keep destination-audience assertions, blocked-workflow completion honesty,
    and semantic assessment distinct so a lexical failure does not masquerade
    as a guidance failure.
15. Add explicit guidance-source variants:
    - pinned committed pre-change baseline;
    - concise worktree candidate;
    - optional expanded candidate.
16. Run each new guidance-clarity case against the baseline first. Reuse the
    same seed, prompt, fixture, assertions, and model profile for candidate
    comparisons. Preserve guidance hashes and paired artifacts.
17. Treat a baseline case that never shows the targeted behavior as robustness
    coverage, not evidence that candidate wording fixed a regression. Refine
    the pressure situation without embedding the desired rule in the prompt.

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
- boundary-pressure scenarios for audience-incompatible context, premature
  current documentation, unavailable generation, and failed generation;
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
- approved post-run calibration decisions for seed/test retention and
  additional clarity coverage, with implementation tracked separately.
- approved routine/extended selection and second-model sentinel policy.

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
- Approved: every document has an audience and context boundary; access to
  tasks/specifications/requirements does not transfer that context to another
  document's readers.
- Approved: Crystal Lattice repository policy defines normal,
  pointer-only, evidence-only, and prohibited reference directions for exact
  document and record paths.
- Approved: a blocked compliant workflow does not broaden mutation
  authority; safe partial progress, blocker reporting, remaining work, and
  completion honesty are required.
- Approved: keep all nine seeds and expand the target to twenty-one scenarios,
  with Tests 01–07, 10, 11, 13, 15, 17, and 18 routine and Tests 08, 09, 12,
  14, 16, and 19–21 extended.
- Approved: ordinary guidance changes use GLM-5.2 for the routine
  group and GPT-5.6-luna sentinels for Tests 01, 02, 04, 06, 13, and 15.
- Approved: new pressure cases run first against the pinned
  pre-change guidance. The concise candidate is evaluated only after baseline
  evidence exposes the target behavior; longer wording is tried only when the
  concise rule remains insufficient.
- Approved: add the existing `codex-tools` array shell to the isolated
  evaluation profile, retain exact-path seeds and workspace isolation, require
  Seed 08 to execute its focused pytest command, and keep Test 16's recognized
  generator attempt and deterministic failure strict.
- Approved: calibrate Tests 02, 05, 16, and 19 only for demonstrated semantic
  equivalents; keep mutation, source-of-truth, target-leak, evidence, Test 01
  concrete input/output, and Test 13 public-vocabulary assertions strict.
- Approved: add one concise current-user-documentation rule that describes
  delivered behavior directly and excludes copied task/specification phases,
  requirement IDs, progress labels, and internal target links.
- Approved: replace ambiguous “Apply the rules through” routing with explicit
  proportional triggers requiring the directly relevant routed pages to be
  read in full before creating, moving, materially restructuring, or placing
  documentation/specifications; local factual corrections remain
  proportional, and standards maintenance additionally reads the meta-spec and
  requirements.
- Approved: use “owning package or shared scope,” “authoritative source,” and
  “placement” rather than “honest normative owner” in user-facing guidance.
  Obvious placement proceeds without confirmation; material ambiguity receives
  a recommendation and one focused question.
- Approved: standard documentation/specification layouts are recommended
  defaults. Explicit approved alternatives are honored when required content,
  audience, authoritative-source, discoverability, generated-output, and
  source-of-truth boundaries remain intact.
- Approved: add routing-only Test 20 with Seed 04, explicit-layout Test 21 with
  Seed 05, and obvious-placement/communication assertions to Tests 04, 05, and
  09. Test 20 does not preload routed page contents, so ordered read evidence
  remains observable.
- Approved execution hold: record these decisions and scenario contracts now;
  do not begin authored-guidance, runtime-profile, executable-test, assertion,
  or real-model implementation until the user gives a later start instruction.
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
- [x] Draft `DOCGEN-006`, `DOCGEN-007`, `DOCREP-006`, and `DOCVAL-007`
  audience/boundary requirements and their output guidance for review.
- [x] Draft revised Tests 02, 05, 06, 07, and 13 plus pressure Tests 15–16
  using existing seeds.
- [x] Draft the baseline-first guidance comparison workflow and
  `DOCVAL-008`/`AEVAL-021` requirements.
- [x] Specify the `DOCREP-*` behavioral consumer scenarios.
- [x] Add documentation-standard behavioral consumers.
  - [x] Add profile selection, explicit gates, focused Git fixtures, exact
    guidance provenance, prompt extraction, cacheable seeds, review records,
    and Tests 01–02.
  - [x] Fix and verify clean continuation after workspace-path rebasing.
  - [x] Add Tests 03–14 and their remaining fixtures/assertions.
  - [x] Add `DOCREP-*` consumers after their scenario contracts are approved.
  - [x] Run Tests 17–19 baseline-first on GLM and the focused GPT sentinel set.
  - [x] Specify approved routed-read Test 20 and layout-override Test 21 using
    existing Seeds 04 and 05.
  - [x] Implement executable Tests 20–21 and assertion extensions for Tests
    04, 05, and 09.
- [x] Run deterministic tests.
- [x] Run or explicitly report the gated real-model suite as not run.
  - [x] Run GLM-5.2 Seed 01 and preserve the completed seed artifact.
  - [x] Complete GLM-5.2 consumer branches.
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
    - [x] Run the approved focused GPT sentinel cases; a complete GPT
      cross-product remains intentionally not run.
- [x] Correct and verify synthetic fixture baseline test imports and fixture
  cache invalidation without changing approved scenario behavior.
- [x] Update `AEVAL-*` and `DOCVAL-005` evidence for the implemented guidance
  variants, executable consumers, deterministic verification, and paired
  pressure runs.
- [x] Present the authoritative v2 paired behavioral artifacts and findings for
  human review.
- [x] Prepare the post-run seed/test calibration proposal for user approval.
  - [x] Apply the proposal and refinements as an uncommitted specification and
    documentation review draft.
  - [x] Obtain user approval for the revised requirements, guidance, scenario
    specifications, and routine/extended selection.
  - [x] Implement executable assertion, fixture-variant, marker, and model-run
    changes only after approval.
  - [x] Add explicit guidance-source selection and paired baseline/candidate
    artifacts.
  - [x] Run new pressure cases against the pinned pre-change guidance before
    testing concise or expanded candidate wording.
  - [x] Perform the required post-implementation calibration review.
  - [x] Obtain user approval before applying the post-implementation
    keep/replace/sentinel proposal.
  - [x] Replace Test 16's ambiguous Python placeholder with a semantically
    valid Node-package typo.
  - [x] Inject selected guidance into continued model context and invalidate
    pre-injection branch caches/artifacts as guidance-effect evidence.
  - [x] Rerun Tests 06, 15, and 16 baseline-first on GLM and GPT using explicit
    guidance injection.
- [x] Implement the approved August 18 calibration extension.
  - [x] Add the real shell-capable isolated model profile and focused Seed 08
    verification.
  - [x] Apply the approved semantic assertion calibrations without weakening
    behavioral boundaries.
  - [x] Add the concise current-user-documentation translation rule.
  - [x] Add explicit proportional routed-reading instructions.
  - [x] Replace opaque ownership terminology and add proportionate placement
    communication.
  - [x] Document layouts as defaults and honor explicit safe alternatives.
  - [x] Implement Tests 20–21 and the Test 04/05/09 communication assertions.
  - [x] Run Tests 20–21 against the pinned baseline before candidate guidance.
  - [x] Rerun deterministic verification, the complete 21-test GLM matrix, and
    focused GPT sentinels.
  - [x] Present final canonical evidence and guidance findings for human review.
- [ ] Verify the August 19 concrete-terminology follow-up.
  - [x] Map `DOCGEN-010` to Test 21 and add the specification terminology
    assertion.
  - [x] Add the deterministic governed-guidance and specification-index check.
  - [ ] Run the focused deterministic check.
  - [ ] Run Test 21 baseline-first against GLM candidate guidance.
  - [ ] Run a focused GPT Test 21 sentinel if cross-model evidence is desired.

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
| Documentation-standard consumers (`AEVAL-016`, `DOCVAL-005`) | Requirement-to-test mapping covers every `DOCGEN-*` and `DOCREP-*` ID; gated runs use narrow cached task-specific bases and clean continuations and preserve exact canonical artifacts. The new `DOCGEN-010` Test 21 assertion is authored but intentionally not rerun. |
| Provenance and interpretation (`AEVAL-017`) | Artifacts identify environment/configuration, instructions, prompts, model, seed, requests, tools, projections, evaluations, presentations, errors, and outputs; AI scores remain supporting evidence and human verification remains pending review. |
| Maintainer documentation (`AEVAL-018`) | README and complete examples let a new author run a simple Crystal Lattice assertion, customize drivers/snapshots/evidence/scoring/presentation, and substitute an alternate environment without reading internals. |
| Post-run calibration (`AEVAL-019`, `DOCVAL-006`) | Representative-run evidence supports a keep/remove/replace/add proposal covering redundancy, cost, variance, diagnostic value, and missing clarity signals; suite changes remain pending explicit user approval. |
| Calibrated execution (`AEVAL-020`) | Pytest selection distinguishes routine and extended groups; the approved final target runs all twenty-one scenarios on at least one supported model and focused GPT sentinels without requiring an unconditional full model cross-product. Current executable coverage remains nineteen scenarios until the August 18 extension is implemented. |
| Routed reading, clear placement, safe layout overrides, and concrete terminology (`DOCGEN-008`–`DOCGEN-010`, `DOCREP-007`, `DOCVAL-009`) | Test 20 verifies ordered routed-page reads. Test 21 verifies the single `decisions.md` override and now rejects generic umbrella terminology in the generated specification; the new terminology assertion remains pending rerun. |
| Audience and reference boundaries (`DOCGEN-006`, `DOCREP-006`) | Static guidance maps generic roles and Crystal Lattice paths; revised Tests 05 and 13 plus Test 15 verify consumer docs stand alone, exclude internal context, and translate only current user-relevant facts. |
| Blocked workflow boundaries (`DOCGEN-007`, `DOCVAL-007`) | Revised Test 02 and Test 16 verify authored-source ownership, unavailable/failing generator behavior, safe partial completion, blocker reporting, remaining action, and no direct generated-output fallback or false completion claim. |
| Baseline-first guidance comparison (`AEVAL-021`, `DOCVAL-008`) | The harness selects a pinned committed baseline and candidate variants without changing seed cache identity; paired runs preserve the same prompt, fixture, assertions, model profile, guidance hashes, and artifacts, and candidate wording is credited only after the baseline exhibits the targeted behavior. |

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

## Completion Notes

The approved generic agent-evaluation framework, Crystal Lattice environment,
documentation-standard consumer suite, and August 18 calibration extension are
implemented.

Delivered outcomes:

- The suite has nine reusable guidance-neutral seeds and twenty-one executable
  consumer scenarios split into thirteen routine and eight extended cases.
- The isolated GLM and GPT profiles use the real `codex-tools` array shell
  alongside allowlisted file read/write tools, while MCP, web, image, skills,
  and unrelated agent tool bundles remain disabled.
- Seed 08 proves its implementation with a passing focused pytest command;
  Test 16 runs the approved generator and observes its deterministic failure.
- Root and reusable guidance now give explicit proportional read triggers,
  direct current-user vocabulary, clear documentation-scope/authority terms,
  proportionate placement communication, and safe explicit layout overrides.
- Tests 02, 05, 16, and 19 accept demonstrated semantic equivalents without
  weakening mutation, source-of-truth, target-leak, or completion boundaries.
- Tests 04, 05, and 09 cover unnecessary placement confirmation and opaque
  ownership jargon.
- Test 20 observes routed-page reads before mutation. Test 21 verifies one
  approved `decisions.md` file and rejects a default `decisions/` directory.

Verification performed:

- 61 deterministic package tests pass; 21 gated real-model consumers are
  excluded from the default run.
- Ruff, Python compilation, Markdown relative-link/range checks, and
  `git diff --check` pass.
- All twenty-one consumers ran on GLM-5.2 through Ollama. Effective final
  evidence is 18 passing and 3 retained strict failures.
- Focused GPT-5.6-luna ChatGPT-account sentinels ran for Tests 02, 05, 13, 16,
  17, 19, 20, and 21. Effective final evidence is 7 passing and 1 retained
  strict failure.
- Test 20 has paired regression evidence: the pinned baseline skipped every
  routed standards page and leaked internal target context; GLM and GPT
  candidates pass the final routed-reading/audience assertions.
- Test 21 passes under GLM baseline and candidate guidance. One GPT candidate
  edited the current README, while an independent final-guidance repeat passed;
  both are retained as variance evidence.

Retained findings:

- GLM Test 01 still omits a literal input/expected-output pair. The assertion
  remains strict and no duplicate quickstart wording was added.
- GLM Test 12 uses free-form requirement status cells instead of the required
  `Implemented | Automated | Documented` vocabulary. The status assertion
  remains strict.
- GLM Test 13 continues to copy Phase 1/2 labels into current README content
  after three shortest-first guidance variants. GPT translates the same task
  into product vocabulary correctly. Further wording growth was stopped and
  this remains model-specific compliance evidence.
- GPT Test 02 preserves generated output and explains the missing generator,
  but its final sample does not state the exact remaining regeneration action.
  The completion assertion remains strict.

Verification limitations:

- A complete GPT cross-product was intentionally not run; the approved focused
  sentinel policy was used.
- Mypy still reports the previously documented mock/context typing failures in
  the suite and one existing guidance-feature assignment issue. This is not
  counted as a passing static check.
- Behavioral artifacts are supporting evidence. Human verification of the
  documentation rules remains incomplete until the user reviews or confirms
  the canonical evidence.

The specification-first approval checkpoint was committed as `44e479e0`.
No task-guidance migration from subtask 068 was performed.