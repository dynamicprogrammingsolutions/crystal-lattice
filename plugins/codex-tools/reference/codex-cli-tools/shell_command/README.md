# `shell_command`

**Historical:** upstream Codex CLI removed `shell_command` on 2026-08-20
(`8a40095e`, #39757, "Standardize shell execution on unified exec") and now
ships `exec_command` + `write_stdin`; see `../exec_command/`. This snapshot
preserves the final pre-removal contract, which the platform still serves
via the explicit `shell_tool_mode: "shell_command"` (under `auto` the
shell-command family now selects unified exec).

## JSON tool spec

- `schema.with_request_permissions.json` includes `additional_permissions` (feature gated).
- `schema.without_request_permissions.json` omits it.

Notes:

- `command` is a **string** (shell script). Codex derives the actual argv via the user’s default shell.
- Optional `login` controls whether the shell is invoked with “login shell” semantics. If login shells are disallowed by config, `login=true` is rejected.

## Model/feature variants

- Most `gpt-5.*-codex` models in the stock catalog use `shell_type = shell_command`, so they prefer exposing this tool.

## Handler behavior (implementation notes)

- Builds an argv command via the user shell and forwards into the same exec orchestration as `shell`.
- Output formatting and truncation follow `../shared/README.md`.
- Non-zero exit code becomes a tool error with the formatted output (so the model sees stderr/stdout in-band).
- Intercepts embedded `apply_patch` invocations and routes them through `apply_patch`.
