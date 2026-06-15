# `exec_command`

`exec_command` is the “unified exec” / interactive exec tool. It can return either a complete output or a session id (paired with `write_stdin`) depending on runtime behavior.

## JSON tool spec

- `schema.with_request_permissions.json` includes `additional_permissions` (feature gated).
- `schema.without_request_permissions.json` omits it.

## Handler behavior (implementation notes)

- Runs a command (optionally in a PTY), supports incremental output via `yield_time_ms` and token-budget truncation via `max_output_tokens`.
- Produces the same structured vs freeform output formatting described in `../shared/README.md`.
- Non-zero exit code becomes a tool error containing the formatted output.
