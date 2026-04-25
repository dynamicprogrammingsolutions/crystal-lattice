# OpenRouter Image Generation Provider

Add OpenRouter image-generation support as a separate provider, using session asset storage for both input and generated images, with V1 focused on a single-turn flow and V2 reserved for follow-up multi-turn image-editing behavior.

## Task checklist

- [ ] `tasks/20260422-openrouter-image-generation-provider/010-v1-openrouter-image-generation-provider.md`
- [ ] `tasks/20260422-openrouter-image-generation-provider/020-v2-multiturn-draft-requirements.md`

## Context

The requested direction is:

- OpenRouter image generation should be a separate provider, not a feature of the existing OpenRouter chat provider.
- V1 should support one turn only: a single user message with optional input image.
- V2 should support multiple turns, where output images from turn 1 can become the input image for turn 2.
- Available generation parameters should come from config and UI elements.
- The UI should support downloading generated images to disk.
- Both input and generated images must be stored in session asset storage.
- Upload and download should be exposed through actions.
- The request/response chunking path for actions must be verified for bridge transport.
- `_session_asset_store` must not be injected into config; runtime-only objects should flow through the newer context-based contracts.

## Research Summary

### OpenRouter API direction

The current OpenRouter image-generation docs describe image generation via a chat-completions style request using image-generation-specific fields such as requested output modalities and image configuration, with generated images returned on the assistant message. This supports a separate provider design while still fitting the existing message pipeline.

Sources:

- https://openrouter.ai/docs/guides/overview/multimodal/image-generation
- https://openrouter.ai/docs/guides/overview/multimodal/images
- https://openrouter.ai/docs/api-reference/chat-completion

### Existing codebase findings

- The core message model already supports attachments via `multipartContent` in `core/python/agent_core/types.py`.
- The server already accepts multipart messages and enriches session-asset-backed image attachments with preview bytes in `application/python/agent_terminal_app/server.py`.
- The mobile UI already renders message attachments in `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`.
- The mobile composer already uploads picked attachments through provider-extension actions and stores them as session assets in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`.
- Existing attachment actions already exist in:
  - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachments_extension.py`
  - `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/attachments_extension.py`
- Existing providers already know how to resolve `asset_ref` attachments from runtime state or config:
  - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
  - `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`

### Important correction to include in implementation

The current app runtime still decorates request config with `_session_asset_store` in:

- `core/python/agent_app/application_future.py`

This is wrong because config should stay serializable and should not carry runtime-only objects.

The current code path still relies on this pattern in at least:

- `core/python/agent_app/application_future.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`

The task should explicitly migrate these runtime-object uses to the newer context-aware contracts for provider conversion and request handling, instead of continuing the config injection pattern.

### Bridge chunking investigation summary

Generic chunking support for large request and response bodies already exists end to end:

- Frontend request chunking and response reassembly:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts`
- Python bridge request reassembly and response chunking:
  - `application/python/agent_terminal_app/bridge_client.py`
- Elixir bridge forwarding of chunked request/response events:
  - `bridge-elixir/lib/bridge/app_channel.ex`
  - `bridge-elixir/lib/bridge/server_channel.ex`

Existing tests confirm generic large-body behavior:

- `packages/frontend-sdk/src/transport/bridgeTransport.test.ts`
- `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`
- `application/python/tests/test_bridge_client_chunked_http.py`
- `bridge-elixir/test/bridge/server_channel_chunked_http_test.exs`

However, there is not yet explicit action-focused coverage for large `/actions` payloads and large download responses. V1 should add that coverage.

## Recommended design direction

- Use a separate OpenRouter image-generation provider.
- Reuse normal assistant messages plus `multipartContent` image attachments instead of inventing a new message type.
- Store both input and generated images in session asset storage.
- Keep generated images out of persisted session JSON except as `asset_ref` attachment references.
- Use provider-extension actions for upload and download.
- Treat the runtime-context cleanup for session asset access as part of the same task, not as a later cleanup.