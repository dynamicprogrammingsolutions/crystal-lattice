# Shell Stdin Hardening And Noninteractive Defaults

Short description: High-priority shell-runtime fix to prevent spawned commands from inheriting the server terminal stdin and blocking forever on interactive reads.

## Requirements checklist

- [x] Default shell subprocess stdin to a noninteractive source such as `DEVNULL` unless a tool explicitly supports stdin streaming.
- [x] Ensure commands that attempt to read stdin fail fast or receive EOF instead of hanging the request forever.
- [x] Cover both shared shell-engine paths and direct `Popen` streaming implementations.
- [x] Add regression coverage for stdin-reading commands like `apply_patch` and `cat`.

## Why this exists

Investigation found an orphaned process:

- `python3 /Users/ferenci84/.local/bin/apply_patch`

Sampling showed it blocked in `sys.stdin.read()`, and the helper script reads stdin unconditionally:

- `/Users/ferenci84/.local/bin/apply_patch:471`

Our shell launch paths do not specify `stdin`, so child processes can inherit the controlling terminal:

- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py:257-263`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_command_tool.py:298-304`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_tool.py:289-297`

## Fix scope

This task is specifically about stdin safety and noninteractive defaults. It should remain separate from process-group cancellation so either fix can land independently if needed.

## Suggested implementation outline

1. Audit all shell launch sites for implicit stdin inheritance.
2. Introduce a shared default for noninteractive stdin handling.
3. Update shell tool result formatting/tests so stdin-dependent commands return a useful failure or EOF-based result.
4. Document the expectation that stdin is unavailable unless a dedicated stdin-capable tool is used.

## Testing expectations

- `apply_patch` invoked without stdin does not wait forever.
- A simple stdin consumer such as `cat` exits promptly instead of hanging.
- The noninteractive default works in both streaming and non-streaming execution paths.
- Existing shell commands that do not read stdin continue to behave normally.

## Useful references

- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_command_tool.py`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_tool.py`
- `application/python/agent_terminal_app/default_config/.plugin_cache/plugins/codex-tools@60017b8be6285556c9d71bd1a707bc9016b012ece2144c4f9fd1d03280488a81/codex_tools/shell_array_tool.py`

## Execution plan

Added during completion on 2026-04-04.

1. Add a shared subprocess stdin policy in `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py` so shell commands default to noninteractive stdin instead of inheriting the server terminal.
2. Apply that policy to every current shell launch site:
   - shared `run_shell_command(...)`
   - Codex async streaming in `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
   - Codex sync streaming in `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
   - Codex array streaming in `plugins/codex-tools/src/codex_tools/shell_tool.py`
   - legacy opt-in shell tool in `plugins/codex-tools/src/codex_tools/shell_tool_legacy.py`
3. Preserve deterministic completion for stdin readers so commands like `cat`, `python -c "input()"`, and PATH `apply_patch` receive EOF or fail promptly rather than hanging.
4. Add focused regression tests for modern and legacy shell paths covering both streaming and non-streaming behavior.
5. Run the shell-tool and shared-engine test suites to confirm stdin hardening does not regress normal command execution or the recent timeout/cancel fixes.

## Completion Notes

Added during completion on 2026-04-04.

- Implemented shared noninteractive stdin helpers in `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py` and applied them to the shared async shell engine.
- Updated Codex shell streaming launch sites in `plugins/codex-tools/src/codex_tools/shell_command_tool.py` and `plugins/codex-tools/src/codex_tools/shell_tool.py` so streaming subprocesses also default to `stdin=DEVNULL`.
- Updated the opt-in legacy shell tool in `plugins/codex-tools/src/codex_tools/shell_tool_legacy.py` for both `subprocess.run(...)` and streaming `Popen(...)`.
- Added stdin regression coverage in:
  - `plugins/tool-compat-shared/tests/test_shell_engine.py`
  - `plugins/codex-tools/tests/test_shell_command_tool.py`
  - `plugins/codex-tools/tests/test_shell_tool.py`
  - `plugins/codex-tools/tests/test_shell_tool_legacy.py`
- Verified with:
  - `pytest plugins/tool-compat-shared/tests/test_shell_engine.py plugins/codex-tools/tests/test_shell_command_tool.py plugins/codex-tools/tests/test_shell_tool.py plugins/codex-tools/tests/test_shell_tool_legacy.py -q`
  - `python -m compileall plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py plugins/codex-tools/src/codex_tools/shell_command_tool.py plugins/codex-tools/src/codex_tools/shell_tool.py plugins/codex-tools/src/codex_tools/shell_tool_legacy.py`
- Test run emitted a few existing asyncio subprocess cleanup warnings in unrelated background-process tests, but all targeted assertions passed.