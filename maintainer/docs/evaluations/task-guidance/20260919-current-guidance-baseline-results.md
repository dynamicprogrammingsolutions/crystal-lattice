# Current-guidance baseline results

This report records
[Stage B0 — Current-guidance baseline](test-plan.md#stage-b0--current-guidance-baseline)
after semantic rescoring with the six explicit task-quality dimensions.
Read the [test plan](test-plan.md) and
[test-case catalog](test-cases.md) first when the projects or evaluation flow
are unfamiliar.

## Status

| Evidence stage | Expected | Present | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|
| Task creation | 18 | 18 | 18 | 0 | 0 |
| Fresh-agent planning | 12 | 12 | 12 | 0 | 0 |
| Same-agent planning | 6 | 6 | 5 | 1 | 0 |
| Task semantic assessment | 6 batches | 6 | — | — | 0 |
| Handoff semantic assessment | 3 batches | 3 | — | — | 0 |
| Incomplete-handoff negative control | 1 | 1 | — | — | 0 |

The single invalid record is the GPT-high same-agent chain for
[Scenario TG-03 — Flask/Vue selected-filter refresh regression](test-cases.md#scenario-tg-03--flaskvue-selected-filter-refresh-regression).
Its parent turn produced no task file, so downstream planning was stopped and
excluded from semantic scoring.

All 18 task-creation assessments covered the approved outcomes. No assessed
producer added a mandatory product obligation.

## Scoring method

The semantic judge records statuses and concrete occurrences. Code derives the
scores:

- fragmentation: none/low/medium/high → 100/67/33/0;
- every other issue: none/partial/present → 100/50/0.

An assessment's success percentage is the equal-weight average of:

1. fragmentation;
2. phase-only children;
3. layer splits without independent value;
4. evidence re-ownership;
5. unsafe dependencies;
6. piecewise production-connection evidence.

Scores do not replace occurrence review. Averages may conceal one severe case.

## Aggregate task-creation quality

| Dimension | Score | Affected assessments | Occurrences |
|---|---:|---:|---:|
| Overall success | 67.4% | — | — |
| Fragmentation | 68.5% | 11/18 | 19 |
| Phase-only children | 50.0% | 10/18 | 14 |
| Layer split without independent value | 72.2% | 6/18 | 11 |
| Evidence re-ownership | 58.3% | 8/18 | 9 |
| Dependency safety | 75.0% | 7/18 | 8 |
| Production-connection evidence | 80.6% | 5/18 | 5 |

Phase-only children and evidence re-ownership are the broadest weaknesses.
Important production connections are less frequent but remain material because
separate mocked/component and direct route checks do not prove the connection.

## Scores by model and effort

| Cohort | Assessments | Overall | Fragmentation | Phase-only | Layer split | Evidence re-ownership | Dependency safety | Production connection |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 18 | 67.4% | 68.5% | 50.0% | 72.2% | 58.3% | 75.0% | 80.6% |
| GLM max | 6 | 84.7% | 83.3% | 83.3% | 75.0% | 100.0% | 91.7% | 75.0% |
| GPT high | 6 | 62.9% | 61.0% | 33.3% | 83.3% | 33.3% | 75.0% | 91.7% |
| GPT xhigh | 3 | 48.2% | 55.7% | 16.7% | 50.0% | 50.0% | 50.0% | 66.7% |
| GPT max | 3 | 61.1% | 66.7% | 50.0% | 66.7% | 33.3% | 66.7% | 83.3% |

Higher GPT effort did not monotonically improve task quality. GPT xhigh
expanded phase and dependency problems most strongly in the three complex
cases.

## Test-case pattern

| Test case | GLM max | GPT high | GPT xhigh | GPT max | Main baseline issue |
|---|---:|---:|---:|---:|---|
| [Scenario TG-01 — Eleventy archive pagination as one task](test-cases.md#scenario-tg-01--eleventy-archive-pagination-as-one-task) | 100.0% | 100.0% | — | — | Clean one-task nonregression case. |
| [Scenario TG-02 — FastAPI notes pagination as one task](test-cases.md#scenario-tg-02--fastapi-notes-pagination-as-one-task) | 100.0% | 55.5% | — | — | GPT split implementation, tests, and documentation into phase children. |
| [Scenario TG-03 — Flask/Vue selected-filter refresh regression](test-cases.md#scenario-tg-03--flaskvue-selected-filter-refresh-regression) | 91.7% | 91.7% | — | — | Both plans proved the client/server connection only piecewise. |
| [Scenario TG-04 — Flask/Vue book-discovery decomposition](test-cases.md#scenario-tg-04--flaskvue-book-discovery-decomposition) | 38.8% | 38.8% | 30.5% | 30.5% | Layer-shaped work, phase children, evidence re-ownership, and crossing gaps. |
| [Scenario TG-05 — FastAPI service, client, and CLI query capability](test-cases.md#scenario-tg-05--fastapi-service-client-and-cli-query-capability) | 100.0% | 52.8% | 52.8% | 91.7% | GPT high/xhigh added final evidence phases; some dependencies serialized independent consumers. |
| [Scenario TG-06 — Eleventy author-metadata compatibility migration](test-cases.md#scenario-tg-06--eleventy-author-metadata-compatibility-migration) | 77.8% | 38.8% | 61.2% | 61.2% | Content/tool splits, final evidence phases, and unsafe intermediate ordering. |

The largest implementation-task count was five. The failure pattern is not
extreme task count; it is using the wrong boundaries within a superficially
reasonable count.

## Handoff findings

All 12 fresh-agent plans were structurally valid and covered the approved
outcomes.

| Test case | Model | Fresh retain calls | Fresh omit calls | Same-agent plan calls |
|---|---|---:|---:|---:|
| [Scenario TG-01 — Eleventy archive pagination as one task](test-cases.md#scenario-tg-01--eleventy-archive-pagination-as-one-task) | GLM max | 24 | 24 | 2 |
| [Scenario TG-01 — Eleventy archive pagination as one task](test-cases.md#scenario-tg-01--eleventy-archive-pagination-as-one-task) | GPT high | 17 | 29 | 3 |
| [Scenario TG-02 — FastAPI notes pagination as one task](test-cases.md#scenario-tg-02--fastapi-notes-pagination-as-one-task) | GLM max | 14 | 23 | 2 |
| [Scenario TG-02 — FastAPI notes pagination as one task](test-cases.md#scenario-tg-02--fastapi-notes-pagination-as-one-task) | GPT high | 18 | 14 | 1 |
| [Scenario TG-03 — Flask/Vue selected-filter refresh regression](test-cases.md#scenario-tg-03--flaskvue-selected-filter-refresh-regression) | GLM max | 15 | 19 | 2 |
| [Scenario TG-03 — Flask/Vue selected-filter refresh regression](test-cases.md#scenario-tg-03--flaskvue-selected-filter-refresh-regression) | GPT high | 10 | 24 | Invalid upstream |

Retained plans usually reduced investigation, but not consistently. Plan
quality, not call count, determines whether saved work is useful.

The incomplete-handoff negative control used 22 calls—nearly the same as the
complete GLM omit handoff's 23—but lost a public requirement question and
required broad reconstruction. No call-count threshold is justified.

## Calibration

Calibration and retries did not change the tested guidance:

- incomplete project fixtures and one hidden target condition were corrected
  before the frozen producer set;
- coordinating parents were excluded from implementation-task counts;
- semantic schema version 2 added explicit issue dimensions and deterministic
  scoring;
- semantic and handoff responses that omitted subjects or failed structural
  validation were rerun;
- invalid upstream task creation is preserved rather than scored downstream.

The matrix remains observational: one frozen producer per
model/effort/test-case identity is not a statistical estimate of response
variance.

## Decision

This baseline justified
[Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate).
The candidate has now been evaluated separately; see
[Task-mechanics candidate results](20260919-task-mechanics-b1-results.md).

## Preserved evidence

- [Frozen baseline records](../../../agent-evaluation/suites/task_guidance/fixtures/results/task_guidance_b0_results.json)
- [Machine status and cohort scores](../../../agent-evaluation/suites/task_guidance/fixtures/results/task_guidance_b0_results.md)
- [Evaluator contracts](../../../agent-evaluation/suites/task_guidance/scenarios/index.md)
- [Suite specification](../../../agent-evaluation/suites/task_guidance/docs/development/specification.md)
- [Execution task](../../../../tasks/20260728-package-local-documentation-standard/090-task-guidance-handoff-baseline-and-placement.md)