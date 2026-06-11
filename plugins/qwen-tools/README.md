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
- `list_directory`
- `grep_search`
- `glob`
- `write_file`
- `edit`
- `bash`
- `web_fetch`

Write/edit surface summary:

- `write_file(file_path, content)` writes the full file at an absolute path and overwrites existing content.
- `edit(file_path, old_string, new_string, replace_all=false)` performs literal replacement and expects exactly one match unless `replace_all` is enabled.
- `edit` also supports file creation when `old_string` is the empty string and the target file does not yet exist.

The plugin repo exposes these classes through `agent_plugin.json`:

- `qwen_tools.qwen_read_file_tool.QwenReadFileTool`
- `qwen_tools.qwen_list_directory_tool.QwenListDirectoryTool`
- `qwen_tools.qwen_grep_search_tool.QwenGrepSearchTool`
- `qwen_tools.qwen_glob_tool.QwenGlobTool`
- `qwen_tools.qwen_write_file_tool.QwenWriteFileTool`
- `qwen_tools.qwen_edit_tool.QwenEditTool`
- `qwen_tools.qwen_shell_tool.QwenShellTool`
- `qwen_tools.qwen_web_fetch_tool.QwenWebFetchTool`

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

## Writer behavior notes

The Qwen-compatible writer entrypoint is `write_file`.

- `file_path` must be absolute.
- `content` is the full file body and overwrites existing content.
- Missing parent directories are created automatically.
- `.qwenignore` patterns are honored relative to `working_directory`.
- Writes are restricted to `workspace_dirs`, `project_temp_dir`,
  `global_temp_dir`, and `user_skills_dir`.

Representative `write_file` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "write_file",
    "arguments": {
      "file_path": "/workspace/src/note.txt",
      "content": "alpha\n"
    }
  }
}
```

Representative outcomes:

```text
Successfully created and wrote to new file: /workspace/src/note.txt.
Successfully overwrote file: /workspace/src/note.txt.
File path must be absolute: src/note.txt
```

## Edit behavior notes

The Qwen-compatible edit entrypoint is `edit`.

- `edit` uses literal text matching, not regex.
- `file_path` must be absolute.
- By default, `edit` expects exactly one match.
- Set `replace_all` to `true` to replace every occurrence of `old_string`.
- If `old_string` is empty and the target file does not already exist,
  `edit` creates a new file with `new_string` as its content.

Representative `edit` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "edit",
    "arguments": {
      "file_path": "/workspace/src/note.txt",
      "old_string": "alpha",
      "new_string": "beta"
    }
  }
}
```

Representative outcomes:

```text
The file: /workspace/src/note.txt has been updated.
Failed to edit, 0 occurrences found for old_string in /workspace/src/note.txt. No edits made. The exact text in old_string was not found. Ensure you're not escaping content incorrectly and check whitespace, indentation, and context. Use read_file tool to verify.
Failed to edit. Found 2 occurrences for old_string in /workspace/src/note.txt but replace_all was not enabled.
Created new file: /workspace/src/note.txt with provided content.
```

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

## Search behavior notes

The Qwen-compatible search entrypoints are `list_directory`, `grep_search`,
and `glob`.

- `list_directory(path, ignore?, file_filtering_options?)` requires an absolute
  directory path.
- `grep_search(pattern, glob?, path?, limit?)` keeps the simpler Qwen shape and
  is case-insensitive by default.
- `glob(pattern, path?)` follows the Qwen-style path parameter and truncates
  long results based on package config.
- `list_directory` reports separate `git-ignored` and `qwen-ignored` counts
  when those filters hide entries.
- `grep_search` and `glob` both reuse the workspace/temp path allowlist used by
  the rest of the Qwen bundle.

Representative `list_directory` output:

```text
Directory listing for /workspace/src:
[DIR] nested
alpha.txt

(1 git-ignored, 1 qwen-ignored)
```

Representative `glob` output:

```text
Found 3 file(s) matching "*.ts" in the workspace directory, sorted by modification time (newest first):
---
/workspace/src/app.ts
/workspace/src/api.ts
---
[1 file truncated] ...
```

Representative `grep_search` output:

```text
Found 2 matches for pattern "todo" in the workspace directory (filter: "*.py"):
---
File: /workspace/src/main.py
L4: # TODO: tighten validation
---
```

## Shell behavior notes

The Qwen-compatible shell entrypoint is `bash`.

- `command` is the shell command to execute (required).
- `timeout` is in milliseconds (default: 120000, max: 600000).
- `description` is an optional brief description of the command purpose.
- `directory` sets the working directory for execution.
- `is_background` runs the command in background mode.
- Output is truncated by lines first (1000 lines), then by characters (25000).
- Background output includes platform-specific kill hint (`kill` or `taskkill`).

Representative `bash` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "bash",
    "arguments": {
      "command": "npm run build",
      "description": "Build the project",
      "directory": "/workspace",
      "timeout": 300000
    }
  }
}
```

Representative outcomes:

Success (no stderr):
```text
Build completed successfully.
```

Failure:
```text
Stdout: (empty)
Stderr: Build failed
Error: (none)
Exit Code: 1
Signal: (none)
```

Background (Unix):
```text
Background command started. PID: 12345 (Use kill 12345 to stop)
```

Background (Windows):
```text
Background command started. PID: 12345 (Use taskkill /F /T /PID 12345 to stop)
```

Timeout:
```text
Stdout: (empty)
Stderr: (empty)
Error: Command timed out after 2.0 seconds
Exit Code: (none)
Signal: (none)
```

Truncation:
```text
Build output line 1...
Build output line 2...

[500 lines truncated]
```

## Web Fetch behavior notes

The Qwen-compatible web fetch entrypoint is `web_fetch`.

- `url` is the URL to fetch content from (required).
- `prompt` is the prompt to run on the fetched content (required).
- Content is fetched directly using HTTP GET.
- HTML content is converted to plain text using trafilatura.
- Content is truncated to `web_fetch_max_content_chars` characters.
- The configured provider is used to summarize content based on the prompt.
- Supports both public and private/localhost URLs.
- Rate limited per-host (default: 10 requests per 60 seconds).

Representative `web_fetch` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "web_fetch",
    "arguments": {
      "url": "https://example.com/article",
      "prompt": "Summarize the main points of this article"
    }
  }
}
```

Representative outcomes:

Success:
```text
[LLM-summarized content based on the prompt]
```

Error:
```text
Error: Error during fetch for https://example.com: HTTP 404
```

Rate limited:
```text
Error: Rate limit exceeded. Please wait 30 seconds.
```

### Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `web_fetch_enabled` | `true` | Enable the web_fetch tool |
| `web_fetch_timeout_seconds` | `10` | Fetch timeout in seconds |
| `web_fetch_max_content_chars` | `100000` | Max content length in characters |
| `web_fetch_rate_limit_requests` | `10` | Max requests per window per host |
| `web_fetch_rate_limit_window` | `60` | Rate limit window in seconds |
| `web_fetch_summarization_agent_id` | `null` | Optional dedicated agent for summarization |
| `web_fetch_summarization_model` | `null` | Optional model override for summarization |

### Known Limitations

- No browser rendering for JavaScript-heavy pages
- Requires a configured provider for summarization
- No special handling for private IPs (fetches all URLs directly)

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

## Cross-Package Edit Comparison

The three compatibility packages intentionally preserve different public edit tool names and flags:

- Gemini uses `replace(..., allow_multiple=false)` and keeps the Gemini name `replace`.
- Qwen uses `edit(..., replace_all=false)` and keeps the Qwen name `edit`.
- Grok uses `str_replace_editor(..., replace_all=false)` and keeps the Grok name `str_replace_editor`.

If you are choosing between packages, the shared behavior is literal text replacement inside workspace-safe paths. The public name, argument names, path rules, and some validation wording stay vendor-specific.

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
- `shell_timeout_seconds`
  Default: `120`.
  Default timeout for shell command execution in seconds.
- `shell_max_timeout_seconds`
  Default: `600`.
  Maximum allowed timeout for shell commands.
- `shell_max_output_lines`
  Default: `1000`.
  Maximum lines to return in shell output before line truncation.
- `shell_max_output_chars`
  Default: `25000`.
  Maximum characters to return in shell output before char truncation.
- `truncate_tool_output_lines`
  Default: `500`.
  Default line window for `read_file` when `limit` is omitted.
- `truncate_tool_output_threshold`
  Default: `2500`.
  Character budget used by Qwen-style truncation.
- `list_directory` requires an absolute `path` value.
- `glob.path` and `grep_search.path` may be omitted, in which case the current
  `working_directory` is used.

Write/edit safety notes:

- `write_file` and `edit` require absolute `file_path` values.
- File access is restricted to `workspace_dirs`, `project_temp_dir`, `global_temp_dir`, and `user_skills_dir`.
- `.qwenignore` can block both reads and edits.
- `edit` is literal, not regex-based.
- `replace_all` defaults to `false`, so repeated text requires an explicit opt-in.
- Using `old_string: ""` is the package-level creation path for `edit` when the file does not already exist.

Ignore behavior:

- `.qwenignore` is read from `working_directory` when present.
- `list_directory` can report separate `git-ignored` and `qwen-ignored`
  counts.
- `glob` and `grep_search` reuse `.qwenignore` filtering and the same
  workspace/temp allowlist as the Qwen reader and edit tools.

## Compatibility and Limitations

In scope for this package:

- Qwen-style tool names and OpenAI chat-completions function schemas
- Qwen-style absolute-path validation, truncation behavior, and major success/error wording
- Qwen-style model-visible behavior for file reads, listing, globbing,
  grep-style search, full-file writes, and literal replacements

Intentionally out of scope for this tool-plugin package:

- host approval and confirmation UX
- IDE integration and diff handoff flows
- telemetry and internal service behavior from Qwen Code
- exact host-managed application prompting and orchestration

That means schema parity and tool behavior parity are the goal here. CLI confirmation screens, editor handoff, and approval workflows remain host-application concerns rather than tool-plugin concerns.

## Notes

The current package scope includes writer/editor tools in addition to the first
reader subtask because later subtasks extended the same compatibility bundle.

## License

qwen-tools is a Qwen-compatible tool plugin bundle for Crystal Lattice.
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
