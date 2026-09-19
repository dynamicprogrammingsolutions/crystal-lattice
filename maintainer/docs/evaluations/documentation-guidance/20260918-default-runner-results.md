# Corrected default-runner guidance results

## Status

The corrected matrix is complete:

- 84 valid producer records;
- 84 semantic assessments in 12 project/bundle/mode batches;
- 42 valid pairwise quality reviews;
- no missing producer, semantic, or pairwise identity;
- no unresolved structured-output error.

This is the first matrix in this workstream that represents the ordinary
Crystal Lattice Codex and Claude runner closely enough for candidate decisions.
The earlier September 18 matrix remains historical direct-injection evidence.

## Tested runner

Each fixture used a reduced projection of the bundled default configuration:

- GPT-5.6-luna used the standard Codex developer message and Codex tool package;
- GLM-5.3-flash used the standard Claude system message and Claude tool package;
- fixture `AGENTS.md` was loaded by the normal model-family helper;
- canonical `TASKS_v7.md` was included only when `include_tasks=true`;
- no suite-owned guidance injector supplied AGENTS or TASKS;
- preflights verified source occurrence counts and the effective shell schema:
  Codex `shell.command` is an array and Claude `Bash.command` is a string.

The matrix used three fixture projects, root-only and task-file modes, seven
model/effort profiles, and baseline versus combined-v2 guidance.

Five incomplete producers were retried without changing the canonical
`default-runner-r2` dataset identity. Nine malformed pairwise responses were
similarly retried. Behavioral assertion failures, such as a missing task-plan
section, were retained as evidence rather than misclassified as invalid input.
Accordingly, the machine analysis's `producer_failures` count refers to eight
retained behavioral assertion sets; all 84 producer records pass the upstream
validity gate.

## Aggregate semantic results

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirements | **36/42** | 35/42 |
| Partial requirements | 6/42 | 7/42 |
| Average coverage score | **94.3** | 93.3 |
| Average scope-restraint score | 42.9 | **66.7** |
| High expansion | 8 | **1** |
| No expansion | 4 | **14** |
| Complete testing plans | 14/42 | **18/42** |
| Average testing score | 75.5 | **86.5** |
| Appropriate test layers | 25/42 | **37/42** |
| Important crossing present | 31/42 | **41/42** |
| Effort expectation met | 11/42 | **18/42** |

Combined-v2 strongly improves scope restraint and testing, but it does not
satisfy the strict requirement-completeness gate. It loses one complete cell
overall.

## Results by delivery mode

### Root-only

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirements | **16/21** | 15/21 |
| High expansion | 7 | **1** |
| No expansion | 0 | **3** |
| Complete testing | 3/21 | **7/21** |
| Appropriate layers | 11/21 | **19/21** |
| Important crossing present | 14/21 | **20/21** |

Combined-v2 is much more disciplined and test-aware, but root-only requirement
coverage remains the main weakness.

### Task mode

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirements | 20/21 | 20/21 |
| High expansion | 1 | **0** |
| No expansion | 4 | **11** |
| Complete testing | 11/21 | 11/21 |
| Appropriate layers | 14/21 | **18/21** |
| Important crossing present | 17/21 | **21/21** |

Task guidance already improves structure and requirement-role separation, so
the candidate's advantage is smaller than in root-only mode. It nevertheless
removes high expansion and closes all important-crossing gaps.

## Pairwise review

Combined-v2 is preferred overall in 34 of 42 cells.

| Mode | Combined-v2 | Baseline |
|---|---:|---:|
| Root-only | **20** | 1 |
| Task | **14** | 7 |
| Total | **34** | 8 |

Dimension preferences:

| Mode | Dimension | Combined-v2 | Baseline | Tie |
|---|---|---:|---:|---:|
| Root-only | Requirements | **17** | 3 | 1 |
| Root-only | Testing | **18** | 3 | 0 |
| Root-only | Plan usability | **12** | 3 | 6 |
| Task | Requirements | **11** | 8 | 2 |
| Task | Testing | **12** | 7 | 2 |
| Task | Plan usability | **10** | 8 | 3 |

Every model/effort group prefers combined-v2 more often than baseline:

- GLM low: 6–0;
- GLM high: 4–2;
- GLM max: 4–2;
- GPT medium: 5–1;
- GPT high: 6–0;
- GPT xhigh: 5–1;
- GPT max: 4–2.

## Effort-sensitive findings

The candidate behaves especially well at GPT high and xhigh:

- GPT high keeps 6/6 requirement sets complete, has all six important
  crossings, and wins all six pairwise reviews;
- GPT xhigh keeps 5/6 complete, has all six crossings, and wins five of six.

Max effort remains a warning:

- baseline max has 10/12 complete requirement sets;
- combined-v2 max has 9/12 complete;
- combined-v2 GLM max has only 4/6 complete;
- pairwise still favors combined-v2 8–4 at max because scope and testing often
  improve despite the coverage loss.

Better restraint does not compensate for omitting an approved outcome at a
high-assurance effort level.

## Scenario patterns

### Eleventy archive pagination

Both variants cover the target well. Combined-v2 greatly reduces expansion,
but task-mode GLM max drops the accessibility quality from the previous/next
navigation requirement. This is the candidate's additional partial cell.

### FastAPI notes pagination

Combined-v2 keeps all 14 requirement sets complete and improves complete
testing from 3 to 8. Remaining expansion is concentrated in:

- documentation production promoted into product requirements;
- one GPT-medium requirement mandating storage/query-boundary mechanics;
- one GPT-xhigh requirement selecting behavior for an omitted companion
  parameter.

### Flask/Vue book filter

Both variants have 8/14 complete requirement sets. Combined-v2 transforms the
testing result: important crossings improve from 3/14 to 13/14 and every test
plan uses an appropriate layer except bounded mixed cases.

The recurring requirement omission is narrow and consistent: six root-only
candidate outputs require the All/Read/Unread choices or default selection but
do not require the active choice to be visibly identifiable. One remaining
crossing gap appears in GPT-max root-only.

## Recommendation

Do not promote combined-v2 unchanged.

Retain its demonstrated direction:

- strong reduction in high and medium expansion;
- better separation of unresolved public choices;
- much better test-layer selection;
- nearly complete important-crossing coverage;
- strong preference under every model/effort group.

Create a short v3 candidate addressing only observed gaps:

1. After grouping or removing requirement rows, trace every approved outcome
   and condition to a remaining requirement. A recommendation or plan detail
   does not count as requirement coverage.
2. An applicable rule requiring documentation to change makes documentation
   plan work; it does not make documentation production a product requirement
   unless that documentation outcome is independently requested.
3. Preserve the existing rules that unresolved public behavior remains a
   question and that internal mechanisms are not authorized requirements.

Calibrate first against the sensitive cells:

- Flask/Vue root-only active-choice visibility at GLM low/high/max and GPT
  medium/xhigh/max;
- Eleventy task-mode GLM max accessibility;
- FastAPI root-only GPT medium and xhigh expansion.

If that focused comparison restores coverage without losing the candidate's
scope/testing gains, run the full effort-aware matrix before adoption.

## Preserved evidence

- Machine results:
  `maintainer/agent-evaluation/suites/documentation_standard/fixtures/results/compiled_guidance_default_runner_20260918_results.json`
- Effort-aware analysis:
  `maintainer/agent-evaluation/suites/documentation_standard/fixtures/results/compiled_guidance_default_runner_20260918_analysis.json`
- Historical direct-injection comparison:
  `maintainer/docs/evaluations/documentation-guidance/20260918-portable-root-guidance-results.md`