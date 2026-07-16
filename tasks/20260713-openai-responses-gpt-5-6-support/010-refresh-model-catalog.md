# Refresh the GPT-5.6 Model Catalog

Refresh the checked-in OpenAI Codex model snapshot and make GPT-5.6 model discovery reliable for both API and ChatGPT authentication paths, including offline/fallback behavior.

## Requirements checklist

- [ ] Refresh the checked-in Codex model snapshot from a pinned current upstream commit.
- [ ] Include `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna` with correct names and descriptions.
- [ ] Preserve the documented discovery precedence: manual models, checked-in snapshot, then live Codex catalog.
- [ ] Keep ChatGPT discovery usable when live GitHub catalog access fails.
- [ ] Decide and document whether the bare `gpt-5.6` alias should appear in the UI; do not invent it if authoritative discovery does not publish it.
- [ ] Add or update unit tests for snapshot generation, normalization, merge precedence, and fallback behavior.
- [ ] Add a separate real API model-discovery integration test.
- [ ] Add a separate saved-login ChatGPT model-discovery integration test and run it with `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"`.
- [ ] Update model-discovery documentation and checked-in snapshot provenance.
- [ ] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

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
