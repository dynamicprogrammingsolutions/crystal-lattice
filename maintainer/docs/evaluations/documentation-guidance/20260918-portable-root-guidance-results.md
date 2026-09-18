# Portable root-guidance comparison results

Date: September 18, 2026

## Status

The producer matrix contains all 84 requested model runs, but the intended
root-plus-task integration comparison is not complete.

Valid interpreted evidence:

- 42 root-only producers;
- 42 root-only semantic assessments;
- 21 of 21 root-only pairwise reviews.

Incomplete or invalid for the intended claim:

- all 42 task-mode producer records initially omitted captured task-file
  content even though raw workspace evidence retained the files;
- task-mode semantic evaluation rejected those records before model calls;
- task-mode pairwise review therefore did not run;
- the task mode delivered root `AGENTS.md` and `TASKS-v7` together through one
  suite-owned instruction message rather than preserving repository-file
  guidance versus task-enabled developer-message delivery;

Do not report this as a complete root-plus-TASKS comparison.

## Provenance

Guidance source revision:

```text
2a8f477b Share documentation guidance
```

Projects:

- Eleventy archive pagination;
- FastAPI notes pagination;
- Flask/Vue book filtering.

Producer profiles:

- `glm-5.3-flash:cloud`: low, high, and max effort;
- `gpt-5.6-luna` through ChatGPT login: medium, high, xhigh, and max effort.

Compared bundles:

- baseline: `maintainer/guidance/current`;
- candidate: `maintainer/guidance/candidates/root-requirements-testing-v2`.

The frozen records retain exact bundle/target compilation hashes, source run
IDs, producer model and effort, prompts, outputs, and recovered instruction
delivery evidence.

Machine-readable evidence:

- [`compiled_guidance_20260918_results.json`](../../../agent-evaluation/suites/documentation_standard/fixtures/results/compiled_guidance_20260918_results.json)
- [`compiled_guidance_20260918_analysis.json`](../../../agent-evaluation/suites/documentation_standard/fixtures/results/compiled_guidance_20260918_analysis.json)

## Instruction delivery

The root-only mode directly injected compiled `AGENTS.md` content through the
suite instruction mechanism. This tests wording under direct instruction
delivery; it does not test discovery of an ordinary repository file.

The task mode concatenated compiled `AGENTS.md` and canonical `TASKS-v7` into
the same injected guidance message. Recorded delivery used a leading `system`
message for GLM and endpoint `instructions` for ChatGPT. It did not reproduce
the intended distinction between repository-file guidance and task-enabled
developer-message guidance.

See
[Instruction delivery and authority](../../instruction-delivery-and-authority.md).

## Root-only semantic results

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirement sets | **21/21** | 19/21 |
| Partial requirement sets | 0/21 | 2/21 |
| Average requirement coverage | **100.0** | 96.2 |
| Average scope restraint | 25.7 | **65.6** |
| No expansion | 0 | **5** |
| Low expansion | 5 | **10** |
| Medium expansion | 8 | 6 |
| High expansion | 8 | **0** |
| Average testing score | 73.4 | **76.0** |
| Complete testing plans | 5 | **7** |
| Important crossing present | 14 | **17** |
| Effort expectation met | 2 | **7** |

Combined-v2 strongly reduces expansion and modestly improves testing. The
tradeoff is two partial requirement sets:

- one GLM-high result;
- one GPT-xhigh result.

Max effort is materially better than in the legacy Crystal Lattice-context
matrix: combined-v2 has 6/6 complete max-effort requirement sets, two
no-expansion and four low-expansion results, and an average scope score of
85.0.

The xhigh completeness loss remains a warning because xhigh is selected when
quality matters. High effort also has one partial candidate result.

## Results by project

### Eleventy

- Baseline: 7/7 complete, scope score 17.3, testing score 85.7.
- Combined-v2: 7/7 complete, scope score 48.6, testing score 90.4.
- All important crossings remain present.

### FastAPI

- Baseline: 7/7 complete but five high-expansion results and scope score 4.3.
- Combined-v2: 7/7 complete, no high expansion, scope score 85.7.
- All important HTTP crossings remain present.

This is the clearest candidate improvement.

### Flask/Vue

- Baseline: 7/7 complete, but every plan misses the client/server crossing.
- Combined-v2: 5/7 complete and 2/7 partial; three plans include the crossing.

The candidate improves scope and some crossing coverage but introduces the two
requirement-completeness regressions. This scenario is the main acceptance
risk.

## Root-only pairwise review

Twenty-one valid pairwise reviews produced, including successful retries of
the two initial invalid JSON responses:

| Preference | Baseline | Combined-v2 | Tie |
|---|---:|---:|---:|
| Overall | 4 | **17** | 0 |
| Requirements | 3 | **18** | 0 |
| Testing | 6 | **13** | 2 |
| Plan usability | 6 | **10** | 5 |

Average overall-quality score:

- baseline: 3.33 / 5;
- combined-v2: 4.10 / 5.

Combined-v2 was preferred in all six max-effort comparisons. The initial
Flask/Vue GLM-high and GPT-high evaluator responses failed JSON parsing; clean
retry records replace those failures in the aggregate above.

## Task-mode capture defect

All 42 task-mode agents created task files. `changed_paths` and raw retained
workspace data prove those mutations. The producer recorder attempted to read
the cleaned live workspace after the harness closed and therefore wrote an
empty `generated_files` mapping.

The suite now recovers retained untracked files from:

```text
raw/workspace/untracked/
```

This repair makes the existing producer outputs inspectable, but it does not
repair the instruction-layer mismatch. Semantic and pairwise task-mode reruns
should wait until delivery is modeled correctly.

## Recommendation

Do not promote combined-v2 yet.

The root-only evidence is substantially more favorable than the legacy matrix,
especially at max effort and for FastAPI. However:

1. task-mode interaction with accepted task guidance is still unverified;
2. the current task-mode delivery collapses distinct instruction layers;
3. Flask/Vue retains two high-assurance completeness regressions;
4. pairwise preference cannot compensate for missing task-mode integration.

Next:

1. define and implement a task-mode delivery profile that preserves the
   intended source and authority distinction;
2. assert delivery role, position, source, availability, and read evidence
   deterministically;
3. rerun only the 42 task-mode producers under that profile;
4. run six task-mode semantic batches and 21 task-mode pairwise reviews;
5. combine the valid root-only and corrected task-mode evidence before an
   acceptance decision.
