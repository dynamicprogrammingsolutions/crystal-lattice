# codex-openrouter

Plugin bundle containing:

- `OpenRouterProvider` (provider)
- `OpenRouterImageGenerationProvider` (provider)
- OpenRouter extensions:
  - tools
  - reasoning
  - web search (citations)
  - image-generation attachments (`store_attachment`, `delete_attachment`, `download_attachment`)

Load via module-only spec so the descriptor can register multiple classes.

## Image generation

The bundle now includes a separate `openrouter_image_generation` provider for
OpenRouter image-generation models. V1 intentionally supports a single user
turn with optional one input image and normalizes generated output into
ordinary assistant messages with `multipartContent` image parts backed by
session-asset `asset_ref` descriptors.

The provider itself is intentionally non-streaming in V1. Applications may
request streaming by default, but the current application layer detects the
provider's `NotImplementedError` for streaming and transparently retries the
request in non-streaming mode.

The companion `openrouter_image_generation_attachments` extension exposes:

- `store_attachment`
- `delete_attachment`
- `download_attachment`

These actions are session-asset-backed so uploaded input images and generated
output images can both be previewed and downloaded by clients without storing
large base64 payloads in session JSON.

## License

This directory is available under the [Apache License 2.0](../../LICENSE).
