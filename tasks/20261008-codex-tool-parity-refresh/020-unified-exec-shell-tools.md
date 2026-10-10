# Unified exec shell tools (exec_command + write_stdin)

Implement the current upstream Codex CLI unified exec shell surface —
`exec_command` plus `write_stdin` — as the forward-looking shell tooling for
codex agents, replacing reliance on the upstream-removed `shell` (array) and
`shell_command` tools.

Parent Task: `tasks/20261008-codex-tool-parity-refresh/000-main.md`

## Requirements checklist

- [ ] An `exec_command` tool is available to codex agents with the current
  upstream contract: `cmd` (string, required), `workdir`, `tty`, `yield_time_ms`,
  `max_output_tokens`, plus `login` and sandbox/approval parameters where the
  platform has equivalents, and the upstream description "Runs a command in a
  PTY, returning output or a session ID for ongoing interaction."
- [ ] A `write_stdin` tool is available with the current upstream contract:
  `session_id` (required), `chars`, `yield_time_ms`, `max_output_tokens`, and
  the upstream description "Writes characters to an existing unified exec
  session and returns recent output."
- [ ] Long-running commands yield a session ID and remain interactable through
  `write_stdin` (PTY-backed when `tty` is set, pipe-backed otherwise).
- [ ] Tool selection and rollout are decided explicitly (see open questions)
  and preserve a working shell tool for every currently supported model and
  `shell_tool_mode`.
- [ ] Reference snapshots for the shell surface reflect the current upstream
  contract (`exec_command`, `write_stdin`) and stop presenting the removed
  `shell` variants as current.
- [ ] Unit tests cover schema parity, session lifecycle, output truncation, and
  error paths; integration coverage exercises the tools through the default
  codex agent configuration.

## Supporting details

- Upstream source of truth:
  `../codex/codex-rs/core/src/tools/handlers/shell_spec.rs`
  (`create_exec_command_tool_with_environment_id`, `create_write_stdin_tool`),
  `../codex/codex-rs/core/src/tools/handlers/unified_exec.rs` (handler), and
  `shell_spec_tests.rs`.
- Upstream timeline: array `shell` removed `83decfa3` (2026-05-13, #22246);
  `shell_command` removed `8a40095e` (2026-08-20, #39757); unified exec is the
  only current shell surface.
- Current local surface:
  `plugins/codex-tools/src/codex_tools/shell_tool.py` (array `shell`),
  `shell_command_tool.py` (`shell_command`), `shell_tool_legacy.py` (opt-in
  legacy string `shell`). `shell_tool_mode: "auto"` picks `shell_command` for
  shell-command family models (`model_family.py`), which includes all
  `gpt-5.1+`/`sol`/`terra`/`luna`/`astra` and `-codex` models — i.e. every
  model the codex agents realistically run.
- The default-config gpt-6.x developer messages already reference
  `functions.exec`-style naming, so prompt-side alignment favors this change.
- `write_stdin` already has a current reference snapshot
  (`reference/codex-cli-tools/write_stdin/schema.json`); `exec_command` has no
  snapshot directory yet even though the reference README lists it.
- Upstream output schema (`unified_exec_output_schema`): `chunk_id`,
  `wall_time_seconds` (required), `exit_code`, `session_id`,
  `original_token_count`, `output` (required).

## Execution plan

Status: Draft

Not yet approved. The material design decisions below must be resolved with
the user before implementation.

Approach outline (to finalize after decisions):

1. Add a unified exec tool plugin in `plugins/codex-tools` implementing
   `exec_command` + `write_stdin` with a PTY/pipe session runtime keyed by
   `session_id`, honoring `workdir`, `yield_time_ms`, `max_output_tokens`, and
   the existing `allowed_paths`/working-directory sandbox conventions.
2. Extend `shell_tool_mode` with a unified exec mode and decide the `auto`
   mapping; wire model-family selection accordingly.
3. Refresh the reference shell snapshots; update the plugin README and the
   default-config codex agent documentation where `shell_command` is named.
4. Unit tests (schema parity, session lifecycle, truncation, errors) plus
   default-config integration coverage through the public agent API.

### Implementation decisions and open questions

- Rollout mode (material): add `shell_tool_mode: "exec_command"` (or
  `"unified_exec"`) as opt-in, or make `auto` select unified exec for
  shell-command family models and demote `shell_command`? Recommendation:
  opt-in mode first, flip `auto` after burn-in, but the default affects all
  codex agents immediately, so this needs an explicit user decision.
- Fate of `shell` (array) and `shell_command` (material): keep as selectable
  legacy modes (upstream-removed but working locally), or remove? Removal
  affects persisted sessions and any configured agents pinned to those modes.
- PTY runtime (implementation): stdlib `pty`/`selectors`-based session manager
  versus a dependency; must work on macOS/Linux (Windows is out of scope for
  this platform today).
- Sandbox/approval parameters: upstream exposes `sandbox_permissions`,
  `justification`, `prefix_rule`, `additional_permissions`; the platform has a
  different permission model. Decide which parameters to accept (possibly
  accept-and-document vs reject) — user-visible contract decision.
- `environment_id` parameter: omit (no multi-environment concept) unless the
  platform gains one; same decision as view_image in the 010 subtask.
- Session lifetime: per-request vs per-session (turn-spanning) sessions;
  upstream keeps sessions across turns within a rollout. Affects state store
  and cleanup.

### Documentation

- `plugins/codex-tools/README.md` — new tools section, config keys, mode
  matrix.
- `plugins/codex-tools/reference/codex-cli-tools/` — `exec_command/` snapshot,
  updated `shell/` and README tool-list notes marking removed variants as
  historical.
- `application/python/docs/configuration.md` if `shell_tool_mode` values change.

### Task checklist

- [ ] Resolve rollout, legacy-tool, sandbox-parameter, and session-lifetime
      decisions with the user; return plan to Approved.
- [ ] Implement `exec_command` + `write_stdin` plugin and session runtime.
- [ ] Wire tool selection / `shell_tool_mode`.
- [ ] Refresh reference snapshots and documentation.
- [ ] Add unit and integration tests; run plugin and application test suites.

### Requirement verification

- Schema parity: unit tests asserting the exact `exec_command`/`write_stdin`
  schemas against the upstream spec text.
- Session lifecycle and interaction: unit/integration tests driving a real
  long-running command through `exec_command` → session ID → `write_stdin`
  through the public tool boundary.
- Default-config behavior: application-level integration test through the
  public agent API for a codex agent with the decided default mode.

### Additional implementation verification

- Output truncation and token-budget behavior compared against upstream
  `unified_exec` handler semantics.
- Cross-platform smoke of the PTY runtime on macOS (primary dev platform).
