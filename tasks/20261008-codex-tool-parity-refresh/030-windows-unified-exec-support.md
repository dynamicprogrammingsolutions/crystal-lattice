# Windows unified exec support (exec_command + write_stdin)

Bring the unified exec shell tools (`exec_command` + `write_stdin`, delivered
by the 020 subtask) to Windows: native shell resolution, ConPTY-backed
`tty` sessions, and the upstream Windows schema guidance variant.

Parent Task: `tasks/20261008-codex-tool-parity-refresh/000-main.md`
Depends On: `tasks/20261008-codex-tool-parity-refresh/020-unified-exec-shell-tools.md`

## Requirements checklist

- [ ] `exec_command` and `write_stdin` execute commands on Windows with
  correct native shell resolution (PowerShell/cmd per the upstream Windows
  shell contract).
- [ ] `tty: true` sessions work on Windows via ConPTY (or an explicitly
  decided, documented, and tested fallback if ConPTY is unavailable).
- [ ] The Windows schema variant (upstream `include_windows_shell_guidance`
  description text) is served when running on Windows, and the non-Windows
  variant elsewhere.
- [ ] Windows behavior is covered by tests: schema-variant unit tests that
  run on any platform, plus execution tests gated to Windows environments
  (skipped elsewhere with an explicit, reported skip reason).

## Supporting details

Facts (verified against `../codex` on 2026-10-10):

- Upstream Windows surface: `shell_spec.rs` gates a Windows guidance variant
  of the `exec_command` description via `include_windows_shell_guidance`
  (`cfg!(windows)` in the default handler options); the process/PTY layer is
  `codex-rs` `unified_exec` over `portable-pty` (ConPTY on Windows) and
  `CreateProcessW` spawn paths; Windows also carries a
  `windows_sandbox_level` config concept.
- The 020 engine (`tool-compat-shared`
  `interactive_process_engine.py`) uses POSIX stdlib `pty`/`selectors` and
  must grow a platform abstraction: PTY backend selection
  (POSIX `pty.openpty()` vs Windows ConPTY) and spawn path
  (`subprocess` works cross-platform; process-tree termination on Windows
  needs `taskkill`/job-object semantics rather than POSIX process groups).
- The platform has no Windows CI or documented Windows deployment today;
  verification environment availability is an open question below.

## Execution plan

Status: Draft

Not yet approved and not scheduled. Detailed planning happens when this
subtask is picked up; the outline below records the known shape.

### Design outline

- Extend the interactive process engine with a platform layer: a PTY backend
  protocol with a POSIX implementation (current stdlib code) and a Windows
  ConPTY implementation; Windows-aware shell resolution and process-tree
  termination.
- Serve the upstream Windows guidance schema variant when
  `sys.platform == "win32"` in `ExecCommandTool.get_tool_schemas`, mirroring
  upstream's `include_windows_shell_guidance` gating.
- Keep the tool-layer contract (schemas, result dicts, selection modes)
  identical across platforms; only the engine internals and the gated
  description text differ.

### Ordered steps

1. Investigate upstream Windows specifics (`portable-pty` ConPTY usage,
   Windows shell defaults, `windows_sandbox_level` interaction) and pick the
   ConPTY runtime approach.
2. Add the platform abstraction to the engine and the Windows backends.
3. Gate the Windows schema variant.
4. Tests per the requirements; documentation.

### Implementation decisions and open questions

- **ConPTY runtime (material):** `pywinpty` dependency (maintained, wheels
  available, small API) vs raw ctypes `CreatePseudoConsole` (no new
  dependency but high-risk low-level code to own). Recommendation:
  evaluate `pywinpty` first; fall back to ctypes only if the dependency is
  unacceptable.
- **Default Windows shell (material):** which shell `exec_command` resolves
  to when the model does not pass `shell` (PowerShell vs cmd vs following
   upstream's detection exactly).
- **Verification environment (material):** no Windows CI is known; decide
  whether a manual Windows host is available for verification runs, or
  whether the first iteration ships with cross-platform unit tests plus
  explicitly reported "not run" execution coverage.
- **`tty` fallback (material if ConPTY is unavailable):** degrade to pipes
  with a documented warning vs error out. Upstream always has ConPTY
  available; the platform needs an explicit decision if it ships without.

### Documentation

- `plugins/codex-tools/README.md` — Windows notes in the unified exec
  section.
- `plugins/codex-tools/reference/codex-cli-tools/exec_command/README.md` —
  document the Windows guidance variant snapshot.
- `plugins/tool-compat-shared/README.md` — engine platform support notes.

### Task checklist

- [ ] Resolve the open questions above; write the detailed plan and get
  approval.
- [ ] Engine platform abstraction + Windows backends.
- [ ] Windows schema variant.
- [ ] Tests (cross-platform unit + Windows-gated execution).
- [ ] Documentation updates.

### Requirement verification

- Schema variant: unit tests asserting the exact upstream Windows guidance
  description text is served on `win32` and the POSIX variant elsewhere
  (monkeypatch `sys.platform`; no Windows host needed).
- Execution: Windows-gated integration tests driving `exec_command` →
  `write_stdin` (pipe and ConPTY) through `ToolWrapper` on a Windows host;
  reported as "not run" if no environment is available.
- Shell resolution: unit tests for Windows shell detection logic
  (monkeypatched environment).

### Additional implementation verification

- Process-tree termination semantics on Windows (no orphaned children after
  session termination or interpreter exit).
- PTY echo/interaction smoke on the chosen ConPTY runtime.
