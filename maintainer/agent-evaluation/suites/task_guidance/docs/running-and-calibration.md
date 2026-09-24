# Running and calibrating the task-guidance suite

The suite is a pytest-parametrized live evaluation driven by one
configuration manifest. Every live case — which scenarios run, which
model and effort produce them, which agent judges each stage — derives
from `configuration.json` and the stage catalog; no environment variable
selects cells or changes collection.

The human-operated CLI is still available for imported planning sessions:

```bash
python maintainer/agent-evaluation/suites/task_guidance/task_guidance_eval.py --help
```

See [Current CLI workflow](legacy-cli.md) for its Codex handoff scenario.
The evaluator for
[Stage B0 — Current-guidance baseline](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b0--current-guidance-baseline)
and candidate v1 for
[Stage B1 — Task-mechanics candidate](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b1--task-mechanics-candidate)
are implemented and frozen. The practical-baseline revision and
[Stage B2 — Guidance-placement confirmation](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b2--guidance-placement-confirmation)
remain pending task 090.

Use
[Reproducing and inspecting results](../../../../docs/evaluations/task-guidance/reproducing-and-inspecting-results.md)
for completed result identities, concise reproduction commands, raw-run
locations, report generation, and cell-level task-file inspection.

## Layout

- `evaluation/` — the live matrix: one parametrized driver file per
  catalog stage, collected by pytest and gated by the `agent_eval`
  marker. `matrix.py` derives every case from the configuration.
- `tests/` — deterministic tests of the suite machinery; a bare pytest
  run collects no live evaluation.
- `docs/development/` — the suite specification, requirements, and
  testing strategy.

## Deterministic coverage

```bash
(cd maintainer/agent-evaluation && pytest suites/task_guidance -q)
ruff check maintainer/agent-evaluation/suites/task_guidance
```

## Running the live matrix

Every live command needs `-m agent_eval`; the repository-wide pytest
configuration deselects live evaluation otherwise. The full matrix on
the current configuration is one command with no run parameters:

```bash
(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance -m agent_eval -q)
```

Slice the matrix with `-k` and the stage markers:

```bash
pytest suites/task_guidance/evaluation -m agent_eval -k glm -q
pytest suites/task_guidance/evaluation -m agent_eval \
  -k tg02-fastapi-pagination-handoff -q
pytest suites/task_guidance/evaluation -m "agent_eval and handoff_plan" -q
```

The stage markers are `task_creation`, `handoff_plan`, `continuation`,
`negative_control`, `task_creation_assessment`, and `handoff_assessment`.
Assessment cases are parametrized per subject cell — one case per
(scenario, producer cell) for task-creation judgments and one case per
fresh plan, same-agent continuation, or negative control for handoff
judgments — and every sample of a cell is assessed.

Run options (registered by `evaluation/conftest.py`):

- `--label LABEL` — the run label recorded as provenance for every
  executed request. One invocation uses one label; the freeze selects a
  whole invocation with it. Unset, a label is generated.
- `--fresh` — re-execute every request even when a compatible cached run
  exists.
- `--samples N` — execute each request N times as variance samples.

## How runs are identified and cached

Request identity is structural: the suite composes it from the stage,
agent and model, scenario, reasoning effort, variant, workspace
fingerprint, reviewed-target hash, prompt hash, and — for
continuations — the parent run's identity. Run labels are provenance
only: they never enter the cache key, so relabeling an unchanged request
replays it from the execution cache instead of re-executing.

An unchanged request replays from the cache (recorded as a cache hit in
the run's provenance). `--fresh` re-executes deliberately. `--samples N`
executes N genuine runs under one label. Provider-error values are not
cached and re-execute naturally on a later invocation.

## Freezing a dataset

The freeze adapter consolidates raw run records into one dataset JSON
plus a Markdown status summary:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.freeze \
    --labels <run-label> \
    --dataset-id <dataset-id> \
    --label "<human description>" \
    --bundle <guidance bundle path> \
    --output <path.json>)
```

Without `--labels` the freeze selects the latest valid record per cell;
with `--labels` it selects every sample of the listed invocations. The
frozen dataset records the run selection, the guidance bundle
provenance, per-cell selection counts, and the flat record lists.

## Collecting the result package

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.result_package collect \
    --frozen <consolidated.json> \
    --output <package directory>)
```

The dataset identity — id, human label, run selection, and guidance
bundle — is read from the frozen dataset; the package name is the output
directory name. `--cells` collects a partial package for selected
`scenario:profile:effort` cells; `--no-reconstruction` skips GPT
compiled-message reconstruction. Collection ends with the package check,
so a collected package always passes `check`.

## Record discovery and parallelism

Record discovery reads only `profile/runs/run-id/records/` paths, so
workers may run in parallel without traversing workspaces being cleaned
up by other processes. Slice by `-k` (scenario, producer, variant) and
redirect each process to its own log; keep at most eight concurrent
processes per provider, and warm or validate each provider serially
before parallel execution.

## Cleaning up run directories

Raw run directories accumulate one directory per executed request under
`<artifact-root>/<profile>/runs/`. The prune command classifies them by
the consolidation semantics and removes what no freeze or collection can
select again:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.prune_runs \
    --keep-labels <label-a>,<label-b>)          # dry run: report only

(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.prune_runs \
    --keep-labels <label-a>,<label-b> --cache --execute)
```

A run directory is kept when one of its records is selected for the kept
labels: every genuine managed sample (records with a `run-model.json`
provenance sibling), or — when a cell has only cache replays — its
replays; for legacy records the latest per cell and label. Run
directories without readable records are kept and reported (they may be
in flight or broken). `--cache` clears the execution cache, so kept
requests re-execute on their next invocation. Run the prune while no
live evaluation is executing.

## Sequence

1. Validate the reviewed scenario contracts and canonical plans. Completed.
2. Run deterministic suite tests and Crystal Lattice message/tool preflights.
   Completed for GLM and the blocked GPT sentinel.
3. Run
   [Stage B0 — Current-guidance baseline](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b0--current-guidance-baseline)
   with current guidance unchanged. Completed with one explicit invalid GPT
   same-agent upstream.
4. Review validity, semantic behavior, and efficiency variance. Combined
   GLM/GPT report complete.
5. Propose and approve the shortest
   [Stage B1 — Task-mechanics candidate](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b1--task-mechanics-candidate)
   wording. Candidate v1 completed.
6. Run paired task-mechanics candidate cases and nondegradation checks.
   Candidate v1 completed and is preserved as strong decomposition evidence;
   it is not promoted verbatim.
7. Add and run the focused practical-baseline plan-preservation, generated-task
   handoff, design-visibility, dependency, and connected-test confirmation.
8. Freeze the approved practical task-mechanics baseline as the comparison
   baseline.
9. Compile the descriptive placement designs defined by
   [Stage B2 — Guidance-placement confirmation](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b2--guidance-placement-confirmation).
10. Run focused sensitive cases.
11. Run the full justified matrix only for the selected candidate.

## Identities

Cache and evidence identity includes:

- project and pinned revision;
- scenario contract and canonical stage input;
- task/plan variant;
- guidance bundle and compilation hash;
- instruction delivery;
- model and effort;
- stage prompt;
- the parent run's identity, for continuations.

Run labels record which invocation produced a record; they are provenance
for selection and reporting, not part of the identity. The completed
stages were recorded under their historical per-stage run selections,
which the freeze and package adapters still read.

## Upstream gates

Assessment starts only from structurally valid subject records; a case
whose subjects are all invalid skips with the recorded reasons instead
of failing the batch. Pairwise review starts only from structurally
valid assessment records. Behavioral assertion failures remain evidence
and do not block downstream interpretation.

## Calibration

Current-guidance baseline calibration covered:

- scenario assertions;
- semantic targets;
- task topology normalization;
- fresh-agent handoff expectations;
- tool-call categories and variance;
- the need for a negative control.

The first
[Stage B1 — Task-mechanics candidate](../../../../docs/evaluations/task-guidance/test-plan.md#stage-b1--task-mechanics-candidate)
is frozen as evidence but is not promoted verbatim. Placement candidates are
not created until the practical task-mechanics baseline receives focused
confirmation and explicit approval.
Human-facing plans, test descriptions, and results are under
`maintainer/docs/evaluations/task-guidance/`.