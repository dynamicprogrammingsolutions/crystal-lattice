# Reproducing and inspecting task-guidance results

This guide is for a maintainer, another agent, or a human reviewer who needs to
reproduce a task-guidance evaluation, inspect one model result, regenerate the
machine summary, or understand how a dated report was assessed.

The commands assume the repository root as the working directory. Real-model
runs may consume hosted-model quota and can take several minutes per cell.

## What is stored where

| Purpose | Location |
|---|---|
| Human test plan | `maintainer/docs/evaluations/task-guidance/test-plan.md` |
| Human test-case descriptions | `maintainer/docs/evaluations/task-guidance/test-cases.md` |
| Dated human interpretations | `maintainer/docs/evaluations/task-guidance/*-results.md` |
| Committed result packages | `maintainer/docs/evaluations/task-guidance/results/<evaluation>/` |
| Scenario input definitions export | `maintainer/docs/evaluations/task-guidance/scenarios/` |
| Machine-readable reviewed targets | `maintainer/agent-evaluation/suites/task_guidance/targets/` |
| Project fixtures and canonical handoffs | `maintainer/agent-evaluation/suites/task_guidance/fixtures/` |
| Raw local run records | `tmp/agent-evaluation/task-guidance/<profile>/runs/<run-id>/` |
| Current portable guidance | `maintainer/guidance/current/` |
| Task-mechanics candidate v1 | `maintainer/guidance/candidates/task-mechanics-b1/` |

A result package is the durable, self-contained record of one completed
evaluation: per-run `run.json`, full session transcripts, generated task
files, semantic assessments, the aggregate matrix source, and the usage and
cost inventory, plus regenerated human views. The scenario input definitions
export holds what the evaluations fed the models: reviewed targets, exact
prompts, shared configs and system messages, and every file added to the
workspaces beyond the repository checkout. Raw run directories remain useful
for the full provider session, exact delivery observation, workspace diff,
cache status, and retries; they are local and may be absent on another
machine.

## Completed result identities

| Evaluation | Dataset | Producer and handoff attempt | Semantic attempt | Result package |
|---|---|---|---|---|
| [Stage B0 — Current-guidance baseline](test-plan.md#stage-b0--current-guidance-baseline) | `task-guidance-b0-20260919` | `b0-v5-r1` | `b0-metrics1` | [20260919-current-guidance-b0](results/20260919-current-guidance-b0/index.md) |
| [Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate) v1 | `task-guidance-b1-20260919` | `b1-v1-r1` | `b1-metrics1` | [20260919-task-mechanics-b1](results/20260919-task-mechanics-b1/index.md) |

The dataset identifies the intended result set. The completed stages were
recorded under historical per-stage run selections, which the freeze and
package adapters still read; current runs record one run label per
invocation instead. `--fresh` re-executes a request deliberately while
keeping the same identity; consolidation selects the latest valid record
for each cell by default, or every sample of the listed labels.

Do not rerun a completed evaluation's selection into the main raw-result
directory unless the intent is to replace an invalid cell. For independent
reproduction, use a separate artifact root and a fresh run label.

## Prerequisites

Install the evaluator and local Crystal Lattice dependencies:

```bash
python -m pip install -e "maintainer/agent-evaluation[crystal-lattice,dev]"
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
```

The GLM profile defaults to `glm-5.3-flash` on the Z.ai provider and can
be switched to Ollama (`glm-5.3-flash:cloud`) with
`TASK_GUIDANCE_GLM_PROVIDER=ollama`; `ZAI_API_KEY` comes from the
repository `.env`. The GPT profile uses `gpt-5.6-luna` through the
ChatGPT login and expects the normal Crystal Lattice credentials, usually
under `~/.crystal`.

## Running the evaluation with one command

The parallel runner executes the whole matrix — or any slice — with one
command instead of one pytest invocation per stage, preserving every
stage dependency (producers, then dependent stages, then assessments)
and honoring per-agent maximum parallelism from a config file:

```bash
cd maintainer/agent-evaluation
python -m suites.task_guidance.run --label b1v4-r1
python -m suites.task_guidance.run --label b1v4-r1 \
  --stages task-creation,handoff-plan --scenarios tg01,tg02 --agents glm
python -m suites.task_guidance.run --label probe --dry-run
```

Cases, prompts, validity checks, and records come from the same shared
recipes as the parametrized live tests, so both paths stay identical.
`--parallelism parallelism.json` (for example `{"glm": 2, "gpt": 4}`)
raises an agent's concurrency; without it agents run serially while
different agents still run concurrently. Raise a cap only after verifying
the agent's run machinery tolerates concurrent runs under one label.
Per-case outcomes print live (`.` ok, `s` skipped, `F` failed) and the
exit code is non-zero when any case fails.

Run deterministic checks before spending model quota:

```bash
pytest maintainer/agent-evaluation/suites/task_guidance \
  -c maintainer/agent-evaluation/pyproject.toml -q

ruff check maintainer/agent-evaluation/suites/task_guidance
```

## Select the evaluation

Use a separate raw-result directory when reproducing completed evidence,
and select the guidance bundle the evaluation ran with:

```bash
export AGENT_EVAL_ARTIFACT_ROOT="$PWD/tmp/agent-evaluation/task-guidance-reproduction"
export AGENT_EVAL_GUIDANCE_BUNDLE="$PWD/maintainer/guidance/current"
```

Use `maintainer/guidance/candidates/task-mechanics-b1` to reproduce
[Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate)
v1. These variables make the following commands short and keep the
selected guidance visible; every other selection is a pytest flag.

## Reproduce one task-creation cell

This example reproduces the GPT-5.6-luna xhigh result for the Flask/Vue book
discovery case. Give the invocation a run label so the freeze can select
it:

```bash
(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_task_creation.py \
    -m agent_eval -k "tg04-flask-vue-discovery-decomposition and gpt and xhigh" \
    --label reproduction-1 -q)
```

Add `--fresh` when a genuinely new response is needed instead of a
compatible cached run.

## Reproduce the producer matrix

Run every GLM producer cell:

```bash
(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_task_creation.py \
    -m agent_eval -k glm --label reproduction-1 -q)
```

Run every producer cell of every declared agent:

```bash
(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_task_creation.py \
    -m agent_eval --label reproduction-1 -q)
```

Parallel execution is only an optimization: split the focused command by
`-k` (scenario, producer, effort), redirect each process to its own log,
and give each process the same run label. Before parallel execution, warm
or validate each provider serially. Earlier calibration found that two
providers simultaneously building the same local plugin package could
race.

## Reproduce handoff and continuation evidence

Fresh-agent retain/omit plans, same-agent continuations, and the
incomplete-handoff negative control are separate stage files, all sliced
the same way:

```bash
(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_handoff_plan.py \
    -m agent_eval -k glm --label reproduction-1 -q)

(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_continuation.py \
    -m agent_eval -k glm --label reproduction-1 -q)

(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_negative_control.py \
    -m agent_eval --label reproduction-1 -q)
```

Continuations require their producer cells under the same label first;
the continuation driver continues from each recorded parent sample.

## Reproduce the assessments

The assessments judge one subject per request — every sample of every
producer or handoff cell — under a neutral subject label that hides the
producer identity, validity, and tool metrics. They read the producer
and handoff records recorded under the run label and skip with the
recorded reasons when a subject cell is missing or invalid:

```bash
(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_task_creation_assessment.py \
    -m agent_eval --label reproduction-1 -q)

(cd maintainer/agent-evaluation && \
  pytest suites/task_guidance/evaluation/test_handoff_assessment.py \
    -m agent_eval --label reproduction-1 -q)
```

Run the assessments only after the cells they judge exist under the same
run label. A skipped assessment case records its reason in the report; a
partial assessment pass does not complete a stage.

## Consolidate and collect the result package

The `freeze` module is the consolidation command. It reads the raw run
records under the artifact root and writes one consolidated dataset JSON
plus a Markdown status summary. Without `--labels` it selects the latest
valid record per cell; with `--labels` it selects every sample of the
listed invocations:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.freeze \
    --artifact-root "$AGENT_EVAL_ARTIFACT_ROOT" \
    --labels reproduction-1 \
    --dataset-id "task-guidance-reproduction" \
    --label "reproduction" \
    --bundle "$AGENT_EVAL_GUIDANCE_BUNDLE" \
    --output "$AGENT_EVAL_ARTIFACT_ROOT/consolidated/reproduction.json")
```

The command generates:

- `<output>`: complete consolidated machine evidence;
- `<output>` with a `.md` suffix: generated stage status and cohort scores.

Collect the durable result package from a consolidated dataset without any
model request:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.result_package collect \
    --artifact-root "$AGENT_EVAL_ARTIFACT_ROOT" \
    --frozen "$AGENT_EVAL_ARTIFACT_ROOT/consolidated/reproduction.json" \
    --output ../docs/evaluations/task-guidance/results/reproduction)
```

The dataset identity — id, human label, run selection, and guidance
bundle — is read from the frozen dataset; the package name is the output
directory name. `--cells` collects a partial package for selected
`scenario:profile:effort` cells; `--no-reconstruction` skips GPT
compiled-message reconstruction. Collection ends with the package check,
so a collected package always passes `check`.

The frozen dataset names the raw run of every record, so re-running an
invocation under the same label or collecting `--samples N` assessments
keeps every judgment: each maps to its own run and renders at its own
location. Frozen datasets from before the run-id field still collect
through the identity-and-label fallback.

Regenerate the human views of a committed package after changing the report
configuration, and verify a package at any time:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.result_package render \
    --package ../docs/evaluations/task-guidance/results/20260919-task-mechanics-b1)

(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.result_package check \
    --package ../docs/evaluations/task-guidance/results/20260919-task-mechanics-b1)
```

The scenario input definitions export regenerates from the suite sources and
one guidance bundle:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.result_package extract-scenarios)
```

The committed export documents the current guidance bundle (the default);
passing another `--bundle` regenerates the compiled shared inputs from that
bundle instead.

The dated human reports are not generated mechanically. Their author reviews
the result package, scenario definitions, raw records, and model outputs;
explains patterns and limitations; and records the resulting decision.

## Inspect a completed result

Start from the package index of the evaluation you are reviewing:

```text
maintainer/docs/evaluations/task-guidance/results/20260919-task-mechanics-b1/index.md
```

The [matrix](results/20260919-task-mechanics-b1/matrix.md) view is the
aggregate entry point. Every cohort row is the average of its detail rows,
and every detail row links both the judgment rendering and the run or stage
directory it is about. To answer "what did GPT-5.6-luna xhigh produce for the
book-discovery decomposition case, and how was it judged":

1. Open [matrix](results/20260919-task-mechanics-b1/matrix.md) and find the
   `GPT xhigh` cohort row, then its detail rows.
2. Follow the detail row's run link to
   [scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh](results/20260919-task-mechanics-b1/scenarios/tg04-flask-vue-discovery-decomposition/gpt-xhigh/index.md).
3. Read the generated task files under `task-files/`, the full session
   transcript in `session.md` (exact prompt, tool activity, verbatim
   response, delivered instructions and config links), and the slim
   `run.json` for lineage and validity.
4. Follow the detail row's judgment link to
   [assessment/task-creation/results.md](results/20260919-task-mechanics-b1/scenarios/tg04-flask-vue-discovery-decomposition/assessment/task-creation/results.md)
   for the rubric, per-dimension statuses and scores, occurrence descriptions,
   and the task paths involved in each finding.

The same navigation answers handoff questions: the handoff detail rows link
`plan-retain`, `plan-omit`, `control`, and `continuation` stage directories,
and [costs.md](results/20260919-task-mechanics-b1/costs.md) holds one usage
and cost row per run. The [scenario input definitions](scenarios/index.md)
export shows exactly what each stage was given: models, tools, delivered
instructions, config, workspace revision, fixture upstream, every file added
to the workspace, and the exact prompt.

Raw run directories are only needed for provider-level forensics — the full
saved provider session, exact delivery observation, workspace diff, cache
status, and retries. They live under
`tmp/agent-evaluation/task-guidance/<profile>/runs/<run-id>/` and may be
absent on another machine; the committed package remains self-contained.

## How results are assessed

Use this order so an aggregate score cannot hide a setup problem or important
regression:

1. **Validity:** confirm execution completed, instruction delivery matched the
   intended model family, task files were captured, and no unexpected files
   changed.
2. **Approved outcomes:** check missing outcomes and added obligations before
   looking at task count.
3. **Task structure:** inspect fragmentation, phase-only children, layer
   splits without independent value, evidence re-ownership, and dependency
   safety separately.
4. **Important connections:** check whether one named test traverses every
   required production connection; separate side-specific checks are not
   equivalent.
5. **Handoff:** distinguish canonical fresh-agent, same-agent generated-task,
   and—when implemented—fresh-agent generated-task evidence.
6. **Plan quality:** inspect implementation design, component ownership,
   interfaces or flow, decisions, compatibility states, and verification
   strategy rather than rewarding a long ordered checklist.
7. **Human readability:** check whether a reviewer can find the outcome,
   design, child ownership, dependencies, open questions, and decisive
   evidence without following repeated context through every file.
8. **Cohorts and patterns:** compare models and efforts only after inspecting
   representative passing and failing task files.
9. **Decision:** weigh severity and recurrence against the known cost of
   leaving current guidance unchanged. Record what remains unproven.