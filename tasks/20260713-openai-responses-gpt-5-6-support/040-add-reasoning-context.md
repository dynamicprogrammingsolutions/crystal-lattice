# Add Reasoning Context Preservation Controls

Add first-class `reasoning.context` support for `auto`, `current_turn`, and `all_turns`, including multi-turn verification that preserved reasoning items are actually available to later requests.

## Requirements checklist

- [x] Add a first-class configuration key for `reasoning.context`.
- [x] Support `auto`, `current_turn`, and `all_turns`.
- [x] Preserve omission semantics and avoid sending undocumented values.
- [x] Merge context with effort, mode, summary, encrypted-content include, and raw request options.
- [x] Ensure `all_turns` works with the provider's retained/replayed native response history.
- [x] Preserve or expose the effective response context mode when OpenAI returns it.
- [x] Add focused unit tests for normalization, nested merging, and response metadata extraction.
- [x] Add a separate multi-turn real API integration test.
- [x] Add a separate multi-turn saved-login ChatGPT integration test and run it with credentials from `~/.crystal`.
- [x] Update reasoning/history documentation with the prerequisites and first-turn behavior.
- [x] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Official semantics

OpenAI documents:

| Value | Behavior |
| --- | --- |
| `auto` | Use the selected model's default; omission has the same effect. |
| `current_turn` | Make reasoning from the active turn available without rendering earlier-turn reasoning into the next sample. |
| `all_turns` | Render available, compatible reasoning items from earlier turns into the next sample. |

Important constraints:

- support is model-dependent;
- the response may report an effective mode of `current_turn` or `all_turns`;
- the setting does not create missing reasoning items;
- `all_turns` only has an effect when earlier response items are available;
- first-request behavior is the same for `current_turn` and `all_turns`.

This framework replays retained provider-native history rather than relying only
on `previous_response_id`. The reasoning extension already requests
`reasoning.encrypted_content` and preserves reasoning items, so the
implementation should verify that the second request includes the earlier
compatible reasoning item(s).

## Configuration design

Preferred public key:

```json
{
  "reasoning_context": "all_turns"
}
```

Normalize it to:

```json
{
  "reasoning": {
    "context": "all_turns"
  }
}
```

If `reasoning_context` is absent, omit the wire field. If explicitly set to
`auto`, either send `auto` or normalize to omission, but make the decision
explicit and cover it with tests.

## Implementation plan

1. Add schema and UI options in the reasoning extension.
2. Add model-aware validation if official model capability data is available.
3. Merge the field into the existing nested reasoning request object.
4. Inspect streaming and non-streaming completed response shapes for the
   response-level effective context.
5. Preserve the effective value in a stable metadata location, preferably under
   existing OpenAI reasoning metadata, for example:

   ```json
   {
     "metadata": {
       "openai_responses_reasoning": {
         "context": "all_turns"
       }
     }
   }
   ```

   Use a different key only if it better matches current metadata ownership.
6. Confirm native history retains the reasoning items needed for the next turn.
7. Do not introduce a second conversation-state mechanism when full native
   replay already satisfies the API requirement.

## Test requirements

Unit tests:

- schema contains exactly the three documented values;
- absent, `auto`, `current_turn`, and `all_turns` normalization;
- merging with effort, summary, and Pro mode;
- encrypted-content include remains present;
- raw request options are preserved;
- completed response effective context is extracted when present;
- missing response context does not fabricate a value;
- retained reasoning items survive core/native conversion for a follow-up turn.

Separate real API integration test:

- Use a GPT-5.6 model documented to support persisted reasoning.
- Send two turns with `reasoning_context: "all_turns"`.
- Ensure turn one produces a preserved reasoning item.
- Ensure turn two sends or has access to the complete prior response history.
- Assert the response-reported effective context when available.
- Add a comparison or focused assertion for `current_turn`.
- Gate on `OPENAI_API_KEY`.

Separate ChatGPT saved-login integration test:

- Use a dedicated test with saved ChatGPT credentials.
- Run at least two turns through the ChatGPT backend.
- Verify outgoing request payloads contain the configured context.
- Verify prior reasoning items are retained/replayed.
- Assert backend acceptance and effective context if the ChatGPT response
  exposes it.
- Run during implementation with:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest <chatgpt-reasoning-context-test> \
      -m "manual_integration and integration and openai" -q
  ```

- If ChatGPT accepts the request but omits the effective response field, record
  that difference without inventing metadata.
- If it rejects `all_turns`, report the exact error and do not weaken the API
  test.

Documentation:

- Update `plugins/openai_responses/README.md`.
- Explain `auto`, `current_turn`, `all_turns`, first-turn equivalence, required
  prior reasoning items, and this provider's native-history replay behavior.

## Execution plan

(Approved 2026-07-18. Implementation proceeds in the order below. Added
during completion.)

### Request configuration, nested merging, native-history, effective-response context

See the approved plan in the conversation history. Summary:

- **Request configuration:** first-class `reasoning_context` config key
  (enum `["auto", "current_turn", "all_turns"]`), GPT-5.6 family only.
  `auto` normalizes to omission. `current_turn`/`all_turns` inject
  `reasoning.context` into the nested `request_options["reasoning"]` dict.
- **Nested merging:** reuses the existing `initialize_request` merge
  (`{**existing_reasoning, **reasoning}`); config-level `reasoning_context`
  overrides raw `request_options.reasoning.context`; when config is
  `auto`/unset, raw is preserved.
- **Native-history:** the existing retained native history
  (`session.metadata["native_messages"]` + `_expanded_request_history` +
  `to_native_messages`) already replays reasoning items with
  `encrypted_content` into follow-up requests. No second conversation-state
  mechanism is introduced.
- **Effective-response context:** provider extracts
  `response.reasoning.context` into internal `_metadata` on output items;
  reasoning extension reads it and publishes
  `metadata.openai_responses_reasoning.context`.

### Behavior split: reasoning extension vs provider

- **Reasoning extension** owns `reasoning_context` config schema, UI,
  normalization, nested merge, and the public `openai_responses_reasoning`
  metadata key (including the new `context` sub-key and the `message_footer`
  element).
- **Provider** owns extracting `response.reasoning.context` into internal
  `_metadata._openai_responses_reasoning_context` (parallel to
  `_openai_responses_usage_raw` and `_openai_responses_service_tier`).
- **Native-history** owns retaining and replaying reasoning items with
  `encrypted_content` across turns (unchanged).

### Human decisions

- `auto` normalizes to omission (consistent with `reasoning_mode` omitting
  `standard`).
- Model gating: GPT-5.6 family only (conservative; Codex catalog has no
  per-model capability data). Reuses `_model_supports_pro_reasoning`.
- Public metadata key: `metadata.openai_responses_reasoning.context`.
- Internal provider key: `_openai_responses_reasoning_context`.
- Missing effective context: not fabricated (key absent).
- Footer element: unconditional definition, `condition` handles visibility.
- Threshold for multi-turn size assertions: 2/3 (found by running tests
  multiple times; all_turns ratio ~0.55, current_turn ratio ~1.10).

### Concrete example

Config:
```json
{
  "model": "gpt-5.6-sol",
  "reasoning_context": "all_turns",
  "reasoning_effort": "medium",
  "reasoning_summary": "concise"
}
```

Resulting `request_options["reasoning"]`:
```json
{"context": "all_turns", "effort": "medium", "summary": "concise"}
```

Assistant metadata after a response reporting `reasoning.context: "all_turns"`:
```json
{
  "metadata": {
    "reasoning": "Used internal reasoning.",
    "openai_responses_reasoning": {
      "items": [...],
      "encrypted_content": [...],
      "context": "all_turns"
    }
  }
}
```

### Changed metadata contract

`metadata.openai_responses_reasoning` gains optional `context` sub-key.
Internal `_metadata._openai_responses_reasoning_context` on native output
items is new (provider-internal). Backward-compatible: existing readers of
`items`, `summary`, `encrypted_content`, `summary_text`, `content_text` are
unaffected.

### Exact unit tests

In `test_openai_responses_reasoning_extension_unit.py` (30 new tests):
schema, UI visibility (4 models + footer), normalization (6 cases), nested
merging (8 cases), encrypted-content include (2 cases), raw options
preservation (1 case), response extraction (4 cases), merge across
segments (1 case).

In `test_openai_responses_provider_unit.py` (6 new tests):
`_response_internal_metadata` extracts/omits reasoning context.

In `test_openai_responses_native_history_regressions.py` (1 new test):
native-history round trip with `encrypted_content`.

### Multi-turn API and ChatGPT tests

Real API (`test_openai_responses_reasoning_extension_integration.py`):
- `test_openai_responses_reasoning_context_all_turns_reuses_prior_reasoning_gpt_5_6_luna_real_api`:
  bank-file prompt, 2 turns, 5 retry attempts. Success: turn 2 encrypted
  reasoning <= 2/3 of turn 1's (or zero items), content contains "Clock".
- `test_openai_responses_reasoning_context_current_turn_re_derives_reasoning_gpt_5_6_luna_real_api`:
  same flow. Success: turn 2 encrypted reasoning >= 2/3 of turn 1's.
  Label check omitted (model may re-derive incorrectly without earlier
  reasoning).

ChatGPT (`test_openai_responses_chatgpt_reasoning_context_manual_integration.py`):
- `test_openai_responses_chatgpt_reasoning_context_all_turns_reuses_prior_reasoning_gpt_5_6_luna`
- `test_openai_responses_chatgpt_reasoning_context_current_turn_focus_gpt_5_6_luna`
  Same assertions, ChatGPT backend, streaming.

### Documentation

`plugins/openai_responses/README.md`:
- Reasoning keys: added `reasoning_context` bullet, first-turn equivalence,
  required prior reasoning items, effective response context, footer
  element, model gating, precedence.
- Capabilities/caveats: updated native-history bullet for `all_turns`.
- Usage keys: cross-reference to reasoning context footer.

### Implementation order

1. Provider: add `_RAW_REASONING_CONTEXT_METADATA_KEY`, extract in
   `_response_internal_metadata`.
2. Reasoning extension: add constants, `_model_supports_reasoning_context`,
   schema, UI (select + footer), normalization, extraction, merge.
3. Unit tests (reasoning extension + provider + native history).
4. Real API integration tests (all_turns + current_turn).
5. ChatGPT integration tests (all_turns + current_turn).
6. README updates.
7. Run fast default suite, real API tests, ChatGPT tests.
8. Lint/format.
9. Completion notes + main checklist.

### Verification commands

- Unit: `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- Native history: `pytest plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py -q`
- Fast default: `pytest plugins/openai_responses/tests -q`
- Real API: `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py -m 'integration and api and not slow_integration and openai' -q`
- ChatGPT: `CHATGPT_TEST_STATE_DIR="$HOME/.crystal" OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_context_manual_integration.py -m "manual_integration and integration and openai" -q`
- Lint/format: `ruff check` and `black`.

### Risks

- API/ChatGPT rejection of `reasoning.context`: handled via `xfail` with
  exact rejection message.
- ChatGPT login expiry: saved login valid through 2026-07-18.
- Pre-existing test failures: 3 in `test_openai_responses_native_history_regressions.py`
  (`KeyError: '_openai_responses_uploaded_attachments'`), unchanged.
- GPT-5.6 pricing not yet present: integration tests do not assert on cost.
- Encrypted reasoning size variability: 5 retry attempts; 2/3 threshold
  found by running tests multiple times.

### Prerequisite assumptions

- Tasks 010, 020, 030 complete (model catalog, effort levels, Pro mode).
- Existing native-history replay sufficient for `all_turns` (verified by
  unit test).
- `OPENAI_API_KEY` in repo root `.env`.
- ChatGPT saved login at `~/.crystal/auth/chatgpt-auth.json`.
- `REASONING_DIR` and `FileReaderTool` available.

## Completion Notes

(Added 2026-07-18 during completion.)

### What was done

- Extended `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`:
  - Added `_RAW_REASONING_CONTEXT_METADATA_KEY = "_openai_responses_reasoning_context"` constant.
  - Extended `_response_internal_metadata` to extract `response.reasoning.context` (if a non-empty string) into `md[_RAW_REASONING_CONTEXT_METADATA_KEY]`.
- Extended `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`:
  - Added `_RAW_REASONING_CONTEXT_METADATA_KEY`, `_REASONING_CONTEXTS`, `_REASONING_CONTEXT_INJECT_VALUES` constants.
  - Added `_model_supports_reasoning_context(model) -> bool` helper (delegates to `_model_supports_pro_reasoning`, GPT-5.6 family only).
  - Extended `get_config_schema()` with `reasoning_context` key (enum `["auto", "current_turn", "all_turns"]`, required `False`).
  - Extended `get_ui_elements()` to include a `reasoning_context` select (GPT-5.6 only) and a `message_footer` element for `metadata.openai_responses_reasoning.context` (unconditional, `condition` handles visibility).
  - Extended `_normalize_reasoning_config()` to read `reasoning_context`: `current_turn`/`all_turns` inject `context` for GPT-5.6 models; `auto` and invalid/non-GPT-5.6 values are silently dropped (normalized to omission).
  - Extended `_extract_reasoning_metadata()` to read `_openai_responses_reasoning_context` from any relevant native item's `_metadata` (not just reasoning items) and add it to `raw_metadata["context"]`. No longer returns `{}` early when there are no reasoning items but `context` is present.
  - Extended `_merge_reasoning_metadata()` to handle `context`: latest non-empty string wins.
  - No change to `initialize_request` merge logic: the existing `{**existing_reasoning, **reasoning}` spread handles `context`.
- Added 30 unit tests to `test_openai_responses_reasoning_extension_unit.py`:
  - Schema: `test_get_config_schema_includes_reasoning_context_enum`
  - UI visibility: `test_get_ui_elements_shows_reasoning_context_for_gpt_5_6_sol`, `test_get_ui_elements_shows_reasoning_context_for_gpt_5_6_luna`, `test_get_ui_elements_shows_reasoning_context_for_bare_gpt_5_6_alias`, `test_get_ui_elements_hides_reasoning_context_for_older_models`
  - Footer: `test_get_ui_elements_includes_context_footer`, `test_get_ui_elements_context_footer_present_for_luna`, `test_get_ui_elements_context_footer_present_for_older_models`, `test_get_ui_elements_context_footer_distinct_from_config_selects`
  - Normalization: `test_init_drops_reasoning_context_for_gpt_5_4`, `test_init_drops_reasoning_context_for_unknown_model`, `test_init_normalizes_auto_to_omission`, `test_init_preserves_current_turn_for_luna`, `test_init_preserves_all_turns_for_sol`, `test_init_drops_invalid_reasoning_context_value`
  - Nested merging: `test_initialize_request_injects_context_all_turns_for_sol`, `test_initialize_request_injects_context_current_turn_for_luna`, `test_initialize_request_context_composes_with_effort_summary_and_mode`, `test_initialize_request_auto_context_omits_wire_field`, `test_initialize_request_context_preserves_unrelated_existing_reasoning_fields`, `test_initialize_request_config_context_overrides_request_options_context`, `test_initialize_request_preserves_raw_request_options_context_when_config_unset`, `test_initialize_request_auto_context_does_not_override_raw_context`
  - Encrypted-content include: `test_initialize_request_context_all_turns_keeps_encrypted_content_include`, `test_initialize_request_context_all_turns_preserves_raw_include_values`
  - Raw options: `test_initialize_request_context_all_turns_preserves_unrelated_request_options`
  - Response extraction: `test_from_native_messages_extracts_effective_context_from_reasoning_item_metadata`, `test_from_native_messages_extracts_effective_context_from_message_item_metadata`, `test_from_native_messages_omits_context_when_response_does_not_report_it`, `test_from_native_messages_context_survives_merge_across_segments`
- Added 6 unit tests to `test_openai_responses_provider_unit.py`:
  - `test_response_internal_metadata_extracts_reasoning_context`
  - `test_response_internal_metadata_extracts_current_turn_context`
  - `test_response_internal_metadata_omits_reasoning_context_when_absent`
  - `test_response_internal_metadata_omits_reasoning_context_when_no_reasoning_obj`
  - `test_response_internal_metadata_omits_reasoning_context_when_not_string`
  - `test_response_internal_metadata_omits_reasoning_context_when_empty`
- Added 1 unit test to `test_openai_responses_native_history_regressions.py`:
  - `test_native_history_retains_reasoning_items_with_encrypted_content_for_follow_up` — verifies reasoning items with `encrypted_content` survive core/native conversion and are replayed into the follow-up request's `input`.
- Added 2 real API integration tests to `test_openai_responses_reasoning_extension_integration.py`:
  - `test_openai_responses_reasoning_context_all_turns_reuses_prior_reasoning_gpt_5_6_luna_real_api` — bank-file prompt, 2 turns, 5 retry attempts. Success: turn 2 encrypted reasoning <= 2/3 of turn 1's (or zero items), content contains "Clock", recorded `reasoning.context == "all_turns"`, turn 2 input contains replayed reasoning items.
  - `test_openai_responses_reasoning_context_current_turn_re_derives_reasoning_gpt_5_6_luna_real_api` — same flow. Success: turn 2 encrypted reasoning >= 2/3 of turn 1's, recorded `reasoning.context == "current_turn"`, turn 2 input contains replayed reasoning items. Label check omitted (model may re-derive incorrectly without earlier reasoning).
- Created `test_openai_responses_chatgpt_reasoning_context_manual_integration.py` with 2 ChatGPT saved-login tests:
  - `test_openai_responses_chatgpt_reasoning_context_all_turns_reuses_prior_reasoning_gpt_5_6_luna`
  - `test_openai_responses_chatgpt_reasoning_context_current_turn_focus_gpt_5_6_luna`
  Same assertions as the real API tests, ChatGPT backend, streaming. Credential gate reuses the exact helper from tasks 020/030.
- Updated `plugins/openai_responses/README.md`:
  - Reasoning keys: added `reasoning_context` bullet (enum, GPT-5.6 only, `auto`/absence = omission, first-turn equivalence, `all_turns` requires prior reasoning items, effective response context, model gating, precedence); updated bare `gpt-5.6` alias note; updated no-default-inferred note; added `message_footer` note for effective context.
  - Capabilities/caveats: updated native-history bullet to explain `all_turns` and that no second conversation-state mechanism is needed.
  - Usage keys: added cross-reference to the reasoning context footer.

### Threshold found by running tests multiple times

The user requested opposite assertions for `all_turns` vs `current_turn`:
- `all_turns`: turn 2 reasoning <= 2/3 of turn 1's (or zero items)
- `current_turn`: turn 2 reasoning >= 2/3 of turn 1's

The 2/3 threshold was found by running the tests multiple times:
- `all_turns` observed ratio (second_len / first_len): ~0.55 (e.g., 1016/1848)
- `current_turn` observed ratio: ~1.10 (e.g., 2148/1956)

The 2/3 boundary cleanly separates the two modes. Both tests pass
consistently with this threshold (verified by running each test 3+ times).

The initial 1/2 threshold for `all_turns` was too strict (the observed ~0.55
ratio is above 1/2). The 2/3 threshold gives margin while still being
clearly below the `current_turn` ratio.

### Verification commands and results

All commands run with `/Users/ferenci84/Dev/Mine/ai-agent-platform/.venv/bin/python -m pytest`.

1. Reasoning extension + provider unit tests:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q
   ```
   Result: 170 passed in 7.42s (74 reasoning extension + 96 provider; 30 + 6 new respectively).

2. Native history regression tests:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py -q
   ```
   Result: 14 passed, 3 failed (pre-existing `KeyError: '_openai_responses_uploaded_attachments'` failures, unchanged from tasks 010/020/030). My new test `test_native_history_retains_reasoning_items_with_encrypted_content_for_follow_up` passed.

3. Fast default plugin suite:
   ```
   pytest plugins/openai_responses/tests -q
   ```
   Result: 365 passed, 74 deselected, 3 failed in 26.34s. The 3 failures are pre-existing (same as tasks 010/020/030). My 37 new tests are included in the 365 passed (up from 328 in task 030).

4. Real API reasoning context tests:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py -m 'integration and api and not slow_integration and openai' -q
   ```
   Result: 6 passed, 1 xfailed in 34.53s. The 2 new reasoning context tests passed; the 1 xfail is the pre-existing task 020 `ultra` test (API rejects `ultra`). `OPENAI_API_KEY` was loaded from repo root `.env`.

5. ChatGPT saved-login reasoning context tests:
   ```
   CHATGPT_TEST_STATE_DIR="$HOME/.crystal" OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
     pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_context_manual_integration.py \
       -m "manual_integration and integration and openai" -q
   ```
   Result: 2 passed in 47.61s. The saved login at `~/.crystal/auth/chatgpt-auth.json` was valid (expires `2026-07-18T19:42:08Z`).

6. Lint/format:
   ```
   ruff check <changed files>
   ```
   Result: All checks passed.
   ```
   black <changed files>
   ```
   Result: 6 files reformatted (formatting only, no semantic changes). Re-ran unit tests after formatting: 170 passed.

### Credential/API gating report

- `OPENAI_API_KEY`: available in repo root `.env`, loaded by plugin `conftest.py`. Real API tests ran and passed. Not skipped.
- ChatGPT saved login at `~/.crystal/auth/chatgpt-auth.json`: present, valid through `2026-07-18T19:42:08Z`. ChatGPT tests ran and passed. Not skipped.
- No credentials were printed during verification. The ChatGPT test's credential gate checks `access_token` presence and `expires_at` validity without printing token values.

### Risks confirmed

- Pre-existing test failures: the 3 failures in `test_openai_responses_native_history_regressions.py` are unchanged by this task (same 3 as tasks 010/020/030).
- GPT-5.6 pricing not yet present: integration tests do not assert on cost. Task 050 owns pricing.
- ChatGPT login expiry: the saved login expires `2026-07-18T19:42:08Z`. Implementation ran on `2026-07-18` so the tests passed. If run after expiry, the tests will skip with `saved ChatGPT login at {path} expired at {expires_at}` and must be reported as not run.
- Encrypted reasoning size variability: the 2/3 threshold was found by running the tests multiple times. The `all_turns` ratio (~0.55) is below 2/3, and the `current_turn` ratio (~1.10) is above 2/3, giving a clean separation. The 5-attempt retry loop handles per-run variability.

### Files changed

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` (added `_RAW_REASONING_CONTEXT_METADATA_KEY`, extended `_response_internal_metadata`)
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py` (added constants, `_model_supports_reasoning_context`, schema, UI select + footer, normalization, extraction, merge)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py` (30 new tests + helpers)
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py` (6 new tests)
- `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py` (1 new test)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py` (2 new real API tests + helpers)
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_context_manual_integration.py` (new file, 2 ChatGPT saved-login tests)
- `plugins/openai_responses/README.md` (reasoning keys, capabilities/caveats, usage keys cross-reference)
- `tasks/20260713-openai-responses-gpt-5-6-support/040-add-reasoning-context.md` (this file: execution plan + completion notes)
