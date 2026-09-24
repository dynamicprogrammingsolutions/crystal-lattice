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

The dataset identifies the intended result set. The run attempt selects
producer, handoff, or continuation records. The semantic attempt selects the
assessment pass. `AGENT_EVAL_CACHE_NONCE` may force a retry while retaining the
same canonical run attempt; consolidation selects the latest matching record
for each identity.

Do not rerun a frozen canonical attempt into the main raw-result directory
unless the intent is to replace an invalid cell. For independent reproduction,
use a separate artifact root.

## Prerequisites

Install the evaluator and local Crystal Lattice dependencies:

```bash
python -m pip install -e "maintainer/agent-evaluation[crystal-lattice,dev]"
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
```

The recorded GLM profile uses `glm-5.3-flash:cloud` at max effort. The GPT
profile uses `gpt-5.6-luna` through the ChatGPT login and expects the normal
Crystal Lattice credentials, usually under `~/.crystal`.

Run deterministic checks before spending model quota:

```bash
pytest maintainer/agent-evaluation/suites/task_guidance \
  -c maintainer/agent-evaluation/pyproject.toml -q

ruff check maintainer/agent-evaluation/suites/task_guidance
```

## Select the evaluation

Use a separate raw-result directory when reproducing completed evidence:

```bash
export AGENT_EVAL_ARTIFACT_ROOT="$PWD/tmp/agent-evaluation/task-guidance-reproduction"
```

For
[Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate)
v1:

```bash
export AGENT_EVAL_GUIDANCE_BUNDLE="$PWD/maintainer/guidance/candidates/task-mechanics-b1"
export AGENT_EVAL_TASK_DATASET_ID="task-guidance-b1-20260919"
export AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT="b1-v1-r1"
export AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT="b1-v1-r1"
export AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT="b1-metrics1"
```

For
[Stage B0 — Current-guidance baseline](test-plan.md#stage-b0--current-guidance-baseline):

```bash
export AGENT_EVAL_GUIDANCE_BUNDLE="$PWD/maintainer/guidance/current"
export AGENT_EVAL_TASK_DATASET_ID="task-guidance-b0-20260919"
export AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT="b0-v5-r1"
export AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT="b0-v5-r1"
export AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT="b0-metrics1"
```

These variables make the following commands short and keep the selected
guidance, dataset, and attempts visible.

## Reproduce one task-creation cell

This example reproduces the GPT-5.6-luna xhigh result for the Flask/Vue book
discovery case:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
AGENT_EVAL_TASK_SCENARIO=tg04-flask-vue-discovery-decomposition \
AGENT_EVAL_TASK_EFFORT=xhigh \
pytest maintainer/agent-evaluation/suites/task_guidance/test_baseline_producers.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Add `AGENT_EVAL_CACHE_NONCE=review-1` when a genuinely new response is needed
instead of a compatible cached run.

## Reproduce the producer matrix

Run all GLM-max producer cells:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
pytest maintainer/agent-evaluation/suites/task_guidance/test_baseline_producers.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Run all GPT high/xhigh/max producer cells:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
pytest maintainer/agent-evaluation/suites/task_guidance/test_baseline_producers.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

The completed evaluations used independent scenario/effort processes, with up
to eight concurrent processes per provider. Parallel execution is only an
optimization: split the focused command by `AGENT_EVAL_TASK_SCENARIO` and
`AGENT_EVAL_TASK_EFFORT`, redirect each process to its own log, and keep the
common variables above unchanged.

Before parallel execution, warm or validate each provider serially. Earlier
calibration found that two providers simultaneously building the same local
plugin package could race.

## Reproduce handoff and continuation evidence

Fresh-agent retain/omit plans run for GLM:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
pytest maintainer/agent-evaluation/suites/task_guidance/test_handoff_plans.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Run the same file with GPT:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
pytest maintainer/agent-evaluation/suites/task_guidance/test_handoff_plans.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Same-agent continuation uses the equivalent commands with
`test_same_agent_continuation.py`. For example, run the GLM cells with:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
pytest maintainer/agent-evaluation/suites/task_guidance/test_same_agent_continuation.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Run the GPT cells by adding `AGENT_EVAL_ALLOW_HOSTED=1` and setting
`AGENT_EVAL_PROFILE=gpt`.

The incomplete-handoff negative control uses GLM:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
pytest maintainer/agent-evaluation/suites/task_guidance/test_negative_control.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

## Reproduce semantic assessment

Clear focused producer filters before assessing a complete matrix:

```bash
unset AGENT_EVAL_TASK_SCENARIO AGENT_EVAL_TASK_EFFORT
```

Task-creation semantic assessment uses GLM:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
pytest maintainer/agent-evaluation/suites/task_guidance/test_semantic_assessment.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_semantic -q
```

Handoff semantic assessment:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
pytest maintainer/agent-evaluation/suites/task_guidance/test_handoff_semantic_assessment.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_semantic -q
```

Set `AGENT_EVAL_TASK_ALLOW_PARTIAL=1` only for explicitly labeled calibration
or blocked-provider analysis. A partial semantic pass does not complete a
stage.

## Consolidate and collect the result package

The `freeze_b0` module is the consolidation command for both completed
stages. It reads the raw run records under the artifact root and writes one
consolidated dataset JSON plus a Markdown status summary. Its default output
lives under `<artifact-root>/consolidated/<dataset-id>.json`; pass `--output`
to place it elsewhere.

For
[Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate)
v1:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.freeze_b0 \
    --artifact-root "$AGENT_EVAL_ARTIFACT_ROOT" \
    --producer-attempt "$AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT" \
    --handoff-attempt "$AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT" \
    --semantic-attempt "$AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT" \
    --dataset-id "$AGENT_EVAL_TASK_DATASET_ID" \
    --label "task-mechanics candidate" \
    --output "$AGENT_EVAL_ARTIFACT_ROOT/consolidated/task_guidance_b1_results.json")
```

The command generates:

- `<output>`: complete consolidated machine evidence;
- `<output>` with a `.md` suffix: generated stage status and cohort scores.

Collect the durable result package from a consolidated dataset without any
model request:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.result_package collect \
    --dataset b1 \
    --artifact-root "$AGENT_EVAL_ARTIFACT_ROOT" \
    --frozen "$AGENT_EVAL_ARTIFACT_ROOT/consolidated/task_guidance_b1_results.json" \
    --output ../docs/evaluations/task-guidance/results/20260919-task-mechanics-b1)
```

`--dataset` selects the evaluation identity (attempts, guidance bundle,
package name); `--frozen` selects the consolidated dataset JSON; `--cells`
collects a partial package for selected `scenario:profile:effort` cells;
`--no-reconstruction` skips GPT compiled-message reconstruction. Collection
ends with the package check, so a collected package always passes `check`.

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
  python -m suites.task_guidance.result_package extract-scenarios \
    --bundle ../guidance/candidates/task-mechanics-b1)
```

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