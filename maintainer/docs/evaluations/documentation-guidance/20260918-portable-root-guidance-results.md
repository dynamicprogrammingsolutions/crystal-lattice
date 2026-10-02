# Portable root-guidance comparison results

Date: September 18, 2026

## Status

This matrix is historical direct-injection evidence, not default-runner
calibration. The producer matrix contains all 84 requested model runs, but the
suite-specific injection path did not faithfully reproduce the normal Crystal
Lattice Codex and Claude system-message compilation.

Preserved interpreted evidence:

- 42 root-only producers;
- 42 root-only semantic assessments;
- 21 of 21 root-only pairwise reviews.

Invalid for a default-runner acceptance claim:

- GLM inserted a synthetic leading system message that could replace the
  standard Claude template;
- GPT appended suite guidance after normal Codex compilation and could include
  workspace AGENTS content twice;
- both modes forced `include_tasks=false` and bypassed the normal conditional
  `TASKS` template variable;
- all 42 task-mode producer records initially omitted captured task-file
  content even though raw workspace evidence retained the files;
- task-mode semantic evaluation rejected those records before model calls;
- task-mode pairwise review therefore did not run;

Do not use the root-only or task-mode aggregates below to accept or reject the
candidate under the normal Crystal Lattice runner.

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

The fixture already contained compiled `AGENTS.md`, and the projected config
retained the normal model-family mixins. The suite nevertheless applied a
second delivery path:

- GLM received a synthetic leading system message containing suite guidance;
- GPT retained compiled Codex instructions and received the same suite
  guidance appended through endpoint `instructions`;
- canonical TASKS was supplied by the suite wrapper rather than the normal
  `include_tasks` condition.

The corrected setup must remove the suite injector, retain the standard
Codex/Claude message, let the production system-message helpers read workspace
`AGENTS.md`, and toggle canonical `${CONFIG_DIR}/TASKS_v7.md` through
`include_tasks`.

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

Do not promote or reject combined-v2 from this matrix.

The observed outputs suggest useful hypotheses, especially reduced expansion,
but both modes used the wrong runner setup. The Flask/Vue completeness
regressions remain sentinels for the corrected run rather than accepted
candidate findings.

Next:

1. use the reduced default-config projection without the suite guidance
   feature;
2. preserve the standard GPT/Codex and GLM/Claude messages;
3. copy compiled AGENTS into the workspace and use normal helper loading;
4. use `include_tasks=false` for root-only and `true` for task mode;
5. complete four no-model compiled-message preflights;
6. rerun all 84 producers, 12 semantic batches, and 42 pairwise reviews.
