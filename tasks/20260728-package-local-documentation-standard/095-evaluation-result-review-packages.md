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
  package must pin its own price table instead of depending on whatever
  table the repository uses later. The maintained snapshot is
  `plugins/openai_responses/src/openai_responses_plugins/data/openai_model_pricing.json`
  (fetched 2026-07-18); its gpt-5.6-luna standard-tier rates are input
  $1.00/1M, cached input $0.10/1M, cache write $1.25/1M, output $6.00/1M.
  The saved per-turn cost metadata was computed from this same snapshot, so
  a pinned copy reproduces the historical estimates exactly.
- Verified September 21, 2026: each raw run directory contains
  `result.json` (including `parent_run_id`), `records/<record>.json`,
  `raw/environment/crystal-lattice-session.json`,
  `raw/environment/crystal-lattice-observation.json`, and
  `raw/workspace/git-diff.patch`.
- Verified: GLM sessions retain the full compiled system message in
  `compiled_content` (about 18 KB with exactly one machine-specific absolute
  path, the run workspace) but no usage metadata; GPT sessions retain no
  system message but carry per-assistant-message usage (input, output,
  reasoning, cached, and cache-write tokens, per-turn and cumulative
  provider-reported cost; one sampled producer run totals 91,279 input and
  8,823 output tokens, $0.0789 cumulative).
- Verified: same-agent continuation sessions contain the complete inherited
  parent history (sample: 62 messages where the parent has 28), so
  `parent_run_id` plus the parent session is required to bound the inherited
  prefix and avoid counting inherited history as new usage.
- Verified: no deterministic test reads the frozen fixture result JSONs;
  `test_documentation.py` checks the review page set and link integrity,
  and `freeze_b0.py` defaults its output to the fixture results path.
- Verified: the raw runtime configs used by the runs are preserved under
  `tmp/agent-evaluation/task-guidance/runtime-config/<hash>/` (config,
  system-message sources, TASKS copies) with projected configs under
  `projected-config/`, and the guidance sources have not changed since the
  runs, so hash-verified reconstruction of GPT system messages is plausible.

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

Status: Approved

The user approved this plan and the four open-question resolutions on
September 21, 2026.

### 1. Generic result-package support

Add an optional reusable library module, `src/agent_eval/result_packages.py`,
separate from the kernel contract and free of Crystal Lattice imports. Split
collection from rendering: collection reads suite-selected records plus
environment-owned review projections and writes committed source records and
a manifest; rendering reads only the committed package and its report
configuration and regenerates every human or machine view; checking verifies
manifest hashes and byte-for-byte regeneration. The module defines only
structural contracts — package identity, run references, stage shapes,
availability states (`captured`, `reconstructed` with verification, and
`unavailable`), redaction hooks, normalized-path classification, and one
configured usage/cost presentation. Suite and environment records remain
opaque named values, so layout, metadata selection, and cost presentation can
change later without invoking a model or requiring temporary raw directories.

### 2. Crystal Lattice review projection

Add `src/agent_eval/crystal_lattice/review.py`. It projects a saved session,
observation, and effective configuration into lean review material:
delivered instructions with provenance, visible user and assistant messages,
tool-call intent with concise status and failures (no full tool results, no
encrypted reasoning), request boundaries, runtime errors, and aggregate
provider usage. It redacts secret values and normalizes machine-specific
paths while recording the original hash, classification, and replacement map;
bounds an inherited continuation prefix using the parent run's session; and
classifies every important field as captured, reconstructed, or unavailable.
It contains no task-guidance, documentation-guidance, or other suite
semantics.

### 3. Task-guidance adapter and report configuration

Implement the suite result adapter and a `collect`/`render`/`check`
command-line entry point under `suites/task_guidance/`. The adapter selects
the frozen b0/b1 consolidated records plus raw run directories; maps
producer, handoff, continuation, control, and assessment stages onto the
scenario/cell layout; exports generated task files; deduplicates scenario
targets; maps semantic judgments to their subject runs; reconstructs GPT
system messages from the preserved runtime-config sources with SHA-256
verification against the recorded `compiled_sha256`; and supplies sanitized
effective-config views. The committed `report-config.toml` pins the price
table — the gpt-5.6-luna standard-tier rates copied from the maintained
OpenAI pricing snapshot (fetched 2026-07-18) with source provenance — so
later repository snapshot refreshes cannot reprice these reports. Historical
GLM usage and cost remain unknown. Future runs record the compiled system
message and sanitized effective config directly so historical reconstruction
is unnecessary.

### 4. Representative cell review gate

Collect one representative failing cell — the GPT-xhigh Flask/Vue
book-discovery producer from the task-mechanics dataset — and pause for human
review of its input, generated task files, normalized session, assessment,
effective config, system-message provenance, and run-level cost row. Adjust
the package schema and report configuration from that review before
generating any complete package.

### 5. Complete migration and parity

Generate the complete `20260919-task-mechanics-b1` package, then the
`20260919-current-guidance-b0` package, both under
`maintainer/docs/evaluations/task-guidance/results/`, without model requests.
Prove parity automatically: selected identities, task-file text, prompts,
responses, scores, occurrence counts, invalid records, and run-level
usage and cost must agree with the frozen records and saved sessions, and
regeneration must be byte-for-byte deterministic across two consecutive
runs. Exercise one invalid or retried cell and one continuation chain
explicitly so selection, lineage, and run-level usage remain reviewable.

### 6. Documentation and navigation

Update the task-guidance evaluation index, both dated reports, and the
maintainer evaluations index to lead to the packages; rewrite the
command-heavy inspection section of the reproduction guide into package
navigation while keeping the reproduction commands; add package-local user
and development documentation for the new modules; and update the owning
requirement ledgers (`ERPKG-*`, `CLEVAL-*`, `TGEVAL-012`–`TGEVAL-017`) as
implementation, verification, and documentation progress.

### 7. Fixture replacement

After parity and link checks pass, replace completed-result suite fixtures
with focused synthetic data covering collection, rendering, checking,
projection, and adapter behavior, point `freeze_b0.py`'s default output away
from fixture ownership, and remove the old fixture result copies.

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
  and the run's aggregated usage fields. The pinned table copies the
  gpt-5.6-luna standard-tier rates from the maintained OpenAI pricing
  snapshot (fetched 2026-07-18) with source provenance; provider-reported
  cost metadata remains captured provenance, and the parity check compares
  it with the pinned-table calculation.
- Cost totals are per run. Continuation lineage must avoid counting inherited
  session history as newly consumed usage.
- Missing usage, price, system-message text, or config fields use explicit
  availability states.
- Proposed resolutions for the open questions, pending plan approval:
  normalize machine-specific paths while preserving the exact original hash,
  a path classification, and a replacement map; keep the dated reports as
  short entry points linking to the generated package indexes during the
  first migration; keep historical GLM usage and cost unknown rather than
  inferred; and use `collect`, `render`, and `check` command semantics.
- The semantic assessment batches are scenario-level records; the adapter
  places them so each cell links to its own judgments without duplicating
  the batch. Exact stage and assessment file names are adapter-owned and
  finalized at the representative-cell review.

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

- [x] Approve this execution plan and resolve the material open questions.
- [x] Add the separate result-package specification and correct the former
  framework provenance requirement.
- [x] Add Crystal Lattice and task-guidance requirements to their owning
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

## Implementation Notes

- September 21, 2026: the user approved the execution plan and the four
  open-question resolutions (path normalization with original hash and
  replacement map; dated reports retained as entry points; GLM usage and cost
  kept unknown; `collect`/`render`/`check` command semantics). The pinned price
  table copies the gpt-5.6-luna standard-tier rates from the maintained
  OpenAI pricing snapshot fetched 2026-07-18. Implementation began after
  approval.
