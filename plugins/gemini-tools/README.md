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
- `list_directory`
- `grep_search`
- `glob`
- `write_file`
- `replace`

Write/edit surface summary:

- `write_file(file_path, content)` writes the full file and overwrites existing content.
- `replace(file_path, instruction, old_string, new_string, allow_multiple=false)` performs literal replacement and expects exactly one match unless `allow_multiple` is enabled.

The plugin repo exposes these classes through `agent_plugin.json`:

- `gemini_tools.gemini_read_file_tool.GeminiReadFileTool`
- `gemini_tools.gemini_list_directory_tool.GeminiListDirectoryTool`
- `gemini_tools.gemini_grep_search_tool.GeminiGrepSearchTool`
- `gemini_tools.gemini_glob_tool.GeminiGlobTool`
- `gemini_tools.gemini_write_file_tool.GeminiWriteFileTool`
- `gemini_tools.gemini_replace_tool.GeminiReplaceTool`

## Write and Edit Examples

Representative `write_file` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "write_file",
    "arguments": {
      "file_path": "src/note.txt",
      "content": "alpha\n"
    }
  }
}
```

Representative outcomes:

```text
Successfully created and wrote to new file: /workspace/src/note.txt.
Successfully overwrote file: /workspace/src/note.txt.
```

Representative `replace` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "replace",
    "arguments": {
      "file_path": "src/note.txt",
      "instruction": "Rename alpha to beta",
      "old_string": "alpha",
      "new_string": "beta"
    }
  }
}
```

Representative outcomes:

```text
Successfully modified file: /workspace/src/note.txt (1 replacements).
Failed to edit, 0 occurrences found for old_string in /workspace/src/note.txt. Ensure you're not escaping content incorrectly and check whitespace, indentation, and context. Use read_file tool to verify.
Failed to edit. Expected 1 occurrence but found 2 for old_string in file: /workspace/src/note.txt. If you intended to replace multiple occurrences, set 'allow_multiple' to true.
```

Special case:

- If `old_string` is empty and the target file does not already exist, `replace` creates a new file and returns `Created new file: ... with provided content.`

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

## Search behavior notes

The Gemini-compatible search entrypoints are `list_directory`, `grep_search`,
and `glob`.

- `list_directory(dir_path, ignore?, file_filtering_options?)` lists only the
  direct children of a directory.
- `grep_search(pattern, dir_path?, include_pattern?, exclude_pattern?,
  names_only?, max_matches_per_file?, total_max_matches?)` keeps the fuller
  Gemini search shape, including names-only mode and per-file/total match caps.
- `glob(pattern, dir_path?, case_sensitive?, respect_git_ignore?,
  respect_gemini_ignore?)` returns absolute paths sorted by modification time
  with recent files first.
- Relative search paths are resolved from `working_directory`.
- `.geminiignore` and optional `.gitignore` filtering are applied in the same
  compatibility layer used by the reader and edit tools.

Representative `list_directory` output:

```text
Directory listing for /workspace/src:
[DIR] nested
alpha.py (128 bytes)

(1 ignored)
```

Representative `glob` output:

```text
Found 2 file(s) matching "*.py" within /workspace/src, sorted by modification time (newest first):
/workspace/src/main.py
/workspace/src/util.py
```

Representative `grep_search` output:

```text
Found 2 matches for pattern "TODO" in path "src":
File: /workspace/src/main.py
L12: # TODO: tighten validation
---
File: /workspace/src/util.py
L7: # TODO: remove debug path
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

## Cross-Package Edit Comparison

The three compatibility packages intentionally preserve different public edit tool names and flags:

- Gemini uses `replace(..., allow_multiple=false)` and keeps the Gemini name `replace`.
- Qwen uses `edit(..., replace_all=false)` and keeps the Qwen name `edit`.
- Grok uses `str_replace_editor(..., replace_all=false)` and keeps the Grok name `str_replace_editor`.

If you are choosing between packages, the shared behavior is literal text replacement inside workspace-safe paths. The public name, argument names, path rules, and some validation wording stay vendor-specific.

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
- `list_directory`, `grep_search`, and `glob` also resolve relative paths from
  `working_directory` and restrict access to `allowed_paths` plus
  `project_temp_dir`.

Write/edit safety notes:

- `write_file` and `replace` both allow relative `file_path` values, resolved from `working_directory`.
- Writes and edits are restricted to `allowed_paths` plus `project_temp_dir`.
- `.geminiignore` can block both reads and edits.
- `replace` is literal, not regex-based.
- `allow_multiple` defaults to `false`, so repeated text requires an explicit opt-in.

Ignore behavior:

- `.geminiignore` is read from `working_directory` when present.
- `list_directory` can also report ignored child counts.
- `glob` and `grep_search` both reuse the same `.geminiignore` filtering and
  accept optional `.gitignore` participation flags in the Gemini-compatible
  schema.

## Compatibility and Limitations

In scope for this package:

- Gemini-style tool names and OpenAI chat-completions function schemas
- Gemini-style path handling, validation, and major success/error wording
- Gemini-style model-visible behavior for file reads, listing, globbing,
  grep-style search, full-file writes, and literal replacements

Intentionally out of scope for this tool-plugin package:

- host approval and confirmation UX
- IDE integration and diff handoff flows
- telemetry and internal service behavior from Gemini CLI
- exact host-managed application prompting and orchestration

That means schema parity and tool behavior parity are the goal here. CLI confirmation screens, editor handoff, and approval workflows remain host-application concerns rather than tool-plugin concerns.

## Notes

The current package scope includes writer/editor tools in addition to the first
reader subtask because later subtasks extended the same compatibility bundle.
