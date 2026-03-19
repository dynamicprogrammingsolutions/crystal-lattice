# 100 - Shell Tools (All Vendors)

Short description: Add vendor-compatible shell/command execution tools to `gemini-tools`, `qwen-tools`, `grok-tools`, and `kimi-tools`, sharing subprocess execution internals from `tool-compat-shared`, with Kimi's Python-native implementation as the first seed for the shared helper layer.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`

## Goal

Add one tool type (shell command execution) across all four vendor packages. Each vendor exposes its own tool name, parameter names, timeout defaults, working directory handling, and result message formatting. The shared internal package provides the common subprocess execution, streaming, timeout, and clean-environment mechanics.

## Public package outcome

1. `plugins/gemini-tools/`
- `GeminiShellTool` (tool name: `run_shell_command`)
2. `plugins/qwen-tools/`
- `QwenShellTool` (tool name: `bash`)
3. `plugins/grok-tools/`
- `GrokShellTool` (tool name: `bash`)
4. `plugins/kimi-tools/`
- `KimiShellTool` (tool name: `Shell`)

## Key source references

### Gemini

- Shell tool implementation:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/shell.ts:456` (`class ShellTool`)
- Schema/declaration helpers:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/dynamic-declaration-helpers.ts` (`getShellDeclaration`, `getCommandDescription`)
- Config/definition wiring:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/coreTools.ts:176` (`getShellDefinition`)

### Qwen

- Shell tool implementation:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts:527` (`class ShellTool`)
- Tool names:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/tool-names.ts:8`

### Grok

- Shell schema:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts:102` (`bash` tool definition)
- Agent guidance:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts` (usage patterns)

### Kimi

- Shell tool implementation:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/__init__.py` (`class Shell`)
- Bash description template:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/bash.md`
- PowerShell description template:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/powershell.md`
- Clean environment helper:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/subprocess_env.py` (`get_clean_env`)

## Compatibility findings

### Shared internals are realistic

All four vendors share the same core mechanics:

1. Spawning a subprocess with a shell command.
2. Streaming stdout and stderr capture.
3. Timeout enforcement (different defaults per vendor).
4. Working directory override (where supported).
5. Exit code interpretation and result message formatting.
6. Environment variable handling.

These should become shared helpers in `tool-compat-shared`.

### Public schemas differ meaningfully

| Aspect | Gemini | Qwen | Grok | Kimi |
|--------|--------|------|------|------|
| Tool name | `run_shell_command` | `bash` | `bash` | `Shell` |
| Command param | `command` | `command` | `command` | `command` |
| Working dir param | `workdir` | `directory` | (none) | (none — uses CWD) |
| Timeout param | `timeout` (seconds) | `timeout` (milliseconds) | (none) | `timeout` (seconds) |
| Timeout default | 120s | — | — | 60s |
| Max timeout | (configurable) | 600000ms (10 min) | — | 300s (5 min) |
| Env param | `env` (dict) | (none) | (none) | (none — clean env) |
| Description param | (none) | `description` | (none) | (none) |
| Background param | (none) | `is_background` | (none) | (none) |
| PowerShell support | (none) | (none) | (none) | Yes (auto-detects) |

### Kimi's `Shell` tool is the cleanest Python seed

Kimi's implementation uses:
- `kaos.exec(*shell_args, env=get_clean_env())` — async subprocess execution.
- `asyncio.wait_for` for timeout enforcement.
- Stream-reading callbacks for stdout/stderr.
- `get_clean_env()` for safe environment construction.
- Auto-detection of PowerShell on Windows with different description template.

This should be ported as the shared base, adapted to use stdlib `asyncio.create_subprocess_exec` (without the `kaos` dependency).

### Important parity limits

1. **Command allowlisting**: Qwen implements command allowlists and permission checks. This is host-side UX, not tool schema behavior — out of scope.
2. **Interactive shell sessions**: No vendor exposes interactive shell features in the tool plugin scope.
3. **Background process management**: Qwen's `is_background` spawns long-running processes. This is host-side — out of scope for the tool plugin.
4. **PowerShell auto-detection**: Kimi's auto-detect can be ported as a shared helper option.

## Proposed shared internals in `tool-compat-shared`

Add a new module `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`:

1. **Async subprocess execution**:
   - `run_shell_command(command, *, shell_path, workdir, timeout, env, on_stdout, on_stderr) -> exit_code`
   - Streaming stdout/stderr via line-reading callbacks.
   - Timeout via `asyncio.wait_for` with process kill on timeout.

2. **Shell detection**:
   - `detect_shell() -> (shell_path, shell_name, shell_args_func)`
   - PowerShell auto-detection on Windows.

3. **Clean environment**:
   - `get_clean_env() -> dict` — safe environment construction (port Kimi's pattern).

4. **Result formatting templates**:
   - Per-vendor success/failure/timeout message templates.
   - Common patterns: exit code reporting, timeout message.

## Response formatting requirement

Every vendor shell tool must match its CLI's LLM-visible output:

1. **Success messages**:
   - Gemini: TBD (verify from source during implementation).
   - Qwen: TBD (verify from source during implementation).
   - Grok: TBD (verify from source during implementation).
   - Kimi: `"Command executed successfully."` (confirmed from `shell/__init__.py`).

2. **Failure messages**:
   - Kimi: `"Command failed with exit code: N."` (confirmed).
   - Others: Verify exact wording from source during implementation.

3. **Timeout messages**:
   - Kimi: `"Command killed by timeout (Ns)"` (confirmed).
   - Qwen: `"Timeout: command timed out after Ns"` (verify).
   - Others: Verify during implementation.

4. **Empty command rejection**:
   - Kimi: `"Command cannot be empty."` (confirmed).
   - Others: Verify during implementation.

5. **Output content**: stdout and stderr interleaved as produced by the subprocess.

Implementation pattern: shared helper produces vendor-neutral result `{exit_code, stdout, stderr, timed_out}`; vendor wrapper applies vendor-specific message formatting.

## Behavior requirements

### Gemini (`run_shell_command`)

1. Params: `command` (required), `workdir`, `timeout`, `env`.
2. `workdir` sets working directory for command execution.
3. `env` allows environment variable overrides.
4. Verify timeout default and max from source during implementation.
5. Schema description should match Gemini CLI's shell tool description.

### Qwen (`bash`)

1. Params: `command` (required), `timeout` (milliseconds), `description`, `directory`, `is_background`.
2. `timeout` in milliseconds, max 600000 (10 min).
3. `directory` must be absolute and within workspace.
4. `description` is a brief user-facing description of the command.
5. `is_background` for long-running processes (host-side — schema only, no actual background management).
6. Command allowlist validation: out of scope (host-side UX).

### Grok (`bash`)

1. Params: `command` (required). Minimal schema.
2. No timeout, no workdir, no env params.
3. Schema description matches Grok CLI's `"Execute a bash command"`.

### Kimi (`Shell`)

1. Params: `command` (required), `timeout` (seconds, default 60, max 300).
2. Uses clean environment (no inheritance of potentially unsafe vars).
3. Auto-detects PowerShell on Windows with different description template.
4. Shell invocation: `(shell_path, "-c", command)` for bash, `(shell_path, "-command", command)` for PowerShell.
5. Streams stdout/stderr via line callbacks.
6. Timeout kills process via `asyncio.wait_for` + `process.kill()`.

## Test plan

### Schema tests

1. Assert exact tool names per vendor.
2. Assert parameter names, types, required fields, defaults.
3. Assert description text matches vendor.

### Shell execution tests (all vendors)

1. Simple command: `echo hello` → stdout contains `"hello"`, success message.
2. Non-zero exit code: `false` or `exit 1` → failure message with exit code.
3. Timeout: long-running command killed by timeout → timeout message.
4. Stderr capture: command that writes to stderr → stderr in output.
5. Empty command → rejection error.

### Vendor-specific tests

1. Gemini: `workdir` parameter sets working directory.
2. Qwen: `timeout` in milliseconds, `directory` validation, max 600000 enforcement.
3. Kimi: clean environment (e.g. `env` or `printenv` output differs from full environment), PowerShell detection helper.
4. Grok: minimal schema (no timeout/workdir/env).

### Integration tests

1. Each package loads through application plugin manager with shell tool exposed.
2. Real subprocess calls succeed.
3. OpenRouter integration tests (one per vendor package with cheap model).

## Deliverables

1. Shared shell engine in `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`.
2. Shared shell engine tests in `plugins/tool-compat-shared/tests/test_shell_engine.py`.
3. Four vendor-specific shell tool classes.
4. Package exports, manifests, and READMEs updated.
5. Tests for schema, behavior, and integration.

## Documentation follow-up

After implementation, update each vendor package README with:

1. Exposed shell tool name and parameters.
2. Vendor-specific behavior notes (timeout units, workdir handling, env handling).
3. Known limitations (no allowlist, no background management, no interactive sessions).
