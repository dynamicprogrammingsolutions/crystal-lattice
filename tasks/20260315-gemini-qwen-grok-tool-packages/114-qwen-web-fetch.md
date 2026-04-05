# 114 - Qwen Web Fetch Tool

Short description: Implement `QwenWebFetchTool` in `qwen-tools` with local HTTP fetch + HTML-to-text conversion + LLM summarization. Simpler than Gemini with explicit `url` and `prompt` parameters.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/111-tool-plugin-context.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/112-web-fetch-shared.md`

## Goal

Add a Qwen CLI-compatible `web_fetch` tool to the `qwen-tools` plugin package. The tool uses local HTTP fetch with HTML-to-text conversion, followed by LLM summarization using the configured provider.

## Tool Specification

### Tool Name

`web_fetch`

### Schema

```json
{
  "type": "function",
  "function": {
    "name": "web_fetch",
    "description": "Fetches content from a specified URL and processes it using an AI model.\n- Takes a URL and a prompt as input\n- Fetches the URL content, converts HTML to markdown\n- Processes the content with the prompt using a small, fast model\n- Returns the model's response about the content\n- Use this tool when you need to retrieve and analyze web content\n\nUsage notes:\n  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool instead of this one, as it may have fewer restrictions.\n  - The URL must be a fully-formed valid URL\n  - The prompt should describe what information you want to extract from the page\n  - This tool is read-only and does not modify any files\n  - Results may be summarized if the content is very large\n  - Supports both public and private/localhost URLs using direct fetch",
    "parameters": {
      "type": "object",
      "properties": {
        "url": {
          "type": "string",
          "description": "The URL to fetch content from"
        },
        "prompt": {
          "type": "string",
          "description": "The prompt to run on the fetched content"
        }
      },
      "required": ["url", "prompt"]
    }
  }
}
```

### Parameters

- `url` (required): The URL to fetch content from
- `prompt` (required): The prompt to run on the fetched content

## Behavior

### Single Path: Local Fetch + LLM Summarization

Unlike Gemini, Qwen has only one execution path:

1. Validate URL format (must start with `http://` or `https://`)
2. Apply GitHub URL normalization using `normalize_github_url()`
3. Fetch URL content using `fetch_url()` from `web-fetch-shared`
4. Extract text using `extract_text()` from `web-fetch-shared`
5. Truncate content to `MAX_CONTENT_LENGTH = 100000` chars
6. Call LLM for summarization via context:
   ```python
   core = context.get("core")
   if core:
       summarization_prompt = f'''The user requested the following: "{user_prompt}".

I have fetched the content from {url}. Please use the following content to answer the user's request.

---
{content}
---'''
       temp_session = core.add_message(
           Session(session_id="temp", messages=[]),
           "user",
           summarization_prompt,
       )
       events = core.stream_request(temp_session, config)
       # Extract summary from events
   ```
7. Return LLM-summarized content

### No Private IP Special Handling

Qwen fetches all URLs directly, including private/localhost URLs.

### Content Limits

- `MAX_CONTENT_LENGTH = 100000` chars
- `URL_FETCH_TIMEOUT_MS = 10000` (10 seconds)

## Response Formatting

### Success

```
[LLM-summarized content]
```

With message: `"Content from <url> processed successfully."`

### Error

```
Error during fetch for <url>: <error message>
```

## Implementation File

`plugins/qwen-tools/src/qwen_tools/qwen_web_fetch_tool.py`

## Package Updates

### Update `agent_plugin.json`

```json
{
  "module": "qwen_tools",
  "subdirectory": ".",
  "entries": [
    "qwen_tools.qwen_read_file_tool.QwenReadFileTool",
    "qwen_tools.qwen_list_directory_tool.QwenListDirectoryTool",
    "qwen_tools.qwen_grep_search_tool.QwenGrepSearchTool",
    "qwen_tools.qwen_glob_tool.QwenGlobTool",
    "qwen_tools.qwen_write_file_tool.QwenWriteFileTool",
    "qwen_tools.qwen_edit_tool.QwenEditTool",
    "qwen_tools.qwen_shell_tool.QwenShellTool",
    "qwen_tools.qwen_web_fetch_tool.QwenWebFetchTool"
  ],
  "kinds": {
    ...
    "qwen_tools.qwen_web_fetch_tool.QwenWebFetchTool": "tools"
  }
}
```

### Update `__init__.py`

```python
from .qwen_web_fetch_tool import QwenWebFetchTool

__all__ = [
    ...
    "QwenWebFetchTool",
]
```

### Update `pyproject.toml`

Add dependency:
- `web-fetch-shared` (from path)

## Tests

### Schema Tests (`tests/test_qwen_web_fetch_tool.py`)

1. Tool name is `web_fetch`
2. Parameters `url` and `prompt` are both required
3. Description matches Qwen CLI

### URL Validation Tests

1. Valid http:// URL → accepted
2. Valid https:// URL → accepted
3. Invalid URL → error response
4. Empty URL → error response
5. URL without scheme → error response

### Fetch Behavior Tests

1. Mock HTTP server returning HTML → extracted text
2. Mock HTTP server returning text/plain → passthrough
3. Network error → error response
4. Timeout handling
5. GitHub URL normalization applied

### LLM Summarization Tests

1. Context with core → LLM call made
2. Context without core → raw content returned with note
3. Content too large → truncation before LLM call

### Integration Tests (`tests/test_qwen_web_fetch_tool_openrouter_integration.py`)

1. Tool works with OpenRouter provider
2. End-to-end fetch and summarize flow

## Documentation

### Update `plugins/qwen-tools/README.md`

Add section:

```markdown
## Web Fetch Tool

### Tool Name
`web_fetch`

### Parameters
- `url` (required): The URL to fetch content from
- `prompt` (required): The prompt to run on the fetched content

### Behavior

1. Fetches content from the specified URL
2. Converts HTML to plain text
3. Processes the content with the provided prompt using the configured provider
4. Returns the LLM's response

### Configuration

- `web_fetch_timeout_seconds`: Fetch timeout (default: 10)
- `web_fetch_max_content_chars`: Max content length (default: 100000)

### Known Limitations

- No IDE integration for approval flows
- No browser rendering for JavaScript-heavy pages
- Requires a configured provider for summarization
```

## Requirements Checklist

- [ ] Implement `QwenWebFetchTool` class
- [ ] URL validation
- [ ] Local fetch via `web-fetch-shared`
- [ ] HTML-to-text extraction via `web-fetch-shared`
- [ ] LLM summarization via context
- [ ] Update `agent_plugin.json`
- [ ] Update `__init__.py` exports
- [ ] Update `pyproject.toml` dependencies
- [ ] Add schema tests
- [ ] Add URL validation tests
- [ ] Add fetch behavior tests
- [ ] Add LLM summarization tests
- [ ] Add OpenRouter integration test
- [ ] Update README documentation

## Key Files

| File | Purpose |
|------|---------|
| `plugins/qwen-tools/src/qwen_tools/qwen_web_fetch_tool.py` | Tool implementation |
| `plugins/qwen-tools/agent_plugin.json` | Plugin manifest |
| `plugins/qwen-tools/src/qwen_tools/__init__.py` | Package exports |
| `plugins/qwen-tools/pyproject.toml` | Package dependencies |
| `plugins/qwen-tools/tests/test_qwen_web_fetch_tool.py` | Unit tests |
| `plugins/qwen-tools/tests/test_qwen_web_fetch_tool_openrouter_integration.py` | Integration tests |
| `plugins/qwen-tools/README.md` | Documentation |

## Source References

- Qwen web fetch implementation: `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/web-fetch.ts`

## Notes

- Simpler than Gemini - no API-specific server-side fetch
- LLM summarization uses `context["core"]` for core-level access
- No special handling for private IPs (fetches directly)
- Tool matches Qwen CLI behavior as closely as practical
