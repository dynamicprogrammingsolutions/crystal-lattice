# 010 — Shell tool: switch to inactivity timeout, default 300 s

Parent Task: `tasks/20260702-gemini-tools-upstream-parity/000-main.md`

Switch our `run_shell_command` from a hard wall-clock timeout to an **inactivity** timeout (timer resets on each stdout/stderr line), and change the default from 120 s to 300 s to match upstream `gemini-cli`. This also makes our existing timeout message (`"exceeded the timeout of X minutes without output"`) accurate instead of misleading.

## Requirements checklist

- [ ] Shared shell engine supports inactivity-based timeout as an additive option; existing wall-clock behavior preserved for other callers.
- [ ] `gemini_shell_tool` default timeout changed from 120 s to 300 s.
- [ ] `gemini_shell_tool` passes the timeout as an inactivity timeout, not a wall-clock timeout.
- [ ] Timeout message (`"exceeded the timeout of X minutes without output"`) is now accurate.
- [ ] Other vendor shell tools (codex, claude, qwen, grok, kimi) unaffected.
- [ ] Tests cover: periodic-output survival past wall-clock duration, silent-command kill at the inactivity deadline, default value, message format.

## Clarification: `timeoutMs` is NOT a tool call parameter

`timeoutMs` is the **internal variable name** in upstream's TypeScript code (`../gemini-cli/packages/core/src/tools/shell.ts:171`) — it holds the value of `config.getShellToolInactivityTimeout()` in milliseconds. It is **not** exposed to the LLM. Neither upstream nor our tool has a `timeout` parameter in the tool schema. The timeout is a **config-level setting only**, set via `tools.shell.inactivityTimeout` in `settings.json` (upstream) or `shell_timeout_seconds` in the plugin config (ours).

## References

### Upstream (`../gemini-cli`)
- `packages/core/src/tools/shell.ts:171-218, 233` — inactivity timeout implementation (timer reset on each output event)
- `packages/core/src/config/config.ts:899-900` — default 300 s
- `packages/cli/src/config/settingsSchema.ts:1244-1253` — `inactivityTimeout` setting
- `docs/tools/shell.md` — documents the inactivity timeout

### Our code
- `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py:32` — `DEFAULT_TIMEOUT_SECONDS = 120` (needs to become 300)
- `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py:77` — reads `shell_timeout_seconds` from config
- `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py:159-171` — passes `timeout_seconds` to shared engine
- `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py:303-306` — timeout message (becomes accurate once semantics match)
- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py:287-467` — `run_shell_command` async function
- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py:436-440` — the `asyncio.wait_for(..., timeout=timeout_seconds)` call that needs to become inactivity-based

## Plan

### A) Add inactivity-timeout support to the shared shell engine

In `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`, `run_shell_command`:

- Add a new parameter, e.g. `inactivity_timeout_seconds: float | None = None`, alongside the existing `timeout_seconds`.
- When `inactivity_timeout_seconds` is set, reset the deadline whenever stdout or stderr produces a line. Cleanest approach: replace the single outer `asyncio.wait_for(asyncio.gather(read_stdout(), read_stderr()), timeout=...)` with a per-read loop that uses `asyncio.wait_for` on each `process.stdout.readline()` / `process.stderr.readline()` call with the inactivity timeout, and accumulates output. On `asyncio.TimeoutError` from a readline, break and treat as timed out.
- Keep the existing `timeout_seconds` behavior intact for other callers (codex, claude, qwen, etc.) — this is an additive option, not a replacement.
- Background mode already ignores `timeout_seconds`; `inactivity_timeout_seconds` should also be ignored in background mode.

Verify the approach against upstream's `shell.ts:210-218, 233` before implementing — upstream uses a `setTimeout` that is cleared and re-set on each event, combined with an `AbortController`. The Python equivalent is the per-readline `wait_for` loop described above.

### B) Wire the gemini shell tool to use the inactivity timeout

In `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py`:

- Change `DEFAULT_TIMEOUT_SECONDS = 120` to `DEFAULT_TIMEOUT_SECONDS = 300`.
- In `execute_tool`, pass `inactivity_timeout_seconds=timeout_seconds` to `run_shell_command` instead of `timeout_seconds=timeout_seconds`.
- The existing `_format_timeout_result` message (`"exceeded the timeout of X minutes without output"`) becomes accurate once the semantics match — no message change needed.

### C) Other vendor tools

Do not change codex/claude/qwen/grok/kimi shell tools in this subtask. They can adopt `inactivity_timeout_seconds` later if desired. The shared-engine change is additive and non-breaking.

### D) Tests

- Add a test in `plugins/tool-compat-shared/tests/test_shell_engine.py` that verifies a command producing output periodically survives past the wall-clock duration of `inactivity_timeout_seconds`, but a silent command is killed at `inactivity_timeout_seconds`.
- Add/update a test in `plugins/gemini-tools/tests/` for the new 300 s default (config-level, can be a unit test on `init()`).
- Verify the timeout message format is unchanged.

## Acceptance criteria

- `gemini_shell_tool` default timeout is 300 s.
- A shell command that prints output periodically is not killed as long as output keeps arriving within the inactivity window.
- A silent shell command is killed after `inactivity_timeout_seconds` and the result's `output` field contains the upstream-matching `"exceeded the timeout of X minutes without output"` message.
- Other vendor shell tools (codex, claude, qwen, grok, kimi) are unaffected.
- Shared engine's existing `timeout_seconds` behavior is preserved for existing callers.

## Open questions

- Should the inactivity reset happen on stdout only, stderr only, or both? Upstream resets on "any event" (both). Recommend both.
- Should we also expose `inactivity_timeout_seconds` as a config key distinct from `shell_timeout_seconds`, or repurpose `shell_timeout_seconds` to mean inactivity? Recommend repurposing — `shell_timeout_seconds` already reads as a generic timeout and the gemini tool is the only caller; adding a second key is unnecessary complexity.