# GPT-6 Sol and Luna model update

Import the new GPT-6 family members (`gpt-6-sol`, `gpt-6-luna`) with
date-versioned developer messages, refresh the drifted GPT-6-Astra and
GPT-5.6 templates, and run the companion catalog/pricing/reasoning
maintenance. Follows the protocol documented in
`application/python/docs/development/agent-creation.md`.

Predecessor task: `tasks/20260914-gpt-6-astra-model-update.md` (committed
as `90fe2d86`).

## Requirements checklist

- [x] `gpt-6-sol` and `gpt-6-luna` developer messages exist as
  date-versioned assets under `default_config/codex/gpt-6-{sol,luna}/`
  (introduction date `20260922`) with reference copies, and their
  `codex_developer_messages` rows select them for the bare and
  `openai/`-prefixed IDs with every personality resolving to the same
  template; no pre-existing model instruction asset is modified or removed.
- [x] New date-versioned instruction files exist for the drifted upstream
  templates — `gpt-6-astra` (`20260923`) and the GPT-5.6 family
  (`20260923`) — with the `codex_developer_messages` rows repointed to them
  and all previous version files retained unmodified.
- [x] The checked-in Codex models snapshot reflects the current upstream
  catalog: `gpt-6-sol` and `gpt-6-luna` present; `gpt-5.4` absent.
- [x] The checked-in pricing snapshot contains `gpt-6-sol` and `gpt-6-luna`
  entries with the published prices, and Fast-mode cost estimation resolves
  them.
- [x] `gpt-6-sol` is offered its real reasoning-effort set (`low` through
  `ultra`) with Pro mode and reasoning context; `gpt-6-luna` is offered its
  real set (`low` through `max`, no `ultra`).
- [x] `default_config/codex/README.md` records the new import commits,
  dates, and family notes, and `docs/reference/default-config.md` is
  updated for the changed rows.
- [x] Model selection and end-to-end instruction delivery for the new and
  refreshed models are covered by automated tests: unit selection tests
  (model regex, `openai/` prefix, personality fallback, content
  distinctions, older-model regressions), a real-API test, and a ChatGPT
  saved-login test proving the compiled gpt-6-sol instructions reach
  top-level instructions.

## Resolved decisions

1. **Retired models stay untouched** (user-approved): `gpt-5.4` — retired
   upstream 2026-09-24 (`694d8d45bd3d`, #47932) — keeps its config rows,
   assets, and tests exactly as they are; there is no upstream source to
   refresh from. Same standing policy as `gpt-5.2` / `gpt-5.4-mini`.
2. No bare `gpt-6` alias row (consistent with the established bare-alias
   policy; upstream publishes only explicit IDs).
3. `{{connector_id}}` stays verbatim in the new templates (upstream renders
   it literally); `persistent_instructions` imported as dated provenance
   copies only.

## Supporting details

### Upstream state (investigated 2026-09-27)

- Latest inspected `openai/codex` commit:
  `41f9084b30812db321a0b592def4f500d1e79cf4` (2026-09-27), file
  `codex-rs/models-manager/models.json`; 10 models.
- Relevant commits since the 2026-09-14 import base (`e9633d7a02`):
  - `49e95cc73f4e` (2026-09-22, #47332): add `gpt-6-sol` and `gpt-6-luna`;
  - `deb0a08f240f` (2026-09-21, #47085): update catalog descriptions and
    GPT-5.6-Sol priority tier description;
  - `cf6754e6828d` (2026-09-21, #47130): remove the `ultrafast` service
    tier from `gpt-5.6-sol`;
  - `24462234b2ae` (2026-09-23, #47397): refresh instructions for
    `gpt-6-astra` and the GPT-5.6 family (also later Guardian change
    `e9b4c6967ee3`, not instruction-relevant);
  - `694d8d45bd3d` (2026-09-24, #47932): retire `gpt-5.4`.

### New model entries

| | `gpt-6-sol` | `gpt-6-luna` |
|---|---|---|
| display_name / description | GPT-6-Sol / "Workhorse model for coding and everyday work." | GPT-6-Luna / "Fast and affordable model for easier tasks." |
| context_window / max | 272000 / 872000 | 272000 / 872000 |
| default_reasoning_level | medium | medium |
| supported efforts | low, medium, high, xhigh, max, ultra | low, medium, high, xhigh, max |
| service_tiers | priority ("Fast") | priority ("Fast") |
| visibility / supported_in_api | list / true | list / true |
| minimal_client_version | 0.155.0 | 0.155.0 |
| shell_type | shell_command | shell_command |
| template | 18992 chars, sha256 `b1dd8718c037906c53a305c5cbccb4a4be35ccbb7837461ec349bfc495412f0d` | 18037 chars, sha256 `b707476816bfe5e571a1bd2179f130fff2b132da5ab8e61063acdb7fd24daf12` |
| persistent_instructions | 5737 chars (same as astra) | 5737 chars (same as astra) |
| pricing (standard, per 1M) | 2.0 / 10.0 out (cached 0.2, write 2.5); fast 4.0 / 20.0 | 0.1 / 0.5 out (cached 0.01, write 0.125); fast 0.2 / 1.0 |

Both open with `You are Codex, an agent based on GPT-6`, contain
`{{connector_id}}` verbatim, have no personality placeholder, and have
empty/absent `instructions_variables`.

### Template drift for existing models

- `gpt-6-astra` new template introduced 2026-09-23 (`24462234b2ae`):
  21420 chars, sha256
  `35bd51b5f577cb7b24cd5f4629e49e37cb724ab57754ce6f8f202001635bab8a`.
  Exactly one line differs from our `20260904` file: the tool-messaging
  authorization sentence in the permission section.
- GPT-5.6 family new shared template introduced 2026-09-23 (same commit):
  17730 chars, sha256
  `a91357a1cd2727a0be06d461248d6e3a7274746e38108f548a3adf2cc2430415`.
  Exactly one line differs from our `20260718` file: heading
  `# Destructive Actions` → `# Destructive actions`.
- `gpt-5.5` unchanged (sha256 `2351631dfc5644dc…` equals our `20260911`
  import).
- `codex-auto-review` now shares the gpt-5.6 template (metadata-only
  concern; not wired into our config).

### Pricing page (fetched 2026-09-27)

- 38 models (was 36): `gpt-6-sol` and `gpt-6-luna` are already published.
- All GPT-5.6 and gpt-6-astra prices unchanged since the last refresh.
  Tier names still `standard`, `batch`, `flex`, `fast`.

### Repo state

- Catalog snapshot at `e9633d7a02` (2026-09-14): missing gpt-6-sol/luna,
  still lists gpt-5.4.
- Instruction assets: gpt-6-astra `20260904` and GPT-5.6 `20260718` are
  one revision behind upstream.
- Reasoning patterns in `openai_responses_reasoning_extension.py`: only
  `gpt-6-astra` covered for the GPT-6 family. `gpt-6-luna`'s effort tuple
  (`low…max`) already exists in `_GPT_5_6_REASONING_EFFORTS`, so
  Pro/context gating needs no new tuple.

## Execution plan

Status: Approved

Extraction source: local `openai/codex` clone at
`/Users/ferenci84/Dev/Mine/codex` (fetched to `origin/main`
`41f9084b30` on 2026-09-27). Re-verify the recorded template hashes at
execution start; if upstream moved, re-derive the introduction dates
before importing.

### Step 1 — Import gpt-6-sol and gpt-6-luna (previous assets untouched)

1. Extract both entries at the inspected commit.
2. Create `default_config/codex/gpt-6-sol/` and `gpt-6-luna/` with
   date-versioned files (introduction date `20260922`):
   `instructions_default.20260922.md` (effective message, identical to the
   template), `model_messages.instructions_template.20260922.md`,
   `model_messages.instructions_variables.20260922.json` (empty object),
   `model_messages.persistent_instructions.20260922.md` (provenance copy).
3. Copy the same files to the reference archive under
   `system_messages/reference/default-system-instructions/codex/`.
4. Add two config rows at the top of `codex_developer_messages` (above
   gpt-6-astra), no `personality` field:
   `^(openai/)?gpt-6-sol$` and `^(openai/)?gpt-6-luna$`.

### Step 2 — Refresh drifted templates

1. `gpt-6-astra`: add `instructions_default.20260923.md` +
   `model_messages.instructions_template.20260923.md` +
   `model_messages.instructions_variables.20260923.json`; repoint the
   config row; keep `20260904` files.
2. GPT-5.6 family: add `*.20260923.md` / `*.json` dated files to each of
   `gpt-5.6-{sol,terra,luna}`; repoint the three rows; keep `20260718`
   and the original unversioned files.
3. Update the gpt-6-astra and gpt56 selection unit tests to assert the new
   dated files (the astra hash and the one-line GPT-5.6 heading change).

### Companion maintenance

1. Catalog: run
   `python plugins/openai_responses/benchmark/refresh_openai_responses_models.py`;
   verify gpt-6-sol/luna present and gpt-5.4 absent; extend the catalog
   unit tests.
2. Pricing: run
   `python plugins/openai_responses/benchmark/refresh_openai_responses_pricing.py`;
   verify gpt-6-sol/luna entries; extend the pricing snapshot unit test.
3. Reasoning: add patterns for `gpt-6-sol` (full set through `ultra`) and
   `gpt-6-luna` (`low…max`, no `ultra`) before the gpt-6-astra pattern;
   extend the reasoning unit tests (effort options, Pro mode, reasoning
   context, effort injection).
4. Docs: update `default_config/codex/README.md` (new imports, drift
   refresh notes); update the model-discovery snapshot note; surgically
   update `docs/reference/default-config.md` rows.

### Implementation decisions and open questions

All decisions resolved (see Resolved decisions). Local reversible choices:
date-versioned naming per the protocol page; catalog/pricing refresh
scripts as-is.

### Documentation

- `application/python/agent_terminal_app/default_config/codex/README.md`
- `plugins/openai_responses/docs/development/model-discovery.md`
- `docs/reference/default-config.md` (surgical row updates)
- `plugins/openai_responses/README.md` reasoning-effort list if needed

### Task checklist

- [x] Re-verify upstream hashes and introduction dates at execution start
- [x] Step 1: gpt-6-sol/gpt-6-luna dated assets + reference copies + config rows
- [x] Step 2: gpt-6-astra 20260923 refresh + repointed row
- [x] Step 2: GPT-5.6 family 20260923 refresh + repointed rows
- [x] Companion: catalog snapshot refresh + tests + docs note
- [x] Companion: pricing snapshot refresh + tests
- [x] Companion: reasoning patterns for gpt-6-sol/luna + tests
- [x] Docs: codex README + default-config reference rows
- [x] Tests: gpt-6 family unit selection tests (new file)
- [x] Tests: updated drift tests (gpt6-astra + gpt56 suites)
- [x] Tests: real-API instruction delivery test for gpt-6-sol
- [x] Tests: ChatGPT saved-login instruction delivery test for gpt-6-sol
- [x] Verification: default suites + hosted API + ChatGPT slice + lint/typecheck

### Requirement verification

| Requirement | Acceptance evidence |
|---|---|
| gpt-6-sol/luna dated assets + selection | Unit tests selecting dated files for bare and `openai/`-prefixed IDs across personalities; hash provenance assertions |
| Drifted-template refresh | Unit tests asserting 20260923 files selected for gpt-6-astra and the GPT-5.6 family; previous dated files still present |
| Catalog snapshot | Snapshot JSON contains gpt-6-sol/luna, lacks gpt-5.4; catalog unit tests pass |
| Pricing snapshot | Pricing snapshot tests pass with gpt-6-sol/luna entries; fast-tier estimation resolves |
| Reasoning efforts | Reasoning unit tests assert per-model effort sets, Pro mode, and context for both new models |
| Docs | README provenance section; default-config reference rows match config.json |
| End-to-end delivery | Real-API and ChatGPT saved-login tests assert compiled gpt-6-sol instructions reach top-level instructions |

### Additional implementation verification

- `pytest plugins/openai_responses/tests -q`
- `pytest application/python/tests -q`
- Hosted API: new gpt-6 real-API instruction test (and existing suites)
- ChatGPT saved-login: new instruction test with `CHATGPT_TEST_STATE_DIR`
- `ruff check` + `black` on touched files; `pyright` (no new errors)

### Risks

- Upstream drift between planning and execution: re-verify hashes first.
- gpt-6-sol/luna may not be reachable by the test API key or saved ChatGPT
  login; if so, keep the tests realistic and report the blocker.
- The gpt56/astra suites assert the `20260904`/`20260718` hashes; they must
  be updated to the new dated files (expected, not a regression).
## Implementation Notes

- Upstream moved slightly between planning and execution
  (`41f9084b30` → `ea64727556`, both 2026-09-27); all recorded template
  hashes were re-verified unchanged, so the introduction dates stayed
  valid and the catalog refresh used the newer head.
- The gpt56 selection suite's dated-files test initially kept the
  `GPT_56_20260718_SHA256` constant after the file-swap; fixed to assert
  `GPT_56_20260923_SHA256` for the new files plus heading presence, and
  the retained `20260718` hash.
- The gpt-6-astra selection suite needed only constant updates (date and
  template hash); its structural assertions (selection, fallback,
  provenance, row order) carried over unchanged.

## Completion Notes

**Outcome.** `gpt-6-sol` and `gpt-6-luna` are fully wired into the default
configuration with date-versioned developer messages (`20260922`), the
drifted `gpt-6-astra` and GPT-5.6 templates were refreshed as `20260923`
dated files with all previous versions retained, and the companion
catalog, pricing, and reasoning maintenance is complete. Retired models
(`gpt-5.4` and older) are untouched per the approved decision.

**Requirement evidence.**

- gpt-6-sol/luna assets/selection: 14 unit tests in
  `test_default_config_codex_gpt6_sol_luna_instruction_selection.py`
  (dated selection for bare and `openai/`-prefixed IDs, personality
  fallback, hash provenance, pairwise-distinct templates, reference-copy
  parity, row order); real-API test
  `test_terminal_default_config_codex_gpt6_sol_system_instructions_real_api.py`
  (passed live); ChatGPT saved-login round trip + selection-only (passed
  live).
- Drift refresh: updated gpt-6-astra suite (13 tests) and gpt56 suite (16
  tests) assert the `20260923` files, the astra hash
  `35bd51b5f577cb7b…`, the GPT-5.6 heading change, and retention of the
  `20260904`/`20260718` files; astra/gpt56 real-API and ChatGPT tests pass
  live.
- Catalog: refreshed snapshot at `ea64727556` contains gpt-6-sol/luna and
  lacks gpt-5.4 (`test_checked_in_codex_snapshot_lists_gpt_6_family_and_daybreak`).
- Pricing: refreshed snapshot contains gpt-6-sol (2.0/10.0 standard,
  4.0/20.0 fast) and gpt-6-luna (0.1/0.5 standard, 0.2/1.0 fast)
  (`test_checked_in_snapshot_has_gpt_6_family_and_no_priority_tiers`).
- Reasoning: `gpt-6-(?:astra|sol)` full effort set through `ultra`,
  `gpt-6-luna` `low…max` without `ultra`; Pro mode and reasoning context
  offered for both new models (5 new unit tests).
- Docs: codex README restructured with a GPT-6 family section (imports,
  hashes, refresh history), model-discovery note, README reasoning-key
  lists, and surgically updated `docs/reference/default-config.md` rows
  (only the 3 pre-existing semantic diffs vs config.json remain).

**Verification performed.**

- `pytest plugins/openai_responses/tests -q`: 445 passed (93 deselected).
- `pytest application/python/tests -q`: 449 passed, 1 skipped; the single
  failure is the pre-existing `test_repo_run_script` issue verified at the
  base of the predecessor task.
- Hosted API: gpt-6-sol, gpt-6-astra, and gpt56 real-API instruction
  tests (3 passed live).
- ChatGPT saved login (`~/.crystal`): gpt-6-sol, gpt-6-astra, and gpt56
  instruction round trips + selection-only (6 passed live).
- `ruff check` + `black` clean on all touched Python files; `pyright`
  shows no new errors vs the committed state.

**Plan deviations and findings.** None material. Upstream head moved
within the day before execution; hashes were stable.

**Unresolved or deferred scope.** None.
