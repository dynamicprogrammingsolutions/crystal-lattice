# `exec_command`

`exec_command` is the “unified exec” / interactive exec tool. It runs a
command (optionally in a PTY), waits up to `yield_time_ms`, and returns
either the finished output with its exit code or a `session_id` for a
still-running process that can be polled or fed via `write_stdin`.

Upstream removed the older `shell` (array) tool on 2026-05-13 (`83decfa3`)
and `shell_command` on 2026-08-20 (`8a40095e`); unified exec
(`exec_command` + `write_stdin`) is the only current shell surface.

## JSON tool spec

- `schema.without_request_permissions.json` — approval parameters with the
  two-value `sandbox_permissions` enum (`exec_permission_approvals_enabled`
  false upstream).
- `schema.with_request_permissions.json` — adds `additional_permissions`
  and the three-value `sandbox_permissions` enum (feature gated upstream).

Upstream variant gating (not serialized differently otherwise):

- `environment_id` — added when the multi-environment feature is enabled
  (description: “Environment id from <environment_context>. Omit to use the
  primary environment.”).
- `login` — added when `allow_login_shell` is enabled.
- `shell` — omitted in some zsh-fork configurations.
- Windows — the description gains Windows shell safety guidance, and
  `yield_time_ms` uses a Windows-specific description with a 10000 ms floor.

The `output_schema` (structured result: `chunk_id`, `wall_time_seconds`,
`exit_code`, `session_id`, `original_token_count`, `output`) is
serde-skipped on the Responses wire upstream, so it does not appear in
these snapshots.

## Handler behavior (implementation notes)

- Model-facing response text format:
  `Wall time: <s> seconds` / `Process exited with code <n>` or
  `Process running with session ID <n>` / optional
  `Original token count: <n>` / `Output:` + output.
- `yield_time_ms` is clamped to 250-30000 ms (default 10000 ms).
- Output is truncated per call to `max_output_tokens` (default 10000) with
  a head/tail split and a `Warning: truncated output (original token
  count: N)` + `Total output lines: L` header.
- Non-empty `write_stdin` writes to a non-TTY session are rejected
  (“stdin is closed for this session; rerun exec_command with tty=true to
  keep stdin open”); `\x03` interrupts the session instead.
- A process observed finished leaves the session store, so later
  `write_stdin` calls report `Unknown process id <n>`.
- Produces the same structured vs freeform output formatting described in
  `../shared/README.md`.

## Platform divergence (this plugin)

The locally served schema omits the approval parameters
(`sandbox_permissions`, `justification`, `prefix_rule`,
`additional_permissions`) and `environment_id`: the platform has no
per-command sandbox, approval flow, or multi-environment concept, and
no-op parameters would mislead the model. All other parameter names and
description texts match upstream exactly.

Windows is not implemented locally yet; see
`tasks/20261008-codex-tool-parity-refresh/030-windows-unified-exec-support.md`.
