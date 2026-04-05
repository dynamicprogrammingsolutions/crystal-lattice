# 115 - Kimi FetchURL Tool

Short description: Implement `KimiFetchURLTool` in `kimi-tools` with Moonshot fetch service (primary, optional) and local HTTP fetch + trafilatura extraction (fallback). Returns raw extracted text without LLM summarization.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/111-tool-plugin-context.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/112-web-fetch-shared.md`

## Goal

Add a Kimi CLI-compatible `FetchURL` tool to the `kimi-tools` plugin package. The tool uses the Moonshot fetch service when configured, falling back to local HTTP fetch with trafilatura extraction. Unlike Gemini and Qwen, Kimi returns raw extracted text without LLM summarization.

## Tool Specification

### Tool Name

`FetchURL` (PascalCase, matching Kimi CLI)

### Schema

```json
{
  "type": "function",
  "function": {
    "name": "FetchURL",
    "description": "Fetch a web page from a URL and extract main text content from it.",
    "parameters": {
      "type": "object",
      "properties": {
        "url": {
          "type": "string",
          "description": "The URL to fetch content from."
        }
      },
      "required": ["url"]
    }
  }
}
```

### Parameters

- `url` (required): The URL to fetch content from

## Behavior

### Primary Path: Moonshot Fetch Service (Optional)

When Moonshot fetch service is configured:

1. Get service configuration from `config.services.moonshot_fetch`:
   - `base_url`: Service endpoint URL
   - `api_key`: API key (may be resolved via OAuth)
   - `oauth`: OAuth configuration (optional)
   - `custom_headers`: Additional headers (optional)

2. POST to service with:
   ```json
   {"url": "https://example.com"}
   ```

3. Headers:
   ```
   Authorization: Bearer <api_key>
   Accept: text/markdown
   X-Msh-Tool-Call-Id: <tool_call_id>
   ```

4. Response: Markdown content

5. If service fails, fall back to local fetch

### Fallback Path: Local HTTP Fetch + Trafilatura

When Moonshot service is not configured or fails:

1. Fetch URL content using `fetch_url()` from `web-fetch-shared`
2. Check content type:
   - `text/plain` or `text/markdown`: passthrough (no extraction)
   - Other types: trafilatura extraction
3. Extract text using `extract_text()` with Kimi-specific options:
   ```python
   extracted_text = trafilatura.extract(
       html_content,
       include_comments=True,
       include_tables=True,
       include_formatting=False,
       output_format="txt",
       with_metadata=True,
   )
   ```
4. Return extracted text

### No LLM Summarization

Kimi returns raw extracted text without any LLM summarization step.

### Content Limits

- Uses `ToolResultBuilder` pattern with `DEFAULT_MAX_CHARS = 50000`
- Per-line handling via trafilatura extraction

## Response Formatting

### Service Fetch Success

```
[Extracted markdown content]
```

With message: `"The returned content is the main content extracted from the page."`

### Text/Plain Passthrough

```
[Raw content]
```

With message: `"The returned content is the full content of the page."`

### Empty Response

```
The response body is empty.
```

### Extraction Failure

```
Failed to extract meaningful content from the page. This may indicate the page content is not suitable for text extraction, or the page requires JavaScript to render its content.
```

### Network Error

```
Failed to fetch URL due to network error: <error message>. This may indicate the URL is invalid or the server is unreachable.
```

### HTTP Error

```
Failed to fetch URL. Status: <status_code>. This may indicate the page is not accessible or the server is down.
```

## Implementation File

`plugins/kimi-tools/src/kimi_tools/kimi_fetch_url_tool.py`

## Package Updates

### Update `agent_plugin.json`

```json
{
  "module": "kimi_tools",
  "subdirectory": ".",
  "entries": [
    "kimi_tools.kimi_read_file_tool.KimiReadFileTool",
    "kimi_tools.kimi_write_file_tool.KimiWriteFileTool",
    "kimi_tools.kimi_str_replace_file_tool.KimiStrReplaceFileTool",
    "kimi_tools.kimi_glob_tool.KimiGlobTool",
    "kimi_tools.kimi_grep_tool.KimiGrepTool",
    "kimi_tools.kimi_shell_tool.KimiShellTool",
    "kimi_tools.kimi_fetch_url_tool.KimiFetchURLTool"
  ],
  "kinds": {
    ...
    "kimi_tools.kimi_fetch_url_tool.KimiFetchURLTool": "tools"
  }
}
```

### Update `__init__.py`

```python
from .kimi_fetch_url_tool import KimiFetchURLTool

__all__ = [
    ...
    "KimiFetchURLTool",
]
```

### Update `pyproject.toml`

Add dependency:
- `web-fetch-shared` (from path)

## Configuration

### Moonshot Fetch Service Configuration

```yaml
services:
  moonshot_fetch:
    base_url: "https://api.moonshot.cn/v1/fetch"
    api_key: "${MOONSHOT_API_KEY}"
    oauth: null
    custom_headers: null
```

The plugin should read this from `config.get("services", {}).get("moonshot_fetch")`.

## Tests

### Schema Tests (`tests/test_kimi_fetch_url_tool.py`)

1. Tool name is `FetchURL` (PascalCase)
2. Parameter `url` is required
3. Description matches Kimi CLI

### Moonshot Service Tests

1. Service configured → service fetch attempted
2. Service returns markdown → content returned
3. Service fails → fallback to local fetch
4. Service not configured → local fetch used

### Local Fetch Tests

1. Mock HTTP server returning HTML → trafilatura extraction
2. Mock HTTP server returning text/plain → passthrough
3. Mock HTTP server returning text/markdown → passthrough
4. Network error → error response
5. HTTP error (404, 500) → error response
6. Empty response → empty message

### Extraction Tests

1. HTML with main content → extracted text
2. HTML with no extractable content → extraction failure message
3. Extraction options match Kimi defaults

### Integration Tests (`tests/test_kimi_fetch_url_tool_openrouter_integration.py`)

1. Tool works with OpenRouter provider
2. End-to-end fetch flow (no summarization)

## Documentation

### Update `plugins/kimi-tools/README.md`

Add section:

```markdown
## FetchURL Tool

### Tool Name
`FetchURL`

### Parameters
- `url` (required): The URL to fetch content from

### Behavior

1. **Primary path** (when Moonshot fetch service is configured):
   - POSTs to Moonshot fetch service
   - Returns markdown content from service

2. **Fallback path** (when service not configured or fails):
   - Local HTTP fetch
   - Trafilatura extraction for HTML
   - Passthrough for text/plain and text/markdown

### No LLM Summarization

Unlike other vendors, Kimi returns raw extracted text without LLM summarization.

### Configuration

```yaml
services:
  moonshot_fetch:
    base_url: "https://api.moonshot.cn/v1/fetch"
    api_key: "${MOONSHOT_API_KEY}"
```

- `web_fetch_timeout_seconds`: Fetch timeout (default: 10)
- `web_fetch_max_chars`: Max content length (default: 50000)

### Known Limitations

- No IDE integration for approval flows
- No browser rendering for JavaScript-heavy pages
- Extraction quality depends on trafilatura
```

## Requirements Checklist

- [ ] Implement `KimiFetchURLTool` class
- [ ] Moonshot fetch service support
- [ ] Local fetch via `web-fetch-shared`
- [ ] Trafilatura extraction with Kimi options
- [ ] text/plain and text/markdown passthrough
- [ ] Update `agent_plugin.json`
- [ ] Update `__init__.py` exports
- [ ] Update `pyproject.toml` dependencies
- [ ] Add schema tests
- [ ] Add Moonshot service tests
- [ ] Add local fetch tests
- [ ] Add extraction tests
- [ ] Add OpenRouter integration test
- [ ] Update README documentation

## Key Files

| File | Purpose |
|------|---------|
| `plugins/kimi-tools/src/kimi_tools/kimi_fetch_url_tool.py` | Tool implementation |
| `plugins/kimi-tools/agent_plugin.json` | Plugin manifest |
| `plugins/kimi-tools/src/kimi_tools/__init__.py` | Package exports |
| `plugins/kimi-tools/pyproject.toml` | Package dependencies |
| `plugins/kimi-tools/tests/test_kimi_fetch_url_tool.py` | Unit tests |
| `plugins/kimi-tools/tests/test_kimi_fetch_url_tool_openrouter_integration.py` | Integration tests |
| `plugins/kimi-tools/README.md` | Documentation |

## Source References

- Kimi FetchURL implementation: `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/web/fetch.py`
- Kimi description template: `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/web/fetch.md`

## Notes

- Tool name is `FetchURL` (PascalCase), matching Kimi CLI convention
- No LLM summarization - returns raw extracted text
- Moonshot fetch service is optional; local fetch works without it
- Trafilatura extraction options match Kimi CLI defaults
- No context/LLM access needed (unlike Gemini and Qwen)
