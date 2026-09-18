# Requirement and testing guidance v3 results

Date: September 15, 2026

Candidate v3 applies the user-approved selective ablation to the requirement
and testing guidance. It preserves v2's task-creation and final-section rules,
makes approval-gated recommendations explicitly non-normative, and restores
shorter testing guidance.

## Recommendation

Accept v3 as the requirement/testing guidance.

V3 is the best balanced result:

- all 21 task files are structurally valid and leave only the requested task
  mutation;
- all 21 requirement sets cover the approved target;
- requirement expansion improves over current and v2 guidance;
- 13 of 21 testing plans contain complete decisive evidence, the best result
  of the compared versions;
- no plan receives a poor primary-layer assessment;
- the two remaining missing crossings and four material public-decision
  mistakes remain useful calibration cases.

Do not add more recurring guidance for those residual failures. V2 demonstrated
that a larger testing checklist can reduce testing quality. Keep the failures
visible in evaluation and revisit wording only if another project exposes a
repeatable pattern.

## V3 wording

V3 retains:

- minimum necessary, traceable requirements;
- grouped variants without hiding approved conditions;
- public and persisted behavior as approval-gated decisions;
- bounded task-file planning with no repository scratch implementation;
- one required final-section sequence;
- user-relevant requirement verification;
- separation of acceptance evidence, implementation robustness, and routine
  quality checks.

V3 changes:

- an unresolved recommendation may explain tradeoffs but remains outside
  requirements and implementation until approved;
- recurring accepted/rejected-boundary wording is removed;
- recurring missing-test-harness wording is removed;
- testing returns to selecting the least expensive reliable boundary;
- a mock that supplies or bypasses the behavior is explicitly non-decisive;
- existing tests count only when they prove the preserved behavior; otherwise
  the plan identifies focused evidence or records the gap.

The exact guidance-source hash used by all 21 producers is:

`e774becd184a8154dacd50bfc82c05132b444937c3cb687a4b9ae599ba720bef`

## Execution

The focused gate ran ten cells selected from prior failures:

- Eleventy GLM max;
- FastAPI GLM low/max and GPT high/max;
- Flask/Vue GLM low/high/max and GPT medium/max.

Compared with v2 in those cells, v3 improved complete testing plans from 1 to
3, appropriate primary layers from 3 to 5, and removed the one poor-layer
assessment. This met the approved condition for running the complete matrix.

The remaining eleven producer cells then ran without changing guidance. All
21 producers passed the task-only structural and mutation checks.

Three full semantic batches assessed all seven model/effort profiles for each
project. The semantic judge used `glm-5.3-flash:cloud` at max effort.

## Aggregate comparison

| Measure | Current | Candidate v1 | Candidate v2 | Candidate v3 |
|---|---:|---:|---:|---:|
| Structurally valid task-only plans | 18 | 18 | 21 | **21** |
| Complete requirement coverage | **21** | 18 | **21** | **21** |
| No expansion | 5 | 10 | 2 | **7** |
| Low expansion | 11 | 9 | 14 | **10** |
| Medium expansion | 5 | 2 | 5 | **4** |
| Complete testing evidence | 12 | 7 | 5 | **13** |
| Partial testing evidence | 9 | 13 | 16 | **8** |
| Appropriate primary layer | **20** | 18 | 11 | 16 |
| Mixed primary layer | **1** | 2 | 9 | 5 |
| Poor primary layer | **0** | 1 | 1 | **0** |
| Important crossing present | **20** | 19 | 19 | 19 |
| No duplicated testing | 11 | 16 | **19** | 18 |
| No combinatorial expansion | **18** | 20 | 15 | **18** |
| Focused verification | 18 | 18 | **19** | **19** |

Requirement coverage and testing measures are directly comparable. V3 uses the
approved evaluator rule that an approval-gated recommendation outside
requirements and implementation is not expansion. Earlier versions used the
previous rubric: three of v2's five medium labels arose from recommendations
that did not yet become completion obligations. The old expansion columns are
therefore useful historical results but not an exact controlled comparison for
that one classification.

All four v3 medium-expansion results are normative choices, not merely
recommendations.

## Results by project

| Project | Requirement result | Testing result |
|---|---|---|
| Eleventy | 7/7 complete; 2 none, 5 low, 0 medium expansion | 7/7 complete; 7 appropriate layers; 7 crossings present |
| FastAPI | 7/7 complete; 4 none, 1 low, 2 medium expansion | 2 complete, 5 partial; 5 appropriate and 2 mixed layers; all crossings present |
| Flask/Vue | 7/7 complete; 1 none, 4 low, 2 medium expansion | 4 complete, 3 partial; 4 appropriate and 3 mixed layers; 5 crossings present |

### Eleventy

V3 fully recovers the archive scenario. Every producer uses the generated-site
boundary, preserves protected surfaces, and avoids combinatorial testing.
Minor findings concern exact navigation markup, compatibility-row splitting,
or review length; they do not omit an outcome or decisive boundary.

### FastAPI

Requirement restraint improves substantially. Four producers add no semantic
scope and one adds only minor scope.

Two public-decision failures remain:

- GLM low selects `limit=100` for offset-only requests while calling the choice
  local and reversible.
- GPT xhigh makes an omitted `limit` mean no page-size restriction and declares
  that no question remains.

GLM max and GPT medium provide complete boundary-level testing. The five
partial plans generally omit valid boundary values, use mocked ordering, or add
internal database-query assertions. All seven retain the public HTTP crossing.

### Flask/Vue

V3 recovers four complete testing plans from a v2 result of zero. GLM low,
GLM high, GPT high, and GPT max cover the client/server flow.

Two requirement failures remain:

- GLM low selects unknown `read` values as unfiltered behavior.
- GLM high makes the same behavior normative while asserting it is not a new
  public decision.

GLM max and GPT medium still test client and server separately and miss the
real crossing. GPT xhigh includes the crossing but remains partial for other
evidence. These failures should remain evaluation sentinels.

## Why further wording is not recommended

The remaining errors already contradict clear v3 rules:

- public behavior is material and approval-gated;
- recommendations stay outside implementation;
- a real boundary is required when the behavior appears only there;
- a mock that supplies the behavior is not decisive evidence.

Adding the literal examples—unknown query values, omitted pagination
companions, Axios arguments, or database query shape—would overfit three
fixtures and make the general guide less portable. V2 also shows that more
testing instructions can increase mixed layers, combinations, and
implementation coupling.

The proportionate response is to accept v3, retain the diverse scenarios, and
revisit only a repeated failure found in future work.

## Evaluation reliability

- All 21 producer records use the same guidance hash and contain one task-file
  mutation.
- Producer profiles are GLM low/high/max and GPT medium/high/xhigh/max.
- GPT runs use the configured ChatGPT login.
- One full FastAPI judge response contained a trailing comma. A
  content-preserving parser repair removed only that comma.
- Some judge runs attempted invalid shell calls despite the JSON-only prompt.
  The harness returned an error message to the judge; complete final JSON
  followed and validated.
- Frozen v3 records retain prompts, targets, model/effort, guidance hashes,
  generated task files, semantic results, repairs, and findings.

## Human decision

Please confirm:

1. Accept v3 as the final requirement/testing guidance.
2. Keep the four normative public-decision mistakes and two missing crossings
   as calibration limits rather than adding more standing wording.

After acceptance, subtask 069 can commit the guidance checkpoint and continue
to the separately planned task-decomposition baseline.

## Evidence

- [Current/v1/v2 candidate results](20260915-requirement-testing-candidate-results.md)
- [V3 task records](../../../agent-evaluation/suites/documentation_standard/fixtures/candidate_v3_task_guidance_requirement_quality_dataset.json)
- [V3 semantic results](../../../agent-evaluation/suites/documentation_standard/fixtures/requirement_quality_candidate_v3_semantic_results.json)
- [Owning task](../../../../tasks/20260728-package-local-documentation-standard/069-task-guidance-scope-and-decomposition.md)