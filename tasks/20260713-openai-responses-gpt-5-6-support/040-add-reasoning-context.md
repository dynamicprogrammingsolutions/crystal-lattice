# Add Reasoning Context Preservation Controls

Add first-class `reasoning.context` support for `auto`, `current_turn`, and `all_turns`, including multi-turn verification that preserved reasoning items are actually available to later requests.

## Requirements checklist

- [ ] Add a first-class configuration key for `reasoning.context`.
- [ ] Support `auto`, `current_turn`, and `all_turns`.
- [ ] Preserve omission semantics and avoid sending undocumented values.
- [ ] Merge context with effort, mode, summary, encrypted-content include, and raw request options.
- [ ] Ensure `all_turns` works with the provider's retained/replayed native response history.
- [ ] Preserve or expose the effective response context mode when OpenAI returns it.
- [ ] Add focused unit tests for normalization, nested merging, and response metadata extraction.
- [ ] Add a separate multi-turn real API integration test.
- [ ] Add a separate multi-turn saved-login ChatGPT integration test and run it with credentials from `~/.crystal`.
- [ ] Update reasoning/history documentation with the prerequisites and first-turn behavior.
- [ ] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

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
