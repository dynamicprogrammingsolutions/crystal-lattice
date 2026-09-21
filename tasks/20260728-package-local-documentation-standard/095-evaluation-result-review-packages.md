Parent Task:
tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- `tasks/20260728-package-local-documentation-standard/071-guidance-source-compilation-migration.md`
- `tasks/20260728-package-local-documentation-standard/080-maintainer-documentation-ownership-migration.md`

Uses completed evidence from:

- `tasks/20260728-package-local-documentation-standard/090-task-guidance-handoff-baseline-and-placement.md`

Owning specifications to update:

- `maintainer/agent-evaluation/docs/development/specifications/result-packages/index.md`
- `maintainer/agent-evaluation/docs/development/specifications/crystal-lattice-environment/index.md`
- `maintainer/agent-evaluation/suites/task_guidance/docs/development/specification.md`

Boundary correction:

- `maintainer/agent-evaluation/docs/development/specifications/framework/requirements.md`

Requirement IDs:

- `ERPKG-001`–`ERPKG-006`
- `CLEVAL-001`–`CLEVAL-004`
- `TGEVAL-012`–`TGEVAL-017`

# Evaluation Result Review Packages

Create a small reusable system for committing completed evaluation results as
regenerable, human-readable and machine-readable result packages. Move actual
task-guidance baseline and candidate results out of suite test fixtures,
preserve the inputs and outputs needed to diagnose model behavior, and support
changing report presentation or included metadata without rerunning models.

## Requirements checklist

### Shared evaluation result packages

- [ ] Completed evaluations can be preserved as compact, self-contained result
  packages that are useful to both human reviewers and machine consumers.
- [ ] Human-readable views can be regenerated deterministically from committed
  result data without rerunning models.
- [ ] Result packages can represent different suites' inputs, stages, outputs,
  and assessments without imposing domain-specific concepts on those suites.
- [ ] Result packages preserve enough provenance to understand how each
  included result was produced and clearly identify unavailable or
  reconstructed information.
- [ ] Result packages remain safe and proportionate: they exclude secrets and
  unnecessary diagnostic volume while retaining the information needed to
  understand significant execution or evaluation problems.
- [ ] Reviewers can compare available usage and estimated cost across
  evaluation runs, while incomplete usage or pricing remains visibly
  incomplete.

### Crystal Lattice evaluation adapter

- [ ] Crystal Lattice evaluation consumers can obtain an accurate review
  representation of delivered instructions, effective configuration, visible
  conversation, tool activity, execution failures, and available provider
  usage.
- [ ] Crystal Lattice review representations are lean, human-readable, safe to
  retain, and sufficiently detailed to diagnose relevant model or execution
  behavior.
- [ ] The Crystal Lattice representation is reusable by multiple evaluation
  suites and does not contain task-guidance, documentation-guidance, or other
  suite-specific semantics.
- [ ] The representation distinguishes information captured directly from
  information reconstructed or unavailable after the run.

### Task-guidance evaluation suite

- [ ] A task-guidance result package preserves the reviewed scenario context,
  model-produced plans and task files, continuation outputs, semantic
  assessments, and relationships needed to evaluate handoff and decomposition
  behavior.
- [ ] A reviewer can move from an aggregate task-guidance result to the exact
  relevant model output, generated task file, execution context, and semantic
  assessment without reconstructing the evaluation through command-line
  queries.
- [ ] Aggregate reports present the approved task-guidance quality dimensions
  clearly and summarize recurring execution concerns only when they materially
  affect interpretation.
- [ ] Usage and cost information supplied by the shared and Crystal Lattice
  layers is presented in the context of the relevant task-guidance run without
  changing task-quality judgments.

### Repository migration and durable results

- [ ] The completed current-guidance and task-mechanics evaluations are
  converted into durable, discoverable result packages without rerunning
  producer or assessor models.
- [ ] The migrated packages preserve the selected runs, generated task
  content, semantic results, and known historical limitations of the existing
  frozen records.
- [ ] Completed evaluation datasets no longer serve as suite test fixtures;
  focused synthetic data covers deterministic result-package behavior.
- [ ] Existing evaluation reports and navigation continue to lead maintainers
  to the migrated results.

## Scope

This task owns:

- reusable result-package collection and presentation support separate from
  the generic evaluation-kernel contract;
- a reusable Crystal Lattice review projection owned by the Crystal Lattice
  environment integration;
- the task-guidance result adapter and per-evaluation report configuration;
- lean Crystal Lattice session and input/output review exports;
- run-level usage and cost summaries;
- human indexes and machine manifests;
- migration of the completed task-guidance current-guidance and
  task-mechanics result sets;
- removal of completed evaluation datasets from suite fixture ownership after
  parity is proven.

This task does not own task-guidance wording, semantic scoring rules, model
calibration, or promotion decisions. Those remain in task 090. It also does
not add session, message, request, tool, provider, or presentation semantics to
the generic `agent_eval` kernel.

## Non-goals

- Rerunning producer, handoff, continuation, or semantic model requests.
- Building a web application, result database, benchmark service, or
  leaderboard.
- Committing complete successful tool output, provider stream events, cache
  entries, binary snapshots, pickles, temporary workspaces, or encrypted
  reasoning.
- Guessing historical GLM token usage or pricing when the saved provider
  session does not contain enough evidence.
- Maintaining two competing cost calculations or repricing historical reports
  automatically when a repository price table changes.
- Creating request-level cost tables or separate cost rollups by model,
  vendor, or provider.
- Hardcoding task files, plans, semantic dimensions, Crystal Lattice sessions,
  or provider usage semantics into the generic evaluation kernel.

## Verified ownership facts

- The generic `RunEnvironment` exchanges opaque snapshots and observations.
  The kernel does not define or inspect sessions, messages, prompts, tools,
  providers, or assessment semantics.
- Generic `agent_eval` modules import neither `agent_core` nor `agent_app`.
  Those dependencies and the `Session` type begin in the optional
  `agent_eval.crystal_lattice` integration.
- The generic kernel already owns run identity, lifecycle, workspace, cache,
  continuation, opaque evidence persistence, result location, and structured
  errors. This task does not expand that stable execution contract.
- The former `AEVAL-017` requirement combined generic persistence, Crystal
  Lattice provenance, and suite presentation. The owning specifications split
  those responsibilities rather than replacing them with a new kernel
  requirement.

## Approved decisions

- September 21, 2026: completed evaluation records belong with the interpreted
  evaluation under `maintainer/docs/evaluations/`, not in a suite fixture
  directory.
- Use a result directory per named evaluation and keep the existing dated
  summary page as an entry point during migration.
- Store canonical machine records and generated human views together, with a
  manifest identifying source hashes, generator version, report config, and
  generated files.
- Specify reusable result-package support separately from the generic
  evaluation-kernel specification.
- Put reusable Crystal Lattice session/request/configuration/usage review
  projection in the Crystal Lattice environment integration; task-guidance
  semantics remain in the task-guidance suite.
- Preserve visible messages and tool-call intent but omit full tool results
  from the committed lean session view.
- Keep recurring diagnostic findings only in an aggregate table when they are
  demonstrated and useful.
- Use one price table selected by the report config and one run-level cost
  calculation.
- Use one row per run for usage and cost. Include model and provider columns
  for filtering, but do not add request-level rows or separate model/vendor
  aggregate tables.
- Generate the task-mechanics package first, review one representative failing
  cell, adjust the report config, then generate the complete candidate and
  current-guidance packages.

## Supporting facts

- Current task-guidance raw run directories occupy approximately 720 MB, while
  the committed frozen result files occupy approximately 3.7 MB.
- A sampled GPT session is approximately 650 KB in raw JSON and approximately
  67 KB after normalizing messages and omitting full tool results.
- Saved GPT sessions include reported input, output, reasoning, estimated
  cached-input, cumulative token, and estimated cost metadata.
- Saved GLM task-guidance sessions do not contain equivalent usage or cost
  fields, so those historical runs must be marked unknown unless another
  verified source is identified.
- GLM sessions retain the exact compiled system message in
  `compiled_content`. GPT task-guidance runs retain its hash but not the full
  compiled text even though the runner computed it before the request.
- GPT system messages can be reconstructed without a model request from the
  recorded fixture, guidance source, runtime config, and compiler path, then
  accepted as verified only when the reconstructed SHA-256 matches.
- Projected configs are not sufficient presentation by themselves because the
  model and effort are changed by runtime profile overrides. The package needs
  a sanitized effective-config view.
- Semantic assessor sessions preserve the exact user prompt and response.
  Human review still benefits from a separately rendered concise rubric
  because the exact prompt may embed several complete subjects.
- The GPT price snapshot and saved cost metadata demonstrate why a result
  package must pin its own selected price table instead of depending on
  whatever table the repository uses later.

## Proposed result package

```text
maintainer/docs/evaluations/task-guidance/results/
└── 20260919-task-mechanics-b1/
    ├── index.md
    ├── manifest.json
    ├── matrix.md
    ├── matrix.json
    ├── costs.md
    ├── costs.csv
    ├── report-config.toml
    ├── shared/
    │   ├── configs/
    │   └── system-messages/
    └── cases/
        └── <scenario-id>/
            ├── index.md
            └── <model-effort>/
                ├── index.md
                ├── cell.json
                ├── input/
                ├── stages/
                └── assessment/
```

The suite adapter determines the contents and names under `stages/`. A
task-creation run may export task files; a future plan-to-task evaluation may
export separate plan, task-creation, and fresh-agent-plan stages.

## Open questions

- Should full compiled system messages retain safe absolute workspace paths,
  or should paths be normalized while preserving the exact original hash and
  a replacement map? Recommendation: normalize machine-specific paths and
  preserve the original hash plus classification.
- Should the old dated report become the directory's `index.md` immediately,
  or remain a compatibility entry point until both existing result sets are
  migrated? Recommendation: retain the current page as a short entry point
  during the first migration.
- What approved price or billing representation, if any, should be supplied
  for historical GLM cloud runs without saved token usage? Recommendation:
  keep usage and cost unknown rather than infer them from characters or a
  different model tokenizer.
- The exact generic protocol and command names are local, reversible
  implementation choices. Prefer `collect`, `render`, and `check` semantics
  unless existing `agent_eval` conventions suggest smaller names.

## Execution plan

Status: Draft

Define result-package support as an optional reusable component separate from
the generic evaluation-kernel contract. Separate collection from rendering:
collection reads suite-selected run records and environment-owned projections
and produces a committed package; rendering consumes only that package and the
committed report config. This allows Markdown layout, metadata selection, and
cost presentation to change without invoking a model or requiring temporary
raw directories.

Add a reusable Crystal Lattice review projection that produces lean session,
instruction, effective-configuration, tool-activity, failure, and usage
material without suite semantics. Implement a task-guidance adapter that
identifies producer, handoff, continuation, and assessment stages; exports
generated task files; and maps semantic judgments to their subject runs.

Use task-mechanics candidate v1 as the first migration. Export one
representative GPT-xhigh book-discovery cell and review its input, generated
tasks, normalized session, assessment, config, and run-level cost before
generating the complete package. After the layout is accepted, generate the
current-guidance package with the same structure, prove parity, update links,
replace real-result test dependencies with synthetic fixtures, and remove the
old suite-fixture result copies.

### Implementation decisions and open questions

- Do not begin collection or migration until this Draft plan is approved.
- Collection may use current raw run directories for the initial migration,
  but committed packages must be sufficient for later `render` and `check`
  operations.
- Future runs should record the full compiled system message and sanitized
  effective config directly so historical reconstruction is unnecessary.
- The reusable result-package component consumes opaque suite records and
  environment-owned projections; it does not define a session contract.
- The Crystal Lattice integration owns the shared lean-session and request
  projection used by any Crystal Lattice-backed suite.
- The report config owns its price table. Cost rendering uses only that table
  and the run's aggregated usage fields.
- Cost totals are per run. Continuation lineage must avoid counting inherited
  session history as newly consumed usage.
- Missing usage, price, system-message text, or config fields use explicit
  availability states.
- Resolve the path-normalization and compatibility-entry-point questions
  before finalizing the package schema.

### Documentation

- Add a separate package-local result-package specification and development
  documentation without presenting it as part of the kernel API.
- Correct the former generic `AEVAL-017` provenance requirement and link its
  environment- and suite-owned replacements.
- Update the Crystal Lattice environment specification with its reusable
  review-projection outcomes and boundaries.
- Update task-guidance suite documentation with its report adapter, package
  contents, generation commands, and historical limitations.
- Replace the current command-heavy inspection guide with the generated result
  package navigation once migration is complete.
- Link the two migrated packages from the task-guidance evaluation index and
  dated reports.

### Task checklist

- [ ] Approve this execution plan and resolve the material open questions.
- [ ] Add the separate result-package specification and correct the former
  framework provenance requirement.
- [ ] Add Crystal Lattice and task-guidance requirements to their owning
  specifications.
- [ ] Define the result-package manifest, availability, redaction, usage,
  cost, and suite-adapter contracts without a generic session schema.
- [ ] Define the reusable Crystal Lattice review projection.
- [ ] Implement collection, rendering, and deterministic check support.
- [ ] Add synthetic unit/integration fixtures for package generation.
- [ ] Implement the task-guidance result adapter and report configuration.
- [ ] Export and review the representative GPT-xhigh book-discovery cell.
- [ ] Adjust the package schema/config after human review.
- [ ] Generate the complete task-mechanics candidate package without model
  requests.
- [ ] Generate the current-guidance package with the same structure.
- [ ] Verify task files, selected identities, scores, prompts, and run-level
  usage/cost against saved records.
- [ ] Update evaluation indexes, reports, running guidance, and package docs.
- [ ] Replace completed-result suite fixtures with synthetic test data.
- [ ] Remove the old task-guidance fixture result copies after parity and link
  checks pass.
- [ ] Record historical missing-data limitations and completion evidence.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Ownership boundaries | Kernel behavior and imports remain unchanged; generic result packaging consumes opaque records, the Crystal Lattice integration owns session/request projection, and task-guidance types remain suite-owned. |
| Canonical package | A collected evaluation package validates against the manifest/schema, records source and generated hashes, and can be copied to a clean checkout. |
| Regeneration | Delete generated Markdown/CSV views, run `render`, and reproduce them byte-for-byte from committed machine records and `report-config.toml` without raw runs or model access. |
| Task-dependent stages | Synthetic coverage and the task-guidance adapter export different stage shapes without changing the generic schema. |
| Inputs and configuration | Representative subject and assessment cells expose system message, prompt, target, effective config, tools, fixture/guidance provenance, and availability classification. |
| Outputs and sessions | The Crystal Lattice projection and representative cell expose assistant responses, generated task files, lean session commentary/tool calls, concise failures, and no full tool results or encrypted reasoning. |
| Semantic review | The exact assessment prompt/response, concise rubric, parsed result, assessor config, and subject links agree with the saved semantic record. |
| Usage and cost | One row per run reports available token categories and one configured-price cost; estimated cached input is used; missing GLM usage remains unknown; continuation history is not double-counted. |
| Historical migration | Both task-guidance packages reproduce current selected identities, generated task text, outcome coverage, issue metrics, and invalid/retry status without model requests. |
| Ownership migration | Completed evaluation records no longer live under suite fixtures; deterministic suite tests use synthetic result data and maintained links resolve. |
| Security and focus | Secret scanning and fixture inspection find no credentials, auth headers, secret environment values, full tool-result dumps, encrypted reasoning, cache data, or binary snapshots in committed packages. |
| Human review | From the package index, a reviewer can reach a failed dimension, exact generated file, session timeline, system message, prompt, config, assessment, and cost row without command-line extraction. |

### Additional implementation verification

- Compare package size with the current frozen JSON and raw directories; report
  any unexpectedly large generated section before committing it.
- Run generation twice and compare hashes to prove deterministic ordering and
  rendering.
- Verify the generic kernel source and API do not acquire Crystal Lattice,
  session, message, provider, task-guidance, or report-presentation semantics.
- Verify path normalization does not remove instruction content or break the
  recorded compiled-message hash classification.
- Exercise one invalid/retried cell and one continuation chain so selection,
  lineage, and run-level usage remain reviewable.
- Run the generic `agent_eval`, task-guidance suite, documentation-link, and
  guidance-compiler tests affected by the migration.
