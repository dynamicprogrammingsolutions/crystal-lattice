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
  documentation-standard instruction requirement using a reusable neutral
  repository investigation and clean continuations.
- [ ] Behavioral model results remain supporting evidence; static checks and
  explicit human review retain their distinct roles.
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

- a guidance-neutral repository investigation;
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

1. Implement and maintain the standard-owned scenario contracts under
   `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/`.
2. Register an `agent_eval` marker and exclude real-model suites from normal
   package tests.
3. Create a session-scoped neutral repository investigation using a pinned
   baseline that does not contain the candidate instructions.
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
- neutral pinned repository investigation;
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
- [ ] Specify the `DOCREP-*` behavioral consumer scenarios.
- [ ] Add documentation-standard behavioral consumers.
- [x] Run deterministic tests.
- [ ] Run or explicitly report the gated real-model suite as not run.
- [ ] Update `AEVAL-*` and `DOCVAL-005` evidence.
- [ ] Present canonical behavioral artifacts for human review.

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
| Documentation-standard consumers (`AEVAL-016`, `DOCVAL-005`) | Requirement-to-test mapping covers every `DOCGEN-*` and `DOCREP-*` ID; gated runs use a neutral cached seed and clean continuations and preserve exact canonical artifacts. |
| Provenance and interpretation (`AEVAL-017`) | Artifacts identify environment/configuration, instructions, prompts, model, seed, requests, tools, projections, evaluations, presentations, errors, and outputs; AI scores remain supporting evidence and human verification remains pending review. |
| Maintainer documentation (`AEVAL-018`) | README and complete examples let a new author run a simple Crystal Lattice assertion, customize drivers/snapshots/evidence/scoring/presentation, and substitute an alternate environment without reading internals. |

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