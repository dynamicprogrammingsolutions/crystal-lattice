# 113 - Gemini Web Fetch Tool

Short description: Implement `GeminiWebFetchTool` in `gemini-tools` with Gemini API server-side fetch (primary) and local fetch + LLM summarization (fallback). Tool is disabled when no Gemini API key is available.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/111-tool-plugin-context.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/112-web-fetch-shared.md`

## Goal

Add a Gemini CLI-compatible `web_fetch` tool to the `gemini-tools` plugin package. The tool uses the Gemini API's server-side URL grounding capability as the primary path, falling back to local HTTP fetch + LLM summarization when the primary fails or for private IP URLs.

## Tool Specification

### Tool Name

`web_fetch`

### Schema

```json
{
  "type": "function",
  "function": {
    "name": "web_fetch",
    "description": "Processes content from URL(s), including local and private network addresses (e.g., localhost), embedded in a prompt. Include up to 20 URLs and instructions (e.g., summarize, extract specific data) directly in the 'prompt' parameter.",
    "parameters": {
      "type": "object",
      "properties": {
        "prompt": {
          "type": "string",
          "description": "A comprehensive prompt that includes the URL(s) (up to 20) to fetch and specific instructions on how to process their content (e.g., \"Summarize https://example.com/article and extract key points from https://another.com/data\"). All URLs to be fetched must be valid and complete, starting with \"http://\" or \"https://\", and be fully-formed with a valid hostname (e.g., a domain name like \"example.com\" or an IP address). For example, \"https://example.com\" is valid, but \"example.com\" is not."
        }
      },
      "required": ["prompt"]
    }
  }
}
```

### Parameters

- `prompt` (required): A prompt containing URLs (up to 20) and instructions for processing their content.

## Behavior

### API Key Gating

The tool checks for a Gemini API key in `init()` and reports disabled in `is_enabled()`:

```python
def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
    api_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
    return {
        "config": config,
        "api_key": api_key,
        "disabled": api_key is None,
    }

def is_enabled(self, config, tags, models, context) -> Optional[bool]:
    if self._state.get("disabled"):
        return False
    return None  # Fall back to tag-based checks
```

### Primary Path: Gemini API Server-Side Fetch

When a Gemini API key is available:

1. Parse URLs from `prompt` text using `parse_urls_from_text()`
2. Apply GitHub URL normalization using `normalize_github_url()`
3. Check rate limiting (10 requests per 60 seconds per host)
4. Call Gemini API with the prompt using `google-genai` SDK
5. Extract grounding metadata from response:
   - `groundingChunks`: source titles and URLs
   - `groundingSupports`: citation index positions
6. Format response with inline `[N]` citations and `Sources:` footer using `format_gemini_citations()`
7. Return formatted response

**Source reference**: `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/web-fetch.ts`

### Fallback Path: Local Fetch + LLM Summarization

Triggered when:
- URL is a private/internal IP (detected via `is_private_url()`)
- Primary API call fails
- No usable content from API (no text, no sources)

Fallback behavior:

1. Parse first URL from prompt
2. Apply GitHub URL normalization
3. Fetch URL content using `fetch_url()` from `web-fetch-shared`
4. Extract text using `extract_text()` from `web-fetch-shared`
5. Truncate content using `truncate_content()`
6. Call LLM for summarization via context:
   ```python
   core = context.get("core")
   if core:
       # Build summarization prompt
       summarization_prompt = f'The user requested: "{user_prompt}"\n\nContent:\n---\n{content}\n---'
       temp_session = core.add_message(
           Session(session_id="temp", messages=[]),
           "user",
           summarization_prompt,
       )
       events = core.stream_request(temp_session, config)
       # Extract summary from events
   ```
7. Return LLM-summarized content

### Rate Limiting

Per-host rate limit: 10 requests per 60 seconds.

```python
# Track requests per host
host_history: dict[str, list[float]] = {}

def check_rate_limit(url: str) -> tuple[bool, Optional[int]]:
    """Returns (allowed, wait_seconds)."""
    hostname = urlparse(url).hostname
    now = time.time()
    window_start = now - 60.0
    
    history = [t for t in host_history.get(hostname, []) if t > window_start]
    
    if len(history) >= 10:
        wait = int(history[0] + 60 - now)
        return False, wait
    
    history.append(now)
    host_history[hostname] = history
    return True, None
```

### Content Limits

- `MAX_CONTENT_LENGTH = 100000` chars
- `MAX_EXPERIMENTAL_FETCH_SIZE = 10 * 1024 * 1024` bytes (10MB)
- `URL_FETCH_TIMEOUT_MS = 10000` (10 seconds)

## Response Formatting

### Primary Path Success

```
The API returns data[1] about the topic[2].

Sources:
[1] Title (https://example.com)
[2] Another Title (https://another.com)
```

### Primary Path No Results

```
No search results or information found for query: "..."
```

### Fallback Success

```
[LLM-summarized content]
```

### Error

```
Error: [error message]
```

## Implementation File

`plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

## Package Updates

### Update `agent_plugin.json`

```json
{
  "module": "gemini_tools",
  "subdirectory": ".",
  "entries": [
    "gemini_tools.gemini_read_file_tool.GeminiReadFileTool",
    "gemini_tools.gemini_list_directory_tool.GeminiListDirectoryTool",
    "gemini_tools.gemini_grep_search_tool.GeminiGrepSearchTool",
    "gemini_tools.gemini_glob_tool.GeminiGlobTool",
    "gemini_tools.gemini_write_file_tool.GeminiWriteFileTool",
    "gemini_tools.gemini_replace_tool.GeminiReplaceTool",
    "gemini_tools.gemini_shell_tool.GeminiShellTool",
    "gemini_tools.gemini_web_fetch_tool.GeminiWebFetchTool"
  ],
  "kinds": {
    ...
    "gemini_tools.gemini_web_fetch_tool.GeminiWebFetchTool": "tools"
  }
}
```

### Update `__init__.py`

```python
from .gemini_web_fetch_tool import GeminiWebFetchTool

__all__ = [
    ...
    "GeminiWebFetchTool",
]
```

### Update `pyproject.toml`

Add dependencies:
- `web-fetch-shared` (from path)
- `google-genai>=0.3.0` (for Gemini API calls)

## Tests

### Schema Tests (`tests/test_gemini_web_fetch_tool.py`)

1. Tool name is `web_fetch`
2. Parameter `prompt` is required
3. Description matches Gemini CLI

### API Key Tests

1. API key present → tool enabled
2. No API key → tool disabled (empty schemas or `is_enabled()` returns False)
3. API key from config takes precedence over environment variable

### Fetch Behavior Tests

1. Mock HTTP server returning HTML → extracted text
2. Mock HTTP server returning text/plain → passthrough
3. Network error → error response
4. Timeout handling
5. GitHub URL normalization applied

### Citation Formatting Tests

1. Response with grounding metadata → formatted with `[N]` markers
2. Response with sources → `Sources:` footer appended
3. Response without grounding → raw text returned

### Fallback Tests

1. Private IP URL → fallback triggered
2. Primary API failure → fallback triggered
3. No usable content → fallback triggered
4. Fallback uses context for LLM call

### Rate Limiting Tests

1. First 10 requests allowed
2. 11th request blocked with wait time
3. Wait time expires → requests allowed again

### Integration Tests (`tests/test_gemini_web_fetch_tool_openrouter_integration.py`)

1. Tool works with OpenRouter provider
2. End-to-end fetch and summarize flow

## Documentation

### Update `plugins/gemini-tools/README.md`

Add section:

```markdown
## Web Fetch Tool

### Tool Name
`web_fetch`

### Parameters
- `prompt` (required): A prompt containing URLs (up to 20) and instructions for processing their content.

### Behavior

1. **Primary path**: Uses Gemini API's server-side URL grounding capability.
   - Returns content with inline citations `[N]` and a `Sources:` footer.
   - Requires a Gemini API key.

2. **Fallback path**: Local HTTP fetch + LLM summarization.
   - Triggered for private IP URLs or when primary fails.
   - Uses the configured provider for summarization.

### Configuration

- `gemini_api_key`: Gemini API key (or `GEMINI_API_KEY` environment variable)
- `web_fetch_timeout_seconds`: Fetch timeout (default: 10)
- `web_fetch_max_content_chars`: Max content length (default: 100000)

### Known Limitations

- No IDE integration for approval flows
- No browser rendering for JavaScript-heavy pages
- Requires Gemini API key for primary path
```

## Requirements Checklist

- [ ] Implement `GeminiWebFetchTool` class
- [ ] API key gating via `is_enabled()`
- [ ] Primary path: Gemini API server-side fetch with grounding
- [ ] Citation formatting with `format_gemini_citations()`
- [ ] Fallback path: local fetch + LLM summarization via context
- [ ] Rate limiting per host
- [ ] Update `agent_plugin.json`
- [ ] Update `__init__.py` exports
- [ ] Update `pyproject.toml` dependencies
- [ ] Add schema tests
- [ ] Add API key tests
- [ ] Add fetch behavior tests
- [ ] Add citation formatting tests
- [ ] Add fallback tests
- [ ] Add rate limiting tests
- [ ] Add OpenRouter integration test
- [ ] Update README documentation

## Key Files

| File | Purpose |
|------|---------|
| `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py` | Tool implementation |
| `plugins/gemini-tools/agent_plugin.json` | Plugin manifest |
| `plugins/gemini-tools/src/gemini_tools/__init__.py` | Package exports |
| `plugins/gemini-tools/pyproject.toml` | Package dependencies |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py` | Unit tests |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool_openrouter_integration.py` | Integration tests |
| `plugins/gemini-tools/README.md` | Documentation |

## Source References

- Gemini web fetch implementation: `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/web-fetch.ts`
- Gemini schema definition: `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts` (line 366)

## Notes

- The `google-genai` SDK is used for Gemini API calls
- LLM summarization in fallback uses `context["core"]` for core-level access
- Tool matches Gemini CLI behavior as closely as practical
