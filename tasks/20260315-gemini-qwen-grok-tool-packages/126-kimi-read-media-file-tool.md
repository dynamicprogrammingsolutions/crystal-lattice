# 126 - Kimi ReadMediaFile Tool

Short description: Add Kimi CLI's `ReadMediaFile` tool to `plugins/kimi-tools`, using Kimi's filesystem media-reader behavior as the vendor source of truth and reusing lessons from the completed Codex `view_image` tool.

## Requirements checklist

- [x] Implement a `KimiReadMediaFileTool` exposed to the model as `ReadMediaFile`.
- [x] Match Kimi CLI's schema: a required `path` string with Kimi's path description.
- [x] Gate tool availability on model media capabilities, especially `image_in`; include `video_in` support if the platform can preserve video outputs cleanly.
- [x] Safely read local image files from the configured workspace/additional allowed directories and reject unsafe relative outside-workspace paths.
- [x] Detect media type from file content/header and reject text, unknown, empty, too-large, missing, and non-file paths with Kimi-style error wording.
- [x] Return image outputs in a model-visible media form equivalent to Kimi's `ImageURLPart` wrapped by `<image path="...">...</image>`.
- [x] Preserve useful metadata and display output for UIs without dumping large base64 strings in compact display text.
- [x] Add tests for schema, capability gating, path validation, image data URL output, error cases, and optional image-size reporting.
- [x] Register and document the tool in `plugins/kimi-tools`.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Related Task: `tasks/20260225-codex-tools-parity/060-view-image-tool.md`

## Goal

Port Kimi CLI's filesystem media-viewing tool into the local `kimi-tools` plugin package. Kimi does not have a tool named `view_image`; its equivalent is broader and named `ReadMediaFile`. It reads image and video files from the filesystem, converts them to model-visible media parts, and returns a short status message.

The first implementation should prioritize image parity because the platform already has a completed Codex `view_image` implementation and structured image-output plumbing. Video support should be implemented only if the current provider/core path can preserve video media outputs without degrading the model-visible result into an unusable text blob.

## Source References

Kimi CLI references from `../kimi-cli`:

- Implementation: `src/kimi_cli/tools/file/read_media.py`
- Description template: `src/kimi_cli/tools/file/read_media.md`
- Tests: `tests/tools/test_read_media_file.py`
- Tool key argument handling: `src/kimi_cli/tools/__init__.py`

Relevant completed local task:

- Codex `view_image` parity task: `tasks/20260225-codex-tools-parity/060-view-image-tool.md`

Important Kimi implementation details:

- Tool class/name: `ReadMediaFile`
- Parameter model:
  ```python
  class Params(BaseModel):
      path: str = Field(
          description=(
              "The path to the file to read. Absolute paths are required when reading files "
              "outside the working directory."
          )
      )
  ```
- Tool is skipped entirely when neither `image_in` nor `video_in` is supported.
- Maximum media size is `100MB`.
- Images are read as bytes and converted to `data:<mime>;base64,...`.
- Image output is an `ImageURLPart` wrapped with:
  ```text
  <image path="...">
  [image_url part]
  </image>
  ```
- Kimi optionally extracts original image dimensions via Pillow and includes `original size WxHpx` in the result message when available.
- Error handling distinguishes empty file, too large, text file, unknown media, unsupported model capability, missing path, directory path, and invalid outside-workspace relative paths.

## Compatibility Notes

### Relationship to Codex `view_image`

Codex's completed `view_image` task already added a local image reader with:

- safe path resolution
- image MIME detection
- data URL output
- compact display payload
- Responses-native structured `input_image` output via `metadata.tool_output_content`
- chat-compatible JSON/text fallback

Reuse that platform plumbing where it fits, but keep the model-facing Kimi contract distinct:

- Kimi tool name is `ReadMediaFile`, not `view_image`.
- Kimi parameter is only `path`; there is no `detail`.
- Kimi supports image and video conceptually; Codex `view_image` is image-only.
- Kimi returns media wrapped with `<image path="...">` or `<video path="...">` text markers, while Codex returns a Codex-shaped object with `image_url` and `detail`.
- Kimi's success message includes file kind, MIME type, byte size, optional original dimensions, and a coordinate/read-back note.

### Platform interpretation

For image outputs, prefer the same structured tool-output path used by Codex `view_image` so the model receives an actual image content item. The Kimi wrapper should produce Kimi-style surrounding text/media parts for LLM-visible output where the provider supports multipart tool output.

If a provider only supports text tool results, the fallback should preserve the data URL and Kimi metadata in a predictable JSON/text form rather than dropping the image payload.

For video outputs, investigate current provider support before implementation. If video content items are not supported, either defer video with clear tests/documentation or return a Kimi-style unsupported-capability error unless a provider path can carry video inputs.

## Proposed Implementation

Add `plugins/kimi-tools/src/kimi_tools/kimi_read_media_file_tool.py`.

Suggested class:

```python
class KimiReadMediaFileTool:
    name = "ReadMediaFile"
```

Configuration and context:

- Reuse existing `kimi-tools` / shared filesystem path handling from the Kimi core file tools.
- Support the current working directory config used by other vendor tools.
- Support allowed/additional directories consistently with `KimiReadFileTool`.
- Add an optional `kimi_read_media_max_bytes` config if there is no package-level media size setting; default to `100 * 1024 * 1024`.

Schema:

- Function tool named `ReadMediaFile`.
- Single required `path` property.
- Description should be loaded or mirrored from Kimi's `read_media.md`, including the capability-dependent "supports image/video files" section where practical.

Execution flow:

1. Validate `path` is present and non-empty.
2. Resolve and canonicalize path.
3. Enforce Kimi's outside-workspace rule: outside workspace/additional dirs is allowed only when the path is absolute.
4. Reject missing paths and directories.
5. Read enough bytes to detect media type.
6. Reject text files with: `` `<path>` is a text file. Use ReadFile to read text files. ``
7. Reject unknown files with Kimi's "seems not readable as an image or video file" wording.
8. Check model capability for the detected kind.
9. Enforce size limit and non-empty file checks.
10. Read bytes and convert supported image types to a data URL.
11. Return Kimi-style output with wrapped media part and message.

Image result shape can use an internal canonical structure similar to:

```json
{
  "success": true,
  "kind": "image",
  "path": "/abs/path.png",
  "mime_type": "image/png",
  "bytes": 1234,
  "image_url": "data:image/png;base64,...",
  "width": 3,
  "height": 4,
  "tool_output_content": [
    {"type": "text", "text": "<image path=\"/abs/path.png\">"},
    {"type": "input_image", "image_url": "data:image/png;base64,..."},
    {"type": "text", "text": "</image>"}
  ]
}
```

Adapt the final structure to the exact conventions already used in `plugins/kimi-tools` and the Codex structured-output plumbing.

## Tests

Add focused tests under `plugins/kimi-tools/tests/`, likely `test_kimi_read_media_file_tool.py`.

Cover:

- Schema name and required `path`.
- Tool skipped or hidden when no `image_in` / `video_in` capability is present, if the plugin framework supports capability-aware tool exposure.
- Tiny PNG read returns `data:image/png;base64,...` and Kimi-style wrapper parts.
- Extensionless PNG is accepted when content/header detection identifies it as an image.
- Optional Pillow dimension detection adds `original size WxHpx` when available.
- Missing path returns `File not found`.
- Directory path returns `Invalid path`.
- Empty file returns `Empty file`.
- Text file tells the model to use `ReadFile`.
- Unknown binary returns Kimi-style "not readable as an image or video file" error.
- Outside-workspace relative path is rejected with Kimi's absolute-path requirement.
- Image capability missing returns Kimi's unsupported media type message.
- Compact display text includes the filename/tool name but not the full data URL.

Run at minimum:

```bash
pytest plugins/kimi-tools/tests -q
pytest plugins/codex-tools/tests/test_view_image_tool.py -q
```

Add broader provider/core tests if new structured media-output plumbing is needed beyond what Codex `view_image` already added.

## Acceptance Criteria

- `ReadMediaFile` is registered in `plugins/kimi-tools` and appears only when appropriate for the configured model/tool context.
- Image files are safely loaded from allowed filesystem locations and delivered to the model as actual image content where supported.
- Kimi-style messages and wrapper text are preserved closely enough for model behavior and snapshot testing.
- Text, unknown, invalid, unsafe, empty, and too-large files produce clear Kimi-compatible errors.
- Documentation explains the tool, capability requirements, size limit, and current video support status.

## Execution plan

Added during completion after user approval.

1. Add reusable media-reader helpers to `tool-compat-shared` under `reader_engine.py`, including media sniffing, image/video classification, data URL generation, and optional Pillow-based image dimension extraction.
2. Implement `KimiReadMediaFileTool` in `plugins/kimi-tools`, exposed as `ReadMediaFile`, using existing Kimi path handling patterns plus the shared media helpers.
3. Gate schema exposure and media execution through explicit `kimi_read_media_capabilities` config for now, with `image_in` enabled by default and `video_in` only honored if configured.
4. Return Kimi-style image wrapper text plus structured image output via `tool_output_content` and `multipartContent`, reusing the provider/core plumbing added for Codex `view_image`.
5. Register and export the tool in `kimi-tools`, and update README/config documentation.
6. Add unit tests for shared media helpers and the Kimi tool: schema, capability gating, PNG/extensionless image reads, display payload, errors, size limit, and path validation.
7. Add an OpenRouter integration test using `moonshotai/kimi-k2.5`, loading API keys from the root `.env`, similar to the Codex `view_image` integration test.
8. Run focused shared/Kimi/Codex tests, then the new OpenRouter integration test if credentials and provider dependencies are available.

## Completion Notes

Added during completion.

- Added shared media-reader helpers to `tool-compat-shared`: `MediaFileType`, `MEDIA_SNIFF_BYTES`, `detect_media_file_type`, `media_data_url`, and optional Pillow-backed `extract_image_size`.
- Implemented `plugins/kimi-tools/src/kimi_tools/kimi_read_media_file_tool.py` with Kimi-compatible `ReadMediaFile` schema, path validation, media detection, Kimi-style errors, image data URL output, `<image path="...">` fallback formatting, `multipartContent`, and structured `tool_output_content`.
- Registered/exported `KimiReadMediaFileTool` and documented configuration keys `kimi_read_media_capabilities` and `kimi_read_media_max_bytes`.
- Added unit coverage for shared media detection/data URLs and Kimi `ReadMediaFile` schema, capability gating, PNG reads, extensionless image reads, display output, and error handling.
- Added and ran an OpenRouter integration test using `moonshotai/kimi-k2.5`; the model called `ReadMediaFile` and read the expected text from the image.
- Video files are detected and capability-gated, but model-visible video output remains deferred because the current provider path used here is image-focused.