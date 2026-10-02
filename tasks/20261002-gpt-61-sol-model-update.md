# GPT-6.1 Sol model update

Import the new `gpt-6.1-sol` model (upstream's new default catalog model)
with date-versioned developer messages and run the companion catalog,
pricing, and reasoning maintenance, following the protocol in
`application/python/docs/development/agent-creation.md`. Afterwards, port
the model into the personal config at `~/.crystal`.

Predecessor tasks: `tasks/20260914-gpt-6-astra-model-update.md`,
`tasks/20260927-gpt-6-sol-luna-model-update.md`.

## Requirements checklist

- [x] `gpt-6.1-sol` developer messages exist as date-versioned assets under
  `default_config/codex/gpt-6.1-sol/` (introduction date `20260929`) with
  reference copies, and its `codex_developer_messages` row selects them for
  the bare and `openai/`-prefixed IDs with every personality resolving to
  the same template; no pre-existing model instruction asset is modified.
- [x] The checked-in Codex models snapshot includes `gpt-6.1-sol`.
- [x] The checked-in pricing snapshot contains a `gpt-6.1-sol` entry with
  the published prices, and Fast-mode cost estimation resolves it.
- [x] `gpt-6.1-sol` is offered its real reasoning-effort set (`low` through
  `ultra`) with Pro mode and reasoning context.
- [x] `default_config/codex/README.md` records the import commit, date,
  and model notes, and `docs/reference/default-config.md` is updated for
  the new row.
- [x] Selection and end-to-end instruction delivery are covered by
  automated tests: unit selection tests, a real-API test, and a ChatGPT
  saved-login test.
- [x] The personal config at `~/.crystal` gains the dated assets, the
  config row, and an updated README note; the `codex-openai` agent model
  is left unchanged (currently `gpt-5.6-sol` by user choice).

## Resolved decisions

1. Work directly on `develop` in the original worktree (consistent with
   the previous task-file commit); no separate task worktree.
2. Agent model unchanged in the personal config; switching
   `codex-openai` to `gpt-6.1-sol` remains a user decision (it was
   manually reverted to `gpt-5.6-sol` after the last migration).
3. Reasoning pattern is member-specific (`^gpt-6\.1-sol(?:-|$)`) so later
  GPT-6.1 family members can carry their own effort sets.

## Supporting details

### Upstream state (investigated 2026-10-02)

- Latest inspected `openai/codex` commit:
  `14a477ea89712071944244022e8a10142845456e` (2026-10-02), file
  `codex-rs/models-manager/models.json`; 11 models.
- `gpt-6.1-sol` introduced 2026-09-29 (`b1e72963c3b7`, #49318, "Add
  GPT-6.1 Sol as the default catalog model"); it takes catalog priority 1.
- Catalog entry: display_name "GPT-6.1-Sol", description "Latest workhorse
  model for coding and everyday work.", context 272000/872000, default
  reasoning level `low` (gpt-6-sol is `medium`), efforts `low, medium,
  high, xhigh, max, ultra`, service_tiers `priority`, visibility `list`,
  supported_in_api true, `send_user_message_async` + `clock`
  experimental tools, shell_type `shell_command`.
- Template: 21769 chars, sha256
  `e1bdd4f8f0df4b20f4a0ffc8a861ce819df45325d8cecdfb92e80379cf8d142e`;
  opens `You are Codex, an agent based on GPT-6`, keeps `{{connector_id}}`
  verbatim, empty variables, 5737-char persistent block (same as the rest
  of the GPT-6 family).
- All other model templates unchanged from the 2026-09-27 import.
- Pricing page (fetched 2026-10-02, 39 models): gpt-6.1-sol standard
  2.0/10.0 (cached 0.1, write 2.5), fast 4.0/20.0 (cached 0.2, write
  5.0) — input/output identical to gpt-6-sol, cached input cheaper.

### Repo and personal state (verified 2026-10-02)

- Default config: no `gpt-6.1` row, no assets, catalog snapshot at
  `ea64727556` (2026-09-27) without the model, pricing snapshot without
  it, and no reasoning pattern matches `gpt-6.1-sol` (verified against
  `_MODEL_REASONING_EFFORT_PATTERNS`; the `.` in `6.1` defeats
  `^gpt-6-(?:astra|sol)`).
- Personal config: no rows/assets; `codex-openai` currently
  `gpt-5.6-sol`.

## Execution plan

Status: Approved

### Step 1 — Import and wiring (repo)

1. Re-verify the recorded template hash at the inspected commit.
2. Create `default_config/codex/gpt-6.1-sol/` with dated `20260929`
   files: `instructions_default.20260929.md` (effective message, identical
   to the template), `model_messages.instructions_template.20260929.md`,
   `model_messages.instructions_variables.20260929.json` (empty object),
   `model_messages.persistent_instructions.20260929.md` (provenance copy);
   mirror all four under the reference archive.
3. Add the config row at the top of `codex_developer_messages` (above
   gpt-6-sol, mirroring upstream's new default-model priority), no
   `personality` field:
   `^(openai/)?gpt-6\.1-sol$` → `instructions_default.20260929.md`.

### Step 2 — Companion maintenance (repo)

1. Catalog: run
   `python plugins/openai_responses/benchmark/refresh_openai_responses_models.py`;
   verify gpt-6.1-sol present; extend the catalog unit test.
2. Pricing: run
   `python plugins/openai_responses/benchmark/refresh_openai_responses_pricing.py`;
   verify the gpt-6.1-sol entry; extend the pricing snapshot unit test.
3. Reasoning: add `^gpt-6\.1-sol(?:-|$)` with
   `("low", "medium", "high", "xhigh", "max", "ultra")` before the GPT-6
   patterns; the tuple is already in `_GPT_5_6_REASONING_EFFORTS`, so Pro
   mode and reasoning context gating come free; extend reasoning tests.
4. Docs: codex README GPT-6.1 note, model-discovery snapshot note,
   README reasoning-key list, and the `docs/reference/default-config.md`
   row.

### Step 3 — Tests (repo)

1. New unit selection test file mirroring the gpt-6 sol/luna suite
   (selection, prefix, personality fallback, hashes, reference parity,
   row order, distinctness from other families).
2. Real-API and ChatGPT saved-login instruction-delivery tests for
   gpt-6.1-sol (adapted from the gpt-6-sol ones).

### Step 4 — Personal config port

1. Backup `~/.crystal/config.json` → `config.json.bak-20261002-port-gpt61`.
2. Copy the four dated asset files (sha-verified) into
   `~/.crystal/codex/gpt-6.1-sol/`.
3. Insert the same config row at the top of the personal
   `codex_developer_messages`.
4. Update the personal `codex/README.md` provenance note.
5. Selection smoke test through the personal config (row resolves,
   GPT-6.1 template selected, other models unchanged, below-5.4 models
   still select nothing).

### Implementation decisions and open questions

All decisions resolved (see Resolved decisions).

### Documentation

- `application/python/agent_terminal_app/default_config/codex/README.md`
- `plugins/openai_responses/docs/development/model-discovery.md`
- `plugins/openai_responses/README.md` (reasoning-effort list)
- `docs/reference/default-config.md` (surgical row insert)

### Task checklist

- [x] Re-verify upstream hash at execution start
- [x] Step 1: dated assets + reference copies + config row
- [x] Step 2: catalog + pricing refresh, reasoning pattern, docs
- [x] Step 3: unit selection, real-API, and ChatGPT tests
- [x] Step 4: personal config port + smoke test

### Requirement verification

| Requirement | Acceptance evidence |
|---|---|
| gpt-6.1-sol dated assets + selection | Unit tests selecting the dated file for bare and `openai/`-prefixed IDs across personalities; hash provenance assertions |
| Catalog snapshot | Snapshot JSON contains gpt-6.1-sol; catalog unit test passes |
| Pricing snapshot | Pricing snapshot test passes with the gpt-6.1-sol entry and fast tier |
| Reasoning efforts | Reasoning unit tests assert the effort set, Pro mode, and context |
| Docs | README provenance; default-config reference row matches config.json |
| End-to-end delivery | Real-API and ChatGPT saved-login tests assert compiled gpt-6.1-sol instructions reach top-level instructions |
| Personal config | Smoke test through the personal config; sha-verified assets |

### Additional implementation verification

- `pytest plugins/openai_responses/tests -q`
- `pytest application/python/tests -q`
- Hosted API: new gpt-6.1-sol real-API test
- ChatGPT saved-login: new instruction test with `CHATGPT_TEST_STATE_DIR`
- `ruff check` + `black` on touched files; no new `pyright` errors

### Risks

- The test API key or saved ChatGPT login may not have gpt-6.1-sol access
  yet; if so, keep tests realistic and report the blocker.
- gpt-6.1-sol is one day past the pricing/catalog publication window;
  re-run both refreshes at execution time in case prices moved.
## Implementation Notes

- Upstream moved during execution (14a477ea89 → ca466061d6); the recorded
  gpt-6.1-sol template hash was re-verified unchanged at execution start,
  and the catalog refresh used the newer head.
- The gpt-6.1-sol cached-input price is 0.1/1M (cheaper than gpt-6-sol's
  0.2); supporting details corrected accordingly.
- The personal config had been reordered since the last migration
  (gpt-6-sol first); the new row was inserted above it.

## Completion Notes

**Outcome.** `gpt-6.1-sol` is fully wired into the default configuration
(dated `20260929` assets + reference copies, first config row, catalog and
pricing snapshots, reasoning pattern with full effort set and Pro
mode/context gating, docs) and ported into `~/.crystal` (assets + row +
README note; agent model left untouched per decision).

**Requirement evidence.**

- Assets/selection: 13 unit tests in
  `test_default_config_codex_gpt61_sol_instruction_selection.py`
  (dated selection, prefix, personality fallback, hashes, reference
  parity, row order, distinctness, bare-alias rejection).
- Catalog/pricing: snapshot tests extended and passing
  (`test_checked_in_codex_snapshot_lists_gpt_6_family_and_daybreak`,
  `test_checked_in_snapshot_has_gpt_6_family_and_no_priority_tiers` with
  gpt-6.1-sol entries).
- Reasoning: 4 new tests (effort set through `ultra`, Pro mode, context,
  request injection).
- End-to-end: real-API instruction test passed live against
  api.openai.com; ChatGPT saved-login round trip + selection-only passed
  live (saved login in `~/.crystal` is current).
- Docs: codex README (GPT-6.1 section), model-discovery note,
  openai_responses README reasoning lists, `default-config.md` row — my
  row is semantically consistent with config.json (11 remaining diffs are
  pre-existing on develop from unrelated config work: zai agent,
  token_rates, plugins list).
- Personal config: smoke test through the personal config verified
  selection (sha-verified template), prefix, personality fallback,
  unchanged older models, and bare-alias/no-below-5.4 behavior.

**Verification performed.**

- `pytest plugins/openai_responses/tests -q`: 508 passed.
- `pytest application/python/tests -q`: 559 passed, 1 skipped; one
  failure is the pre-existing
  `test_claude_system_message_helpers.py::test_default_config_claude_system_message_renders_sections_tasks_and_agents`
  (compiled claude system message no longer contains the
  "Task files are a handoff mechanism" text; verified failing on clean
  develop via stash — unrelated to this task). The known pre-existing
  `test_repo_run_script` failure was also excluded.
- Hosted API + ChatGPT saved-login gpt-6.1-sol tests passed live.
- `ruff check` + `black` clean on all touched files.

**Plan deviations and findings.** The claude system-message helper failure
on develop is a separate pre-existing issue worth its own fix (stale
expected text after recent config restructuring).

**Unresolved or deferred scope.** None for this task. The personal
`codex-openai` agent model remains `gpt-5.6-sol` by user choice; switching
to `gpt-6.1-sol` is a one-line change when wanted.
