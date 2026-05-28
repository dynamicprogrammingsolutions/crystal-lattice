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

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
