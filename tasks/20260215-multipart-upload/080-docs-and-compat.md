# Docs + Compatibility Notes for `multipartContent`

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Update developer-facing documentation to describe the new core message key `multipartContent`, the per-attachment UI schema elements, and compatibility expectations across server/SDK/UIs.

## Depends On

- `tasks/20260215-multipart-upload/010-core-message-multipartcontent.md`
- `tasks/20260215-multipart-upload/020-server-append-multipartcontent.md`

## Requirements

- Document core message shape:
  - `content` remains primary and may be empty.
  - `multipartContent` is optional and extensible.
- Document UI schema shape for composer attachments:
  - `ui_type: "composer_attachment"`
  - `attachment_type`, `supported_file_types`, `display_placement`
  - reorder behavior when multiple types share a side.
- Document bridge constraint:
  - JSON-only request bodies; attachments must be representable as base64 or URLs.

## Suggested Files to Update

- `TYPES_AND_PROTOCOLS.md`
- `docs/api/core-sdk.md` (or other relevant docs under `docs/`)
- Optionally: `application/python/agent_terminal_app/server_endpoints_parity.md` to mention multipart payload on append.

## Definition of Done

- Docs clearly state the contract and extension points.
