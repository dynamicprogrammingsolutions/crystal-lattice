# Establish the Current Product and Compatibility Baseline

Create an evidence-backed catalog of current configured agents, providers,
accounts, application-wide features, defaults, optional behavior, limitations,
and verification state.

## Requirements checklist

- [x] Configured-agent compatibility is cataloged separately from
      provider/account support and application-wide features.
- [x] The catalog distinguishes repository presence, packaging, loading,
      default enablement, frontend support, automated verification, and
      real-provider verification.
- [x] Important gaps and limitations are explicit without implying full parity
      with official upstream coding-agent products.
- [x] The retained review output provides three exhaustive product-named
      matrices: the plugin feature catalog, provider-native support, and
      model-family-specific features.
- [x] A compact canonical website projection selects non-overlapping product
      features, user-relevant provider columns, and package-specific current
      and planned tool rows for human verification before publication.
- [x] The result is suitable as a maintained source for later website and
      contributor-facing compatibility content.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/010-website-documentation-and-content-specification-foundation.md`

## Scope

Audit:

- configured-agent profiles and model-family compatibility packages;
- provider routes and model discovery;
- API-key, subscription-account, and local-model authentication paths;
- system/developer instructions and tool surfaces;
- compaction, memory, skills, MCP, todo/planning, web, media, background, and
  provider-native behavior;
- session, action, notification, filtering, status, export, attachment,
  transparency, and configuration features;
- mobile, desktop, terminal, and HTTP rendering or execution support.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared program requirements, decisions, facts, handoff rules, output
   rules, and boundaries.
2. `landing_page/AGENTS.md:1-68` — package claim, research, privacy, and
   evidence boundaries.
3. `landing_page/docs/development/specifications/product-website-content/content-spec.md:14-218`
   — current product baseline, visitor groups, compatibility, transparency,
   features, customization, and connection distinctions that the catalog must
   eventually support.
4. `landing_page/docs/development/research/positioning-and-product-baseline.md:9-170`
   — current facts, hypotheses, compatibility recommendations, and open
   questions. Correct it rather than creating a competing baseline.
5. `landing_page/docs/development/research/evidence-index.md:18-75` — current
   product, plugin, compatibility, feature, and release source map.
6. `application/python/agent_terminal_app/default_config/config.json` —
   checked-in default providers, globally declared plugins, application
   settings, mixins, and configured-agent composition. Re-locate the named
   sections at the revision being audited; historical line ranges have drifted.
7. `plugins/docs/index.md:1-32` — plugin documentation router. Follow the
   owning package README, AGENTS, docs, source, and tests only for rows being
   classified or verified.

### Additional references

- `landing_page/docs/development/specifications/product-website-content/requirements.md:6-22`
  — compatibility, current-state, transparency, contribution, and proof
  requirements.
- Mobile, desktop, terminal, frontend, and provider package documentation
  identified by the evidence index when a row requires client or real-provider
  verification.

## Known facts and supporting details

- The default configuration is coding-agent-oriented and combines model-family
  profiles, provider routes, global application plugins, and optional features.
- A compatibility package name is not evidence of complete parity with the
  official upstream product.
- Provider/account support and configured-agent behavior are separate axes.
- Application-wide session and transparency features may apply independently
  of a configured-agent profile.
- “Present in source,” “packaged,” “loaded,” “default-enabled,”
  “frontend-supported,” “automatically tested,” and “real-provider verified”
  are different states.
- Website content will consume the catalog but must not become authoritative
  for the underlying package behavior.
- At the planning revision, the checked-in default config declares 20 agents,
  seven provider routes, and 28 global plugin specs. These are inventory
  counts, not proof that every profile or plugin works across every client or
  distribution.
- The checked-in `codex-openai` agent currently specifies `gpt-5.4-mini`;
  the user's active session instead uses `codex-openai`, `gpt-6-sol`, and high
  reasoning effort through a personal configuration. Investigators may use
  that active profile, but the checked-in default and personal runtime must
  remain distinct evidence populations.
- Completed sibling tasks
  `tasks/20260825-crystal-lattice-product-positioning-and-website/021-headless-agent-runs-and-optimized-history-api.md`
  and
  `tasks/20260825-crystal-lattice-product-positioning-and-website/022-session-and-message-query-projections.md`
  provide current synchronous persisted CLI/Python runs and projected
  session/message reads. They do not deliver persistent parent-child
  subagents or a single-command cross-session text search. The additional
  usability gaps recorded in task 021 remain follow-up work.

## Expected outputs

Human-readable finding:

- `landing_page/docs/development/research/findings/current-product-and-compatibility-baseline.md`

Retained research package:

```text
landing_page/research/020-current-product-and-compatibility-baseline/
├── input-manifest.json
├── compatibility-matrix-source.json
├── generate_compatibility_matrices.py
├── feature-catalog.json
├── feature-catalog.csv
├── provider-support-matrix.json
├── provider-support-matrix.csv
├── model-family-feature-matrix.json
├── model-family-feature-matrix.csv
├── compatibility-matrices.md
├── website-compatibility-selection.json
├── generate_website_compatibility_data.py
├── website-compatibility-data.json
├── website-compatibility-data.md
├── catalog-schema.json
├── catalog-review-overrides.json
├── extract_baseline.py
├── configured-agent-compatibility.csv
├── provider-account-compatibility.csv
├── application-feature-compatibility.csv
├── claim-evidence.jsonl
├── verification-summary.md
└── completion-manifest.json
```

The three product-named matrix concepts and
`compatibility-matrices.md` are the authoritative review outputs. The older
configured-agent, provider/account, and application-feature CSVs remain
supporting normalized extraction and evidence inputs rather than separate
website-facing matrices.

Required updates:

- `landing_page/docs/development/research/positioning-and-product-baseline.md`
  for corrected shared facts;
- `landing_page/docs/development/research/evidence-index.md` for authoritative
  catalog and verification routes;
- `landing_page/docs/development/specifications/product-website-content/requirements.md`
  only for requirement evidence/status affected by delivered documentation,
  not for unimplemented public content.

## Scope boundaries

- Do not perform broad market, search-demand, community, or competitor
  research.
- Do not change `landing_page/src/content/`.
- Do not change the content target merely because a product capability exists.
- Do not create provider or compatibility claims without checking the owning
  source and appropriate verification boundary.
- Store disposable inspection output under
  `landing_page/artifacts/research/020-current-product-and-compatibility-baseline/`.

## Execution plan

Status: Approved

**Design and ownership.** Treat the checked-in default configuration at the
audited commit as the starting population. Retain three authoritative matrix
concepts under the task-declared research package: an exhaustive plugin
feature catalog, a provider-by-native-feature matrix, and a
model-family-by-feature matrix. Each has normalized JSON and long-form CSV;
one generated Markdown document presents all three for review. Keep the
earlier configured-agent, provider/account, and application-feature CSVs as
supporting normalized extraction/evidence inputs. Provider, plugin,
application, client, and release packages remain authoritative for their own
behavior. Keep one `claim-evidence.jsonl` record per consequential assertion
with stable claim and row IDs, source paths/revisions, verification method,
observation date, and human-review state. The input and completion manifests
identify the transformation version, checked-in config fingerprint,
distribution targets, accepted outputs, and limitations. Repeatable
generators and validators produce config-owned fields and matrix projections;
manual classifications and disagreements stay visible rather than silently
overwriting extracted facts.

**Inventory boundaries.** Cover every checked-in default agent ID, provider
route, configured global plugin, and pertinent application setting. Classify
agents by role and compatibility family so specialized cloud and image agents
do not imply official upstream-product parity. Inspect optional first-party
packages only when needed for the named scope (prompts/tools, compaction,
memory, skills, MCP, planning, web, media, background work, provider-native
behavior, and application/session features). Identify test, template, and
implementation-only projects without treating them as shipped user features.
Do not build a full plugin-project-by-agent-by-client matrix.

**Status and evidence flow.** Each applicable row records separately:
capability state (current, optional, partial, experimental, planned,
unsupported, not applicable, or unknown); source presence; selected
distribution and packaging; global/provider/agent/optional loading;
default and session-level enablement; runtime prerequisites; HTTP execution
or configuration support; terminal, mobile, and desktop rendering and
interaction; automated coverage present; tests actually run and their
revision/date; real-provider verification; limitations; and evidence IDs.
Mark genuinely unexamined states `unknown`. In particular distinguish
model-family profiles from provider/auth/account routes; Ollama cloud models
from local weights; prompt references to memory/tasks from actual persistent
memory or task tools; and HTTP endpoints from visual frontend support.

**Investigation and collaboration.** Start with deterministic extraction of
the checked-in default config, resolved mixins/variants, plugin descriptors,
packaging closure, and distribution manifests in an isolated resolution
environment. Pin `CONFIG_DIR`, `BUILTIN_PLUGINS`, and `WORKING_DIR`; avoid
retaining credential values. Then inspect only row-owning docs, source,
config, and tests. Use up to three distinct persisted Crystal Lattice
sessions for bounded read-only investigations of (1) configured-agent
compatibility, (2) provider/account/distribution paths, and (3)
application/client features if they materially speed the review. The current
task default is the calibrated `gpt-5.6-terra` / `high` investigator; set and
verify the intended model and effort explicitly for each child run through the
private audit config. Give workers exact scope, source revision, evidence
shape, and mutation boundaries. Retrieve only final reports and bounded
projected history, retain IDs/inputs in the manifest, and verify proposed
claims independently before promoting them. Ordinary persisted sessions are
not treated as parent-linked subagents.

The user-authorized GPT-5.6 model/effort calibration is the sole exception to
that ordinary three-session investigation limit: it evaluated six intended
configurations and created one additional abandoned Terra-xhigh session while
changing orchestration from serial to parallel. Future product-evidence work
returns to bounded package batches and no more than three concurrent
investigator sessions unless separately approved.

**Trial checkpoint approved 2026-09-29.** Before scaling any delegated
investigation, run two or three bounded turns in *each* of the three distinct
investigator sessions. Stop and report observed performance, answer quality,
cost, specific package findings and their usefulness to the catalog. Continue
the broader audit only after the user reviews this checkpoint.

**Continuation of delegation.** Use only the GPT-5.6 family for this task.
Default canonical package audits to `gpt-5.6-terra` at `high`; use
`gpt-5.6-luna` at `high` for broad, test-heavy sweeps where a somewhat longer
run is acceptable. Reserve `gpt-5.6-terra` at `xhigh` for narrower,
high-risk synthesis that justifies roughly twice the latency and a larger
evidence packet. Do not use Sol or Luna at `xhigh` for this broad one-shot
audit shape unless a later bounded calibration changes the result. Record
actual model, effort, wall time, and cost for every batch.

Each worker receives the ordinary Codex model-specific instructions plus an
appended task-020 evidence-auditor system section. Narrow the named packages,
define decision questions, allow focused local tests, and require exact
commands, collection/result state, and skipped gates. Require the worker to
write `report.md`, `claims.jsonl`, `verification.md`, and `review-notes.md`
under a distinct ignored directory. For deep work, require an initial claim
map and incremental packet writes before extended testing so a timeout does
not discard the investigation. Independently review before moving bounded
evidence into the retained research package. Preserve the human-review gate
for claims that will guide website copy.

**Broader-audit waves and budget (planned 2026-09-29).** Reuse the
Codex/OpenAI calibration packets as proposed evidence instead of rerunning
that slice. First define the CSV schemas and deterministically extract all 20
checked-in agents, seven provider routes, 28 global plugin specs, and the
selected packaging closure. Then use fresh one-turn sessions in these bounded
batches, with no more than three concurrent:

1. `gpt-5.6-terra/high`: Claude profiles, Claude tools, direct Anthropic, and
   OpenRouter/Anthropic route distinctions.
2. `gpt-5.6-terra/high`: Qwen, Gemini, Grok, Kimi, and GLM compatibility
   profiles, prompt/tool packages, web routes, and parity limits.
3. `gpt-5.6-terra/high`: Ollama local versus cloud models, Fireworks, Z.ai,
   reference-compatible providers, discovery, credentials, and verification.
4. `gpt-5.6-terra/high`: image-generation and cloud-script specialist agents,
   source/bundled/optimized/cloud packaging selection, and unknown artifacts.
5. `gpt-5.6-luna/high`: session-list organization features—search, titles,
   generated titles, pin/archive/status/order/actions/count/timestamps—and
   their filter/action contracts.
6. `gpt-5.6-luna/high`: message/history features—summaries, exports,
   attachments/assets, snapshots, compaction, media, and query/projection
   boundaries.
7. `gpt-5.6-terra/high`: configuration and transparency features—auth,
   system/request options, MCP, file/web context, usage/cost/duration,
   application configuration/reload, cloud/background behavior.
8. `gpt-5.6-luna/high`: HTTP, terminal, frontend SDK, mobile, and desktop
   production-consumer matrix for decision-bearing rows from prior batches.

After each wave, independently review citations and tests, reject weak or
duplicated claims, and narrow later prompts. Use one optional
`gpt-5.6-terra/xhigh` session only for a small set of material contradictions
remaining after ordinary review; do not give it the complete inventory again.
Require an initial claim map and incremental writes before tests, a 22-minute
timeout for high runs, and a 30-minute timeout for the optional xhigh run.

At calibration rates, five Terra/high and three Luna/high runs project to
about **$6.82**. Allowing for varying package complexity, one failed/retried
batch, and the optional Terra/xhigh challenge gives an expected additional
range of **$8–$12 API-equivalent cost**. Use **$18** as the broader-audit stop
ceiling. Stop launching work and report if observed cost reaches $15 before
optional synthesis, or if a batch fails to write its initial claim map within
eight minutes. Hosted-provider checks are excluded and remain separately
authorized. These ChatGPT-route figures are estimates, not subscription
invoices.

**Verification and handoff.** Check decision-critical behavior through the
smallest public boundary containing the claim: resolved runtime for agent
enablement; distribution inputs/manifest for packaging; actual API plus the
production frontend adapter for a client feature that crosses both; and
dated, model/auth-specific evidence for real-provider operation. Existing
gated tests count as coverage only until actually executed at the pinned
revision. Choose a small representative deterministic/local integration
slice for disputed claims; record hosted API checks as unrun until separately
authorized. Prepare decision-bearing classifications, explicit limitations,
counterexamples, and unknowns for the user's human review; record the
reviewer's actual decisions before marking those conclusions accepted.
Write the human finding and update the shared baseline/evidence index for
verified facts, leaving public copy and downstream feature-value research to
their owning tasks.

### Implementation decisions and open questions

- The three task-declared CSVs are the durable reviewed research source for
  later website/contributor content; they are derivatives, not a new
  product-wide compatibility contract. This resolves the earlier location
  question in the direction agreed during the preliminary review.
- Evidence must distinguish "test exists" from "test ran and passed here",
  source/default configuration from a personal session, and source checkout
  from bundled-Python, optimized, and cloud-specific packaging. A release
  target not examined is marked unknown rather than inferred from source.
- Limit task 020 to current Crystal Lattice behavior and internal
  compatibility claims. Official-upstream comparisons belong to task 080;
  user jobs, pain, alternatives, and proof priority belong to task 050.
- The calibrated `gpt-5.6-terra`/high settings guide ordinary investigative
  delegation; they do not replace checked-in product-default classifications.
  Do not silently broaden validation or incur hosted provider charges to make
  unverified rows look complete.
- No requirement question remains from the agreed scope. Local CSV column
  names, extraction script placement, and the precise manual-review ledger
  layout may be settled during execution without altering required outcomes.

### Documentation

- Add the task-declared human-readable research finding only after evidence
  and review produce substantive conclusions; route it from the research
  index where needed.
- Correct verified shared facts in the positioning/product baseline and add
  the retained catalog and evidence routes to the evidence index.
- Add requirement evidence only where task 020 actually advances
  documentation; leave website-public implementation statuses open until
  public content is delivered by downstream tasks. Do not publish tentative
  compatibility or target-only claims as current user documentation.

### Task checklist

- [x] Capture the source revision, default-config fingerprint, distribution
      targets, and isolated config-resolution inputs in `input-manifest.json`.
- [x] Define stable row/evidence IDs, three CSV schemas, status vocabulary,
      review state, and repeatable extraction/validation.
- [x] Inventory every default configured agent and classify roles,
      compatibility-family prompts/tools, runtime activation, and important
      support gaps.
- [x] Inventory provider routes, authentication/account modes, model
      discovery, local versus Ollama-cloud prerequisites, and verification
      freshness.
- [x] Inventory default and relevant optional application features, selected
      distributions, and backend/terminal/mobile/desktop support boundaries.
- [x] Run two or three trial turns per distinct investigator session and
      report time, quality, cost, and specific package findings; pause for
      the approved user checkpoint before the broader audit.
- [x] Side todo on continuation: correct `plugins/codex-tools` automatic shell
      selection for the supported GPT-5.6 and GPT-6 variants, including the
      checked-in `gpt-5.6-sol`/`terra`/`luna` and
      `gpt-6-sol`/`luna`/`astra` names. Verify actual plugin/tool selection
      with focused regression coverage, preserve the existing GPT-5 and
      `*-codex` behavior, update the owning plugin docs, and record the
      pre-fix and post-fix source states separately in the catalog evidence.
- [x] Run broader bounded delegated investigations where useful, retain
      concise reports in ignored scratch, and independently review claims.
- [x] Enforce the broader-audit wave, timeout, checkpoint, and $18
      API-equivalent stop budget; record each batch's model, effort, session,
      duration, cost, packet completeness, and review disposition.
- [x] Run focused deterministic/public-boundary verification for disputed or
      decision-critical rows and record genuine hosted-verification gaps.
- [x] Prepare the three CSVs, claim evidence, limitations, counterexamples,
      verification summary, manifest lineage, and stable regeneration for
      human review.
- [x] Generate the three authoritative exhaustive matrix concepts in JSON and
      CSV plus one product-named Markdown review: 66 plugin projects, 10
      provider routes × 19 native-feature cells, and 12 model-family groups ×
      21 feature cells.
- [x] Record the user's approval of all nine decision-bearing
      classifications and update the 60 normalized catalog rows and 24 claim
      records to `accepted`.
- [x] Generate the canonical website projection with 9 non-overlapping
      product features, 9 provider rows × 6 selected columns, and 71 current
      or planned package-specific tool rows across 6 model-family bundles.
- [x] Record user verification or corrections for the canonical website
      projection and update its review state.
- [x] Write the finding and `completion-manifest.json`, finalize the existing
      verification summary, and correct the shared research baseline and
      evidence index.
- [x] Update affected website content-requirement evidence only when
      supported, then record requirement evidence and completion notes in
      this task and its parent.

### Requirement verification

- **Separate catalog views:** validate the exhaustive product-named feature,
  provider, and model-family matrices plus their supporting normalized
  extraction from the checked-in resolved default config without flattening
  compatibility profiles into upstream products.
- **Distinct support states:** inspect representative cells in each
  authoritative JSON/CSV matrix through owning config/source, packaging and
  release inputs, loaded/default runtime behavior, and the relevant public
  client path. Where the claim spans HTTP and a frontend, use a real HTTP
  backend with the production frontend adapter. Verify that supported,
  conditional, planned, unsupported, not-applicable, unknown, optional, and
  unrun-hosted examples retain different states.
- **Gaps and parity restraint:** human review of the finding and
  decision-bearing rows traces every material limitation and unknown to
  bounded evidence, with no claim of full official-product parity derived
  from a plugin name or prompt. Leave review-dependent conclusions incomplete
  until the user confirms the prepared decision-bearing classifications.
- **Maintained research source:** regenerate or validate the retained
  research package against its manifest and stable claim IDs, follow sample
  row-to-evidence-to-owner links, and confirm the research baseline/evidence
  index route to the reviewed outputs. No public website change is needed to
  satisfy this requirement.

### Additional implementation verification

- Run the packaging analyzer/config-resolution checks with isolated
  environment inputs; review warning types without persisting secret values.
- Run only focused existing tests for rows whose status or limitation needs
  current execution evidence. Treat gated hosted-provider tests as not run
  until their conditions and cost are explicitly authorized.
- Validate CSV/JSONL parsing, evidence-ID referential integrity, source
  paths, documentation links, and `git diff --check`. Verify that no new
  research output exposes credentials or full private transcripts.

## Implementation Notes

- Approved execution started on 2026-09-29 with an explicit checkpoint: two
  or three trial turns in each of three distinct investigator sessions,
  followed by a report and pause before expanding delegated work.
- Created `landing_page/research/020-current-product-and-compatibility-baseline/input-manifest.json`
  for the pinned source checkout and checked-in default config. An initial
  packaging-analysis call inherited `CONFIG_DIR` from the live personal
  runtime and incorrectly reported missing personal instruction files.
  Repeating the same read-only analysis with `CONFIG_DIR` set to the
  checked-in default-config directory, `BUILTIN_PLUGINS` to this checkout,
  and `WORKING_DIR` to this worktree removed those path errors. The resolved
  config has 20 agents, seven provider routes, 28 global plugin specs,
  and 37 selected local plugin projects. Remaining warning type:
  `env_missing`; credential values were not retained.
- The prior uncommitted runtime-layout fix and tests predate this execution.
  The checked-in default config is unchanged. Treat the copied personal
  config used to run investigators as tooling, not evidence of product
  defaults.
- **Trial checkpoint (2026-09-29):** Three distinct ordinary persisted
  `codex-openai` sessions each completed two read-only turns using
  `gpt-6-sol`, high reasoning effort, and a request-scoped *attempt* to
  disable the delegation access section. They shared one
  runtime (6.80 s startup) and ran concurrently. All six turns succeeded,
  each with four completed shell calls and five provider responses. Per-turn
  elapsed time was 49.22–61.12 s; total concurrent wall time including
  startup was 121.82 s.

  | Trial topic | Session ID | Turn times (s) | ChatGPT API-equivalent estimated USD |
  |---|---|---:|---:|
  | Configured-agent compatibility | `5bbe6ea8-9ae9-4bce-8dea-da5d6f23f0a1` | 61.12, 52.37 | 0.1946172 |
  | Provider/account routes | `8959ffa0-b4d3-4c39-85eb-df20cd3258b6` | 59.90, 49.22 | 0.1661458 |
  | Application/client features | `db521fc8-4771-4fb8-ad05-a0bd718c4cdf` | 59.28, 55.68 | 0.1495134 |

  Total API-equivalent estimate: **$0.5102764**, read from the
  `openai-responses-chatgpt` cost-store rows for these three session IDs.
  `actual_cost` was absent; this estimate is not an invoice or a claim of
  incremental subscription charges. The 30 provider responses reported
  897,262 input and 8,012 output tokens in aggregate. Returning to the
  same session increased prompt-history size. The initial compiled messages
  printed by the system-message feature contained access guidance despite
  the per-request `include_crystal_lattice_access: false` override. Do not
  count that override as successful prompt reduction; inspect the actual
  child prompt or use a copied config with the setting disabled *before*
  session creation when this matters.
- **Quality and usefulness:** The six concise reports supplied source/config
  citations and separated unrun checks from verified behavior. Spot checks
  against the cited files support:
  `plugins/codex-tools` auto-selects shell behavior for the checked-in
  `gpt-5.4-mini` profile, while its skills mixin is enabled; `plugins/gemini-tools`
  is a separate tool surface from the OpenRouter model route, and its
  configured Gemini-API web search requires a key; `plugins/openai_responses`
  distinguishes ChatGPT login from API-key auth and labels ChatGPT cost as
  estimated; `plugins/openrouter` uses its own key and model discovery;
  `plugins/session-main-search-app` filters session summaries rather than
  searching all messages; `plugins/session-archive-app` declares archive
  actions and a default-false archive filter, and the frontend SDK provides
  a generic action invocation path. This is useful seed evidence for the
  three catalogs; it does not establish distributed packaging, live behavior
  for those profiles, or native mobile/desktop presentation. None of these
  trial claims has been promoted into accepted catalog rows.
- **Trial-specific gap:** All 24 tool calls from the trial investigators
  selected the array-form `shell`. Inspection of
  `plugins/codex-tools/src/codex_tools/model_family.py` shows
  `gpt-6-sol` fails the `shell_command` auto-selection pattern, while the
  checked-in `gpt-5.4-mini` matches. The direct model-family check returned
  `False` and `True`, respectively. This needs a separate compatibility
  decision; it was not changed during the checkpoint.
- **User-approved side todo for continuation:** Correct auto-selection for
  GPT-5.6 and GPT-6 variants before the broader compatibility audit. The
  current selector already recognizes plain `gpt-5.6`, `gpt-6`, and later
  numeric versions; it misses named variants. The checked-in default config
  has instruction variants for `gpt-5.6-sol`, `gpt-5.6-terra`,
  `gpt-5.6-luna`, `gpt-6-sol`, `gpt-6-luna`, and `gpt-6-astra`, with optional
  `openai/` prefixes. Implement and test the owned Codex tool behavior when
  execution resumes; preserve the source revision and changed-file fingerprint
  for pre- and post-fix claims. This code correction is a side fix, not a new
  product-website requirement or evidence of full official Codex parity.
- **Prompt and model choices for continuation:** The trial instruction
  expressly prohibited tests and writes, capped each turn at four read-only
  tool calls and 280 words, and returned assistant text to ignored scratch.
  Its outputs were useful source leads but could not prove behavior. This
  guidance was superseded by the GPT-5.6 calibration below. Permit focused
  local verification and distinct ignored draft findings when warranted;
  require recorded command/result and reviewed evidence before catalog
  promotion.
- **GPT-5.6 calibration (2026-09-29):** The user replaced the earlier GPT-6
  preference with GPT-5.6-only delegation. A copied private config appended
  a task-specific evidence-auditor section to the ordinary Codex system
  template and defined Sol, Terra, and Luna agents at `high` and `xhigh`.
  Every worker received the same cross-layer Codex/OpenAI assignment, could
  run focused local tests, and had to write four canonical evidence files to
  its own ignored directory. The six evaluated sessions plus one abandoned
  Terra-xhigh orchestration session cost an API-equivalent estimated
  **$14.49803498**, below the approved $30 ceiling; actual subscription
  billing remains unknown.

  | Model / effort | Result | Time | Tools | Estimated USD | Packet |
  |---|---|---:|---:|---:|---|
  | `gpt-5.6-terra` / `high` | succeeded | 11m 11s | 50 | 1.2511152 | 14 valid claims, 42 report citations, complete |
  | `gpt-5.6-luna` / `high` | succeeded | 15m 33s | 73 | 0.18809726 | 16 valid claims, 45 report citations, complete |
  | `gpt-5.6-sol` / `high` | timed out | 30m 08s | 108 | 6.0128792 | no packet |
  | `gpt-5.6-terra` / `xhigh` | succeeded | 28m 11s | 66 | 2.069895 | 17 valid claims, 88 report citations, complete |
  | `gpt-5.6-luna` / `xhigh` | timed out | 30m 07s | 59 | 0.10848012 | no packet |
  | `gpt-5.6-sol` / `xhigh` | timed out | 30m 06s | 98 | 4.7465172 | partial `report.md` only |

  A terminated early Terra-xhigh orchestration session added $0.121051 and
  is not a model-quality result. Terra-high provided the best balance of
  convergence, evidence quality, and elapsed time. Luna-high was a strong,
  inexpensive, test-heavy alternative, but took longer and more tool calls.
  Terra-xhigh produced the deepest packet and found additional contradictions
  and client boundaries, but nearly reached the timeout. Both Sol settings
  over-investigated without producing a complete packet; Luna-xhigh also
  failed to converge. Future workers should write their claim map and files
  incrementally, use smaller package batches than the calibration slice, and
  treat timeouts/partial packets as failures even when the intermediate
  research is useful.
- **Named-model shell side fix:** Expanded Codex shell-command family
  matching to the configured GPT-5.6 Sol/Terra/Luna and GPT-6
  Sol/Luna/Astra variants while preserving array `shell` for `gpt-5` and
  `gpt-5-mini`. Updated owning docs and direct tool-selection tests.
  `pytest plugins/codex-tools/tests/test_shell_tool_selection.py -q`
  passed 46 tests. The existing application-loader selection file remained
  too slow in this environment and is still recorded as incomplete, not
  passing.
- **Broader-audit estimate (2026-09-29):** Planned eight fresh,
  package-bounded high-effort sessions in three review-gated waves: five
  Terra and three Luna. Reuse the Codex/OpenAI calibration evidence; add at
  most one narrow Terra/xhigh contradiction pass. Expected additional
  API-equivalent cost: **$8–$12**. Stop ceiling: **$18**. The completed
  calibration's $14.49803498 is sunk evidence-generation cost and is not
  included in the additional estimate; expected combined calibration plus
  broader audit is about **$22.50–$26.50**, with an absolute combined ceiling
  of about **$32.50** if the full broader-audit reserve is consumed.
  Hosted-provider verification is excluded.
- **Catalog extraction foundation (2026-09-29):** Added
  `catalog-schema.json` and `extract_baseline.py`. Semantic row IDs use
  `agent:<id>`, `provider:<id>`, and `feature:<plugin-id>`. The extractor pins
  the checked-in config environment, resolves mixins, analyzes packaging,
  preserves human review fields on refresh, and validates generated columns
  with `--check`. Initial outputs contain 20 configured-agent rows, seven
  provider/account rows, and 28 global-feature rows. The first attempted run
  failed closed because an inherited personal `CONFIG_DIR` redirected file
  placeholders; explicit pinning corrected the environment before any CSV was
  written. The generated catalogs and manifest now pass the extractor check
  and JSON validation.
- **Broader audit wave 1 (2026-09-29):** Three Terra/high sessions completed
  in 13 minutes wall time for an API-equivalent estimate of **$2.9902856**:
  Claude/Anthropic (`15b5b52a-60b5-4732-9190-9cdea6be7fdb`,
  $1.2504302), Qwen/Gemini/Grok/Kimi/GLM through OpenRouter
  (`b5eb8d84-184c-4bfe-9489-dbbde3778c98`, $1.0451172), and
  Ollama/Fireworks/Z.ai reference-compatible routes
  (`e44698f6-377f-4e72-93f3-b5e3726543a9`, $0.6947382). All wrote complete
  packets and claim maps before eight minutes; the reference run finished
  before the monitor recorded the checkpoint, so its stored `pending` label
  is a runner bookkeeping defect and is reviewed as
  `completed_before_checkpoint`.

  Independent verification reproduced 121 reference-provider tests, 80
  focused OpenRouter capability/tool/reasoning/usage/web-search tests, 94
  broader OpenRouter provider tests, 84 Claude-tools tests, and 58 Anthropic
  provider/transport/cache/reasoning/tool/usage tests after installing the
  owning package's declared development dependencies in the worktree venv. The
  default-config Claude prompt suite remains incomplete: 4 tests passed and
  3 failed while dynamic plugin imports reported a missing compiled
  `pydantic_core` module in the generated plugin cache. These are retained as
  verification/environment gaps, not product passes. Wave-1 claims are
  accepted only as proposed source/config/local-test evidence; real-provider,
  per-profile effective-tool, produced-artifact, and native-client states
  remain unknown or conditional.
- **Broader audit wave 2 (2026-09-29):** Three sessions completed in 13.5
  minutes wall time for an API-equivalent estimate of **$1.71422046**:
  specialist image/cloud/distribution behavior
  (`54f5f21b-1141-49f3-baa5-4cceae47c6a0`, Terra/high, $1.3537684),
  message/history/compaction/export/background behavior
  (`6ee3e665-2e60-4c9d-8f67-79e288f13b67`, Luna/high, $0.18058832), and
  session-list organization
  (`de853df1-06c4-4909-9ed0-bb6565f56a47`, Luna/high, $0.17986374). All
  checkpoints passed and all packets were complete.

  Independent verification reproduced 5 public session-list HTTP tests
  (6 integration-marked cases deselected), 33 core list/filter/application
  plugin tests, 61 snapshot/asset/projection/notification tests, 88 frontend
  SDK tests plus 6 React-binding tests, 9 image-provider/attachment tests,
  12 focused cloud-plugin tests, and 12 cloud bundle/source staging tests.
  Retain the plugin-suite contradictions reported by workers: session-list
  combined tests had four current failures and one deselection; export tests
  were initially uncollectable because the optional package's declared
  `xhtml2pdf` dependency was not installed; and one broad effective-config
  test failed before reaching its specialist assertions. Generic application
  snapshots/projections are not attributed to the asset plugin, source/builder
  selection is not artifact proof, and generic mobile/desktop action consumers
  do not establish terminal parity or native-device completion.
- **Broader audit wave 3 (2026-09-30):** Two sessions completed in 17.2
  minutes wall time for an API-equivalent estimate of **$1.47747262**:
  configuration/auth/MCP/context/transparency
  (`1474d08d-e9f4-4e86-84f2-d9da74ae64ec`, Terra/high, $1.2181784) and the
  production client matrix
  (`d0b442bd-8954-49c6-bade-e6d78bc36669`, Luna/high, $0.25929422). Both
  checkpoints passed and packets were complete. The client run crossed a real
  local FastAPI process, HTTP transport, and production `RestAgentBackend`
  through 21 backend integration tests, plus status and action-display
  integrations. An independent fresh-cache rerun passed 19 and had two
  backend-startup timeouts while installing path plugins; an immediate
  warm-cache retry passed all 21. Treat this boundary as passing but
  startup-sensitive. The packet also recorded 24 React-binding tests, 76 shared RN
  component tests, 10 selected mobile tests, 195 desktop tests, and focused
  CLI/HTTP action tests. Native mobile/macOS suites were present but not run.

  The review preserves a layered client boundary: public HTTP/SDK support is
  strongest; mobile/desktop have production generic consumers with native UI
  verification pending; terminal console supports sessions, settings,
  plugins, history, streaming event rendering, cancellation, reasoning, and
  tools, but generic application/session action execution remains unknown;
  standalone CLI/Python provides synchronous persisted runs and projections,
  not an interactive terminal or general action surface. The transparency
  packet independently confirms duration tracking is optional-not-default,
  MCP is selected but disabled by common defaults, compiled-message
  inspection is non-mutating, and cost meanings are provider-specific rather
  than invoice-equivalent.

  Installing `message-export-actions` with its declared dependencies resolved
  the initial missing-`xhtml2pdf` import, but the full suite and a reduced
  non-browser subset both exceeded bounded timeouts. Export remains
  source-present/optional-not-default with incomplete local verification.
  Cumulative broader-audit cost after wave 3 is **$6.18197868**.
- **Contradiction challenge (2026-09-30):** One Terra/xhigh session
  (`f5224148-a8fa-4f0e-8c49-62f888b90897`) completed in 20.3 minutes with
  79 tool calls for an API-equivalent estimate of **$2.306117**. It resolved
  the terminal boundary as no generic interactive action executor; confirmed
  the five-profile Codex `update_plan` prompt/tool mismatch; confirmed Grok
  bash/status-schema/historical-agent-delete drift; and narrowed the
  generated-cache `pydantic_core` symptom to an unresolved loading boundary.
  Fresh offline full-default probes stopped earlier on unavailable local build
  prerequisites, so neither stale-cache contamination nor a clean-start
  product defect is proven.

  Total broader-audit model cost is **$8.48809568**, within the expected
  $8–$12 range and below the $18 ceiling. Calibration plus broader audit cost
  is **$22.98613066** API-equivalent. All nine broader-audit packets were
  complete and all practical claim-map checkpoints passed.
- **Human-review package (2026-09-30):** The retained package now has 20
  configured-agent rows, seven provider/account rows, 33 feature rows, and 24
  stable claim-evidence records. At that checkpoint every classification was
  `needs_review`.
  `catalog-review-overrides.json` is the reproducible human-classification
  source, while `extract_baseline.py` refreshes config-owned fields and
  validates headers, generated fields, override row IDs, claim IDs, required
  evidence fields, row references, and evidence-ID resolution.
  `verification-summary.md` records the proposed conclusions, contradictions,
  test outcomes, cost, and nine decisions requiring user confirmation.
- **Three-matrix restructuring (2026-10-01):** Reframed the authoritative
  review output around product concepts rather than task numbering:
  `feature-catalog`, `provider-support-matrix`, and
  `model-family-feature-matrix`, with JSON and long-form CSV for each plus
  `compatibility-matrices.md`. The feature catalog exhaustively covers 66
  plugin projects, including default selections, optional plugins,
  distribution-specific packages, examples, fixtures, templates, and support
  libraries. The provider matrix expands 10 routes across 19 native/provider
  features and includes explicit `planned` cells only where maintained
  requirements own future work. The model-family matrix expands 12 profile
  groups across 21 tool, web, media, MCP, skills, compaction, provider-native,
  planning, and subagent features. Generated product-facing filenames,
  headings, IDs, and content contain no numeric task identifier.
- **Decision approval and website projection (2026-10-01):** The user approved
  all nine decision-bearing classifications. Updated all 20 configured-agent,
  7 provider/account, 33 application-feature, and 24 claim-evidence review
  states to `accepted`. Added a separate canonical website selection and
  deterministic transformation. The proposed public projection contains 9
  non-overlapping application/session features, 9 provider rows with 6
  user-relevant native-capability columns, and 71 package-specific current or
  planned tool rows across Codex-, Claude-, Gemini-, Qwen-, Grok-, and
  Kimi-oriented bundles. Implemented tool rows validate against package
  descriptors; planned rows validate against maintained task files. Internal
  task paths and numeric task identifiers are stripped from public output.
- **Accepted draft and closure (2026-10-02):** The user accepted the canonical
  website projection as a draft that downstream website work may refine.
  Exhaustive matrices, normalized catalogs, claim evidence, and the website
  projection now carry accepted review state; the projection separately
  records `maturity: draft`. The durable finding, shared baseline, evidence
  index, content-requirement evidence, parent status, and completion manifest
  were finalized. The six calibration answers and broader runner diagnostics
  remain disposable under the ignored task-artifacts directory; retained
  manifests preserve session IDs, timings, cost estimates, and verification
  boundaries.

## Completion Notes

- **Outcome:** Delivered and accepted an evidence-backed current product and
  compatibility baseline at source revision
  `add5f5e71de3bb1676851bb840dfd77620f63ddb`. The retained package includes
  exhaustive feature/provider/model-family matrices, normalized supporting
  catalogs, stable claim evidence, deterministic generators, a human-readable
  verification summary, and an accepted-draft website projection.
- **Requirement evidence:** The accepted outputs separately represent
  application/session features, provider-native support, and model-family
  tool bundles; preserve source, packaging, default, client, automated-test,
  hosted-verification, limitation, confidence, and review boundaries; and
  explicitly exclude official upstream product/account/session parity.
- **Human review:** The user approved all nine decision-bearing
  classifications on October 1, 2026 and accepted the compact website
  projection as a downstream draft on October 2, 2026. All 20
  configured-agent rows, 7 provider/account rows, 33 application-feature
  rows, 24 claim records, and exhaustive matrix entities are accepted.
- **Website boundary:** No public website content was changed or deployed.
  The downstream website task may refine the accepted draft's selection,
  wording, grouping, and presentation while preserving accepted identity,
  status, limitation, and source-traceability boundaries.
- **Verification:** The catalog extractor, exhaustive matrix generator, and
  website projection generator all pass deterministic `--check` validation.
  Current website tool rows resolve to package descriptors; planned rows
  resolve to maintained task files; selected provider cells are consistent
  with the exhaustive provider matrix; generated public data contains no
  internal task paths or numeric task identifiers. Focused Codex shell/model
  selection coverage also passes for the added GPT-5.6 and GPT-6 variants.
- **Plan deviations:** The original three normalized CSVs were retained as
  supporting evidence, while the user-approved authoritative shape expanded
  to three product-oriented JSON/CSV matrices and a smaller canonical website
  projection. A bounded Codex shell-selection correction was completed as an
  approved side item.
- **Remaining limits:** No current hosted-provider/account entitlement was
  established for every route; native mobile/macOS suites and produced
  bundled/optimized/cloud artifacts were not run; complete clean-default
  runtime loading remains unresolved; message-export verification remained
  timeout-incomplete; and cost values remain provider-reported or local
  estimates rather than invoice truth.
