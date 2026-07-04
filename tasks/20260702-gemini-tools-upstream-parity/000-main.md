# Gemini-tools upstream parity (`plugins/gemini-tools`)

Bring the Gemini-style tool bundle in `plugins/gemini-tools` closer to the open-source `gemini-cli` checked out at `../gemini-cli`, with extra importance on **LLM-facing semantics and behavior**. These tools exist to give Gemini-trained models familiar tools, behavior, and responses.

Scope: the tool plugins in `plugins/gemini-tools` (Python package `gemini_tools`), with the shell tool (`gemini_shell_tool.py` → `run_shell_command`) as the primary focus.

Out of scope for now: provider changes, UI work, full pty/interactive shell, policy engine.

It is OK to differ from upstream where our implementation is cleaner/simpler/more practical and the difference does not affect LLM-facing behavior. Internal architecture (where truncation is applied, how backgrounding is implemented, etc.) can stay as-is.

## Task checklist

- [ ] `tasks/20260702-gemini-tools-upstream-parity/010-shell-inactivity-timeout.md`

## Guiding principles

1. **LLM-facing parity first.** Schema shape, parameter names, output format, and observable behavior matter most. Internal plumbing does not.
2. **Match upstream naming and schemas.** Tool name (`run_shell_command`), parameter names (`command`, `description`, `dir_path`, `is_background`), and output text format should match `gemini-cli` where practical.
3. **No per-call timeout parameter.** Upstream does not expose a `timeout` parameter to the model, and neither do we. The timeout is a config-level setting only.
4. **Verify upstream before implementing.** Re-read the referenced upstream files in `../gemini-cli` before planning each change. The upstream code may have evolved since this task was written (findings captured 2026-07-02).

## Findings: current state vs upstream

Comparison done 2026-07-02 against `../gemini-cli` (TypeScript) and `plugins/gemini-tools` (Python).

### Matches (no action needed)

- **Tool name & schema**: `run_shell_command` with `command` (req), `description`, `dir_path`, `is_background`. No per-call timeout param in either. Sources: `../gemini-cli/packages/core/src/tools/definitions/dynamic-declaration-helpers.ts:74-110`, `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py:82-129`.
- **Truncation**: 40,000-char threshold, 20% head / 80% tail split, temp-file fallback with `"Output too large. Showing first X and last Y characters. For full output see: <path>"` message. Sources: `../gemini-cli/packages/core/src/utils/fileUtils.ts:596-616`, `gemini_shell_tool.py:32-34, 194-228`.
- **Process group isolation on Unix**: upstream `detached: !isWindows`, ours `start_new_session: True`.
- **Background mode concept**: both delay briefly (~200 ms) before returning the PID.

### Meaningful divergences (LLM-facing or behavioral)

1. **Timeout semantics — the real bug.** Upstream uses an **inactivity** timeout that resets whenever stdout/stderr produces a line (`../gemini-cli/packages/core/src/tools/shell.ts:210-218, 233`). Ours uses a **hard wall-clock** timeout via `asyncio.wait_for(..., timeout=timeout_seconds)` at `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py:436-440`. Our timeout message says `"exceeded the timeout of X minutes without output"` (copied from upstream) but our implementation does not track inactivity — a command that is actively printing gets killed at 120 s and reported as "without output."
2. **Default timeout**: ours 120 s, upstream 300 s (5 min). Source: `../gemini-cli/packages/core/src/config/config.ts:899-900`.
3. **No `GEMINI_CLI=1` env marker**: upstream sets `GEMINI_CLI=1`, `TERM=xterm-256color`, `PAGER=cat`, `GIT_PAGER=cat` on the child env (`../gemini-cli/packages/core/src/services/shellExecutionService.ts:40, 315-322`). We inherit `os.environ` unchanged. Scripts that detect "running inside Gemini CLI" cannot detect us.
4. **Signal not reported**: upstream includes `Signal: <sig>` in output when the process was terminated by a signal (`../gemini-cli/packages/core/src/tools/shell.ts:371-373`). We do not.
5. **Error/output format**: upstream format is `Output: ...\nError: ...\nExit Code: N\nSignal: S\nBackground PIDs: ...\nProcess Group PGID: N` (`../gemini-cli/packages/core/src/tools/shell.ts:355-381`). We fold error into output and omit signal/PGID/background-PID lines.
6. **No child PID discovery**: upstream wraps the command with `pgrep -g 0 >tempFile` on Unix to enumerate child PIDs and reports them as `Background PIDs` (`../gemini-cli/packages/core/src/tools/shell.ts:182-189, 299-326`). We only report the immediate PID.
7. **Platform-aware description**: upstream's `command` parameter description is platform-specific (`bash -c` on Unix, `powershell.exe -NoProfile -Command` on Windows) and mentions process-group killing. Ours is generic.
8. **Windows shell**: upstream uses PowerShell (`powershell.exe -NoProfile -Command`); we use `cmd.exe /c` via `detect_shell()`.

### OK-to-keep differences (internal or non-LLM-facing)

- **No pty/interactive shell**: upstream supports `node-pty` for `vim`/`htop`/interactive `git rebase -i`. We are non-interactive only. Fine for agent context.
- **No live output streaming**: upstream streams partial output to the UI throttled at 1 s. We buffer until completion. UX-only.
- **No policy engine / command parsing**: upstream has `tools.core`/`tools.exclude` allowlists, tree-sitter bash parser for command splitting, user confirmation prompts. App-layer concern, not the tool itself.
- **No binary output detection**: upstream halts on binary streams. Minor UX.
- **Truncation applied at tool layer (ours) vs scheduler (upstream)**: both work; ours is simpler and reusable.
- **Backgrounding via `&` (ours) vs `ShellExecutionService.background(pid)` (upstream)**: both work.

## Decisions (open, with recommendations)

These are not yet finalized. Each should be confirmed when defining a subtask or starting implementation.

### D1 — Inactivity timeout (HIGH, LLM-facing) — RECOMMEND FIX
Switch `run_shell_command` in `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py` from wall-clock to inactivity-based timeout, and change the gemini shell tool default from 120 s to 300 s. This is the only subtask in this task for now — see `010-shell-inactivity-timeout.md`.

### D2 — `GEMINI_CLI=1` env marker (MEDIUM, LLM-facing) — RECOMMEND ADD
Set `GEMINI_CLI=1` (and probably `TERM=xterm-256color`, `PAGER=cat`, `GIT_PAGER=cat`) on the child env in the shared shell engine, gated on a flag so other vendor tools (codex, claude, qwen, etc.) do not inherit Gemini-specific behavior unintentionally. Trivial change, helps scripts detect the runtime.

### D3 — Signal + PGID + Background PIDs in output (MEDIUM, LLM-facing) — RECOMMEND ADD
Extend the gemini shell tool's result formatting to include `Signal: <sig>`, `Process Group PGID: <pid>`, and `Background PIDs: <pids>` lines when applicable, matching upstream's `shell.ts:355-381`. Child PID discovery via `pgrep` is more involved; PGID and signal are cheap.

### D4 — Platform-aware `command` description (LOW, LLM-facing) — RECOMMEND UPDATE
Update the `command` parameter description in `get_tool_schemas` to mention `bash -c` on Unix and the actual Windows shell we use. Cheap.

### D5 — Windows shell: PowerShell vs cmd.exe (MEDIUM, LLM-facing) — DEFER
Upstream uses PowerShell on Windows; we use `cmd.exe`. Switching is a bigger change and may not be worth it for our use cases. If we keep `cmd.exe`, the schema description should say so (see D4). Decide when implementing D4.

### D6 — Child PID discovery via `pgrep` (LOW, LLM-facing) — DEFER
Upstream wraps commands with `pgrep -g 0 >tempFile` to enumerate child PIDs. Adds complexity; only matters for backgrounded process management. Could be a follow-up after D3.

### D7 — Interactive pty, output streaming, policy engine, binary detection (LOW, non-LLM-facing) — DEFER
Significant complexity, mostly UX/app-layer. OK to differ. Revisit only if a concrete need appears.

## References

### Upstream `gemini-cli` (at `../gemini-cli`)
- Shell tool declaration: `packages/core/src/tools/definitions/dynamic-declaration-helpers.ts:74-110`
- Shell tool implementation: `packages/core/src/tools/shell.ts`
- Shell execution service (env vars, pty): `packages/core/src/services/shellExecutionService.ts`
- Truncation: `packages/core/src/utils/fileUtils.ts:596-647`
- Timeout config: `packages/core/src/config/config.ts:899-900`, `packages/cli/src/config/settingsSchema.ts:1244-1253`
- Shell docs: `docs/tools/shell.md`

### Our `gemini-tools` and shared engine
- Shell tool: `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py`
- Shared shell engine: `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
- Shared truncation: same file, `truncate_output` around line 715
- README: `plugins/gemini-tools/README.md`

### Related prior tasks
- `tasks/20260404-shell-process-group-timeout-and-cancel.md` — process-group kill work (already done)
- `tasks/20260404-shell-stdin-hardening-and-noninteractive-defaults.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/` — gemini-tools package creation

## Implementation note

Before planning any subtask, re-read the referenced upstream files in `../gemini-cli` to confirm the behavior described above has not changed. The upstream code is actively developed and the line numbers / behavior in this task were captured on 2026-07-02.