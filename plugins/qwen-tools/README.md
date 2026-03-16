# Qwen Tools

Compatibility-oriented Qwen-style filesystem tools for the AI Agent Platform.

This package aims to match Qwen Code model-facing tool schemas, parameter
names, major parameter semantics, important truncation and error wording, and
LLM-visible tool result content closely while reusing shared Python filesystem
helpers underneath.

Structured media payloads are preserved in raw tool results. In the current
text-first tool message pipeline, those payloads are still rendered to the
model as text/JSON.

## Exposed tools

Current public tools in this package:

- `read_file`
- `write_file`
- `edit`

The plugin repo exposes these classes through `agent_plugin.json`:

- `qwen_tools.qwen_read_file_tool.QwenReadFileTool`
- `qwen_tools.qwen_write_file_tool.QwenWriteFileTool`
- `qwen_tools.qwen_edit_tool.QwenEditTool`

## Quickstart

Minimal global plugin loading with the application plugin manager:

```json
{
  "plugin_cache_dir": "~/.crystal/plugins",
  "plugin_policy": {
    "base_dir": ".",
    "install_deps": true
  },
  "plugins": [
    "path:./plugins/qwen-tools"
  ]
}
```

Combine it with a provider bundle such as OpenRouter:

```json
{
  "plugin_cache_dir": "~/.crystal/plugins",
  "plugin_policy": {
    "base_dir": ".",
    "install_deps": true
  },
  "plugins": [
    "path:./plugins/openrouter",
    "path:./plugins/qwen-tools"
  ],
  "agents": {
    "default": {
      "provider": "openrouter",
      "model": "qwen/qwen3.5-flash-02-23"
    }
  }
}
```

`install_deps` matters for this package because it depends on the sibling
shared package under `plugins/tool-compat-shared`.

For now, the simplest setup is to load this package in the global `plugins`
list. Once subtask `040-agent-and-provider-plugin-package-config` is completed,
agent-level and provider-level `plugins` placement will also be documented and
available for this package family.

## Reader behavior notes

The Qwen-compatible reader entrypoint is `read_file`.

- `absolute_path` must be absolute.
- `offset` is 0-based.
- `limit` is a line count.
- Output lines are right-trimmed to match Qwen-style text rendering.
- Truncation is controlled by package config and uses the Qwen-style wrapper
  beginning with `Showing lines X-Y of Z total lines.`
- `.qwenignore` patterns are honored relative to `working_directory`.
- Allowed read/write roots include workspace directories, `project_temp_dir`,
  `global_temp_dir`, and `user_skills_dir`.

Representative `read_file` examples:

Successful text read:

```text
line one
line two
line three
```

Truncated text read:

```text
Showing lines 1-500 of 932 total lines.

---

line one
line two
...
```

Representative error cases:

```text
Error: The 'absolute_path' parameter must be non-empty.
Error: File path must be absolute, but was relative: src/app.py. You must provide an absolute path.
Error: File path '/workspace/secret.txt' is ignored by .qwenignore pattern(s).
```

## Compatibility contract

Parity for this package means:

- Qwen-facing tool names and parameter names stay stable.
- Important parameter semantics match Qwen expectations.
  Absolute paths, 0-based `offset`, `limit` as line count, and `edit`
  replacement behavior are part of that contract.
- Important truncation and validation wording stays close to Qwen Code.
- The LLM-visible result content stays aligned with Qwen-style tool usage,
  including truncation wrappers and major read/write/edit success and error
  messages.

This package does not attempt to mirror Qwen Code's internal service graph or
application-side orchestration.

## Configuration reference

Shared package-level config keys used by the current Qwen tools:

- `working_directory`
  Default: current working directory.
  Used as the display root for relative output paths and ignore-file lookup.
- `workspace_dirs`
  Default: falls back to `allowed_paths`, then `[working_directory]`.
  Primary allowlist for file access.
- `allowed_paths`
  Optional compatibility alias for `workspace_dirs`.
- `project_temp_dir`
  Default: `<working_directory>/.temp`.
  Additional allowed location for reads and writes.
- `global_temp_dir`
  Default: system temp directory.
  Additional allowed location for reads and writes.
- `user_skills_dir`
  Default: `~/.qwen/skills`.
  Additional allowed location for reads and writes.
- `truncate_tool_output_lines`
  Default: `500`.
  Default line window for `read_file` when `limit` is omitted.
- `truncate_tool_output_threshold`
  Default: `2500`.
  Character budget used by Qwen-style truncation.

Ignore behavior:

- `.qwenignore` is read from `working_directory` when present.

## Limitations

Intentionally out of scope for this tool-plugin package:

- host approval and confirmation UX
- IDE integration and diff handoff flows
- telemetry and internal service behavior from Qwen Code
- exact host-managed application prompting and orchestration

## Notes

The current package scope includes writer/editor tools in addition to the first
reader subtask because later subtasks extended the same compatibility bundle.
