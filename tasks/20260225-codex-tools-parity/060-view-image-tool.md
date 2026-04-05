# 060 — Add `view_image` tool plugin

**STATUS: PENDING**

## Problem

Codex CLI exposes a `view_image` tool that attaches a local image file into the model context as an image input.

Our platform currently:

- Has ongoing work around attachments/multipart content.
- Uses Chat Completions in the default OpenAI-compatible provider (which does not support Responses-style `input_image` content items).

So we need to implement `view_image` in a way that is:

- useful today (at least for UIs/humans), and
- can evolve to true “model sees the image” behavior when our provider stack supports it.

## References

- Codex CLI reconstructed schema: `docs/codex-tools/view_image/schema.json`
- Codex CLI handler notes: `docs/codex-tools/view_image/README.md`

## Plan

### A) Implement `ViewImageTool` in `plugins/codex-tools`

1) Add tool plugin:
   - File: `plugins/codex-tools/src/codex_tools/view_image_tool.py`
   - Tool name: `view_image`

2) Schema:
   - `path: string` only
   - `additionalProperties: false`

### B) Runtime behavior (v1: safe + UI-visible)

1) Resolve paths relative to `working_directory` in tool config.
2) Enforce `allowed_paths` similar to `apply_patch` / `shell`.
3) Validate file exists and looks like an image (by extension or magic header).
4) Return a tool result dict that includes:
   - `success`
   - `path`
   - `mime_type`
   - `bytes_base64` (or a short placeholder if size too large)

### C) Model-visible image attachment (deferred / conditional)

This depends on provider support.

Add an internal feature flag/config option:

- `emit_multimodal_content: bool` (default false)

When enabled *and* the active provider supports multimodal messages, modify the tool’s formatted output (or metadata) so that the subsequent model call includes the image.

Implementation will require additional investigation of:

- how the OpenAI-compatible provider should represent images (Chat Completions uses `content: [{type:"image_url",...}]` in some APIs, Responses uses `input_image` items).
- how our core message schema should carry those content items.

### D) Wire into plugin manifest

- Add `codex_tools.view_image_tool.ViewImageTool` to `plugins/codex-tools/agent_plugin.json`.

### E) Tests

- Test: rejects non-existent file.
- Test: accepts a small PNG fixture.
- Test: denies path outside allowed_paths.

## Acceptance criteria

- Tool exists with the Codex CLI schema.
- v1 behavior is safe and provides a UI-friendly rendering.
- Design leaves room for true multimodal injection later.

## Open questions / follow-ups

- We may need a core-level message type update to support “tool returns image content items” cleanly.
