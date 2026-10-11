# `shell`

**Historical:** upstream Codex CLI removed the array-based `shell` tool on
2026-05-13 (`83decfa3`, #22246) and now ships the unified exec surface
(`exec_command` + `write_stdin`) instead; see `../exec_command/`. This
snapshot preserves the final pre-removal contract, which the platform still
serves to legacy (non-shell-command-family) models under
`shell_tool_mode: "auto"` and to any agent via `shell_tool_mode: "shell"`.

## JSON tool spec

- `schema.with_request_permissions.json` corresponds to Codex runs where the `RequestPermissions` feature is enabled (it adds `additional_permissions`).
- `schema.without_request_permissions.json` corresponds to runs without that feature.

Notes:

- `command` is an argv array. On Unix-like systems, Codex guidance is to use `command: ["bash", "-lc", "..."]`.
- `workdir` is preferred over `cd`.

## Model/feature variants

- Models with `shell_type = default` prefer exposing `shell`.
- Models with `shell_type = shell_command` prefer exposing `shell_command` instead.

## Handler behavior (implementation notes)

The `shell` handler ultimately runs the command through the shared exec orchestration.

Key behaviors that affect outputs and errors:

- Output formatting and truncation follow the shared rules in `../shared/README.md`.
- Non-zero exit codes are converted into a tool error (Codex returns a `RespondToModel` error containing the formatted output).
- Timeouts and sandbox denials are surfaced as tool errors, using the *same* output format but with timeout/denied info included.
- If the command payload is detected to be an `apply_patch` invocation (directly or via a shell heredoc), Codex intercepts and routes it through the `apply_patch` flow.
