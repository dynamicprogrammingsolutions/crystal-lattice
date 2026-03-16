# Grok Tools

Compatibility-oriented Grok-style filesystem tools for the AI Agent Platform.

This package aims to match Grok CLI model-facing tool schemas, parameter names,
major parameter semantics, important truncation and error wording, and
LLM-visible tool result content closely while reusing shared Python filesystem
helpers underneath.

## Exposed tools

Current public tools in this package:

- `view_file`
- `create_file`
- `str_replace_editor`

The plugin repo exposes these classes through `agent_plugin.json`:

- `grok_tools.grok_view_file_tool.GrokViewFileTool`
- `grok_tools.grok_create_file_tool.GrokCreateFileTool`
- `grok_tools.grok_str_replace_editor_tool.GrokStrReplaceEditorTool`

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
    "path:./plugins/grok-tools"
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
    "path:./plugins/grok-tools"
  ],
  "agents": {
    "default": {
      "provider": "openrouter",
      "model": "x-ai/grok-4.1-fast"
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

The Grok-compatible reader entrypoint is `view_file`.

- `path` may point to either a file or a directory.
- For files, `start_line` and `end_line` are 1-based and inclusive.
- For directories, the tool returns a directory listing instead of a read-file
  error.
- File reads currently reuse the shared Gemini-style slicing/truncation engine,
  so large text reads use the same truncation banner style.

Representative `view_file` examples:

Successful file read:

```text
function greet(name) {
  return `hello ${name}`;
}
```

Directory listing:

```text
Directory listing for src:
agent/
main.ts
tools.ts
```

Representative error cases:

```text
Error: The 'path' parameter must be non-empty.
Error: start_line cannot be greater than end_line
Error: Path not in workspace: /tmp/outside.txt
```

## Compatibility contract

Parity for this package means:

- Grok-facing tool names and parameter names stay stable.
- Important parameter semantics match Grok expectations.
  That includes `view_file` serving both file reads and directory listings.
- Important validation wording stays close to the Grok tool surface.
- The LLM-visible result content stays aligned with Grok-style tool usage,
  including directory listings and major file-read success and error messages.

This package does not attempt to mirror Grok CLI's surrounding agent guidance,
confirmation flow, or other application-side orchestration.

## Configuration reference

Shared package-level config keys used by the current Grok tools:

- `working_directory`
  Default: current working directory.
  Used as the base for relative paths and relative display output.
- `allowed_paths`
  Default: `[working_directory]`.
  Paths must resolve inside one of these directories or the project temp dir.
- `project_temp_dir`
  Default: `<working_directory>/.temp`.
  Additional allowed location for reads and writes.

## Limitations

Intentionally out of scope for this tool-plugin package:

- host approval and confirmation UX
- IDE integration and diff handoff flows
- telemetry and internal service behavior from Grok CLI
- exact host-managed application prompting and orchestration

## Notes

The current package scope includes writer/editor tools in addition to the first
reader subtask because later subtasks extended the same compatibility bundle.
