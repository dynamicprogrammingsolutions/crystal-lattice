# 127 - Provider-Native Tool Result Payloads

Short description: Extend the framework so tool result formatting can return explicit provider-native structured payloads, allowing Kimi `ReadMediaFile` to return ordered text/image/text content equivalent to Kimi CLI without embedding base64 media bytes in ordinary text.

## Requirements checklist

- [x] Add an explicit provider-native tool result payload contract while preserving plain string tool results as the compatibility path.
- [x] Keep `ToolLoopRunner` provider-neutral: it must carry the formatted payload opaquely and must not understand OpenAI, Anthropic, Kimi, image parts, or provider-specific schemas.
- [x] Update core tool result/message plumbing so non-string formatted payloads can survive tool execution and session/message conversion.
- [x] Update provider adapters to consume provider-native payloads for their API type and optionally convert between known dialects when safe.
- [x] Update Kimi `ReadMediaFile` so `format_tool_result` returns OpenAI chat-completions-style ordered text/image/text content matching Kimi CLI semantics.
- [x] Keep existing text tools unchanged and covered by regression tests.
- [x] Update Codex `view_image` / OpenAI Responses behavior only where needed so the current Responses-native image output path remains supported and, if possible, uses the new shared payload contract.
- [x] Add unit and integration tests covering Kimi OpenRouter chat-completions media output without context blow-up.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/126-kimi-read-media-file-tool.md`

Related Task: `tasks/20260225-codex-tools-parity/060-view-image-tool.md`

## Problem

The first Kimi `ReadMediaFile` implementation exposed a framework limitation. The tool can read an image and produce a data URL, but the current framework mostly treats the model-facing tool result as a string:

- `ToolPlugin.format_tool_result` is typed and documented as returning `str` in `core/python/agent_core/types.py`.
- `ToolWrapper.format_tool_result` in `core/python/agent_core/plugin/tool.py` returns `str`.
- `AgentCore.iter_tool_messages` in `core/python/agent_core/core.py` calls `tool.format_tool_result(...)` and stores the result as the core tool message's `"content"`.
- `Message.content` is typed as `str` in `core/python/agent_core/types.py`.
- `DefaultToolAdapter.format_tool_result` in `core/python/agent_core/plugin/adapters.py` coerces non-string output with `str(out)`, which would destroy provider-native structure for adapted tools.

Because of this, the Kimi tool initially had two imperfect choices:

1. Put the full `data:image/...;base64,...` URL into the string fallback. This preserves the image for some chat-completions models but can explode prompt tokens when reading multiple images.
2. Omit the base64 from the string fallback and rely on `multipartContent`. This avoids the token blow-up but is not equivalent to Kimi CLI, and some providers/models may ignore image parts attached to `role: tool`.

The correct fix is not to hide the image in `multipartContent` or to put base64 in string text. The tool should be able to return an explicit provider-native structured result payload.

## Source Findings

### Kimi CLI behavior

Kimi CLI's `ReadMediaFile` in `../kimi-cli/src/kimi_cli/tools/file/read_media.py` returns a `ToolOk` whose output is a content-part list:

```python
[
    TextPart(text='<image path="...">'),
    ImageURLPart(image_url=ImageURLPart.ImageURL(url="data:image/png;base64,...")),
    TextPart(text="</image>"),
]
```

The wrapper is built by `../kimi-cli/src/kimi_cli/utils/media_tags.py`:

```python
def wrap_media_part(part, *, tag, attrs=None):
    return [
        TextPart(text=_format_tag(tag, attrs)),
        part,
        TextPart(text=f"</{tag}>"),
    ]
```

Kimi then converts the `ToolResult` into a tool message in `../kimi-cli/src/kimi_cli/soul/message.py` by preserving the content-part list. Provider adapters map those structured parts into provider-native forms. They do not require the image data URL to be tokenized as normal text.

### Current local Kimi implementation

`plugins/kimi-tools/src/kimi_tools/kimi_read_media_file_tool.py` currently returns image metadata plus:

- `tool_output_content`: OpenAI Responses-style structured output.
- `multipartContent`: local platform image attachment shape.
- `format_tool_result`: string fallback wrapped in Kimi-style `<image path="...">...</image>`.

The string fallback previously included the full data URL, which caused OpenAI-compatible providers to count base64 as prompt text. It was temporarily changed to omit the data URL, but that is only damage control and does not match Kimi CLI's semantic payload.

### Existing OpenAI Responses path

`plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` already has a structured output path for tool messages:

- For `role == "tool"`, it checks `metadata["tool_output_content"]`.
- If present and it is a list of dicts, it uses that as `function_call_output.output`.
- Otherwise it falls back to string `msg["content"]`.

This is why Codex `view_image` can work through OpenAI Responses: `plugins/codex-tools/src/codex_tools/view_image_tool.py` returns `tool_output_content` containing `{"type": "input_image", ...}`.

### Existing OpenAI-compatible chat path

`plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py` currently converts messages this way:

- If `msg["content"]` is not a string, it replaces it with `""`.
- If `multipartContent` exists, it creates chat-completions content parts beginning with `{"type": "text", "text": content}` and appends image parts from `multipartContent`.
- It does not understand an explicit provider-native tool-result payload envelope.

This means Kimi's ordered content cannot currently be represented as the canonical tool result. It can only be approximated as string text plus side-channel multipart image.

## Proposed Contract

Allow `format_tool_result` to return either a plain string or an explicit provider-native payload envelope.

Plain strings remain valid:

```python
"plain text tool result"
```

Structured provider-native payloads should use an envelope so adapters can distinguish them from ordinary JSON-like tool output:

```python
{
    "type": "provider_native_tool_result",
    "format": "openai.chat_completions",
    "content": [
        {"type": "text", "text": "<image path=\"/abs/path.png\">"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        {"type": "text", "text": "</image>"},
    ],
}
```

Responses-native payloads could use:

```python
{
    "type": "provider_native_tool_result",
    "format": "openai.responses",
    "output": [
        {"type": "input_text", "text": "<image path=\"/abs/path.png\">"},
        {"type": "input_image", "image_url": "data:image/png;base64,..."},
        {"type": "input_text", "text": "</image>"},
    ],
}
```

Anthropic-native payloads could use:

```python
{
    "type": "provider_native_tool_result",
    "format": "anthropic.messages",
    "content": [
        {"type": "text", "text": "<image path=\"/abs/path.png\">"},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}},
        {"type": "text", "text": "</image>"},
    ],
}
```

The initial implementation can focus on OpenAI chat-completions and OpenAI Responses. Anthropic can be documented as future adapter work unless an Anthropic provider exists locally and is easy to cover.

## Implementation Direction

1. Introduce a shared helper/type concept for provider-native tool result envelopes.
   - Candidate location: `core/python/agent_core/types.py` for public type aliases and helper docs.
   - Optional helper functions can live under `core/python/agent_core/tool_result_payloads.py` or similar if that matches local style.

2. Relax relevant type hints from `str` to JSON-like payloads.
   - `ToolPlugin.format_tool_result`
   - `ToolWrapper.format_tool_result`
   - `DefaultToolAdapter.format_tool_result` must stop coercing dict/list payloads with `str(out)`.
   - `Message.content` and `Message.from_dict` should accept at least string or JSON-like provider-native payloads, or the payload should be stored under a dedicated message field/metadata key. Prefer keeping the envelope in `"content"` so `ToolLoopRunner` stays provider-neutral.

3. Keep `ToolLoopRunner` provider-neutral.
   - `AgentCore.iter_tool_messages` may carry the formatted payload as `tool_message["content"]`.
   - It may pass a text fallback to `to_display_format`, but it should not parse provider-native parts.
   - Do not add provider-specific branches to `ToolLoopRunner`.

4. Teach provider adapters to consume envelopes.
   - `reference_openai_compatible_provider.provider.OpenAICompatibleProvider.to_native_messages` should detect `role == "tool"` with a provider-native envelope.
   - If `format == "openai.chat_completions"`, set the native message `content` to the envelope's `content` list and preserve `tool_call_id`.
   - Existing plain string behavior remains unchanged.
   - Existing `multipartContent` behavior remains for user/assistant attachments and compatibility.

5. Teach OpenAI Responses adapters/providers to consume envelopes.
   - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` should convert `format == "openai.responses"` directly to `function_call_output.output`.
   - Optionally convert `format == "openai.chat_completions"` text/image_url parts to Responses `input_text`/`input_image` output items.
   - Mirror the same behavior in `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`, which currently has a simpler string-only `function_call_output` path.
   - Preserve the existing `metadata.tool_output_content` path for Codex `view_image` until tools are migrated.

6. Update Kimi `ReadMediaFile`.
   - `format_tool_result` should return an `openai.chat_completions` provider-native envelope with ordered text/image/text parts.
   - The text parts should include Kimi's system/status message and `<image path="...">` wrapper.
   - The image part should be `{"type": "image_url", "image_url": {"url": data_url}}`.
   - Keep display output compact and base64-free.

7. Review Codex `view_image`.
   - Current OpenAI Responses integration relies on `tool_output_content` and `multipartContent`.
   - Do not break this path.
   - Consider adding an OpenAI Responses provider-native envelope to `format_tool_result` only if it does not disrupt Codex's existing model-facing format. This may be better as a second step after the framework accepts envelopes.

## Tests To Add Or Change

Core/framework tests:

- Add a test that a tool returning a provider-native envelope from `format_tool_result` is preserved by `AgentCore.execute_tool_calls`.
- Add a regression test that plain string `format_tool_result` behavior is unchanged.
- Add a test for `DefaultToolAdapter.format_tool_result` preserving dict/list payloads instead of coercing to string.

OpenAI-compatible provider tests:

- Extend `plugins/reference-openai-compatible-provider/tests/test_provider_multipart_conversion_unit.py` or add a focused test:
  - Input core tool message content is an `openai.chat_completions` envelope.
  - Native output is `{"role": "tool", "tool_call_id": "...", "content": [text, image_url, text]}`.
  - No base64 appears in a text part.

OpenAI Responses tests:

- Add unit tests under `plugins/openai_responses/tests/` for tool message envelope conversion:
  - `openai.responses` envelope goes directly to `function_call_output.output`.
  - Optional `openai.chat_completions` envelope converts to Responses `input_text`/`input_image`.
  - Existing `metadata.tool_output_content` still works for Codex `view_image`.
- Add equivalent unit coverage under `plugins/openrouter_responses/tests/` if that plugin has tests available.

Kimi tests:

- Update `plugins/kimi-tools/tests/test_kimi_read_media_file_tool.py`:
  - Assert `format_tool_result` returns a provider-native envelope.
  - Assert ordered content parts are text/image_url/text.
  - Assert base64 is only in the image part, never inside text parts.
- Update `plugins/kimi-tools/tests/test_kimi_read_media_file_tool_openrouter_integration.py`:
  - Remove any expected xfail/placeholder behavior.
  - Verify OpenRouter `moonshotai/kimi-k2.5` can call `ReadMediaFile` and read fixture text without context-length failure.

Codex tests:

- Rerun `plugins/codex-tools/tests/test_view_image_tool.py`.
- Rerun `plugins/codex-tools/tests/test_view_image_tool_integration.py` when credentials are available.
- Add/adjust tests only if Codex `view_image` adopts the new envelope contract.

## Suggested Test Commands

Focused unit tests:

```bash
pytest core/python/tests/test_tool_result_payloads.py -q
pytest plugins/reference-openai-compatible-provider/tests/test_provider_multipart_conversion_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_tool_result_payloads.py -q
pytest plugins/openrouter_responses/tests/test_openrouter_responses_tool_result_payloads.py -q
pytest plugins/kimi-tools/tests/test_kimi_read_media_file_tool.py -q
pytest plugins/codex-tools/tests/test_view_image_tool.py -q
```

Focused integration tests:

```bash
pytest plugins/kimi-tools/tests/test_kimi_read_media_file_tool_openrouter_integration.py -q -m openrouter
pytest plugins/codex-tools/tests/test_view_image_tool_integration.py -q -m "openai or openrouter"
```

Broader regression, if time permits:

```bash
pytest core/python/tests -q
pytest plugins/reference-openai-compatible-provider/tests -q
pytest plugins/openai_responses/tests -q
pytest plugins/openrouter_responses/tests -q
pytest plugins/kimi-tools/tests -q
pytest plugins/codex-tools/tests -q
```

## Acceptance Criteria

- Kimi `ReadMediaFile` can return the equivalent of Kimi CLI's ordered text/image/text content without encoding image bytes into ordinary text.
- OpenAI-compatible chat providers pass `openai.chat_completions` envelope content through as native tool message content.
- OpenAI Responses providers understand either `openai.responses` envelopes or safe conversion from OpenAI chat-completions envelopes.
- Existing string-based tools continue to work without changes.
- Existing Codex `view_image` behavior remains green.
- The OpenRouter Kimi integration test no longer depends on a base64 text fallback and no longer risks context blow-up when multiple images are read.

## Execution plan

Added during completion after user approval.

1. Add small provider-native tool result payload helpers in `agent_core` so tools and providers share the same envelope checks/conversions.
2. Relax the core `format_tool_result`/message typing enough to preserve JSON-like payloads, and update the default tool adapter so it no longer coerces structured payloads to strings.
3. Keep `AgentCore.iter_tool_messages` and `ToolLoopRunner` provider-neutral: preserve the formatted payload as the tool message content, and derive only a generic text fallback for display hooks.
4. Update chat-completions providers that own their own native conversion:
   - `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
   - `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
5. Update Responses providers:
   - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
   - `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
6. Update `KimiReadMediaFileTool.format_tool_result` to return an `openai.chat_completions` envelope with ordered Kimi-style text/image/text parts.
7. Add focused framework/provider/Kimi tests, rerun Codex `view_image` tests to guard the existing OpenAI Responses path, and rerun the OpenRouter Kimi integration test.

## Completion Notes

Added during completion.

- Added `agent_core.tool_result_payloads` with explicit provider-native tool-result envelopes and OpenAI chat-completions/Responses conversion helpers.
- Relaxed core tool-result/message plumbing so structured payloads survive `format_tool_result`, `AgentCore.iter_tool_messages`, `execute_tool_calls`, and session addition while preserving existing string tool results.
- Updated OpenRouter chat, reference OpenAI-compatible chat, OpenAI Responses, and OpenRouter Responses providers to consume the new envelopes.
- Updated Kimi `ReadMediaFile` to return an `openai.chat_completions` ordered text/image_url/text payload from `format_tool_result`, matching Kimi CLI's semantic content-part shape without embedding base64 in ordinary text.
- Left Codex `view_image` on its existing `metadata.tool_output_content` Responses path and verified it still works.
- Added provider/core/Kimi tests and reran the live Kimi/OpenRouter and Codex `view_image` integrations successfully.
- Ran an explicit old-style text-tool compatibility sweep covering core execute-tool behavior plus Kimi read/write/edit/search tools and Codex shell/apply-patch tests.
- Updated plugin authoring/tool-result documentation in `plugins/docs` and related API/reference docs to describe the additive `str | provider_native_tool_result` contract.