# Add GPT-5.6 Codex System Instructions

Import the GPT-5.6 Codex model-specific instruction templates from current Codex upstream and wire them into default configuration for Sol, Terra, Luna, and any supported bare alias.

## Requirements checklist

- [ ] Add exact upstream GPT-5.6 Codex instruction assets with source provenance.
- [ ] Preserve the Sol-specific instruction variant.
- [ ] Map Terra and Luna explicitly even though their templates are identical in the inspected upstream commit.
- [ ] Map bare `gpt-5.6` to the Sol instruction variant if the alias is supported.
- [ ] Update default-config model regex selection for OpenAI and `openai/`-prefixed IDs.
- [ ] Handle default, friendly, and pragmatic personality selection without inventing text absent from upstream.
- [ ] Mirror/update reference instruction assets and notices where required by the existing layout.
- [ ] Add unit/default-config tests for exact model-to-template selection and fallback behavior.
- [ ] Add a separate real API system-instruction integration test.
- [ ] Add a separate saved-login ChatGPT system-instruction integration test and run it with credentials from `~/.crystal`.
- [ ] Regenerate default-config documentation and update Codex instruction docs.
- [ ] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

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
