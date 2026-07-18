# Add GPT-5.6 Codex System Instructions

Import the GPT-5.6 Codex model-specific instruction templates from current Codex upstream and wire them into default configuration for Sol, Terra, Luna, and any supported bare alias.

## Requirements checklist

- [x] Add exact upstream GPT-5.6 Codex instruction assets with source provenance.
- [x] Preserve the Sol-specific instruction variant.
- [x] Map Terra and Luna explicitly even though their templates are identical in the inspected upstream commit.
- [x] Map bare `gpt-5.6` to the Sol instruction variant if the alias is supported.
- [x] Update default-config model regex selection for OpenAI and `openai/`-prefixed IDs.
- [x] Handle default, friendly, and pragmatic personality selection without inventing text absent from upstream.
- [x] Mirror/update reference instruction assets and notices where required by the existing layout.
- [x] Add unit/default-config tests for exact model-to-template selection and fallback behavior.
- [x] Add a separate real API system-instruction integration test.
- [x] Add a separate saved-login ChatGPT system-instruction integration test and run it with credentials from `~/.crystal`.
- [x] Regenerate default-config documentation and update Codex instruction docs.
- [x] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Current layout

Relevant files:

- `application/python/agent_terminal_app/default_config/config.json`
- `application/python/agent_terminal_app/default_config/codex/`
- `application/python/agent_terminal_app/default_config/system_messages/codex/template.md`
- `application/python/agent_terminal_app/default_config/system_messages/helpers/select_codex_developer_message.py`
- `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/`
- `application/python/agent_terminal_app/default_config/codex/README.md`
- `docs/reference/default-config.md`
- `application/python/tests/test_default_config_effective_agent_configs.py`
- existing Codex real-API default-config tests under `application/python/tests/`

Default config currently has explicit default/friendly/pragmatic mappings for
`gpt-5.5` and older families, but no GPT-5.6 mapping.

## Upstream prompt findings

Source:

`../codex`, commit
`2f7d89b1419bf7064346855b0acde23514b1ebc5`,
file `codex-rs/models-manager/models.json`.

All three models include:

- `model_messages.instructions_template`;
- `model_messages.instructions_variables`;
- `base_instructions`;
- empty personality variable values for default, friendly, and pragmatic;
- no approvals block.

At the inspected commit:

| Model | Template length | SHA-256 |
| --- | ---: | --- |
| `gpt-5.6-sol` | 16,299 | `e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9` |
| `gpt-5.6-terra` | 16,270 | `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec` |
| `gpt-5.6-luna` | 16,270 | `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec` |

Sol has a distinct template. Terra and Luna are byte-identical today, but they
must remain explicit model mappings so a later upstream divergence is not
hidden.

The new GPT-5.6 instructions also materially differ from the checked-in
GPT-5.5 prompt, so reusing the GPT-5.5 directory is not acceptable.

## Implementation plan

1. Extract the exact upstream fields for each model:
   - `base_instructions`;
   - `model_messages.instructions_template`;
   - `model_messages.instructions_variables`.
2. Add model-specific directories, preferably:
   - `codex/gpt-5.6-sol/`
   - `codex/gpt-5.6-terra/`
   - `codex/gpt-5.6-luna/`
3. Keep explicit assets/mappings for all three models even if Terra/Luna files
   are generated from the same current content.
4. Add bare `gpt-5.6` mapping to Sol only if the model-catalog/API alias decision
   confirms it.
5. Add regex mappings for both unprefixed and `openai/`-prefixed IDs.
6. Preserve existing personality selection semantics:
   - use exact upstream variable values;
   - if all variants are empty/equivalent, do not invent friendly/pragmatic
     prose;
   - it is acceptable for multiple personality selections to resolve to the
     same upstream template when that is the authoritative behavior.
7. Update reference copies and notices/licenses following the existing Codex
   asset layout.
8. Regenerate `docs/reference/default-config.md`.
9. Do not update the OpenAI Responses model snapshot or reasoning controls in
   this subtask.

## Test requirements

Unit/default-config tests:

- each explicit GPT-5.6 model selects its intended instruction asset;
- bare alias selects Sol only when supported;
- `openai/gpt-5.6-*` prefixed forms select correctly;
- Sol content is distinct from Terra/Luna;
- Terra and Luna mappings are both present even if content is identical;
- default/friendly/pragmatic selection follows upstream variables without
  fabricated text;
- older model mappings remain unchanged;
- compiled top-level instructions contain a stable distinctive GPT-5.6
  substring;
- source assets match the expected upstream commit/hash or an equivalent
  provenance assertion.

Suggested existing test locations:

- `application/python/tests/test_default_config_effective_agent_configs.py`
- a focused new default-config Codex instruction selection unit test if the
  existing file would become too broad.

Separate real API integration test:

- Load the real default configuration or the same public application path used
  by existing Codex default-config tests.
- Select a GPT-5.6 model.
- Record/assert that the compiled model-specific prompt is sent as top-level
  `instructions`.
- Send a short instruction-sensitive prompt and assert the request completes.
- Gate on `OPENAI_API_KEY`.

Separate ChatGPT saved-login integration test:

- Use the default-config/system-message feature path, not a hardcoded provider
  `instructions` value.
- Use `auth_mode: "chatgpt"` and a GPT-5.6 family model.
- Record the outgoing request and assert the correct GPT-5.6 compiled
  instructions are present.
- Assert ChatGPT endpoint compatibility and successful response.
- Prefer Luna for the ordinary round-trip, but include a selection-only unit
  assertion for every family member.
- Run during implementation with:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest <chatgpt-gpt56-system-instructions-test> \
      -m "manual_integration and integration and openai" -q
  ```

- If saved credentials are unavailable or rejected, report the exact reason and
  mark the test not run.

Documentation:

- Update `application/python/agent_terminal_app/default_config/codex/README.md`.
- Update any reference instruction README/provenance notes.
- Regenerate `docs/reference/default-config.md`.
- Mention the upstream Codex commit used for the import.

## Execution plan

(Approved 2026-07-17. Implementation proceeds in the order below.)

### Upstream instruction extraction

Source: `../codex`, commit `2f7d89b1419bf7064346855b0acde23514b1ebc5` (2026-07-13), file `codex-rs/models-manager/models.json`.

For each of `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, extract three fields verbatim:
- `base_instructions` (string) -> `base_instructions.md`
- `model_messages.instructions_template` (string) -> `model_messages.instructions_template.md`
- `model_messages.instructions_variables` (object) -> `model_messages.instructions_variables.json`

Key upstream facts verified:
- For all three GPT-5.6 models: `base_instructions` == `instructions_template` (byte-identical sha256).
- No `{{ personality }}` placeholder in any GPT-5.6 template.
- All three personality variables (`personality_default`, `personality_friendly`, `personality_pragmatic`) are empty strings (len=0).
- Sol sha256: `e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9` (16299 bytes); Terra/Luna sha256: `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec` (16270 bytes).
- Sol has a 289-byte extra paragraph in the Personality section ("When presented with clarifying questions..."); Terra/Luna have that same paragraph later in the template, so it is position-distinct, not content-unique.
- GPT-5.6 distinctive opening: `"You are Codex, an agent based on GPT-5"` (vs GPT-5.5's `"You are Codex, a coding agent based on GPT-5"`).

Effective instructions: since there is no placeholder and all personality variables are empty, `instructions_default.md` == `model_messages.instructions_template.md`. Only `instructions_default.md` is created; friendly/pragmatic files are NOT created to avoid fabricating personality prose that does not exist upstream.

### Asset layout

Three separate directories under `application/python/agent_terminal_app/default_config/codex/`:
- `gpt-5.6-sol/` -- `base_instructions.md`, `model_messages.instructions_template.md`, `model_messages.instructions_variables.json`, `instructions_default.md`
- `gpt-5.6-terra/` -- same four files (content byte-identical to Luna)
- `gpt-5.6-luna/` -- same four files (content byte-identical to Terra)

`instructions_default.md` is the template verbatim (no placeholder substitution needed). `base_instructions.md` and `model_messages.instructions_template.md` are byte-identical for GPT-5.6 but both are kept to preserve the established directory shape documented in `codex/README.md`.

### Model-regex selection

Three new rows in `config.json` under `mixins.codex_developer_message.codex_developer_messages`, inserted before the existing `gpt-5.5` rows and after the `gpt-5.4` rows. The existing fallback `.*` row stays at the end.

No `personality` field in these rows (matching the `gpt-5.1-codex` pattern). This means:
- `select_codex_developer_message()` first tries `_select_matching_text(model, personality)` -- no row matches for friendly/pragmatic.
- Falls back to `_select_matching_text(model, None)` -- the no-personality row matches because `row_personality` is `None`, which is in `(None, "")`.
- All three personality selections (default, friendly, pragmatic) resolve to the same `instructions_default.md` content.

### Personality handling

Decision: do NOT create `instructions_friendly.md` or `instructions_pragmatic.md` files for GPT-5.6. Do NOT add friendly/pragmatic config rows. All three personality selections fall back to the single default row. This follows the task guidance and matches the existing `gpt-5.1-codex` pattern.

### Provenance

Update `application/python/agent_terminal_app/default_config/codex/README.md`:
- Add the GPT-5.6 family to the model list.
- Record the upstream source: `https://github.com/openai/codex`, file `codex-rs/models-manager/models.json`, commit `2f7d89b1419bf7064346855b0acde23514b1ebc5`.
- Note that GPT-5.6 templates have no `{{ personality }}` placeholder and all personality variables are empty, so only `instructions_default.md` is provided per model.
- Note that Terra/Luna are byte-identical at the inspected commit but kept as separate directories to surface future upstream divergences.

### Generated documentation

Regenerate `docs/reference/default-config.md` from the updated `config.json` by manually updating the file to match the current config (it is a manually-maintained copy wrapped in a markdown code block).

### Why prompt assets and selection belong in the application default-config/system-message layer

- The `select_codex_developer_message.py` helper and `codex/` instruction assets already live in `application/python/agent_terminal_app/default_config/`, not in `plugins/openai_responses/` or `core/python/agent_core/`.
- System messages are an application-level concern: they are compiled from config templates, runtime helpers, and file assets, then injected into the provider-native request by `SystemMessageFeature`. The provider only sees the compiled `instructions` string.
- Moving model-specific prompt assets into the provider would couple prompt content to provider code and break the existing pattern where all Codex instruction assets (gpt-5 through gpt-5.5) already live in the default-config layer.
- The core library (`agent_core`) is provider-agnostic and should not know about Codex-specific instruction templates.

### Human decisions

1. Separate Sol/Terra/Luna directories: YES. Three separate directories to preserve the per-model convention and surface future upstream divergences.
2. Identical Terra/Luna content: YES. Byte-identical at the inspected commit but both directories kept explicit.
3. Bare-alias mapping: NO. Task 010 decided NOT to add bare `gpt-5.6` alias. No bare-alias config row. The existing `.*` fallback handles unrecognized IDs.
4. Personality variants: NO separate friendly/pragmatic files or config rows. All three personalities resolve to the same `instructions_default.md` via fallback.
5. Deduplication versus explicit model assets: keep explicit model assets (separate directories and files per model). Do NOT deduplicate Terra/Luna.

### Example default-config mapping

Three new rows inserted into `codex_developer_messages` (before `gpt-5.5` rows, after `gpt-5.4` rows):

```json
{
  "model_regex": "^(openai/)?gpt-5\\.6-sol$",
  "text": "${file:${env:CONFIG_DIR}/codex/gpt-5.6-sol/instructions_default.md}"
},
{
  "model_regex": "^(openai/)?gpt-5\\.6-terra$",
  "text": "${file:${env:CONFIG_DIR}/codex/gpt-5.6-terra/instructions_default.md}"
},
{
  "model_regex": "^(openai/)?gpt-5\\.6-luna$",
  "text": "${file:${env:CONFIG_DIR}/codex/gpt-5.6-luna/instructions_default.md}"
}
```

No `personality` field -> matches as fallback for all personalities. The existing `.*` fallback row at the end is preserved.

### Exact unit/default-config tests

New test file: `application/python/tests/test_default_config_codex_gpt56_instruction_selection.py`

Tests (all non-integration, no API markers):
1. `test_gpt_56_sol_selects_sol_instruction_asset` -- model `gpt-5.6-sol` selects `codex/gpt-5.6-sol/instructions_default.md`.
2. `test_gpt_56_terra_selects_terra_instruction_asset` -- model `gpt-5.6-terra` selects `codex/gpt-5.6-terra/instructions_default.md`.
3. `test_gpt_56_luna_selects_luna_instruction_asset` -- model `gpt-5.6-luna` selects `codex/gpt-5.6-luna/instructions_default.md`.
4. `test_openai_prefixed_gpt_56_ids_select_correctly` -- `openai/gpt-5.6-sol`, `openai/gpt-5.6-terra`, `openai/gpt-5.6-luna` each select the correct model-specific asset.
5. `test_bare_gpt_56_alias_does_not_select_gpt_56_template` -- bare `gpt-5.6` (not in catalog per task 010) falls through to the `.*` fallback row, NOT a GPT-5.6 template.
6. `test_sol_content_is_distinct_from_terra_luna` -- Sol's `instructions_default.md` contains the Sol-specific paragraph position ("they feel like you understand them.\n\nWhen presented with clarifying questions") that Terra/Luna do not have at that position.
7. `test_terra_and_luna_mappings_are_both_present` -- both `gpt-5.6-terra/` and `gpt-5.6-luna/` directories exist and both have `instructions_default.md`.
8. `test_terra_and_luna_instructions_are_byte_identical` -- Terra and Luna `instructions_default.md` files have the same sha256.
9. `test_personality_selection_resolves_to_same_template` -- for `gpt-5.6-luna`, all three personalities (default, friendly, pragmatic) resolve to the same compiled text via the fallback path; no fabricated friendly/pragmatic prose.
10. `test_older_model_mappings_remain_unchanged` -- `gpt-5.5`, `gpt-5.4`, `gpt-5.2-codex`, `gpt-5.1-codex`, `gpt-5` still select their existing instruction assets.
11. `test_compiled_top_level_instructions_contain_distinctive_gpt_56_substring` -- compiled system text for `gpt-5.6-luna` contains `"You are Codex, an agent based on GPT-5"`.
12. `test_gpt_56_source_assets_match_upstream_sha256` -- `base_instructions.md` sha256 for Sol is `e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9`; for Terra/Luna is `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec`.

Update existing test `core/python/tests/test_default_system_instructions_docs.py`: `test_portable_default_config_is_self_contained` already iterates all `codex_developer_messages` rows and asserts referenced files exist; the three new GPT-5.6 rows will be automatically covered. No change needed, but verify it passes.

### Separate real API and saved-login ChatGPT tests

Real API test -- new file `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_real_api.py`:
- Use `AgentApplication` with the default config.
- Create a session with `codex-openai` agent.
- Override model to `gpt-5.6-luna` (or env var `OPENAI_CODEX_GPT56_TEST_MODEL`).
- Send a short instruction-sensitive prompt.
- Assert the request completes and the assistant replies.
- Assert the compiled system text from the session contains `"You are Codex, an agent based on GPT-5"`.
- Gate on `OPENAI_API_KEY` via `get_repo_env("OPENAI_API_KEY")`.
- Markers: `@pytest.mark.integration`, `@pytest.mark.api`, `@pytest.mark.openai`.

ChatGPT saved-login test -- new file `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_chatgpt_manual_integration.py`:
- Use the default-config/system-message feature path: `AgentApplication` with the default config to compile the system message for a GPT-5.6 model (prefer Luna).
- Extract the compiled system message from the session's system message metadata.
- Use a recording `_RecordingChatGPTProvider` (subclass of `OpenAIResponsesProvider`) with `auth_mode: "chatgpt"`, ChatGPT credentials from `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`, and the extracted compiled system message as `system_message`.
- Send a short prompt and record the outgoing request.
- Assert the recorded request's `instructions` field contains the GPT-5.6 distinctive substring.
- Assert ChatGPT endpoint compatibility: the response completes successfully and `metadata.usage_effective_auth_mode == "chatgpt"`.
- Include a selection-only unit assertion for every family member (Sol, Terra, Luna).
- Credential gate: skip with exact reason on missing file, non-dict JSON, missing/blank `access_token`, or expired `expires_at`. Never print tokens/account/email.
- Markers: `pytestmark = pytest.mark.api`; per-test `@pytest.mark.manual_integration`, `@pytest.mark.integration`, `@pytest.mark.openai`.
- Implementation run:
  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_chatgpt_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```

### Exact prompt assets, notices, READMEs, reference copies, and generated default-config documentation to update

New files:
- `application/python/agent_terminal_app/default_config/codex/gpt-5.6-sol/` (4 files)
- `application/python/agent_terminal_app/default_config/codex/gpt-5.6-terra/` (4 files)
- `application/python/agent_terminal_app/default_config/codex/gpt-5.6-luna/` (4 files)
- `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/gpt-5.6-sol/` (4 reference copies)
- `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/gpt-5.6-terra/` (4 reference copies)
- `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/gpt-5.6-luna/` (4 reference copies)
- `application/python/tests/test_default_config_codex_gpt56_instruction_selection.py`
- `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_real_api.py`
- `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_chatgpt_manual_integration.py`

Modified files:
- `application/python/agent_terminal_app/default_config/config.json` -- add three GPT-5.6 rows.
- `application/python/agent_terminal_app/default_config/codex/README.md` -- add GPT-5.6 family, record upstream commit, note no-personality-placeholder behavior.
- `docs/reference/default-config.md` -- regenerate from updated `config.json`.

Not updated (out of scope):
- `codex/LICENSE` and `codex/NOTICE` -- already cover all Codex-derived assets.
- Reference directory `README.md` -- already describes the per-model layout. The reference directory is missing `gpt-5.5` (pre-existing gap, not introduced by this task). GPT-5.6 reference copies are added; `gpt-5.5` is NOT backfilled.

### Implementation order

1. Extract the three GPT-5.6 models' `base_instructions`, `instructions_template`, and `instructions_variables` from `../codex` at commit `2f7d89b` into the three live `codex/gpt-5.6-*/` directories. Generate `instructions_default.md` as the template verbatim.
2. Add the three reference copies under `system_messages/reference/default-system-instructions/codex/gpt-5.6-*/`.
3. Add the three GPT-5.6 rows to `config.json` (before the `gpt-5.5` rows, after `gpt-5.4`).
4. Update `codex/README.md` with GPT-5.6 family, upstream commit, and no-placeholder note.
5. Add the unit/default-config test file.
6. Add the real API test file.
7. Add the ChatGPT saved-login test file.
8. Regenerate `docs/reference/default-config.md` from the updated `config.json`.
9. Run the fast default application test suite.
10. Run the real API test (if `OPENAI_API_KEY` available).
11. Run the ChatGPT saved-login test with `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"`.
12. Run `ruff check` and `black` on new test files.
13. Append `## Completion Notes` and update `000-main.md` checklist.

### Verification commands

- Fast default: `pytest application/python/tests -q`
- Unit tests only: `pytest application/python/tests/test_default_config_codex_gpt56_instruction_selection.py -q`
- Existing default-config docs test: `pytest core/python/tests/test_default_system_instructions_docs.py -q`
- Real API: `pytest application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_real_api.py -m "integration and api and not slow_integration and openai" -q`
- ChatGPT saved-login:
  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_chatgpt_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```
- Lint/format: `ruff check <new test files>` and `black <new test files>`

### Risks

- Saved ChatGPT login expiry: valid through `2026-07-18T19:42:08Z` at investigation time. If expired, the ChatGPT test will skip with an exact reason and must be reported as not run.
- `OPENAI_API_KEY` availability: present in repo root `.env`, loaded by `application/python/tests/conftest.py`. If not available, the real API test will skip.
- Upstream template drift: future upstream Codex commits may change GPT-5.6 templates. The sha256 provenance assertions will catch this.
- Reference directory pre-existing gap: missing `gpt-5.5` (pre-existing). This task adds `gpt-5.6` reference copies but does not backfill `gpt-5.5`.
- `docs/reference/default-config.md` staleness: the existing file is already stale. The task asks to regenerate it, so updating it to match the current `config.json` will fix pre-existing staleness as a side effect.
- Two-step ChatGPT test approach: uses `AgentApplication` to compile the system message, then a recording provider to send the request. This tests compilation and transmission separately. An alternative would be to monkey-patch the provider inside `AgentApplication`, but that is more fragile.

### Prerequisite assumptions

- Task 010's decision to NOT add bare `gpt-5.6` alias is accepted and final.
- Task 010's refreshed checked-in snapshot contains all three GPT-5.6 family IDs.
- The upstream codex commit `2f7d89b1419bf7064346855b0acde23514b1ebc5` is available in the local `../codex` checkout.
- Provider model discovery and reasoning behavior are out of scope (owned by tasks 010, 020, 030, 040).
- Pricing and cost estimation are out of scope (owned by task 050).

## Completion Notes

(Added 2026-07-18 during completion.)

### What was done

- Extracted the three GPT-5.6 models' `base_instructions`, `instructions_template`, and `instructions_variables` from `../codex` at commit `2f7d89b1419bf7064346855b0acde23514b1ebc5` into three live `codex/gpt-5.6-*/` directories. Each directory contains `base_instructions.md`, `model_messages.instructions_template.md`, `model_messages.instructions_variables.json`, and `instructions_default.md`. For GPT-5.6, `base_instructions` == `instructions_template` == `instructions_default.md` (no `{{ personality }}` placeholder, all personality variables empty).
  - `gpt-5.6-sol` sha256: `e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9` (16299 bytes)
  - `gpt-5.6-terra` sha256: `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec` (16270 bytes)
  - `gpt-5.6-luna` sha256: `78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec` (16270 bytes, byte-identical to Terra)
- Added three reference copies under `system_messages/reference/default-system-instructions/codex/gpt-5.6-*/` with the same four files each.
- Added three GPT-5.6 rows to `config.json` under `mixins.codex_developer_message.codex_developer_messages`, inserted before the `gpt-5.5` rows. Each row has no `personality` field, so all three personality selections (default, friendly, pragmatic) resolve to the same `instructions_default.md` via the fallback path in `select_codex_developer_message.py`.
- Updated `application/python/agent_terminal_app/default_config/codex/README.md` with:
  - GPT-5.6 family in the model list.
  - Upstream source provenance: commit `2f7d89b1419bf7064346855b0acde23514b1ebc5` for GPT-5.6, `c10f95ddac7b35095d334dece2ebcf69bcde61fc` for gpt-5.5, `39869f74435cb199d56ca5d53cf198f7c5332eec` for older models.
  - Note that GPT-5.6 templates have no `{{ personality }}` placeholder and all personality variables are empty, so only `instructions_default.md` is provided per model.
  - Note that Terra/Luna are byte-identical at the inspected commit but kept as separate directories.
  - Note that the bare `gpt-5.6` alias is intentionally not mapped.
- Added `manual_integration` marker to `application/python/pyproject.toml` pytest config to avoid `PytestUnknownMarkWarning` for the ChatGPT saved-login test.
- Created `application/python/tests/test_default_config_codex_gpt56_instruction_selection.py` with 12 unit tests:
  - `test_gpt_56_sol_selects_sol_instruction_asset`
  - `test_gpt_56_terra_selects_terra_instruction_asset`
  - `test_gpt_56_luna_selects_luna_instruction_asset`
  - `test_openai_prefixed_gpt_56_ids_select_correctly`
  - `test_bare_gpt_56_alias_does_not_select_gpt_56_template`
  - `test_sol_content_is_distinct_from_terra_luna`
  - `test_terra_and_luna_mappings_are_both_present`
  - `test_terra_and_luna_instructions_are_byte_identical`
  - `test_personality_selection_resolves_to_same_template`
  - `test_older_model_mappings_remain_unchanged`
  - `test_compiled_top_level_instructions_contain_distinctive_gpt_56_substring`
  - `test_gpt_56_source_assets_match_upstream_sha256`
- Created `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_real_api.py` with 1 real API test:
  - `test_default_config_codex_gpt56_luna_system_instructions_real_api` — uses `AgentApplication` with the default config, `codex-openai-api` agent (which has `system_message_as_instructions: false`), overrides the agent base config model to `gpt-5.6-luna` before session creation so `SystemMessageFeature` stamps the GPT-5.6 compiled content, sends a short prompt, asserts the compiled system text contains `"You are Codex, an agent based on GPT-5"`, and asserts the assistant replies with the expected marker. Gated on `OPENAI_API_KEY`.
- Created `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_chatgpt_manual_integration.py` with 2 ChatGPT saved-login tests:
  - `test_openai_responses_chatgpt_gpt56_system_instructions_round_trip` — uses `AgentApplication` with the default config to compile the system message for `gpt-5.6-luna` (via `select_codex_developer_message` helper), then uses a recording `_RecordingChatGPTProvider` with `auth_mode: "chatgpt"` and the compiled system message as `system_message`. Asserts the recorded request's `instructions` field contains `"You are Codex, an agent based on GPT-5"`, asserts the assistant replies, and asserts `metadata.usage_effective_auth_mode == "chatgpt"`.
  - `test_openai_responses_chatgpt_gpt56_family_selection_only` — selection-only unit assertion for every family member (Sol, Terra, Luna): verifies the compiled system message contains the GPT-5.6 distinctive substring, Sol is distinct from Terra/Luna, and Terra == Luna.
- Regenerated `docs/reference/default-config.md` from the updated `config.json`.

### Human decisions recorded

- Separate Sol/Terra/Luna directories: YES. Three separate directories to preserve the per-model convention and surface future upstream divergences.
- Identical Terra/Luna content: YES. Byte-identical at the inspected commit but both directories kept explicit.
- Bare-alias mapping: NO. Task 010 decided NOT to add bare `gpt-5.6` alias. No bare-alias config row. The existing `.*` fallback handles unrecognized IDs. The bare `gpt-5.6` falls through to the `gpt-5/instructions_default.md` fallback, verified by `test_bare_gpt_56_alias_does_not_select_gpt_56_template`.
- Personality variants: NO separate friendly/pragmatic files or config rows. All three personalities resolve to the same `instructions_default.md` via fallback. Verified by `test_personality_selection_resolves_to_same_template`.
- Deduplication versus explicit model assets: keep explicit model assets (separate directories and files per model). Do NOT deduplicate Terra/Luna.
- Real API test agent: used `codex-openai-api` (which has `system_message_as_instructions: false`) instead of `codex-openai` (which has `system_message_as_instructions: true`) because the former keeps the system message with `compiled_content` in the provider-native history for inspection. The model is overridden in the agent base config before session creation so `SystemMessageFeature` stamps the GPT-5.6 compiled content.

### Verification commands and results

All commands run with `/Users/ferenci84/Dev/Mine/ai-agent-platform/.venv/bin/python -m pytest`.

1. Unit/default-config tests:
   ```
   pytest application/python/tests/test_default_config_codex_gpt56_instruction_selection.py -q
   ```
   Result: 12 passed in 0.07s.

2. Existing default-config docs tests:
   ```
   pytest core/python/tests/test_default_system_instructions_docs.py -q
   ```
   Result: 9 passed in 0.37s.

3. Real API GPT-5.6 system-instruction test:
   ```
   pytest application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_real_api.py -m "integration and api and not slow_integration and openai" -q
   ```
   Result: 1 passed in 25.90s. `OPENAI_API_KEY` was loaded from repo root `.env` by `application/python/tests/conftest.py` via `load_repo_root_env()`. The API request completed successfully with `gpt-5.6-luna`, and the compiled system text contained `"You are Codex, an agent based on GPT-5"`.

4. ChatGPT saved-login system-instruction tests:
   ```
   CHATGPT_TEST_STATE_DIR="$HOME/.crystal" OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
     pytest application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_chatgpt_manual_integration.py \
       -m "manual_integration and integration and openai" -q
   ```
   Result: 2 passed in 4.89s. The saved login at `~/.crystal/auth/chatgpt-auth.json` was valid. The ChatGPT request completed successfully with `gpt-5.6-luna`, the recorded request's `instructions` field contained `"You are Codex, an agent based on GPT-5"`, and `metadata.usage_effective_auth_mode == "chatgpt"`.

5. Lint/format:
   ```
   ruff check <new test files>
   ```
   Result: All checks passed.
   ```
   black <new test files>
   ```
   Result: 3 files reformatted (test files only; no source files changed).

### Credential/API gating report

- `OPENAI_API_KEY`: available in repo root `.env`, loaded by `application/python/tests/conftest.py` via `load_repo_root_env()`. Real API test ran and passed. Not skipped.
- ChatGPT saved login at `~/.crystal/auth/chatgpt-auth.json`: present and valid. ChatGPT tests ran and passed. Not skipped.
- No credentials were printed during verification. The ChatGPT test's credential gate checks `access_token` presence and `expires_at` validity without printing token values.

### Risks confirmed

- The saved ChatGPT login was valid at verification time. If it expires later, the ChatGPT tests will skip with an exact reason and must be reported as not run.
- The reference directory is missing `gpt-5.5` (pre-existing gap, not introduced by this task). GPT-5.6 reference copies were added; `gpt-5.5` was NOT backfilled.
- `docs/reference/default-config.md` was regenerated to match the current `config.json`, which also fixed pre-existing staleness (e.g., `z-ai/glm-5` -> `z-ai/glm-5.2`, missing `glm-ollama` agent) as a side effect.
- The real API test overrides the `codex-openai-api` agent's base config model before session creation and restores it afterward. This is necessary because `SystemMessageFeature._stamp_compiled_content_once` only stamps once (during session creation), so the model must be set before the session is created.

### Files changed

- `application/python/agent_terminal_app/default_config/codex/gpt-5.6-sol/` (new directory: `base_instructions.md`, `model_messages.instructions_template.md`, `model_messages.instructions_variables.json`, `instructions_default.md`)
- `application/python/agent_terminal_app/default_config/codex/gpt-5.6-terra/` (new directory: same four files)
- `application/python/agent_terminal_app/default_config/codex/gpt-5.6-luna/` (new directory: same four files)
- `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/gpt-5.6-sol/` (new reference directory: same four files)
- `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/gpt-5.6-terra/` (new reference directory: same four files)
- `application/python/agent_terminal_app/default_config/system_messages/reference/default-system-instructions/codex/gpt-5.6-luna/` (new reference directory: same four files)
- `application/python/agent_terminal_app/default_config/config.json` (added three GPT-5.6 rows to `codex_developer_messages`)
- `application/python/agent_terminal_app/default_config/codex/README.md` (added GPT-5.6 family, upstream commit provenance, no-placeholder note)
- `application/python/pyproject.toml` (added `manual_integration` pytest marker)
- `docs/reference/default-config.md` (regenerated from updated `config.json`)
- `application/python/tests/test_default_config_codex_gpt56_instruction_selection.py` (new file, 12 unit tests)
- `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_real_api.py` (new file, 1 real API test)
- `application/python/tests/test_terminal_default_config_codex_gpt56_system_instructions_chatgpt_manual_integration.py` (new file, 2 ChatGPT saved-login tests)
- `tasks/20260713-openai-responses-gpt-5-6-support/060-add-gpt56-codex-system-instructions.md` (this file: execution plan + completion notes)
