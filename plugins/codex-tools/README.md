# codex-tools

Codex CLI-compatible tool plugin bundle. Provides shell tools and apply-patch with schemas, parameter names, output formatting, and behavioral semantics matching OpenAI's Codex CLI.

## Exposed Tools

### Shell (Array-based)
Execute shell commands using array-style arguments passed directly to execvp.

- **Plugin name**: `shell`
- **Schema name**: `shell`
- **Parameters**: `command` (array, required), `workdir` (string), `timeout_ms` (number)
- **Command format**: Array of strings (e.g., `["bash", "-lc", "echo hello"]`)
- **Execution**: Direct execvp (no shell wrapper)
- **Models**: Baseline GPT-5 shell family (`gpt-5`, `gpt-5-mini`)
- **Selection**: Auto-selected when `codex-variant` tag is absent

### Shell Command (String-based)
Execute shell scripts using the user's default shell.

- **Plugin name**: `shell_command`
- **Schema name**: `shell_command`
- **Parameters**: `command` (string, required), `workdir` (string), `timeout_ms` (number), `login` (boolean)
- **Command format**: String script (e.g., `"echo hello"`)
- **Execution**: Wrapped via shell (e.g., `bash -lc "echo hello"`)
- **Models**: Codex variants plus the shell-command GPT family (`gpt-5.1`, `gpt-5.2`, `gpt-5.4`, and later)
- **Selection**: Auto-selected when `codex-variant` tag is present

### Shell Legacy
Legacy shell tool with string-based command execution.

- **Plugin name**: `shell_legacy`
- **Schema name**: `shell`
- **Parameters**: `command` (string), `workdir` (string), `timeout_seconds` (number), `env` (object)
- **Status**: Disabled by default (`default_enabled = false`)
- **Enable via**: `enabled_plugins` or `force_enabled_plugins` config

### Apply Patch
Apply Codex-style `*** Begin Patch` edits to files.

- **Plugin name**: `apply_patch`
- **Schema name**: `apply_patch`
- **Primary schema**: Freeform/custom tool on provider paths that support custom tools (for example, OpenAI/OpenRouter Responses)
- **Fallback schema**: Function tool with a single `input` string on OpenAI-compatible chat-completions paths
- **Execution**: Shared internal patch runtime used by both the dedicated tool and optional shell interception

## Exposed Features

### CodexVariantFeature
Emits the `codex-variant` tag when the model belongs to the shell-command family.

- **Plugin name**: `codex_variant`
- **Tag emitted**: `codex-variant` (for `*-codex` models and `gpt-5.4` and later plain/minified GPT models)
- **Purpose**: Enables automatic shell tool selection based on model type

## Shell Tool Selection

Tools are automatically selected based on:

| Condition | Tool Enabled |
|-----------|-------------|
| `gpt-5` and `gpt-5-mini` (auto mode) | `shell` |
| `gpt-5.1`, `gpt-5.2`, `*-codex`, `gpt-5.4`, and later GPT families (auto mode) | `shell_command` |
| `shell_tool_mode: "shell"` | `shell` (forced) |
| `shell_tool_mode: "shell_command"` | `shell_command` (forced) |

### Selection Logic

```
shell_tool_mode = "auto" (default)
├── codex-variant tag present -> shell_command enabled
└── codex-variant tag absent -> shell enabled

shell_tool_mode = "shell"
└── shell forced on, shell_command forced off

shell_tool_mode = "shell_command"  
└── shell_command forced on, shell forced off
```

## Configuration

```json
{
  "plugins": ["codex-tools"],
  "agents": {
    "codex-agent": {
      "provider": "openrouter",
      "model": "openai/gpt-5.2-codex",
      "shell_tool_mode": "auto"
    },
    "standard-agent": {
      "provider": "openrouter",
      "model": "openai/gpt-5",
      "shell_tool_mode": "auto"
    },
    "legacy-agent": {
      "provider": "openrouter",
      "model": "openai/gpt-4",
      "enabled_plugins": ["shell_legacy"],
      "disabled_plugins": ["shell", "shell_command"]
    }
  }
}
```

### Config Keys

| Key | Level | Description |
|-----|-------|-------------|
| `shell_tool_mode` | Agent | Shell tool selection mode: `"auto"` (default), `"shell"`, `"shell_command"` |
| `intercept_apply_patch` | Agent/Provider | When true, shell tools intercept Codex-style `apply_patch` shell invocations and route them to the internal patch runtime |
| `enabled_plugins` | Agent | List of plugin IDs to enable (re-enables `default_enabled = false` plugins) |
| `disabled_plugins` | Agent/Provider/Global | List of plugin IDs to disable |
| `force_enabled_plugins` | Agent | List of plugin IDs to force-enable (overrides tag-based selection) |

### Shell Tool Config

```json
{
  "intercept_apply_patch": false,
  "shell_working_directory": ".",
  "shell_allowed_paths": ["."],
  "shell_timeout_seconds": 60,
  "shell_max_output_lines": 2000,
  "shell_max_output_chars": 160000
}
```

## Codex-Specific Behavior Notes

1. **Two shell tool variants**: Array-based (`shell`) and string-based (`shell_command`)
2. **Automatic selection**: Based on `codex-variant` tag from model-family detection
3. **Model detection**: `CodexVariantFeature` keeps `gpt-5` and `gpt-5-mini` on `shell`, and routes `gpt-5.1`, `gpt-5.2`, `*-codex`, `gpt-5.4`, and later GPT families to `shell_command`
4. **Workdir semantics**: Missing or empty `workdir` falls back to the effective turn cwd, and relative `workdir` values are resolved against that cwd before execution
5. **Apply patch fallback**: If `apply_patch` is disabled with `disabled_plugins`, shell tools can still route `apply_patch` heredocs internally when `intercept_apply_patch` is enabled
6. **Legacy tool**: Disabled by default, enable via `enabled_plugins`
7. **Config override**: `shell_tool_mode` forces specific tool regardless of model

## Dependencies

- `tool-compat-shared` (shared shell execution helpers)
- `agent-core` (plugin framework)

## Development

```bash
pip install -e ".[dev]"
pytest tests -q
```

The Python package name is `codex_tools` and uses a `src/` layout.

Plugin metadata lives at `agent_plugin.json` in the repo root.