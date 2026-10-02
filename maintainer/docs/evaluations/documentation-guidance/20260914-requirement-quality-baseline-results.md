# Requirement-quality diverse-project baseline

Status: Human accepted; evaluator and task-file comparison planned

Run date: September 14, 2026

## Review outcome

The user accepted the semantic interpretation on September 14, 2026. No
guidance change or candidate matrix has started. The approved next scope is to
plan a structured semantic evaluator and one current-guidance task-file matrix
that reuses these scenarios and also assesses testing-plan quality from the
same producer outputs.

The accepted calibration directions are:

1. Calibration should focus on preventing unsupported design,
   implementation, verification, and documentation obligations while allowing
   useful specification detail.
2. Splitting one accepted outcome is appropriate when the resulting
   requirements are independently meaningful; splitting every edge case,
   operation, or protected surface should be discouraged.
3. Tests 30–32 are redundant as primary scenarios and remain optional controls
   only when a later hypothesis needs them.

## Experiment

Three small public-project fixtures were evaluated:

| Project | Task | Target outcomes |
|---|---|---:|
| Eleventy Base Blog | Paginate a public static archive while preserving URLs, accessibility, ordering, related generated surfaces, and zero-JavaScript output | 7 |
| FastAPI CRUD Async | Add optional pagination to a public REST collection while preserving the existing body and unparameterized behavior | 8 |
| Flask-Vue CRUD | Add an All/Read/Unread filter across the Vue client and Flask API while preserving CRUD behavior | 8 |

Seven producer profiles ran each task:

- `glm-5.3-flash:cloud`: low, high, max;
- `gpt-5.6-luna` through ChatGPT login: medium, high, xhigh, max.

The 21 runs used fresh workspaces, one identical requirement-minimal guidance
variant, no `TASKS-v7`, no target or assessment rubric, and no model-generated
seed.

## Run integrity

All 21 model requests completed and produced specification and requirements
content under `docs/development/`. No run changed source code, tests, or
current user documentation. Model and effort provenance were recorded for
every run, and GPT used the configured ChatGPT account.

The original pytest processes reported 3 GLM and 12 GPT failures because the
running processes had loaded an initial output-presence matcher that accepted
only a literal `requirements.md` filename or exact `Requirements` heading.
Every rejected output used a clear equivalent such as
`archive-pagination-requirements.md`, `Functional requirements`, or `Outcomes`.
The corrected matcher accepts all 21 preserved records. No replacement model
call was made.

One GLM max full-stack run issued malformed shell-tool calls, recovered,
completed its documentation, and reported no provider error. The tool misuse
is retained as model behavior but does not invalidate its requirements.

## Main findings

### 1. Completeness was not the problem

All 21 outputs cover the central target behavior. The GLM-low full-stack result
only implies rather than clearly states that the active filter is visibly
identified; otherwise no required outcome is materially missing.

The prompts provide substantial product detail, so this baseline primarily
measures how models organize and expand known scope rather than whether they
discover omitted product requirements.

### 2. GPT expands more than GLM

Across the three projects:

| Model | Formal requirement items | Average generated documentation |
|---|---:|---:|
| GLM, 9 runs | 84 total; 9.3 per run | 723 words per run |
| GPT, 12 runs | 149 formal items; 12.4 per run | 1,342 words per run |

GPT xhigh also added required verification/documentation sections outside its
formal tables on FastAPI and Flask/Vue. Counting those explicit obligations
would increase the GPT total further.

Requirement count is descriptive rather than a verdict: several extra rows
are harmless decomposition of accepted behavior. The consistent difference in
review burden remains substantial.

### 3. GLM expansion increases with effort

Formal GLM requirement counts:

| Project | Low | High | Max |
|---|---:|---:|---:|
| Eleventy | 9 | 11 | 13 |
| FastAPI | 7 | 7 | 11 |
| Flask/Vue | 7 | 9 | 10 |

Higher GLM effort adds implementation design, edge cases, exact markup, or
unspecified API behavior. Low effort stays closest to the semantic targets.

### 4. GPT effort is not monotonic

Formal GPT requirement counts:

| Project | Medium | High | Xhigh | Max |
|---|---:|---:|---:|---:|
| Eleventy | 17 | 13 | 18 | 14 |
| FastAPI | 10 | 10 | 10 plus 6 required sections | 10 |
| Flask/Vue | 13 | 14 | 12 plus 5 required bullets | 8 plus 3 process requirements |

Xhigh is the most expansive on Eleventy and Flask/Vue. Max sometimes becomes
more compact, but it can add stronger implementation constraints, as in the
FastAPI data-query requirement.

### 5. Project type changes the expansion pattern

- **Public website:** models turn edge cases, accessibility techniques,
  exact navigation markup, and every protected generated surface into separate
  requirements.
- **Public REST API:** models resolve unspecified parameter defaults, empty
  pages, error-body details, and database implementation differently.
- **Full stack:** models split one user outcome by UI choice, API branch, CRUD
  operation, layer, test type, and documentation state.

This diversity is diagnostically useful and should replace the three
same-family API/package scenarios in the primary matrix.

## Eleventy archive pagination

Target: seven outcomes. Every run is complete.

The exact later-page URL chosen by a model is not treated as expansion because
the target requires a stable address and permits the specification to select
the pattern. Separate rows for home, tags, feed, sitemap, and post navigation
increase review burden but generally restate one accepted compatibility
outcome.

| Producer | Formal items | Expansion | Interpretation | Detail |
|---|---:|---|---|---|
| GLM low | 9 | Low–medium | Adds `rel=prev/next` and exact accessibility mechanics; otherwise concise and complete. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T181737.068040Z-requirement-baseline-33-eleventy-archive-pagination-low-4754d518/records/requirement-baseline.json) |
| GLM high | 11 | Medium | Splits every unaffected surface and adds detailed Eleventy design, but little new product scope. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T181903.584396Z-requirement-baseline-33-eleventy-archive-pagination-high-2a260faf/records/requirement-baseline.json) |
| GLM max | 13 | Medium | Adds exact landmark/rel markup, page-one alias behavior, route-collision rules, and build implementation detail. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T182021.577338Z-requirement-baseline-33-eleventy-archive-pagination-max-0a310067/records/requirement-baseline.json) |
| GPT medium | 17 | High | Adds zero-post and page-count contracts, current-page semantics, exact accessibility structure, and separate requirements for every protected surface. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T181737.911489Z-requirement-baseline-33-eleventy-archive-pagination-medium-1046571c/records/requirement-baseline.json) |
| GPT high | 13 | Medium–high | Complete but highly fragmented; turns the documentation-only mutation boundary into a formal requirement. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T182102.472142Z-requirement-baseline-33-eleventy-archive-pagination-high-809a4b2f/records/requirement-baseline.json) |
| GPT xhigh | 18 | High | Adds exact empty-archive/page-count, tie-order, chunk-order, navigation, feed, post-URL, and task-scope requirements. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T182333.208519Z-requirement-baseline-33-eleventy-archive-pagination-xhigh-7662c5fd/records/requirement-baseline.json) |
| GPT max | 14 | High | Requires an exact navigation label, page indicator, relation attributes, zero-post behavior, and detailed per-surface compatibility. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T182728.321635Z-requirement-baseline-33-eleventy-archive-pagination-max-cea2d5f6/records/requirement-baseline.json) |

## FastAPI notes pagination

Target: eight outcomes. Every run is complete.

The target intentionally leaves behavior unspecified when only one of
`limit`/`offset` is supplied. This reveals whether a model records a design
question or silently selects a contract.

| Producer | Formal items | Expansion | Interpretation | Detail |
|---|---:|---|---|---|
| GLM low | 7 | Low | Groups validation and compatibility cleanly; stays closest to the target. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T182419.813679Z-requirement-baseline-34-fastapi-notes-pagination-low-7b17d0af/records/requirement-baseline.json) |
| GLM high | 7 | Low–medium | Requirements remain focused; specification chooses unbounded remainder when `limit` is omitted and adds implementation notes. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T182443.153800Z-requirement-baseline-34-fastapi-notes-pagination-high-800bb22a/records/requirement-baseline.json) |
| GLM max | 11 | Medium | Invents `limit=100`/`offset=0` defaults, empty-page behavior, unpaginated header absence, and detailed data-query design. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T182521.907836Z-requirement-baseline-34-fastapi-notes-pagination-max-9e85747e/records/requirement-baseline.json) |
| GPT medium | 10 | Medium | Invents 100/0 defaults, standard error-body details, and total-count behavior for empty pages. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T183256.830622Z-requirement-baseline-34-fastapi-notes-pagination-medium-13429ad4/records/requirement-baseline.json) |
| GPT high | 10 | Medium | Makes the same 100/0 default choice and adds out-of-range page behavior and expanded endpoint compatibility. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T183448.299834Z-requirement-baseline-34-fastapi-notes-pagination-high-b7739adb/records/requirement-baseline.json) |
| GPT xhigh | 10 plus 6 | Medium–high | Chooses an unbounded omitted limit, then promotes five verification bullets and one documentation rule into required sections. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T183651.371855Z-requirement-baseline-34-fastapi-notes-pagination-xhigh-a732b552/records/requirement-baseline.json) |
| GPT max | 10 | High | Requires database-side ordering/slicing and a separate count query, turning one implementation strategy into product completion. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T183900.707445Z-requirement-baseline-34-fastapi-notes-pagination-max-310d851f/records/requirement-baseline.json) |

## Flask/Vue book filtering

Target: eight outcomes. Every run is complete. GLM low leaves visible active
filter indication implicit; all other outputs state it directly.

| Producer | Formal items | Expansion | Interpretation | Detail |
|---|---:|---|---|---|
| GLM low | 7 | Low | Groups the full-stack behavior well; active-selection visibility is only implicit. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T182653.762106Z-requirement-baseline-35-flask-vue-book-filter-low-c87b7288/records/requirement-baseline.json) |
| GLM high | 9 | Low–medium | Splits each UI choice and adds detailed mutation-membership examples; no material new feature. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T182718.271643Z-requirement-baseline-35-flask-vue-book-filter-high-4e4a60ba/records/requirement-baseline.json) |
| GLM max | 10 | Medium | Requires unknown `read` values to return all books, preserves ordering, and treats manual checks as the only verification path. | [record](../../../../tmp/agent-evaluation/documentation-standard/glm/runs/20260914T182753.131010Z-requirement-baseline-35-flask-vue-book-filter-max-d23b4263/records/requirement-baseline.json) |
| GPT medium | 13 | High | Adds an unsupported API-error contract for unknown values and splits add/update/delete refresh into separate requirements. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T184245.009590Z-requirement-baseline-35-flask-vue-book-filter-medium-0bb063d1/records/requirement-baseline.json) |
| GPT high | 14 | Medium–high | Avoids the unknown-value invention but fragments refresh, active state, and membership behavior by operation. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T184417.051808Z-requirement-baseline-35-flask-vue-book-filter-high-b8bbfdc1/records/requirement-baseline.json) |
| GPT xhigh | 12 plus 5 | High | Adds string-truthiness implementation behavior, exact existing-field rendering, storage-mutation constraints, verification bullets, and documentation scope. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T184607.832820Z-requirement-baseline-35-flask-vue-book-filter-xhigh-b4871168/records/requirement-baseline.json) |
| GPT max | 8 plus 3 | Medium | Keeps the eight product outcomes compact but promotes API tests, component tests, and the documentation mutation boundary into formal requirements. | [record](../../../../tmp/agent-evaluation/documentation-standard/gpt/runs/20260914T184851.862965Z-requirement-baseline-35-flask-vue-book-filter-max-1629223b/records/requirement-baseline.json) |

## Interpretation

The baseline supports a distinction among four behaviors:

1. **Useful specification detail:** selecting a concrete stable archive URL
   pattern or clarifying response examples can be necessary to make a target
   implementable.
2. **Fragmentation:** splitting one compatibility outcome into separate home,
   feed, sitemap, tag, and post rows increases review burden without changing
   scope.
3. **Unsupported behavior:** inventing pagination defaults, invalid-query
   behavior, zero-post guarantees, or exact UI/accessibility contracts changes
   the accepted target.
4. **Wrong record role:** database query strategies, verification plans,
   current-documentation restrictions, and test cases can be useful in a
   specification or plan but should not automatically become product
   requirements.

No producer added a large unrelated feature such as search, authentication,
API versioning, caching, or database replacement. The observed problem is
mostly completeness bias: models convert every discovered edge, implementation
idea, validation example, and protected detail into a completion obligation.

## Control recommendation

Retain original Test 22 as historical evidence that already-classified scope
can be translated at GLM low/high/max.

Recommend removing Tests 30–32 from the eventual routine suite unless a later
calibration hypothesis specifically needs an API/package control. The diverse
matrix already exposes:

- model-level expansion;
- effort-sensitive expansion;
- project-sensitive fragmentation;
- unsupported public-contract decisions;
- implementation and verification work promoted into requirements.

## Calibration boundary

No calibration is authorized yet. If the interpretation is accepted, a later
plan can decide whether the shortest useful guidance should address:

- minimum sufficient independently verifiable outcomes;
- avoiding separate requirements for every edge case or protected surface;
- keeping unspecified design choices visible rather than silently selecting
  them;
- keeping implementation, test, documentation, and verification work in their
  appropriate records;
- allowing higher-effort analysis to add supporting information without
  enlarging completion.

Any candidate wording would run against the same pinned projects, prompts,
targets, profiles, and efforts only after separate approval.