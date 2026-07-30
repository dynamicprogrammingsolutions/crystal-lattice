# Refresh the GPT-5.6 Model Catalog

Refresh the checked-in OpenAI Codex model snapshot and make GPT-5.6 model discovery reliable for both API and ChatGPT authentication paths, including offline/fallback behavior.

## Requirements checklist

- [x] Refresh the checked-in Codex model snapshot from a pinned current upstream commit.
- [x] Include `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` with correct names and descriptions.
- [x] Preserve the documented discovery precedence: manual models, checked-in snapshot, then live Codex catalog.
- [x] Keep ChatGPT discovery usable when live GitHub catalog access fails.
- [x] Decide and document whether the bare `gpt-5.6` alias should appear in the UI; do not invent it if authoritative discovery does not publish it.
- [x] Add or update unit tests for snapshot generation, normalization, merge precedence, and fallback behavior.
- [x] Add a separate real API model-discovery integration test.
- [x] Add a separate saved-login ChatGPT model-discovery integration test and run it with `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"`.
- [x] Update model-discovery documentation and checked-in snapshot provenance.
- [x] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Current behavior

Relevant code:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_codex_models.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/data/openai_codex_models.json`
- `plugins/openai_responses/src/openai_responses_plugins/data/openai_chatgpt_manual_models.json`
- `scripts/refresh_openai_responses_models.py`
- `plugins/openai_responses/tests/test_openai_responses_codex_models_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`

The checked-in snapshot was fetched on April 24, 2026 and stops at `gpt-5.5`.
Running the existing refresh script to a temporary path on July 13, 2026
successfully produced all three GPT-5.6 family entries and recorded upstream
commit `2f7d89b1419bf7064346855b0acde23514b1ebc5`.

The snapshot intentionally normalizes upstream entries to minimal model
descriptors:

```json
{
  "id": "gpt-5.6-sol",
  "name": "GPT-5.6-Sol",
  "description": "Latest frontier agentic coding model."
}
```

Do not expand this subtask into reasoning-configuration implementation.
Model-specific reasoning capability controls are owned by
`tasks/20260713-openai-responses-gpt-5-6-support/020-add-reasoning-effort-levels.md`.
If richer descriptor metadata is judged necessary for future capability-driven
UI, record that as a deliberate design decision rather than changing the public
descriptor shape incidentally.

## ChatGPT discovery findings

In ChatGPT mode, `OpenAIResponsesProvider._fetch_chatgpt_discovery_models()`:

1. validates the saved ChatGPT credentials;
2. loads manual model descriptors;
3. loads the checked-in snapshot;
4. fetches the live public Codex catalog;
5. merges manual, snapshot, and live descriptors;
6. only calls ChatGPT `/models` if the live Codex fetch failed and there is no
   snapshot.

A live saved-login check on July 13, 2026 returned:

```text
merged_count=9
gpt_56_ids=['gpt-5.6-luna', 'gpt-5.6-sol', 'gpt-5.6-terra']
```

The direct ChatGPT endpoint
`https://chatgpt.com/backend-api/codex/models?client_version=0.1.0` returned an
empty `models` list. Therefore:

- the user's observation that GPT-5.6 is already visible is correct;
- it is visible because the live Codex GitHub catalog is preferred;
- refreshing the checked-in snapshot is still required for offline and GitHub
  failure fallback;
- tests must not falsely require the direct ChatGPT `/models` endpoint to list
  GPT-5.6.

## Implementation plan

1. Run `scripts/refresh_openai_responses_models.py` against the authoritative
   upstream Codex catalog.
2. Review the generated diff and pin the recorded source commit.
3. Confirm the snapshot contains the three family IDs and retains existing
   entries expected by current tests.
4. Preserve current merge precedence and fallback semantics.
5. Evaluate the bare `gpt-5.6` alias:
   - OpenAI examples use it and describe it as routing to Sol.
   - The inspected Codex catalog publishes only the three explicit family IDs.
   - Prefer authoritative discovery behavior; if the alias is added manually,
     document why and ensure it does not override an authoritative descriptor.
6. Update README model-discovery documentation with the ChatGPT-specific source
   and fallback behavior.

## Test requirements

Unit tests:

- Extend `test_openai_responses_codex_models_unit.py` to verify generated
  snapshots preserve:
  - all three GPT-5.6 IDs;
  - source commit metadata;
  - deterministic sorting;
  - model names and descriptions.
- Extend `test_openai_responses_provider_unit.py` to verify:
  - live Codex descriptors override stale snapshot/manual descriptors;
  - refreshed snapshot supplies all three GPT-5.6 models when live fetch fails;
  - manual models only fill gaps;
  - ChatGPT `/models` fallback is not called when a snapshot is available;
  - an empty ChatGPT `/models` payload normalizes safely if that last-resort
    branch is exercised.

Separate real API integration test:

- Add or update a test that calls API-authenticated `get_models()`.
- Assert the explicit GPT-5.6 family IDs expected from the GA API are present.
- Gate on `OPENAI_API_KEY`.
- Do not merge this into the ChatGPT test through auth-mode parametrization.

Separate ChatGPT saved-login integration test:

- Add a dedicated test function or module marked:
  `manual_integration`, `integration`, `openai`, and `api`.
- Use `CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`.
- Call provider `get_models()` with `auth_mode: "chatgpt"`.
- Assert `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` are visible.
- Do not assert that the direct ChatGPT `/models` endpoint itself returned them.
- During implementation run with:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
    pytest <chatgpt-model-discovery-test> \
      -m "manual_integration and integration and openai" -q
  ```

Documentation:

- Update `plugins/openai_responses/README.md` model-discovery section.
- Document the live-Codex/snapshot/manual precedence and the last-resort
  ChatGPT `/models` behavior.
- Record snapshot refresh command and upstream commit.

## Execution plan

(Approved 2026-07-13. Implementation proceeds in the order below.)

### Catalog sources, discovery precedence, snapshot generation, fallback

Catalog sources (ChatGPT auth path, `OpenAIResponsesProvider._fetch_chatgpt_discovery_models` at `openai_responses_provider.py:761`):

1. Manual fallback models — `data/openai_chatgpt_manual_models.json` (currently only `gpt-5.5`).
2. Checked-in Codex snapshot — `data/openai_codex_models.json` (stale April 24, 2026; stops at `gpt-5.5`).
3. Live Codex GitHub catalog — `https://raw.githubusercontent.com/openai/codex/{commit}/codex-rs/models-manager/models.json`, commit resolved via `https://api.github.com/repos/openai/codex/commits/main`.
4. ChatGPT `/models` endpoint — `https://chatgpt.com/backend-api/codex/models?client_version=0.1.0`, last resort only.

Discovery precedence (preserved, unchanged):

- Merge order is manual -> snapshot -> live Codex; later sources override earlier per-id via `merge_model_descriptors` (`openai_responses_codex_models.py:228`).
- If live Codex succeeds: return `merge(manual, snapshot, live)`. ChatGPT `/models` is not called.
- If live Codex fails and snapshot is non-empty: return `merge(manual, snapshot)`. ChatGPT `/models` is not called.
- If live Codex fails and snapshot is empty: return `merge(manual, normalize(chatgpt /models))`.

Snapshot generation (`scripts/refresh_openai_responses_models.py` -> `build_live_snapshot_payload`):

- Resolve latest `openai/codex` main commit SHA.
- Fetch `models.json` at that commit (fallback to `main` raw URL if commit lookup fails).
- Normalize each entry to `{id, name, description}` via `normalize_model_descriptor` (already maps `slug` -> `id`, `display_name` -> `name`).
- Emit `{version: 1, fetched_at, source_base_url, source_commit, models: {id: descriptor, sorted}}`.

Fallback behavior: the current provider code already implements the precedence and fallback correctly. The only gap is the stale snapshot, which after refresh will carry all three GPT-5.6 IDs so offline/GitHub-failure mode shows them.

### Where changes belong

- Catalog loader (`openai_responses_codex_models.py`): no source changes required. `normalize_model_descriptor` already handles `slug`/`display_name`, and `build_snapshot_payload` already records `source_commit`. Only tests added.
- Provider discovery code (`openai_responses_provider.py`): no source changes required. `_fetch_chatgpt_discovery_models` already implements the required precedence and fallback. Only tests added.
- Generated snapshot (`data/openai_codex_models.json`): refresh via the script. Expected new content: 8 entries (`codex-auto-review`, `gpt-5.2`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.5`, `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`), `fetched_at` = current run time, `source_commit` = `2f7d89b1419bf7064346855b0acde23514b1ebc5`. `gpt-5.3-codex` is no longer in upstream and will be dropped (verified no tests depend on the checked-in snapshot content).
- Documentation (`plugins/openai_responses/README.md`): update the "ChatGPT model-discovery precedence" section (lines 242-246), the snapshot data-file entry (lines 234-237), and the "Capabilities and caveats" ChatGPT `/models` note (line 621).

### Human decisions (with recommendations)

Bare `gpt-5.6` alias: do not add it. The inspected Codex catalog publishes only `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`. The task says "do not invent it if authoritative discovery does not publish it." OpenAI examples use `gpt-5.6` as a routing alias to Sol, but that is an API-layer convention, not a catalog entry. Document the decision in the README and in `## Completion Notes`.

Authoritative source precedence: keep current precedence — live Codex > snapshot > manual. The live Codex catalog is the most authoritative. The snapshot is a pinned fallback. Manual models are gap-fill only.

Offline behavior: keep current fallback chain. After the snapshot refresh, offline mode (live Codex fetch fails, snapshot non-empty) returns `merge(manual, snapshot)` which will include all three GPT-5.6 IDs from the snapshot. ChatGPT `/models` is only contacted when both live Codex and snapshot are unavailable.

### Exact unit tests

`test_openai_responses_codex_models_unit.py` — add:

- `test_normalize_model_descriptor_maps_slug_and_display_name`
- `test_normalize_model_descriptor_drops_blank_or_missing_id`
- `test_normalize_models_payload_rejects_non_list_models`
- `test_merge_model_descriptors_preserves_earlier_only_ids_and_sorts`
- `test_build_snapshot_payload_records_source_commit_and_sorts` (realistic GPT-5.6 fixture with `slug`/`display_name`)
- `test_build_snapshot_payload_omits_source_commit_when_absent`
- `test_refresh_models_snapshot_preserves_gpt_5_6_family`

`test_openai_responses_provider_unit.py` — add:

- `test_get_models_live_codex_overrides_stale_snapshot_and_manual_for_gpt_5_6`
- `test_get_models_snapshot_supplies_all_three_gpt_5_6_when_live_fetch_fails`
- `test_get_models_does_not_call_chatgpt_models_endpoint_when_snapshot_available`
- `test_get_models_handles_empty_chatgpt_models_payload`
- `test_get_models_manual_models_only_fill_gaps`

### Separate real API and saved-login ChatGPT discovery tests

Real API test — update `test_openai_responses_provider_integration.py`:

- Add `test_openai_responses_get_models_includes_gpt_5_6_family_real_api` gated on `OPENAI_API_KEY` via the existing `ensure_openai_api_key` fixture. Assert `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` are present in `provider.get_models({...})` IDs. No ChatGPT auth parametrization. Markers: `integration`, `openai`, `api`.

ChatGPT saved-login test — new file `test_openai_responses_chatgpt_model_discovery_manual_integration.py`:

- Markers: `pytestmark = pytest.mark.api`; per-test `@pytest.mark.manual_integration`, `@pytest.mark.integration`, `@pytest.mark.openai`.
- Credential path: `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json` (fall back to `plugins/chatgpt-auth-app/tests/.manual-state`).
- Credential gate: skip with exact reason on `FileNotFoundError`, non-dict JSON, missing/blank `access_token`, or expired `expires_at`. Never print tokens/account/email.
- Test body: `provider.get_models({"auth_mode": "chatgpt", "chatgpt_credentials_path": str(path), "timeout": 120})`; assert IDs include `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`. Do not assert against the direct ChatGPT `/models` endpoint.
- Implementation run: `CHATGPT_TEST_STATE_DIR="$HOME/.crystal" pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_model_discovery_manual_integration.py -m "manual_integration and integration and openai" -q`.
- If credentials are missing/expired on run, report as not run with the exact skip reason, not as a pass.

### Generated files and documentation to update

- Generated: `plugins/openai_responses/src/openai_responses_plugins/data/openai_codex_models.json` (refreshed; 8 entries; new `fetched_at`; `source_commit: 2f7d89b1419bf7064346855b0acde23514b1ebc5`).
- No change: `data/openai_chatgpt_manual_models.json` (keep `gpt-5.5` only; do not add bare `gpt-5.6`).
- Docs: `plugins/openai_responses/README.md` — update "ChatGPT model-discovery precedence" (lines 242-246), snapshot data-file entry (lines 234-237), "Capabilities and caveats" ChatGPT `/models` note (line 621), and add a short note that the bare `gpt-5.6` alias is intentionally not published in the UI.

### Implementation order

1. Run `python scripts/refresh_openai_responses_models.py` to regenerate the snapshot; review the diff.
2. Verify the refreshed snapshot contains all three GPT-5.6 IDs, the expected names/descriptions, and `source_commit`.
3. Add the normalization, merge-precedence, and snapshot-provenance unit tests in `test_openai_responses_codex_models_unit.py`.
4. Add the fallback-behavior unit tests in `test_openai_responses_provider_unit.py`.
5. Add the real API GPT-5.6 family assertion test in `test_openai_responses_provider_integration.py`.
6. Create `test_openai_responses_chatgpt_model_discovery_manual_integration.py`.
7. Update `plugins/openai_responses/README.md`.
8. Run the fast default plugin suite.
9. Run the ChatGPT saved-login discovery test with `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"`.
10. Run the real API discovery test if `OPENAI_API_KEY` is available; otherwise report as not run with the exact reason.
11. Append `## Completion Notes` to this task file and update `000-main.md` checklist.

### Verification commands

- Fast default: `pytest plugins/openai_responses/tests -q`
- Real API: `pytest plugins/openai_responses/tests -m 'integration and api and not slow_integration and openai' -q` (specifically the `get_models` GPT-5.6 test)
- ChatGPT saved-login: `CHATGPT_TEST_STATE_DIR="$HOME/.crystal" pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_model_discovery_manual_integration.py -m 'manual_integration and integration and openai' -q`

### Risks

- The refreshed snapshot drops `gpt-5.3-codex` (removed from upstream). Verified no tests depend on the checked-in snapshot content; all provider unit tests monkey-patch the loader. Low risk.
- The saved ChatGPT login expires `2026-07-18T19:42:08Z`. If implementation runs after that, the ChatGPT discovery test will skip with an exact reason and must be reported as not run, not as a pass.
- The ChatGPT `/models` endpoint returned an empty list at investigation time. The new ChatGPT integration test must not assert against that endpoint's content; it only asserts `get_models()` returns the GPT-5.6 family (sourced from live Codex or snapshot).
- `OPENAI_API_KEY` is present in repo root `.env` but not exported in the current shell. The plugin `conftest.py` loads repo root `.env`, so the real API test should pick it up. If not, report as not run.
- Lint/typecheck: `ruff check` and `black` on any new test files.

### Unresolved discovery questions (flagged in completion notes, not blocking)

- Should a bare `gpt-5.6` UX alias be added later as a deliberate manual-models convenience? Recommendation: no, revisit as a separate follow-up if the API publishes it or if UX feedback asks for it.
- Should the snapshot carry richer descriptor metadata (context window, supported reasoning efforts) for future capability-driven UI? Out of scope here; reasoning capabilities are owned by subtask 020. Recording the current minimal `{id, name, description}` shape as a deliberate design decision.
- Should the refresh script optionally pin to a specific commit for reproducibility? Currently it always fetches latest main and records the commit. The checked-in snapshot is the pinned artifact. No change recommended for this task.

## Completion Notes

(Added 2026-07-17 during completion.)

### What was done

- Refreshed `plugins/openai_responses/src/openai_responses_plugins/data/openai_codex_models.json` via `python scripts/refresh_openai_responses_models.py` using the repo `.venv` Python.
  - `fetched_at`: `2026-07-17T20:51:17+00:00`
  - `source_commit`: `50b82133850d940627cf307d77e280619bfafe25` (latest `openai/codex` `main` at run time, 2026-07-17; newer than the July 13 investigation commit `2f7d89b1419bf7064346855b0acde23514b1ebc5` but contains the same 8 model entries and the same GPT-5.6 family).
  - 8 entries: `codex-auto-review`, `gpt-5.2`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.5`, `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`.
  - `gpt-5.3-codex` was removed from upstream between the April 24 snapshot and the July 17 refresh; it is no longer in the snapshot. No tests depended on the checked-in snapshot content (all provider unit tests monkey-patch the loader).
  - GPT-5.6 names/descriptions: `GPT-5.6-Sol` / "Latest frontier agentic coding model.", `GPT-5.6-Terra` / "Balanced agentic coding model for everyday work.", `GPT-5.6-Luna` / "Fast and affordable agentic coding model."
- No source changes to `openai_responses_codex_models.py` or `openai_responses_provider.py`. The existing `normalize_model_descriptor` (maps `slug`->`id`, `display_name`->`name`), `build_snapshot_payload` (records `source_commit`), `merge_model_descriptors` (later sources override earlier per-id), and `_fetch_chatgpt_discovery_models` (manual -> snapshot -> live Codex, last-resort ChatGPT `/models` only when snapshot empty) already implement the required behavior.
- Added unit tests to `test_openai_responses_codex_models_unit.py`:
  - `test_normalize_model_descriptor_maps_slug_and_display_name`
  - `test_normalize_model_descriptor_drops_blank_or_missing_id` (parametrized)
  - `test_normalize_models_payload_rejects_non_list_models`
  - `test_merge_model_descriptors_preserves_earlier_only_ids_and_sorts`
  - `test_build_snapshot_payload_records_source_commit_and_sorts` (realistic GPT-5.6 fixture with `slug`/`display_name`)
  - `test_build_snapshot_payload_omits_source_commit_when_absent`
  - `test_refresh_models_snapshot_preserves_gpt_5_6_family`
- Added unit tests to `test_openai_responses_provider_unit.py`:
  - `test_get_models_live_codex_overrides_stale_snapshot_and_manual_for_gpt_5_6`
  - `test_get_models_snapshot_supplies_all_three_gpt_5_6_when_live_fetch_fails` (also asserts ChatGPT `/models` is not called)
  - `test_get_models_does_not_call_chatgpt_models_endpoint_when_snapshot_available`
  - `test_get_models_handles_empty_chatgpt_models_payload`
  - `test_get_models_manual_models_only_fill_gaps`
- Added real API integration test `test_openai_responses_get_models_includes_gpt_5_6_family_real_api` in `test_openai_responses_provider_integration.py`, gated on `OPENAI_API_KEY` via the existing `ensure_openai_api_key` fixture. Markers: `integration`, `openai`, `api`.
- Created `test_openai_responses_chatgpt_model_discovery_manual_integration.py` with `test_openai_responses_chatgpt_model_discovery_includes_gpt_5_6_family`. Markers: `manual_integration`, `integration`, `openai`, `api`. Credential gate skips with exact reason on missing file, non-dict JSON, missing/blank `access_token`, or expired `expires_at`. Never prints tokens/account/email. Asserts `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` are present in `get_models()`; does not assert against the direct ChatGPT `/models` endpoint.
- Updated `plugins/openai_responses/README.md`:
  - "ChatGPT model-discovery precedence" section now explicitly documents manual -> snapshot -> live Codex order, the authoritative-source statement, the last-resort ChatGPT `/models` behavior (only when snapshot empty), and the observation that the endpoint has returned an empty list even when upstream lists GPT-5.6.
  - Snapshot data-file entry now records the refresh command, the current `source_commit`, and the included GPT-5.6 family IDs.
  - "Capabilities and caveats" ChatGPT `/models` note corrected to state it is a last-resort fallback, not a primary source.
  - Added a note that the bare `gpt-5.6` alias is intentionally not published in the UI because authoritative discovery does not list it; users can still type it manually.

### Human decisions recorded

- Bare `gpt-5.6` alias: not added. The inspected Codex catalog publishes only `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`. OpenAI examples use `gpt-5.6` as a routing alias to Sol, but that is an API-layer convention, not a catalog entry. Documented in README and here. Revisit as a separate follow-up if UX feedback asks for it.
- Authoritative source precedence: kept current — live Codex > snapshot > manual.
- Offline behavior: kept current fallback chain. After refresh, offline mode (live Codex fails, snapshot non-empty) returns `merge(manual, snapshot)` which includes all three GPT-5.6 IDs. ChatGPT `/models` is only contacted when both live Codex and snapshot are unavailable.
- Snapshot descriptor shape: kept minimal `{id, name, description}`. Richer metadata (context window, supported reasoning efforts) is out of scope; reasoning capabilities are owned by subtask 020.

### Verification commands and results

All commands run with `/Users/ferenci84/Dev/Mine/ai-agent-platform/.venv/bin/python -m pytest` (the repo `.venv` has `openai`, `pytest`, and `agent_core` installed).

1. Fast default plugin suite:
   ```
   pytest plugins/openai_responses/tests -q
   ```
   Result: 269 passed, 61 deselected, 3 failed. The 3 failures are pre-existing in `test_openai_responses_native_history_regressions.py` (attachment upload metadata, `KeyError: '_openai_responses_uploaded_attachments'`) and are unrelated to this task. Verified by stashing all task-010 changes and re-running: the same 3 tests fail on the clean tree.

2. Codex-models + provider unit tests (the suites I touched):
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_codex_models_unit.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q
   ```
   Result: 106 passed in 6.4s.

3. Real API GPT-5.6 family discovery test:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py::test_openai_responses_get_models_includes_gpt_5_6_family_real_api plugins/openai_responses/tests/test_openai_responses_provider_integration.py::test_openai_responses_get_models_real_api -m "integration and api and not slow_integration and openai" -q
   ```
   Result: 2 passed in 8.24s. `OPENAI_API_KEY` was loaded from repo root `.env` by the plugin `conftest.py`. The API model list includes `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna`.

4. ChatGPT saved-login model discovery integration test:
   ```
   CHATGPT_TEST_STATE_DIR="$HOME/.crystal" pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_model_discovery_manual_integration.py -m "manual_integration and integration and openai" -q
   ```
   Result: 1 passed in 0.75s. The saved login at `~/.crystal/auth/chatgpt-auth.json` was valid (expires `2026-07-18T19:42:08Z`). ChatGPT `get_models()` with `auth_mode: "chatgpt"` returned all three GPT-5.6 family IDs (sourced from live Codex catalog, not from the direct ChatGPT `/models` endpoint which returned an empty list at investigation time).

5. Lint/format:
   ```
   ruff check <changed test files>
   ```
   Result: All checks passed.
   ```
   black <changed test files>
   ```
   Result: 4 files reformatted (test files only; no source files changed).

### Credential/API gating report

- `OPENAI_API_KEY`: available in repo root `.env`, loaded by plugin `conftest.py`. Real API test ran and passed. Not skipped.
- ChatGPT saved login at `~/.crystal/auth/chatgpt-auth.json`: present, valid through `2026-07-18T19:42:08Z`. ChatGPT discovery test ran and passed. Not skipped.
- No credentials were printed during verification. The ChatGPT test's credential gate checks `access_token` presence and `expires_at` validity without printing token values.

### Risks confirmed

- The refreshed snapshot drops `gpt-5.3-codex` (removed from upstream). No tests depended on the checked-in snapshot content. Confirmed.
- The saved ChatGPT login expires `2026-07-18T19:42:08Z`. Implementation ran on `2026-07-17` so the test passed. If run after expiry, the test will skip with `saved ChatGPT login at {path} expired at {expires_at}` and must be reported as not run.
- The ChatGPT `/models` endpoint returned an empty list at investigation time. The ChatGPT integration test does not assert against it; it only asserts `get_models()` returns the GPT-5.6 family. Confirmed.

### Files changed

- `plugins/openai_responses/src/openai_responses_plugins/data/openai_codex_models.json` (refreshed snapshot)
- `plugins/openai_responses/tests/test_openai_responses_codex_models_unit.py` (7 new tests + imports)
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py` (5 new tests)
- `plugins/openai_responses/tests/test_openai_responses_provider_integration.py` (1 new real API test)
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_model_discovery_manual_integration.py` (new file, 1 ChatGPT saved-login test)
- `plugins/openai_responses/README.md` (model-discovery documentation)
- `tasks/20260713-openai-responses-gpt-5-6-support/010-refresh-model-catalog.md` (this file: execution plan + completion notes)
