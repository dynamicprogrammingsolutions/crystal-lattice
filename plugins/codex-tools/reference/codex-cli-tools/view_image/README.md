# `view_image`

## Model/feature variants

The schema snapshot (`schema.json`) documents the default upstream variant:
`can_request_original_image_detail = true`, `unified_image_budget = false`,
`include_environment_id = false`.

- `detail` (enum `high | original`) is only included when the model can
  request original image detail and the unified image budget is disabled;
  with a unified image budget the parameter is dropped entirely.
- An optional `environment_id` parameter is added for multi-environment
  sessions; omitting it targets the primary environment.
- The current description (upstream reword, 2026-05-26) deliberately allows
  self-initiated use for images already on disk; the older "only use if given
  a full filepath by the user" wording is historical.

## Handler behavior (implementation notes)

- Validates that the current model supports image inputs; otherwise returns an error: `view_image is not allowed because you do not support image inputs`.
- Resolves the given path relative to the turn cwd, verifies it exists and is a file.
- Returns the image as Responses-API content items (an `input_image` plus optional label text).
- Emits a `ViewImageToolCall` event for clients.
