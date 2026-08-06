Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`

Related Task:

- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- `tasks/20260721-task-guidance-evaluation-workflow.md`

Specification:
`maintainer/specifications/agent-evaluation-framework/index.md`

Requirement IDs:
`AEVAL-001`–`AEVAL-017`, `DOCGEN-001`–`DOCGEN-005`,
`DOCREP-001`–`DOCREP-005`, `DOCVAL-005`

# Programmatic Agent Evaluation Framework

Create a small maintainer-owned Python library that makes Crystal Lattice agent
programs easy to exercise, cache, fork, observe, and inspect from ordinary
pytest tests. Use the documentation-standard instructions as the first
behavioral consumers without hardcoding evaluation semantics into the
framework.

## Requirements checklist

- [ ] A package under `maintainer/agent-evaluation/` exposes the approved
  minimal `agent_eval` public contract.
- [ ] `AgentEval.run()` accepts only a name, arbitrary execution callback, and
  optional adapter, parent run, workspace, and cache key.
- [ ] Evaluation-specific behavior remains in ordinary Python, Crystal Lattice
  configuration, and plugins rather than framework inputs or required
  abstractions.
- [ ] A single runtime-adapter boundary supports the Crystal Lattice
  Core/Application implementation while preserving a direct escape hatch to
  the underlying application, core, session, and configuration.
- [ ] Execution callbacks can perform one or several requests and return any
  Python value.
- [ ] Runs can be cached and forked into clean compatible workspaces with exact
  snapshot, configuration, repository, and parent provenance.
- [ ] Canonical artifacts show useful messages/results, tool activity, changed
  paths, errors, and provenance without requiring routine inspection of raw
  sessions or event streams.
- [ ] Complete raw evidence remains available separately and does not retain
  credentials or authentication state.
- [ ] Deterministic package tests cover the framework lifecycle and failure
  behavior.
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

### Approved design

The user approved a deliberately small public model:

```python
run = evaluation.run(
    "run-name",
    execute,
    adapter=runtime,
    continue_from=previous_run,
    workspace=workspace_factory,
    cache_key="optional-cache-key",
)
```

The only initial central types are:

- `AgentEval`, which owns lifecycle, caching, workspace handling, and
  artifacts;
- `Run[T]`, which returns the callback value, reusable runtime snapshot,
  observations, workspace evidence, artifacts, and errors;
- one `RuntimeAdapter` strategy boundary;
- the Crystal Lattice adapter/context implementation;
- an optional Git workspace helper.

Do not add required `Case`, `Suite`, `Check`, `Reviewer`, `Score`,
`InstructionLayer`, or `RunPolicy` types. If repeated consumer code later
justifies conveniences, implement them as optional helpers over the minimal
contract.

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
material is only a small fraction. The new library should produce a canonical
result by default and preserve raw evidence separately.

### Boundary with subtask 068

This subtask creates the library and documentation-standard consumers.

Subtask 068 remains responsible for:

- moving task-guidance evaluation code, fixtures, and documentation under
  `maintainer/`;
- adopting the new library where appropriate;
- updating existing commands and consumers;
- preserving task-guidance-specific deterministic assertions and empirical
  review behavior;
- removing obsolete specialized infrastructure only after equivalent behavior
  is verified.

This subtask must not make task-guidance migration a hidden prerequisite for
the first library version.

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

Tests may vary the user message, configuration, plugins, skills, or models.
They should not require a particular instruction-injection mechanism.

Deterministic assertions should inspect paths, files, links, responses, and
provenance where possible. Structured model scoring is allowed as ordinary
test code and recorded as supporting evidence.

## Execution plan

Status: Draft

The implementation should establish the smallest useful library first, verify
it deterministically, and only then add real-model documentation-standard
consumers. The existing task-guidance evaluator remains unchanged except for
read-only comparison and possible reuse of clearly generic implementation
ideas.

### 1. Establish the package and public contract

1. Create the maintainer-owned Python package with an independently testable
   `pyproject.toml`, concise README, `src/agent_eval/`, package tests, and
   real-model suite directory.
2. Export only the approved initial contract:
   - `AgentEval`;
   - `Run`;
   - `RuntimeAdapter`;
   - Crystal Lattice application adapter/context/observation;
   - optional `git_workspace()` helper.
3. Implement `AgentEval.run(name, execute, *, adapter=None,
   continue_from=None, workspace=None, cache_key=None)`.
4. Keep internal lifecycle, serialization, artifact, lock, and workspace
   helpers private until a repeated public use is demonstrated.

### 2. Implement the Crystal Lattice adapter

1. Build on `AgentApplication` and `AgentCore` rather than reproducing provider
   or tool-loop behavior.
2. Support caller-owned application configuration, environment, and plugins.
3. Provide context conveniences for:
   - starting/selecting an agent;
   - adding arbitrary supported message roles/content;
   - issuing requests with ordinary Crystal Lattice overrides;
   - obtaining final assistant responses;
   - recording custom artifacts.
4. Preserve direct access to application, core, current immutable session, base
   configuration, and workspace.
5. Capture normalized visible messages, requests, tool calls, errors, timing,
   usage when available, and raw runtime artifacts.

### 3. Implement runs, continuation, workspaces, and cache

1. Return the callback value unchanged through `Run.value`.
2. Preserve adapter snapshot and observation without assigning pass/fail.
3. Accept existing paths and arbitrary workspace factories.
4. Add the optional Git helper using pinned revisions, reusable repository
   cache, detached clean workspaces, status, changed paths, and diff capture.
5. Restore parent snapshots into fresh workspaces and preserve immutable parent
   hashes and rebase/rebuild provenance.
6. Implement explicit versioned cache keys combined with adapter, workspace,
   parent, and framework-schema fingerprints.
7. Use safe atomic cache writes and locking; reject incompatible, corrupt, or
   partial entries.

### 4. Implement canonical and raw artifacts

1. Write canonical Markdown and JSON for every completed or failed run.
2. Include callback value when safely renderable, adapter canonical
   observation, changed paths, cache/parent/workspace provenance, and concise
   failure information.
3. Keep full sessions, events, compiled requests, tool payloads, Git evidence,
   and diagnostics under a separate raw area.
4. Ensure artifacts do not copy credentials or authentication state.
5. Provide `canonical_text()` and custom `record()` without defining reviewer
   or score semantics.

### 5. Add deterministic framework tests

Cover:

1. Arbitrary callback execution and return values.
2. Default and per-run adapter selection.
3. Multi-request execution through a deterministic fake or local adapter.
4. Parent snapshot restoration and immutability.
5. Workspace creation, Git changes, cleanup, and reconstruction evidence.
6. Cache hit, miss, incompatibility, corruption, locking, and atomic writes.
7. Canonical/raw artifact shape.
8. Runtime and callback failure preservation.
9. Credential/auth-state exclusion.
10. An existing real Crystal Lattice consumer at the lowest practical
    non-provider boundary so adapter tests do not only exercise mocks.

### 6. Add pytest documentation-standard consumers

1. Register an `agent_eval` marker and exclude real-model suites from normal
   package tests.
2. Create a session-scoped neutral repository investigation using a pinned
   baseline that does not contain the candidate instructions.
3. Fork clean continuations covering all `DOCGEN-*` and `DOCREP-*`
   requirements.
4. Exercise at least one ordinary user-message instruction path and leave room
   for configuration/plugin/skill variants without framework changes.
5. Use normal pytest assertions for objective path, content, mutation, and
   provenance outcomes.
6. Where semantic interpretation adds value, request test-owned structured
   scores or findings and validate them in ordinary Python.
7. Record exact model/configuration, instruction hash, prompt, seed, tool,
   output, and error evidence.
8. Keep human-review requirements unverified until the user reviews the
   canonical artifacts.

### 7. Verify and document

1. Run package deterministic tests in the normal fast path.
2. Run the documentation-standard real-model tests only with their explicit
   gate enabled.
3. Report skipped provider/model cases as not run.
4. Inspect canonical artifacts for concision and raw artifact links for
   diagnostic sufficiency.
5. Update `AEVAL-*` and `DOCVAL-005` evidence.
6. Present the behavioral results for human review of `DOCGEN-*` and
   `DOCREP-*`.

### Implementation decisions and open questions

- Approved: the library is programmatic rather than declarative.
- Approved: arbitrary execution callbacks own all evaluation-specific
  behavior.
- Approved: one runtime-adapter strategy is the only required initial
  abstraction.
- Approved: pytest modules are the initial suites and runner.
- Approved: the first consumers verify documentation-standard instructions.
- Approved: task-guidance migration remains in subtask 068.
- Recommendation for plan approval: use `maintainer/agent-evaluation/` as the
  distribution directory and `agent_eval` as the Python import.
- Recommendation for plan approval: require all `DOCGEN-*` and `DOCREP-*`
  requirements to have at least one behavioral consumer, but allow one test to
  cover a coherent group.
- Recommendation for plan approval: require one explicitly enabled supported
  real-model path for initial behavioral evidence; additional model families
  and repeated statistical thresholds remain optional until actual variance
  justifies them.
- Local reversible choices include internal module decomposition, JSON
  serialization library, file-lock implementation, and canonical Markdown
  rendering details.
- No unresolved requirement question changes the required outcome.

### Documentation

- `maintainer/agent-evaluation/README.md`
- Public API docstrings and typing for the exported contract
- Pytest marker and real-model execution instructions
- Cache and artifact-layout guidance
- A concrete documentation-standard test example
- `maintainer/README.md` routing
- `maintainer/specifications/agent-evaluation-framework/*`
- Updated evidence in both framework and documentation-standard requirements

### Task checklist

- [ ] Create the maintainer package and minimal public exports.
- [ ] Implement `AgentEval.run()` and `Run`.
- [ ] Implement the Crystal Lattice runtime adapter and context.
- [ ] Implement parent snapshot continuation.
- [ ] Implement workspace factories and optional Git helper.
- [ ] Implement explicit compatible caching and locking.
- [ ] Implement canonical and raw artifacts.
- [ ] Add deterministic framework and adapter tests.
- [ ] Register the gated pytest real-model marker.
- [ ] Add documentation-standard behavioral consumers.
- [ ] Run deterministic tests.
- [ ] Run or explicitly report the gated real-model suite as not run.
- [ ] Update `AEVAL-*` and `DOCVAL-005` evidence.
- [ ] Present canonical behavioral artifacts for human review.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Minimal public contract (`AEVAL-001`–`AEVAL-007`) | Package import and API tests exercise the exact `AgentEval.run()` signature, arbitrary callbacks/return values, default and overridden adapters, Crystal Lattice context access, and `Run` fields without required evaluation-specific abstractions. |
| Continuation, cache, and workspace (`AEVAL-008`–`AEVAL-010`) | Deterministic tests show immutable parent restoration, clean fork workspaces, path rebasing/rebuilding, pinned Git evidence, compatible cache reuse, and rejection of incompatible/corrupt entries. |
| Artifacts and safety (`AEVAL-011`–`AEVAL-012`) | Failure and success fixtures produce concise canonical Markdown/JSON and separate raw evidence; tests confirm credential/auth files are not copied. |
| Deterministic quality (`AEVAL-013`) | Normal package test command collects and passes callback, adapter, continuation, cache, workspace, artifact, and failure tests, including one real Crystal Lattice boundary consumer. |
| Pytest operation (`AEVAL-014`) | Marker registration and default test configuration exclude real-model calls; explicitly gated invocation collects the intended tests; disabled hosted cases are reported as not run. |
| Documentation-standard consumers (`AEVAL-015`, `DOCVAL-005`) | Requirement-to-test mapping covers every `DOCGEN-*` and `DOCREP-*` ID; gated runs use a neutral cached seed and clean continuations and preserve exact canonical artifacts. |
| Provenance and interpretation (`AEVAL-016`) | Artifacts identify instructions, prompts, model/config, seed, requests, tools, errors, and outputs; AI-produced scores are labeled supporting evidence and human verification remains incomplete pending review. |
| Maintainer documentation (`AEVAL-017`) | README and examples let a new evaluation author create a cached investigation, continuation, custom configuration/plugin run, structured score, and pytest assertion without reading framework internals. |

### Additional implementation verification

- Compare canonical artifact size and review usefulness with a representative
  current `test/task_guidance` case.
- Verify a cache hit makes no model request.
- Verify a continuation never mutates the parent artifact or source snapshot.
- Verify custom Crystal Lattice plugins/configuration can vary instruction
  behavior without changing `AgentEval`.
- Run `git diff --check`, package lint/type checks, and package-local tests.
- If real-model tests run, record provider/model and exact gate used.