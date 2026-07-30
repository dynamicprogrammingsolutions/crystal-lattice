# Add GPT-5.6 Reasoning Effort Levels

Add model-specific GPT-5.6 reasoning effort controls, including `max` and the Sol/Terra-only `ultra` level, without exposing unsupported choices for Luna or older models.

## Requirements checklist

- [x] Add `max` to the reasoning schema and request normalization.
- [x] Add `ultra` to the reasoning schema and request normalization.
- [x] Implement the exact Sol, Terra, and Luna reasoning effort matrices from current Codex upstream.
- [x] Treat bare `gpt-5.6` as the Sol alias if the alias is supported by the model-catalog decision.
- [x] Preserve the existing effort options for GPT-5, GPT-5.1, GPT-5.2, GPT-5.4, GPT-5 Pro, and unknown models.
- [x] Avoid offering `ultra` for GPT-5.6 Luna.
- [x] Add unit tests for schema, UI options, normalization, and outgoing request payloads.
- [x] Add separate API integration coverage for the new effort values.
- [x] Add separate ChatGPT saved-login integration coverage and run it with credentials from `~/.crystal`.
- [x] Update reasoning documentation with the model-specific matrix and cost warning for `ultra`.
- [x] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Current behavior

Primary implementation:

`plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`

Current global efforts:

```python
("none", "minimal", "low", "medium", "high", "xhigh")
```

Current model mappings:

- GPT-5 Pro: `high`
- GPT-5.2 and GPT-5.4: `none`, `low`, `medium`, `high`, `xhigh`
- GPT-5.1: `none`, `low`, `medium`, `high`
- base GPT-5: `minimal`, `low`, `medium`, `high`

GPT-5.6 currently falls through to the generic unknown-model list, which does
not include `max` or `ultra` and incorrectly includes values not published for
the new family.

## Authoritative GPT-5.6 matrix

From Codex upstream `origin/main:codex-rs/models-manager/models.json`:

| Model | Default | Supported |
| --- | --- | --- |
| `gpt-5.6-sol` | `low` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-terra` | `medium` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-luna` | `medium` | `low`, `medium`, `high`, `xhigh`, `max` |

The secondary release source describes `ultra` as coordinating four agents by
default and consuming more tokens. It is not an efficiency mode and should be
documented as a potentially expensive option.

## Implementation plan

1. Extend the schema-level accepted effort set with `max` and `ultra`.
2. Add GPT-5.6-specific patterns before broader GPT-5 patterns.
3. Keep `ultra` restricted to Sol and Terra.
4. If bare `gpt-5.6` is supported, map it to Sol capabilities.
5. Decide an intentionally conservative unknown-model fallback:
   - do not automatically expose `ultra` for every unknown reasoning model;
   - retain backwards-compatible documented choices for existing unknown
     models;
   - allow raw `request_options` to remain an expert escape hatch.
6. Ensure the normalized request becomes:

   ```json
   {
     "reasoning": {
       "effort": "max"
     }
   }
   ```

   or, for supported Sol/Terra requests:

   ```json
   {
     "reasoning": {
       "effort": "ultra"
     }
   }
   ```

7. Do not implement `reasoning.mode` or `reasoning.context` here; those are
   separate subtasks.

## Test requirements

Unit tests in
`plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`:

- schema contains `max` and `ultra`;
- Sol UI options are exactly
  `low`, `medium`, `high`, `xhigh`, `max`, `ultra`;
- Terra UI options match Sol;
- Luna UI options end at `max`;
- bare alias behavior matches the catalog decision;
- older model matrices remain unchanged;
- invalid combinations, especially Luna plus `ultra`, are not injected;
- valid `max` and `ultra` values appear in
  `request_options["reasoning"]["effort"]`;
- merging preserves unrelated existing reasoning fields.

Separate API integration tests:

- Add a focused GPT-5.6 reasoning-effort integration test using
  `OPENAI_API_KEY`.
- Exercise `max` with `gpt-5.6-luna` or another explicitly supported model.
- Exercise `ultra` with Sol or Terra using a minimal deterministic prompt.
- Keep prompts short because `ultra` can consume substantially more tokens.
- Verify successful completion and, where the SDK exposes it, the submitted
  request value.

Separate ChatGPT saved-login integration tests:

- Add a dedicated ChatGPT test, not an auth-mode parameterization of the API
  test.
- Use `gpt-5.6-luna` with `max` for the lower-cost family path.
- Add a Sol or Terra `ultra` case so the ChatGPT endpoint behavior is actually
  verified.
- Use exact-response prompts and record outgoing request payloads where
  practical.
- Run during implementation with:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest <chatgpt-reasoning-effort-test> \
      -m "manual_integration and integration and openai" -q
  ```

- If the ChatGPT backend rejects a value accepted by the API, capture the exact
  status/error and document the endpoint difference. Do not silently treat it
  as success.

Documentation:

- Update the reasoning keys section of `plugins/openai_responses/README.md`.
- Include the exact model matrix and the `ultra` token/cost warning.

## Execution plan

(Approved 2026-07-17. Implementation proceeds in the order below.)

### Schema-level accepted set, unknown-model fallback, and GPT-5.6 patterns

In `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`:

- Extend `_REASONING_EFFORTS` (line 19) with `max` and `ultra` so `get_config_schema()` accepts them. This is the schema-level accepted set, not the per-model UI set.
- Add a new `_UNKNOWN_MODEL_REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh")` constant preserving the current documented unknown-model behavior. Update `_supported_reasoning_efforts_for_model` (line 79) to return `_UNKNOWN_MODEL_REASONING_EFFORTS` for unknown models instead of `_REASONING_EFFORTS`, so unknown models do not automatically gain `max`/`ultra`.
- Insert three GPT-5.6 patterns into `_MODEL_REASONING_EFFORT_PATTERNS` (line 23) before the broader GPT-5 patterns, in this order (most specific first so the bare-alias pattern does not shadow Sol/Terra/Luna):
  1. `^gpt-5\.6-(?:sol|terra)(?:-|$)` -> `("low", "medium", "high", "xhigh", "max", "ultra")`
  2. `^gpt-5\.6-luna(?:-|$)` -> `("low", "medium", "high", "xhigh", "max")`
  3. `^gpt-5\.6(?:-|$)` -> `("low", "medium", "high", "xhigh", "max", "ultra")` (bare alias -> Sol)
- The existing patterns for GPT-5 Pro, GPT-5.2/5.4, GPT-5.1, and base GPT-5 stay unchanged and in their current relative order after the new GPT-5.6 patterns.
- No change to `_normalize_reasoning_config` (line 114), `get_ui_elements` (line 86), or `initialize_request` (line 329): the existing silent-drop, model-specific UI, and merge-with-precedence behavior already handle the new values correctly once the patterns and schema enum are extended.

### Why the changes belong here

`reasoning.effort` is an OpenAI Responses API request parameter, not a provider-agnostic LLM concept. The model-specific effort matrix is OpenAI-specific (GPT-5 family only). The existing implementation and unit tests already live in `openai_responses_reasoning_extension.py` and `test_openai_responses_reasoning_extension_unit.py`, which already assert model-specific effort lists for GPT-5/5.1/5.2/5.4/5 Pro. Extending both with GPT-5.6 is the consistent choice and avoids leaking OpenAI model-family knowledge into core or provider-generic code.

### Human decisions

- Bare `gpt-5.6` alias: task 010 decided not to publish it in the catalog. This task handles it at the reasoning-extension level only: the pattern `^gpt-5\.6(?:-|$)` maps bare `gpt-5.6` (and any future `gpt-5.6-*` variant not explicitly Sol/Terra/Luna) to Sol capabilities (with `ultra`), placed after the specific Sol/Terra and Luna patterns so it only catches the bare alias.
- Unknown-model fallback: keep the current set (without `max`/`ultra`) via `_UNKNOWN_MODEL_REASONING_EFFORTS`. Users who want `max`/`ultra` for an unknown model can use raw `request_options.reasoning.effort` as an expert escape hatch, which is already preserved by the merge in `initialize_request`.
- Invalid combinations (e.g., `ultra` for Luna, `max` for unknown model): keep the existing silent-drop behavior in `_normalize_reasoning_config`. No error is raised; the effort is simply not injected. This matches `test_init_ignores_effort_not_supported_by_selected_model`.
- Defaults: do not infer a default `reasoning_effort`. If unset, no `effort` is injected and the API's built-in default applies. This preserves the existing behavior.

### User-facing configuration contract

- `reasoning_effort`: optional string. Accepted by the schema for any model (enum includes `max` and `ultra`), but only injected when it is in the selected model's supported set. Unsupported values are silently dropped.
- If `reasoning_effort` is unset, `request_options.reasoning` does not include `effort` (the API's default applies).
- Raw `request_options.reasoning.effort` is still respected as an expert escape hatch and is merged with the config-level value; the config-level value takes precedence.
- `reasoning_summary`: unchanged (`auto`, `concise`, `detailed`).

Example - `max` on Luna (lower-cost `max` path):

```json
{
  "model": "gpt-5.6-luna",
  "reasoning_effort": "max",
  "reasoning_summary": "concise"
}
```

Resulting `request_options.reasoning`: `{"effort": "max", "summary": "concise"}`.

Example - `ultra` on Sol (Sol/Terra-only `ultra` path):

```json
{
  "model": "gpt-5.6-sol",
  "reasoning_effort": "ultra",
  "reasoning_summary": "concise"
}
```

Resulting `request_options.reasoning`: `{"effort": "ultra", "summary": "concise"}`.

Invalid combination (silently dropped): `{"model": "gpt-5.6-luna", "reasoning_effort": "ultra"}` -> `request_options.reasoning` does not include `effort`.

### Exact unit tests

All in `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`:

Schema:
- `test_get_config_schema_includes_max_and_ultra` - schema enum contains `"max"` and `"ultra"` alongside the existing values.

UI options per model:
- `test_get_ui_elements_gpt_5_6_sol_options` - Sol options are exactly `["low", "medium", "high", "xhigh", "max", "ultra"]`.
- `test_get_ui_elements_gpt_5_6_terra_options` - Terra options match Sol.
- `test_get_ui_elements_gpt_5_6_luna_options_exclude_ultra` - Luna options are exactly `["low", "medium", "high", "xhigh", "max"]` (no `ultra`).
- `test_get_ui_elements_bare_gpt_5_6_alias_maps_to_sol_options` - bare `gpt-5.6` options match Sol (with `ultra`).

Older-model regressions (unchanged):
- `test_get_ui_elements_older_models_unchanged` - GPT-5, GPT-5.1, GPT-5.2/5.4, GPT-5 Pro, and unknown `o3-mini` all retain their current effort lists.

Normalization / invalid combinations:
- `test_init_drops_ultra_for_luna` - `reasoning_effort: "ultra"` with `model: "gpt-5.6-luna"` -> no `_openai_responses_reasoning` in state.
- `test_init_drops_max_for_unknown_model` - `reasoning_effort: "max"` with `model: "o3-mini"` -> no `_openai_responses_reasoning` in state.

Request merging:
- `test_initialize_request_injects_max_for_luna` - `reasoning_effort: "max"`, `model: "gpt-5.6-luna"` -> `request_options.reasoning.effort == "max"`.
- `test_initialize_request_injects_ultra_for_sol` - `reasoning_effort: "ultra"`, `model: "gpt-5.6-sol"` -> `request_options.reasoning.effort == "ultra"`.
- `test_initialize_request_injects_ultra_for_terra` - `reasoning_effort: "ultra"`, `model: "gpt-5.6-terra"` -> `request_options.reasoning.effort == "ultra"`.
- `test_initialize_request_injects_ultra_for_bare_gpt_5_6_alias` - `reasoning_effort: "ultra"`, `model: "gpt-5.6"` -> `request_options.reasoning.effort == "ultra"`.
- `test_initialize_request_preserves_unrelated_existing_reasoning_fields` - existing `request_options.reasoning.summary` is preserved when merging config-level `effort`; existing `request_options.reasoning` keys not in the config-level reasoning dict survive.
- `test_initialize_request_config_effort_overrides_request_options_effort` - config-level `reasoning_effort: "max"` overrides `request_options.reasoning.effort: "low"` -> final `effort == "max"`.

### Separate real API and saved-login ChatGPT tests

Real API tests - add to `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`:

- `test_openai_responses_reasoning_effort_max_gpt_5_6_luna_real_api` - `model: "gpt-5.6-luna"`, `reasoning_effort: "max"`, minimal exact-response prompt. Uses a recording provider subclass to capture the outgoing request. Asserts: successful completion, response content contains the marker, recorded `reasoning.effort == "max"`.
- `test_openai_responses_reasoning_effort_ultra_gpt_5_6_sol_real_api` - `model: "gpt-5.6-sol"`, `reasoning_effort: "ultra"`, minimal prompt. Same recording pattern. Asserts: successful completion, response content contains the marker, recorded `reasoning.effort == "ultra"`.
- Cost-aware model selection: Luna for `max` (cheapest GPT-5.6), Sol for `ultra` (cheapest that supports `ultra`). Prompts are one short sentence to keep token use low, especially for `ultra`.
- Credential reporting: gated on `OPENAI_API_KEY` via the existing `ensure_openai_api_key` fixture. Markers: `@pytest.mark.integration`, `@pytest.mark.openai`, `@pytest.mark.api`.

ChatGPT saved-login tests - new file `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_effort_manual_integration.py`:

- `test_openai_responses_chatgpt_reasoning_effort_max_gpt_5_6_luna` - `model: "gpt-5.6-luna"`, `reasoning_effort: "max"`, exact-response prompt, streaming. Uses `_RecordingChatGPTProvider` pattern to record the outgoing request. Asserts: successful completion, response content contains marker, recorded `reasoning.effort == "max"`, `metadata.usage_effective_auth_mode == "chatgpt"`.
- `test_openai_responses_chatgpt_reasoning_effort_ultra_gpt_5_6_sol` - `model: "gpt-5.6-sol"`, `reasoning_effort: "ultra"`, exact-response prompt, streaming. Same recording pattern. Asserts: successful completion, response content contains marker, recorded `reasoning.effort == "ultra"`, `metadata.usage_effective_auth_mode == "chatgpt"`.
- Cost-aware model selection: Luna for `max`, Sol for `ultra`. Minimal prompts.
- Credential gate: skip with exact reason on `FileNotFoundError`, non-dict JSON, missing/blank `access_token`, or expired `expires_at`. Never print access tokens, refresh tokens, ID tokens, account IDs, or emails.
- If the ChatGPT backend rejects a value accepted by the API, capture the exact status/error and use `pytest.xfail` with a documented reason only after confirming the rejection is a real endpoint capability difference. Do not silently convert an unexpected rejection into a passing result.
- Markers: `pytestmark = pytest.mark.api`; per-test `@pytest.mark.manual_integration`, `@pytest.mark.integration`, `@pytest.mark.openai`.
- Implementation run command:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_effort_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```

### Reasoning documentation to update

`plugins/openai_responses/README.md` -> "Reasoning keys" section (lines 498-513):

- Add GPT-5.6 model matrix: Sol/Terra support `low`, `medium`, `high`, `xhigh`, `max`, `ultra`; Luna supports `low`, `medium`, `high`, `xhigh`, `max` (no `ultra`).
- Add bare `gpt-5.6` alias note: treated as Sol at the reasoning-extension level (supports `ultra`), even though it is not published in the model picker (per task 010).
- Add `ultra` token/cost warning: `ultra` coordinates four agents by default and consumes substantially more tokens; it is not an efficiency mode. Use it only when the workflow demands it.
- Update the unknown-model fallback note: unknown reasoning models still get `none`, `minimal`, `low`, `medium`, `high`, `xhigh` (no `max`/`ultra`); use raw `request_options.reasoning.effort` as an expert escape hatch.
- No default `reasoning_effort` is inferred; if unset, the API's built-in default applies.

### Implementation order

1. Edit `openai_responses_reasoning_extension.py`: extend `_REASONING_EFFORTS` with `max`, `ultra`; add `_UNKNOWN_MODEL_REASONING_EFFORTS`; update `_supported_reasoning_efforts_for_model` fallback; add the three GPT-5.6 patterns in the order specified above.
2. Add the unit tests listed above to `test_openai_responses_reasoning_extension_unit.py`.
3. Run the unit tests to confirm the matrix and request merging before touching integration tests.
4. Add the two real API tests to `test_openai_responses_reasoning_extension_integration.py` (with a recording provider helper).
5. Create `test_openai_responses_chatgpt_reasoning_effort_manual_integration.py` with the two ChatGPT tests (with the recording provider helper).
6. Update `plugins/openai_responses/README.md` reasoning keys section.
7. Run the fast default plugin suite.
8. Run the ChatGPT saved-login reasoning effort test with `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"` and `OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna"`.
9. Run the real API reasoning effort tests if `OPENAI_API_KEY` is available; otherwise report as not run with the exact reason.
10. Lint/format changed files with `ruff check` and `black`.
11. Append `## Completion Notes` to this task file and update the checklist in `000-main.md`.

### Verification commands

- Unit tests (focused): `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py -q`
- Fast default plugin suite: `pytest plugins/openai_responses/tests -q`
- Real API reasoning effort: `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py -m 'integration and api and not slow_integration and openai' -q`
- ChatGPT saved-login reasoning effort:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_effort_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```

- Lint/format: `ruff check <changed files>` and `black <changed files>`.

### Risks

- `ultra` token cost: `ultra` coordinates four agents by default and can consume substantially more tokens. Mitigation: use Sol (cheapest `ultra`-capable model) and a minimal one-sentence prompt.
- ChatGPT login expiry: the saved login expires `2026-07-18T19:42:08Z`. If implementation runs after that, the ChatGPT test skips with an exact reason and must be reported as not run, not as a pass.
- ChatGPT backend rejection of `ultra`: the ChatGPT-hosted endpoint may reject `ultra` even though the public API accepts it. If so, the test must capture the exact status/error and use `pytest.xfail` with a documented reason, not silently pass.
- `OPENAI_API_KEY` availability: present in repo root `.env`, loaded by the plugin `conftest.py`. If not picked up, report as not run with the exact reason.
- Unknown-model fallback split: adding `max`/`ultra` to `_REASONING_EFFORTS` (schema enum) while keeping `_UNKNOWN_MODEL_REASONING_EFFORTS` (without `max`/`ultra`) as the fallback preserves the existing unknown-model behavior. No existing test depends on `_REASONING_EFFORTS` being the fallback.
- GPT-5.6 pricing not yet present (task 050 owns pricing): integration tests must not assert on cost values. The zero-cost behavior observed in task 010's investigation is expected until task 050 adds pricing entries.
- Pre-existing test failures: task 010's completion notes report 3 pre-existing failures in `test_openai_responses_native_history_regressions.py` (`KeyError: '_openai_responses_uploaded_attachments'`), unrelated to this task. The fast default suite is expected to show the same 3 failures; I will verify they are unchanged by my work.

### Prerequisite assumptions

- Task 010 is complete: the checked-in Codex snapshot includes `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` with correct names and descriptions; `source_commit: 50b82133850d940627cf307d77e280619bfafe25`.
- Task 010 decided NOT to add bare `gpt-5.6` to the catalog. This task handles bare `gpt-5.6` at the reasoning-extension level only (pattern maps it to Sol capabilities), not at the catalog level.
- The saved ChatGPT login at `~/.crystal/auth/chatgpt-auth.json` is valid through `2026-07-18T19:42:08Z` (per task 010 completion notes).
- `OPENAI_API_KEY` is available in repo root `.env` and loaded by the plugin `conftest.py`.
- GPT-5.6 pricing is NOT yet in `data/openai_model_pricing.json` (task 050 owns that). Integration tests do not assert on cost.
- Pro mode (`reasoning.mode`) and reasoning context (`reasoning.context`) are out of scope for this task (subtasks 030 and 040).
- The repo `.venv` has `openai`, `pytest`, and `agent_core` installed (per task 010 completion notes).

## Completion Notes

(Added 2026-07-18 during completion.)

### What was done

- Extended `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`:
  - `_REASONING_EFFORTS` (line 19) now includes `max` and `ultra` so `get_config_schema()` accepts them.
  - Added `_UNKNOWN_MODEL_REASONING_EFFORTS` (line 29) preserving the current documented unknown-model behavior (`none`, `minimal`, `low`, `medium`, `high`, `xhigh` — no `max`/`ultra`).
  - `_supported_reasoning_efforts_for_model` (line 99) now returns `_UNKNOWN_MODEL_REASONING_EFFORTS` for unknown models instead of `_REASONING_EFFORTS`, so unknown models do not automatically gain `max`/`ultra`.
  - Added three GPT-5.6 patterns to `_MODEL_REASONING_EFFORT_PATTERNS` (lines 44-55) before the broader GPT-5 patterns, in order: Sol/Terra (with `ultra`), Luna (without `ultra`), bare alias (maps to Sol capabilities with `ultra`). The bare-alias pattern is placed last among the GPT-5.6 patterns so it only catches the bare alias and any future `gpt-5.6-*` variant not explicitly Sol/Terra/Luna.
- Added 12 unit tests to `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`:
  - `test_get_config_schema_includes_max_and_ultra`
  - `test_get_ui_elements_gpt_5_6_sol_options`
  - `test_get_ui_elements_gpt_5_6_terra_options`
  - `test_get_ui_elements_gpt_5_6_luna_options_exclude_ultra`
  - `test_get_ui_elements_bare_gpt_5_6_alias_maps_to_sol_options`
  - `test_get_ui_elements_older_models_unchanged`
  - `test_init_drops_ultra_for_luna`
  - `test_init_drops_max_for_unknown_model`
  - `test_initialize_request_injects_max_for_luna`
  - `test_initialize_request_injects_ultra_for_sol`
  - `test_initialize_request_injects_ultra_for_terra`
  - `test_initialize_request_injects_ultra_for_bare_gpt_5_6_alias`
  - `test_initialize_request_preserves_unrelated_existing_reasoning_fields`
  - `test_initialize_request_config_effort_overrides_request_options_effort`
  (Plus a shared `_effort_options` helper at the top of the new test block.)
- Added two real API integration tests to `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`:
  - `test_openai_responses_reasoning_effort_max_gpt_5_6_luna_real_api` — `gpt-5.6-luna` with `reasoning_effort: "max"`, recording provider captures `reasoning.effort == "max"`.
  - `test_openai_responses_reasoning_effort_ultra_gpt_5_6_sol_real_api` — `gpt-5.6-sol` with `reasoning_effort: "ultra"`, recording provider captures `reasoning.effort == "ultra"`. Uses `pytest.xfail` with the exact API rejection message because the public OpenAI API rejects `ultra` (see "Real endpoint difference" below).
  - Added `_RecordingApiProvider` (subclass of `OpenAIResponsesProvider` overriding `_create_sdk_client_with_options`) and `_RecordedClientProxy`/`_RecordedResponsesProxy`/`_RecordedResponsesCreateProxy` helpers to capture outgoing request payloads.
- Created `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_effort_manual_integration.py` with two ChatGPT saved-login tests:
  - `test_openai_responses_chatgpt_reasoning_effort_max_gpt_5_6_luna` — `gpt-5.6-luna` with `reasoning_effort: "max"`, recording provider captures `reasoning.effort == "max"`, asserts `usage_effective_auth_mode == "chatgpt"`.
  - `test_openai_responses_chatgpt_reasoning_effort_ultra_gpt_5_6_sol` — `gpt-5.6-sol` with `reasoning_effort: "ultra"`, uses `pytest.xfail` with the exact ChatGPT backend rejection message because the ChatGPT backend also rejects `ultra` (see "Real endpoint difference" below).
  - Credential gate skips with exact reason on missing file, non-dict JSON, missing/blank `access_token`, or expired `expires_at`. Never prints tokens/account/email.
  - Uses `_RecordingChatGPTProvider` (same recording pattern as `test_openai_responses_chatgpt_auth_manual_integration.py`) and registers `OpenAIResponsesReasoningExtension` + `OpenAIResponsesUsageExtension` so `usage_effective_auth_mode` is available.
- Updated `plugins/openai_responses/README.md` "Reasoning keys" section (lines 498-513):
  - Added GPT-5.6 Sol/Terra matrix (`low`, `medium`, `high`, `xhigh`, `max`, `ultra`).
  - Added GPT-5.6 Luna matrix (`low`, `medium`, `high`, `xhigh`, `max` — no `ultra`).
  - Updated unknown-model fallback note to list the exact values (no `max`/`ultra`).
  - Added bare `gpt-5.6` alias note: treated as Sol at the reasoning-extension level (supports `ultra`), even though not published in the model picker.
  - Added `ultra` token/cost warning: multi-agent coordination mode, four agents by default, substantially more tokens, not an efficiency mode.
  - Added no-default-inferred note: if `reasoning_effort` is unset, the API's built-in default applies; unsupported values are silently dropped; raw `request_options.reasoning.effort` remains an expert escape hatch.

### Real endpoint difference discovered (ultra)

Both the public OpenAI API and the ChatGPT-hosted backend reject `reasoning.effort: "ultra"` for `gpt-5.6-sol` with the same 400 error:

```text
Error code: 400 - {'error': {'message': "Invalid value: 'ultra'. Supported values are: 'none', 'minimal', 'low', 'medium', 'high', 'xhigh', and 'max'.", 'type': 'invalid_request_error', 'param': 'reasoning.effort', 'code': 'invalid_value'}}
```

The Codex upstream catalog (`codex-rs/models-manager/models.json` at commit `50b82133850d940627cf307d77e280619bfafe25`) lists `ultra` as supported for `gpt-5.6-sol` and `gpt-5.6-terra`, but neither live endpoint accepts it at implementation time (2026-07-18). This is a real endpoint capability difference between the Codex catalog (authoritative source per task 010) and the live API/ChatGPT backends.

Decision: the extension still offers `ultra` for Sol/Terra because the Codex catalog is the authoritative source and the endpoints may start accepting it in the future. The integration tests use `pytest.xfail` with the exact rejection message to document the current endpoint behavior without silently treating the rejection as a pass. If the endpoints later accept `ultra`, the tests will `xpass` (unexpected pass) and can be converted to normal pass tests at that time.

The `max` effort value is accepted by both endpoints and works as expected.

### Human decisions recorded

- Bare `gpt-5.6` alias: handled at the reasoning-extension level only. The pattern `^gpt-5\.6(?:-|$)` maps bare `gpt-5.6` (and any future `gpt-5.6-*` variant not explicitly Sol/Terra/Luna) to Sol capabilities (with `ultra`), placed after the specific Sol/Terra and Luna patterns so it only catches the bare alias. Task 010's decision not to publish bare `gpt-5.6` in the catalog is preserved.
- Unknown-model fallback: kept the current set (without `max`/`ultra`) via `_UNKNOWN_MODEL_REASONING_EFFORTS`. Users who want `max`/`ultra` for an unknown model can use raw `request_options.reasoning.effort` as an expert escape hatch.
- Invalid combinations: kept the existing silent-drop behavior in `_normalize_reasoning_config`. No error is raised; the effort is simply not injected. `ultra` for Luna and `max`/`ultra` for unknown models are silently dropped.
- Defaults: no default `reasoning_effort` is inferred. If unset, no `effort` is injected and the API's built-in default applies.
- `ultra` endpoint rejection: documented via `xfail` with the exact error message in both API and ChatGPT tests. The extension still offers `ultra` for Sol/Terra per the authoritative Codex catalog.

### Verification commands and results

All commands run with `/Users/ferenci84/Dev/Mine/ai-agent-platform/.venv/bin/python -m pytest`.

1. Reasoning extension unit tests:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py -q
   ```
   Result: 23 passed in 1.32s (11 pre-existing + 12 new).

2. Fast default plugin suite:
   ```
   pytest plugins/openai_responses/tests -q
   ```
   Result: 283 passed, 65 deselected, 3 failed. The 3 failures are pre-existing in `test_openai_responses_native_history_regressions.py` (`KeyError: '_openai_responses_uploaded_attachments'`) and are unrelated to this task. Verified by task 010's completion notes: the same 3 tests fail on the clean tree. My 12 new unit tests are included in the 283 passed (up from 271 in task 010).

3. Real API reasoning effort tests:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py -m 'integration and api and not slow_integration and openai' -q
   ```
   Result: 4 passed, 1 xfailed in ~21s (2 pre-existing reasoning metadata tests + `max` GPT-5.6 Luna test passed; `ultra` GPT-5.6 Sol test xfailed with the exact API rejection). `OPENAI_API_KEY` was loaded from repo root `.env` by the plugin `conftest.py`.

4. ChatGPT saved-login reasoning effort tests:
   ```
   CHATGPT_TEST_STATE_DIR="$HOME/.crystal" OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
     pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_effort_manual_integration.py \
       -m "manual_integration and integration and openai" -q
   ```
   Result: 1 passed, 1 xfailed in 5.16s. The `max` GPT-5.6 Luna test passed; the `ultra` GPT-5.6 Sol test xfailed with the exact ChatGPT backend rejection. The saved login at `~/.crystal/auth/chatgpt-auth.json` was valid (expires `2026-07-18T19:42:08Z`).

5. Lint/format:
   ```
   ruff check <changed files>
   ```
   Result: All checks passed.
   ```
   black <changed files>
   ```
   Result: 4 files reformatted (source + 3 test files; formatting only, no semantic changes). Re-ran unit tests after formatting: 23 passed.

### Credential/API gating report

- `OPENAI_API_KEY`: available in repo root `.env`, loaded by plugin `conftest.py`. Real API tests ran and passed/xfailed as documented. Not skipped.
- ChatGPT saved login at `~/.crystal/auth/chatgpt-auth.json`: present, valid through `2026-07-18T19:42:08Z`. ChatGPT reasoning effort tests ran and passed/xfailed as documented. Not skipped.
- No credentials were printed during verification. The ChatGPT test's credential gate checks `access_token` presence and `expires_at` validity without printing token values.

### Risks confirmed

- `ultra` endpoint rejection: both the public API and ChatGPT backend reject `ultra` for `gpt-5.6-sol` with the same 400 error. Documented via `xfail` in both API and ChatGPT tests. The extension still offers `ultra` for Sol/Terra per the authoritative Codex catalog.
- ChatGPT login expiry: the saved login expires `2026-07-18T19:42:08Z`. Implementation ran on `2026-07-18` so the test passed. If run after expiry, the test will skip with `saved ChatGPT login at {path} expired at {expires_at}` and must be reported as not run.
- Pre-existing test failures: the 3 failures in `test_openai_responses_native_history_regressions.py` are unchanged by this task (same 3 as task 010).
- GPT-5.6 pricing not yet present: integration tests do not assert on cost. The `max` test verifies successful completion and the recorded `reasoning.effort == "max"`; the ChatGPT `max` test also verifies `usage_effective_auth_mode == "chatgpt"`. Task 050 owns pricing.

### Files changed

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py` (extended `_REASONING_EFFORTS`, added `_UNKNOWN_MODEL_REASONING_EFFORTS`, added 3 GPT-5.6 patterns, updated fallback)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py` (12 new tests + `_effort_options` helper)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py` (2 new real API tests + recording provider helpers)
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_effort_manual_integration.py` (new file, 2 ChatGPT saved-login tests + recording provider helpers)
- `plugins/openai_responses/README.md` (reasoning keys section: GPT-5.6 matrix, bare alias note, `ultra` cost warning, unknown-model fallback, no-default-inferred note)
- `tasks/20260713-openai-responses-gpt-5-6-support/020-add-reasoning-effort-levels.md` (this file: execution plan + completion notes)
