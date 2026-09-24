# Task-mechanics candidate results

Revised September 20, 2026, after direct review of the generated task files
and the handoff-test boundaries. Frozen evidence and scores are unchanged; the
promotion interpretation is revised below.

This report compares
[Stage B1 — Task-mechanics candidate](test-plan.md#stage-b1--task-mechanics-candidate)
with
[Stage B0 — Current-guidance baseline](test-plan.md#stage-b0--current-guidance-baseline).
Both use the same six test cases, reviewed targets, fixtures, models, efforts,
semantic schema, and deterministic status-to-score mapping.

## Candidate

The candidate overrides only task guidance. It adds a compact decomposition
block that:

- defaults to one task;
- requires independent acceptance value for each child;
- rejects phase-only implementation, test, documentation, integration,
  cleanup, and review children;
- permits technical-layer children only for independent users, ownership,
  compatibility, or acceptance;
- keeps tests and documentation with the owning result;
- requires safe dependencies and an owner for decisive production-connection
  evidence.

Source:
`maintainer/guidance/candidates/task-mechanics-b1/`.

Current guidance was not modified or promoted.

## Status

| Evidence stage | Expected | Present | Valid | Invalid | Missing |
|---|---:|---:|---:|---:|---:|
| Task creation | 18 | 18 | 18 | 0 | 0 |
| Fresh-agent planning | 12 | 12 | 12 | 0 | 0 |
| Same-agent planning | 6 | 6 | 5 | 1 | 0 |
| Task semantic assessment | 6 batches | 6 | — | — | 0 |
| Handoff semantic assessment | 3 batches | 3 | — | — | 0 |
| Incomplete-handoff negative control | 1 | 1 | — | — | 0 |

The same GPT-high selected-filter same-agent chain remained invalid because its
parent turn created no task file. The candidate did not improve that behavior.

All 18 task-creation assessments covered the approved outcomes. One GLM
multi-consumer task recommended package version bumps but kept them explicitly
approval-gated rather than making them a completion requirement.

## Models, efforts, and retries

Task creation used:

- GLM-5.3-flash at max effort for all six test cases;
- GPT-5.6-luna at high effort for all six test cases;
- GPT-5.6-luna at xhigh and max effort for the three decomposition cases.

Fresh-agent and same-agent planning used GLM max and GPT high for the three
bounded handoff cases.

Three GPT producer identities received one focused retry:

- high-effort notes pagination initially produced no task file;
- high-effort book discovery initially produced no task file;
- max-effort book discovery had an incomplete provider stream.

All three retries passed under fresh cache identities. The frozen matrix uses
the latest valid record for each canonical identity; the original invalid raw
records remain in the run directory.

Candidate workspace preparation also exposed an evaluator defect: it tried to
copy `documentation.md` directly from the overlay directory instead of
resolving inherited sections. The compiler now resolves inherited bundle
sections, and a deterministic regression test covers that path. The failed
pre-model setup attempts are not behavior evidence.

## Aggregate comparison

| Dimension | Baseline | Candidate | Delta | Affected assessments | Occurrences |
|---|---:|---:|---:|---:|---:|
| Overall success | 67.4% | 87.0% | +19.6 | — | — |
| Fragmentation | 68.5% | 83.3% | +14.8 | 11 → 6 | 19 → 6 |
| Phase-only children | 50.0% | 100.0% | +50.0 | 10 → 0 | 14 → 0 |
| Layer split without independent value | 72.2% | 83.3% | +11.1 | 6 → 3 | 11 → 6 |
| Evidence re-ownership | 58.3% | 100.0% | +41.7 | 8 → 0 | 9 → 0 |
| Dependency safety | 75.0% | 80.6% | +5.6 | 7 → 6 | 8 → 6 |
| Production-connection evidence | 80.6% | 75.0% | **−5.6** | 5 → 5 | 5 → 5 |

The candidate completely removed phase-only children and evidence
re-ownership in this matrix. It also reduced fragmentation and dependency
problems. It did not reduce the number of production-connection failures and
made their severity worse overall.

## Success by model and effort

| Cohort | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| All | 67.4% | 87.0% | +19.6 |
| GLM max | 84.7% | 95.8% | +11.1 |
| GPT overall | 58.8% | 82.6% | +23.8 |
| GPT high | 62.9% | 88.9% | +26.0 |
| GPT xhigh | 48.2% | 75.0% | +26.8 |
| GPT max | 61.1% | 77.8% | +16.7 |

The improvement is broad across models and efforts, but aggregate totals hide
the crossing regression and handoff-quality losses described below.

## Candidate scores by dimension

| Cohort | Overall | Fragmentation | Phase-only | Layer split | Evidence re-ownership | Dependency safety | Production connection |
|---|---:|---:|---:|---:|---:|---:|---:|
| All | 87.0% | 83.3% | 100.0% | 83.3% | 100.0% | 80.6% | 75.0% |
| GLM max | 95.8% | 100.0% | 100.0% | 100.0% | 100.0% | 91.7% | 83.3% |
| GPT high | 88.9% | 83.3% | 100.0% | 83.3% | 100.0% | 91.7% | 75.0% |
| GPT xhigh | 75.0% | 66.7% | 100.0% | 66.7% | 100.0% | 50.0% | 66.7% |
| GPT max | 77.8% | 66.7% | 100.0% | 66.7% | 100.0% | 66.7% | 66.7% |

## Remaining occurrences

### Fragmentation

Six assessments remain affected:

- GPT high, xhigh, and max book discovery each created two horizontal
  server/client workstreams instead of end-to-end capability slices;
- GPT high, xhigh, and max author migration each retained one low-severity
  split or overpacked working-state boundary.

### Layer splits without independent value

All six occurrences are in GPT book discovery. The API child is testable and
reviewable, but every approved user-facing filtering, search, and pagination
outcome still crosses both children. API testability alone did not produce an
independent product capability.

### Unsafe dependencies

Six assessments remain affected:

- all four book-discovery efforts contain either missing fixture dependencies
  or whole-workstream serialization;
- GPT xhigh and max author migration allow or risk content conversion before
  compatible consumers are guaranteed.

### Production-connection evidence

Five assessments remain affected:

- GLM and GPT selected-filter tasks still use mocked component checks and
  separate Flask route checks without one decisive Vue → production transport
  → Flask → rendering check;
- GPT high, xhigh, and max book-discovery tasks similarly stop at adapter,
  router, or direct Flask boundaries instead of naming a live client-to-server
  check.

Phase-only children and evidence re-ownership have zero candidate occurrences.

## Test-case comparison

| Test case | Baseline → candidate | Interpretation |
|---|---:|---|
| [Scenario TG-01 — Eleventy archive pagination as one task](test-cases.md#scenario-tg-01--eleventy-archive-pagination-as-one-task) | GLM 100.0 → 100.0; GPT 100.0 → 100.0 | Clean nonregression. |
| [Scenario TG-02 — FastAPI notes pagination as one task](test-cases.md#scenario-tg-02--fastapi-notes-pagination-as-one-task) | GPT 55.5 → 100.0 | The implementation/test/docs phase split disappeared. |
| [Scenario TG-03 — Flask/Vue selected-filter refresh regression](test-cases.md#scenario-tg-03--flaskvue-selected-filter-refresh-regression) | GLM 91.7 → 83.3; GPT 91.7 → 91.7 | Task shape stayed clean, but decisive crossing evidence did not improve and became more severe for GLM. |
| [Scenario TG-04 — Flask/Vue book-discovery decomposition](test-cases.md#scenario-tg-04--flaskvue-book-discovery-decomposition) | GLM 38.8 → 91.7; GPT high 38.8 → 47.2; GPT xhigh/max 30.5 → 47.2 | Phase tasks disappeared. GLM produced coherent capability slices; GPT converged on two horizontal layer workstreams and retained crossing gaps. |
| [Scenario TG-05 — FastAPI service, client, and CLI query capability](test-cases.md#scenario-tg-05--fastapi-service-client-and-cli-query-capability) | GLM 100.0 → 100.0; GPT high/xhigh 52.8 → 100.0; GPT max 91.7 → 100.0 | Valid component boundaries remained while generic evidence children and unnecessary dependencies disappeared. |
| [Scenario TG-06 — Eleventy author-metadata compatibility migration](test-cases.md#scenario-tg-06--eleventy-author-metadata-compatibility-migration) | GLM 77.8 → 100.0; GPT high 38.8 → 94.5; GPT xhigh 61.2 → 77.8; GPT max 61.2 → 86.2 | Strong improvement, with remaining GPT content/tool splits and intermediate-state risks. |

## Handoff comparison

The candidate retained 12/12 valid fresh-agent plans and the same 5/6 valid
same-agent result. It did not improve the invalid GPT selected-filter
same-agent chain.

Tool-call counts generally fell, but semantic handoff quality was mixed:

- GPT archive generated-task planning improved from 75 to 81, but its
  omitted-plan score fell from 91 to 78 and lost decisive testing;
- notes-pagination handoff scores remained broadly similar;
- GLM selected-filter generated-task planning fell from 84/complete to
  72/partial, while fresh retained and omitted plans remained complete;
- GPT selected-filter fresh plans improved slightly but still had only partial
  testing boundaries.

Under the original acceptance gate, the candidate did not satisfy handoff
nondegradation merely because investigation became cheaper.

This comparison has an important limitation. Fresh-agent planning uses
reviewed canonical task files. Candidate-generated task files are continued
only by the same session that created them. The handoff evidence therefore
tests whether a good handoff supports replanning, but it does not yet prove
that task files generated under this candidate preserve enough implementation
design for an unrelated agent.

## Direct review of the generated task files

The direct review found that candidate v1 usually produces more coherent and
substantial plans than the aggregate decision suggested:

- simple changes generally remain one self-contained task with requirements,
  supporting facts, public-contract questions, an implementation approach,
  and requirement-level verification;
- the GLM book-discovery result contains four end-to-end capability children
  and an explicit parent design covering server, client, transport, routing,
  dependencies, risks, and decisive evidence;
- the multi-consumer and author-migration results substantially reduce generic
  test, documentation, cleanup, and final-review children while preserving
  approved outcomes and compatibility constraints.

The remaining plan-quality problem is consistency and findability. Some
Execution plans clearly explain component responsibilities, interfaces,
working states, and rationale. Others are primarily ordered server/client/test
steps, with important design spread across scope, supporting facts, decisions,
and child files. Complex task sets range from roughly 2,500 to 5,300 words and
sometimes repeat parent-level questions, facts, documentation plans, and
verification in every child.

Current semantic assessment does not directly score:

- preservation of a reviewed implementation design when a plan becomes a task;
- fresh-agent continuation from an agent-generated task file;
- whether component responsibilities and interactions are easy to find;
- whether an Execution plan is more than ordered steps;
- proportionate duplication between a parent and its children.

## Revised decision

Do not promote candidate v1 verbatim, but do use it as the evidence-backed
foundation for a practical task-mechanics baseline.

The earlier decision treated two findings as hard blockers:

1. important production-connection evidence regressed from 80.6% to 75.0%;
2. several handoff semantic scores regressed, and the invalid same-agent chain
   remained.

That threshold was too conservative relative to the known defect on
`develop`, which has no meaningful decomposition instructions. Candidate v1:

- keeps approved-outcome coverage complete in all 18 task-creation
  assessments;
- eliminates all observed phase-only children and evidence re-ownership;
- reduces fragmentation occurrences from 19 to 6;
- materially improves every reported model/effort cohort;
- leaves production-connection affected-assessment and occurrence counts
  unchanged at five, despite a lower severity score;
- retains the same 12/12 valid fresh-agent plans and 5/6 valid same-agent
  chains.

The production-connection findings are real testing-strategy weaknesses, but
they do not outweigh the demonstrated decomposition gains. The handoff score
changes are also not direct evidence that candidate-generated tasks became
worse because the fresh-agent inputs were unchanged canonical handoffs.

The practical baseline should retain candidate v1 and add concise guidance
that:

- a technical layer's API testability is not independent value when every
  approved user-facing capability still crosses another child;
- separate component/adapter and route checks do not satisfy a required
  production connection—one named check must traverse the real connected
  components;
- every child completion state allowed by declared dependencies must remain
  usable and compatible;
- a retained plan preserves implementation design, rationale, component
  responsibilities, interfaces or data flow, compatibility/dependency states,
  material decisions, and verification strategy;
- a nontrivial Execution plan explains the design rather than consisting only
  of ordered work steps;
- the parent owns shared end-to-end design, requirement ownership,
  cross-cutting decisions, dependency states, and decisive crossings, while
  children keep local design and evidence without repeating the parent.

Focused confirmation should add one plan-to-task preservation chain and one
fresh-agent continuation from generated task files, then exercise
selected-filter refresh, book discovery, and author-migration working states.
Archive pagination, notes-pagination GPT high, and the multi-consumer case
remain compact nonregression checks. Another full calibration matrix is needed
only if focused evidence exposes a material uncertainty.

[Stage B2 — Guidance-placement confirmation](test-plan.md#stage-b2--guidance-placement-confirmation)
must not start until the practical baseline wording is explicitly approved and
the focused confirmation passes.

## Preserved evidence

- [Candidate result package](results/20260919-task-mechanics-b1/index.md) —
  the committed, self-contained records for this evaluation: every run,
  generated task file, session transcript, semantic assessment, and cost row,
  with [matrix](results/20260919-task-mechanics-b1/matrix.md) and
  [cost](results/20260919-task-mechanics-b1/costs.md) views
- [Baseline result package](results/20260919-current-guidance-b0/index.md)
- [Scenario input definitions](scenarios/index.md) — the reviewed targets,
  exact prompts, shared configs and system messages, and every file added to
  the workspaces beyond the repository checkout
- [Candidate source](../../../guidance/candidates/task-mechanics-b1/README.md)
- [Reproduction and inspection guide](reproducing-and-inspecting-results.md)
- [Execution task](../../../../tasks/20260728-package-local-documentation-standard/090-task-guidance-handoff-baseline-and-placement.md)