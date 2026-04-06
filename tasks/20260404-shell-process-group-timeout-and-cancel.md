# Shell Process-Group Timeout And Cancel

Short description: High-priority runtime fix to ensure every shell invocation can be terminated reliably on timeout or user cancellation, including child and grandchild processes.

## Requirements checklist

- [x] Launch shell commands in an isolated process group/session so the runtime can target the full subprocess tree, not just the direct shell PID.
- [x] On timeout, terminate the entire shell process tree for `shell_command`, `shell`, and any shared shell-engine execution paths used by Codex-style tools.
- [ ] On user cancel, terminate the same process tree with the same guarantees as timeout.
- [x] Ensure orphaned descendants are not left behind when the parent shell exits or is killed.
- [x] Add extensive regression coverage for child-process, grandchild-process, quiet-process, and compound-shell-script cases.

## Why this exists

Investigation on 2026-04-04 found that our shell timeout logic kills only the direct shell process, not the whole process tree:

- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_command_tool.py:298-304`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_command_tool.py:331-340`
- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py:257-263`
- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py:316-333`

A local reproduction showed that a compound shell script such as:

```sh
apply_patch
echo after >/dev/null
```

can leave `python3 ~/.local/bin/apply_patch` orphaned with `PPID 1` after the parent shell is killed. That matches the suspicious live process seen during investigation.

## Current behavior to preserve

- Existing output capture and truncation behavior should keep working after the kill-path refactor.
- Timeout should still produce a final tool result rather than hanging forever.
- User cancel should still surface `request_cancelled` at the application/event layer once the process tree has been stopped.

## Fix scope

Focus this task on the subprocess lifecycle itself:

- process-group/session creation
- timeout kill behavior
- explicit kill helpers
- cross-tool reuse for shell execution paths

Do not fold in:

- shell `apply_patch` prompt/interception cleanup
- broader prompt/tool-selection policy
- unrelated sandbox/approval work

## Suggested implementation outline

1. Introduce a shared subprocess-launch helper that can start commands in a killable process group/session.
2. Introduce a shared terminate helper that escalates from graceful termination to hard kill when needed.
3. Thread that helper through `shell_command`, `shell`, and the shared `shell_engine`.
4. Make timeout handling call the shared terminate helper instead of `process.kill()`.
5. Expose enough subprocess state so a later cancellation task can target the same process group.

## Testing expectations

- A command that spawns a child which sleeps forever is terminated on timeout.
- A compound shell script that starts a helper and then blocks does not leak an orphan after timeout.
- A command with no stdout/stderr still times out and returns.
- Streaming and non-streaming shell paths behave consistently.
- If supported on this platform, verify grandchild termination rather than only direct child termination.
- Add at least one regression test that inspects the process state after cancellation/timeout rather than only asserting on returned events.

## Useful references

- `core/python/agent_app/tool_loop.py`
- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_command_tool.py`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_tool.py`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_array_tool.py`

## Execution plan

Added during completion on 2026-04-04.

1. Refactor the shared shell runtime to launch subprocesses in a dedicated process group/session and add a shared helper for terminating the full process tree.
2. Update shell timeout paths to use the shared termination helper instead of killing only the direct shell PID.
3. Thread the same launch/termination behavior through both shared-engine execution and the codex-tools streaming fallback paths so shell timeout behavior is consistent.
4. Add regression tests for process-tree timeout behavior, including compound shell scripts, quiet commands, and child/grandchild cleanup checks.
5. Run focused plugin/core tests to verify the new timeout behavior and confirm existing shell success cases still pass.

## Completion Notes

Added during completion on 2026-04-04.

Implemented shared process-tree launch and termination helpers in `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`. Foreground shell commands now launch in an isolated session on Unix and use shared terminate helpers that escalate from `SIGTERM` to `SIGKILL` for the whole process group instead of killing only the direct shell PID.

Threaded the new behavior through:

- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
- `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
- `plugins/codex-tools/src/codex_tools/shell_tool.py`

Timeout results remain bounded and continue to return final tool payloads with `timed_out: true` and `exit_code: None`.

Added regression coverage in:

- `plugins/codex-tools/tests/test_shell_command_tool.py`
- `plugins/codex-tools/tests/test_shell_tool.py`

The new tests cover compound shell scripts, quiet long-running commands, descendant cleanup, and both streaming and non-streaming timeout paths. This closes the timeout/orphan leak that left child helpers running after the parent shell was killed.

Not completed in this task: wiring request-level user cancel into the same subprocess termination path. That remains the follow-up in `tasks/20260404-tool-loop-cancellation-during-tool-execution.md`.