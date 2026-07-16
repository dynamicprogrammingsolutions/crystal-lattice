# Add GPT-5.6 Reasoning Pro Mode

Expose OpenAI's GPT-5.6 `reasoning.mode: "pro"` request control as a first-class OpenAI Responses setting, distinct from Fast/priority service tier behavior.

## Requirements checklist

- [ ] Add a first-class optional configuration key for GPT-5.6 Pro reasoning mode.
- [ ] Emit `reasoning.mode: "pro"` only for supported GPT-5.6 models.
- [ ] Treat omission as standard reasoning mode unless official API behavior supports an explicit standard value.
- [ ] Keep Pro reasoning mode separate from `service_tier: "priority"` Fast mode.
- [ ] Preserve existing `reasoning.effort`, `reasoning.summary`, raw request options, and include values.
- [ ] Add unit tests for schema/UI visibility, normalization, nested merging, and model restrictions.
- [ ] Add a separate real API Pro-mode integration test.
- [ ] Add a separate saved-login ChatGPT Pro-mode integration test and run it with credentials from `~/.crystal`.
- [ ] Update reasoning and pricing documentation to explain Pro-mode billing semantics.
- [ ] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Source behavior

The OpenAI reasoning guide recommends GPT-5.6 Sol with:

```json
{
  "reasoning": {
    "mode": "pro",
    "effort": "medium"
  }
}
```

OpenAI states that Pro mode performs more model work and bills the resulting
tokens at the selected model's normal token rates. It is not a separate model
ID and does not use a separate per-token pricing table.

This must not be confused with the existing Fast mode extension:

`plugins/openai_responses/src/openai_responses_plugins/openai_responses_fast_mode_extension.py`

Fast mode sets:

```json
{
  "service_tier": "priority"
}
```

Pro reasoning mode instead belongs inside the nested `reasoning` object.

## Configuration design

Preferred public key:

```json
{
  "reasoning_mode": "pro"
}
```

Use an optional enum containing `pro`, with absence meaning standard behavior.
Do not send `"mode": "standard"` unless the current official API schema is
verified to accept that exact value.

An enable-style boolean may be considered only if it better matches current UI
patterns, but the wire concept and configuration documentation should remain
clear. Avoid naming that could be confused with ChatGPT subscription plans or
Fast mode.

## Implementation plan

1. Extend
   `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`.
2. Add schema and a model-aware UI control visible only for supported GPT-5.6
   selections.
3. Normalize valid config into the existing extension-owned reasoning state.
4. Merge mode with effort and summary in:

   `request_options["reasoning"]`.

5. Preserve expert-provided nested request options unless a first-class config
   key intentionally overrides the same field.
6. Do not modify Fast mode, Flex mode, or pricing multipliers.

## Test requirements

Unit tests:

- schema exposes the optional Pro setting;
- UI shows it for GPT-5.6 family selections and hides it for older models;
- unset config emits no `reasoning.mode`;
- enabled config emits exactly `"mode": "pro"`;
- mode composes with effort and summary;
- existing raw reasoning fields remain intact;
- Fast mode can coexist, producing both:

  ```json
  {
    "reasoning": {"mode": "pro"},
    "service_tier": "priority"
  }
  ```

  without either feature overwriting the other.

Separate real API integration test:

- Use `gpt-5.6-sol` or the authoritative bare alias with
  `reasoning_mode: "pro"` and a moderate effort.
- Send a short deterministic prompt.
- Assert successful completion.
- Record/verify the outgoing nested reasoning payload if the test harness
  supports request recording.
- Gate on `OPENAI_API_KEY`.

Separate ChatGPT saved-login integration test:

- Add a dedicated `manual_integration` test using
  `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`.
- Use a GPT-5.6 model explicitly.
- Record the outgoing request and assert it contains
  `reasoning.mode == "pro"`.
- Assert whether the ChatGPT backend accepts and completes the request.
- Run during implementation with:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-sol" \
    pytest <chatgpt-pro-mode-test> \
      -m "manual_integration and integration and openai" -q
  ```

- If ChatGPT rejects Pro mode while the API accepts it, report the exact
  endpoint response and document the divergence. Do not silently remove the
  field or count an `xfail` as full support.

Documentation:

- Update `plugins/openai_responses/README.md`.
- Explain that Pro mode increases model work and token usage but uses the
  selected model's standard per-token rates.
- Cross-reference Fast mode to prevent configuration confusion.
