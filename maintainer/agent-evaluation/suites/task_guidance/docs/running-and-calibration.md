# Running and calibrating the task-guidance suite

The migrated human-operated CLI is available at:

```bash
python maintainer/agent-evaluation/suites/task_guidance/task_guidance_eval.py --help
```

See [Current CLI workflow](legacy-cli.md) for its existing Codex handoff
scenario. The evaluator for
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

Run deterministic suite coverage:

```bash
(cd maintainer/agent-evaluation && pytest suites/task_guidance -q)
ruff check maintainer/agent-evaluation/suites/task_guidance
```

Run one current-guidance baseline producer profile:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT=b0-v5-r1 \
pytest maintainer/agent-evaluation/suites/task_guidance/test_baseline_producers.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Set `AGENT_EVAL_TASK_SCENARIO` to one scenario ID for a focused run. ChatGPT
also requires `AGENT_EVAL_ALLOW_HOSTED=1`.

Retry one model-effort cell without repeating successful cells:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_ALLOW_HOSTED=1 \
AGENT_EVAL_PROFILE=gpt \
AGENT_EVAL_TASK_SCENARIO=tg04-flask-vue-discovery-decomposition \
AGENT_EVAL_TASK_EFFORT=max \
AGENT_EVAL_CACHE_NONCE=retry1 \
AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT=b0-v5-r1 \
pytest maintainer/agent-evaluation/suites/task_guidance/test_baseline_producers.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

`AGENT_EVAL_CACHE_NONCE` changes only the execution cache identity. The
canonical run-attempt value remains unchanged, so the latest valid record for
that model/effort cell replaces the earlier invalid retry target during
consolidation.

Run a partial GLM semantic pass only when missing/invalid provider cells have
been separately recorded:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT=b0-v5-r1 \
AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT=b0-metrics1 \
AGENT_EVAL_TASK_ALLOW_PARTIAL=1 \
pytest maintainer/agent-evaluation/suites/task_guidance/test_semantic_assessment.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_semantic -q
```

Partial assessment does not satisfy the complete matrix requirement.

Run fresh-agent retained/omitted plans for one bounded scenario:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_TASK_SCENARIO=tg02-fastapi-pagination-handoff \
AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT=b0-v5-r1 \
pytest maintainer/agent-evaluation/suites/task_guidance/test_handoff_plans.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Run its same-agent continuation and incomplete negative control:

```bash
AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_TASK_SCENARIO=tg02-fastapi-pagination-handoff \
AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT=b0-v5-r1 \
pytest maintainer/agent-evaluation/suites/task_guidance/test_same_agent_continuation.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q

AGENT_EVAL_RUN_REAL=1 \
AGENT_EVAL_PROFILE=glm \
AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT=b0-v5-r1 \
pytest maintainer/agent-evaluation/suites/task_guidance/test_negative_control.py \
  -c maintainer/agent-evaluation/pyproject.toml \
  -m task_guidance_baseline -q
```

Freeze the selected attempts:

```bash
(cd maintainer/agent-evaluation && \
  python -m suites.task_guidance.freeze_b0 \
    --producer-attempt b0-v5-r1 \
    --handoff-attempt b0-v5-r1 \
    --semantic-attempt b0-metrics1)
```

The consolidated dataset is written under
`tmp/agent-evaluation/task-guidance/consolidated/<dataset-id>.json` by default;
pass `--output` to place it elsewhere. Collect the durable result package
from a consolidated dataset with
`python -m suites.task_guidance.result_package collect --dataset <key>
--frozen <consolidated.json>`; see
[Reproducing and inspecting results](../../../../docs/evaluations/task-guidance/reproducing-and-inspecting-results.md)
for the full package workflow.

Record discovery reads only `profile/runs/run-id/records/` paths, so semantic
workers may run in parallel without traversing workspaces being cleaned up by
other processes. Use at most eight concurrent processes per provider.

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

Cache and evidence identity will include:

- project and pinned revision;
- scenario contract and canonical stage input;
- task/plan variant;
- guidance bundle and compilation hash;
- instruction delivery;
- model and effort;
- stage prompt;
- run attempt.

Retries keep the canonical dataset identity and use a separate run-attempt key.
The frozen attempts are `b0-v5-r1` for producers/handoffs and
`b0-metrics1` for semantic assessment.

## Upstream gates

Semantic assessment starts only from structurally valid producer records.
Pairwise review starts only from structurally valid semantic records.
Behavioral assertion failures remain evidence and do not block downstream
interpretation.

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

## Migrated workflow

The package-owned CLI currently preserves:

- imported planning sessions;
- retain-plan and omit-plan forks;
- deterministic assertions;
- empirical review;
- review-bundle generation.

Historical records remain readable by the migrated assertion and bundle
commands.