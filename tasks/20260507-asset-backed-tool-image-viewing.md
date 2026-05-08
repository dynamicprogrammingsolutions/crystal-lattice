# Asset-backed viewing for tool-opened images

Enable images opened by Codex `view_image` and Kimi `ReadMediaFile` to appear inline in chat and open through the existing full-size image workflow. Image previews and asset references must be written by tools/plugins/providers at message creation time; server endpoints must not enrich, mutate, or add preview/media fields to messages.

## Requirements checklist

- [x] Store images opened by `view_image` and `ReadMediaFile` as session assets when tool execution context includes `session_asset_store` and `session_id`.
- [x] Emit frontend-ready image `multipartContent` directly from the tool/plugin/provider, including `asset_ref`, filename, MIME type, preview bytes, preview MIME type, and `metadata.download_plugin_id`.
- [x] Keep the current data-URL fallback when no session asset store is available, so pure core/tool contexts continue to work.
- [x] Preserve model-visible image payloads such as `metadata.tool_output_content` or provider-native image content for providers that need them.
- [x] Ensure frontend/API-visible tool message `content` is always a string, including for Kimi `ReadMediaFile` provider-native tool result paths.
- [x] Add or reuse a generic session-asset attachment/download action that is independent of OpenRouter/OpenAI-specific attachment extensions.
- [x] Remove server-side message preview enrichment entirely, including code that injects previews, filenames, MIME types, or missing-asset markers into listed messages.
- [x] Update existing providers and tests that currently rely on server-side enrichment so previews are produced by plugins/providers instead.
- [ ] Verify mobile inline preview and full-size open/download behavior using the existing attachment viewer workflow.
- [x] Wire desktop message attachment opening if thumbnails are currently display-only.
- [x] Add or update backend, tool, frontend SDK, mobile, and desktop tests as appropriate.

## Background

The platform now has image-opening tools:

- Codex `view_image` in `plugins/codex-tools/src/codex_tools/view_image_tool.py`.
- Kimi `ReadMediaFile` in `plugins/kimi-tools/src/kimi_tools/kimi_read_media_file_tool.py`.

Both tools already create useful image output for the model and UI, but they currently use data URLs directly in tool results. The application also has an asset-backed image-generation workflow from the OpenRouter image-generation provider. That workflow is a better pattern for user-facing image display because it separates:

- a durable full-size media file in `FilesystemSessionAssetStore`
- a message `multipartContent` part containing an `asset_ref`
- inline preview data for the thumbnail/viewer
- a `download_plugin_id` that lets the frontend fetch the original image through `downloadSessionAttachment()`

The key architectural correction for this task is that preview enrichment must not happen in the HTTP server. Message-producing plugins/tools/providers should write complete frontend-ready message data. Server endpoints should return stored message data without presentation-oriented mutation.

## Hard architecture constraint: remove server enrichment

The current server contains message preview enrichment in `application/python/agent_terminal_app/server.py` around `_enrich_multipart_part_for_client()` and `_enrich_message_for_client()` (current investigation found this around lines 336-406), and `list_session_messages()` calls `_enrich_message_for_client()` before returning messages (around lines 2960-3010).

This enrichment must be removed, not simplified. In particular, server endpoints must not:

- inspect `multipartContent` for `content.asset_ref`
- load `SessionAssetStore` during message listing to add presentation data
- inject `filename`
- inject `mime_type`
- inject `preview_data_base64`
- inject `preview_mime_type`
- add `metadata.asset_missing`

The replacement behavior is that stored messages already contain whatever preview/media fields the frontend needs. A bare `asset_ref` should remain bare when listed.

Existing tests that assert server enrichment should be removed or replaced. In particular:

- `application/python/tests/test_session_asset_message_preview_enrichment.py`

Replace this coverage with tests proving:

- listing messages returns stored `multipartContent` unchanged
- the server does not inject preview fields for a bare `asset_ref`
- the server does not add `asset_missing`
- plugin/provider-created preview fields roundtrip exactly

## Existing tool output shapes

### Codex `view_image`

File: `plugins/codex-tools/src/codex_tools/view_image_tool.py`

Relevant current behavior:

- `execute_tool()` reads a local image, detects MIME type, and builds a data URL.
- It returns `tool_output_content` with an `input_image`.
- It returns `multipartContent` similar to:

```json
[
  {
    "type": "image",
    "content": {"url": "data:image/png;base64,..."},
    "metadata": {"detail": "high", "path": "/abs/path.png"}
  }
]
```

- `to_display_format()` returns a compact display payload with:
  - `type: "image"`
  - `content: <data url>`
  - `mime_type`
  - `path`
  - `single_line`
  - `text_fallback`

This should become asset-backed when application context is present, while preserving the data-URL fallback for lower-level core/tool usage.

### Kimi `ReadMediaFile`

File: `plugins/kimi-tools/src/kimi_tools/kimi_read_media_file_tool.py`

Relevant current behavior:

- `execute_tool()` reads image files, detects MIME type, and builds a data URL.
- It returns `tool_output_content` with an `input_image`.
- It returns `multipartContent` similar to:

```json
[
  {
    "type": "image",
    "content": {"url": "data:image/png;base64,..."},
    "metadata": {"path": "/abs/path.png", "mime_type": "image/png"}
  }
]
```

- `format_tool_result()` can return a provider-native tool result object containing OpenAI chat-completions style text/image parts.
- `to_display_format()` returns a compact image display payload.

Important contract issue: frontend SDK messages require `content` to be a string. The provider-native object is useful for provider/model submission, but the stored/frontend-visible tool message content must remain string-safe. Preserve provider-native/model-visible payloads elsewhere, such as metadata or the provider/tool interop path, without exposing non-string `content` in API-visible messages.

## Existing asset-backed image-generation pattern

The OpenRouter image-generation provider is the strongest existing pattern to mirror, with the correction that preview fields should be produced by the provider, not the server.

Important files:

- `plugins/openrouter/src/openrouter_plugins/openrouter_image_generation_provider.py`
- `plugins/openrouter/src/openrouter_plugins/openrouter_image_generation_attachments_extension.py`
- `core/python/agent_app/session_assets.py`

Current useful pieces:

- `FilesystemSessionAssetStore` stores blobs and manifests and returns `asset_ref` descriptors.
- OpenRouter image generation stores generated images as session assets.
- It emits assistant image `multipartContent` with:
  - `type: "image"`
  - `content.asset_ref`
  - `content.filename`
  - `content.mime_type`
  - `metadata.download_plugin_id`
- The frontend can use `download_plugin_id` with `downloadSessionAttachment()` to fetch the original image.

Current problem:

- The inline preview may be added by server-side enrichment when listing messages. Move preview production into the provider output itself.
- For generated images, the provider already has the bytes while storing the asset, so it can also include:

```json
{
  "preview_data_base64": "...",
  "preview_mime_type": "image/png"
}
```

directly in the stored assistant message part.

## Target message shape

When a tool opens an image under `AgentApplication` and has session asset context, the resulting tool message should include a part like:

```json
{
  "type": "image",
  "content": {
    "asset_ref": {
      "kind": "session_asset",
      "session_id": "sess_...",
      "asset_id": "asset_...",
      "attachment_type": "image"
    },
    "filename": "screenshot.png",
    "mime_type": "image/png",
    "preview_data_base64": "...",
    "preview_mime_type": "image/png"
  },
  "metadata": {
    "download_plugin_id": "session_asset_attachments",
    "source_tool": "view_image",
    "path": "/abs/path/screenshot.png"
  }
}
```

The tool message itself should be frontend-compatible:

```json
{
  "role": "tool",
  "content": "view_image: screenshot.png",
  "multipartContent": [
    {
      "type": "image",
      "content": {
        "asset_ref": "...",
        "filename": "screenshot.png",
        "mime_type": "image/png",
        "preview_data_base64": "...",
        "preview_mime_type": "image/png"
      },
      "metadata": {
        "download_plugin_id": "session_asset_attachments",
        "source_tool": "view_image",
        "path": "/abs/path/screenshot.png"
      }
    }
  ],
  "metadata": {
    "display": {
      "type": "image",
      "single_line": "view_image: screenshot.png"
    },
    "tool_output_content": [
      {"type": "input_image", "image_url": "data:image/png;base64,..."}
    ]
  }
}
```

The exact metadata can be adapted to local conventions, but the stored message must include enough preview data for the frontend and enough asset metadata to download the full-size image without server enrichment.

## Generic session-asset download action

Current frontend helper defaults are provider-specific:

- `packages/frontend-sdk/src/plugins/attachmentActions.ts`
- default plugin id is currently `openai_responses_attachments`
- OpenRouter image-generation test passes an explicit `openrouter_image_generation_attachments` plugin id

Tool-opened images should not depend on OpenRouter/OpenAI-specific attachment extensions. Add or reuse a generic session-asset attachment action plugin, likely named:

```text
session_asset_attachments
```

Minimum required action:

- `download_attachment`

Potential optional actions, if useful for consistency:

- `store_attachment`
- `delete_attachment`

The action should load the requested session asset from `SessionAssetStore` and return:

```json
{
  "attachment_asset": {
    "asset_ref": {
      "kind": "session_asset",
      "session_id": "...",
      "asset_id": "...",
      "attachment_type": "image"
    },
    "filename": "screenshot.png",
    "mime_type": "image/png"
  },
  "data_base64": "..."
}
```

Make sure the frontend can use this plugin id through `downloadSessionAttachment()`.

## Frontend SDK integration tests found

### Real OpenRouter image-generation workflow

File: `packages/frontend-sdk/src/integration/__tests__/backend.image_attachments.integration.test.ts`

Script:

```bash
npm run integration:backend:openrouter-images
```

Gate:

```bash
RUN_BACKEND_OPENROUTER_INTEGRATION=1
OPENROUTER_API_KEY=...
```

Optional env:

```bash
OPENROUTER_BASE_URL=...
OPENROUTER_IMAGE_GENERATION_E2E_MODEL=google/gemini-2.5-flash-image
```

This integration test currently:

- starts a real FastAPI backend with the OpenRouter image-generation plugin
- sends a simple image-generation prompt
- waits for an assistant message with image `multipartContent`
- checks `selectAttachmentPreviewUrl(simplePart.content)` returns a `data:image/...` URL
- stores a source input image via `storeSessionAttachment()`
- sends that input image by `asset_ref`
- waits for generated image output
- checks `generatedPart.metadata.download_plugin_id`
- calls `downloadSessionAttachment()` and verifies the downloaded full-size data is non-empty

This is the main frontend SDK integration workflow to mirror or complement for tool-opened images.

New or changed frontend SDK integration coverage should:

- start a backend with the relevant image-opening tool config plus the generic session-asset download action
- create or reference a local fixture PNG
- force or prompt a `view_image` or `ReadMediaFile` tool call
- wait for a tool message with image `multipartContent`
- assert `selectAttachmentPreviewUrl(toolImagePart.content)` returns `data:image/...`
- assert `toolImagePart.content.asset_ref.asset_id` exists
- assert `toolImagePart.metadata.download_plugin_id` is the generic session-asset plugin id
- call `downloadSessionAttachment()` with that plugin id
- assert downloaded bytes/base64 match the fixture when possible, or at least are non-empty and image-typed

### General backend integration test relying on server enrichment

File: `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`

Test name:

```text
F2: uploaded attachment previews are present in frontend-visible user messages
```

This currently:

- stores an image asset
- appends a user message with only an `asset_ref`, filename, and MIME type
- lists messages
- expects preview data to be present

That expectation is now wrong because it relies on server-side enrichment. Update it so either:

- the appended message already includes `preview_data_base64` and the test asserts exact roundtrip, or
- a new negative test appends a bare `asset_ref` and asserts it remains bare after `listMessages()`

Both are useful, but the negative test is important because it protects the server boundary.

### OpenAI attachment integration

File: `packages/frontend-sdk/src/integration/__tests__/backend.openai.integration.test.ts`

This real OpenAI Responses integration stores an attachment through the SDK action helper and sends it by `asset_ref` to a vision-capable model. It verifies the send path, not the generated-image/full-size download path. It may not need direct changes unless default attachment plugin ids or action contracts change.

### Unit tests for frontend helpers

Files:

- `packages/frontend-sdk/src/attachments/preview.test.ts`
- `packages/frontend-sdk/src/plugins/__tests__/attachmentActions.test.ts`

Existing coverage:

- `selectAttachmentPreviewUrl()` builds preview data URLs from `preview_data_base64`
- `selectAttachmentPreviewUrl()` returns null for bare `asset_ref`
- `downloadSessionAttachment()` forwards explicit plugin id overrides
- `storeSessionAttachment()` and `deleteSessionAttachment()` use the provider-extension action contract

Add or update tests if introducing a new generic plugin id or changing frontend defaults.

## Mobile and desktop notes

Mobile already has most of the image viewer path:

- message bubbles render `multipartContent` thumbnails
- `AttachmentViewerHost` uses `selectAttachmentPreviewUrl()` for inline display
- `AttachmentViewerHost` uses `downloadSessionAttachment()` for full-size asset download

Relevant files:

- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- `mobile/crystal-lattice-control-rn/src/components/AttachmentViewerHost.tsx`
- `mobile/crystal-lattice-control-rn/src/messageAttachments.ts`

Desktop currently renders `multipartContent` thumbnails in message bubbles, but investigation did not confirm an equivalent open/viewer callback for message attachments.

Relevant files:

- `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/AttachmentThumbnailStrip.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`

If thumbnails are display-only, add desktop attachment opening with the same asset-backed content shape.

## Suggested implementation steps

1. Add a generic session-asset attachment action plugin, probably `session_asset_attachments`, with at least `download_attachment`.
2. Update frontend SDK attachment helpers only if needed so callers can use the generic plugin id cleanly.
3. Update `view_image`:
   - accept optional `context` in `execute_tool()`
   - when `session_asset_store` and `session_id` are available, store the image bytes as a session asset
   - emit asset-backed `multipartContent` with preview fields and generic `download_plugin_id`
   - keep the existing data-URL fallback without app context
4. Update Kimi `ReadMediaFile` with the same asset-backed behavior and fallback.
5. Ensure tool-result messages use string `content` even when provider-native tool results are needed for model submission.
6. Update OpenRouter image-generation provider to include preview fields directly in stored assistant messages.
7. Remove server-side enrichment functions and all calls to them.
8. Replace Python server enrichment tests with no-mutation/roundtrip tests.
9. Update frontend SDK integration tests:
   - keep `backend.image_attachments.integration.test.ts` passing without server enrichment
   - add or mirror a tool-image integration using `downloadSessionAttachment()`
   - update `backend.integration.test.ts` F2 to stop relying on enrichment
10. Verify mobile viewer path.
11. Add desktop open/viewer behavior if needed.

## Suggested verification commands

Run focused Python tests after implementation:

```bash
pytest plugins/codex-tools/tests/test_view_image_tool.py -q
pytest plugins/kimi-tools/tests/test_kimi_read_media_file_tool.py -q
pytest application/python/tests/test_session_asset_message_preview_enrichment.py -q
pytest application/python/tests/test_agent_terminal_app_server.py -q
```

The `test_session_asset_message_preview_enrichment.py` file is expected to be removed or replaced; adjust the command to the replacement test file.

Run frontend SDK unit/integration tests:

```bash
cd packages/frontend-sdk
npm test -- src/attachments/preview.test.ts src/plugins/__tests__/attachmentActions.test.ts
npm run integration:backend
```

Run the real OpenRouter image workflow when credentials are available:

```bash
cd packages/frontend-sdk
RUN_BACKEND_OPENROUTER_INTEGRATION=1 npm run integration:backend:openrouter-images
```

If a new tool-image frontend SDK integration script/test is added, run it as part of verification.

Run existing real tool/image tests when credentials are available:

```bash
pytest application/python/tests/test_terminal_default_config_codex_view_image_real_api.py -q
pytest plugins/kimi-tools/tests/test_kimi_read_media_file_tool_openrouter_integration.py -q
```

## Acceptance criteria

- Server list/message endpoints return stored message data unchanged.
- Server-side preview enrichment code and tests are removed.
- Bare `asset_ref` message parts remain bare after `listMessages()`.
- Plugin/provider-created preview fields roundtrip exactly.
- Tool-opened images show inline previews in chat.
- Tool-opened images open/download full size through the same asset-download workflow as generated images.
- Existing OpenRouter generated-image workflow still works without server enrichment.
- Frontend SDK OpenRouter image integration remains passing, and a new or mirrored integration covers tool image download.
- Tool messages remain frontend-compatible with string `content`.

## Execution plan

Added during completion after user approval.

1. Add a generic session asset attachment application plugin under `plugins/`, with plugin id `session_asset_attachments` and at least a `download_attachment` action returning `{attachment_asset, data_base64}` from `FilesystemSessionAssetStore`.
2. Add or reuse a shared image asset helper so Codex, Kimi, and OpenRouter can store bytes once and emit the same frontend-ready `multipartContent` shape with `asset_ref`, filename, MIME type, preview bytes, preview MIME type, and `metadata.download_plugin_id`.
3. Update Codex `view_image` to accept optional execution `context`, store the original image in the session asset store when `session_asset_store` and `session_id` are available, and keep the current data-URL fallback when application context is absent.
4. Update Kimi `ReadMediaFile` with the same asset-backed/fallback behavior while preserving model-visible image payloads.
5. Ensure API/core-visible tool messages always have string `content`. Provider/model-facing structured tool result payloads should be converted through native history, not exposed as public message content. The native message should preserve the structured model payload plus enough `_metadata` to reconstruct the public message without recomputing previews.
6. Fix tool-loop persistence so `multipartContent` from final tool messages is passed into `core.add_message()`; otherwise previews can appear in transient events but disappear from stored/listed messages.
7. Avoid repeated image resizing/preview generation by writing preview fields at message creation time and roundtripping them through native `_metadata` during native-to-core rebuild. Rebuilds should copy stored `multipartContent`, not reload assets or regenerate preview bytes. Provider-specific resized/model-upload representations should be cached against the session asset/provider refs when needed.
8. Update OpenRouter image generation to include preview fields directly in generated assistant `multipartContent`.
9. Remove server-side message preview enrichment and update server tests to prove listed messages are unchanged, bare `asset_ref` parts remain bare, missing assets are not marked by listing, and plugin/provider-created preview fields roundtrip exactly.
10. Update frontend SDK constants/tests for the generic `session_asset_attachments` plugin id and adjust integration expectations that currently rely on server enrichment.
11. Verify mobile's existing viewer path works with the new shape, and wire desktop message attachment opening if thumbnails are currently display-only.
12. Run focused Python and frontend tests, then report any gated/credentialed tests not run.

## Completion Notes

Added during completion.

- Added `plugins/session-asset-attachments`, an application plugin exposing generic `session_asset_attachments.download_attachment`.
- Updated Codex `view_image` and Kimi `ReadMediaFile` to store opened images as session assets when tool context has `session_asset_store` and `session_id`; both keep data-URL fallback behavior without app context.
- Tool messages now keep frontend/API `content` as a string. Structured provider-native tool result payloads are carried through a temporary private top-level `_provider_native_tool_result` handoff only while appending to native history; they are not stored in public core message metadata. Follow-up cleanup is tracked in `tasks/20260508-tool-result-interop-accessors-adapters.md`.
- Tool-loop persistence now passes `multipartContent` to `core.add_message()`. Core native-history rebuilds roundtrip `_core_multipartContent` so stored preview data is copied back instead of regenerated.
- Removed HTTP server message-list enrichment; `list_session_messages()` now returns stored `msg.to_dict()` unchanged.
- Updated OpenRouter image generation to include preview bytes in provider-created assistant image parts and to roundtrip preview fields through native `image_asset` parts.
- Updated frontend SDK attachment actions with `SESSION_ASSET_ATTACHMENTS_PLUGIN_ID`; download calls for that plugin use `action_owner: "application"`.
- Added desktop message attachment opening with a modal image viewer that displays preview immediately and downloads full-size session assets when `download_plugin_id` is present.
- Added/updated focused tests for tool asset output, no server enrichment, tool-loop persistence, generic session asset download action, provider-native string-content behavior, and frontend attachment actions.