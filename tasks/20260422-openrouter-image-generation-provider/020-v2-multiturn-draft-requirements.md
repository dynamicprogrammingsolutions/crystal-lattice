# V2 Multi-Turn Draft Requirements

Define the next-stage requirements for OpenRouter image generation after V1, focused on multi-turn image editing and reuse of prior generated images.

## Requirements checklist

- [ ] Support multi-turn sessions where a generated image from a previous assistant message can become the input image for a later user turn.
- [ ] Preserve the session-asset-backed storage model for both prior outputs and new inputs.
- [ ] Support clean UI affordances for reusing a generated image as the next-turn input.
- [ ] Keep the persisted message format compatible with V1 assistant `multipartContent` image attachments backed by `asset_ref`.
- [ ] Leave room for later reference-image support without redesigning the attachment/message contract.

Parent Task: tasks/20260422-openrouter-image-generation-provider/000-main.md
Depends On: tasks/20260422-openrouter-image-generation-provider/010-v1-openrouter-image-generation-provider.md

## High-level draft requirements

V2 should extend the V1 provider and UI model rather than replacing it.

Expected behavior:

- A later turn may select one of the prior generated images as the next input image.
- The image source of truth should remain the session asset store.
- The provider should define explicit rules for which prior messages are eligible as image-editing context.
- The UI should expose a clear action like “use as next input” for assistant-generated images.
- The provider should preserve a clean boundary between:
  - prompt text
  - primary editable input image
  - future reference images

## Non-goals for this draft

- No implementation plan yet.
- No requirement yet for arbitrary reference-image sets.
- No commitment yet to any specific OpenRouter model family or per-model editing semantics.

## Design guardrails

- Do not introduce a new message type if the V1 assistant attachment model still works.
- Keep compatibility with session-asset preview enrichment and mobile attachment rendering.
- Keep runtime-only objects out of config in V2 as well; any additional runtime dependencies should continue to use context-based plumbing.