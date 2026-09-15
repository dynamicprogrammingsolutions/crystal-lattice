# Requirement and testing guidance candidate results

Date: September 15, 2026

This report compares the committed current-guidance baseline with two
successive requirement/testing candidates. It covers the same three projects,
seven model/effort profiles, task prompt, fixtures, semantic targets, task
structure checks, and calibrated requirement/testing evaluator.

The candidate task prompt remained:

> Create one task file with a Draft execution plan for this change. Do not
> implement the change.

It did not ask for a testing strategy.

## Decision summary

Candidate v2 was not accepted as a complete requirement/testing rewrite. It
has three different outcomes:

1. **Keep the task-structure direction.** V2 gives 21 of 21 structurally valid
   task-only plans. It fixes the prior scratch-output, incomplete max-effort,
   misordered closing-section, and premature-note cases in this matrix.
2. **Retain but refine the requirement direction.** V2 restores complete
   requirement coverage in all 21 cells and avoids high expansion, but it
   produces more low/medium expansion and review burden than current guidance.
3. **Do not accept the v2 testing wording.** Testing completeness and layer
   choice regress materially. More explicit boundary/checklist instructions
   lead to more mechanical enumeration and mixed-layer plans without reliably
   producing the missing frontend/backend crossing.

On September 15, 2026, the user approved accepting the task-structure
direction independently, retaining and refining the requirement direction,
treating approval-gated public-contract recommendations as expansion only when
they become normative, and proceeding with the shorter testing ablation below.
Decomposition testing remains deferred until that candidate is calibrated.

## Compared guidance

| Version | Description |
|---|---|
| Current | General documentation guidance and task guidance pinned to commit `73a2f4bf` |
| Candidate v1 | Initial approved replacement: necessity/traceability, public-decision authority, concise planning cleanup, and boundary-focused verification |
| Candidate v2 | V1 plus preserved grouped conditions, no invented input fallback, stronger task-creation limits, exact final headings, accepted/rejected boundary language, actual-existing-test language, and missing-harness guidance |

All candidate v1 and v2 producer and semantic records are frozen under
`maintainer/agent-evaluation/suites/documentation_standard/fixtures/`.

## Task structure and workspace behavior

| Version | Structural/task-only passes | Important failures |
|---|---:|---|
| Current | 18/21 | Eleventy high generated output; FastAPI low omitted a closing section; FastAPI high added premature notes |
| Candidate v1 | 18/21 | Eleventy max produced no task and left a large scratch tree; FastAPI low and Flask/Vue low misordered final sections |
| Candidate v2 | 21/21 | None after correcting the parser to reject actual note headings rather than inline mentions |

The v2 task-creation wording has direct behavioral support:

- the previously incomplete GLM-max Eleventy cell produces one task;
- no producer installs dependencies or leaves a scratch implementation;
- all final H3 sections appear once and in the required order;
- all 21 workspaces contain only the requested task-file change.

## Requirement quality

### Aggregate results

| Measure | Current | Candidate v1 | Candidate v2 |
|---|---:|---:|---:|
| Complete coverage | 21 | 18 | 21 |
| Partial coverage | 0 | 2 | 0 |
| Missing coverage | 0 | 1 | 0 |
| No expansion | 5 | 10 | 2 |
| Low expansion | 11 | 9 | 14 |
| Medium expansion | 5 | 2 | 5 |
| High expansion | 0 | 0 | 0 |
| Low review burden | 14 | 18 | 13 |
| Medium review burden | 7 | 3 | 8 |

Candidate v1 achieved the cleanest requirement sets but lost two Flask/Vue
conditions and one complete producer result. Candidate v2 restores all approved
outcomes, including visible active filter state, but the stronger wording
encourages more acceptance mechanics, compatibility splitting, and material
recommendations.

### Project patterns

**Eleventy**

- V2 restores the max-effort producer and complete coverage in all seven cells.
- Several candidates still prescribe exact accessibility markup or split
  protected compatibility surfaces.
- Later-page URL choices are generally raised instead of silently fixed.

**FastAPI**

- All seven v2 candidates cover the eight approved outcomes.
- Most candidates now raise the single-parameter default instead of silently
  making it normative.
- GLM low adds a database query-strategy constraint.
- GLM high and GPT high still make or recommend companion-parameter choices
  strongly enough to be classified as medium expansion.

**Flask/Vue**

- V2 restores complete coverage in all seven cells, including visible active
  filter state.
- GLM low still defines behavior for unknown `read` values.
- GLM high raises a 400-error recommendation. It is approval-gated rather than
  normative, but the evaluator treats the new public response contract as a
  material unresolved design addition.
- GPT candidates generally keep unknown-value behavior outside the contract.

The next refinement should distinguish recording a public requirement question
from recommending a new public contract. A recommendation should not become a
completion obligation, and agents should avoid selecting an answer merely to
make the plan complete.

## Testing-plan quality

### Aggregate results

| Measure | Current | Candidate v1 | Candidate v2 |
|---|---:|---:|---:|
| Complete decisive evidence | 12 | 7 | 5 |
| Partial evidence | 9 | 13 | 16 |
| Missing evidence | 0 | 1 | 0 |
| Appropriate primary layer | 20 | 18 | 11 |
| Mixed primary layer | 1 | 2 | 9 |
| Poor primary layer | 0 | 1 | 1 |
| Important crossing present | 20 | 19 | 19 |
| Important crossing missing | 1 | 2 | 2 |
| No duplication | 11 | 16 | 19 |
| No combinatorial expansion | 18 | 20 | 15 |
| Focused verification | 18 | 18 | 19 |

V2 produces less duplicated prose, but that is outweighed by reduced decisive
coverage and more mixed-layer or combinatorial plans.

### Project patterns

**Eleventy**

- Five of seven v2 plans are complete.
- All seven use the generated-site boundary.
- Partial plans omit one protected-surface or exact archive-set check rather
  than choosing the wrong overall layer.

**FastAPI**

- All seven remain partial.
- Several v2 plans add real data-access checks and accepted/rejected boundaries.
- No plan gives unconditional focused regression evidence for all four
  protected item/mutation endpoints.
- Some plans still assert internal SQL/call placement rather than only the
  required ordering, count, body, and compatibility behavior.

**Flask/Vue**

- All seven v2 plans are partial.
- Server-boundary coverage improves, but most plans make client verification
  manual because the fixture lacks an existing client harness.
- GPT medium relies on separate mocked client and server checks and misses the
  production crossing.
- GPT max also leaves the client-to-Flask crossing under-specified.
- The v2 “missing infrastructure” rule does not reliably produce a small
  harness; it often adds explanation while leaving the evidence partial.

### Interpretation

The v2 testing text combines too many desirable checks in recurring task
guidance:

- accepted and rejected boundaries;
- preserved-behavior regression evidence;
- existing-test validation;
- missing-harness behavior;
- real crossings;
- implementation-coupling avoidance.

Models respond by enumerating checks, adding internal mechanics, or mixing
manual and mocked evidence. The results support a shorter principle-based rule
instead of another checklist.

## Recommended next candidate

Do not extend v2 with more testing bullets. Use an ablation:

1. Keep v2 task-creation limits and exact final-heading rule.
2. Keep requirement necessity, traceability, preserved grouped conditions, and
   public-question handling.
3. Refine public-decision wording so approval-gated questions remain visible
   without selecting a new fallback/error contract by default.
4. Restore testing wording close to the current baseline.
5. Retain only two evidence-backed testing refinements:
   - a mock that supplies or bypasses the claimed result is not decisive
     evidence;
   - cite existing test coverage only when it actually proves the preserved
     behavior; otherwise plan focused evidence or record the gap.
6. Remove the recurring accepted/rejected-boundary and missing-harness
   instructions from `TASKS-v7`. Keep proportional examples in the general
   guide only if a focused comparison supports them.

This candidate should first run the known-sensitive cells:

- Eleventy GLM max;
- FastAPI GLM low/max and GPT high/max;
- Flask/Vue GLM low/high/max and GPT medium/max.

If structure remains clean and testing behavior improves, run the full 21 cells
and three semantic batches. Do not begin the six decomposition scenarios until
that comparison is accepted.

## Human review decision

The user approved all four decisions on September 15, 2026:

1. Accept v2 task-creation limits and final-heading rules independently.
2. Retain v2's complete-coverage requirement direction and refine its remaining
   low/medium expansion.
3. Count an approval-gated recommendation for unspecified public behavior as
   expansion only if it becomes normative in requirements or implementation.
4. Run the shorter testing ablation before decomposition work.

## Evidence

- [Current baseline and candidate-v1 interpretation](20260915-requirement-task-testing-comparison.md)
- [Candidate v1 task records](../../../agent-evaluation/suites/documentation_standard/fixtures/candidate_task_guidance_requirement_quality_dataset.json)
- [Candidate v1 semantic results](../../../agent-evaluation/suites/documentation_standard/fixtures/requirement_quality_candidate_semantic_results.json)
- [Candidate v2 task records](../../../agent-evaluation/suites/documentation_standard/fixtures/candidate_v2_task_guidance_requirement_quality_dataset.json)
- [Candidate v2 semantic results](../../../agent-evaluation/suites/documentation_standard/fixtures/requirement_quality_candidate_v2_semantic_results.json)
- [Owning task](../../../../tasks/20260728-package-local-documentation-standard/069-task-guidance-scope-and-decomposition.md)