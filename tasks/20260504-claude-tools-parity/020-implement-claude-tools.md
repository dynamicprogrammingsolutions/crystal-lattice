# Implement Claude Tools

Create a `claude-tools` plugin package that reproduces Claude Code's standard tool schemas and model-facing result formatting using the shared tool libraries.

## Requirements checklist

- [x] Add `plugins/claude-tools` with package metadata, `agent_plugin.json`, source package, README, and tests.
- [ ] Implement `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, and `WebSearch` with Claude-compatible names and schemas.
- [ ] Author Claude tools in Anthropic-native schema/call/result format, not primarily in OpenAI Chat Completions function format.
- [ ] Add tool interop accessors/adapters so Anthropic-native Claude tools can run through OpenAI Chat Completions-style providers.
- [ ] Reuse `tool-compat-shared` and `web-fetch-shared` for filesystem, search, shell, and web functionality.
- [ ] Add Claude-specific formatting helpers to shared packages only when they are genuinely reusable and covered by tests.
- [ ] Match observed success, error, and truncation result formatting from the investigation fixtures.

## Task checklist

- [x] Create the `claude-tools` package scaffold and investigation fixture layout.
- [x] Implement the first Claude `Read` slice with Anthropic-native schema/call/result handling.
- [x] Add narrow tool-result interop so Anthropic-native Claude `Read` can run through OpenAI-compatible providers.
- [ ] Implement the remaining Claude standard tools: `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, and `WebSearch`.
- [ ] Expand fixture parity and tests from the `Read` slice to the remaining tools.
- [ ] Revisit shared interop/formatting cleanup once the full Claude tool surface is implemented.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

Depends On: tasks/20260504-claude-tools-parity/010-investigate-claude-code-behavior.md

## Existing Vendor Patterns

Use existing packages as templates:

- `plugins/gemini-tools`
- `plugins/qwen-tools`
- `plugins/kimi-tools`
- `plugins/grok-tools`

Shared libraries:

- `plugins/tool-compat-shared`
- `plugins/web-fetch-shared`

Existing shared code includes:

- `tool_compat_shared.reader_engine`
- `tool_compat_shared.editor_engine`
- `tool_compat_shared.search_engine`
- `tool_compat_shared.shell_engine`
- `tool_compat_shared.web_search_engine`
- `web_fetch_shared.web_fetch_engine`

The `claude-tools` package should follow the same plugin package structure:

```text
plugins/claude-tools/
  agent_plugin.json
  pyproject.toml
  README.md
  src/claude_tools/
    __init__.py
    claude_read_tool.py
    claude_write_tool.py
    claude_edit_tool.py
    claude_bash_tool.py
    claude_glob_tool.py
    claude_grep_tool.py
    claude_web_fetch_tool.py
    claude_web_search_tool.py
  tests/
```

Expected `agent_plugin.json` entries:

```json
{
  "module": "claude_tools",
  "subdirectory": ".",
  "entries": [
    "claude_tools.claude_read_tool.ClaudeReadTool",
    "claude_tools.claude_write_tool.ClaudeWriteTool",
    "claude_tools.claude_edit_tool.ClaudeEditTool",
    "claude_tools.claude_bash_tool.ClaudeBashTool",
    "claude_tools.claude_glob_tool.ClaudeGlobTool",
    "claude_tools.claude_grep_tool.ClaudeGrepTool",
    "claude_tools.claude_web_fetch_tool.ClaudeWebFetchTool",
    "claude_tools.claude_web_search_tool.ClaudeWebSearchTool"
  ],
  "kinds": {
    "claude_tools.claude_read_tool.ClaudeReadTool": "tools",
    "claude_tools.claude_write_tool.ClaudeWriteTool": "tools",
    "claude_tools.claude_edit_tool.ClaudeEditTool": "tools",
    "claude_tools.claude_bash_tool.ClaudeBashTool": "tools",
    "claude_tools.claude_glob_tool.ClaudeGlobTool": "tools",
    "claude_tools.claude_grep_tool.ClaudeGrepTool": "tools",
    "claude_tools.claude_web_fetch_tool.ClaudeWebFetchTool": "tools",
    "claude_tools.claude_web_search_tool.ClaudeWebSearchTool": "tools"
  }
}
```

## Native Anthropic Tool Contract

Claude tools should be implemented around the Anthropic-native Claude Code contract captured by proxy logs.

Tool schemas should be authored in this shape:

```json
{
  "name": "Read",
  "description": "...",
  "input_schema": {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": false
  }
}
```

Tool calls should be treated canonically as Anthropic `tool_use` blocks:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "Read",
  "input": {}
}
```

Tool results should be represented as Anthropic `tool_result` blocks:

```json
{
  "type": "tool_result",
  "tool_use_id": "<TOOL_CALL_ID>",
  "content": "...",
  "is_error": true,
  "cache_control": {
    "type": "ephemeral"
  }
}
```

OpenAI Chat Completions compatibility should come from adapters, similar in spirit to the Codex tools' use of the tool interop system. Add or extend tool interop pieces as needed:

- Anthropic schema accessor.
- Anthropic tool-call accessor.
- Anthropic schema to OpenAI Chat Completions function schema adapter.
- OpenAI Chat Completions function call to Anthropic `tool_use` adapter.
- Any result/message adapter required so OpenAI-compatible providers can carry Anthropic-native tool results through the existing tool loop.

Tests must assert both:

- Native Anthropic schema/call/result parity against `plugins/claude-tools/investigation/fixtures/*`.
- OpenAI Chat Completions adapter output/input compatibility.

## Confirmed `Read` Behavior To Match

Tool name: `Read`

Parameters:

- `file_path`: required string, absolute path to file.
- `offset`: optional integer, line number to start reading from, minimum `0`.
- `limit`: optional integer, number of lines to read, exclusive minimum `0`.
- `pages`: optional string, PDF page range.

Successful text result sent back to model:

```text
1\tfirst line
2\tsecond line
```

No `is_error` was present on successful Anthropic wire payloads.

## Testing Expectations

Add focused unit tests for each tool:

- schema exactly matches normalized fixtures from investigation
- execution uses allowed paths and working directory config
- formatting matches Claude Code observed output
- display format remains useful for terminal/UI rendering

Add integration tests similar to existing vendor packages:

- local tool execution through `AgentApplication`
- gated OpenRouter/Ollama tests if appropriate

## Execution plan

Added during completion after user approval.

First implementation slice: Claude `Read` parity only. Other tools remain blocked on their investigation fixtures.

- [x] Add narrow Anthropic tool-result bridge support:
  - introduce an Anthropic Messages provider-native result format constant
  - add Anthropic result text extraction
  - add Anthropic result to OpenAI Chat Completions content conversion
  - keep the bridge small so `tasks/20260508-tool-result-interop-accessors-adapters.md` can replace it cleanly
- [x] Add Claude package-local tool schema/call interop:
  - Anthropic `{"name", "description", "input_schema"}` schema accessor
  - Anthropic schema to OpenAI Chat Completions schema adapter
  - Anthropic `tool_use` call accessor for future native Anthropic compatibility
  - OpenAI Chat Completions function call to Anthropic `tool_use` adapter
- [x] Implement `ClaudeReadTool`:
  - expose the observed Claude Code `Read` schema
  - return Anthropic-native `toolResult` envelopes as source of truth
  - support text, image, PDF status/page rendering, notebook, empty-file, and key error cases from fixtures
  - provide plain text fallback and display metadata for current UI/client compatibility
- [x] Register only `ClaudeReadTool` in `plugins/claude-tools/agent_plugin.json` for this slice.
- [x] Add focused unit tests for schema, text formatting, native result shape, OpenAI Chat conversion, image/notebook/PDF result shapes.
- [x] Add integration tests:
  - OpenRouter with `anthropic/claude-haiku-4.5` (OpenRouter catalog slug for Claude Haiku 4.5; override with `OPENROUTER_MODEL_CLAUDE_READ`)
  - reference OpenAI-compatible provider against Ollama with `glm-5:cloud`
- [x] Run focused unit tests and syntax checks.

## Progress Notes

Added during completion.

Implemented the first task-020 slice for Claude `Read` only:

- Added `ClaudeReadTool` in `plugins/claude-tools/src/claude_tools/claude_read_tool.py`.
- Registered `ClaudeReadTool` in `plugins/claude-tools/agent_plugin.json`.
- Added package-local Anthropic tool schema/call interop in `plugins/claude-tools/src/claude_tools/interop.py`.
- Added a narrow temporary Anthropic Messages result bridge in `core/python/agent_core/tool_result_payloads.py`.
- Exported `FORMAT_ANTHROPIC_MESSAGES` from `agent_core`.
- Added unit tests in `plugins/claude-tools/tests/test_claude_read_tool.py`.
- Added requested integration tests:
  - `plugins/claude-tools/tests/test_claude_read_tool_openrouter_integration.py`
  - `plugins/claude-tools/tests/test_claude_read_tool_ollama_integration.py`

The OpenRouter test uses `anthropic/claude-haiku-4.5`, which is the slug currently exposed by OpenRouter's live `/models` catalog for Claude Haiku 4.5. The originally requested `anthropic/claude-4.5-haiku` slug produced an empty OpenRouter provider response because it is not in the catalog. The test remains overrideable with `OPENROUTER_MODEL_CLAUDE_READ`.

Verification run during completion:

```bash
python -m py_compile core/python/agent_core/tool_result_payloads.py core/python/agent_core/__init__.py plugins/claude-tools/src/claude_tools/*.py plugins/claude-tools/tests/test_claude_read_tool.py plugins/claude-tools/tests/test_claude_read_tool_openrouter_integration.py plugins/claude-tools/tests/test_claude_read_tool_ollama_integration.py
ruff check core/python/agent_core/tool_result_payloads.py core/python/agent_core/__init__.py plugins/claude-tools/src/claude_tools plugins/claude-tools/tests
pytest plugins/claude-tools/tests/test_claude_read_tool.py plugins/claude-tools/tests/test_claude_read_tool_openrouter_integration.py plugins/claude-tools/tests/test_claude_read_tool_ollama_integration.py -q
```

Focused Claude tests and lint passed: `10 passed`; `ruff` reported `All checks passed`.

Additional adjacent regression command:

```bash
pytest core/python/tests/test_core_execute_tool_calls.py core/python/tests/test_tool_structured_output.py plugins/openrouter/tests/test_openrouter_provider_multipart_conversion_unit.py plugins/reference-openai-compatible-provider/tests/test_provider_multipart_conversion_unit.py -q
```

Result: `17 passed, 1 failed`. The failure is `core/python/tests/test_tool_structured_output.py::test_iter_tool_messages_preserves_structured_tool_output_content`, which expects tool messages to expose `multipartContent`. Current core emits `tool_output_content` metadata and `toolResult`, but does not add top-level `multipartContent` in `iter_tool_messages()`. This appears to be outside the Claude `Read` slice and overlaps the cleanup direction in `tasks/20260508-tool-result-interop-accessors-adapters.md`.
