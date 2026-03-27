# 106 - Shell Tool Selection

Short description: Implement automatic shell tool selection based on model and config-based legacy override.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/104-codex-v2-tool.md`

## Goal

After implementing both `shell` (array) and `shell_command` (string) tools, provide a mechanism to automatically select the appropriate tool based on the model being used, while allowing users to opt for the legacy tool via configuration.

## High-Level Requirements

### Model-Based Selection

Codex CLI selects the shell tool based on `shell_type` in models.json:

| Model Pattern | `shell_type` | Tool Selected |
|---------------|--------------|---------------|
| gpt-5, gpt-5.1, gpt-5.2 | `"default"` | `shell` (array) |
| gpt-5.2-codex, gpt-5.3-codex, gpt-5.4 | `"shell_command"` | `shell_command` (string) |

The agent should:
- Detect the model being used
- Select the appropriate shell tool automatically
- Default to `shell_command` for unknown models (safe default for Codex-style usage)

### Config-Based Override

Users should be able to override the automatic selection via config:

```yaml
# In agent config
shell_tool:
  # Override automatic selection
  mode: "auto" | "shell" | "shell_command" | "legacy"
```

- `"auto"` (default): Use model-based selection
- `"shell"`: Always use array-based `shell` tool
- `"shell_command"`: Always use string-based `shell_command` tool
- `"legacy"`: Use the old `shell_tool.py` implementation (string-based, non-Codex schema)

### Legacy Tool Support

The existing `plugins/codex-tools/src/codex_tools/shell_tool.py` should remain available for users who prefer the legacy implementation. This can be selected via config or feature flag.

## Implementation Notes

- Tool selection logic should live in the application layer, not in the tool itself
- Consider using a feature plugin or agent-level configuration to expose the selected tool
- The selection should be transparent to the model - only one shell tool should be exposed per request
- Document the selection behavior and config options in user-facing docs

## Out of Scope

- Dynamic tool switching mid-session
- Per-request tool selection overrides
- Tool schema merging or aliasing

## Completion Notes

(To be filled during implementation)