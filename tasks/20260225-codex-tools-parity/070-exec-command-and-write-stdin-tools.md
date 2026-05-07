# 070 — Add `exec_command` and `write_stdin` tools (alternative shell interface)

**STATUS: PENDING**

## Problem

On macOS/Linux, Codex CLI commonly exposes `exec_command` + `write_stdin` (PTY-backed unified exec), not `shell` / `shell_command`.

This provides two benefits:

- better interactive behavior (REPLs, prompts, long-running processes)
- explicit session handles / stdin writes

Our platform currently has only a `shell` tool. We want to add these two tools as additional plugins (without removing `shell`).

## References

- Codex CLI schemas:
  - `docs/codex-tools/exec_command/schema.*.json`
  - `docs/codex-tools/write_stdin/schema.json`
- Codex CLI handler notes:
  - `docs/codex-tools/exec_command/README.md`
  - `docs/codex-tools/write_stdin/README.md`

## Plan

### A) Implement a minimal PTY/session manager

Create a shared module in `plugins/codex-tools/src/codex_tools/exec_runtime.py` that:

- spawns processes in a PTY when available (macOS/Linux) or falls back to pipes
- maintains a mapping: `exec_id -> process/session`
- supports:
  - `exec_command`: start a process or run a one-shot command
  - `write_stdin`: write to an existing exec session

Key decisions (investigate before coding):

- whether session state should live in the tool plugin `state` dict vs a module-level singleton.
- how to enforce timeouts and cleanup.

### B) `ExecCommandTool`

1) Tool name: `exec_command`.
2) Schema should track Codex CLI as closely as practical.
   - Avoid adding non-Codex parameters (treat this as a new major-version tool).
   - If we can’t honor a Codex field yet, prefer failing with a clear message over accepting aliases.

   We can start with a strict subset of Codex fields only if the schema still matches Codex (i.e. the subset is a *real* Codex schema variant). Otherwise, implement the full schema.
   - `cmd: string`
   - `yield_time_ms?: int`
   - `max_output_tokens?: int`
   - `workdir?: string`
   - `env?: object`
   - `tty?: boolean`
3) Behavior:
   - start process
   - return initial output + an `exec_id`
   - support yielding early

### C) `WriteStdinTool`

1) Tool name: `write_stdin`.
2) Schema:
   - `exec_id: string`
   - `stdin: string`
   - `yield_time_ms?: int`
   - `max_output_tokens?: int`
3) Behavior:
   - write stdin
   - collect output for `yield_time_ms`
   - return new output

### D) Output format and limits

Use the same Round-2 truncation policy (token-aware) to cap outputs.

### E) Wire into plugin manifest

- Add two new plugin entrypoints to `plugins/codex-tools/agent_plugin.json`.

### F) Tests

- Exec a simple command and capture output.
- Start `cat` and then write stdin and verify echo.
- Cleanup test to ensure processes are terminated at end of test.

## Acceptance criteria

- `exec_command` and `write_stdin` exist and work on macOS/Linux.
- Behavior is good enough for interactive sessions.
- Output is bounded and truncation is explicit.

## Open questions / follow-ups

- Windows behavior: Codex CLI has platform-specific branches. We can start by falling back to non-PTY behavior on Windows.
- How to persist/clean exec sessions across turns/sessions in a long-running server.
