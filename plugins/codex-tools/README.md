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
- **Models**: Non-Codex variants (gpt-5, gpt-5.1, gpt-5.2)
- **Selection**: Auto-selected when `codex-variant` tag is absent

### Shell Command (String-based)
Execute shell scripts using the user's default shell.

- **Plugin name**: `shell_command`
- **Schema name**: `shell_command`
- **Parameters**: `command` (string, required), `workdir` (string), `timeout_ms` (number), `login` (boolean)
- **Command format**: String script (e.g., `"echo hello"`)
- **Execution**: Wrapped via shell (e.g., `bash -lc "echo hello"`)
- **Models**: Codex variants (gpt-5-codex, gpt-5.1-codex, gpt-5.2-codex, gpt-5.3-codex, gpt-5.4)
- **Selection**: Auto-selected when `codex-variant` tag is present

### Shell Legacy
Legacy shell tool with string-based command execution.

- **Plugin name**: `shell_legacy`
- **Schema name**: `shell`
- **Parameters**: `command` (string), `workdir` (string), `timeout_seconds` (number), `env` (object)
- **Status**: Disabled by default (`default_enabled = false`)
- **Enable via**: `enabled_plugins` or `force_enabled_plugins` config

### Apply Patch
Apply unified diff patches to files.

- **Plugin name**: `apply_patch`
- **Schema name**: `apply_patch`
- **Parameters**: `patch` (string, required)
- **Format**: Unified diff format

## Exposed Features

### CodexVariantFeature
Emits the `codex-variant` tag when the model name ends with `-codex`.

- **Plugin name**: `codex_variant`
- **Tag emitted**: `codex-variant` (when model ends with `-codex`)
- **Purpose**: Enables automatic shell tool selection based on model type

## Shell Tool Selection

Tools are automatically selected based on:

| Condition | Tool Enabled |
|-----------|-------------|
| Model ends with `-codex` (auto mode) | `shell_command` |
| Model does NOT end with `-codex` (auto mode) | `shell` |
| `shell_tool_mode: "shell"` | `shell` (forced) |
| `shell_tool_mode: "shell_command"` | `shell_command` (forced) |

### Selection Logic

```
shell_tool_mode = "auto" (default)
├── codex-variant tag present → shell_command enabled
└── codex-variant tag absent → shell enabled

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
| `enabled_plugins` | Agent | List of plugin IDs to enable (re-enables `default_enabled = false` plugins) |
| `disabled_plugins` | Agent/Provider/Global | List of plugin IDs to disable |
| `force_enabled_plugins` | Agent | List of plugin IDs to force-enable (overrides tag-based selection) |

### Shell Tool Config

```json
{
  "shell_working_directory": ".",
  "shell_allowed_paths": ["."],
  "shell_timeout_seconds": 60,
  "shell_max_output_lines": 2000,
  "shell_max_output_chars": 160000
}
```

## Codex-Specific Behavior Notes

1. **Two shell tool variants**: Array-based (`shell`) and string-based (`shell_command`)
2. **Automatic selection**: Based on `codex-variant` tag from model name
3. **Model detection**: `CodexVariantFeature` checks if model ends with `-codex`
4. **Legacy tool**: Disabled by default, enable via `enabled_plugins`
5. **Config override**: `shell_tool_mode` forces specific tool regardless of model

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