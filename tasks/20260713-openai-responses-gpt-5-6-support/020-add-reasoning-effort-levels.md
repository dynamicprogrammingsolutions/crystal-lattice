# Add GPT-5.6 Reasoning Effort Levels

Add model-specific GPT-5.6 reasoning effort controls, including `max` and the Sol/Terra-only `ultra` level, without exposing unsupported choices for Luna or older models.

## Requirements checklist

- [ ] Add `max` to the reasoning schema and request normalization.
- [ ] Add `ultra` to the reasoning schema and request normalization.
- [ ] Implement the exact Sol, Terra, and Luna reasoning effort matrices from current Codex upstream.
- [ ] Treat bare `gpt-5.6` as the Sol alias if the alias is supported by the model-catalog decision.
- [ ] Preserve the existing effort options for GPT-5, GPT-5.1, GPT-5.2, GPT-5.4, GPT-5 Pro, and unknown models.
- [ ] Avoid offering `ultra` for GPT-5.6 Luna.
- [ ] Add unit tests for schema, UI options, normalization, and outgoing request payloads.
- [ ] Add separate API integration coverage for the new effort values.
- [ ] Add separate ChatGPT saved-login integration coverage and run it with credentials from `~/.crystal`.
- [ ] Update reasoning documentation with the model-specific matrix and cost warning for `ultra`.
- [ ] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

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
