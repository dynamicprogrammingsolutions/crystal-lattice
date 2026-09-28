# GPT-6-Astra model update

Import the GPT-6-Astra Codex developer messages, update the drifted
previous-model instructions, and refresh the companion model catalog and
pricing snapshots. Follows the protocol documented in
`application/python/docs/development/agent-creation.md`.

Worktree: `task/20260914-gpt-6-astra-support`
(`/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260914-gpt-6-astra-support`).

## Requirements checklist

- [x] gpt-6-astra developer messages exist as date-versioned assets under
  `default_config/codex/gpt-6-astra/` (introduction date `20260904`) with
  reference copies, and the `codex_developer_messages` row selects them for
  `gpt-6-astra` and `openai/gpt-6-astra` with every personality resolving to
  the same template; no pre-existing model instruction asset is modified.
- [x] New date-versioned instruction files exist for the drifted upstream
  versions — GPT-5.6 family (`20260718`), `gpt-5.5` (`20260911`), `gpt-5.4`
  (`20260911`) — with the `codex_developer_messages` rows repointed to them
  and all previous version files retained unmodified.
- [x] The checked-in Codex models snapshot reflects the current upstream
  catalog: `gpt-6-astra` and both daybreak models present; `gpt-5.2` and
  `gpt-5.4-mini` absent.
- [x] The checked-in pricing snapshot contains a `gpt-6-astra` entry and the
  changed GPT-5.6 prices, the service tier is named `fast` throughout the
  plugin and snapshot (obsolete `priority` keys removed), and Fast-mode cost
  estimation resolves current prices for the `fast` tier.
- [x] `gpt-6-astra` is offered its real reasoning-effort set
  (`low`, `medium`, `high`, `xhigh`, `max`, `ultra`).
- [x] `default_config/codex/README.md` records the new import commits, dates,
  and family notes, and `docs/reference/default-config.md` is regenerated from
  the changed config.
- [x] Model selection and end-to-end instruction delivery for the new and
  updated models are covered by automated tests: unit selection tests
  (model regex, `openai/` prefix, personality fallback, content distinctions,
  older-model regressions), a real-API test, and a ChatGPT saved-login test
  proving the compiled gpt-6-astra instructions reach top-level instructions.

## Open requirement questions and decisions

Resolved at plan approval (2026-09-14):

1. **gpt-5.5 / gpt-5.4 personality-row mapping.** Approved: repoint only
   the `default` rows to the new dated files (upstream's new default *is*
   friendly-embedded), keep the existing `friendly`/`pragmatic` rows pointing
   at the retained old files, and document the change in the README.
2. **Pricing tier naming.** Approved with change: rename the tier
   `priority` → `fast` everywhere, including the plugin code — the pricing
   snapshot keys the tier as `fast` with the current page prices, obsolete
   `priority` keys are removed from the snapshot, and cost estimation
   resolves `fast`. Also retest Fast mode against the ChatGPT endpoint:
   `test_openai_responses_chatgpt_saved_login_priority_tier_pricing` is
   marked xfail because the backend did not report `tier: priority` when
   last tested; update it and rerun it.
   **Refined after the live retest (user-approved Option A):** the official
   API accepts `fast` but still reports `priority` in responses, and the
   ChatGPT backend rejects `fast` with
   `400: Unsupported service_tier: fast` while accepting `priority`. The
   Fast mode extension therefore sends the wire value the target endpoint
   accepts: `fast` for API-key auth and `priority` for ChatGPT auth. The
   pricing lookup normalizes the reported `priority` → the snapshot's
   `fast` prices. The ChatGPT backend reports `service_tier: "default"`
   for the test account (the fast tier is not applied), so the saved-login
   tier test still xfails — now with the verified, accurate reason.
3. **Pro reasoning mode and reasoning context for gpt-6-astra.** Approved:
   gate gpt-6-astra the same way as gpt-5.6-sol (offering Pro mode and
   reasoning context).
4. **Daybreak models.** Approved: include them via the catalog refresh only;
   no instruction assets, no config rows.
5. **Manual ChatGPT fallback entry.** Approved: remove the stale `gpt-5.5`
   entry from `openai_chatgpt_manual_models.json`.

## Supporting details

### Upstream state (investigated 2026-09-14)

- Latest inspected `openai/codex` commit:
  `5b1d6560181680f95cde95c14ed042acc02248ed` (2026-09-14), file
  `codex-rs/models-manager/models.json`.
- Upstream catalog restructuring since the 2026-07-13 import (commit
  `2f7d89b1419bf7064346855b0acde23514b1ebc5`):
  - `base_instructions` removed from every model
    (`8e694e955ae02ca737230a5468c55d5847074072`, 2026-09-07);
  - `instructions_variables` is now an empty object for every model;
  - `gpt-5.4-mini` and `gpt-5.2` retired from the catalog
    (`eb7bd64ef935cedb6a2c90c77c78d6677f1efb45`, 2026-09-09);
  - new hidden models `gpt-daybreak-blue-latest` and
    `gpt-daybreak-red-latest` (cybersecurity variants);
  - new `model_messages` fields (Codex-CLI-internal, provenance only):
    `persistent_instructions`, `approvals`, `collaboration_modes`,
    `auto_review`, `multi_agent`, `token_budget`, `guardian_v2`,
    `confirmation_policies`.

### gpt-6-astra model entry

- `display_name`: `GPT-6-Astra`; description: "Our most capable model for
  complex, demanding work."; `supported_in_api: true`; `visibility: list`;
  `minimal_client_version: 0.153.0`.
- `context_window` 272000, `max_context_window` 872000
  (`supports_experimental_context: true`).
- `default_reasoning_level: low`; supported efforts `low`, `medium`, `high`,
  `xhigh`, `max`, `ultra` (identical set to `gpt-5.6-sol`).
- `service_tiers`: `priority` (display name "Fast"); `shell_type:
  unified_exec`; `tool_mode: code_mode_only`; `apply_patch_tool_type:
  freeform`; `input_modalities`: text, image; `use_responses_lite: true`.

### gpt-6-astra instruction assets

- `model_messages.instructions_template`: 21261 chars, sha256
  `152dfaeeb552876190962be1c12c93d426840ff12691f648261554a7675a6698`.
  Introduced `2026-09-04`
  (`83b62a02fab5c0fc797cbc9896c332148f1fd9d0`, "Make GPT-6-Astra user input
  guidance conditional (#42836)"); first catalog appearance
  `2026-09-03` (`ed391d4dd21396715b66c278e6b451897672c93c`, #42607).
- No `base_instructions`; `instructions_variables` is `{}`.
- New `model_messages.persistent_instructions`: 5737 chars, sha256
  `30747e79e50efb64f91cfff3d5ef1882e347081e81448918d5f7d5358e98c523`
  (Codex CLI persistent mode; provenance copy only, not wired into config).
- Placeholder `{{connector_id}}` appears once in the `# Apps (Connectors)`
  section. Upstream renders it literally (escaped braces in
  `codex-rs/core/src/context/apps_instructions.rs`); it documents the
  `[$app-name](app://{{connector_id}})` user-message syntax and is kept
  verbatim.
- Distinctive opening: `"You are Codex, an agent based on GPT-6"` (GPT-5.6
  templates open with `"based on GPT-5"`).
- New sections vs GPT-5.6: `# When to ask the user for permission`,
  `# Autonomy and persistence` (promoted, expanded), `# Apps (Connectors)`,
  `# Plugins`. Removed: `## File editing constraints`,
  `# Destructive Actions`.

### Previous-model instruction drift

Current upstream templates and their introduction dates (found by walking
`git log` on `models.json` and comparing template sha256 per commit):

| Model | Current template | Introduced | Checked-in asset |
|---|---|---|---|
| gpt-5.6-sol | 17730 chars, `cbefa6b0bede0e332d957fca70ccacf9f12f4c0ecdf81b819e5cbe1a3b16e265` | 2026-07-18 (`d26a9bf671b1c03aabfc32e1092d137c1feb3962`, #33961) | 16299 chars, `e9778714d505f3dd...` |
| gpt-5.6-terra | same as sol | same | 16270 chars, `78a2fc84e1bffa42...` |
| gpt-5.6-luna | same as sol | same | 16270 chars, `78a2fc84e1bffa42...` |
| gpt-5.5 | 21459 chars, `2351631dfc5644dc5a45eaaca4139475bd02810ee6cb792d058b551559b3242e` | 2026-09-11 (`c18277043e52ff4a81fdf2f039ddef85e3a6fd3e`, #44930 "Embed friendly instructions") | byte-identical to checked-in `gpt-5.5/base_instructions.md` |
| gpt-5.4 | 15296 chars, `f8c4032f78fdb19b46f468239c5dc757f745fbb10520e64e1e4afbf747e52fb8` | 2026-09-11 (same commit) | friendly-embedded plus updated file-reference rules |

- All three GPT-5.6 models now share one template; Sol's distinct variant is
  gone upstream.
- The gpt-5.5/gpt-5.4 templates embed the friendly personality directly
  (with a `# Personality` section); the `{{ personality }}` placeholder and
  variables are gone. For gpt-5.5 the new template equals the old
  `base_instructions.md`; it differs from the old `instructions_friendly.md`
  by one blank line.
- Models absent from the current catalog (`gpt-5.4-mini`, `gpt-5.2`,
  `gpt-5.3-codex` and older) cannot be refreshed from upstream and stay
  unchanged.

### Catalog and pricing drift

- Checked-in Codex snapshot: fetched 2026-07-17, commit
  `50b82133850d940627cf307d77e280619bfafe25`, 8 models. The refresh
  (`plugins/openai_responses/benchmark/refresh_openai_responses_models.py`)
  replaces snapshot content, so retired models drop out automatically.
- Reasoning gating in
  `openai_responses_reasoning_extension.py` uses hardcoded per-family
  patterns; `gpt-6-astra` is not covered and would fall to the unknown-model
  effort set. Pro mode and reasoning context are gated on the GPT-5.6 effort
  tuples (`_GPT_5_6_REASONING_EFFORTS`).
- Current pricing page (fetched 2026-09-14) publishes tiers `standard`,
  `batch`, `flex`, `fast` only — the tier previously named `priority` is now
  labeled `fast` on the page for every model.
- GPT-5.6 price changes (standard tier, per 1M tokens):

| Model | Checked-in | Current page |
|---|---|---|
| gpt-5.6-sol | 5.0 / 30.0 (cached 0.5) | 4.0 / 20.0 (cached 0.4, cache-write 5.0) |
| gpt-5.6-terra | 2.5 / 15.0 (cached 0.25) | 2.0 / 12.0 (cached 0.2, cache-write 2.5) |
| gpt-5.6-luna | 1.0 / 6.0 (cached 0.1) | 0.2 / 1.2 (cached 0.02, cache-write 0.25) |

- gpt-6-astra pricing (per 1M tokens): standard 10.0 / 50.0 (cached 1.0,
  cache-write 12.5); batch 5.0 / 25.0; flex 5.0 / 25.0; fast 20.0 / 100.0.
- `merge_pricing_entry` keeps existing tier keys, so a naive refresh leaves
  stale `priority` prices beside the new `fast` prices; Fast-mode estimation
  looks up the wire-level `priority` and would resolve the stale prices.

### Current repo state

- GPT-5.6 instruction assets and config rows: from task
  `20260713-openai-responses-gpt-5-6-support/060` (commit `2f7d89b` import).
- Existing tests that step 2 must update (they assert the old templates):
  `application/python/tests/test_default_config_codex_gpt56_instruction_selection.py`
  (asserts Sol-specific paragraph position and the `e9778714`/`78a2fc84`
  hashes), the gpt56 real-API test, and the gpt56 ChatGPT manual-integration
  test.
- The date-versioned protocol and maintenance workflow are documented in
  `application/python/docs/development/agent-creation.md` (added on this
  branch).

## Execution plan

Status: Approved

Extraction source: local `openai/codex` clone at
`/Users/ferenci84/Dev/Mine/codex` (fetched to `origin/main`
`5b1d656018` on 2026-09-14). Re-verify the recorded template hashes at the
start of execution; if upstream moved, re-derive the introduction dates
before importing.

### Step 1 — Import gpt-6-astra instructions (previous assets untouched)

1. Extract the gpt-6-astra entry from
   `codex-rs/models-manager/models.json` at the inspected commit.
2. Create `default_config/codex/gpt-6-astra/` with date-versioned files
   (introduction date `20260904`):
   - `instructions_default.20260904.md` — effective developer message
     (identical to the template; `{{connector_id}}` kept verbatim);
   - `model_messages.instructions_template.20260904.md` — raw template;
   - `model_messages.instructions_variables.20260904.json` — empty object;
   - `model_messages.persistent_instructions.20260904.md` — provenance copy.
3. Copy the same files to
   `default_config/system_messages/reference/default-system-instructions/codex/gpt-6-astra/`.
4. Add the config row at the top of `codex_developer_messages`:
   `{"model_regex": "^(openai/)?gpt-6-astra$", "text":
   "${file:${env:CONFIG_DIR}/codex/gpt-6-astra/instructions_default.20260904.md}"}`
   — no `personality` field (fallback covers all personalities). No bare
   `gpt-6` alias row.
5. Do not modify any other model's instruction assets in this step.

### Step 2 — Update previous agent instructions

1. GPT-5.6 family: add `instructions_default.20260718.md` (and the raw
   template file) to each of `gpt-5.6-sol/`, `gpt-5.6-terra/`,
   `gpt-5.6-luna/` (byte-identical shared template); repoint the three
   config rows; keep the existing unversioned files in place.
2. `gpt-5.5`: add `instructions_default.20260911.md` and the raw template;
   repoint the `default` row; keep `friendly`/`pragmatic` rows and files
   (decision 1).
3. `gpt-5.4`: add `instructions_default.20260911.md` and the raw template;
   repoint the `default` row; keep `friendly`/`pragmatic` rows and files
   (decision 1).
4. Leave models absent from the current catalog unchanged.
5. Update the gpt56 selection unit tests, real-API test, and ChatGPT
   manual-integration test to assert the new dated files (and that Sol's
   distinct old paragraph is gone — all three family members now share one
   template).

### Companion maintenance

1. Catalog: run
   `python plugins/openai_responses/benchmark/refresh_openai_responses_models.py`;
   verify gpt-6-astra and both daybreak models are present and
   `gpt-5.2`/`gpt-5.4-mini` are absent; update the snapshot note in
   `plugins/openai_responses/docs/development/model-discovery.md`.
2. Pricing: run
   `python plugins/openai_responses/benchmark/refresh_openai_responses_pricing.py`;
   apply decision 2 — rename the tier `priority` → `fast` in the Fast mode
   extension (it sends `service_tier: "fast"`), keep the snapshot's tier keys
   as `fast` with the current page prices, drop obsolete `priority` keys, and
   update the fast-mode/pricing tests. Verify the gpt-6-astra entry and the
   new GPT-5.6 prices; update the ChatGPT saved-login tier test to expect
   `fast` and rerun it (decision 2).
3. Reasoning: add a `gpt-6-astra` pattern to
   `_MODEL_REASONING_EFFORT_PATTERNS` with
   `("low", "medium", "high", "xhigh", "max", "ultra")`; apply decision 3 for
   Pro mode / reasoning context gating; extend reasoning unit tests.
4. Remove the stale `gpt-5.5` manual ChatGPT fallback entry (decision 5).
5. Docs: update `default_config/codex/README.md` (import commits, dates,
  family notes, upstream restructuring); regenerate
  `docs/reference/default-config.md` from the changed `config.json`.

### Implementation decisions and open questions

Resolved local decisions (reversible, no user-visible impact):

- `{{connector_id}}` stays verbatim (upstream renders it literally).
- `persistent_instructions` is imported as a dated provenance copy only.
- No bare `gpt-6` alias row (consistent with the task 010 decision that the
  bare `gpt-5.6` alias is not mapped).
- Date-versioned file naming: `<asset-name>.YYYYMMDD.<ext>` inside the
  existing per-model directory.

Decisions 1–5 above were resolved at plan approval; decision 2 was
approved with the `fast`-everywhere rename instead of a `fast`→`priority`
refresh mapping.

### Documentation

- `application/python/docs/development/agent-creation.md` — protocol page;
  already on this branch; update only if execution reveals inaccuracies.
- `application/python/agent_terminal_app/default_config/codex/README.md` —
  import provenance and family notes (developer audience).
- `docs/reference/default-config.md` — regenerated snapshot.
- `plugins/openai_responses/docs/development/model-discovery.md` — snapshot
  contents note.
- `plugins/openai_responses/README.md` — reasoning-effort list if it names
  per-model sets.

### Task checklist

- [x] Re-verify upstream hashes and introduction dates at execution start
- [x] Step 1: gpt-6-astra dated assets + reference copies + config row
- [x] Step 2: GPT-5.6 family dated files + repointed rows
- [x] Step 2: gpt-5.5 and gpt-5.4 dated files + repointed default rows
- [x] Companion: catalog snapshot refresh + docs note
- [x] Companion: pricing snapshot refresh + `priority`→`fast` tier rename
- [x] Companion: reasoning pattern (+ Pro mode/context gating per decision 3)
- [x] Companion: manual ChatGPT fallback cleanup (decision 5)
- [x] Companion: ChatGPT saved-login Fast-mode tier retest (decision 2,
      Option A refinement applied)
- [x] Tests: gpt-6-astra unit selection tests
- [x] Tests: updated-model selection tests (gpt56 suite updated)
- [x] Tests: real-API instruction delivery test
- [x] Tests: ChatGPT saved-login instruction delivery test
- [x] Tests: pricing + catalog + reasoning unit tests updated
- [x] Docs: codex README + regenerated default-config reference
- [x] Verification: full default test suites + lint/typecheck

### Requirement verification

| Requirement | Acceptance evidence |
|---|---|
| gpt-6-astra dated assets + selection | Unit test selecting dated file for `gpt-6-astra` and `openai/gpt-6-astra` across personalities; asset hash assertions |
| Previous-model updates | Unit tests asserting the new dated files are selected for gpt-5.6 family, gpt-5.5, gpt-5.4; old files still present |
| Catalog snapshot | Snapshot JSON contains gpt-6-astra + daybreak, lacks retired models; openai_responses catalog tests pass |
| Pricing snapshot | Pricing tests pass with new 5.6 prices and gpt-6-astra entry; Fast-mode estimation resolves current fast-tier prices for both the `fast` and reported-`priority` names; ChatGPT saved-login tier test runs live, sends the accepted `priority` wire name, and xfails with the verified reason (backend reports `default`) |
| Reasoning efforts | Reasoning extension unit test offers the full effort set for gpt-6-astra |
| Docs | README provenance section; regenerated default-config reference matches config.json |
| End-to-end delivery | Real-API test asserts compiled gpt-6-astra instructions in the request; ChatGPT manual-integration test asserts recorded `instructions` |

### Additional implementation verification

- `pytest application/python/tests -q` (default suite)
- `pytest plugins/openai_responses/tests -q` (default suite)
- `pytest application/python/tests -m 'integration and api and not slow_integration' -q`
  (hosted API, includes the gpt-6-astra real-API test)
- `pytest application/python/tests -m 'manual_integration' -q` (ChatGPT
  saved-login; requires `$CHATGPT_TEST_STATE_DIR` auth state)
- `ruff check` + `black` on touched Python paths; `pyright`
- `python docs_site/scripts/prepare_mkdocs_site.py` if publishing docs in the
  same change

### Risks

- Upstream drift between planning and execution: re-verify hashes first;
  introduction dates shift with content.
- gpt56 unit/real-API/ChatGPT tests assert old template hashes and the
  Sol-specific paragraph; step 2 must update them (expected, not a
  regression).
- gpt-6-astra may not yet be reachable by the test API key or saved ChatGPT
  login; if so, keep the tests realistic and report the blocker instead of
  weakening them.
- The `priority`→`fast` tier rename touches shared pricing and fast-mode
  code; verify the existing pricing unit tests and cost-estimation
  fixtures.
- Pricing page structure may change again; the refresh parser is shared
  production code.

## Implementation Notes

- Upstream moved between planning and execution start
  (`5b1d656018` → `e9633d7a02`, 2026-09-14); all recorded template hashes
  were re-verified unchanged at the new head, so the introduction dates
  stayed valid. The catalog refresh used the new head commit.
- The pricing refresh originally kept stale top-level `pricing` blocks for
  models whose standard prices changed (the merge only set `pricing` when
  absent). `merge_pricing_entry` now always rebuilds the denormalized
  `pricing` block from the merged standard tier, and the refresh script
  routes retained off-page entries through the merge so their obsolete
  `priority` keys are renamed.
- The `test_default_config_codex_gpt56_*` suites asserted the 2026-07-13
  template hashes and Sol's distinct paragraph; they were updated to
  assert the dated 20260718 files, the shared template, and the retention
  of the old unversioned files (provenance), as anticipated by the risks.
- Two usage-extension unit tests exercised the manual ChatGPT pricing
  fallback through the checked-in manual models file; after decision 5
  emptied it, they were rewritten to supply a synthetic manual payload at
  the loader boundary (keeping the mechanism covered without depending on
  the checked-in file).
- **Live tier retest findings (decision 2):** the official API accepts
  `service_tier: "fast"` but reports `priority` in responses; the ChatGPT
  backend rejects `fast` with `400: Unsupported service_tier: fast` and
  accepts `priority`, reporting `default` for the test account (fast tier
  not applied). Reported to the user with the evidence; the user chose
  Option A: the Fast mode extension resolves the wire value from the
  effective auth mode (`fast` for API-key auth, `priority` for ChatGPT
  auth), the snapshot stays keyed `fast`, and `normalize_service_tier`
  maps reported `priority` → `fast` prices. The saved-login tier test
  (`test_openai_responses_chatgpt_saved_login_fast_tier_pricing`) and the
  fast-mode round-trip test were rerun live against the ChatGPT backend
  with the `~/.crystal` saved login: both send `priority`, are accepted,
  and xfail with the accurate `default`-report reason.
- The pre-existing failure
  `application/python/tests/test_repo_run_script.py::test_python_tooling_scripts_run_through_repo_run`
  (iOS embedded-providers npm scripts not using `repo_run.py`) was verified
  pre-existing at the base commit `65beac9d` and is unrelated to this
  task. The three `request_options_ui.reasoning_effort` differences
  between `docs/reference/default-config.md` and `config.json` are also
  pre-existing and untouched.
## Completion Notes

**Outcome.** GPT-6-Astra is fully wired into the default configuration with
date-versioned developer messages (20260904), the drifted previous-model
instructions were refreshed as dated files (GPT-5.6 family 20260718;
gpt-5.5/gpt-5.4 20260911) with all previous version files retained, and the
companion catalog, pricing, and reasoning maintenance is complete. The
service tier is `fast` throughout the snapshot, pricing, and docs, with the
user-approved Option A wire behavior: `fast` for API-key auth, `priority`
for ChatGPT auth (the only name that endpoint accepts).

**Requirement evidence.**

- gpt-6-astra assets/selection: 13 unit tests in
  `test_default_config_codex_gpt6_astra_instruction_selection.py` (dated
  file selection, `openai/` prefix, bare-alias fallback, personality
  fallback, hash provenance, `{{connector_id}}` verbatim, reference-copy
  parity); real-API test
  `test_default_config_codex_gpt6_astra_system_instructions_real_api.py`
  (passed live twice); ChatGPT saved-login round trip + selection-only
  (passed live).
- Previous-model updates: 16 unit tests in the updated
  `test_default_config_codex_gpt56_instruction_selection.py` (dated 20260718
  selection, shared template, retained 20260713 files with old hashes,
  gpt-5.5/gpt-5.4 default rows repointed to 20260911 with friendly/pragmatic
  rows retained); gpt56 real-API and ChatGPT tests pass live.
- Catalog: refreshed snapshot at commit `e9633d7a02` contains gpt-6-astra
  and both daybreak models, not gpt-5.2/gpt-5.4-mini;
  `test_checked_in_codex_snapshot_lists_gpt_6_astra_and_daybreak` and
  `test_checked_in_manual_chatgpt_models_are_empty` pass.
- Pricing: refreshed snapshot has gpt-6-astra (standard 10/50, fast 20/100)
  and the new GPT-5.6 prices (sol 4/20, terra 2/12, luna 0.2/1.2); no
  `priority` keys anywhere (`test_checked_in_snapshot_has_gpt_6_astra_and_no_priority_tiers`);
  merge-rename and obsolete-name-lookup tests pass; live retests: API
  accepts `fast` and reports `priority` (normalized to fast prices), ChatGPT
  accepts `priority` and reports `default` (tier tests xfail with the
  verified reason).
- Reasoning: gpt-6-astra pattern added; effort set, Pro mode, and reasoning
  context offered (3 new unit tests pass).
- Docs: codex README provenance/family notes, regenerated
  `docs/reference/default-config.md` (surgically, preserving the existing
  compact format; semantically equal to config.json except three
  pre-existing differences), model-discovery/cost-estimation/reasoning-controls
  pages and the openai_responses README updated for `fast` and the
  auth-mode-dependent wire value.

**Verification performed.**

- `pytest plugins/openai_responses/tests -q`: 439 passed (93 deselected by
  default markers).
- `pytest application/python/tests -q`: 435 passed, 1 skipped; the single
  failure (`test_repo_run_script.py::test_python_tooling_scripts_run_through_repo_run`)
  was verified pre-existing at base commit `65beac9d` (iOS npm-script
  wrapping, unrelated).
- Hosted API: gpt-6-astra + gpt56 real-API instruction tests (2 passed);
  fast-mode wire test (passed; API accepts `fast`).
- ChatGPT saved login (`CHATGPT_TEST_STATE_DIR=~/.crystal`): instruction
  round trips + selection-only for gpt-6-astra and gpt56 (4 passed); tier
  pricing + fast-mode round trip (2 xfailed with the accurate
  `default`-report reason — the fast tier is not applied for this account).
- `ruff check` and `black` clean on all touched Python files; `pyright`
  shows only pre-existing errors (verified by before/after comparison).

**Plan deviations and findings.** Decision 2 was refined mid-execution with
user approval (Option A) after the live retest revealed the ChatGPT backend
rejects `service_tier: "fast"`; see Implementation Notes. The pricing merge
gained a fix that rebuilds the denormalized standard `pricing` block on
refresh so price changes are reflected (previously stale blocks survived).
The saved-login tier tests remain expected-fail (xfail) because the test
account does not receive the fast tier — the requests themselves are
verified accepted with the correct wire name.

**Unresolved or deferred scope.** None for this task. Fast-tier pricing for
the ChatGPT account remains unverifiable until the account/model receives
the fast tier; the xfail tests will pass once the backend reports
`fast`/`priority`.
