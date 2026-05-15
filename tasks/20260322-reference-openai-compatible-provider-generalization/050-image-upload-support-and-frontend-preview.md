# Reference Provider Image Upload Support And Frontend Preview

Add image upload support to `reference-openai-compatible-provider`, reusing the existing session-owned attachment upload path where practical, and verify both provider send behavior and frontend preview delivery for Ollama and Fireworks.

## Requirements checklist

- [x] Add image attachment support to the reference OpenAI-compatible provider using local application-owned file storage plus base64 conversion at send time; do not sanitize retained native history afterward.
- [x] Support both inline base64 images and image URLs through a provider/agent config setting, with both enabled by default and either mode individually disableable.
- [x] Reuse the existing attachment upload UX contract so client-selected images upload to the application and become `asset_ref`-backed multipart parts before send.
- [x] Ensure frontend-visible user messages include image preview payloads for stored attachments, and cover this in tests.
- [x] Test Fireworks with both image URL and base64 image flows.
- [x] Test Ollama with base64 image flow only.

Parent Task: `tasks/20260322-reference-openai-compatible-provider-generalization/000-main.md`

## Context and findings

The reference provider currently has no composer attachment UI and no multipart/image conversion path:

- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
  - `get_ui_elements(...)` currently emits only endpoint/model UI.
  - `to_native_messages(...)` currently treats message content as plain text/tool-call-only history.

The closest existing transport implementation is OpenRouter:

- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
  - emits an image `composer_attachment`
  - converts `multipartContent` image parts into chat-completions `content` parts using `{"type":"image_url","image_url":{"url":...}}`
  - accepts either remote image URLs or locally-provided `data:` URLs

The existing local-upload/session-asset flow is already implemented for OpenAI Responses:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachments_extension.py`
  - owns `store_attachment` / `delete_attachment`
  - persists files into the application-owned session asset store
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachment_parts.py`
  - resolves `asset_ref` to inline `data:` URLs for images
- `core/python/agent_app/application_future.py`
  - decorates effective config with `_session_asset_store`
- `application/python/agent_terminal_app/server.py`
  - enriches `asset_ref` image parts with `preview_data_base64` for frontend rendering

Frontend integration risk that must be addressed:

- `packages/frontend-sdk/src/plugins/attachmentActions.ts`
  - currently defaults attachment actions to plugin id `openai_responses_attachments`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - `storeSessionAttachment(...)` / `deleteSessionAttachment(...)` are currently called without a provider-specific `pluginId`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
  - same default-plugin assumption

That means adding a provider-side attachment extension alone is not enough; the frontend must be able to target the attachment action plugin advertised by the active provider UI.

## Implementation notes

- No native-history sanitization is required for this task. It is acceptable for retained native history to include inline base64 image data after send.
- The image attachment capability should be configured per provider/agent using explicit allow/deny settings for:
  - inline base64 image content
  - remote image URLs
- Default behavior should allow both methods.
- Ollama coverage should use base64 image flow only.
- Fireworks coverage should include:
  - base64 image flow
  - image URL flow
- Frontend-oriented testing should verify that the preview image reaches the frontend as part of the stored/reloaded user message payload, not only that the send succeeds.

## Execution plan

Added during completion:

1. Add a new reference-provider attachment extension that exposes image composer attachment UI plus `store_attachment` / `delete_attachment` session actions compatible with the existing frontend upload flow.
2. Extend the reference provider to convert image multipart parts from `url`, `data_base64`, or `asset_ref` into OpenAI-compatible chat-completions image content blocks, while honoring config that enables/disables base64 and URL image methods.
3. Update the shared frontend attachment helper path so attachment UI elements can optionally specify which plugin owns `store_attachment` / `delete_attachment`, then pass that plugin id through mobile and desktop upload/delete flows.
4. Add unit tests for config normalization and multipart conversion, including rejection when a disabled attachment method is used.
5. Add server/application/frontend-facing tests that verify `asset_ref` image previews are enriched and visible in the user message payload returned to the frontend.
6. Add or update integration tests for:
   - Fireworks image URL send
   - Fireworks base64/image-upload send
   - Ollama base64/image-upload send

## Completion Notes

Added during completion:

1. Implemented a new provider extension, `reference_openai_compatible_attachments`, with:
   - local session-asset-backed `store_attachment` / `delete_attachment`
   - image composer attachment UI
   - per-provider/per-agent config gates for `allow_image_attachment_base64` and `allow_image_attachment_url`
2. Added reference-provider attachment helper modules for:
   - `asset_ref` parsing
   - attachment capability normalization
   - image multipart conversion to OpenAI chat-completions `image_url` parts
3. Extended `OpenAICompatibleProvider` to:
   - convert image multipart content from remote URLs, inline base64, or local `asset_ref`
   - reject disabled image methods according to config
   - round-trip image content back into core `multipartContent`
4. Updated frontend upload/delete flows so mobile and desktop pass the owning attachment plugin id instead of assuming `openai_responses_attachments`.
5. Added frontend capability handling for image attachments:
   - `supports_upload`
   - `supports_url`
   Mobile now hides disallowed image-entry paths; desktop now omits disallowed plus-menu entries.
6. Added targeted tests for:
   - attachment extension actions and config/UI behavior
   - provider multipart conversion and method gating
   - frontend SDK attachment helper plugin override
   - frontend-visible attachment payload delivery through a real backend integration test
   - Fireworks image URL and base64 integration coverage
   - Ollama base64 integration coverage, with a graceful skip when the chosen local vision model is not installed

Verification run during completion:

1. `pytest plugins/reference-openai-compatible-provider/tests/test_attachment_extension_unit.py plugins/reference-openai-compatible-provider/tests/test_provider_multipart_conversion_unit.py -q` -> passed
2. `pytest plugins/reference-openai-compatible-provider/tests/test_ollama_image_integration.py plugins/reference-openai-compatible-provider/tests/test_fireworks_image_integration.py -q` -> `2 passed, 1 skipped`
3. `npm test -- --run src/plugins/__tests__/attachmentActions.test.ts` in `packages/frontend-sdk` -> passed
4. `RUN_BACKEND_INTEGRATION=1 npm test -- --run src/integration/__tests__/backend.integration.test.ts -t "F2: uploaded attachment previews are present in frontend-visible user messages"` in `packages/frontend-sdk` -> passed

Notable verification note:

1. A broader run of `RUN_BACKEND_INTEGRATION=1 npm test -- --run src/integration/__tests__/backend.integration.test.ts` still failed in existing test `N: reload and polling timing matrix stays clean during delayed persistence` with `HTTP 500 POST /sessions`. That failure is outside the new attachment-specific test path and was left unchanged.
