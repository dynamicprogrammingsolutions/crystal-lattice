# Shell Stdin Hardening And Noninteractive Defaults

Short description: High-priority shell-runtime fix to prevent spawned commands from inheriting the server terminal stdin and blocking forever on interactive reads.

## Requirements checklist

- [ ] Default shell subprocess stdin to a noninteractive source such as `DEVNULL` unless a tool explicitly supports stdin streaming.
- [ ] Ensure commands that attempt to read stdin fail fast or receive EOF instead of hanging the request forever.
- [ ] Cover both shared shell-engine paths and direct `Popen` streaming implementations.
- [ ] Add regression coverage for stdin-reading commands like `apply_patch` and `cat`.

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