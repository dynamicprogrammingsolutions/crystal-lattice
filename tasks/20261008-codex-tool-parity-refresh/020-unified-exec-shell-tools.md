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
- [ ] Tool selection and rollout are decided explicitly (D1 option B: `auto`
  serves unified exec for shell-command family models) and preserve a working
  shell tool for every currently supported model and `shell_tool_mode`.
- [ ] Reference snapshots for the shell surface reflect the current upstream
  contract (`exec_command`, `write_stdin`) and stop presenting the removed
  `shell` variants as current.
- [ ] Unit tests cover schema parity, session lifecycle, output truncation, and
  error paths; integration coverage exercises the tools through the default
  codex agent configuration.

## Supporting details

### Upstream contract (verified 2026-10-10)

- Source of truth: `../codex/codex-rs/core/src/tools/handlers/shell_spec.rs`
  (`create_exec_command_tool_with_environment_id`, `create_write_stdin_tool`),
  `unified_exec.rs` + `unified_exec/{exec_command.rs,write_stdin.rs}` handlers,
  `shell_spec_tests.rs`.
- `exec_command` schema (non-Windows, options
  `include_shell_parameter=true`, `allow_login_shell=true`,
  `exec_permission_approvals_enabled=false`, `include_environment_id=false`):
  - description: "Runs a command in a PTY, returning output or a session ID
    for ongoing interaction."
  - `cmd` (string, required): "Shell command to execute."
  - `workdir`: "Working directory for the command. Defaults to the turn cwd."
  - `tty` (boolean): "True allocates a PTY for the command; false or omitted
    uses plain pipes."
  - `yield_time_ms` (number): "Wait before yielding output. Defaults to
    10000 ms; effective range is 250-30000 ms."
  - `max_output_tokens` (number): "Output token budget. Defaults to 10000
    tokens; larger requests may be capped by policy."
  - `shell` (string): "Shell binary to launch. Defaults to the user's default
    shell."
  - `login` (boolean): "True runs the shell with -l/-i semantics; false
    disables them. Defaults to true."
  - approval params (`sandbox_permissions`, `justification`, `prefix_rule`,
    `additional_permissions`) are always added upstream; gated variants exist
    for `environment_id` and Windows guidance.
  - `timeout_ms` exists in the handler args but is **not** in the schema (it
    only applies to upstream's internal one-shot lifetime).
- `write_stdin` schema: description "Writes characters to an existing unified
  exec session and returns recent output."; `session_id` (number, required)
  "Identifier of the running unified exec session."; `chars` "Bytes to write
  to stdin. Defaults to empty, which polls without writing.";
  `yield_time_ms` "Wait before yielding output. Non-empty writes default to
  250 ms and cap at 30000 ms; empty polls wait 5000-300000 ms by default.";
  `max_output_tokens` as above.
- Result shape (`unified_exec_output_schema`, not serialized on the Responses
  wire — `output_schema` is serde-skipped upstream, same as the `view_image`
  finding): `chunk_id` (string, optional), `wall_time_seconds` (required),
  `exit_code` (number, when the process finished during this call),
  `session_id` (number, to pass to `write_stdin` when still running),
  `original_token_count`, `output` (required), `additionalProperties: false`.
- Upstream semantics: process IDs are integers allocated by a
  `UnifiedExecProcessManager` held in session services (in-process, persists
  across turns); sessions are drained-not-killed on cancellation; output is
  token-approximation truncated (50/50 head/tail) per call.
- Upstream timeline: array `shell` removed `83decfa3` (2026-05-13, #22246);
  `shell_command` removed `8a40095e` (2026-08-20, #39757); unified exec is the
  only current shell surface.

### Platform facts (verified 2026-10-10)

- Current local surface: `shell_tool.py` (array `shell`),
  `shell_command_tool.py` (`shell_command`), `shell_tool_legacy.py` (opt-in
  legacy string `shell`). `shell_tool_mode: "auto"` picks `shell_command` for
  shell-command family models (`model_family.py`), which includes
  `gpt-6.1-sol`. **Gap:** both tools' `is_enabled` treat any unrecognized mode
  value as `auto`, so a new mode value must be handled explicitly in both.
- The gpt-6.x developer messages already reference `functions.exec`-style
  naming, so prompt-side alignment favors this change.
- Tool protocol capabilities (`core/python/agent_core/plugin/tool.py`):
  `init` → per-request state, `prepare_async(config, state, context=...)`,
  `get_tool_schemas(state, prepared=...)`, `stream_tool` (preferred by the
  tool loop when present), `execute_tool`/`execute_tool_async`,
  `format_tool_result`, `to_display_format`.
- Cross-request persistence precedent: `CodexMCPTool` stores a long-lived
  `MCPRegistry` in the tool runtime context store
  (`context["runtime_store"]` with `get`/`get_or_create`, plus
  `context["app"]`), keyed by `runtime_store_key`
  (`mcp_tool.py:612-651`). This is the pattern for a unified exec process
  manager that must survive across requests.
- `plugins/tool-compat-shared` already hosts the shared shell engine used by
  the codex shell tools (`detect_shell`, `build_shell_args`,
  `run_shell_command`, `terminate_process_tree`, `truncate_output` with
  token-approximation 50/50 head/tail) and a filesystem-backed
  `background_processes.py` engine used by `claude-tools` (start/poll model,
  no stdin interactivity — detached processes cannot be written to later, so
  it does not fit unified exec's interactive sessions; an in-process manager
  holding live handles is required, matching upstream).
- `BaseCodexShellTool` (`base_shell_tool.py`) provides the shared
  result formatting ("Exit code / Wall time / Total output lines"), 10K-token
  default truncation, apply_patch interception, spawn-error handling, preview
  and display formatting. The new tools should reuse this base.
- `write_stdin` already has a current reference snapshot
  (`reference/codex-cli-tools/write_stdin/schema.json`); `exec_command` has
  no snapshot directory yet even though the reference README lists it.
- Windows is not implemented here; it is tracked as a separate subtask:
  `tasks/20261008-codex-tool-parity-refresh/030-windows-unified-exec-support.md`
  (upstream Windows guidance text, ConPTY, and `CreateProcessW` paths belong
  there). This subtask implements the POSIX surface only.

## Execution plan

Status: Approved

Approved 2026-10-10 with the user's decisions: **D1 = option B** (flip `auto`
for shell-command family models so codex agents get unified exec
immediately), **D2 = omit approval/sandbox parameters** (documented
divergence), **D3 = cross-request sessions** via the tool runtime store with
TTL cleanup. Windows support is tracked separately in
`tasks/20261008-codex-tool-parity-refresh/030-windows-unified-exec-support.md`.

### Design

Components and responsibilities:

1. **Interactive process engine** — new
   `plugins/tool-compat-shared/src/tool_compat_shared/interactive_process_engine.py`.
   Generic, provider-agnostic session manager, mirroring how `shell_engine`
   relates to the shell tools:
   - `InteractiveProcessSession`: spawns via the shared shell resolution
     (`detect_shell`, `build_shell_args`, optional explicit shell path,
     login/non-login), either pipe-backed (`pty` unused, stdin/stdout/stderr
     pipes) or PTY-backed (stdlib `pty.openpty()`, command runs on the slave,
     master read via a selector-based reader thread). A reader thread
     accumulates output into a ring buffer with a read position;
     `write(chars)` posts to stdin/master; `drain(until_deadline)` returns new
     output without blocking the event loop; `terminate()` uses the existing
     `terminate_process_tree`; exposes `exit_code`, `alive`, start metadata.
   - `InteractiveProcessManager`: allocates monotonically increasing integer
     session ids (upstream parity), enforces a concurrent-session cap and an
     idle TTL with a reaper, terminates live sessions on interpreter exit
     (`atexit`), and records sessions for observability (command, workdir,
     tty, started-at, last-drained-at).
   - No new dependencies: stdlib `pty`, `selectors`, `threading`.

2. **`ExecCommandTool`** — `plugins/codex-tools/src/codex_tools/unified_exec_tool.py`,
   subclassing `BaseCodexShellTool` for formatting/truncation/interception:
   - Schema: upstream texts listed in Supporting details; parameter surface
     per decision D2 (`login`, `shell` included; approval params omitted by
     recommendation; no `environment_id`, no `timeout_ms` — matching the
     upstream schema).
   - `execute_tool_async`: resolve `workdir` via `resolve_tool_workdir`,
   apply_patch interception first (parity with other shell tools), spawn via
   the engine, wait up to `yield_time_ms` (clamped to 250-30000 ms, default
   10000), then return. If the process finished: formatted output with
   `exit_code` and `wall_time_seconds`. If still running: `session_id` plus
   output-so-far and guidance-free "still running" framing consistent with
   base formatting. Per-call `max_output_tokens` truncation (default 10000)
   with `original_token_count`.
   - `stream_tool`: yields partial output parts while waiting inside the
   yield window, then the final result dict (same contract as
   `shell_command`'s streaming).
   - Manager resolution: from the tool runtime context store
     (`get_or_create` keyed by a `runtime_store_key`, MCP precedent) when
     available; fallback to a module-level manager for request-scoped/unit
     use. Per D3.

3. **`WriteStdinTool`** — same module, also on `BaseCodexShellTool`:
   - Schema per Supporting details; `session_id` is a number.
   - `execute_tool_async`/`stream_tool`: look up the session (unknown/finished
   → plain error text), write `chars` when non-empty, wait up to
   `yield_time_ms` (non-empty writes default 250 ms cap 30000; empty polls
   default 5000 ms, allowed up to 300000), drain and return with
   `exit_code`/`session_id`/`wall_time_seconds`/`output` as applicable.

4. **Selection wiring**:
   - Register both tools in `agent_plugin.json`.
   - `shell_tool_mode` gains `"exec_command"`: both new tools enabled, and
     `shell`/`shell_command` explicitly disabled for that mode (update
     `is_enabled` in `shell_tool.py` and `shell_command_tool.py` so unknown
     explicit modes no longer fall through to `auto`).
   - **`auto` flips for the shell-command family (D1 option B):** the new
     tools' `is_enabled` enables them under `auto` when the `codex-variant`
     tag is present (the same condition `shell_command` used), and
     `shell_command` no longer self-enables under `auto` — it remains
     available only via explicit `shell_tool_mode: "shell_command"`. Array
     `shell` under `auto` is unchanged (legacy models keep it).
   - Existing tests that assert `auto` → `shell_command` for codex-variant
     models are updated to the new expectation; every model × mode
     combination must still resolve to exactly one working shell surface.

5. **Reference and docs**:
   - New `reference/codex-cli-tools/exec_command/` (schema.json of the
     default non-Windows variant + README documenting gated variants and the
     platform's omitted approval params per D2).
   - Mark `shell/` and `shell_command`-era snapshots as historical in the
     reference READMEs; `write_stdin/schema.json` already current.
   - Plugin README: new tools section, config keys
     (`unified_exec_session_ttl_seconds` default 900,
     `unified_exec_max_sessions` default 8), mode matrix.
   - `application/python/docs/configuration.md` if it documents
     `shell_tool_mode` values.

Data flow: model calls `exec_command` → tool resolves manager (runtime store
→ fallback) → engine spawns session → tool waits ≤ `yield_time_ms` →
finished: formatted result with exit code; running: result with `session_id`
→ model later calls `write_stdin(session_id, chars, yield_time_ms)` → same
drain path. Sessions survive across tool calls and, per D3 recommendation,
across requests through the runtime store; idle sessions are reaped by TTL.

Compatibility: legacy models keep array `shell` under `auto`; `shell_command`
remains available via its explicit mode; no persisted-data changes. The
default surface for shell-command family models changes from `shell_command`
to `exec_command` + `write_stdin` (D1 option B, user-approved).

### Ordered steps

1. Implement the interactive process engine in `tool-compat-shared` with
   unit tests (spawn/drain/write/terminate, PTY and pipe modes, TTL reaper,
   session cap).
2. Implement `ExecCommandTool` + `WriteStdinTool` (schemas, execution,
   streaming, formatting, interception) and register them.
3. Wire selection: new `exec_command` mode, `auto` flip for the
   shell-command family, `is_enabled` updates in the existing shell tools,
   and updates to existing selection tests.
4. Add reference snapshots and update documentation.
5. Add codex-tools unit tests (schema parity with exact upstream texts,
   lifecycle, truncation, clamping, errors, mode matrix) and deterministic
   plugin-local integration tests (real processes: short command, long
   command → session, interactive `cat`/read via PTY, poll semantics).
6. Extend the application-level shell-selection test
   (`test_shell_tool_selection_application.py` pattern) for the new mode and
   the flipped `auto` expectation, and add a default-config integration test
   driving `exec_command` → `write_stdin` through the public agent API with
   a deterministic provider.
7. Run `pytest plugins/codex-tools/tests -m 'not integration' -q`, the new
   integration tests, the application shell-selection tests, and `ruff check`
   on changed files.

### Implementation decisions and open questions

Resolved material decisions (user-approved 2026-10-10):

- **D1 — Rollout: option B.** `auto` flips for shell-command family models:
  codex agents (including `gpt-6.1-sol`) get `exec_command` + `write_stdin`
  by default, matching the `functions.exec` wording already present in the
  gpt-6.x developer messages. `shell_command` stays available only via
  explicit `shell_tool_mode: "shell_command"`; array `shell` keeps serving
  legacy models under `auto`.
- **D2 — Approval/sandbox parameters: omitted.**
  `sandbox_permissions`/`justification`/`prefix_rule`/
  `additional_permissions` are not served because the platform has no
  per-command sandbox or approval flow and no-op parameters would mislead
  the model. The divergence is documented in the reference README.
- **D3 — Session lifetime: cross-request.** The in-process manager is
  persisted via the tool runtime store (MCP precedent), so sessions survive
  across requests/turns; idle sessions are reaped by TTL (default 900 s)
  and concurrent sessions are capped (default 8).

Other resolved implementation decisions: stdlib-only PTY runtime; engine
lives in `tool-compat-shared`; `login` included (default true, matching
current platform shell semantics), `shell` included; `environment_id` and
`timeout_ms` omitted (no multi-environment concept; upstream schema omits
`timeout_ms` too); per-call cancellation stops the wait but does not kill
interactive sessions; `chunk_id` omitted in v1 (only used by upstream for
multi-chunk splitting; revisit if truncation-while-running needs it).

No open questions remain for this subtask.

### Documentation

- `plugins/codex-tools/README.md` — new tools section, config keys, mode
  matrix.
- `plugins/codex-tools/reference/codex-cli-tools/exec_command/` — new
  snapshot + README with variant notes and documented platform divergences.
- Reference READMEs for `shell/` — mark as historical (upstream removed).
- `plugins/tool-compat-shared/README.md` — new engine section, if it
  documents engines.
- `application/python/docs/configuration.md` — only if it lists
  `shell_tool_mode` values.

### Task checklist

- [x] Resolve D1-D3 with the user; update this plan to Approved.
- [x] Interactive process engine + unit tests.
- [x] `ExecCommandTool` + `WriteStdinTool` + registration.
- [x] `shell_tool_mode` wiring incl. existing `is_enabled` updates.
- [x] Reference snapshots and documentation.
- [x] Unit + integration tests (plugin and application level).
- [x] Full verification runs.

## Implementation Notes

- 2026-10-10 (execution): all components implemented and verified locally;
  see Completion Notes for the final record.
- Manager resolution changed during implementation: managers are keyed by
  their settings fingerprint (`max_sessions`, `ttl`) both in the runtime
  store (`codex_tools.unified_exec.<max>.<ttl>`, MCP runtime-key precedent)
  and in a module-level fallback dict, so the `unified_exec_*` config keys
  apply on both paths. Without this the fallback manager ignored the config.
- Added `plugins/tool-compat-shared/tests/conftest.py` (same pattern as the
  codex-tools conftest): the suite previously imported the package from a
  stale editable install pointing at a different checkout
  (`ai-agent-platform-main`); the conftest pins this checkout's `src`.
  Pre-existing failures unrelated to this work exist in that suite
  (1 `test_search_engine` glob-sort failure, 5 `test_web_search_engine`
  Tavily-mock errors, 1 order-dependent `test_background_processes` failure
  in full-suite runs); engine code is byte-identical between checkouts, so
  these predate this change.
- Verification coverage gap found and fixed during execution:
  `test_shell_tool_openrouter_integration.py` (skipif-key-gated, no API
  calls) and `test_codex_shell_tool_openrouter_integration.py`
  (integration+openrouter marked, no API calls) still asserted the old
  `auto` → `shell_command` behavior and were skipped in the keyless full
  run. Both files now register the unified exec tools and assert the new
  mode matrix; both pass with the key exported (27 passed).
- Per user request, the hosted-API test default
  `OPENROUTER_MODEL_CODEX_TOOLS` in `test_codex_shell_tool_api_integration.py`
  changed from `openai/gpt-5.2-codex` to `openai/gpt-6-luna`
  ($0.10/$0.50 per M tokens on OpenRouter). The old default 402'd with the
  account's remaining credits (~$0.31) at the provider's default token
  budget; the two affected tests pass with the new default (real model
  round-trip: model → `exec_command` call → execution → file created). The
  402 is surfaced by the provider as an empty response with no error
  metadata (pre-existing provider behavior quirk, not addressed here).
- Incident during verification (no lasting effect): a `git stash push` with
  an untracked path failed, but a subsequent `git stash pop` popped a
  pre-existing stash (`Preserve reconciled task 013...`). The pop hit
  conflicts on 3 files, kept the stash entry, and applied no net changes
  (its content had already landed on develop); the 3 conflicted files were
  restored to their pre-pop state with `git checkout --ours` +
  `git restore --staged`. Working tree and stash list verified intact.
- Pyright: the new engine is clean; the new tool module shows the same
  pre-existing `reportIncompatibleMethodOverride` errors as the sibling
  shell tools, and its `tool_compat_shared.interactive_process_engine`
  import is unresolved under pyright because `plugins/*/src` is not in
  `pyrightconfig.json` extraPaths and the stale editable install lacks the
  new module (environment, not code).

### Requirement verification

- Schema parity: unit tests asserting the exact upstream description and
  parameter texts for both tools at the public `get_tool_schemas` boundary
  (same style as the 010 subtask tests).
- Session lifecycle and interaction: deterministic plugin-local tests with
  real processes driving `exec_command` (finish path and session path) and
  `write_stdin` (poll and write) through `ToolWrapper`, including PTY mode,
  truncation, yield clamping, and error paths (unknown session, invalid
  args).
- Tool selection: application-level test that an agent configured with the
  decided mode exposes exactly the intended shell tools (extends the
  existing `test_shell_tool_selection_application.py` coverage), crossing
  the real config → plugin wiring path.
- End-to-end: default-config integration test through the public agent API
  with a deterministic provider executing a command and polling a session.

### Additional implementation verification

- Output truncation behavior compared against upstream
  `unified_exec` semantics (token approximation, per-call budget).
- PTY runtime smoke on macOS (primary platform), including terminal-echo
  interaction and cleanup on idle expiry.
- Leak check: no surviving child processes after TTL reaper and interpreter
  exit in the unit tests.

## Completion Notes

Completed 2026-10-10.

**Outcome:** the upstream unified exec shell surface is implemented and
selected by default for the shell-command model family. Components:

- `plugins/tool-compat-shared/.../interactive_process_engine.py` —
  generic session engine (pipe/PTY spawn, reader threads, drain, write,
  interrupt, terminate; manager with integer ids, session cap, idle TTL,
  atexit cleanup; stdlib-only).
- `plugins/codex-tools/.../unified_exec_tool.py` — `ExecCommandTool` +
  `WriteStdinTool` on `BaseCodexShellTool`, upstream-parity schemas and
  model-facing response format ("Wall time / Process exited|running /
  Original token count / Output"), per-call token truncation with the
  upstream warning header, upstream yield-time clamping and stdin rules
  (non-tty writes rejected with the upstream message; `\x03` interrupts),
  apply_patch interception, streaming, config-fingerprinted managers via
  the runtime store or module fallback.
- Selection: `shell_tool_mode` gained `exec_command`; `auto` now selects
  unified exec for codex-variant models; `shell_command` is explicit-mode
  only; unknown explicit modes disable all shell tools.
- Reference snapshots refreshed to current upstream
  (`exec_command/` schemas + README, `write_stdin/`), `shell/` and
  `shell_command/` marked historical; READMEs updated.

**Requirement evidence:** 46 tests in `test_unified_exec_tool.py` (schema
parity incl. reference-snapshot text comparison, lifecycle, PTY
interaction, truncation, clamping, errors, interception, streaming,
selection matrix, public `execute_tool_calls` end-to-end); 22 engine tests
in `test_interactive_process_engine.py`; updated selection suites.
Verification: full codex-tools suite 238 passed / 39 key-gated skips;
engine + tool suites re-run after the final fix (68 passed); key-gated
selection suites 27 passed with the key; hosted-API round-trip passed on
`openai/gpt-6-luna` (model issued `exec_command`, file created);
`test_shell_tool_selection_application.py` 11 passed with the key; ruff
clean on all changed files; engine clean under pyright.

**Deviations/findings:** managers keyed by settings fingerprint (store and
fallback) so config keys apply on both paths; tool-compat-shared tests
gained a conftest pinning this checkout's src over a stale editable
install; hosted-API default model switched to `openai/gpt-6-luna` (user
request; old default 402'd on remaining account credits); pre-existing
unrelated failures exist in the tool-compat-shared suite (see
Implementation Notes).

**Not run / deferred:** Windows (subtask 030); `chunk_id` omitted in v1;
mobile UI smoke not performed. Follow-up approved: subtask 040 (drop
model-based selection; session-settable `shell_tool_mode` settings
plugin).
