Parent Task:
tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/095-evaluation-result-review-packages.md`
  (completed: result packages, synthetic fixtures, and the dataset-path CLI exist)

Coordinates with:

- `tasks/20260728-package-local-documentation-standard/090-task-guidance-handoff-baseline-and-placement.md`
  (owns guidance wording, scoring rules, and promotion; its remaining
  practical-baseline confirmation will run on the restructured suite, and the
  per-subject assessor applies to future runs only — frozen b0/b1 evidence
  stays as committed)

Owning specifications to update:

- `maintainer/agent-evaluation/suites/task_guidance/docs/development/specification.md`
- `maintainer/agent-evaluation/suites/task_guidance/docs/development/requirements.md`
- `maintainer/agent-evaluation/suites/task_guidance/docs/development/testing-strategy.md`
- `maintainer/agent-evaluation/suites/task_guidance/docs/running-and-calibration.md`

Requirement IDs:

- Suite `TGEVAL` set: amendments plus new IDs (`TGEVAL-018` onward) for the
  run model and assessment delivery, defined during planning together with
  the specification update.

# Task-Guidance Suite Restructure and Assessment Redesign

Restructure the task-guidance suite into a configuration-declared,
pytest-parametrized evaluation, and redesign the semantic assessments to one
subject per request with producer-identity blinding. One combined migration:
a single declaration file for agents, efforts, the cell matrix, and default
directories; all tests in their own directory; pytest-native selection;
generic consolidation and package CLIs; no evaluation-stage names in code.

## Requirements checklist

### Configuration and parametrization

- [ ] One configuration manifest (`configuration.json`, loaded through a thin
  loader module) declares the agents (model, agent id, declared efforts, and
  pinned runtime-config fixture), the scenario categories with their
  scenario lists, producer cell matrices, and stage lists (each stage's
  inputs: plan variants, the negative-control designation, the judging
  agent), and the default directories. The actual crystal-lattice runtime
  configs are committed fixture files — the authentication method lives
  only there. A fixed stage catalog (`stages.py`) defines what each stage
  name means: the workspace a run starts from, the earlier stage whose
  workspace and session prefix it shares, its expansion, its config schema,
  its executor, and its record file. Tests, consolidation, and the
  result-package adapter derive every expectation from the manifest and the
  catalog; no duplicated matrix, stage, or record definitions remain.
  Configuration tests verify through the manifest — well-formedness
  (scenario membership matches the scenario data, every cell references a
  declared agent and effort, stage names and config keys match the catalog,
  the negative-control designation is well formed, fixtures pin exactly
  their declared agent) and consumer derivation — never duplicated literal
  agent or matrix values.
- [ ] Agent, model, and effort are pytest parameters generated from the
  configuration and scenario data, so collection contains only real cells.
  Slicing a run uses pytest `-k` expressions only.
- [ ] The only environment variables are directories and connection settings:
  the candidate guidance bundle, the guidance target, the artifact root, the
  credentials directory, and the Ollama base URL. No environment variable
  selects scenarios, agents, efforts, or stages, or gates model execution.

### Test layout and gating

- [ ] All suite tests live in a separate `tests/` directory, flat and
  marker-selected. Deterministic tests run under a bare pytest invocation;
  live model tests run only under explicit `agent_eval` marker selection, and
  the repo-wide default deselection keeps them out of CI and accidental runs.
- [ ] The full live matrix on the current candidate is one pytest command
  with no run parameters beyond the marker, and both agents execute in one
  invocation through session-cached per-agent harnesses.

### Reusable run-model layer

- [ ] The run model — run labels, request identity, sample execution, the
  provider-failure publish predicate, and the consolidation core (label
  selection, per-cell sample aggregation) — lives in a reusable framework
  layer in `src/agent_eval/`, positioned between the crystal-lattice adapter
  and the suites: suites consume it and wire adapter-built environments into
  it; the layer depends only on the kernel and receives environments as
  parameters, never importing the adapter. It imports no suite code and
  contains no evaluation-stage names, so other suites can adopt it later
  without changes.
- [ ] Every live run records a run label (auto-generated per invocation,
  overridable with `--label`) as pure provenance; the label never affects
  execution or the cache key, and no environment variable carries it.
- [ ] Cache identity is the request identity only (fixture, prompt, guidance
  compilation, model, effort). Successful executions are cached; provider
  failures such as insufficient-quota errors are not cached, so rerunning a
  failed cell under the same cache re-executes it naturally without any
  flag.
- [ ] Deliberate re-execution of an unchanged, already successful request
  uses an explicit invocation option (`--fresh`, or `--samples N` for
  variance sampling); it is the only way to re-run a successful cell.
- [ ] The consolidation core selects records by one or more run labels; all
  records of a cell across the selected labels become that cell's samples,
  and the statistics aggregate them into one per-cell number with spread and
  per-sample provenance. Single-sample cells and the historical datasets
  behave exactly as today.
- [ ] The layer is verified by a fixture mini-evaluation: a small fixture
  configuration with a real-shaped matrix, multiple stages including an
  assessment, and multiple runs, executed end-to-end (labels, samples,
  provider-failure retry, freeze, aggregation) against a deterministic echo
  provider in short-running tests. An optional local-Ollama variant of the
  same fixture may cover one real-provider path.
- [x] A crystal-lattice mini-evaluation exercises the same run-model
  mechanism through the real crystal-lattice runtime: a deliberately small
  workspace under evaluation whose AGENTS.md carries the evaluated guidance
  candidate, and a strict division of provider labor — the deterministic
  echo agent answers everything that needs only a simple response (the
  no-tool producer scenario and every per-subject assessment), while the
  two local Ollama models (`qwen3.5:0.8b` and `qwen3:0.6b` via the
  reference openai-compatible provider) own every tool call, producing the
  file-writing scenarios through the real tool loop with the core
  read/write tools; the two models form the model axis of the matrix, the
  deterministic default-path tests verify labels, natural provider-failure
  retry, guidance-change cache miss, fresh re-execution, and consolidation
  end-to-end, and at least two `agent_eval`-marked live tests cover the
  Ollama matrix (production, validity derivation from workspace state,
  assessment, and reporting).
  (Amendment approved September 24, 2026: echo owns every simple response —
  the no-tool producer scenario and all per-subject assessments; the two
  local Ollama models own every tool call; at least two live tests.)

### Assessment redesign

- [ ] Semantic assessments run one subject per request with a neutral subject
  label. Producer identity, validity flags, and tool metrics are not part of
  the prompt; variant and stage labels remain where the rubric requires them
  (retain/omit/incomplete/generated-task, fresh-agent/same-agent).
- [ ] The saved assessment record keeps the subject-to-producer mapping, and
  consolidation and result packages render per-subject judgments.
- [ ] A subject whose producer record is missing or invalid skips with an
  explicit recorded reason instead of blocking or invalidating other subjects.
- [ ] The historical batched assessment schema remains readable: the frozen
  b0/b1 datasets and committed packages keep regenerating, and the package
  adapter supports both schemas.

### Consolidation and packaging

- [ ] Consolidation (`freeze`) is a generic CLI: run-label selection, dataset
  id, label, and output path are command arguments, and it records the
  guidance bundle path and compilation hash into the frozen dataset. The
  suite's freeze and results modules are thin adapters over the framework
  consolidation core.
- [ ] The result-package CLI reads evaluation identity (dataset id, label,
  run labels, bundle) from the frozen dataset file; the hardcoded dataset
  registry is removed.

### Naming and compatibility

- [ ] No evaluation-stage names (`b0`, `b1`, `baseline`, `metrics` attempt
  names) appear in suite code or test files. They appear only as command
  arguments and result directory names.
- [ ] The negative-control designation and the expected record sets derive
  from scenario data and the configuration module.
- [ ] Both committed packages pass `check` and regenerate byte-identically
  after the restructure; the scenarios export regenerates byte-identically.
- [ ] Prior evidence stays usable without migration or rerun: committed
  packages and frozen datasets remain valid inputs (readers treat legacy
  attempt fields as run labels), and raw prior run records remain
  selectable by their recorded labels.

## Open questions

- Exact marker names for the live stages (`task_guidance_producer`,
  `task_guidance_handoff`, `task_guidance_continuation`,
  `task_guidance_assessment` proposed) — local, reversible.
- New requirement IDs and specification wording for the run model — defined
  during planning.
- The layer's module shape in `src/agent_eval/` (single module vs small
  package; where the execution side ends and the consolidation core begins)
  and whether the optional local-Ollama variant of the fixture
  mini-evaluation is included — local implementation decisions.
- The kernel publish-predicate API shape (how the layer refuses caching
  values that report provider errors) — a step-level implementation
  decision; record semantics stay unchanged.

## Scope

This task owns the suite's structure and the reusable run-model layer it
needs: the framework layer extraction in `src/agent_eval/`, the suite
configuration module, the tests directory and parametrization, marker and
gating changes, the per-subject assessment delivery, the consolidation and
package CLIs, and the affected documentation.

It does not own guidance wording, scoring rules, scenario content, model
calibration, or promotion decisions (task 090), it does not migrate other
suites to the new layer (they can adopt it later unchanged), and it does
not rerun the frozen b0/b1 evaluations (their committed evidence stays
as-is under the user's option ii: the per-subject assessor applies to
future runs).

## Approved decisions

- September 24, 2026: `-k` slicing for all run selection (decision 1).
- September 24, 2026: marker-only live gating; `AGENT_EVAL_RUN_REAL` and
  `AGENT_EVAL_ALLOW_HOSTED` are deleted; `-m agent_eval` is the explicit
  intent (decision 2).
- September 24, 2026: the configuration file is a Python module
  (decision 4).
- September 24, 2026: `tests/` is flat with markers, no `unit`/`live`
  subdirectories (decision 5).
- September 24, 2026: one combined migration — restructure and assessment
  redesign together, since they touch the same files (decision 6).
- September 24, 2026: the run model is extracted into a reusable framework
  layer in `src/agent_eval/`, positioned between the crystal-lattice
  adapter and the suites (user direction). The suite keeps only its
  configuration values, scenarios, prompts, and package rendering; the
  layer owns labels, request identity, samples, the publish predicate,
  and the consolidation core. The layer is tested by a fixture
  mini-evaluation — a semi-complex but short-running scenario (real-shaped
  matrix, multiple stages, an assessment, multiple runs) against a
  deterministic echo provider, with a local-Ollama variant as the optional
  real-provider path.
- September 24, 2026: configuration tests verify through the configuration
  (well-formedness and derivation), never by duplicating literal agent or
  matrix values in test assertions (user direction).
- September 24, 2026: execution plan approved. The layer is part of the
  `agent_eval` package as a subpackage sibling of `crystal_lattice/`, and it
  is environment-neutral — it depends only on the kernel and receives
  environments as parameters; suites wire crystal-lattice environments into
  it; the layer never imports the adapter.
- September 23, 2026: option ii — the frozen b0/b1 comparison remains the
  promotion evidence; the per-subject, blinded assessor applies to future
  runs (the practical-baseline confirmation and later stages).
- September 24, 2026 (decision 3 resolved): run labels are pure provenance —
  auto-generated per invocation, overridable with `--label`, recorded in
  every run, never part of the cache key. Cache identity is the request
  identity only (fixture, prompt, guidance compilation, model, effort), so
  a slight change executes only affected cells while unchanged cells replay
  from cache, visibly marked. Successful executions are cached; provider
  failures such as insufficient-quota errors are not cached and retry
  naturally under the same cache. Deliberate re-execution of unchanged
  successful requests uses `--fresh` (or `--samples N` for variance
  sampling) — the only way to re-run a successful cell. Freeze takes one or
  more `--labels`; all records of a cell across the selected labels become
  that cell's samples and aggregate into one per-cell statistic with spread
  and per-sample provenance. The word "attempt" disappears from the suite
  vocabulary.
- Environment variables are acceptable only for the candidate bundle and
  target directories (plus artifact root and connection settings); never for
  test parameter values.
- Prior evidence is reused, the execution cache is not: committed packages
  and frozen datasets stay valid without migration or rerun (readers treat
  legacy attempt fields as run labels), raw prior run records stay
  selectable by their recorded labels, but cached executions are not
  carried over — old entries are keyed by a one-way hash that embeds the
  attempt and nonce, and re-keying would require reconstructing every key
  from its source run. The first live run after the restructure re-executes
  once (a b1-sized matrix is about $1.65 GPT; GLM is local) and repopulates
  the cache under the new key.

## Supporting facts

- Current parameter environment variables (all deleted by this task):
  `AGENT_EVAL_PROFILE`, `AGENT_EVAL_TASK_SCENARIO`, `AGENT_EVAL_TASK_EFFORT`,
  `AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT`,
  `AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT`,
  `AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT`,
  `AGENT_EVAL_TASK_ALLOW_PARTIAL`, `AGENT_EVAL_TASK_DATASET_ID`,
  `AGENT_EVAL_CACHE_NONCE`, `AGENT_EVAL_RUN_REAL`,
  `AGENT_EVAL_ALLOW_HOSTED`.
- The cell matrix is currently written three times: `PRODUCER_CELLS` in
  `test_baseline_producers.py`, `expected_producer_cells` in `semantic.py`,
  and the expected sets in `results.py`; the negative-control scenario is
  hardcoded in both `results.py` and `result_package.py`.
- The repo-wide pytest config deselects `agent_eval`-marked tests by default
  (`addopts = "-m 'not agent_eval'"` in `maintainer/agent-evaluation/pyproject.toml`);
  the suite directory has no `conftest.py` today.
- `collect` already requires `--frozen <path>` (fixture copies were removed
  by task 095), but `DATASETS` still hardcodes both evaluations' identity
  (keys, dataset ids, labels, package names, attempt names, bundle paths), and
  `freeze_b0.py` carries b0-flavored defaults. Freeze does not record bundle
  provenance; the registry supplies it.
- Both assessment prompts batch all subjects of a scenario into one request
  and embed producer identity in every record; the required response shape
  forces the assessor to echo `profile` and `reasoning_effort` per judgment
  (`semantic.py` `semantic_prompt`, `handoff_semantic.py`). The frozen
  evidence holds 6 + 3 batched assessor runs.
- The harness is currently one per pytest session, chosen by
  `AGENT_EVAL_PROFILE`; running both agents in one invocation needs
  session-cached per-agent harnesses. Provider plugin caches must warm
  serially (wheel-build race observed in task 090); default sequential pytest
  is safe.
- The committed packages are self-contained for `render` and `check`;
  historical frozen datasets live outside the repository
  (`<artifact-root>/consolidated/<dataset-id>.json` by default) and remain
  valid `--frozen` inputs.
- Historical GLM sessions retain no usage metadata; the restructure does not
  change cost capture. Captured b1 GPT cost is $1.6483; a live sentinel
  (one GLM producer plus one per-subject assessment) is the only planned
  model spend for verification.
- Today's cache and evidence identity includes the run attempt (see the
  Identities section of `running-and-calibration.md`), and the documented
  retry recipe pairs the same attempt with `AGENT_EVAL_CACHE_NONCE` —
  which suggests provider-failed executions may be cached today. The
  restructure removes the label from the cache key and must verify and
  ensure that provider-failed executions are not cached, so a failed cell
  re-executes naturally when rerun under the same cache.
- Kernel cache behavior (verified in `src/agent_eval/eval.py` and
  `src/agent_eval/cache.py`): `AgentEval.run` publishes to the cache only
  when `run.error is None`, so exception-level provider failures already
  retry naturally. The gap is completed runs whose value reports provider
  errors (`value.errors`, for example quota limits): they are cached
  today, which is what the nonce recipe works around. The restructure adds
  a kernel publish predicate so the suite can refuse caching values that
  report provider errors while keeping the current record semantics.
- Cache entries are content-addressed: the entry directory is named by a
  one-way hash of `{schema, caller_key, environment, workspace,
  parent_snapshot}`, and the stored manifest keeps only that hash and
  `source_run_id` — not the caller-key components (suite `runner.py`
  embeds attempt and nonce in the caller key). Re-keying old entries would
  mean reconstructing each key from its source run; a one-off
  re-execution is simpler and cheaper.
- The framework already separates the kernel (`src/agent_eval/eval.py`,
  `cache.py`, `workspace.py`) from the crystal-lattice adapter
  (`src/agent_eval/crystal_lattice/`), but the run model is suite-local
  today: `suites/task_guidance/runner.py` and
  `suites/documentation_standard/support.py` each build harnesses directly
  on the adapter. Framework tests live in
  `maintainer/agent-evaluation/tests/` (`test_kernel.py`, `test_cache.py`);
  the fixture mini-evaluation joins them there.

## Execution plan

Status: Approved

### 1. Run-model layer (framework)

Extract the reusable run model into `src/agent_eval/` as a layer between the
crystal-lattice adapter and the suites (module shape is an implementation
decision): run-label generation (auto per invocation, `--label` override),
request-identity composition with the label excluded, `--fresh`/`--samples N`
execution semantics, the provider-failure publish predicate (kernel hook plus
layer helper), and the consolidation core (label selection — latest per cell
by default with a printed selection, explicit multi-label — per-cell sample
aggregation with mean and spread and per-sample provenance, completeness
validation against caller-supplied expected sets).

Build the fixture mini-evaluation as the layer's own tests in the framework
test directory: a small fixture configuration (two echo agents, a small
matrix over two scenarios), produce and assess stages, a deterministic echo
provider with injectable provider failures, executed end-to-end — labels,
samples, natural retry, freeze, aggregation — in short-running tests. An
optional `ollama`-marked variant of the same fixture covers one real-provider
path. Inside this chunk the same test-first loop applies per mechanism
(labels → identity → samples → predicate → selection/aggregation).

### 2. Configuration module (suite)

Add `suites/task_guidance/configuration.py` declaring agents (with models,
fragments, default efforts), the producer cell matrix with category
restrictions, the assessor cell, and default directories (artifact root,
bundle, target, package output, scenarios export). Its tests verify through
the configuration — well-formedness and consumer derivation — never
duplicated literal values. Refactor `runner.py` to consume it; delete the
duplicated `PROFILES`/cell definitions.

### 3. Suite integration

Slim the suite runner to assembly: agent profiles come from the
configuration, request identities are composed through the layer, and
workspaces and turn functions stay suite-local. Rename `freeze_b0.py` to
`freeze.py` and reduce it and `results.py` to thin adapters over the
consolidation core: expected sets derive from the configuration and scenario
data (including the negative-control designation), bundle path and
compilation hash are recorded into the frozen dataset, and the CLI arguments
are generic.

### 4. Suite migration (tests directory and parametrization)

Move every test file into `suites/task_guidance/tests/` with a `conftest.py`
providing the session-cached per-agent harness factory and the run options
(`--label`, `--fresh`, `--samples`) wired to the layer. Rewrite the live
tests as configuration-derived parametrized tests (producers, handoff plans,
continuations, negative control, both assessments) with ids designed for
`-k`; rename the stage markers; update the pyproject marker list; delete all
parameter environment variables and the real-model gates.

### 5. Per-subject assessment redesign

Rewrite the assessment prompt templates to one subject per request with a
neutral subject label; keep variant/stage labels where the rubric requires
them; strip producer identity, validity, and tool metrics from the prompt
material. Bump the assessment schema versions, keep the subject-to-producer
mapping in the saved record, parametrize the assessment tests per
(scenario, cell), and skip with a recorded reason on invalid upstreams.
Assess every sample of a cell (samples multiply assessor requests).

### 6. Package adapter

Replace the `DATASETS` registry with identity read from the frozen dataset
file (`collect --frozen <path>` plus output/package arguments); support both
the historical batched and the new per-subject assessment schemas in
collection, rendering, and the scenarios export templates; render per-cell
sample aggregates (per-sample rows where a cell has more than one sample).

### 7. Documentation and naming cleanup

Rewrite `running-and-calibration.md` and the reproduction guide's command
sections to the new command set; document the framework layer and its
fixture mini-evaluation; update the suite specification, requirements, and
testing strategy for the configuration-declared run model and per-subject
assessment delivery; complete the naming cleanup.

### 8. Verification

Deterministic and targeted — the suite is never rerun in full during
development, and the final pass is also targeted: each chunk's own tests plus
the directly affected existing tests stay green; the fixture mini-evaluation
proves the whole mechanism (labels absent from identity, cached replay
marked, guidance change misses, provider-error value not cached and
re-executed, `--fresh` re-executes, multi-label freeze aggregates mean and
spread with provenance, single-sample datasets unchanged);
`--collect-only` shows exactly the declared matrix; `-k` slices deselect
correctly; bare pytest runs no live tests; committed packages pass `check`
and regenerate byte-identically; the scenarios export regenerates
byte-identically; grep finds no evaluation-stage names in code or tests.
Live (human-approved): one GLM producer sentinel plus one per-subject
assessment through the new path, collected into a throwaway package.

### Test-first execution order

Every chunk follows the same loop: add the chunk's own tests and watch them
fail, make the smallest change that turns them green, then run only that
chunk's tests plus the directly affected existing tests. Suite tests live in
`suites/task_guidance/tests/`; the layer and its fixture mini-evaluation live
in the framework's `tests/` directory.

| # | Chunk | Own tests | First failing assertions | Targeted runs |
|---|---|---|---|---|
| 1 | Run-model layer | Framework fixture mini-evaluation (fixture package + `tests/test_run_model*.py`, `tests/test_consolidation*.py`) + publish-predicate tests in `tests/test_kernel.py` | Fixture scenario end-to-end with the echo provider: labels recorded and absent from identity; provider-failure injection not cached and retried naturally; `--fresh` re-executes; `--samples N` executes N times; guidance change misses; multi-label freeze aggregates per-cell mean and spread with per-sample provenance; single-label selection unchanged; legacy attempt fields accepted as labels | New fixture tests + framework `tests/test_cache.py`, `tests/test_kernel.py` |
| 1b | Crystal-lattice mini-evaluation (approved amendment) | `tests/fixtures/crystal_mini_scenario.py` + `tests/test_crystal_mini_evaluation.py` (deterministic) + `tests/test_crystal_mini_ollama.py` (`agent_eval`+`ollama` marked) | The real runtime runs the whole mechanism: the echo agent produces the no-tool scenario and assesses every subject (scripted verdicts, one subject per request); a scripted provider failure retries naturally under the same identity; a changed AGENTS.md guidance candidate misses the cache; a second label replays unchanged cells and fresh re-executes one; consolidation aggregates labels with completeness against configuration-derived cells; at least two live tests run both qwen models through the real tool loop (`write_file`/`read_file`), derive validity from the workspace state, assess the subjects, and report the mini dataset | New tests + `tests/test_crystal_lattice.py`, `tests/fixtures/crystal_plugins.py` consumers |
| 2 | Configuration module | Suite `tests/test_configuration.py` | Verified through the configuration: every cell references a declared agent and a valid scenario category; every effort is declared for its agent; runner, semantic, and results derive identical expectations from it; no literal duplication | New file + runner, semantic, results tests |
| 3 | Suite integration | Suite `tests/test_runner_assembly.py` | Runner composes layer identities from configuration; freeze and results delegate to the consolidation core; bundle provenance recorded | New file + runner, results, freeze tests |
| 4 | Suite migration | Suite `tests/test_collection.py` | `--collect-only` lists exactly the configuration-derived matrix; bare pytest collects no live tests; legacy env vars do not change collection; `-k` slices select cells | New file + moved stage tests via `-k` |
| 5 | Per-subject assessment | Suite `tests/test_per_subject_assessment.py` | One subject per prompt; no producer identity, validity, or tool metrics; variant/stage labels kept; no producer echo in the response schema; mapping kept in the record; invalid upstream skips with reason; every sample assessed | New file + updated semantic tests |
| 6 | Package adapter | Suite `tests/test_package_adapter.py` | `collect --frozen` works without the registry; batched and per-subject schemas both render; sample aggregates render | New file + result_package tests + both committed-package `check` runs |
| 7 | Naming cleanup and docs | Suite `tests/test_no_evaluation_stage_names.py` | Forbidden tokens absent from suite code and tests | New file + documentation-link and guidance-compiler tests |

Chunk order is the dependency order: the layer is self-contained and comes
first; 3 needs 1 and 2; 4 needs 2 and 3; 5 needs 4; 6 needs 1, 3, and 5;
7 completes the cleanup.

### Implementation decisions and open questions

- Decision 3 is resolved (September 24, 2026): run labels are provenance
  only; the cache keys on request identity; provider failures are not cached
  and retry naturally; `--fresh`/`--samples N` are the only deliberate
  re-execution paths; freeze aggregates multiple labels per cell.
- The layer's module shape in `src/agent_eval/`, the kernel
  publish-predicate API shape, and whether the optional Ollama variant of
  the fixture mini-evaluation is included are implementation decisions made
  inside chunk 1; record semantics stay unchanged.
- Prior evidence is reused without migration; the execution cache is not
  carried over (see Approved decisions). A re-key migration script was
  considered and rejected as more complicated than one re-execution pass.
- Marker names, requirement IDs, and specification wording are local
  decisions finalized during planning; no model work starts before plan
  approval.
- The historical batched schema stays readable forever; no repricing or
  rescoring of frozen evidence happens in this task.

### Documentation

- Framework layer documentation: the reusable run model, its fixture
  mini-evaluation, and how suites consume it.
- Suite running guide and reproduction guide command sections.
- Suite specification, requirements, testing strategy for the run model.
- Task 090 cross-reference: future confirmation runs use the new commands.

### Task checklist

- [x] Resolve the run-label/cache/sampling mechanism (decision 3, September
  24, 2026).
- [x] Approve this execution plan (September 24, 2026).
- [x] Extract the run-model layer with the fixture mini-evaluation (chunk 1,
  test-first).
- [x] Build the crystal-lattice mini-evaluation: fixture workspace with the
  guidance candidate, echo agent for simple responses (no-tool produce and
  all assessments), both qwen Ollama models for every tool call,
  deterministic mechanism tests, and at least two `agent_eval`-marked live
  tests (chunk 1b amendment, approved September 24, 2026).
- [x] Add the configuration module with verify-through-configuration tests
  (chunk 2, test-first).
- [x] Integrate the suite: runner assembly, thin freeze/results adapters
  over the consolidation core (chunk 3, test-first).
- [x] Move tests into `tests/`, add the conftest wired to the layer,
  parametrize the live stages from the configuration manifest and stage
  catalog (including echo-path stage-mechanics tests asserting the
  catalog's declared workspace origin and parent linkage — deferred from
  the chunk 2 rework), rename markers, delete parameter env vars
  and gates (chunk 4, test-first).
- [x] Implement the per-subject assessment prompts, records, and tests
  (chunk 5, test-first).
- [x] Remove the package dataset registry; support both assessment schemas
  and per-cell sample rendering (chunk 6, test-first).
- [x] Rewrite the affected documentation; complete the naming cleanup
  (chunk 7, test-first).
- [x] Pass targeted deterministic verification and package regeneration
  parity (no full-suite reruns).
- [ ] Run the live sentinel verification (needs approval and credentials).
- [x] Update requirement ledgers and append completion notes.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Reusable run-model layer | The layer lives in `src/agent_eval/`, imports no suite code, and contains no evaluation-stage names (import test plus grep); the fixture mini-evaluation runs the whole mechanism end-to-end with the echo provider in short-running tests; the crystal-lattice mini-evaluation runs the same mechanism through the real runtime (deterministic echo path plus `agent_eval`-marked Ollama tool-loop tests); the suite consumes it through thin adapters. |
| Run labels and cache | The fixture mini-evaluation proves: the label never changes the cache key; an unchanged request replays from cache visibly; a changed guidance compilation misses; a provider-error value is not cached and re-executes on rerun (exception failures already excluded); `--fresh` re-executes a successful request. |
| Multi-sample aggregation | The fixture scenario's multi-label freeze produces per-cell mean and spread with per-sample provenance; single-sample and historical datasets are unchanged and readable. |
| Single-source configuration | Deterministic tests verify through the configuration — well-formedness and consumer derivation — with no duplicated literal matrices; grep finds no duplicated cell matrices. |
| Parametrized selection | `pytest --collect-only` lists exactly the configuration-derived matrix; `-k` slices deselect the intended cells; no env var influences collection. |
| Live gating | A bare pytest invocation collects no live tests; `-m agent_eval` collects them; CI configuration unchanged. |
| Assessment blinding | Prompt-rendering tests assert per-subject prompts contain no producer identity, validity flags, or tool metrics, and that variant/stage labels remain; saved records keep the mapping. |
| Invalid upstreams | A synthetic invalid producer record causes an explicit recorded skip, not a batch failure. |
| Consolidation and packaging | Freeze writes bundle provenance; `collect --frozen` reproduces a package from a frozen dataset without a registry; both committed packages pass `check` and regenerate byte-identically. |
| Prior-evidence compatibility | Synthetic legacy-format records and frozen datasets are selected and rendered by the new code (attempt treated as label); committed packages regenerate byte-identically. |
| Naming cleanup | Grep over suite code and tests finds no `b0`/`b1`/baseline/metrics attempt names and no "attempt" vocabulary; evaluation names appear only in CLI arguments and result directories. |
| Live path | The approved sentinel (one GLM producer, one per-subject assessment) runs, freezes, and collects into a throwaway package through the new commands only. |

### Additional implementation verification

- Prove both committed packages and the scenarios export regenerate
  byte-identically after the restructure.
- Keep credentials and authentication state out of all artifacts.
- Run the generic `agent_eval`, task-guidance suite, documentation-link, and
  guidance-compiler tests affected by the migration.

## Implementation Notes

- September 24, 2026 — chunk 1 (run-model layer) completed test-first:
  tests were written first and failed on the missing module, then the
  smallest implementation turned them green.
- The layer is the `src/agent_eval/runner/` subpackage: `labels.py`
  (auto label per invocation), `identity.py` (`request_identity` — takes
  no label argument, so provenance is structurally excluded from the cache
  key), `model.py` (`RunModel` with `run`/`run_samples`, fresh semantics,
  and the `publish_when_no_provider_errors` helper), and
  `consolidation.py` (record scanning, label resolution, cell selection,
  sample aggregation, completeness).
- Kernel hooks: `AgentEval.run` gained `cache_read` (skip the cache read
  but still publish — the mechanism behind `fresh` and `run_samples`) and
  `cache_publish` (publication predicate; provider-error values stay out
  of the cache and retry naturally). The public-signature test was updated
  for both parameters.
- Provenance record: every run writes `records/run-model.json`
  (label, identity, cache_hit, sample_index, run_id). Label resolution in
  consolidation: record `run_label` → sibling `run-model.json` → legacy
  `run_attempt`. Managed records keep every genuine execution as a sample
  and drop cache-replay duplicates; legacy records keep the latest record
  per cell and label (historical behavior).
- Fixture mini-evaluation: `tests/fixtures/run_model_scenario.py` — echo
  provider with injectable provider failures, per-agent environments, and
  a `MiniHarness` built on `RunModel`. Sharing environments across
  harnesses continues the echo counters, emulating model nondeterminism
  across invocations. New tests: `tests/test_run_model.py`,
  `tests/test_consolidation.py`, `tests/test_run_model_scenario.py`, plus
  kernel predicate/read tests in `tests/test_kernel.py` — 45 tests, all
  green in under a second; framework `tests/` green (175 passed); suites
  still collect cleanly against the changed kernel.
- The optional local-Ollama variant of the fixture was deferred: the echo
  fixture covers the mechanism and the approved GLM sentinel covers the
  real-provider path. Adding it later is an additive marked test.
  (Superseded September 24, 2026 by the approved chunk 1b amendment below.)
- September 24, 2026 — chunk 1b (crystal-lattice mini-evaluation) completed
  test-first per the approved amendment: deterministic tests were written
  first and failed on the missing fixture module, then the smallest
  implementation turned them green.
- Provider labor is divided as approved: the echo agent (fixture
  `EvaluationProvider`, extended with a `raise_error` mode) owns every
  simple response — the `mini-answer` producer scenario and all
  per-subject assessments with scripted `VERDICT:` responses — while both
  local Ollama models (`qwen3.5:0.8b`, `qwen3:0.6b` via the reference
  openai-compatible provider, `path:`-loaded with the shared plugin cache)
  own every tool call, producing `mini-task`/`mini-fix` through the real
  tool loop with the core `FileReaderTool`/`FileWriterTool` scoped to the
  run workspace by request overrides.
- The guidance candidate is the workspace `AGENTS.md`; a new fixture
  `GuidanceSystemMessage` feature plugin (minimal mirror of the real
  system-message feature) injects it as the leading provider-native system
  message from the per-request `guidance_file` override, and its sha256 is
  an identity component, so a guidance change misses the cache.
- `tests/fixtures/crystal_mini_scenario.py` holds the fixture workspace
  factory (AGENTS.md, `tasks/seed.md`, `src/app.py` with the planted
  defect), the agent/scenario configuration, validity derivation from
  workspace state, the `MiniCrystalHarness` over `RunModel`, and the mini
  freeze adapter (`freeze_mini_dataset`/`render_mini_report`) over the
  consolidation core.
- Deterministic tests (`tests/test_crystal_mini_evaluation.py`, 5 tests,
  <1 s): guidance-feature injection unit test; full lifecycle
  produce→assess→freeze with provenance and report; provider-failure
  natural retry (the tool loop converts a raised provider error into a
  completed run with error messages, so the value is not cached and the
  same identity re-executes); guidance-change miss; second-label replay
  plus fresh re-execution with two-label aggregation (deterministic echo:
  spread 0.0) and latest-label default selection.
- Live tests (`tests/test_crystal_mini_ollama.py`, `agent_eval`+`ollama`
  markers, 2 tests): both qwen models × both tool scenarios through the
  real tool loop — completed, no provider errors, tool loop engaged,
  validity derivation self-consistent with the workspace (model
  capability is reported, not asserted); and the produce→assess→freeze
  lifecycle with a cached replay (real production replays without a
  second model call). Both passed against local Ollama (~2 min including
  the one-time plugin install).
- Observed live behavior worth knowing: the small models engage the tool
  loop but often fail the tasks — absolute paths rejected by
  `allowed_paths`, or the created file not following the guidance rule
  (which reaches them only via the delivered AGENTS.md system message,
  by design). The scenario prompts gained a relative-path hint (tool
  mechanics, not the guidance rule); after it, `qwen3:0.6b` creates the
  task file. Validity honestly reports these outcomes with reasons.
- `pyproject.toml` gained the `ollama` marker. Framework `tests/` green
  (180 passed, 2 live deselected; the one failure is the known
  pre-existing CWD-sensitive `test_requirement_quality.py`, which passes
  from the repository root); suites still collect 63/254 unchanged.
- Cache carryover confirmed by implementation: nothing to migrate — old
  entries keyed with the attempt and nonce simply miss under the new
  identity, so the first live run re-executes once, as decided.
- Pre-existing quirks (not caused by this chunk, left untouched):
  `tests/test_requirement_quality.py` resolves repo-root-relative paths and
  must run from the repository root; `eval.py` and `tests/test_kernel.py`
  carry pre-existing black formatting drift outside the changed lines.
- September 24, 2026 — chunk 2 (configuration module) completed test-first:
  `suites/task_guidance/tests/test_configuration.py` was written first and
  failed on the missing module, then the configuration and consumer
  refactors turned it green.
- `suites/task_guidance/configuration.py` is the single source: `AgentSpec`
  agents (the moved `ModelProfile` plus declared `efforts` and the
  `request_overrides` behavior), the `PRODUCER_CELLS` matrix with
  scenario-category restrictions, `producer_cells(category)` /
  `all_producer_cells()`, the assessor cell, the handoff variants, the
  negative-control designation (scenario, cell, and variant), the five
  default directories, and the env-resolving `selected_bundle()` /
  `selected_artifact_root()` selectors.
- Consumers derive from it: `runner.py` (agents, artifact root, guidance
  target; `PROFILES`/`ModelProfile` deleted), `semantic.py`
  (`expected_producer_cells` delegates; its records-extractor renamed to
  `producer_cells_from_records` to free the canonical name),
  `results.py` (expected sets, negative control, and the quality-cohort
  display order/titles), `handoff_semantic.py` (fresh/same/negative
  expectations), `result_package.py` (agents, assessor cell, negative
  control, directories), `freeze_b0.py` (artifact root), and `fixtures.py`
  (bundle selection moved out; path anchors imported from the
  configuration).
- The 20 configuration tests verify through the configuration only —
  well-formedness (declared agents, real scenario categories, declared
  efforts, uniqueness, distinct repository directories, env overrides) and
  consumer derivation (behavioral: records written for exactly the
  configuration-derived cells consolidate with nothing missing in
  `results` and `handoff_semantic`; `selected_profile` returns the
  configuration objects) — plus source scans proving no matrix literals
  or directory definitions remain in the consumer modules.
- Verification: suite 83 passed (63 baseline + 20 new), 52 live
  deselected; both committed packages pass `check` byte-identically; the
  scenarios export regenerates content-identically (only the git-revision
  stamp in the guidance locks moves with each commit — pre-existing
  behavior, committed state restored); ruff/black clean on all changed
  files. The live test files still carry their own cell literals by
  design — chunk 4 replaces them with configuration-derived
  parametrization.
- September 24, 2026 — chunk 2 reworked per user direction: the
  Python-declared configuration became a JSON manifest plus pinned
  runtime-config fixtures, with a fixed stage catalog. Design agreed over
  several rounds: data lives in `configuration.json` (agents with their
  fixtures, categories with scenario lists + per-category producer
  matrices + stage maps with per-stage inputs), the actual
  crystal-lattice configs are committed fixtures (the authentication
  method lives only in the gpt fixture; credentials via
  `${env:CHATGPT_TEST_STATE_DIR}`), and `stages.py` holds the catalog
  (workspace origin, parent linkage, expansion, config schema, executor,
  record) that the manifest selects from. The catalog stays in code —
  every field references a code symbol, and a new stage kind always needs
  its executor anyway; the config alone composes existing machinery.
- `configuration.py` shrank to a loader: manifest accessors
  (`producer_cells`, `plan_variants`, `assessment_cell`,
  `negative_control`/`negative_control_designations`, `stage_config`),
  directory/env selectors, and `agent_config_file()` (fixture +
  artifact-local `plugin_cache_dir`, written under
  `<artifact-root>/agent-config/`). Deleted: `AgentSpec`/`Cell`/
  `ProducerCell`, the fragment-based `_project_config_for_profile`, and
  auth/credentials from `request_overrides` (now a plain runner function
  with only the glm/gpt effort-shape branch). `selected_profile()` became
  `selected_agent()` (name string); the harness takes the agent name and
  exposes `agent_name`/`agent`/`runtime_agent`; it gained
  `run_negative_control()` reading the designation from the manifest.
- Consolidation and the package adapter now derive through the stage
  declarations: `results.py` expected sets come from
  `_scenarios_with_stage(...)` (no `"handoff"` literal), record names come
  from `STAGES[...].record` (also in `semantic.py`, `handoff_semantic.py`,
  `result_package.py`), the assessor comes from the assessment stages'
  declared cells (all assessment stages must share one cell — pinned by a
  test), and the export's assessor keys derive from that cell.
- Tests: `tests/test_configuration.py` rewritten for the manifest (24
  tests: scenario membership pinned both ways against `scenarios.py`,
  stage names/config schemas against the catalog, fixture consistency —
  exactly the declared agent, suite model, auth only in the gpt fixture —
  behavioral derivation through `results`/`handoff_semantic`, source
  scans now also forbidding `ASSESSOR_CELL`/`HANDOFF_VARIANTS` and record
  literals); new `tests/test_stages.py` (catalog internal consistency:
  continuation is the only parent-sharing stage, unique records);
  `test_runner.py` rewritten (fixture tool-family pinning,
  `request_overrides` without auth, executor existence, harness
  construction from the pinned fixture); live tests updated mechanically
  to `selected_agent()`/`harness.agent` (their cell literals wait for
  chunk 4).
- One real bug found by the new tests and fixed: the rewritten loader
  computed `REPOSITORY_ROOT` one level too high (`SUITE_ROOT.parents[4]`
  instead of the file-level `parents[4]`); the directory-existence test
  caught it immediately.
- Verification after the rework: suite 100 passed, 52 live deselected
  (unchanged collection); framework tests 181 passed from the repository
  root; both committed packages still pass `check` byte-identically
  (their config views are frozen collected files); the scenarios export
  regenerates with the intended visible diff — `projected_config` renamed
  to `runtime_config`, the fixture now carries the suite model in the
  config itself, and gpt `request_overrides` no longer carries
  `auth_mode`/`chatgpt_credentials_path` (auth provenance moved
  config-side) — while compiled system messages and stage-input pages are
  byte-identical; ruff/black clean.
- Deferred to chunk 4 (noted there): echo-path stage-mechanics tests that
  run each stage through the real kernel asserting the catalog's declared
  workspace origin and parent linkage; the harness currently has no
  driver-injection point, which belongs with the test-migration work.
- September 24, 2026 — chunks 3+4 (suite integration + migration) completed
  test-first in one shot, as approved.
- Chunk 3: `tests/test_runner_assembly.py` written first (14 tests, failed
  on the missing pieces), then the runner became assembly over the
  run-model layer. The harness owns one labeled `RunModel`; four
  module-level identity functions (`task_creation_identity`,
  `handoff_plan_identity`, `continuation_identity`, `assessment_identity`)
  compose through the layer's `request_identity` — labels are structurally
  absent, the continuation's identity carries the parent's identity (read
  from the parent's `run-model.json` provenance), and the hand-built cache
  keys with `RUNNER_VERSION` strings and `AGENT_EVAL_CACHE_NONCE` are gone.
  Stage methods take `fresh`/`samples` and return tuples of runs;
  `_execute` maps one sample to cache-aware `RunModel.run` and multiple
  samples to `run_samples` (always genuine executions).
- `results.py` became a thin adapter over the consolidation core:
  `select_cell_records` per stage (labels select cells — latest label per
  cell by default, every sample of listed labels), `completeness` for the
  assessment statuses, provider blockers derived from a second
  selection pass keyed by provider identity. The frozen dataset is
  schema 2: `labels` replaces per-stage `attempts`, `bundle` records
  path + compilation sha, `selection` carries the per-cell label counts,
  and the flat record lists hold every selected sample (single-sample
  datasets are unchanged). `freeze_b0.py` → `freeze.py` with generic CLI
  (`--labels`, `--dataset-id`, `--label`, `--bundle`, `--output`) that
  compiles the bundle for provenance and prints the selection.
- Chunk 4: every test file moved into `suites/task_guidance/tests/`
  (legacy-file tests keep their own `sys.path` anchors, now pointing at
  the suite root). `conftest.py` provides `--label`/`--fresh`/`--samples`
  and session-cached per-agent harnesses sharing one invocation label;
  `matrix.py` derives the live matrix from the manifest and catalog. The
  six live tests are stage-named (`test_task_creation`, `test_handoff_plan`,
  `test_continuation`, `test_negative_control`,
  `test_task_creation_assessment`, `test_handoff_assessment`) with
  `-k`-friendly case ids; stage markers renamed to the catalog
  (`task_creation`, `handoff_plan`, `continuation`, `negative_control`,
  `task_creation_assessment`, `handoff_assessment`) and registered in
  pyproject. Deleted: `selected_agent()`, `selected_dataset_id()`,
  the `AGENT_EVAL_MAX_EVENTS` knob, and every parameter env var/gate
  (`AGENT_EVAL_PROFILE`, `AGENT_EVAL_TASK_*`, `AGENT_EVAL_RUN_REAL`,
  `AGENT_EVAL_ALLOW_HOSTED`, `AGENT_EVAL_CACHE_NONCE`). The assessment
  loaders (`semantic.load_producer_records`,
  `handoff_semantic.load_handoff_records`) now take `labels` and delegate
  selection to the core; record-identity formatters consolidated in
  `semantic.py` (`producer_cell_identity` etc.) and shared with
  `results.py`/`result_package.py`. New records carry no attempt or
  dataset fields — the `run-model.json` sibling is the provenance.
- The deferred stage-mechanics coverage landed as
  `test_stage_executor_matches_the_catalog_workspace_and_parentage`
  (parametrized over the catalog): each stage's executor is run through
  the real harness with only the model boundary faked, asserting the
  declared workspace origin (factory type per `workspace` kind, the
  parent's workspace for `continuation`) and parentage (`continue_from`
  only for continuation; the negative control plans from the designated
  incomplete variant). The full kernel mechanics stay proven by the
  mini-evaluation; the suite harness pins real agents, so no echo agent
  was added to the manifest.
- One regression caught by the package checks and fixed: the new
  `render_summary` read only `labels`, so the committed packages'
  historical aggregates (per-stage `attempts`) stopped regenerating
  `matrix.md` byte-identically. `render_summary` now renders both shapes
  (labels list, historical attempts dict, or latest-per-cell), and
  `collect` passes the frozen dataset's selection through verbatim.
- `tests/test_collection.py` verifies through subprocess collection:
  `-m agent_eval` collects exactly the 46-case configuration matrix
  (18 producers + 12 plans + 6 continuations + 1 control + 6 + 3
  assessments), bare pytest collects no live tests, the ten legacy env
  vars do not change collection, and `-k` slices (`glm`, one scenario,
  `retain`) select exactly the matching cases.
- Verification: suite 122 passed / 46 live deselected; framework 181
  passed from the repository root; both committed packages pass `check`
  byte-identically; the scenarios export regenerates content-identically
  (only the pre-existing git-revision stamp movement in the guidance
  locks, committed state restored); ruff/black clean.
- September 24, 2026 — layout amendment (user-directed): the live matrix
  is not a test of the suite machinery, so it no longer lives under
  `tests/`. The six stage drivers, the run-options `conftest.py`, and
  `matrix.py` moved to `suites/task_guidance/evaluation/` (a package,
  still pytest-collected and `agent_eval`-gated — run commands are
  unchanged, only the location). `tests/` now holds only the
  deterministic machinery tests; `test_collection.py` targets
  `evaluation/` for the matrix checks and the whole suite for the
  bare-pytest check. Verified: `tests/` alone 122 passed;
  `evaluation/` alone collects exactly the 46-case matrix with the
  `--label`/`--fresh`/`--samples` options registered.
- September 24, 2026 — chunks 5+6 (shot 2), test-first:
  `tests/test_per_subject_assessment.py` (14 tests) written first, then
  `tests/test_package_adapter.py`.
- Chunk 5 — per-subject assessment. `semantic.py`: schema 3 responses
  (single `assessment`, no producer echo — the validator rejects a
  `producer` key or a batch), per-subject prompt carrying only the
  produced work (response, task files, task tree — no producer identity,
  validity, or tool metrics), `ProducerSubject` +
  `load_producer_subjects` (every sample of a cell is one subject;
  `cells` limits one case's expected cells), `subjects_block_reason`
  (blocked only when every subject is invalid, listing the recorded
  reasons), `assessment_record` keeping the subject-to-producer mapping,
  and `assessment_subject_identity` for consolidation. `handoff_semantic.py`:
  schema 2 with stage/variant echo validated against the subject
  (variant/stage labels stay — the rubric interprets them);
  `HandoffSubject` + `load_handoff_subjects` covering fresh plans per
  variant, same-agent continuations (keyed by the variant-less
  continuation identity), and the designated control, with a `selection`
  filter for one case's subject; `handoff_assessment_record`. The
  evaluation drivers parametrize per subject cell: task-creation
  assessments are scenario × producer cell (18 cases), handoff
  assessments are scenario × (variant × cell + same-agent cells +
  control) (19 cases); each sample gets its own request (sample index in
  the test id) and its own record; missing upstreams and all-invalid
  subjects skip with the recorded reasons. `results.py` selects
  assessments by subject identity, expects per-subject cells, and
  aggregates cohort quality from the per-subject records. The live
  matrix is now 74 cases.
- Chunk 6 — package adapter. The `DATASETS` registry is gone:
  `collect` reads dataset id, label, run selection, and bundle from the
  frozen dataset file (`--frozen` + required `--output` + optional
  `--bundle` override; the package name is the output directory name).
  Discovery is label-based for both shapes (`_run_labels` +
  `_record_label` resolving the `records/run-model.json` sibling, then
  the legacy `run_attempt` field); per-subject assessment runs map to
  per-subject discovery keys. Rendering supports both schemas:
  `_iter_judgments` feeds the matrix detail rows (sample column when
  any judgment carries a sample index), the results pages (per-subject
  sections with subject + sample headings), and the index selection
  lines (attempts for historical aggregates, run labels for new ones).
  Per-subject collection gathers one assessor run per subject record
  under `assessment/{name}/s{index}/` with one shared results page.
  Historical batched rendering is byte-identical: both committed
  packages pass `check` after the rework.
- Shot 2 verification: suite 141 passed / 74 live deselected; framework
  181 passed from the repository root; both committed packages pass
  `check` byte-identically; the scenarios export regenerates with only
  the two intended assessment-prompt template diffs (plus the
  pre-existing guidance-lock revision stamps); ruff/black clean.
- September 24, 2026 — chunks 7+8 (shot 3). Chunk 7, test-first:
  `tests/test_no_evaluation_stage_names.py` written first — it pins the
  absence of the historical evaluation names (b0/b1 attempt names, old
  stage markers), confines the deleted parameter environment variables
  to the legacy-inertness collection test, and confines the legacy
  attempt vocabulary to the compatibility adapters (results.py,
  result_package.py) and the tests that construct legacy-shape fixtures;
  the remaining fixture values were replaced with synthetic ones and
  freeze.py's docstring reworded. Documentation: running-and-calibration.md
  rewritten to the new command set (layout, live matrix slicing, run
  options, identity/labels, freeze, collect); the reproduction guide's
  command sections rewritten (env selection, per-cell and matrix
  reproduction, per-subject assessments, freeze + `collect --frozen`);
  new framework page `docs/run-model.md` linked from the documentation
  map; the suite specification gained the configuration-declared stage
  model and per-subject delivery sections; the testing strategy gained
  the run-model/test-layout section; both doc indexes updated; task 090
  gained the new-commands cross-reference. Requirement ledger:
  TGEVAL-018–TGEVAL-021 added (configuration-declared matrix, run-model
  consumption, per-subject assessment, registry-free adapter), and
  TGEVAL-011's evidence notes both assessment schemas.
- Chunk 8 deterministic verification: suite 144 passed / 74 live
  deselected; framework 181 passed from the repository root; both
  committed packages pass `check` byte-identically; the scenarios
  export regenerates byte-identically (only the pre-existing
  guidance-lock revision stamps move, committed state restored);
  `--collect-only -m agent_eval` lists exactly the 74-case matrix;
  ruff/black clean. The live GLM sentinel remains the only open item and
  needs explicit approval and credentials.
## Completion Notes

- Outcome: the task-guidance suite is restructured onto the reusable
  run-model layer with a configuration-declared matrix, per-subject
  assessments, and a registry-free package adapter. All deterministic
  scope is implemented, tested, and documented. The only open item is
  the live GLM sentinel, which needs explicit approval and credentials.
- Requirement evidence: run-model layer and labels (framework
  mini-evaluations plus `tests/test_runner_assembly.py`);
  configuration-declared matrix (`tests/test_configuration.py`,
  `evaluation/matrix.py`, `tests/test_collection.py`); per-subject
  assessment (`tests/test_per_subject_assessment.py` plus the
  evaluation drivers); package adapter (`tests/test_package_adapter.py`
  plus both committed-package `check` runs, byte-identical);
  prior-evidence compatibility (legacy attempts read as labels;
  committed packages regenerate byte-identically); naming cleanup
  (`tests/test_no_evaluation_stage_names.py`). Suite requirement rows
  TGEVAL-018–TGEVAL-021 record the new behavior with their evidence.
- Verification performed: suite 144 passed / 74 live deselected;
  framework 181 passed from the repository root; both committed packages
  pass `check` byte-identically; the scenarios export regenerates
  byte-identically apart from the pre-existing guidance-lock revision
  stamps; `--collect-only -m agent_eval` lists exactly the 74-case
  configuration-derived matrix; ruff and black clean on all changed
  files (pre-existing formatting drift in untouched files left alone).
- Verification blocked: the live sentinel (one GLM producer plus one
  per-subject assessment through the new path into a throwaway package)
  was not run — it is the only planned model spend and requires explicit
  approval and credentials.
- Plan deviations: the live matrix lives under `evaluation/` rather
  than `tests/` (user-directed layout amendment); the render_summary
  row titles stay historical because renaming them would break
  byte-identical regeneration of the committed packages; the naming
  cleanup confines — rather than removes — the legacy attempt vocabulary
  to the compatibility adapters and their fixtures, because the
  historical data-format field names are part of readable prior
  evidence.
- Unresolved or deferred: the live sentinel (above); task 090's
  practical-baseline confirmation and promotion run on the restructured
  suite and are owned by task 090.
