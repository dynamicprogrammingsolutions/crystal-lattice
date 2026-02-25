# Model-to-tool differences (stock Codex catalog)

This file summarizes the most relevant per-model differences that affect which tool schemas appear.

Source of truth in the Codex repo: `codex-rs/core/models.json`.

## GPT-5 family (selected)

Fields that matter for tools:

- `shell_type`: selects whether the prompt exposes `shell` (argv array), `shell_command` (script string), or unified-exec tooling.
- `apply_patch_tool_type`: selects whether `apply_patch` is offered and whether it is freeform vs JSON-function.
- `supports_parallel_tool_calls`: request-level flag; affects concurrency, not tool schema.

### Stock values

- `gpt-5`
  - `shell_type`: `default` (prefers `shell`)
  - `apply_patch_tool_type`: `null` (may still be enabled via features)
  - `supports_parallel_tool_calls`: `false`

- `gpt-5.1`
  - `shell_type`: `shell_command`
  - `apply_patch_tool_type`: `freeform`
  - `supports_parallel_tool_calls`: `true`

- `gpt-5.2`
  - `shell_type`: `shell_command`
  - `apply_patch_tool_type`: `freeform`
  - `supports_parallel_tool_calls`: `true`

- `gpt-5-codex`
  - `shell_type`: `shell_command`
  - `apply_patch_tool_type`: `freeform`
  - `supports_parallel_tool_calls`: `false`

- `gpt-5.1-codex`
  - `shell_type`: `shell_command`
  - `apply_patch_tool_type`: `freeform`
  - `supports_parallel_tool_calls`: `false`

- `gpt-5.2-codex`
  - `shell_type`: `shell_command`
  - `apply_patch_tool_type`: `freeform`
  - `supports_parallel_tool_calls`: `true`

- `gpt-5.3-codex`
  - `shell_type`: `shell_command`
  - `apply_patch_tool_type`: `freeform`
  - `supports_parallel_tool_calls`: `true`
