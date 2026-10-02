# Per-model token rates, `$include` config merging, and bundled pricing extracts

Enable accurate cost tracking for OpenAI-compatible endpoints (ollama, z.ai,
fireworks) that report tokens but no cost: allow per-model rate entries
inside `token_rates`, let config objects include external JSON files, and
ship one-time pricing extracts for the default-config providers so first
install resolves them out of the box.

This task is a follow-up to `tasks/20260920-generic-cost-tracking.md`
(checkpoints 1–2 complete). Revised 2026-09-27 per user decisions: per-model
rates live inside `token_rates` (no separate key), no fetch script (one-time
committed extracts instead), and the default config must resolve the
included pricing at first install.

## Requirements checklist

- [x] Per-model token rates: the reference openai-compatible provider's
  usage extension accepts per-model rate entries inside `token_rates` via a
  `models` sub-mapping; when the active model matches a configured entry,
  those rates are used to compute cost; otherwise the flat base keys of
  `token_rates` apply (existing configs unchanged). Per-model entries
  support the same keys as the base shape, including `cache_write`.
- [x] `$include` config merging: the config parser supports a special
  `"$include": "path/to.json"` key in any config object; the referenced JSON
  file's content is merged into that object using the same merge machinery
  as config mixins, and the `$include` key is consumed so downstream config
  sees only the merged result.
- [x] One-time pricing extracts: committed JSON files under
  `default_config/pricing/` (ollama, z.ai, fireworks) carry per-model rates
  in the `models` shape the usage extension consumes, extracted from each
  provider's official pricing page at implementation time. No fetch/sync
  script is created.
- [x] Default-config wiring: the default config's openai-compatible
  providers (`ollama`, `fireworks`, `zai`) reference their pricing file via
  `token_rates: {"$include": "${env:CONFIG_DIR}/pricing/<provider>.json"}`;
  a first install (`_ensure_default_config`) copies the pricing files and
  the resolved config contains the merged per-model rates with no manual
  steps.
- [x] End-to-end: a config using `$include` with a per-model pricing entry,
  loaded through the real config pipeline and driven through the reference
  provider with a matching model, computes cost from the per-model rates
  (including the checkpoint-2 breakdown).

## Open requirement questions

- None blocking. Resolved by user decisions on 2026-09-27:
  - Config shape: per-model rates inside `token_rates` (a `models`
    sub-mapping; flat keys remain the base), not a separate
    `model_token_rates` key.
  - No pricing fetch script; one-time extraction committed with the
    default config.
  - The default config must resolve included pricing at first install.

## Supporting details

**Verified facts:**

- Ollama's OpenAI-compatible endpoint reports only token counts — no cost.
  Non-stream and streaming (`stream_options.include_usage`) responses both
  carry `prompt_tokens`, `completion_tokens`, `total_tokens`, and
  `prompt_tokens_details.cached_tokens`; there is no `cost` field.
- Ollama official pricing (https://ollama.com/cloud, "Model pricing" table,
  $/M input/cached/output; re-verified 2026-09-20): `glm-5.2`
  1.40/0.26/4.40; `glm-5.3` 1.40/0.26/4.40; `glm-5.3-flash` 0.15/0.03/0.50;
  `glm-5.1` 1.00/0.20/3.20; `gpt-oss:120b` 0.15/0.014/0.60; `kimi-k3`
  3.00/0.30/15.00. A "Peak pricing" table (12:00–18:00 UTC, Mon–Fri)
  affects only some deepseek models; flat rates are used. No
  machine-readable pricing API — the HTML table is the only official
  source. Rates must be re-fetched at implementation time since the Sep 20
  snapshot may be stale.
- Default-config openai-compatible providers (`application/python/
  agent_terminal_app/default_config/config.json`): `ollama`
  (localhost:11434, models incl. `qwen3:0.6b` local and agents
  `glm-5.2:cloud`, `deepseek-v4-pro:cloud`, `kimi-k2.6:cloud`),
  `fireworks` (`fireworks/gpt-oss-20b`), `zai` (`glm-5.3-flash`; the `zai`
  agent carries flat rates 1.4/0.26/4.4 today).
- First-install mechanics (verified): `_ensure_default_config`
  (`application/python/agent_terminal_app/__main__.py:283`) copies every
  support file from the bundled `default_config/` template next to the
  installed config and writes `config.json`; `CONFIG_DIR` defaults to the
  config file's parent (`core/python/agent_app/config.py:102`). Committing
  `default_config/pricing/*.json` therefore installs them at first run and
  `${env:CONFIG_DIR}/pricing/<provider>.json` resolves both in-repo
  (template dir) and after install.
- Rate consumption and model-id mismatch (ollama tags like
  `glm-5.2:cloud` vs pricing key `glm-5.2`) live in
  `plugins/reference-openai-compatible-provider/src/
  reference_openai_compatible_provider/usage_extension.py`:
  `_rate_token_split` resolves rates from `token_rates` (input, cached,
  completion, optional cache_write; cached falls back to input) and
  `get_config_schema` declares the flat schema. The extension runs at
  `priority: int = 60`; keep the 60/70 ordering with cost tracking intact.
- Config pipeline: `load_raw_config` → `resolve_placeholders`
  (`core/python/agent_app/config.py` ~line 380, `${env:...}`) →
  `resolve_config_mixins` (~line 559). Merge machinery in
  `core/python/agent_app/config_merge.py` (`merge_config`, `MERGE_KEY`,
  deep/shallow modes) with mixin guards (cycle detection, bounded depth,
  structured errors `{type, path, detail}`). `$include` should reuse
  `merge_config` with the mixin default mode and consume the key like
  `$mixin_refs` is consumed.
- The user's live config (`~/.crystal/config.json`, agent `glm-ollama`)
  runs `glm-5.2:cloud` with glm-5.1 rates (1/0.2/3.2) — undercounting
  ~27–29%. Updating the user config is out of scope for this task (offered
  separately), but the shipped extracts fix the default config's accuracy.

**Conventions:**

- Tests: config parser → `core/python/tests`; usage extension →
  `plugins/reference-openai-compatible-provider/tests`; default-config
  wiring/first-install → `application/python/tests`
  (`test_default_config_effective_agent_configs.py` style).
- Docs: reference provider user docs for the `models` shape; config docs
  (`application/python/docs/`) for `$include`; default-config/pricing note
  stating extracts are one-time snapshots refreshed manually.

## Execution plan

Status: Approved (2026-09-27)

### Approach

1. **Per-model rates in `token_rates` (usage extension).** Resolve the
   effective rates before `_rate_token_split` runs: if `token_rates` has a
   `models` dict and the active model matches an entry, that entry is the
   effective rate set; otherwise the flat keys of `token_rates` are.
   Matching order: exact model id, then trailing-`:tag` stripped
   (`glm-5.2:cloud` → `glm-5.2`), then case-insensitive. A matching entry
   must carry at least `input` and `completion` (else fall through to the
   base rates). Update `get_config_schema` with the `models` property.
   Unit tests: entry wins, base fallback, no rates → no estimation, suffix
   and case normalization, per-model `cache_write`, schema shape.
2. **`$include` resolution.** In `core/python/agent_app/config.py`, add an
   include-resolution step after `resolve_placeholders` (include paths may
   use `${env:...}`) and before `resolve_config_mixins` (included content
   may carry mixin refs). Walk the tree; any object with `"$include"` loads
   the JSON file and merges it into that object via `merge_config` (mixin
   default mode; `$merge` directives in included files honored), then
   removes the key. Guards mirror mixins: cycle detection, bounded depth,
   structured error entries for missing/unparsable files. Unit tests in
   `core/python/tests`: include at root/provider/agent levels, nested
   includes, env-placeholder path, missing file error, cycle error,
   `$merge` behavior, key not visible downstream.
3. **One-time pricing extracts.** Fetch each provider's official pricing
   page (ollama.com/cloud; z.ai model pricing; fireworks.ai pricing) and
   write `default_config/pricing/ollama.json`, `zai.json`,
   `fireworks.json`, each shaped
   `{"_source": "<url>", "_generated_at": "<iso>", "models": {"<model>":
   {"input": .., "cached": .., "completion": ..}}}` with keys matching the
   model ids the default config uses (ollama keys without the `:cloud`
   suffix; fireworks/z.ai keys as configured). Unknown keys (`_source`,
   `_generated_at`) are ignored by the consumer. The extraction is
   manual/one-time; record the fetched values and date in the completion
   notes.
4. **Default-config wiring.** Set `token_rates` on the `ollama`,
   `fireworks`, and `zai` providers to
   `{"$include": "${env:CONFIG_DIR}/pricing/<provider>.json"}`; remove the
   now-redundant flat `token_rates` from the `zai` agent (same values move
   to the provider-level extract). Extend
   `application/python/tests/test_default_config_effective_agent_configs.py`
   with: template config resolves through the real pipeline to merged
   per-model rates; `_ensure_default_config` into a temp dir produces an
   installed config whose providers resolve the copied pricing files.
5. **End-to-end verification.** An integration-style test chaining
   `$include` → per-model rates → cost metadata: a config with an included
   pricing file, reference provider request with a matching model via a
   stub endpoint, asserting `usage_total_cost`/`usage_cost_breakdown`
   reflect the per-model rates (reuse the cost-tracking integration test
   harness style).

### Implementation decisions and open questions

- Per-model entries override the base as a whole set (no per-key merge
  between a model entry and base keys); within an entry, `cached` falls
  back to that entry's `input` (existing semantics).
- If a matching model entry is incomplete (missing `input`/`completion`),
  fall back to base rates rather than partial pricing.
- Peak pricing (deepseek on ollama) is out of scope; flat rates only.
- Refreshing the extracts is manual (re-do the extraction and commit);
  noted in docs. No automation in this task.
- Local ollama models (e.g. `qwen3:0.6b`) have no cloud pricing; they
  simply match no entry and use base rates (none by default → no
  estimation), preserving current behavior.

### Documentation

- Reference provider user docs: the `token_rates.models` shape and
  matching rule.
- Config user docs (where mixins are documented): `$include` semantics,
  path resolution (`${env:CONFIG_DIR}`, `~`, relative-to-config-dir),
  guards.
- Default-config/pricing: a short note (README or doc section) that the
  files are one-time snapshots, their sources, and how to refresh.

### Task checklist

- [x] Per-model rates in the usage extension + schema + unit tests.
- [x] `$include` resolution in the config parser + unit tests.
- [x] Pricing extracts fetched and committed under
      `default_config/pricing/`.
- [x] Default-config provider wiring + first-install tests.
- [x] End-to-end test of the chain.
- [x] Lint (ruff/black), pyright, and run: `pytest core/python/tests -q`,
      `pytest plugins/reference-openai-compatible-provider/tests -q`,
      `pytest application/python/tests -q`,
      `pytest plugins/cost-tracking/tests -q`.
- [x] Update docs.
- [x] Record completion notes (including extracted rates + sources).

### Requirement verification

- Per-model rates: usage-extension unit tests asserting computed cost for a
  matching model (exact, `:tag`-stripped, case-insensitive), base fallback,
  and no-rates behavior.
- `$include`: parser-level tests asserting the resolved config equals the
  expected merged structure (public boundary: the resolved config handed to
  the application), including error entries for bad includes and that the
  key is consumed.
- Extracts: committed JSON asserted against the sources during extraction
  (human verification of the fetched numbers); shape covered by tests.
- First install: tests running `_ensure_default_config` against the real
  template and loading the installed config through the pipeline, asserting
  providers carry merged per-model rates.
- End-to-end: one integration test through the provider request path
  asserting cost/breakdown metadata reflects per-model rates from an
  included file.

### Additional implementation verification

- Existing mixin behavior unchanged (config-related core tests).
- Cost tracking extension ordering (priority 60/70) intact after usage
  extension changes.
- Default-config effective-agent tests keep passing (the wiring change must
  not alter agents beyond the intended rate resolution).

## Implementation Notes

- 2026-09-27: Implemented per the approved plan. Per-model resolution lives
  in `_effective_token_rates`/`_matching_model_entry` (usage extension);
  finalize reads the active model from `state.request.payload.model` with
  fallback to `config.model`. `$include` resolution is
  `resolve_config_includes` in `core/python/agent_app/config.py`, wired into
  both `load_resolved_config` and the `AgentApplication` pipeline between
  placeholder and mixin resolution.
- Model matching stayed minimal per the approved plan (exact → trailing
  `:tag`-stripped → case-insensitive). No `vendor/` prefix stripping: the
  default config needs none, and `fireworks/gpt-oss-20b` has no priced entry
  to match anyway.
- Extracts cover only models relevant to the default config (ollama cloud
  models used by default agents; z.ai GLM-5 family; the fireworks current
  serverless table). This avoids a false-positive risk: pricing the full
  ollama cloud table would estimate costs for LOCAL runs of same-named
  models (e.g. local `gpt-oss:20b`).
- Deviation found during extraction: fireworks' current serverless pricing
  table (2026-09-27) no longer lists gpt-oss-20b, so the default fireworks
  agent matches no entry and stays unestimated (previous behavior). The
  table's six current models are shipped with id-style keys; their rates are
  much higher than z.ai's direct prices for the same model names (e.g.
  GLM 5.3 Flash $2.96/M input vs z.ai $0.15) — recorded verbatim from the
  official page with `_source` attribution.
- The zai agent's previous flat rates (1.4/0.26/4.4 = GLM-5.3 non-flash
  prices) were wrong for its actual model `glm-5.3-flash` (0.15/0.03/0.5);
  the provider-level extract fixes this ~9x overestimate for fresh installs.
- Tests must be hermetic against the host `CONFIG_DIR` env var (process env
  overlays the derived value): the application-level tests pass explicit
  `env={}`, and the e2e passes `env_overrides={"CONFIG_DIR": tmp}`.
- Pre-existing environmental failure, not from this task:
  `test_runtime_layout.py::test_source_runtime_layout_resolves_bundle_paths`
  fails because the editable `agent_terminal_app` install points at the
  `ai-agent-platform-main` checkout (fails on HEAD too); the new bootstrap
  test passes an explicit manifest path to stay hermetic.
  `test_claude_system_message_helpers` failure is the known pre-existing
  one awaiting a user decision.

## Completion Notes

- Outcome: all five requirements implemented and verified.
- Extracted rates (USD per M tokens, input/cached/output, fetched
  2026-09-27):
  - ollama.com/cloud "Model pricing": `glm-5.2` 1.40/0.26/4.40;
    `deepseek-v4-pro` 1.32/0.044/3.96; `kimi-k2.6` 0.95/0.16/4.00
    (standard rates; off-peak rows for deepseek models not modeled).
  - docs.z.ai/guides/overview/pricing: `glm-5.3` 1.40/0.26/4.40;
    `glm-5.3-flash` 0.15/0.03/0.50; `glm-5.2` 1.40/0.26/4.40;
    `glm-5.1` 1.40/0.26/4.40 (standard API list prices; the coding-plan
    endpoint bills by points — estimates only, noted in the file).
  - fireworks.ai/pricing serverless table: `glm-5.3-flash` 2.96/0.593/7.41;
    `glm-5.3` 4.86/0.972/12.15; `qwen-3.8-27b` 1.86/0.372/5.595;
    `kimi-k3` 10.87/2.17/27.11; `deepseek-v4-flash-0731` 1.74/0.35/4.33;
    `muse-glimmer-30b` 1.96/0.39/4.88. gpt-oss-20b not listed (see
    implementation notes).
- Requirement evidence:
  - Per-model rates: 8 new unit tests in
    `plugins/reference-openai-compatible-provider/tests/test_usage_extension_unit.py`
    (exact/tag-stripped/case-insensitive matching, base fallback, incomplete
    entry fallback, per-model cache_write with breakdown, config-model
    fallback, schema shape).
  - `$include`: 16 tests in `core/python/tests/test_config_includes.py`
    (levels, nesting with file-relative paths, env-placeholder path via the
    full pipeline, local-override precedence, missing/unparsable/non-object/
    non-string errors, cycle, depth bound, `$merge` governance and
    preservation, mixin-refs handoff, `~` expansion, policy default).
  - Extracts + first install:
    `test_default_config_bootstrap_installs_pricing_extracts` (real
    `_ensure_default_config` into a temp dir + pipeline load) and
    `test_default_config_pricing_includes_resolve_per_model_rates`
    (template-level resolution, all three providers, zai agent key removed).
  - End-to-end: `test_config_include_per_model_rates_integration.py`
    (integration-marked, run explicitly): real `AgentApplication` request
    through a stub chat-completions endpoint with model `glm-5.2:cloud`;
    asserts `usage_total_cost` = 0.003372 and cost-store per-item columns
    (input 0.00112, cached 0.000052, output 0.0022) from the included
    per-model rates.
- Verification runs: core 585 passed/26 deselected; reference provider 121
  passed/62 deselected (default) + e2e 1 passed with `-m integration`;
  application 424 passed/1 skipped/1 pre-existing failure (also fails on
  HEAD); cost-tracking 70 passed. ruff clean, black applied, pyright adds no
  new errors (13 vs 14 baseline on the touched files).
- Docs: `application/python/docs/configuration-includes.md` (new, indexed);
  reference provider README per-model section (+`cache_write` bullet that
  was missing); each pricing file carries `_source`/`_generated_at`/`_note`.
- Unresolved/deferred: fireworks gpt-oss-20b has no official price row
  (stays unestimated); off-peak pricing out of scope; vendor-prefix model
  matching not implemented (not needed by the default config); user's live
  `~/.crystal/config.json` still on glm-5.1 rates (separate standing offer).
