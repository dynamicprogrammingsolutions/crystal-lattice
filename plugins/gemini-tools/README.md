# Gemini Tools

Compatibility-oriented Gemini-style filesystem tools for the AI Agent Platform.

This package aims to match Gemini CLI model-facing tool schemas, parameter
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
- `replace`

The plugin repo exposes these classes through `agent_plugin.json`:

- `gemini_tools.gemini_read_file_tool.GeminiReadFileTool`
- `gemini_tools.gemini_write_file_tool.GeminiWriteFileTool`
- `gemini_tools.gemini_replace_tool.GeminiReplaceTool`

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
    "path:./plugins/gemini-tools"
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
    "path:./plugins/gemini-tools"
  ],
  "agents": {
    "default": {
      "provider": "openrouter",
      "model": "google/gemini-2.5-flash-lite"
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

The Gemini-compatible reader entrypoint is `read_file`.

- `file_path` may be relative to `working_directory`.
- `start_line` and `end_line` are 1-based and inclusive.
- If no range is provided, text reads default to a 2000-line window.
- Very long individual lines are shortened to 2000 characters.
- Truncated text reads use the Gemini-style banner beginning with:
  `IMPORTANT: The file content has been truncated.`
- `.geminiignore` patterns are honored relative to `working_directory`.
- Images, audio, video, and PDFs are detected and returned as inline-data tool
  payloads.

Representative `read_file` examples:

Successful text read:

```text
def greet(name):
    return f"hello {name}"
```

Truncated text read:

```text
IMPORTANT: The file content has been truncated.
Status: Showing lines 1-2000 of 2451 total lines.
Action: To read more of the file, you can use the 'start_line' and 'end_line' parameters in a subsequent 'read_file' call. For example, to read the next section of the file, use start_line: 2001.

--- FILE CONTENT (truncated) ---
...
```

Representative error cases:

```text
Error: The 'file_path' parameter must be non-empty.
Error: start_line cannot be greater than end_line
Error: File path '/workspace/secret.txt' is ignored by configured ignore patterns.
```

## Compatibility contract

Parity for this package means:

- Gemini-facing tool names and parameter names stay stable.
- Important parameter semantics match Gemini expectations.
  Relative `file_path`, 1-based line ranges, and `replace` semantics are part
  of that contract.
- Important truncation and validation wording stays close to Gemini CLI.
- The LLM-visible result content stays aligned with Gemini-style tool usage,
  including truncation wrappers and major read/write/edit success and error
  messages.

This package does not attempt to mirror Gemini CLI's internal service graph or
application-side orchestration.

## Configuration reference

Shared package-level config keys used by the current Gemini tools:

- `working_directory`
  Default: current working directory.
  Used as the base for relative paths and ignore-file lookup.
- `allowed_paths`
  Default: `[working_directory]`.
  Paths must resolve inside one of these directories or the project temp dir.
- `project_temp_dir`
  Default: `<working_directory>/.temp`.
  Additional allowed location for reads and writes.

Ignore behavior:

- `.geminiignore` is read from `working_directory` when present.

## Limitations

Intentionally out of scope for this tool-plugin package:

- host approval and confirmation UX
- IDE integration and diff handoff flows
- telemetry and internal service behavior from Gemini CLI
- exact host-managed application prompting and orchestration

## Notes

The current package scope includes writer/editor tools in addition to the first
reader subtask because later subtasks extended the same compatibility bundle.
