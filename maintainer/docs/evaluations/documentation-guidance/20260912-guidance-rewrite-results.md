# Documentation guidance rewrite results

Date: September 12, 2026

## Compared inputs

- Model: `glm-5.3-flash:cloud`
- Previous guidance: committed `develop` revision
  `f81f36326b58268297ba59c1cacbcda604257c27`
- Rewritten guidance: commit `24ba9c24`
- Profile/cache version: v8
- Previous guidance paths: root AGENTS plus the former standards and repository
  pages
- Rewritten guidance paths: root AGENTS, development index, documentation
  guide, and Crystal Lattice conventions

The comparison used the same guidance-neutral seeds, task prompts, fixtures,
model, tools, and deterministic assertions for each paired branch. Local Core,
Application, evaluation, and built-in plugin paths were pinned to the rewrite
worktree.

## Matrix summary

| Matrix | Passed | Failed | Obsolete deselected |
|---|---:|---:|---:|
| Previous guidance, all 21 legacy tests | 13 | 8 | 0 |
| Rewritten guidance, the same 21 legacy tests | 14 | 7 | 0 |
| Previous guidance, calibrated revised suite | 19 | 7 | 5 |
| Rewritten guidance, calibrated revised suite | 22 | 4 | 5 |

The first uncalibrated revised matrices were also preserved. Calibration changed
only assertion recognition and obsolete-test selection; it did not change
guidance, prompts, fixtures, or model outputs.

## Same-test legacy comparison

Improvements under rewritten guidance:

- Test 2, generated-output correction: fail to pass.
- Test 8, implementing a prepared specification: fail to pass.
- Test 21: fail to pass, but the test is obsolete and is not improvement
  evidence for the current target.

Regression under rewritten guidance:

- Test 18, shared plugin authoring: pass to fail.
- Test 20: pass to fail because it requires the retired four-page route; the
  test is obsolete.

Failures retained in both:

- Test 1, README-only mutation; obsolete because the current rule permits one
  justified shared-doc correction.
- Test 6, substantial specification approval.
- Test 13, planning vocabulary copied into user documentation.
- Test 15, every early user-doc mutation prohibited; obsolete because the
  current rule permits a clearly marked branch-only draft.
- Test 17, full package profile required; obsolete.

## Obsolete legacy tests

| Test | Reason | Replacement |
|---|---|---|
| 1 | Treats README-only mutation as mandatory | Test 28 |
| 15 | Prohibits every pre-implementation user-doc draft | Test 29 |
| 17 | Requires the rejected full package profile | Tests 26 and 28 |
| 20 | Hard-codes the retired four-page route | Test 27 |
| 21 | Combines useful layout behavior with a required full file set and literal terminology assertion | Test 26 |

All five remain executable only for the direct old/new comparison.

## New and replacement scenarios

| Scenario | Previous guidance | Rewritten guidance | Interpretation |
|---|---|---|---|
| Test 22 low/high/max: requirement restraint | Pass / Pass / Pass | Pass / Pass / Pass | Robust across reasoning effort; not rewrite evidence |
| Test 23: avoid overspecified local tests | Fail | Pass | Rewrite improvement |
| Test 24: cover an important real crossing | Fail | Pass | Rewrite improvement after accepting “no mocks” wording |
| Test 25: focused verification report | Pass | Pass | Robust; previous response already said work was left for follow-up |
| Test 26: explicit optional layout | Pass | Pass | Robust; not rewrite evidence |
| Test 27: current two-page routing | Fail | Fail, then pass on a fresh repeat | Expected old failure; mixed candidate behavior |
| Test 28: proportionate small-package docs | Pass | Pass | Robust replacement for Test 1 |
| Test 29: explicit early user-doc draft | Pass | Pass | Robust replacement for Test 15 |

## Remaining rewritten-guidance findings

### Test 6: substantial specification approval

The agent created a substantial new specification immediately rather than
presenting scope, placement, expected files, and overlap for approval. The
rewrite omitted the previous concise approval rule. This is a guidance gap.

### Test 13: planning language in user documentation

The README copied the task's Phase 1/Phase 2 organization instead of describing
the implemented capabilities directly. Because the rewritten guidance does not
list `phase` as a forbidden word, this remains useful held-out-vocabulary
evidence. The abstract reader-language rule is not sufficient for this model.

### Test 18: shared plugin authoring

The previous guidance completed this scenario in 10 tool calls. Both rewritten
guidance samples consumed the 30-call budget. One ended with an unfinished
response and the other with no final response. Generated documentation also
retained unsupported claims and incomplete links.

This is a persistent candidate/model interaction across two samples. It may
reflect scenario complexity, tool-use behavior, or guidance interpretation.
The evidence does not isolate one wording change, so no public rule should be
expanded solely from this result.

### Test 27: routed current guidance

The full candidate matrix read the project-independent guide but not the
Crystal Lattice addendum before mutation. A fresh repeat read both and passed.
Treat this as mixed routing compliance. A concise “read both files in full”
clarification may be tested later, but one pass and one failure do not justify
larger recurring instructions.

## Assertion calibration

Three initial failures were false negatives:

- Test 16 now recognizes an explicit statement that generated output still
  contains the defect when the response also gives the remaining generation
  action.
- Test 24 recognizes “no mocks” and root-relative developer-documentation
  paths.
- Test 25 recognizes “left for follow-up” as visible remaining work.

The preserved model outputs were re-evaluated from cache. No prompt, fixture,
guidance, or model response changed.

## Deterministic verification

- Agent-evaluation package: 64 tests passed.
- Documentation-suite support: 27 focused tests passed.
- Revised collection: 26 selected branches and 5 obsolete deselections.
- Ruff and Python compilation passed.
- Two previously documented mypy assignment errors in test doubles remain.

JUnit and full run data remain under:

```text
tmp/agent-evaluation/documentation-standard/matrix-logs/
tmp/agent-evaluation/documentation-standard/glm/runs/
```