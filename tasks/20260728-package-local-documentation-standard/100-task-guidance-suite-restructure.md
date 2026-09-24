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

- [ ] One configuration module declares the agents (model, agent id, plugin
  fragments, default effort), the producer cell matrix with scenario-category
  restrictions, the assessor cell, and the default directories. Tests,
  consolidation, and the result-package adapter derive every cell expectation
  from this one file; no duplicated matrix definitions remain. Configuration
  tests verify through the configuration — well-formedness (every cell
  references a declared agent and a valid scenario category, every effort is
  declared for its agent) and consumer derivation — never duplicated literal
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
- [ ] Extract the run-model layer with the fixture mini-evaluation (chunk 1,
  test-first).
- [ ] Add the configuration module with verify-through-configuration tests
  (chunk 2, test-first).
- [ ] Integrate the suite: runner assembly, thin freeze/results adapters
  over the consolidation core (chunk 3, test-first).
- [ ] Move tests into `tests/`, add the conftest wired to the layer,
  parametrize the live stages, rename markers, delete parameter env vars
  and gates (chunk 4, test-first).
- [ ] Implement the per-subject assessment prompts, records, and tests
  (chunk 5, test-first).
- [ ] Remove the package dataset registry; support both assessment schemas
  and per-cell sample rendering (chunk 6, test-first).
- [ ] Rewrite the affected documentation; complete the naming cleanup
  (chunk 7, test-first).
- [ ] Pass targeted deterministic verification and package regeneration
  parity (no full-suite reruns).
- [ ] Run the live sentinel verification (needs approval and credentials).
- [ ] Update requirement ledgers and append completion notes.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Reusable run-model layer | The layer lives in `src/agent_eval/`, imports no suite code, and contains no evaluation-stage names (import test plus grep); the fixture mini-evaluation runs the whole mechanism end-to-end with the echo provider in short-running tests; the suite consumes it through thin adapters. |
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