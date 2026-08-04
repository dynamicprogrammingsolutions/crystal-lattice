# Correct view_image OpenAI Responses output schema behavior

Fix the model-facing `view_image` schema/result behavior so it matches Codex CLI and works for both OpenAI Responses and OpenRouter. The normal tool schema must not include `output_schema`; success must still send image content to the model; failures must be covered by integration tests.

## Requirements checklist

- [x] Remove `output_schema` from the normal/model-facing `view_image` tool schema.
- [x] Preserve successful `view_image` model-facing image delivery for OpenAI Responses.
- [x] Preserve successful `view_image` model-facing image delivery for OpenRouter.
- [x] Ensure successful `view_image` output is a multipart/content-item result with an `input_image` item and no required JSON-string schema output.
- [x] Ensure failed `view_image` output is plain text and does not produce image content.
- [x] Run existing integration tests covering successful `view_image` behavior for both OpenAI Responses and OpenRouter.
- [x] Add integration tests for `view_image` failure cases.
- [x] Update relevant unit tests and docs that currently expect or document `output_schema` on the normal `view_image` schema.

## Context

The observed production failure came from replaying a session containing a failed `view_image` tool result:

```text
RuntimeError: OpenAI Responses stream failed: Error code: 400 - {'error': {'message': 'Invalid function_call_output.output: expected a JSON string because the function declares output_schema.', ...}}
```

The affected session contained a `view_image` tool message with:

- `metadata.tool_schema.output_schema` present.
- `content` / `toolResult.text` as plain text error: `Error: unable to locate image at ...`.

OpenAI Responses rejects that combination. If a function declares `output_schema`, the API expects `function_call_output.output` to be a JSON string matching the schema. But `view_image` success needs to send image content items, and failure should be plain text.

## Codex CLI research

In upstream Codex (`../codex`), model-facing `view_image` behavior is:

- The OpenAI Responses tool schema sent to the model does **not** include `output_schema`.
- Successful `view_image` result is a `function_call_output` whose `output` is an array containing exactly one `input_image` content item.
- Failed `view_image` result is a `function_call_output` whose `output` is plain text.

References:

- Upstream tool builder defines `view_image`, including the logical output schema internally: `../codex/codex-rs/tools/src/view_image.rs:28`.
- Upstream Responses tool type marks `output_schema` with `#[serde(skip)]`, so it is not serialized to the OpenAI Responses wire payload: `../codex/codex-rs/tools/src/responses_api.rs:25`.
- Upstream success output returns `FunctionCallOutputBody::ContentItems(vec![InputImage { ... }])`: `../codex/codex-rs/core/src/tools/handlers/view_image.rs:183`.
- Upstream test asserts no separate image message and exactly one `input_image` output item: `../codex/codex-rs/core/tests/suite/view_image.rs:335`.
- Upstream missing-file test asserts plain text error and no image item: `../codex/codex-rs/core/tests/suite/view_image.rs:1337`.

## Local code references

- `plugins/codex-tools/src/codex_tools/view_image_tool.py:96` defines `_output_schema()`.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:215` chooses whether the `detail` input parameter is exposed.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:221` currently includes `"output_schema": _output_schema()` in the normal schema. This is the key bug for model-facing tool use.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:365` formats failures as plain text. Preserve this behavior.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:371` formats successful OpenAI Responses tool output. It currently includes an `input_text` item plus an `input_image`; Codex CLI model-facing parity expects only the `input_image` item.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:1841` converts core tool messages to `function_call_output`.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:392` converts configured schemas into the OpenAI Responses request `tools` payload.
- `plugins/openrouter` and the OpenRouter provider path should be checked to ensure `view_image` still works after removing `output_schema` from the normal schema.

## Expected implementation direction

The minimal and preferred correction is to remove `output_schema` from the normal `view_image` schema emitted by `get_tool_schemas()`. Do not add `view_image`-specific stripping logic to generic provider/tool extensions.

After the change, the model-facing OpenAI Responses schema should be a regular function tool:

```json
{
  "type": "function",
  "name": "view_image",
  "description": "...",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "path": {"type": "string", "description": "Local filesystem path to an image file"}
    },
    "required": ["path"],
    "additionalProperties": false
  }
}
```

Success should remain provider-native image output. For exact Codex CLI parity, `view_image` should send only the `input_image` item as model-facing output while preserving human-readable display text in display metadata / fallback text.

Failure should remain plain text and should not attach an image part.

## Testing expectations

Existing integration test coverage to run and keep passing:

```bash
pytest application/python/tests/test_terminal_default_config_codex_view_image_real_api.py -m 'integration and api and openai' -q
pytest application/python/tests/test_terminal_default_config_codex_view_image_real_api.py -m 'integration and api and openrouter' -q
```

Add realistic integration tests for failure cases for both OpenAI Responses and OpenRouter. Cover at least:

- Missing image path.
- Non-image file or directory path if reasonably cheap to exercise.

The failure integration tests should verify:

- The request does not fail before generation because of `output_schema`.
- A `view_image` tool call occurred.
- The tool message/result is plain text error.
- No `input_image` item is emitted for failed tool output.

Also update focused unit tests:

- `plugins/codex-tools/tests/test_view_image_tool.py` should assert the normal schema does not include `output_schema`.
- `plugins/codex-tools/tests/test_view_image_tool.py` should assert success formatting preserves model-facing image output and failure formatting is plain text.
- OpenAI Responses provider/unit tests should continue to prove `function_call_output.output` supports content-item arrays.

## Documentation

Update `plugins/codex-tools/README.md`, which currently describes `view_image` as an OpenAI Responses function tool with `output_schema`. The docs should say the normal model-facing schema omits `output_schema`, and success returns image content items directly.

## Execution plan

Added during completion.

- Update `plugins/codex-tools/src/codex_tools/view_image_tool.py` so the normal `view_image` schema no longer includes `output_schema`, successful OpenAI Responses output contains only the `input_image` item, and failure output remains plain text.
- Update `plugins/codex-tools/tests/test_view_image_tool.py` to assert the schema omits `output_schema`, success output is image-only, and missing-file failures format as plain text.
- Check OpenAI Responses provider/tool-extension tests for coverage of content-item array tool outputs and add a focused regression if needed for schema-free failed `view_image` replay.
- Add realistic failure integration coverage in `plugins/codex-tools/tests/test_view_image_tool_integration.py` for OpenAI Responses and OpenRouter without requiring a real model to choose the failure path.
- Update `plugins/codex-tools/README.md`.
- Run focused unit tests first, then run the existing provider success integration tests if credentials/environment are available; report any gated tests that cannot run.

## Completion Notes

Added during completion.

- Removed `output_schema` from the normal `view_image` schema emitted by `plugins/codex-tools/src/codex_tools/view_image_tool.py`.
- Changed successful OpenAI Responses `view_image` formatting to return only an `input_image` content item in the provider-native tool result, while keeping human-readable display/fallback text.
- Preserved failure formatting as plain text.
- Updated unit tests for schema absence, image-only success output, asset-backed output, and missing-file plain-text failures.
- Added deterministic plugin-local integration coverage for failed `view_image` calls through both OpenAI Responses and OpenRouter provider wiring.
- Ran focused unit tests plus existing hosted API success integrations for OpenAI Responses and OpenRouter successfully.