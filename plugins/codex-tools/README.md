# codex-tools

Codex CLI-compatible tool plugin bundle. Provides shell tools and apply-patch with schemas, parameter names, output formatting, and behavioral semantics matching OpenAI's Codex CLI.

## Exposed Tools

### Unified Exec (`exec_command` + `write_stdin`)
The current upstream Codex shell surface: start a command (optionally in a
PTY), wait up to `yield_time_ms`, and either return the finished output
with its exit code or a `session_id` for a still-running process.

- **Plugin names**: `exec_command`, `write_stdin`
- **exec_command parameters**: `cmd` (string, required), `workdir` (string),
  `tty` (boolean), `yield_time_ms` (number, default 10000, clamped to
  250-30000), `max_output_tokens` (number, default 10000), `shell` (string),
  `login` (boolean, default true)
- **write_stdin parameters**: `session_id` (number, required), `chars`
  (string, default empty poll; `\x03` interrupts), `yield_time_ms` (number),
  `max_output_tokens` (number)
- **Sessions**: Long-running commands stay interactable across tool calls
  and requests; PTY-backed sessions accept stdin writes, pipe-backed ones
  reject them with the upstream error text. Idle sessions are reaped after
  `unified_exec_session_ttl_seconds` (default 900) and concurrent sessions
  are capped at `unified_exec_max_sessions` (default 8).
- **Models**: Shell-command GPT family (`gpt-5.1+`, `gpt-6.x`, codex
  variants, Sol/Terra/Luna/Astra) via `auto`; any agent via
  `shell_tool_mode: "exec_command"`
- **Platform divergence**: Upstream approval parameters
  (`sandbox_permissions`, `justification`, `prefix_rule`,
  `additional_permissions`) and `environment_id` are not served (no
  per-command sandbox, approval flow, or multi-environment concept).
- **Windows**: Not yet supported (POSIX only); tracked in
  `tasks/20261008-codex-tool-parity-refresh/030-windows-unified-exec-support.md`.

### Shell (Array-based)
Execute shell commands using array-style arguments passed directly to execvp.

- **Plugin name**: `shell`
- **Schema name**: `shell`
- **Parameters**: `command` (array, required), `workdir` (string), `timeout_ms` (number)
- **Command format**: Array of strings (e.g., `["bash", "-lc", "echo hello"]`)
- **Execution**: Direct execvp (no shell wrapper)
- **Models**: Baseline GPT-5 shell family (`gpt-5`, `gpt-5-mini`)
- **Selection**: Auto-selected when `codex-variant` tag is absent; forced via
  `shell_tool_mode: "shell"`. Historical upstream tool (removed upstream
  2026-05-13).

### Shell Command (String-based)
Execute shell scripts using the user's default shell.

- **Plugin name**: `shell_command`
- **Schema name**: `shell_command`
- **Parameters**: `command` (string, required), `workdir` (string), `timeout_ms` (number), `login` (boolean)
- **Command format**: String script (e.g., `"echo hello"`)
- **Execution**: Wrapped via shell (e.g., `bash -lc "echo hello"`)
- **Selection**: Explicit `shell_tool_mode: "shell_command"` only. Historical
  upstream tool (removed upstream 2026-08-20); under `auto` the
  shell-command family now selects unified exec.

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

### View Image
Load a local image file for model-visible vision input.

- **Plugin name**: `view_image`
- **Schema name**: `view_image`
- **Primary schema**: OpenAI Responses function tool without `output_schema`; successful results return an `input_image` content item directly
- **Chat fallback**: OpenAI chat-completions function schema plus JSON/text tool result containing the image data URL
- **Parameters**: `path` (string, required), `detail` (optional enum `high | original`, default `high`; `original` preserves the file's original resolution; enabled by default and hidden when `enable_view_image_detail_original` is false)
- **Execution**: Resolves paths against `working_directory`, enforces `allowed_paths`, validates PNG/JPEG/GIF/WebP magic bytes, and returns a data URL

### MCP Tools
Discover and execute MCP (Model Context Protocol) tools through Codex-style qualified tool names.

- **Plugin name**: `codex_mcp_tool`
- **Model-visible naming**: `mcp__server__tool`
- **Parameters**: Wrapper-specific MCP tool parameters discovered from the configured server
- **Execution**: Uses the shared `mcp-shared` runtime package for transport/session management while keeping Codex-specific naming and result formatting in the wrapper plugin
- **Config keys**: `mcp_enabled`, `mcp_fail_on_startup_error`, `mcp_reuse_runtime`, `mcp_servers`
- **UI**: One global MCP toggle plus one enable/disable toggle per configured MCP server

## Exposed Features

### CodexVariantFeature
Emits the `codex-variant` tag when the model belongs to the shell-command family.

- **Plugin name**: `codex_variant`
- **Tag emitted**: `codex-variant` (for `*-codex` models and `gpt-5.4` and
  later plain, minified, Sol, Terra, Luna, and Astra GPT models)
- **Purpose**: Enables automatic shell tool selection based on model type

### CodexSkillsFeature
Discovers explicit skill roots, renders the upstream Codex available-skills
developer block, and supports manual skill activation by mention.

- **Plugin name**: `codex_skills`
- **Prompt behavior**: Populates `CODEX_SKILLS_SECTION` for the Codex system-message template
- **Manual activation**: Detects mentions like `$skillname` in request user messages
- **Injection behavior**: Loads the matching `SKILL.md` and appends an upstream-style
  `<skill>` user message for the current request only

## Shell Tool Selection

Tools are automatically selected based on:

| Condition | Tool Enabled |
|-----------|-------------|
| `gpt-5` and `gpt-5-mini` (auto mode) | `shell` |
| `gpt-5.1`, `gpt-5.2`, `*-codex`, `gpt-5.4`, named GPT-5.6/GPT-6 variants, and later GPT families (auto mode) | `exec_command` + `write_stdin` |
| `shell_tool_mode: "shell"` | `shell` (forced) |
| `shell_tool_mode: "shell_command"` | `shell_command` (forced) |
| `shell_tool_mode: "exec_command"` | `exec_command` + `write_stdin` (forced) |

### Selection Logic

```
shell_tool_mode = "auto" (default)
├── codex-variant tag present -> exec_command + write_stdin enabled
└── codex-variant tag absent -> shell enabled

shell_tool_mode = "shell"
└── shell forced on, other shell tools forced off

shell_tool_mode = "shell_command"
└── shell_command forced on, other shell tools forced off

shell_tool_mode = "exec_command"
└── exec_command + write_stdin forced on, other shell tools forced off
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
| `shell_tool_mode` | Agent | Shell tool selection mode: `"auto"` (default), `"shell"`, `"shell_command"`, `"exec_command"` |
| `unified_exec_session_ttl_seconds` | Agent | Idle lifetime before an interactive exec session is reaped (default 900) |
| `unified_exec_max_sessions` | Agent | Cap on concurrently registered unified exec sessions (default 8) |
| `unified_exec_max_output_tokens` | Agent | Default per-call output token budget for unified exec tools (default 10000) |
| `intercept_apply_patch` | Agent/Provider | When true, shell tools intercept Codex-style `apply_patch` shell invocations and route them to the internal patch runtime |
| `enable_view_image_detail_original` | Agent | Exposes and honors `view_image.detail = "original"` by default; set to `false` to disable |
| `view_image_max_bytes` | Agent | Maximum local image size accepted by `view_image` |
| `mcp_enabled` | Agent/Provider | Enable MCP-backed tools for the active wrapper |
| `mcp_fail_on_startup_error` | Agent/Provider | Fail tool preparation if an enabled MCP server cannot be started |
| `mcp_reuse_runtime` | Agent/Provider | Reuse live MCP runtime connections across requests |
| `mcp_servers` | Agent/Provider | Map of MCP server definitions keyed by server name |
| `skills_enabled` | Agent | Enable Codex skill discovery and manual activation |
| `skills_roots` | Agent | Ordered explicit roots scanned for `SKILL.md` files |
| `skills_follow_symlinks` | Agent | Whether skill discovery follows symlinked directories |
| `skills_max_scan_depth` | Agent | Maximum discovery depth under each root |
| `skills_max_dirs_per_root` | Agent | Maximum directories scanned per root |
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
3. **Model detection**: `CodexVariantFeature` keeps `gpt-5` and `gpt-5-mini`
   on `shell`, and routes `gpt-5.1`, `gpt-5.2`, `*-codex`, `gpt-5.4`, named
   GPT-5.6/GPT-6 variants, and later GPT families to `shell_command`
4. **Workdir semantics**: Missing or empty `workdir` falls back to the effective turn cwd, and relative `workdir` values are resolved against that cwd before execution
5. **Apply patch fallback**: If `apply_patch` is disabled with `disabled_plugins`, shell tools can still route `apply_patch` heredocs internally when `intercept_apply_patch` is enabled
6. **Legacy tool**: Disabled by default, enable via `enabled_plugins`
7. **Config override**: `shell_tool_mode` forces specific tool regardless of model
8. **Skills developer block**: Uses the upstream Codex wording for the available-skills instructions section
9. **Skills activation**: Explicit mentions such as `$skillname` inject the selected `SKILL.md` into the request as a synthetic user message

## Dependencies

- `tool-compat-shared` (shared shell execution helpers)
- `mcp-shared` (shared MCP transport/runtime helpers)
- `skill-shared` (shared skill discovery and parsing helpers)
- `agent-core` (plugin framework)

## Development

```bash
pip install -e ".[dev]"
pytest tests -q
```

The Python package name is `codex_tools` and uses a `src/` layout.

Plugin metadata lives at `agent_plugin.json` in the repo root.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
