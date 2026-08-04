# Dummy MCP Output Server

Local MCP server for investigating and testing large MCP tool outputs.

The server is intentionally deterministic. It exposes tools that return large
text payloads, large error payloads, and multi-block text payloads with stable
sentinel markers so clients can inspect truncation behavior.

## Run

```bash
python -m dummy_mcp_output_server --transport stdio
```

For manual HTTP testing:

```bash
python -m dummy_mcp_output_server --transport streamable-http --port 8775
```

## Tools

- `large_text_output(size_chars, line_length)`
- `large_error_output(size_chars, line_length)`
- `multi_block_output(block_count, block_size)`

Text payloads include markers such as:

```text
BEGIN_SENTINEL
MIDDLE_SENTINEL
END_SENTINEL
```