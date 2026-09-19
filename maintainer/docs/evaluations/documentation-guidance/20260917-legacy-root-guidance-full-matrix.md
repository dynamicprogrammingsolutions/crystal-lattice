# Legacy root-guidance full matrix

Date: September 17, 2026

## Status and interpretation

This is the complete historical comparison produced before guidance sources
and project-specific compilation were separated.

The matrix injected the full Crystal Lattice root `AGENTS.md` into Eleventy,
FastAPI, and Flask/Vue fixture repositories. It is retained as legacy
comparison evidence. It must not be treated as the corrected portable-guidance
baseline because most of the injected project information did not belong to
those repositories.

The required replacement is complete in the
[corrected default-runner results](20260918-default-runner-results.md).

## Matrix

The matrix contains:

- three project/task scenarios;
- `glm-5.3-flash:cloud` at low, high, and max effort;
- `gpt-5.6-luna` through ChatGPT login at medium, high, xhigh, and max effort;
- root-only and root-plus-TASKS delivery modes;
- the integrated baseline and combined-v2 candidate.

This gives 84 fresh producer records and 84 valid semantic assessments.
Every expected semantic assessment was produced; no semantic parser or judge
error remains.

This is a full factorial comparison across the selected scenarios, models,
efforts, modes, and variants. It remains descriptive evidence rather than a
statistical estimate over a population of software tasks.

## Frozen records

Files:

- `maintainer/agent-evaluation/suites/documentation_standard/fixtures/root_guidance_full_matrix_results.json`
- `maintainer/agent-evaluation/suites/documentation_standard/fixtures/root_guidance_full_matrix_analysis.json`

SHA-256:

- full records:
  `9a616caff38bd558f368ce491493e6a00deb799f36f7b9e88604831200bc6516`
- effort-aware analysis:
  `6b7c2a1ad000f5db281f44d913f35c5c27b8ee0738f7745372073cc4879f7d92`

Rendered tested files:

- baseline:
  `a56c068e7ea8357f7ef7f045e5a36c15194dc8d271517434ef74dc2bb8b1c54f`
- combined-v2:
  `cf943bb5833f0d94220cd0bef39240a20151ffa9b642e7759a5d403becedf2b7`

The pairwise readability/usability judge was prepared but was not run against
this setup. That comparison belongs to the corrected project-specific
compilation because irrelevant Crystal Lattice instructions could affect both
the plans and the judge's explanation of their quality.

## Aggregate semantic result

Scores are separate axes from zero to 100. They are descriptive and do not
replace the underlying semantic classifications.

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirement sets | 40/42 | 35/42 |
| Partial requirement sets | 2/42 | 6/42 |
| Missing requirement sets | 0/42 | 1/42 |
| Average requirement-coverage score | 98.1 | 91.9 |
| Average scope-restraint score | 50.8 | 72.3 |
| Average testing score | 73.8 | 81.0 |
| No-expansion results | 4 | 12 |
| High-expansion results | 4 | 1 |
| Complete testing plans | 11 | 17 |
| Important crossing present | 31 | 37 |
| Requirement effort target met | 21 | 29 |
| Testing effort target met | 16 | 25 |
| Combined effort target met | 9 | 18 |

Combined-v2 has a strong aggregate benefit in scope restraint and testing, but
that aggregate conceals a requirement-completeness regression.

## Effort-level interpretation

### Low effort

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirements | 6/6 | 5/6 |
| Partial requirements | 0/6 | 1/6 |
| Scope score | 43.7 | 62.8 |
| Testing score | 74.7 | 82.0 |
| Combined effort target met | 3/6 | 4/6 |

The lower-effort candidate gives up one complete requirement set while
improving scope restraint, testing, and crossing coverage. Under the approved
effort policy, this can be an acceptable tradeoff if higher-effort producers
recover completeness.

### Medium effort

Both variants produce five complete and one partial requirement set. The
candidate improves scope and testing averages, but still has one
high-expansion result. Medium effort therefore improves overall without being
uniformly safe.

### High effort

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirements | 12/12 | 11/12 |
| Partial requirements | 0/12 | 1/12 |
| Scope score | 57.8 | 73.9 |
| Testing score | 72.1 | 80.8 |
| Combined effort target met | 2/12 | 4/12 |

The candidate improves scope and testing substantially but introduces a
high-effort completeness regression. This is a warning condition: high effort
is expected to retain complete requirements while avoiding expansion.

### Xhigh effort

The baseline has six complete requirement sets. Combined-v2 has five complete
and one partial set. Scope and testing improve markedly, and effort-target
success rises from one to four cells, but the completeness regression remains
material because xhigh is selected when quality matters.

### Max effort

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirements | 11/12 | 9/12 |
| Partial requirements | 1/12 | 2/12 |
| Missing requirements | 0/12 | 1/12 |
| Scope score | 45.8 | 75.4 |
| Testing score | 75.0 | 79.3 |
| Combined effort target met | 1/12 | 3/12 |

One missing candidate result comes from the incomplete GLM-max producer, so it
does not establish a semantic guidance regression by itself. The GPT-max
candidate nevertheless has two partial requirement sets where its baseline
has complete requirements. GPT-max scope restraint also drops from 84.0 to
68.3 even though the aggregate max-effort scope score improves because GLM-max
stops its large baseline expansion.

Max effort therefore shows the clearest reason not to accept the candidate
from aggregate scores alone.

## Model patterns

### GLM

- GLM-low improves scope, testing, and crossings, with one completeness loss.
- GLM-high keeps all six requirement sets complete and improves scope, but its
  testing average becomes slightly worse and remains mostly partial.
- GLM-max changes from four high-expansion baseline results to five low and one
  no-expansion candidate result. This is the strongest scope improvement in
  the matrix.
- The candidate GLM-max task-mode Eleventy producer failed to return a task
  file after two long attempts, so its missing semantic result is an execution
  outcome rather than proof that the intended requirements were omitted.

### GPT

- GPT-high, xhigh, and max all have complete baseline requirement sets.
- Combined-v2 changes those to five, five, and four complete sets
  respectively.
- GPT-high and xhigh gain substantial scope restraint and testing quality.
- GPT-max testing improves but requirement coverage and scope restraint both
  worsen.
- No GPT producer has a structural or mutation failure in this matrix.

The candidate appears to help GPT avoid excess scope at high and xhigh effort,
but the wording may make some models too aggressive about excluding necessary
requirements. GPT-max does not show the intended restraint benefit
consistently.

## Producer structure

Seven of 84 producer records fail deterministic producer assertions:

- baseline task mode: four GLM files contain premature implementation notes;
- combined-v2 task mode: two GLM-low files contain premature implementation
  notes;
- combined-v2 GLM-max Eleventy task mode returns no task file after the long
  retry.

Root-only producers are structurally clean. GPT task producers are
structurally clean.

The candidate reduces premature-note failures from four to two but introduces
the incomplete GLM-max cell.

## Legacy conclusions

The complete old-context matrix changes the earlier focused interpretation:

1. Combined-v2 has a broad and repeatable positive effect on scope restraint,
   test-layer choice, complete testing plans, and important crossings.
2. The positive aggregate result is not sufficient for acceptance because
   requirement coverage regresses at GPT high, xhigh, and max effort.
3. Lower-effort incompleteness can be tolerated more readily than the
   high-assurance regressions.
4. The exact wording may overemphasize excluding evidence, implementation, and
   unapproved detail without equally emphasizing preservation of every
   necessary behavioral outcome.
5. The surrounding Crystal Lattice guidance is irrelevant to the fixture
   projects and remains a causal confound.

No v3 wording decision should be based solely on this legacy matrix. The
corrected project-specific compilation must rerun both the current baseline
and combined-v2 candidate, preserve effort-aware scoring, and perform the
pairwise quality comparison over passing as well as failing outputs.