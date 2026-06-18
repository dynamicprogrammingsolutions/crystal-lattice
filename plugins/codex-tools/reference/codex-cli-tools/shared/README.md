# Shared behaviors (shell-like tools)

These behaviors are shared across `shell`, `shell_command`, `exec_command`, `write_stdin`, and `apply_patch` executions.

## Truncation policy

Codex applies a per-turn truncation policy (bytes or tokens) before returning outputs to the model.

- If output is truncated, the formatted string begins with:
  - `Total output lines: <N>`
  - a blank line
  - then the truncated content (prefix + marker + suffix)

The truncation marker reports removed *bytes* or approximate *tokens*, depending on the policy.

## Structured vs freeform tool outputs

Codex can format exec outputs in two ways:

1. **Structured JSON string** (default for most exec-like tools)

   The tool output is a JSON string with keys:

   - `metadata.exit_code`
   - `metadata.duration_seconds`
   - `output` (the truncated/annotated content)

2. **Freeform/sectioned text** (used for `shell_command` and also used when the freeform `apply_patch` tool is present)

   Example shape:

   - `Exit code: <n>`
   - `Wall time: <sec> seconds`
   - optional `Total output lines: <N>`
   - `Output:`
   - then the (possibly truncated) output body

### Important nuance

If the freeform `apply_patch` tool is present in the prompt’s tool list, Codex rewrites prior shell/apply_patch outputs in the conversation history from the structured JSON string into the sectioned text format before sending them back to the model.

## Error semantics for exec-like tools

Codex treats exec-like tool execution failures as *tool call errors* so the model receives the output/error inline:

- **Exit code != 0**: the formatted output is returned as a tool error (so it appears as an error string to the model).
- **Timeout/denied** (sandbox errors): returned as a tool error, using the same output formatting (and in the timeout case, the output text is prefixed with `command timed out after ...`).
- **Rejected** (user declined approval or other rejection path): returned as a tool error, and the event stream reports a declined status.

