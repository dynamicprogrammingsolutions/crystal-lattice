# Claude MCP Output Limits Investigation

Claude Code MCP output formatting was investigated with the deterministic dummy
output server:

```text
plugins/dummy-mcp-output-server
```

The investigation harness is:

```text
plugins/claude-tools/investigation/scripts/investigate_mcp_output.py
```

Normalized fixtures are:

```text
plugins/claude-tools/investigation/fixtures/mcp-output/success-8k.json
plugins/claude-tools/investigation/fixtures/mcp-output/success-16k.json
plugins/claude-tools/investigation/fixtures/mcp-output/success-32k.json
plugins/claude-tools/investigation/fixtures/mcp-output/success-64k.json
plugins/claude-tools/investigation/fixtures/mcp-output/success-256k.json
plugins/claude-tools/investigation/fixtures/mcp-output/error-64k.json
```

## Observed behavior

Claude Code version used:

```text
2.1.154
```

For successful MCP tool outputs:

- 8KB, 16KB, and 32KB outputs were sent back to the model without truncation.
- 64KB and 256KB outputs were replaced by a `<persisted-output>` block.
- The persisted-output block includes:
  - output size in KB
  - path to the saved full output
  - `Preview (first 2KB):`
  - a prefix-only preview
  - final `...`
  - closing `</persisted-output>`

Observed success persisted-output shape:

```text
<persisted-output>
Output too large (64.7KB). Full output saved to: <PATH>

Preview (first 2KB):
<first 2KB of JSON tool output>
...
</persisted-output>
```

For the dummy FastMCP server, Claude Code wrapped successful text tool results
with a JSON string containing a `result` key. For the filesystem MCP server,
previous fixtures showed a JSON string containing a `content` key. The important
large-output behavior is the outer persisted-output wrapper, not the inner key.

For large MCP errors:

- Claude Code does not use `<persisted-output>`.
- It keeps head and tail text.
- It inserts a middle truncation marker.
- The final content is about 10,000 characters.

Observed error truncation marker:

```text

... [55522 characters truncated] ...

```

## Implementation direction

Claude-side MCP formatting should:

- leave small successful outputs unchanged
- use a default persisted-output threshold below 64KB and above 32KB
- use a 2KB prefix preview for large successful outputs
- save the full JSON output locally when possible
- truncate large errors to about 10,000 characters with a Claude-style middle marker

This belongs in `claude-tools`, not `mcp-shared`, because it is model-facing
Claude compatibility behavior. `mcp-shared` should continue to return raw MCP
results.