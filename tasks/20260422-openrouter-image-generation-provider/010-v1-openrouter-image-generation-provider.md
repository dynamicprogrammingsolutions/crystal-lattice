# V1 OpenRouter Image Generation Provider

Implement a first version of OpenRouter image generation as a separate provider, supporting one user turn with an optional input image, with all images stored in session asset storage and upload/download exposed through actions.

## Requirements checklist

- [x] Add a separate OpenRouter image-generation provider instead of extending the existing OpenRouter chat provider.
- [x] Restrict V1 to a single user message with optional single input image.
- [x] Store both input and generated images in session asset storage.
- [x] Represent generated output as ordinary assistant messages with `multipartContent` image parts backed by `asset_ref`.
- [x] Add provider-extension actions for upload and download.
- [x] Update mobile UI so generated images can be previewed and downloaded to device storage.
- [ ] Add explicit bridge chunking coverage for large action uploads and downloads.
- [x] Remove `_session_asset_store` runtime-object injection from config and migrate relevant code to context-based runtime access.

Parent Task: tasks/20260422-openrouter-image-generation-provider/000-main.md

## Scope

V1 is intentionally limited to a single-turn image-generation flow:

- one user message
- prompt text allowed
- optional one input image
- no multi-turn editing flow
- no reference-image semantics beyond the single optional input image

If earlier messages exist in the session, the provider should validate and reject the request clearly rather than silently ignoring history.

## Implementation plan

This plan was added during task creation so the implementing agent can start from a concrete design.

### 1. Provider and plugin structure

- Add a new provider class in the OpenRouter plugin bundle, likely:
  - `plugins/openrouter/src/openrouter_plugins/openrouter_image_generation_provider.py`
- Register it in:
  - `plugins/openrouter/agent_plugin.json`
- Keep the existing `OpenRouterProvider` focused on chat and vision/chat use cases.

The new provider should:

- have its own provider name, for example `openrouter_image_generation`
- expose image-generation-appropriate tags only
- contribute image-generation config schema and UI elements
- remain non-streaming in V1 unless the real API behavior is confirmed and supported cleanly

### 2. Request/response message model

- Input should use the existing core message model:
  - user message `content`
  - optional `multipartContent` image part
- Before provider-native conversion, input images should already be stored as session assets via action-based upload.
- Provider conversion should resolve `asset_ref` image attachments at runtime, not from config.
- Output should be normalized into a normal assistant message with:
  - `content` for any text returned by the model
  - `multipartContent` image parts of type `image`
  - each image part backed by `content.asset_ref`
  - `filename` and `mime_type` when known

Generated images should not be persisted inline as large base64 blobs in session JSON.

### 3. Session asset storage integration

For input images:

- reuse the existing action-driven upload path already used by the mobile composer
- add a provider extension for this provider so the UI can keep using action-based asset storage

For generated images:

- after the provider receives the OpenRouter response, decode each returned image payload
- store each generated image in the session asset store
- create attachment parts using `asset_ref`
- include enough metadata for UI presentation and later reuse

Important:

- generated images should be persisted through the same session-asset-backed message contract the rest of the app already uses
- the server-side preview enrichment path in `application/python/agent_terminal_app/server.py` should continue to work unchanged or with only small targeted additions

### 4. Runtime context cleanup for session asset access

This is part of V1.

Current problem:

- `core/python/agent_app/application_future.py` decorates config with `_session_asset_store`
- some providers then read runtime objects from config

This should be corrected so config remains clean and serializable.

Implementation direction:

- update `AgentApplication` and any relevant `AgentCore` request/conversion entry points so runtime-only objects needed by providers are passed through context, not config
- migrate existing session-asset-aware providers and new provider code away from config-based runtime object access
- audit at least:
  - `core/python/agent_app/application_future.py`
  - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
  - `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
  - the new OpenRouter image-generation provider

The implementing agent should verify the current `to_native_messages` / `from_native_messages` and related request-lifecycle contracts, and route runtime objects through the newer context-aware path consistently.

### 5. Provider-extension actions

Add an attachment-focused provider extension for the new provider, parallel to existing attachment extensions.

Required actions:

- `store_attachment`
- `delete_attachment`
- download action for stored/generated assets

Download action notes:

- The user explicitly requested that actions provide download.
- V1 can return a large base64 payload plus metadata through `/actions`, relying on existing bridge chunking.
- This is acceptable for V1, but the action should be isolated so it can later be replaced or supplemented with a dedicated asset-download endpoint if desired.

### 6. UI work

Mobile UI already has the core upload pipeline in:

- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

Needed additions:

- provider-specific upload action wiring if required by plugin id differences
- full-screen preview for assistant image outputs
- download-to-device action using `react-native-fs`

Relevant files:

- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- `mobile/crystal-lattice-control-rn/src/components/AttachmentThumbnailStrip.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

### 7. Bridge chunking verification

Generic chunking is already implemented and tested for large request/response bodies, but V1 should add explicit action-focused tests.

Add or extend tests so they cover:

- large `POST /actions` upload body for `store_attachment`
- large chunked action response for download
- end-to-end reassembly on the client side

Relevant existing references:

- `packages/frontend-sdk/src/transport/bridgeTransport.ts`
- `packages/frontend-sdk/src/transport/bridgeTransport.test.ts`
- `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`
- `application/python/agent_terminal_app/bridge_client.py`
- `application/python/tests/test_bridge_client_chunked_http.py`
- `bridge-elixir/lib/bridge/app_channel.ex`

### 8. Tests

Add tests for:

- provider request validation for V1 single-turn semantics
- provider-native conversion from `asset_ref` input image
- generated image storage into session assets
- assistant message normalization to `multipartContent` with `asset_ref`
- list-messages preview enrichment for generated images
- upload/download action behavior
- bridge chunking for large upload/download action payloads

## Suggested files to inspect while implementing

- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
- `plugins/openrouter/tests/test_openrouter_provider_multipart_conversion_unit.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachments_extension.py`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/attachments_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
- `core/python/agent_app/application_future.py`
- `core/python/agent_core/core.py`
- `application/python/agent_terminal_app/server.py`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- `packages/frontend-sdk/src/transport/bridgeTransport.ts`

## Notes for the implementing agent

- Prefer `asset_ref`-backed persisted messages over inline image blobs.
- Treat runtime-context cleanup as part of this task, not optional follow-up work.
- Keep the message model unified: assistant image results should still be ordinary assistant messages with attachments.

## Execution plan

This plan was appended during task completion.

1. Refactor provider/runtime context threading before adding the new provider.
   - Extend provider, provider-extension, and feature conversion hooks so `to_native_messages(...)` and `from_native_messages(...)` can receive runtime context in a backward-compatible way.
   - Update the core call sites to pass request/plugin context through conversion, not just `initialize_request(...)` and `finalize(...)`.
   - Remove `_session_asset_store` config decoration from `AgentApplication` and instead provide `session_asset_store` through runtime context.
   - Migrate existing asset-aware providers that currently read `_session_asset_store` from config to use runtime context instead.

2. Implement a separate OpenRouter image-generation provider plus attachment extension.
   - Add a new provider in `plugins/openrouter/src/openrouter_plugins/` and register it in `plugins/openrouter/agent_plugin.json`.
   - Keep V1 intentionally non-streaming and validate the one-turn contract explicitly: exactly one user message, optional single input image, no prior-history editing semantics.
   - Normalize generated output into ordinary assistant messages with `multipartContent` image parts backed by `asset_ref`.
   - Store generated image payloads in session asset storage immediately and keep large binary/base64 content out of persisted session JSON.

3. Add OpenRouter image attachment actions for upload, delete, and download.
   - Reuse the existing session-asset-backed upload/delete action pattern from the OpenAI/OpenAI-compatible attachment extensions.
   - Add a dedicated download action that returns metadata plus base64 payload for stored/generated assets so mobile can save them locally.
   - Keep action behavior compatible with bridge chunking so V1 can rely on chunked `/actions` traffic for large uploads/downloads.

4. Add app/mobile support for assistant image preview and device download.
   - Reuse the existing composer upload path and provider-specific `pluginId` wiring for attachment upload.
   - Add frontend SDK download helper(s) for provider-extension download actions.
   - Update the React Native message attachment UI to support full-screen preview and saving generated images to device storage.

5. Add tests in increasing order of confidence.
   - Unit tests for runtime-context conversion, V1 request validation, native conversion, generated-image asset persistence, and download action behavior.
   - Application/server tests for non-streaming end-to-end behavior and message enrichment with generated asset-backed images.
   - Bridge tests with explicit large `/actions` upload and large download-response chunking coverage.
   - Real OpenRouter integration coverage during implementation using the inexpensive representative models:
     - `black-forest-labs/flux.2-klein-4b`
     - `sourceful/riverflow-v2-fast-preview`
     - `google/gemini-2.5-flash-image`
   - Use those integration tests to verify current request shape expectations, including family-specific `modalities` / `image_config` behavior where applicable.

6. Treat non-streaming support as a hard V1 requirement.
   - Ensure the application path works correctly with the provider’s `call_api(...)` implementation.
   - Add targeted non-streaming coverage through the application layer so the feature does not accidentally depend on streaming-only flows.

## Completion Notes

These notes were appended during task completion.

- Implemented runtime-context threading for provider/extension/feature message
  conversion hooks so `to_native_messages(...)` and
  `from_native_messages(...)` can receive request context without relying on
  runtime-object injection into config.
- Removed `_session_asset_store` config decoration from
  `core/python/agent_app/application_future.py` and migrated session-asset-aware
  providers to request/runtime context access.
- Added a separate OpenRouter image-generation provider and companion
  attachment extension:
  - `plugins/openrouter/src/openrouter_plugins/openrouter_image_generation_provider.py`
  - `plugins/openrouter/src/openrouter_plugins/openrouter_image_generation_attachments_extension.py`
- Registered the new provider/extension in
  `plugins/openrouter/agent_plugin.json`.
- Implemented V1 non-streaming image generation with:
  - exactly one user message
  - optional single input image
  - generated image persistence to session asset storage
  - assistant `multipartContent` image parts backed by `asset_ref`
- Added provider-extension upload/delete/download actions for OpenRouter image
  generation and later extended the same `download_attachment` contract to:
  - `openai_responses_attachments`
  - `reference_openai_compatible_attachments`
- Added frontend SDK download helper support in:
  - `packages/frontend-sdk/src/plugins/attachmentActions.ts`
  - `packages/frontend-sdk/src/index.ts`
- Added application-layer streamed-request fallback for non-streaming-only
  providers:
  - `ToolLoopRunner` now re-raises `NotImplementedError`
  - `AgentApplication` retries in non-streaming mode, logs a warning, and
    caches the provider class as non-streaming-only for later requests
  - resolved config `stream: false` now forces non-streaming at the
    application layer, while explicit caller `stream=False` still wins over
    config
- Updated the React Native client so image attachments can be previewed,
  downloaded, shared, and saved to Photos:
  - image preview uses `react-native-image-modal`
  - Save to File uses `@react-native-documents/picker` `saveDocuments(...)`
  - Save to Photos uses `@react-native-camera-roll/camera-roll`
  - Share uses `react-native-share`
  - zooming begins a background full-resolution download and swaps the preview
    image source once the full asset is cached locally
- Added unit and integration coverage for:
  - provider validation and attachment actions
  - application non-streaming image-generation flow
  - default-config application image-generation flow via a shipped agent
  - default-config send-message endpoint flow using the real streamed app path
  - frontend SDK real OpenRouter e2e coverage for:
    - simple image generation
    - source-image upload + generation
    - generated-image download
  - real OpenRouter API smoke tests for:
    - `black-forest-labs/flux.2-klein-4b`
    - `sourceful/riverflow-v2-fast-preview`
    - `google/gemini-2.5-flash-image`
- Real OpenRouter integration tests were run successfully after normalization
  fixes:
  - `pytest plugins/openrouter/tests/test_openrouter_image_generation_integration.py -q -m 'integration and openrouter'`
  - result observed during completion: `4 passed`
- Plugin README files were updated to document the new public attachment
  download contract and the separate OpenRouter image-generation provider.
- Added a shipped default-config provider/agent under
  `application/python/agent_terminal_app/default_config/config.json` and
  `application/python/agent_terminal_app/default_config.json` for OpenRouter
  image generation (`openrouter-image`).
- Added runtime context plumbing for plain message append so `asset_ref`
  attachments can be appended through `/sessions/{id}/messages` before send.
- Remaining task item still open:
  - explicit bridge chunking coverage for large `/actions` uploads/downloads