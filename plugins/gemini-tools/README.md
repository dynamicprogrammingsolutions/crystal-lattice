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
- `run_shell_command`
- `web_fetch`
- `google_web_search`

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
- `gemini_tools.gemini_shell_tool.GeminiShellTool`
- `gemini_tools.gemini_web_fetch_tool.GeminiWebFetchTool`
- `gemini_tools.gemini_web_search_tool.GeminiWebSearchTool`

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

## Writer behavior notes

The Gemini-compatible writer entrypoint is `write_file`.

- `file_path` may be relative to `working_directory`.
- `content` is the full file body and overwrites existing content.
- Missing parent directories are created automatically.
- `.geminiignore` patterns are honored relative to `working_directory`.
- Writes are restricted to `allowed_paths` plus `project_temp_dir`.

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

## Edit behavior notes

The Gemini-compatible edit entrypoint is `replace`.

- `replace` uses literal text matching, not regex.
- `instruction` is required and mirrors the Gemini model-facing schema.
- By default, `replace` expects exactly one match.
- Set `allow_multiple` to `true` to replace every occurrence of `old_string`.
- If `old_string` is empty and the target file does not already exist,
  `replace` creates a new file with `new_string` as its content.

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
Created new file: /workspace/src/note.txt with provided content.
```

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

## Shell behavior notes

The Gemini-compatible shell entrypoint is `run_shell_command`.

- `command` is the shell command to execute (required).
- `description` is an optional brief description of the command purpose.
- `dir_path` sets the working directory for execution.
- `is_background` runs the command in background mode (useful for dev servers).
- Timeout defaults to 120 seconds (configurable via `shell_timeout_seconds`).
- Output is truncated at 40,000 characters with 20% head / 80% tail split.
- Truncated output is saved to `project_temp_dir` with a reference path.

Representative `run_shell_command` call shape:

```json
{
  "type": "function",
  "function": {
    "name": "run_shell_command",
    "arguments": {
      "command": "npm run build",
      "description": "Build the project",
      "dir_path": "/workspace"
    }
  }
}
```

Representative outcomes:

Success:
```text
Output:
Build completed successfully.
```

Failure:
```text
Output:
Error: Build failed
Error: Command failed with exit code 1
Exit Code: 1
```

Background:
```text
Command moved to background (PID: 12345). Output hidden.
```

Timeout:
```text
Command was automatically cancelled because it exceeded the timeout of 2.0 minutes without output.
Below is the output before it was cancelled:
...
```

Truncation:
```text
Output too large. Showing first 8,000 and last 32,000 characters. For full output see: /workspace/.temp/shell_output_abc123.txt
...
```

## Web Fetch behavior notes

The Gemini-compatible web fetch entrypoint is `web_fetch`.

### Modes

The tool supports two modes controlled by configuration:

1. **Prompt mode (default)**: URLs embedded in a prompt, processed via Gemini API server-side grounding. Returns content with inline citations `[N]` and a `Sources:` footer.

2. **Direct mode**: Single URL per call, fetched directly without Gemini API. Useful when Gemini API is unavailable or for private network URLs.

### Parameters

**Prompt mode:**
- `prompt` (required): A comprehensive prompt that includes the URL(s) (up to 20) to fetch and specific instructions on how to process their content.

**Direct mode:**
- `url` (required): The URL to fetch. Must be a valid http or https URL.

### Behavior

1. **Primary path (prompt mode with Gemini API)**: Uses Gemini API's server-side URL grounding capability.
   - Returns content with inline citations `[N]` and a `Sources:` footer.
   - Requires a Gemini API key and `web_fetch_use_gemini_api=true`.

2. **Fallback path**: Local HTTP fetch + LLM summarization.
   - Triggered when:
     - `web_fetch_use_gemini_api=false` (explicitly disabled)
     - No Gemini API key available
     - Private IP URLs (localhost, 10.x, 172.16-31.x, 192.168.x)
     - Primary path fails
   - Uses the current agent for summarization, or a dedicated fallback agent if configured.
   - Settings can be overridden via `web_fetch_fallback_settings_overrides`.

3. **Rate limiting**: 10 requests per 60 seconds per hostname (configurable).

4. **GitHub URL normalization**: Automatically converts `github.com/.../blob/...` URLs to `raw.githubusercontent.com` URLs.

### Configuration

All configuration keys are flat with `web_fetch_` prefix:

| Key | Type | Default | UI | Description |
|-----|------|---------|----|-------------|
| `web_fetch_enabled` | boolean | true | Yes | Enable the web_fetch tool |
| `web_fetch_use_gemini_api` | boolean | true | Yes* | Use Gemini API for primary path |
| `web_fetch_direct_mode` | boolean | false | Yes | Use direct URL mode instead of prompt mode |
| `web_fetch_primary_model` | string | "web-fetch" | Yes** | Gemini model for primary path |
| `web_fetch_fallback_agent_id` | string | null | No | Optional dedicated agent for fallback |
| `web_fetch_fallback_settings_overrides` | object | {} | No | Settings to override for fallback (e.g., model, temperature) |
| `web_fetch_timeout_seconds` | integer | 10 | Yes | Fetch timeout in seconds |
| `web_fetch_max_content_chars` | integer | 100000 | No | Maximum content length in characters |
| `web_fetch_rate_limit_requests` | integer | 10 | No | Max requests per window per host |
| `web_fetch_rate_limit_window` | integer | 60 | No | Rate limit window in seconds |

\* Only visible when Gemini API key is available.
\** Only visible when API key available AND `web_fetch_use_gemini_api=true`.

Additional configuration:
- `gemini_api_key`: Gemini API key (or `GEMINI_API_KEY` environment variable). Required for primary path when `use_gemini_api=true`.

### Fallback Settings Overrides

The `web_fetch_fallback_settings_overrides` config allows overriding settings for the fallback path. This works similar to the compaction plugin's settings overrides:

```yaml
web_fetch_fallback_settings_overrides:
  model: "gpt-4"
  temperature: 0.3
```

When fallback is triggered:
1. If `fallback_agent_id` is set: switch to that agent, apply settings overrides
2. If `fallback_agent_id` is null: apply settings overrides to current agent

### Representative call shapes

Prompt mode:
```json
{
  "type": "function",
  "function": {
    "name": "web_fetch",
    "arguments": {
      "prompt": "Summarize the main points from https://example.com/article"
    }
  }
}
```

Direct mode (when `web_fetch_direct_mode: true`):
```json
{
  "type": "function",
  "function": {
    "name": "web_fetch",
    "arguments": {
      "url": "https://example.com/article"
    }
  }
}
```

### Representative outcomes

Primary path success:
```text
The article discusses three main topics[1] related to web development[2].

Sources:
[1] Article Title (https://example.com/article)
[2] Related Content (https://example.com/related)
```

Fallback success:
```text
[LLM-summarized content based on raw fetch]
```

Error cases:
```text
Error: The 'prompt' parameter cannot be empty and must contain URL(s) and instructions.
Error: The 'prompt' must contain at least one valid URL (starting with http:// or https://).
Error: Rate limit exceeded for host. Please wait 45 seconds before trying again.
Error: Failed to fetch https://example.com: HTTP 404
```

### Known Limitations

- No browser rendering for JavaScript-heavy pages
- No IDE integration for approval flows
- Requires Gemini API key for primary path when `use_gemini_api=true`
- Private IP URLs always use fallback (local fetch)
- Direct mode does not use Gemini API for URL processing

## Web Search behavior notes

The Gemini-compatible web search entrypoint is `google_web_search`.
Its ordinary `web_search_enabled` checkbox also contributes a compact composer
toggle with theme-aware off/on appearance. When no search backend is
configured, the same control remains visible but disabled and muted.

### Parameters

- `query` (required): The search query to find information on the web.

### Behavior

1. **Primary backend (`gemini_api`)**: Uses the Gemini API's server-side Google Search grounding via `GeminiApiProvider`.
   - Returns content with inline citation markers `[N]` inserted at **UTF-8 byte offsets** (matching Gemini CLI's `TextEncoder`/`TextDecoder` approach).
   - Appends a `Sources:` footer with `[N] Title (url)` entries.
   - Requires a Gemini API key (`gemini_api_key` config or `GEMINI_API_KEY` environment variable).

2. **Alternative backend (`tavily`)**: Uses the Tavily search API via `TavilyProvider`.
   - Returns results in the same Gemini-style wrapper (`Web search results for "query":\n\n...`).
   - Includes a `Sources:` footer built from result URLs.
   - No inline citation markers (only the Gemini API provides grounding metadata).
   - If Tavily returns an AI-generated answer, it is included before the result list.
   - Requires a Tavily API key (`tavily_api_key` config or `TAVILY_API_KEY` environment variable).

3. **Disabled by default**: The tool is not enabled unless `web_search_enabled` is set to `true`. If enabled without any configured provider, the tool returns an error.

### UTF-8 byte-offset citations

The Gemini API's `groundingSupports` use **UTF-8 byte offsets** for `startIndex` and `endIndex`, not character offsets. This matters for multi-byte text (e.g., 日本語, emoji 🎉). The tool encodes the response text to UTF-8 bytes, inserts citation markers at the byte positions, then decodes back — matching the Gemini CLI's `web-search.ts` implementation exactly.

### Configuration

All configuration keys are flat with `web_search_` prefix:

| Key | Type | Default | UI | Description |
|-----|------|---------|----|-------------|
| `web_search_enabled` | boolean | false | Yes | Enable the google_web_search tool |
| `web_search_provider` | string | "gemini_api" | Yes* | Search backend: `"gemini_api"` or `"tavily"` |
| `tavily_api_key` | string | null | No | Tavily API key (for tavily backend) |

\* Only visible when more than one provider is available.

Additional configuration:
- `gemini_api_key`: Gemini API key (or `GEMINI_API_KEY` environment variable). Required for `gemini_api` backend.

### Representative call shape

```json
{
  "type": "function",
  "function": {
    "name": "google_web_search",
    "arguments": {
      "query": "Python programming language history"
    }
  }
}
```

### Representative outcomes

Gemini API backend (with citations):
```text
Web search results for "Python programming language history":

Python was created by Guido van Rossum[1] and first released in 1991[2].

Sources:
[1] Python (https://en.wikipedia.org/wiki/Python_(programming_language))
[2] Python History (https://python.org/about/history)
```

Tavily backend (without inline citations):
```text
Web search results for "Python programming language history":

Python is a high-level programming language.
1. Python (programming language)
   Python is a high-level, general-purpose programming language.

Sources:
[1] Python (https://en.wikipedia.org/wiki/Python_(programming_language))
```

No results:
```text
No search results or information found for query: "obscure non-existent topic xyz"
```

Error:
```text
Error during web search for query "test": [Gemini API] API request failed: ...
```

### Known Limitations

- Disabled by default; must be explicitly enabled
- Requires at least one API key (Gemini or Tavily) to function
- Only the `gemini_api` backend provides inline citation markers
- No browser rendering or JavaScript execution for search results

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
  Additional allowed location for reads and writes. Also used to store full
  output from truncated shell commands.
- `shell_timeout_seconds`
  Default: `120`.
  Default timeout for shell command execution in seconds.
- `shell_max_output_chars`
  Default: `40000`.
  Maximum characters to return in shell output before truncation.
- `shell_truncation_head_ratio`
  Default: `0.2` (20% head, 80% tail).
  Ratio for head/tail split when truncating shell output.
- `list_directory`, `grep_search`, and `glob` also resolve relative paths from
  `working_directory` and restrict access to `allowed_paths` plus
  `project_temp_dir`.

Web search config keys:

- `web_search_enabled`
  Default: `false`.
  Must be set to `true` to enable the `google_web_search` tool.
- `web_search_provider`
  Default: `"gemini_api"`.
  Search backend: `"gemini_api"` (requires `gemini_api_key`) or `"tavily"`
  (requires `tavily_api_key`).
- `tavily_api_key`
  Default: none.
  Tavily API key. Also read from `TAVILY_API_KEY` environment variable.
- `gemini_api_key`
  Default: none.
  Gemini API key. Also read from `GEMINI_API_KEY` environment variable.
  Required for the `gemini_api` web search backend and the primary
  `web_fetch` path.

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
  grep-style search, full-file writes, literal replacements, and web search

Intentionally out of scope for this tool-plugin package:

- host approval and confirmation UX
- IDE integration and diff handoff flows
- telemetry and internal service behavior from Gemini CLI
- exact host-managed application prompting and orchestration

That means schema parity and tool behavior parity are the goal here. CLI confirmation screens, editor handoff, and approval workflows remain host-application concerns rather than tool-plugin concerns.

## Notes

The current package scope includes writer/editor tools in addition to the first
reader subtask because later subtasks extended the same compatibility bundle.

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
