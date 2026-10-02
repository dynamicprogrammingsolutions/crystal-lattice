# Requirement, task-guidance, and testing-plan comparison

Status: Awaiting human review before guidance rewriting

Producer execution: September 15, 2026

The internal Dataset B identifier retains `20260914`, the date the matrix was
approved and frozen. Its producer calls ran on September 15.

## What to review

1. Does the comparison correctly show that current task guidance reduces
   requirement expansion while retaining complete target coverage?
2. Should unresolved public behavior receive stronger task-guidance wording,
   especially when a model calls a public API decision “local and reversible”?
3. Does the testing interpretation strike the right balance: avoiding test
   inflation while still requiring the boundary that can prove the behavior?
4. Should planning guidance explicitly require cleanup of generated files and
   forbid even empty implementation/completion notes before execution?

No maintained documentation, task, or testing guidance has changed.

## Compared datasets

| Dataset | Output | Guidance | Runs |
|---|---|---|---:|
| A | Specification and requirements | Requirement-minimal evaluation guidance; no task guidance | 21 |
| B | One task file with a Draft execution plan | Current general documentation guide plus exact `agents/TASKS-v7.md` content | 21 |

Both datasets use the same three pinned projects, product outcomes, fixtures,
seven model/effort profiles, and hidden requirement targets.

Dataset B's prompt asks only for one task file with a Draft execution plan. It
does not ask for a testing strategy or test plan. Requirement verification and
additional implementation verification are produced from the standing task
guidance.

The comparison changes output type and guidance context together, so it does
not claim that one difference was caused solely by the documentation guide,
task guide, or task-file format.

## Evaluator integrity

The semantic evaluator uses `glm-5.3-flash:cloud` at max effort and assesses
all seven outputs for one project in one call.

Evaluator prompt v1 correctly found most concrete additions but underweighted
cumulative expansion and treated independently regressible surfaces as
automatically valid decomposition. V2 added:

- cumulative expansion-severity definitions;
- independent acceptance/tracking as the separation test;
- clarification rather than silent public-contract decisions;
- exact-mechanism and implementation-constraint handling;
- separate interpretation of task requirements and legitimate plan content.

V2 passes all accepted Dataset A anchors for the three projects.

The Dataset B Flask/Vue response omitted one candidate-closing JSON brace. A
narrow parser repair inserted that one structural brace, recorded the repair,
and validated the complete result against the schema. No semantic text was
changed and no judge call was repeated.

## Main result

All 42 candidate outputs cover the approved product outcomes. Current task
guidance substantially reduces semantic requirement expansion:

| Expansion severity | Dataset A | Dataset B |
|---|---:|---:|
| None | 0 | 5 |
| Low | 4 | 11 |
| Medium | 12 | 5 |
| High | 5 | 0 |

Review burden changes similarly:

| Review burden | Dataset A | Dataset B |
|---|---:|---:|
| Low | 4 | 14 |
| Medium | 13 | 7 |
| High | 4 | 0 |

The improvement is much stronger for GPT than GLM:

| Producer family | Dataset A | Dataset B |
|---|---|---|
| GLM, 9 runs | 4 low, 5 medium | 1 none, 4 low, 4 medium |
| GPT, 12 runs | 7 medium, 5 high | 4 none, 7 low, 1 medium |

The existing requirement-restraint wording therefore appears effective,
especially for GPT. It prevents implementation, testing, verification, and
documentation work from becoming requirements in almost every Dataset B task.

The remaining expansion is narrower and more diagnostic:

- compatibility surfaces still fragment in four Eleventy tasks;
- one GPT Eleventy task promotes a documentation deliverable into completion;
- FastAPI missing-parameter semantics remain unresolved or prematurely
  selected in several plans;
- all three GLM Flask/Vue tasks silently choose behavior for unsupported
  `read` values;
- two GPT Flask/Vue tasks split Read and Unread variants but otherwise remain
  proportionate.

## Requirement interpretation by project

### Eleventy

Dataset A ranged from low to high expansion. Dataset B has two `none`, four
`low`, and one `medium` result.

The main residual behavior is fragmentation: GLM and GPT high commonly give
home, tag, feed, sitemap, and post navigation separate requirement rows even
though the target treats them as one compatibility group. This adds review
burden but little new product scope.

GPT xhigh and max produce the cleanest requirement sets. GPT high is the only
material exception: its requirement-verification table makes creating an
archive specification and indexing it a completion obligation.

### FastAPI

Dataset A is dominated by medium expansion and includes a high result that
mandates a database query strategy. Dataset B has one `none`, five `low`, and
one `medium` result. No Dataset B task makes SQL, ORM, or separate-count-query
mechanics a product requirement.

Missing companion-parameter behavior remains the important ambiguity:

- GLM high chooses an unbounded remainder as an operative local decision.
- GLM max assumes `limit=100` for an offset-only request and makes the plan
  depend on it.
- GPT medium/high raise the default as a question or recommendation, which is
  better, though later plan steps partly assume the recommended answer.
- GPT xhigh/max state an unbounded remainder with limited or ambiguous
  approval framing.

The target's future version should explicitly classify this as an unresolved
public-contract decision. The guidance should make clear that public API
semantics are not local reversible implementation choices.

### Flask/Vue

Dataset A ranges from low to high expansion. Dataset B improves every GPT
result to `none` or `low`; GPT xhigh and max cover eight outcomes in six
well-grouped requirements without invented product behavior.

GLM moves in the opposite direction. Low, high, and max all make unsupported
query-value behavior normative:

- unknown or empty values return all books;
- some variants additionally accept case-insensitive values;
- max also specifies behavior for books missing the `read` field.

The tasks describe these decisions as local or reversible and state that no
requirement question remains. That conflicts with the task guide's own
definition of a material decision because the choices change a public API
contract.

This is the clearest evidence for strengthening ambiguity and decision
authority rather than merely adding more requirement-minimality wording.

## Testing-plan result

The prompt did not request tests. The task guidance naturally produced
requirement-verification plans in all 21 task files.

| Testing measure | Result |
|---|---:|
| Complete required evidence | 12 |
| Partial required evidence | 9 |
| Missing all required evidence | 0 |
| Appropriate primary layers | 20 |
| Mixed layers | 1 |
| Important production crossing present | 20 |
| Important crossing missing | 1 |
| Focused verification | 18 |
| Mixed verification focus | 3 |
| Bloated verification focus | 0 |
| Material duplication | 0 |
| Material combinatorial expansion | 0 |

Current guidance does not cause broad test maximization in these scenarios.
The more common problem is incomplete or weak evidence at the boundary that
matters.

Implementation-coupled checks occur in 15 plans, but most are minor:

- exact `rel`, ARIA, or chosen URL details;
- source-path or byte-identical-source checks;
- axios-call inspection where an HTTP crossing matters;
- route tests with a mocked CRUD layer that cannot prove database ordering;
- checks that internal in-memory collections were not mutated.

These should not all be treated as equally severe. The future evaluator should
distinguish minor implementation detail from a material test strategy that
mocks away the claimed behavior.

### Eleventy testing

Six of seven plans cover the decisive build evidence. Every plan includes a
production Eleventy build crossing.

GLM low is partial because its main path lacks a representative large-post
fixture, exactly-once collection coverage, navigation-boundary absence, and
several protected-surface regressions.

The remaining plans are generally strong. Their excess is small:

- zero-post checks not required by the target;
- repeated boundary fixtures;
- exact accessibility or source-file checks;
- occasional duplicate deterministic rebuilds.

### FastAPI testing

All seven plans are partial even though all use an appropriate HTTP-route
boundary and remain focused.

The recurring gap is that a mocked route test cannot prove ascending database
ordering or total-count behavior. Plans recognize that issue inconsistently:

- GLM max proposes a real-database integration test and is strongest at this
  boundary.
- Several other plans test sorted results from an unsorted mocked response,
  which conflicts with a database-side ordering design.
- Valid boundary acceptance such as `limit=1`, `limit=100`, and `offset=0` is
  often omitted.
- Unchanged create/read/update/delete behavior is frequently delegated to an
  existing suite that the compact fixture does not actually contain.

This is under-testing rather than expansion. Future guidance must preserve the
rule to use the cheapest reliable layer while emphasizing that the chosen
layer still has to contain the failure being claimed.

### Flask/Vue testing

Six of seven plans cover the required server, component, and full-stack
evidence. GPT high is partial because it proposes separate Flask test-client
and Vue component checks but does not commit to a real client-to-Flask HTTP
crossing.

The strongest plans are GPT xhigh and max:

- supported server filtering and response shape are tested;
- UI selection, rendered results, empty state, and representative mutation
  refreshes are covered;
- a browser/network crossing is included;
- exhaustive operation-by-filter combinations are avoided.

GLM plans cover the important crossing, but high/max spend extra effort on
invented unknown-value behavior and internal source identity. This demonstrates
how requirement expansion propagates into testing expansion: once an
unsupported behavior is made normative, the plan adds tests to prove it.

## Task-guidance structural behavior

After correcting two exact-heading parser false negatives, 18 of 21 task files
follow the required structure and modify only one task file.

GPT passes all 12 cells. Three GLM failures remain:

1. Eleventy high ran a scratch build during planning and left six generated
   `_site` files in the workspace.
2. FastAPI low omitted the required
   `Implementation decisions and open questions` closing section.
3. FastAPI high added an empty `Implementation Notes` section before execution.

The first failure suggests a planning-mutation rule: investigation may run
safe diagnostics, but generated output must be cleaned up and task creation
must leave only the authorized task-file mutation.

The other two rules are already explicit in current task guidance. Their
failure may need retained behavior tests more than additional repeated prose.

## Per-run comparison

Testing is shown as `coverage / layer / crossing / focus`.

| Project | Producer | Requirement expansion A → B | Dataset B requirement finding | Testing | Structure |
|---|---|---|---|---|---|
| Eleventy | GLM low | low → low | Compatibility fragmentation | partial / appropriate / present / focused | Pass |
| Eleventy | GLM high | medium → low | Compatibility fragmentation | complete / appropriate / present / focused | Fail: generated `_site` files |
| Eleventy | GLM max | medium → low | Compatibility fragmentation; minor page indicator | complete / appropriate / present / focused | Pass |
| Eleventy | GPT medium | high → low | No material requirement addition | complete / appropriate / present / focused | Pass |
| Eleventy | GPT high | medium → medium | Documentation promoted to completion; compatibility fragmentation | complete / appropriate / present / mixed | Pass |
| Eleventy | GPT xhigh | high → none | Clean grouping and scope | complete / appropriate / present / focused | Pass |
| Eleventy | GPT max | high → none | Clean grouping and scope | complete / appropriate / present / focused | Pass |
| FastAPI | GLM low | low → none | Clean requirement contract | partial / appropriate / present / focused | Fail: required closing section absent |
| FastAPI | GLM high | medium → low | Unbounded offset-only choice made operative | partial / appropriate / present / focused | Fail: premature Implementation Notes |
| FastAPI | GLM max | medium → medium | `limit=100` default assumed before approval | partial / appropriate / present / focused | Pass |
| FastAPI | GPT medium | medium → low | Default raised as a question, partly assumed later | partial / appropriate / present / focused | Pass |
| FastAPI | GPT high | medium → low | Default raised as a question, partly assumed later | partial / appropriate / present / focused | Pass |
| FastAPI | GPT xhigh | medium → low | “Conventional defaults” stated too normatively | partial / appropriate / present / focused | Pass |
| FastAPI | GPT max | high → low | Unbounded offset-only behavior recommended/applied | partial / appropriate / present / focused | Pass |
| Flask/Vue | GLM low | low → medium | Unknown/case-insensitive `read` behavior invented | complete / appropriate / present / focused | Pass |
| Flask/Vue | GLM high | low → medium | Unknown/case-insensitive `read` behavior invented | complete / appropriate / present / mixed | Pass |
| Flask/Vue | GLM max | medium → medium | Unknown/missing-field behavior invented | complete / appropriate / present / mixed | Pass |
| Flask/Vue | GPT medium | medium → low | Query ambiguity correctly raised; minor filter split | complete / appropriate / present / focused | Pass |
| Flask/Vue | GPT high | medium → low | Minor filter-variant split | partial / mixed / missing / focused | Pass |
| Flask/Vue | GPT xhigh | medium → none | Clean grouping and scope | complete / appropriate / present / focused | Pass |
| Flask/Vue | GPT max | high → none | Clean grouping and scope | complete / appropriate / present / focused | Pass |

## Implications for future rewriting

### Requirement guidance

The preserved rewrite direction is supported:

- require necessity and semantic traceability;
- separate only independently meaningful outcomes;
- keep variants and boundary examples beneath requirements;
- treat unspecified public behavior as a question unless decision authority is
  explicit;
- keep implementation, testing, verification, documentation, and task scope
  in their own records.

The strongest new refinement is:

> A local or reversible implementation choice does not include public API,
> persisted-data, compatibility, security, privacy, or user-visible behavior.
> Those choices require explicit authority or a recorded question even when
> the code change would be easy to reverse.

### Testing guidance

The result does not support simply asking for fewer tests. It supports:

- plan the smallest evidence set that covers every required outcome;
- choose the layer containing the failure, not merely a cheap adjacent layer;
- include one real crossing when separate mocked tests bypass the claimed
  interaction;
- use representative boundary and regression cases;
- do not write tests for unresolved or unapproved behavior;
- keep exact internal calls, source identity, and incidental markup outside
  acceptance unless they are contractual;
- record an unavailable important test as a gap rather than substituting a
  weaker test and calling the requirement verified.

The task-file prompt should continue not to request a testing strategy.
Standing task guidance already elicits verification planning.

### Task guidance

Potential task-specific refinements are:

- distinguish material public decisions from local reversible implementation
  decisions;
- require planning diagnostics to leave the workspace clean;
- keep `Requirement verification` focused on user-relevant evidence;
- use `Additional implementation verification` only for material robustness
  risks, not as a place to accumulate internal source checks or tests for
  invented behavior.

The existing closing-section and no-premature-notes rules are already explicit.
Behavior tests should remain before adding more wording for those failures.

## Evidence

- [Accepted Dataset A candidate files](../../../../maintainer/agent-evaluation/suites/documentation_standard/fixtures/accepted_requirement_quality_baseline.json)
- [Dataset B task files and exact guidance metadata](../../../../maintainer/agent-evaluation/suites/documentation_standard/fixtures/current_task_guidance_requirement_quality_dataset.json)
- [All six calibrated semantic result batches](../../../../maintainer/agent-evaluation/suites/documentation_standard/fixtures/requirement_quality_semantic_results.json)
- [Accepted initial baseline interpretation](20260914-requirement-quality-baseline-results.md)
- [Subtask 067 plan and preserved future wording](../../../../tasks/20260728-package-local-documentation-standard/067-requirement-quality-model-effort-baseline.md)

Complete model sessions and canonical/raw run evidence remain available under
`tmp/agent-evaluation/documentation-standard/`.