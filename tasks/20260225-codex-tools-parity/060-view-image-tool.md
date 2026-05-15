# 060 - Add Codex `view_image` tool plugin

Create a `view_image` tool in `plugins/codex-tools` that matches the current Codex CLI tool contract. The Responses path is the native source of truth: schema and tool output should be represented directly in Responses-compatible form. Chat-completions compatibility should be a downgrade/conversion path that preserves the same details, including the image as a data URL, even if the target provider ultimately sends it to the model as text.

## Requirements checklist

- [x] Add `codex_tools.view_image_tool.ViewImageTool` to `plugins/codex-tools` and register it in `plugins/codex-tools/agent_plugin.json`.
- [x] Match the current Codex CLI schema shape as closely as the platform allows: required `path`, optional `detail` gated by config/model capability, no alias parameters, no extra properties.
- [x] Load a local image file safely using the configured turn cwd and allowed paths.
- [x] Return a data URL plus detail metadata in the Codex output shape: `{"image_url": "...", "detail": ...}`.
- [x] Make the Responses path direct and native: the tool should produce a function-call output with `input_image` content rather than round-tripping through text.
- [x] Add a chat-completions conversion/fallback that preserves the full result details, including `image_url` data URL and `detail`, in a compatible text/JSON form.
- [x] Preserve a useful UI display payload without terminal/base64 spam.
- [x] Cover schemas, validation, path sandboxing, display fallback, and Responses-native image output with tests.
- [x] Update `plugins/codex-tools/README.md` and import/manifest tests.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`

## Current investigation

The old task note assumed `path` only and deferred true multimodal behavior. Upstream Codex has since made the contract more explicit.

### Upstream Codex CLI contract

Reference files inspected in `../codex`:

- `../codex/codex-rs/tools/src/view_image.rs:14` defines `create_view_image_tool`.
- `../codex/codex-rs/core/src/tools/handlers/view_image.rs:46` defines the runtime handler.
- `../codex/codex-rs/protocol/src/protocol.rs:3320` defines the UI/event notification payload.

Important upstream behavior:

- Tool name: `view_image`.
- Tool type: Responses function tool, not a custom/freeform tool.
- Description:
  `View a local image from the filesystem (only use if given a full filepath by the user, and the image isn't already attached to the thread context within <image ...> tags).`
- Input schema:
  - `path: string`, required, description `Local filesystem path to an image file`.
  - `detail: string`, optional only when `can_request_original_image_detail` is true. Description says the only supported value is `original`; omit for default resized behavior.
  - `additionalProperties: false`.
  - `strict: false`.
- Output schema:
  - object with required `image_url` and `detail`.
  - `image_url` is a data URL.
  - `detail` is `string | null`; upstream's schema description says it returns `original` when original resolution is preserved, otherwise `null`.
- Runtime:
  - Rejects the tool if the current model does not support image input.
  - Validates `detail`; only omitted or `"original"` is accepted.
  - Resolves the path against the turn cwd/environment.
  - Reads and decodes the file as an image.
  - Uses original bytes/detail only when both requested and supported; otherwise resizes to fit and sets default detail.
  - Emits a UI event with call id and path.
  - Sends the model a function-call output content item: `{"type": "input_image", "image_url": data_url, "detail": ...}`.

### Current platform shape

Relevant local files inspected:

- `plugins/codex-tools/agent_plugin.json:4` currently registers shell tools, legacy shell, apply_patch, and `CodexVariantFeature`; there is no `view_image` entry.
- `plugins/codex-tools/src/codex_tools/workdir.py:19` resolves the effective turn cwd from `working_directory`.
- `plugins/codex-tools/src/codex_tools/apply_patch_runtime.py:717` has the existing allowed-path sandbox pattern used by apply_patch.
- `core/python/agent_core/core.py:4339` formats tool results into a final core `tool` message with string `content` and display metadata.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:1590` already converts user/system/assistant `multipartContent` images into Responses `input_image` parts.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:1652` currently converts `role == "tool"` messages into `function_call_output` with string `output` only.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachment_parts.py:51` already contains reusable data URL conversion behavior for image multipart parts.

The key implementation rule is that the Responses path should not convert the image output to chat/text and then back again. `view_image` should produce structured Responses-compatible output directly. The chat-completions path is lower priority and should be a deliberate downgrade adapter/fallback that carries essentially the same information as text/JSON, including the data URL.

## Concrete implementation plan

### 1) Add the tool plugin

Create `plugins/codex-tools/src/codex_tools/view_image_tool.py`.

Recommended config keys:

- `working_directory`: same meaning as shell/apply_patch.
- `allowed_paths`: default `["."]`, same path sandbox semantics as apply_patch.
- `enable_view_image_detail_original`: default `false` unless a clean model-capability signal is already available in config/context.
- `view_image_max_bytes`: optional guardrail for raw file size before base64 encoding.
- `view_image_emit_native_image_output`: default `true` on Responses-capable paths if the provider/core support from step 3 is implemented; otherwise harmlessly falls back to text.

Schema behavior:

- For OpenAI Responses target formats, expose the native Responses function schema with `output_schema`.
- For OpenAI chat-completions target formats, use an explicit compatibility conversion to `{"type": "function", "function": ...}` rather than making chat the primary schema.
- Parameters object in both formats should contain `path`, and optionally `detail`.
- Required only `["path"]`.
- `additionalProperties: false`.
- `strict: false`.

Execution behavior:

- Accept only `tool_name == "view_image"`.
- Validate payload is a dict with a non-empty string `path`.
- Validate optional `detail` is exactly `"original"`; reject any other value with the upstream-style message.
- Resolve relative paths against `resolve_turn_cwd(config)`.
- Enforce `allowed_paths` after resolving symlinks.
- Reject missing paths, directories, unreadable files, and non-image files.
- Detect MIME from image magic bytes for at least PNG, JPEG, GIF, and WebP; do not rely on extension alone.
- Return:
  ```json
  {
    "success": true,
    "image_url": "data:image/png;base64,...",
    "detail": "original or high/null depending final decision",
    "path": "/abs/path",
    "mime_type": "image/png",
    "bytes": 1234
  }
  ```

Implementation note: upstream resizes large images via Rust `image` crate. This Python package currently has no Pillow dependency. For the first pass, prefer a conservative byte limit and exact data URL output over adding image resizing. If true resize-to-fit parity is required, add `Pillow` explicitly and test it.

Native output, formatting, and display:

- The canonical result should include a structured output item equivalent to:
  ```json
  {
    "type": "input_image",
    "image_url": "data:image/png;base64,...",
    "detail": "high or original"
  }
  ```
- On the Responses path, this structured item should be serialized directly as the tool/function-call output content. Do not convert it to text and then re-parse it.
- On the chat-completions path, convert the canonical result to a compatible text/JSON payload that preserves `image_url`, `detail`, `path`, `mime_type`, and byte metadata. If that provider later converts tool output to text for the model, it should still carry about the same details.
- `format_tool_result` should avoid dumping huge base64 in terminal display unless it is the actual provider-compatible text fallback being sent to a chat-completions model.
- `to_display_format` should return a display payload such as:
  ```json
  {
    "type": "image",
    "content": "data:image/png;base64,...",
    "mime_type": "image/png",
    "path": "/abs/path",
    "single_line": "view_image: image.png"
  }
  ```
  If existing terminal/mobile renderers only understand text, include a text fallback in `content` or document the renderer follow-up.

### 2) Register and document

- Add `codex_tools.view_image_tool.ViewImageTool` to `plugins/codex-tools/agent_plugin.json` `entries` and `kinds`.
- Update `plugins/codex-tools/src/codex_tools/__init__.py` if local package exports are maintained there.
- Update `plugins/codex-tools/README.md` with a "View Image" section and config keys.
- Update `plugins/codex-tools/tests/test_codex_tools_imports.py`.

### 3) Add direct Responses structured tool-output support, if absent

The current core/provider flow turns every final tool result into a core message with string `content` and metadata display only. The OpenAI Responses provider then creates:

```json
{"type": "function_call_output", "call_id": "...", "output": "...string..."}
```

Codex upstream instead sends a function-call output whose output body is content items containing `input_image`. This should be treated as the native representation, not as an optional enhancement after text formatting.

Recommended minimal platform extension:

- Let tool plugins include canonical structured output in a new generic field or metadata key, for example `metadata["tool_output_content"]` or a core-level equivalent.
- `AgentCore.iter_tool_messages` should preserve that structured output in the final tool message without formatting it to text first.
- `openai_responses_provider.to_native_messages` should detect this field for `role == "tool"` and emit `function_call_output.output` as the content-item list/object expected by Responses.
- The chat-completions tool-result adapter/fallback should convert the same canonical result to text/JSON, preserving the data URL and detail fields.
- Add tests before wiring the tool to prove a tool message with an image output becomes a native Responses `function_call_output` image content item and a chat-compatible fallback payload.

Keep this generic enough for future JS REPL or MCP image-emitting tools; do not make it hard-coded to `view_image`.

### 4) Tests

Add `plugins/codex-tools/tests/test_view_image_tool.py`:

- schema has required `path`, no aliases, `additionalProperties: false`.
- optional `detail` appears only when config enables it.
- invalid `detail` is rejected.
- missing file returns a model-facing error.
- directory path returns a model-facing error.
- non-image file returns a model-facing error.
- valid tiny PNG fixture returns `success: true`, a `data:image/png;base64,...` URL, `mime_type`, path, and detail.
- path outside `allowed_paths` is denied.
- display payload does not expose huge base64 in `single_line`.

Add provider/core tests if step 3 is included:

- `AgentCore.iter_tool_messages` preserves structured tool output from a fake tool result.
- `openai_responses_provider.to_native_messages` converts structured image tool output directly to a Responses `function_call_output` image content item.
- chat-completions fallback conversion preserves `image_url`, `detail`, `path`, and `mime_type` in the text/JSON tool result.
- Existing string-only tool result behavior remains unchanged.

Run:

```bash
pytest plugins/codex-tools/tests -q
pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q
pytest core/python/tests -q
```

## Acceptance criteria

- `view_image` is registered in the codex tool package and exposed as a function tool.
- The input schema matches current Codex CLI fields and descriptions closely, while using this platform's supported schema envelope.
- The tool safely reads only allowed local image files and returns a data URL result.
- On OpenAI Responses paths, the model receives the loaded image directly as an image content item after the tool call.
- On chat-completions paths, the model receives a compatible text/JSON tool result that preserves the image data URL and metadata.
- UIs receive a useful display payload without terminal/base64 spam.
- Tests cover both the new tool and any generic tool-output plumbing added for Responses.

## Completion Notes

Added during completion.

- Implemented `codex_tools.view_image_tool.ViewImageTool` and registered it in the codex-tools manifest.
- Added native Responses schema/output handling, including `output_schema` and structured `input_image` function-call output via `metadata.tool_output_content`.
- Added chat-completions compatibility by adding a Responses-function-schema-to-chat-schema adapter and preserving image details in JSON/text plus `multipartContent` for providers that support image parts.
- Added a checked-in text image fixture and real integration tests for OpenAI Responses `gpt-5.4-mini` and OpenRouter `openai/gpt-5.4-mini`; both read `CODEX VIEW IMAGE 7391` via the tool.
- Fixed existing codex shell tools to provide explicit `execute_tool_async` methods compatible with the current tool protocol wrapper.
- Added a provider fallback for `_session_asset_store` in OpenAI Responses unit-test state, matching existing test usage.

## Execution plan

Added during completion after user approval.

1. Add `ViewImageTool` in `plugins/codex-tools` with a Responses-native contract, safe image loading, path sandboxing, data URL output, display fallback, and chat-compatible JSON fallback.
2. Register/document the tool and update import/manifest tests.
3. Add generic structured tool-output plumbing so Responses can serialize `view_image` results directly as `function_call_output` image content items, while chat paths receive a detail-preserving text/JSON fallback.
4. Add unit tests for schema selection, validation, path safety, MIME detection, display, Responses native output, and chat fallback preservation.
5. Add real integration tests for OpenAI Responses `gpt-5.4-mini` and OpenRouter `openai/gpt-5.4-mini` using the same text-in-image fixture and requiring the model to read the text via `view_image`.
6. Run focused unit tests plus the requested integration tests using API keys from the root `.env`.