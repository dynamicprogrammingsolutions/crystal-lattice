# Multipart Message Composer + Image/PDF Upload (Draft Implementation Plan)

## Description

Add first-class support for composing and sending messages that include a main text `content` plus an extensible `multipartContent` array (images, PDFs, and future types). This includes:

- Core SDK: `Message` supports `multipartContent` (opaque/extensible); `content` remains primary and is not derived.
- Server API: accept/return `multipartContent` on message append.
- Frontend SDK + UIs (mobile + desktop): attachment picking, rendering, and reorder (above/below composer), driven by plugin-provided UI schema.
- Plugins/providers: define UI schema per attachment type and map `{content, multipartContent}` to/from provider-native message formats.

This task is structured as a main task + subtasks, intended as a handoff package.

## Subtasks

- `tasks/20260215-multipart-upload/010-core-message-multipartcontent.md`
- `tasks/20260215-multipart-upload/020-server-append-multipartcontent.md`
- `tasks/20260215-multipart-upload/030-frontend-sdk-types-and-payloads.md`
- `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`
- `tasks/20260215-multipart-upload/050-provider-mapping-multipartcontent.md`
- `tasks/20260215-multipart-upload/060-mobile-composer-attachments.md`
- `tasks/20260215-multipart-upload/070-desktop-composer-attachments.md`
- `tasks/20260215-multipart-upload/080-docs-and-compat.md`
- `tasks/20260215-multipart-upload/090-asset-prepare-upload-action.md`
- `tasks/20260215-multipart-upload/100-bridge-chunked-http-over-websocket.md`

## Requirements (Locked)

### Core message contract

- Add a new top-level key on core messages: `multipartContent`.
- `multipartContent` is an array of objects with keys:
  - `type` (string)
  - `content` (shape is plugin/UI contract; core stays agnostic)
  - `metadata` (any)
- The core should not strictly define supported part types nor the schema of each type.
- `content` remains important and is not a fallback/derived field.
  - UI sends main composer text as `content`.
  - UI may send `content: ""` when at least one multipart part exists.

### Plugin/UI contract

- Plugins provide per-attachment-type UI schema elements. One element per attachment type.
- Each attachment type can be displayed either `above` or `below` the composer (display-only guidance).
- If multiple attachment types are defined on the same side, the UI must support reordering the actual attachments within that side.
- Plugins are responsible for assembling `{content, multipartContent}` into provider-native format and splitting it back.
- Plugins may use provider-native `_metadata` for roundtripping additional information.

### Supported types (product v1)

- For initial UX, target: `image`, `pdf`, and main text in `content`.
- Core remains extensible: other types can be added later without core changes.

## Current Repo State (Key References)

### Core message is text-only

- `core/python/agent_core/types.py:1014` defines `Message` with `role`, `content`, `metadata`.
  - `to_dict()` only emits `role/content/metadata`.
  - `from_dict()` expects `role/content`.

### Core add_message builds only role/content/metadata

- `core/python/agent_core/core.py:595` (`AgentCore.add_message`)
  - Constructs `message_dict` containing only `role/content/metadata` (see lines ~633-638).

### HTTP append endpoint requires string content

- `application/python/agent_terminal_app/server.py:839` (`POST /sessions/{session_id}/messages`)
  - Validates `role` and `content` must be strings.

### Frontend SDK message types are text-only

- `packages/frontend-sdk/src/types/messages.ts:3` defines `ApiMessage` as `{ role, content, metadata? }`.

### Bridge transport is JSON-only

- `packages/frontend-sdk/src/transport/bridgeTransport.ts:93` stringifies `req.body` (no binary/multipart form data).
  - This implies v1 uploads must be JSON-compatible (URLs or base64).

## Proposed UI Schema Elements (Per Attachment Type)

Plugins should expose attachment UI capabilities via session UI schema (returned by `GET /sessions/{session_id}/ui-schema`).

Define a new element kind:

```json
{
  "ui_type": "composer_attachment",
  "attachment_type": "image",
  "supported_file_types": ["jpg", "png"],
  "display_placement": "above",
  "label": "Image",
  "metadata_ui": {
    "quality": { "type": "select", "options": ["low", "high"], "default": "low" }
  }
}
```

And:

```json
{
  "ui_type": "composer_attachment",
  "attachment_type": "pdf",
  "supported_file_types": ["pdf"],
  "display_placement": "below",
  "label": "PDF"
}
```

Notes:

- `attachment_type` is a string and may be versioned later (e.g. `"img-v2"`).
- `supported_file_types` is a list of tokens; v1 uses file extensions (`jpg`, `png`, `pdf`).
- `display_placement` is display-only guidance; plugins decide actual provider-native ordering.

## UX Rules (v1)

- Main composer remains a single text box -> sent as core `content`.
- User can add attachments -> sent as core `multipartContent`.
- Sending is allowed when:
  - `content.trim().length > 0`, OR
  - `multipartContent.length > 0`.
- Attachments display above/below composer based on schema `display_placement`.
- If multiple attachment types share the same placement, the UI provides reorder for the attachments list on that side.

## Upload Strategy (v1; bridge-compatible)

Because bridge transport only supports JSON bodies, implement v1 attachments as JSON-friendly payloads:

- In `multipartContent[].content`, store either:
  - `url` (including `data:` URL), and/or
  - `data_base64` plus `mime_type` and optional `filename`.

This is a plugin/UI contract; the core remains agnostic.

## Phase 2 (Optional): Server-side asset preparation / upload

Some providers may prefer assets to be uploaded or normalized (resized/compressed images, thumbnails, provider-specific file references). We can support this without changing the core message interface by adding provider/extension-defined actions that use the same semantics as application actions (definition + execution envelope), and by expanding action support beyond application plugins.

This is intentionally Phase 2 because it adds complexity and is not required for the basic `{content, multipartContent}` flow.

## Acceptance Criteria

- Core can serialize/deserialize sessions with messages containing `multipartContent`.
- Server can accept appended messages with optional `multipartContent` and returns it from message listing.
- Frontend SDK types support `multipartContent` and send it in REST append payloads.
- Mobile + desktop UIs:
  - show attach buttons based on UI schema `composer_attachment` elements
  - support above/below placement and reordering
  - send messages with empty `content` when attachments exist
  - render images and PDFs in message bubbles
- At least one provider plugin demonstrates correct provider-native conversion using `{content, multipartContent}`.

## Testing Strategy (Suggested)

- Core: unit tests for `Message.to_dict()/from_dict()` and export/import session roundtrip.
- Server: endpoint test for append+list with multipart.
- Frontend SDK: integration test verifying append payload includes `multipartContent`.
- UIs: minimal component tests or manual test checklist.

---

## Implementation Notes (2026-02-15)

- OpenRouter v1 implemented (images only):
  - Provider mapping in `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`.
  - Composer attachment UI element emitted by the same provider (`ui_type: "composer_attachment"`, image attachment, `display_placement: "below"`).
- Added OpenRouter multipart integration tests:
  - Provider-level: `plugins/openrouter/tests/test_openrouter_multipart_integration.py`.
  - Real-server HTTP flow: `application/python/tests/test_agent_terminal_app_server_openrouter_multipart_http_integration.py`.

