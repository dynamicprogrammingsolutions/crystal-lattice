# `view_image`

## Handler behavior (implementation notes)

- Validates that the current model supports image inputs; otherwise returns an error: `view_image is not allowed because you do not support image inputs`.
- Resolves the given path relative to the turn cwd, verifies it exists and is a file.
- Returns the image as Responses-API content items (an `input_image` plus optional label text).
- Emits a `ViewImageToolCall` event for clients.
