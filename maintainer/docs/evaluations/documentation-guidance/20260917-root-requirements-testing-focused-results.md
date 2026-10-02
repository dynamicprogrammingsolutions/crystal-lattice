# Focused root Requirements and Testing results

Date: September 17, 2026

## Decision summary

Do not apply combined-v2 to root `AGENTS.md` and do not run the full 21-cell
matrix with this candidate.

Combined-v2 improves requirement restraint and FastAPI test-layer selection,
but it introduces one high-expansion requirement regression, loses required
Flask crossings, reduces one requirement set to partial coverage, and worsens
task-file structural cleanliness for GLM. The appropriate next decision is a
smaller v3 ablation described under [Recommendation](#recommendation).

The real root `AGENTS.md` remains at the integrated baseline recorded in
[the September 17 baseline](20260917-integrated-root-guidance-baseline.md).

## Scope and provenance

The focused comparison used three small projects:

- Eleventy Base Blog: public static-site archive pagination;
- FastAPI CRUD Async: public REST API pagination and response performance;
- Flask-Vue CRUD: a user-facing full-stack filter crossing client and server.

The producer profiles were selected from the established seven-profile matrix:

- `glm-5.3-flash:cloud` at low, high, or max effort;
- `gpt-5.6-luna` through ChatGPT login at medium, high, xhigh, or max effort.

Two delivery modes were evaluated:

- `root-only`: root `AGENTS.md` was injected; the model returned requirements
  and a plan without creating files;
- `task`: root `AGENTS.md` plus canonical `TASKS-v7` were injected; the model
  created one Draft task file.

The detailed documentation guide and Crystal Lattice addendum were copied into
every fixture but were not injected. Canonical TASKS guidance was byte-fixed.

Candidate source commits:

- integrated baseline: `4a0c078c`;
- root-guidance calibration: `e37aba3d`;
- v2 candidate refinement: `fa4e3b1b`.

Injected root-only context size:

| Variant | Words | Guidance SHA-256 |
|---|---:|---|
| Integrated baseline | 3,111 | `d71a35a2bc3bd9d72759bfd5086c8ffb7762ad76608604cbfa9d1b279a88cfe7` |
| Combined-v2 | 2,951 | `d786f8cf1a6c6217f64d60497c264df69836a1597a9d341a1ee595517e822f0d` |

Combined-v2 is shorter because it replaces the existing long Testing section
while adding a dedicated Requirements section.

## Frozen evidence

The durable fixture is:

`maintainer/agent-evaluation/suites/documentation_standard/fixtures/root_guidance_focused_results.json`

SHA-256:

`7a6383835e9303b3721b5f6d6ae3bf1bae1f24cfaa73d201dfd54cbd5ac8cd3c`

It contains:

- 66 selected producer records;
- 60 valid semantic assessments;
- 1 failed producer attempt;
- 3 invalid semantic-evaluator attempts;
- 6 missing assessments belonging only to rejected intermediate candidates.

All decision-critical integrated-baseline and combined-v2 cells have valid
semantic assessments. Invalid evaluator attempts and the one failed producer
attempt are preserved separately and are not counted as guidance failures.

The failed producer attempt was the first root-only Eleventy GPT-max baseline
run, which reached its 30-tool stop condition without a final response. A
45-tool retry completed and is the selected producer record.

## Intermediate candidate findings

### Requirements-only

Requirements v1 did not reliably restrain scope. It still promoted testing and
verification into requirements, selected unapproved public behavior, and
sometimes mandated internal mechanisms.

Requirements v2 fixed the sampled FastAPI public-decision and internal-mechanism
failures, but models continued adding a final “tests cover...” completion
requirement. Direct inspection showed why: the unchanged root Testing section
still said that every new public behavior receives tests, and GLM explicitly
cited that sentence as requirement authority.

### Testing-only

Testing v1 and v2 improved some boundary descriptions and removed incidental
cache files in the v2 sample, but neither could govern requirement scope.
Tests still became requirements, public behavior was still selected without
approval, and several Flask plans still replaced the real client-to-Flask
crossing with separate component checks.

### Combined v1

Combining the sections reduced the conflict between Requirements and the old
Testing section. It fully passed the Eleventy GPT-max sentinel and improved
FastAPI GPT-high and Flask GLM-high, but retained database/public-choice
expansion, missing crossings, and one incidental-cache mutation.

These findings justified combined-v2 but did not justify a full matrix.

## Root-only comparison

The root-only focused comparison contains the same 11 baseline and combined-v2
cells.

### Aggregate result

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirement coverage | 11 | 10 |
| Partial requirement coverage | 0 | 1 |
| No expansion | 0 | 1 |
| Low expansion | 6 | 8 |
| Medium expansion | 5 | 1 |
| High expansion | 0 | 1 |
| Material added obligations | 5 | 2 |
| Complete testing plan | 1 | 1 |
| Partial testing plan | 10 | 10 |
| Appropriate test layer | 2 | 6 |
| Mixed test layer | 9 | 5 |
| Important crossing present | 8 | 6 |
| Important crossing missing | 3 | 5 |
| Focused verification | 6 | 7 |
| Structurally clean producers | 11 | 11 |

Combined-v2 clearly improves average requirement restraint and test-layer
selection. It does not improve decisive testing coverage and regresses crossing
coverage.

### Important cell changes

- Eleventy GPT-max improves from medium to low requirement expansion. Testing
  remains partial, appropriate, and focused.
- FastAPI GLM-low/high keep complete, low-expansion requirements and improve
  from mixed to appropriate test layers.
- FastAPI GPT-high improves from medium to low expansion and from
  partial/mixed to complete/appropriate testing.
- FastAPI GPT-xhigh regresses from low to high expansion by making
  database-side pagination a product requirement.
- FastAPI GLM-max regresses from complete to partial testing.
- Flask GLM-low regresses from complete to partial requirement coverage and
  loses the previously present crossing.
- Flask GLM-max also loses its previously present crossing.
- Flask GPT-medium improves from medium to low expansion, and GPT-xhigh
  improves from low to no expansion, but both still miss the client-to-Flask
  crossing.

## Root plus TASKS comparison

The task-mode comparison contains the same seven baseline and combined-v2
cells.

### Aggregate result

| Measure | Baseline | Combined-v2 |
|---|---:|---:|
| Complete requirement coverage | 7 | 7 |
| No expansion | 0 | 1 |
| Low expansion | 6 | 5 |
| Medium expansion | 1 | 1 |
| Material added obligations | 1 | 0 |
| Complete testing plan | 2 | 2 |
| Partial testing plan | 5 | 5 |
| Appropriate test layer | 5 | 4 |
| Mixed test layer | 2 | 3 |
| Important crossing present | 5 | 5 |
| Important crossing missing | 2 | 2 |
| Focused verification | 7 | 5 |
| Mixed verification | 0 | 2 |
| Structurally clean task files | 6 | 5 |

Combined-v2 provides no aggregate testing or crossing improvement when TASKS
guidance is already active. It removes the one material added obligation but
worsens layer selection, verification focus, and task-file structure.

### Important cell changes

- FastAPI GLM-low improves from low to no expansion and fixes its premature
  notes.
- FastAPI GLM-high regresses from low to medium expansion and introduces
  premature notes.
- FastAPI GPT-high improves from medium to low expansion and from partial to
  complete testing.
- FastAPI GPT-xhigh retains complete testing but continues to mention a
  database-query strategy.
- Flask GLM-high is semantically unchanged but introduces premature notes.
- Flask GPT-medium remains partial/mixed and still misses the crossing.
- Flask GPT-xhigh regresses from complete/appropriate to partial/mixed
  testing, although the crossing remains present.

The task-file structural failures therefore move between effort levels instead
of disappearing.

## Evaluator reliability

The structured judge used `glm-5.3-flash:cloud` at max effort with evaluator
prompt v4.

Three invalid attempts were retained:

- one omitted required testing-evidence indexes;
- one used a signal name as an added-obligation classification;
- one returned no JSON response.

Focused retries produced valid decision-critical baseline and combined-v2
assessments. Some valid judge runs also attempted a malformed shell call before
returning their JSON; the tool failure did not alter candidate content or the
validated assessment.

The six missing semantic assessments belong only to rejected combined-v1 or
Requirements-v2 cells. They do not affect the baseline/combined-v2 decision.

## Recommendation

Reject combined-v2 as final root guidance and keep the integrated root
`AGENTS.md` unchanged for now.

Approve a smaller v3 ablation with these boundaries:

1. Keep a compressed Requirements rule expressing only:
   - minimum approved completed-state outcomes;
   - evidence and work are not product requirements;
   - unapproved public behavior and internal mechanisms remain non-normative.
2. Remove the conflicting “When to add tests — any new public behavior”
   framing from the old Testing section.
3. Replace only the first strategic testing paragraph with:
   - smallest reliable evidence;
   - a mock that bypasses behavior is not decisive;
   - a cross-component requirement needs one real crossing or an explicit gap;
   - existing coverage counts only when it proves the behavior.
4. Retain the existing repository realism and package-specific testing rules
   for this next ablation. Do not move them until behavior is accepted.
5. Do not add boundary-value, regression-list, cache-cleanup, or placement
   detail to the always-loaded section in this iteration; TASKS and package
   guidance already carry the applicable mechanics.
6. Rerun only the demonstrated sentinels:
   - FastAPI GPT-xhigh root-only internal-mechanism expansion;
   - Flask root-only crossing and GLM-low coverage;
   - FastAPI/Flask GLM task-file premature notes;
   - Flask GPT-medium/xhigh task-mode crossing/layer behavior.

Run the full 21-cell matrix only if this smaller candidate:

- keeps all focused requirement sets complete;
- introduces no high expansion;
- does not reduce crossing coverage;
- has task-file structural cleanliness at least equal to the baseline;
- does not reduce complete testing plans or appropriate-layer counts.

This recommendation preserves the demonstrated value of prominent root
Requirements guidance without accepting the testing and task-mode regressions
introduced by the larger rewrite.