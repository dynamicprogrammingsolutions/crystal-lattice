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
| Machine-readable reviewed targets | `maintainer/agent-evaluation/suites/task_guidance/targets/` |
| Project fixtures and canonical handoffs | `maintainer/agent-evaluation/suites/task_guidance/fixtures/` |
| Frozen consolidated JSON and generated machine summaries | `maintainer/agent-evaluation/suites/task_guidance/fixtures/results/` |
| Raw local run records | `tmp/agent-evaluation/task-guidance/<profile>/runs/<run-id>/` |
| Current portable guidance | `maintainer/guidance/current/` |
| Task-mechanics candidate v1 | `maintainer/guidance/candidates/task-mechanics-b1/` |

The frozen JSON embeds generated task files, plan responses, semantic
assessments, validity, provenance, and tool metrics. A reviewer normally starts
there. Raw run directories are useful for the full model session, exact
delivery observation, workspace diff, cache status, and retries.

## Completed result identities

| Evaluation | Dataset | Producer and handoff attempt | Semantic attempt | Frozen JSON |
|---|---|---|---|---|
| [Stage B0 — Current-guidance baseline](test-plan.md#stage-b0--current-guidance-baseline) | `task-guidance-b0-20260919` | `b0-v5-r1` | `b0-metrics1` | `task_guidance_b0_results.json` |
| [Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate) v1 | `task-guidance-b1-20260919` | `b1-v1-r1` | `b1-metrics1` | `task_guidance_b1_results.json` |

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

## Consolidate and generate the machine report

The historical `freeze_b0` module is the general consolidation command for
both completed stages. It writes formatted JSON and a Markdown status summary.

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
    --output suites/task_guidance/fixtures/results/task_guidance_b1_results.json)
```

For an independent reproduction, point `--output` into `tmp/` instead of
overwriting the repository's frozen result.

The command generates:

- `<output>.json`: complete consolidated machine evidence;
- `<output>.md`: generated stage status and cohort scores.

The dated human reports are not generated mechanically. Their author reviews
the frozen JSON, raw records, scenario targets, and model outputs; explains
patterns and limitations; and records the resulting decision.

## Inspect a completed result

Start with the generated machine summary:

```bash
less maintainer/agent-evaluation/suites/task_guidance/fixtures/results/task_guidance_b1_results.md
```

Then use the dated interpretation:

```bash
less maintainer/docs/evaluations/task-guidance/20260919-task-mechanics-b1-results.md
```

### Print the exact generated task files for one cell

Set a frozen result and cell identity:

```bash
RESULT=maintainer/agent-evaluation/suites/task_guidance/fixtures/results/task_guidance_b1_results.json
SCENARIO=tg04-flask-vue-discovery-decomposition
PROFILE=gpt
EFFORT=xhigh
```

Print every generated task file:

```bash
jq -r \
  --arg scenario "$SCENARIO" \
  --arg profile "$PROFILE" \
  --arg effort "$EFFORT" '
    .producer_records[]
    | select(
        .scenario_id == $scenario
        and .producer.profile == $profile
        and .producer.reasoning_effort == $effort
      )
    | .task_files
    | to_entries[]
    | "\n===== \(.key) =====\n\(.value)"
  ' "$RESULT" | less
```

This is the quickest reliable answer to questions such as: “What task files
did GPT-5.6-luna xhigh create for the failed book-discovery decomposition
case?”

### Print that cell's semantic assessment

```bash
jq \
  --arg scenario "$SCENARIO" \
  --arg profile "$PROFILE" \
  --arg effort "$EFFORT" '
    .semantic_records[]
    | select(.scenario_id == $scenario)
    | .assessment.assessments[]
    | select(
        .producer.profile == $profile
        and .producer.reasoning_effort == $effort
      )
  ' "$RESULT" | less
```

The assessment contains:

- missing or added outcomes;
- reviewed-deliverable mappings;
- task paths involved in each problem;
- separate quality dimensions and occurrence descriptions;
- the overall semantic summary.

Read the occurrence description first, then open the task paths listed in that
occurrence using the previous command. This connects a report score to the
exact text that produced it.

### Find the raw run directory

Frozen results intentionally do not depend on an absolute run path. To find
the corresponding local producer record:

```bash
find tmp/agent-evaluation/task-guidance/gpt/runs \
  -path '*/records/task-guidance-producer.json' -print0 |
xargs -0 jq -r \
  --arg scenario "$SCENARIO" \
  --arg effort "$EFFORT" '
    select(
      .scenario_id == $scenario
      and .producer.profile == "gpt"
      and .producer.reasoning_effort == $effort
      and .run_attempt == "b1-v1-r1"
      and .valid == true
    )
    | input_filename
  ' |
sort |
tail -n 1
```

The final `sort`/`tail` selects the newest timestamped valid run when a cell
has retries. From the reported path, move two directories up to the run
directory. Useful files are:

- `result.md` — run identity, final response, captured value, and canonical
  evidence;
- `records/task-guidance-producer-summary.md` — concise model and task-file
  summary;
- `records/task-guidance-producer.json` — exact generated task files and
  provenance;
- `raw/workspace/git-diff.patch` — the task-file changes as a patch;
- `raw/environment/crystal-lattice-session.json` — full saved conversation;
- `raw/environment/crystal-lattice-observation.json` — observed execution
  result.

Raw local directories may be absent on another machine. The frozen JSON still
contains the generated task text and the semantic judgment needed for normal
review.

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

## Current inspection limitation and recommended improvement

The `jq` commands above are reliable but not ideal for frequent review. A
small future read-only command should expose the same data without requiring
query syntax, for example:

```text
python -m suites.task_guidance.inspect_result \
  --results <frozen-json> \
  --scenario <scenario-id> \
  --profile gpt \
  --effort xhigh \
  --show task-files,assessment,raw-path
```

That command is not implemented yet. It should only format existing records;
it must not rerun models, change result selection, or replace the frozen JSON
as the source of truth.