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
- `bash`

Search/list note:

- Grok-compatible unified `search` is intentionally deferred. This package does
  not expose Gemini/Qwen-style `list_directory`, `grep_search`, or `glob`
  wrappers because Grok's search surface is structurally different and will be
  handled in a later dedicated task.

Write/edit surface summary:

- `create_file(path, content)` is creation-only and fails if the target already exists.
- `str_replace_editor(path, old_str, new_str, replace_all=false)` performs literal replacement and expects exactly one match unless `replace_all` is enabled.
- Grok keeps the shortest write surface of the three packages: new-file creation plus targeted replacement.

The plugin repo exposes these classes through `agent_plugin.json`:

- `grok_tools.grok_view_file_tool.GrokViewFileTool`
- `grok_tools.grok_create_file_tool.GrokCreateFileTool`
- `grok_tools.grok_str_replace_editor_tool.GrokStrReplaceEditorTool`
- `grok_tools.grok_shell_tool.GrokShellTool`

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

## Writer behavior notes

The Grok-compatible writer entrypoint is `create_file`.

- `path` may be relative to `working_directory`.
- `create_file` is creation-only and fails if the target already exists.
- Missing parent directories are created automatically.
- Writes are restricted to `allowed_paths` plus `project_temp_dir`.

Representative `create_file` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "create_file",
    "arguments": {
      "path": "src/note.txt",
      "content": "alpha\n"
    }
  }
}
```

Representative outcomes:

```text
Created new file: /workspace/src/note.txt
File already exists, cannot create: /workspace/src/note.txt
```

## Edit behavior notes

The Grok-compatible edit entrypoint is `str_replace_editor`.

- `str_replace_editor` uses literal text matching, not regex.
- `path` may be relative to `working_directory`.
- By default, `str_replace_editor` expects exactly one match.
- Set `replace_all` to `true` to replace every occurrence of `old_str`.
- Unlike Gemini and Qwen, this edit tool does not create files when the target
  is missing.

Representative `str_replace_editor` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "str_replace_editor",
    "arguments": {
      "path": "src/note.txt",
      "old_str": "alpha",
      "new_str": "beta"
    }
  }
}
```

Representative outcomes:

```text
Updated file: /workspace/src/note.txt
Found 2 matches for old_str in /workspace/src/note.txt. Set replace_all to true to replace every occurrence.
File not found: /workspace/src/note.txt
```

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

## Shell behavior notes

The Grok-compatible shell entrypoint is `bash`.

- `command` is the shell command to execute (required).
- Grok has a **minimal schema** - no timeout, no working directory, no background mode.
- Output is returned raw without special formatting.
- No truncation is applied.

Representative `bash` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "bash",
    "arguments": {
      "command": "echo hello"
    }
  }
}
```

Representative outcomes:

Success:
```text
hello
```

Failure:
```text
command not found: invalid_cmd
```

Note: Unlike Gemini and Qwen, Grok does not include timeout, background mode,
or output truncation features in its shell tool.

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

## Cross-Package Edit Comparison

The three compatibility packages intentionally preserve different public edit tool names and flags:

- Gemini uses `replace(..., allow_multiple=false)` and keeps the Gemini name `replace`.
- Qwen uses `edit(..., replace_all=false)` and keeps the Qwen name `edit`.
- Grok uses `str_replace_editor(..., replace_all=false)` and keeps the Grok name `str_replace_editor`.

If you are choosing between packages, the shared behavior is literal text replacement inside workspace-safe paths. The public name, argument names, path rules, and some validation wording stay vendor-specific.

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

Write/edit safety notes:

- `create_file` and `str_replace_editor` accept relative `path` values, resolved from `working_directory`.
- Writes and edits are restricted to `allowed_paths` plus `project_temp_dir`.
- `create_file` is intentionally creation-only and does not overwrite existing files.
- `str_replace_editor` is literal, not regex-based.
- `replace_all` defaults to `false`, so repeated text requires an explicit opt-in.

## Compatibility and Limitations

In scope for this package:

- Grok-style tool names and OpenAI chat-completions function schemas
- Grok-style path handling, directory listing support, and major success/error wording
- Grok-style model-visible behavior for view, create, and literal replacement operations

Intentionally out of scope for this tool-plugin package:

- host approval and confirmation UX
- IDE integration and diff handoff flows
- telemetry and internal service behavior from Grok CLI
- exact host-managed application prompting and orchestration
- the future Grok unified `search` tool discussed in the Gemini/Qwen search
  subtask

That means schema parity and tool behavior parity are the goal here. CLI confirmation screens, editor handoff, and approval workflows remain host-application concerns rather than tool-plugin concerns.

## Notes

The current package scope includes writer/editor tools in addition to the first
reader subtask because later subtasks extended the same compatibility bundle.
