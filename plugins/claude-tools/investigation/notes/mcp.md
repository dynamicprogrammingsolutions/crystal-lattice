# Claude MCP Investigation

Claude Code MCP behavior was investigated with the official filesystem MCP server:

```bash
npx -y @modelcontextprotocol/server-filesystem <workspace-dir>
```

The harness is:

```text
plugins/claude-tools/investigation/scripts/investigate_mcp.py
```

Normalized fixtures are:

```text
plugins/claude-tools/investigation/fixtures/mcp/filesystem-read-file.json
plugins/claude-tools/investigation/fixtures/mcp/filesystem-read-nested-file.json
plugins/claude-tools/investigation/fixtures/mcp/filesystem-missing-file.json
```

## Harness notes

Claude Code version used:

```text
2.1.154
```

The working MCP config shape is a Claude-style `mcpServers` JSON file passed via:

```bash
--strict-mcp-config --mcp-config <mcp.json>
```

Example config:

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "<WORKSPACE>"
      ]
    }
  }
}
```

Important: passing `--tools ""` suppresses MCP tool schemas too. For MCP investigation, do not use `--tools ""`.

The real tool-result fixtures were captured with:

```bash
--permission-mode bypassPermissions
```

Without bypass permissions, Claude still advertised MCP schemas and attempted MCP calls, but the calls were denied by local permission handling.

## Model-facing tool naming

Claude exposes MCP tools with the same qualified name shape used by Codex:

```text
mcp__<server>__<tool>
```

For the filesystem server, examples include:

```text
mcp__filesystem__read_text_file
mcp__filesystem__read_file
mcp__filesystem__list_allowed_directories
mcp__filesystem__search_files
```

This means a Claude wrapper can likely reuse the same high-level name qualification pattern as Codex, while keeping the implementation in `claude-tools`.

## Anthropic tool schema shape

Claude sends MCP tools as normal Anthropic tool definitions in the request `tools` array.

Observed schema shape:

```json
{
  "name": "mcp__filesystem__read_text_file",
  "description": "Read the complete contents of a file from the file system as text...",
  "input_schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "path": {
        "type": "string"
      },
      "head": {
        "description": "If provided, returns only the first N lines of the file",
        "type": "number"
      },
      "tail": {
        "description": "If provided, returns only the last N lines of the file",
        "type": "number"
      }
    },
    "required": ["path"]
  }
}
```

For the investigated filesystem server, Claude preserved the MCP input schema substantially as provided by the server. The `$schema` field remained present. No Codex/OpenAI Responses-specific schema wrapper was used.

## Tool-use payload shape

Claude emits normal Anthropic `tool_use` blocks.

Observed success case:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "mcp__filesystem__read_text_file",
  "input": {
    "path": "<WORKSPACE>/note.txt"
  }
}
```

Claude may use either absolute paths or relative paths depending on the prompt and model behavior:

```json
{
  "name": "mcp__filesystem__read_text_file",
  "input": {
    "path": "<WORKSPACE>/nested/facts.md"
  }
}
```

```json
{
  "name": "mcp__filesystem__read_text_file",
  "input": {
    "path": "missing.txt"
  }
}
```

The wrapper should not require absolute paths; it should forward the model arguments to the MCP server unchanged.

## Tool-result payload shape

For successful text content, Claude sends a normal Anthropic `tool_result` block whose `content` is a JSON string:

```json
{
  "type": "tool_result",
  "tool_use_id": "<TOOL_CALL_ID>",
  "content": "{\"content\":\"CLAUDE_MCP_SENTINEL first line\\nsecond line\\n\"}",
  "cache_control": {
    "type": "ephemeral"
  }
}
```

For missing-file errors, Claude sends:

```json
{
  "type": "tool_result",
  "tool_use_id": "<TOOL_CALL_ID>",
  "is_error": true,
  "content": "ENOENT: no such file or directory, open '<WORKSPACE>/missing.txt'",
  "cache_control": {
    "type": "ephemeral"
  }
}
```

Implementation implication:

- text MCP content should be converted into a JSON string shaped like `{"content": "<text>"}` for success
- MCP errors should set `is_error: true` and use the error text as the tool result content
- include Anthropic-native `cache_control: {"type": "ephemeral"}` when the framework allows provider-native tool-result payloads to carry it

## Runtime behavior

Claude starts the stdio MCP server before sending tool schemas to the model:

```text
MCP server "filesystem": Starting connection with timeout of 30000ms
MCP server "filesystem": Successfully connected (transport: stdio)
MCP server "filesystem": Connection established with capabilities: {"hasTools":true,...}
```

On tool execution:

```text
MCP server "filesystem": Calling MCP tool: read_text_file
MCP server "filesystem": Tool 'read_text_file' completed successfully
```

On exit:

```text
MCP server "filesystem": Sending SIGINT to MCP server process
MCP server "filesystem": STDIO connection closed ... (cleanly)
MCP server "filesystem": Cleared connection cache for reconnection
MCP server "filesystem": MCP server process exited cleanly
```

Our existing `mcp-shared` runtime and `MCPRegistry` already match this lifecycle direction: app-owned runtime reuse during the application lifetime, and cleanup through registry/application close.

## Implementation recommendation

Implement a Claude-specific wrapper in:

```text
plugins/claude-tools/src/claude_tools/claude_mcp_tool.py
```

Use `mcp-shared` only for:

- runtime config dataclasses
- MCP server startup and lifecycle
- raw tool discovery
- raw tool execution
- runtime reuse/cleanup via `MCPRegistry`

Keep Claude-specific behavior in `claude-tools`:

- `mcp__server__tool` name qualification
- Anthropic tool schema shape with `name`, `description`, and `input_schema`
- tool-call parsing
- success result JSON-string formatting
- error result formatting with `is_error: true`
- UI toggles for shared `mcp_*` config keys

The implementation can share conceptual structure with Codex MCP, but not Codex result formatting. Codex returns OpenAI Responses-native results, while Claude should return Anthropic-native MCP tool results matching these fixtures.