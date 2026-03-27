# 100 - Shell Tools (All Vendors)

Short description: Add vendor-compatible shell/command execution tools to `gemini-tools`, `qwen-tools`, `grok-tools`, and `kimi-tools`, sharing subprocess execution internals from `tool-compat-shared`.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`

## Task checklist

- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md` — Core engine with asyncio
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/102-shell-engine-truncation.md` — Generic truncation
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/103-shell-engine-background.md` — Background process support
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/104-codex-v2-tool.md` — Codex V2 tool
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/105-vendor-tools.md` — Vendor wrappers

## Goal

Add one tool type (shell command execution) across all four vendor packages. Each vendor exposes its own tool name, parameter names, timeout defaults, working directory handling, and result message formatting. The shared internal package provides the common subprocess execution, streaming, timeout, and clean-environment mechanics.

## Public package outcome

1. `plugins/gemini-tools/` — `GeminiShellTool` (tool name: `run_shell_command`)
2. `plugins/qwen-tools/` — `QwenShellTool` (tool name: `bash`)
3. `plugins/grok-tools/` — `GrokShellTool` (tool name: `bash`)
4. `plugins/kimi-tools/` — `KimiShellTool` (tool name: `Shell`)

## Related tasks

### Codex parity task

**Task:** `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md`

This task's completion will satisfy the Codex parity task requirements.

## Key Design Decisions (Summary)

### Streaming/Interleaving
- **asyncio with three buffers** accumulated in real-time
- Combined (interleaved), stdout, stderr all tracked
- O(n) efficiency with list + join
- True interleaving preserved (arrival order)

### Truncation
- **Generic parametrized approach** — no vendor-specific code in shared engine
- Parameters: `limit_type` (chars/lines/tokens), `limit_value`, `head_ratio`
- Returns metadata for vendor wrappers to format
- `tiktoken` as **required dependency**

### Platform-Specific
- Shell detection: `SHELL` env → `/bin/bash` fallback (Unix); PowerShell → cmd (Windows)
- Background on Unix: Append `&`
- Background on Windows: Return early, no `&`

### Background Process (Tier 1 only)
- `is_background` param (Gemini, Qwen only)
- Skip timeout, append `&` on Unix, return early with PID
- Tier 2 (registry, streaming after return) deferred

## Source References

### Gemini
- `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/shell.ts`
- `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/services/shellExecutionService.ts`

### Qwen
- `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts`
- `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/services/shellExecutionService.ts`

### Grok
- `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts`

### Kimi
- `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/__init__.py`
- `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/environment.py`
- `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/subprocess_env.py`

### Codex CLI
- `docs/codex-tools/shell_command/schema.without_request_permissions.json`
- `docs/codex-tools/shared/README.md`

## Out of Scope

- Command allowlisting/permission checks (host-side)
- Interactive shell sessions
- Sandbox permissions (host-side security)
- Apply_patch interception (host-side routing)
- Background process registry/streaming (Tier 2, future task)

## Completion notes

(To be filled during implementation)