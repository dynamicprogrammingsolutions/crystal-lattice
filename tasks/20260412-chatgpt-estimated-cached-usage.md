# ChatGPT Estimated Cached Usage And Auth Mode UI

Add ChatGPT-specific estimated cached-token accounting to the OpenAI Responses usage layer, use that estimate for ChatGPT-mode cost calculation when the backend does not report cached tokens, and optionally show the effective auth mode and estimated cached tokens in message footers.

## Requirements checklist

- [x] Add ChatGPT-mode estimated cached-token calculation in the OpenAI Responses usage extension without mutating the raw provider usage payload.
- [x] Keep estimated cached-token data separate from reported usage data.
- [x] Use estimated cached tokens for ChatGPT internal cost calculation regardless of whether the backend reports cached tokens.
- [x] Do not show normal `cached` footer data for ChatGPT mode.
- [x] Add a config flag `show_estimated_cached_tokens` that controls whether estimated cached tokens are shown in ChatGPT mode.
- [x] Add a config flag `show_openai_auth_mode` that controls whether the effective OpenAI auth mode is shown in a message footer.
- [x] Show the effective auth mode as per-message metadata/UI using the resolved effective mode for the request.
- [x] Preserve current API-mode behavior for reported cached tokens, usage display, and pricing.
- [x] Add focused unit tests for the cleaned-up cached-token estimation algorithm, cost behavior, and footer gating.

## Cleaned-up cached-token estimation

The estimator works over a reduced message history:

- Ignore tool result messages entirely.
- Keep only:
  - user messages
  - assistant/tool-call messages that carry usage with `input_tokens`

Define a turn as:

- one user message
- followed by zero or more usage-bearing assistant/tool-call messages
- ending immediately before the next user message

For a single usage-bearing assistant/tool-call message `M`, estimated cached tokens are:

1. Find the user turn that contains `M`.
2. If `M` is not the first usage-bearing assistant/tool-call message in that turn:
   - estimated cached tokens = `input_tokens` of the immediately previous usage-bearing assistant/tool-call message in the same turn
3. If `M` is the first usage-bearing assistant/tool-call message in that turn:
   - look at the previous turn that has at least one usage-bearing assistant/tool-call message
   - if no such previous turn exists, estimated cached tokens = `0`
   - otherwise, estimated cached tokens = `input_tokens` of the first usage-bearing assistant/tool-call message in that previous turn

Example:

1. `user`
2. `assistant/tool` with usage
3. `assistant/tool` with usage
4. `user`
5. `assistant/tool` with usage
6. `assistant/tool` with usage
7. `user`
8. `assistant/tool` with usage

Estimated cached tokens:

- message `2` -> `0`
- message `3` -> `input_tokens(2)`
- message `5` -> `input_tokens(2)`
- message `6` -> `input_tokens(5)`
- message `8` -> `input_tokens(5)`

Rationale:

- within a turn, reuse the immediately previous assistant/tool usage-bearing step
- at the first assistant/tool step of a new turn, the previous turn's interleaved reasoning/tool chain is not reusable, so fall back to the first usage-bearing assistant/tool step from the previous turn

## Proposed implementation

1. Extend the OpenAI Responses usage extension to compute effective per-message usage metadata for ChatGPT mode.
   - Add a small helper in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py` that can:
     - identify reduced-history message candidates
     - partition them into user turns
     - compute the estimated cached tokens for the current usage-bearing assistant/tool message
   - Keep the raw usage payload unchanged in `metadata.usage`.
   - Add separate metadata fields such as:
     - `usage_estimated_cached_tokens`
     - `usage_estimated_cached_tokens_formatted`
     - `usage_effective_auth_mode`
     - `usage_effective_auth_mode_label`

2. Use effective auth mode from the OpenAI Responses ChatGPT auth feature.
   - Read the resolved request mode from `state["config"]["_openai_responses_effective_auth_mode"]`.
   - Treat that resolved value as the source of truth for:
     - whether ChatGPT-mode estimation applies
     - whether auth-mode footer metadata should say `ChatGPT` or `API`

3. Use estimated cached tokens for ChatGPT pricing.
   - When effective auth mode is `chatgpt`:
     - ignore reported `cached_tokens` for pricing
     - pass an effective cached-token count to pricing based on the estimator
   - Do not overwrite public `metadata.usage`.
   - Preserve current pricing behavior for API mode.

4. Adjust message-footer display behavior.
   - In `get_ui_elements(...)` for the usage extension:
     - keep the existing `cached` footer for non-ChatGPT usage
     - suppress normal `cached` footer display for ChatGPT mode
     - add an `estimated cached` footer shown only when:
       - effective auth mode is `chatgpt`
       - `show_estimated_cached_tokens` is enabled
       - estimated cached-token metadata is present
     - add an `auth mode` footer shown only when:
       - `show_openai_auth_mode` is enabled
       - auth-mode metadata is present

5. Keep responsibilities clean.
   - OpenAI Responses ChatGPT auth feature:
     - decides requested mode vs effective mode
     - stores `_openai_responses_effective_auth_mode`
   - OpenAI Responses usage extension:
     - attaches per-message metadata
     - computes the ChatGPT cached-token estimate
     - computes usage/cost display metadata
     - contributes message-footer UI elements

## Test plan

1. Add unit tests for the cleaned-up estimator.
   - Build the exact example sequence above and assert:
     - `2 -> 0`
     - `3 -> input_tokens(2)`
     - `5 -> input_tokens(2)`
     - `6 -> input_tokens(5)`
     - `8 -> input_tokens(5)`

2. Add a unit test proving tool results are ignored.
   - Insert tool-result items between usage-bearing messages and verify the estimate is unchanged.

3. Add a unit test proving estimated cached tokens remain separate from reported usage.
   - `metadata.usage` remains the provider-reported payload.
   - estimated cached tokens appear only in dedicated metadata fields.

4. Add a unit test for ChatGPT pricing.
   - In ChatGPT mode with no reported cached tokens:
     - estimated cached tokens affect `usage_total_cost`
   - In ChatGPT mode with real reported cached tokens:
     - estimated cached tokens still win for pricing

5. Add UI gating tests.
   - `show_estimated_cached_tokens: false` hides the estimated cached footer.
   - `show_estimated_cached_tokens: true` shows the estimated cached footer in ChatGPT mode when metadata exists.
   - `show_openai_auth_mode: false` hides the auth-mode footer.
   - `show_openai_auth_mode: true` shows the auth-mode footer when metadata exists.

6. Add regression tests for API mode.
   - API mode still shows the normal cached-token footer from reported usage.
   - API mode does not synthesize estimated cached tokens for pricing or display.

## Notes

- This task is intentionally scoped to usage metadata, pricing, and footer UI only.
- It does not change provider request shaping, credential handling, or session persistence.
- If later needed, the effective auth mode footer could be moved into a dedicated lightweight extension, but the usage extension is the most practical current seam because it already owns per-message metadata and footer UI.

## Execution plan

Added during completion after plan approval.

1. Implement the reduced-history ChatGPT cached-token estimator inside the OpenAI Responses usage extension.
   - Build helper functions that:
     - filter out tool results
     - retain only user messages and usage-bearing assistant/tool-call messages
     - partition those reduced-history messages into user turns
     - compute the estimated cached tokens for the current usage-bearing assistant/tool message using the approved turn-based rule

2. Attach separate per-message metadata for estimated cached tokens and effective auth mode.
   - Keep `metadata.usage` as the raw provider-reported usage object.
   - Add separate metadata keys for:
     - estimated cached tokens
     - formatted estimated cached tokens
     - effective auth mode
     - effective auth mode display label

3. Use estimated cached tokens only as a ChatGPT-mode pricing fallback.
   - Read `_openai_responses_effective_auth_mode` from request state/config.
   - In ChatGPT mode:
     - use reported cached tokens if available
     - otherwise use the estimated cached-token count for pricing only
   - Leave API-mode cost behavior unchanged.

4. Update footer UI contribution in the usage extension.
   - Preserve the existing reported cached-token footer behavior for API mode.
   - Suppress the normal cached-token footer for ChatGPT mode.
   - Add an estimated cached-token footer gated by `show_estimated_cached_tokens`.
   - Add an auth-mode footer gated by `show_openai_auth_mode`.

5. Add and run focused unit tests.
   - Estimator correctness for the agreed example sequence
   - Tool-result ignoring behavior
   - Separation of reported usage from estimated metadata
   - ChatGPT pricing fallback with and without reported cached tokens
   - Footer/UI gating for estimated cached tokens and auth mode
   - API-mode regressions

## Completion Notes

Added during completion.

- Implemented the ChatGPT estimated cached-token heuristic in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`.
- Kept estimated cached-token metadata separate from reported `metadata.usage`.
- Added `usage_estimated_cached_tokens`, `usage_estimated_cached_tokens_formatted`, `usage_effective_auth_mode`, and `usage_effective_auth_mode_label`.
- ChatGPT mode now uses the estimated cached-token count for pricing even when the backend reports cached tokens.
- ChatGPT mode suppresses the normal `cached` footer, while optional `estimated cached` and `auth` footers are gated by `show_estimated_cached_tokens` and `show_openai_auth_mode`.
- API mode continues to use reported cached tokens and does not synthesize estimated cached tokens.
- Added unit coverage in `plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py` for:
  - the approved `2/3/5/6/8` estimation sequence
  - tool-result ignoring behavior
  - separation of raw vs estimated usage metadata
  - ChatGPT pricing precedence over reported cached tokens
  - UI/footer gating
  - API-mode regression behavior
- Added saved-login manual integration coverage in `plugins/openai_responses/tests/test_openai_responses_chatgpt_usage_manual_integration.py` for:
  - two user turns
  - multiple assistant responses per user turn via tool loop
  - real ChatGPT usage metadata on every assistant response
  - first-turn zero estimate and later non-zero estimates
- Verified with:
  - `python -m pytest plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py -q`
  - `python -m pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py plugins/openai_responses/tests/test_openai_responses_chatgpt_auth_feature_unit.py -q`
  - `python -m pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_usage_manual_integration.py --collect-only -q`