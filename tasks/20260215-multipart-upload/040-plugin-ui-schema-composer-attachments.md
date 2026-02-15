# Plugins: Per-type `composer_attachment` UI schema elements

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Define and implement plugin-provided session UI schema elements that describe which attachment types can be added in the composer, which file types are supported, and whether attachments should be displayed above/below the main composer.

Each attachment type is described by its own UI schema element.

## Depends On

- `tasks/20260215-multipart-upload/010-core-message-multipartcontent.md`

## Requirements

- UI schema element type: `ui_type: "composer_attachment"`.
- No `id` field is needed.
- Required keys:
  - `attachment_type`: e.g. `"image"`, `"pdf"` (may be versioned later like `"img-v2"`).
  - `supported_file_types`: e.g. `["jpg","png"]` or `["pdf"]`.
  - `display_placement`: `"above" | "below"` (display-only guidance).
- Optional keys:
  - `label`
  - `metadata_ui` describing optional per-attachment metadata controls (shape is frontend contract).
  - `prepare_action` (string action id, e.g. `"upload_image"`)

## Semantics: `prepare_action`

When present, `prepare_action` names an action that the UI can call to normalize or upload an asset.

- The action is defined by the same plugin that contributed this UI schema element.
  - Frontends should use the element's `plugin` field (attached by `AgentCore.get_ui_schema`) as `plugin_id`.
  - Frontends should use `prepare_action` as `action_id`.
- The action semantics should match application actions (inputs/result envelope), but the implementation lives in provider/extension (or other core plugin types).
  - See Phase 2 plan: `tasks/20260215-multipart-upload/090-asset-prepare-upload-action.md`.

## Suggested Ownership

- Prefer provider plugins (e.g. `openrouter`, `openai_compatible`) to expose these elements because they best know what content types the downstream model supports.
- Alternatively, a dedicated feature plugin can expose these if capabilities are orthogonal to provider.

## Implementation Plan

1) Define element conventions (documentation-level)

- Decide the exact key set and expected values.
- Keep the element dict opaque to the core; core should only flatten and return it as part of session UI schema.

2) Add elements to at least one provider

- Example files:
  - `core/python/plugins/openrouter_provider.py` (`get_ui_elements` already returns config UI).
  - `core/python/plugins/openai_provider.py` currently returns `[]` for UI.

Add elements such as:

```python
return [
  {
    "ui_type": "composer_attachment",
    "attachment_type": "image",
    "supported_file_types": ["jpg", "png"],
    "display_placement": "above",
    "label": "Image",
    "prepare_action": "upload_image",
  },
  {
    "ui_type": "composer_attachment",
    "attachment_type": "pdf",
    "supported_file_types": ["pdf"],
    "display_placement": "below",
    "label": "PDF",
    "prepare_action": "upload_pdf",
  },
]
```

3) Ensure UI schema endpoint returns these

- The server already exposes `GET /sessions/{session_id}/ui-schema` via `core.get_ui_schema()`.
- Confirm element appears there for sessions using the provider.

## Tests (Optional but recommended)

- Unit test that `AgentCore.get_ui_schema()` includes these elements when provider is registered.

## Definition of Done

- At least one provider/plugin emits `composer_attachment` elements.
- Mobile/desktop UIs can rely on this schema for showing attach controls.
