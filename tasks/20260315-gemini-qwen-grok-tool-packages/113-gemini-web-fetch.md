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

- [x] Implement `GeminiWebFetchTool` class
- [x] API key gating via `is_enabled()`
- [x] Primary path: Gemini API server-side fetch with grounding
- [x] Citation formatting with `format_gemini_citations()`
- [x] Fallback path: local fetch + LLM summarization via context
- [x] Rate limiting per host
- [x] Update `agent_plugin.json`
- [x] Update `__init__.py` exports
- [x] Update `setup.py` dependencies (web-fetch-shared, google-genai)
- [x] Add schema tests
- [x] Add API key tests
- [x] Add fetch behavior tests
- [x] Add citation formatting tests
- [x] Add fallback tests
- [x] Add rate limiting tests
- [x] Add Gemini integration test
- [x] Update README documentation

## Key Files

| File | Purpose |
|------|---------|
| `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py` | Tool implementation |
| `plugins/gemini-tools/agent_plugin.json` | Plugin manifest |
| `plugins/gemini-tools/src/gemini_tools/__init__.py` | Package exports |
| `plugins/gemini-tools/setup.py` | Package dependencies |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py` | Unit tests |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool_integration.py` | Integration tests |
| `plugins/gemini-tools/README.md` | Documentation |

## Source References

- Gemini web fetch implementation: `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/web-fetch.ts`
- Gemini schema definition: `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts` (line 366)

## Notes

- The `google-genai` SDK is used for Gemini API calls
- LLM summarization in fallback uses `context["core"]` for core-level access
- Tool matches Gemini CLI behavior as closely as practical

---

## Completion Notes

**Implementation completed successfully.**

### Files Created

| File | Purpose |
|------|---------|
| `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py` | Tool implementation (320 lines) |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py` | 32 unit tests |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool_integration.py` | 5 integration tests |

### Files Modified

| File | Changes |
|------|---------|
| `plugins/gemini-tools/setup.py` | Added web-fetch-shared and google-genai dependencies |
| `plugins/gemini-tools/agent_plugin.json` | Added GeminiWebFetchTool entry |
| `plugins/gemini-tools/src/gemini_tools/__init__.py` | Exported GeminiWebFetchTool |
| `plugins/gemini-tools/README.md` | Added Web Fetch Tool documentation section |
| `plugins/gemini-tools/tests/test_gemini_read_file_tool.py` | Updated plugin manager test for new tools |
| `plugins/gemini-tools/tests/test_gemini_search_tools.py` | Updated plugin manager test for new tools |

### Implementation Details

1. **Primary Path**: Uses `google.genai.Client` with model `gemini-2.5-flash`. Gemini can access URLs directly in prompts without explicit grounding configuration.

2. **Fallback Path**: Triggered for private IP URLs or when primary fails. Uses `fetch_url()` and `extract_text()` from web-fetch-shared, then uses `context["core"]` for LLM summarization.

3. **Rate Limiting**: 10 requests per 60 seconds per hostname, stored in class-level `_host_history` dict.

4. **API Key Gating**: Tool disabled when no `GEMINI_API_KEY` in environment or `gemini_api_key` in config. `is_enabled()` returns False when disabled.

5. **Citation Formatting**: Uses `format_gemini_citations()` from web-fetch-shared, but note that the standard Gemini API doesn't return grounding metadata for URL fetching (unlike the Gemini CLI's internal `web-fetch` model).

6. **stream_tool Method**: Must be a regular function returning `Iterator`, NOT an async generator. The core's `iter_tool_messages` expects synchronous iterators.

### Test Results

- **Unit tests**: 32 tests passing
- **Integration tests**: 
  - Gemini API primary path test passing with real API key
  - End-to-end test with Ollama API documentation passing
  - User request simulation test passing
- **All gemini-tools tests**: 84 tests passing

### Known Limitations

- The standard Gemini API doesn't provide grounding metadata for URL fetching (unlike the Gemini CLI's internal implementation)
- Citations are formatted but may not appear unless grounding metadata is present
- Fallback LLM summarization requires `context["core"]` to be available

---

## Follow-Up: Align with Gemini CLI Implementation

**Status**: Pending approval

**Reference**: Comparison with Gemini CLI `web-fetch.ts` and `default-legacy.ts` revealed gaps in the initial implementation.

### Gap Analysis

| Aspect | Gemini CLI | Current Implementation | Gap |
|--------|------------|------------------------|-----|
| **Schema modes** | Two modes: prompt mode (default) and direct mode (`url` param) | Only prompt mode | Missing direct mode |
| **Primary model** | Uses `web-fetch` model (special Gemini model) | Uses `gemini-2.5-flash` | Not configurable |
| **Fallback model** | Uses `web-fetch-fallback` model | Uses `context["core"]` (current agent) | No dedicated fallback agent |
| **Rate limiting** | LRU cache (1000 hosts) via `mnemonist` library | Simple class dict (unbounded) | No eviction, potential memory growth |
| **Configuration** | `directWebFetch` config flag + model selection | No configuration | Not configurable at runtime |

### Implementation Plan

#### Task 1: Add Configuration Schema and UI Elements

**File**: `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

Add `get_config_schema()` and `get_ui_elements()` methods following the OpenAI web search extension pattern (flat keys with prefix):

```python
def get_config_schema(self) -> Dict[str, Any]:
    return {
        "web_fetch_enabled": {
            "type": "boolean",
            "default": True,
            "description": "Enable the web_fetch tool",
        },
        "web_fetch_direct_mode": {
            "type": "boolean",
            "default": False,
            "description": "Use direct URL fetch mode instead of prompt mode",
        },
        "web_fetch_primary_model": {
            "type": "string",
            "default": "web-fetch",
            "description": "Gemini model for primary path (server-side URL grounding)",
        },
        "web_fetch_fallback_agent_id": {
            "type": "string",
            "default": None,
            "description": "Optional dedicated agent for fallback summarization",
        },
        "web_fetch_fallback_model": {
            "type": "string",
            "default": None,
            "description": "Optional model override for fallback",
        },
        "web_fetch_timeout_seconds": {
            "type": "integer",
            "default": 10,
            "description": "Fetch timeout in seconds",
        },
        "web_fetch_max_content_chars": {
            "type": "integer",
            "default": 100000,
            "description": "Maximum content length in characters",
        },
        "web_fetch_rate_limit_requests": {
            "type": "integer",
            "default": 10,
            "description": "Max requests per rate limit window per host",
        },
        "web_fetch_rate_limit_window": {
            "type": "integer",
            "default": 60,
            "description": "Rate limit window in seconds",
        },
    }

def get_ui_elements(
    self,
    config: Dict[str, Any],
    tags: List[str],
    models: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        {"type": "checkbox", "key": "web_fetch_enabled", "label": "Enable web fetch"},
        {"type": "checkbox", "key": "web_fetch_direct_mode", "label": "Direct URL mode"},
        {"type": "text", "key": "web_fetch_primary_model", "label": "Primary model"},
        {"type": "text", "key": "web_fetch_fallback_agent_id", "label": "Fallback agent"},
        {"type": "number", "key": "web_fetch_timeout_seconds", "label": "Timeout (seconds)"},
    ]
```

#### Task 2: Implement Direct Mode Schema

**File**: `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

Modify `get_tool_schemas()` to return different schemas based on `web_fetch_direct_mode` config:

- **Prompt mode (default)**: Current schema with `prompt` parameter
- **Direct mode**: Schema with single `url` parameter (matches Gemini CLI experimental mode)

```python
def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    config = state.get("config", {})
    direct_mode = config.get("web_fetch_direct_mode", False)
    
    if direct_mode:
        return [{
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "Fetch content from a URL directly. Send multiple requests for this tool if multiple URL fetches are needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to fetch. Must be a valid http or https URL.",
                        }
                    },
                    "required": ["url"],
                },
            },
        }]
    
    # Default: prompt mode schema (current implementation)
    return [self._get_prompt_mode_schema()]
```

#### Task 3: Implement Configurable Primary Model

**File**: `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

Update `_execute_primary()` to use `web_fetch_primary_model` config (default: `web-fetch`):

```python
async def _execute_primary(self, prompt: str, state: Dict[str, Any]) -> Dict[str, Any]:
    config = state.get("config", {})
    primary_model = config.get("web_fetch_primary_model", "web-fetch")
    
    response = client.models.generate_content(
        model=primary_model,
        contents=prompt,
    )
    # ...
```

#### Task 4: Implement Configurable Fallback Agent/Model

**File**: `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

Update `_execute_fallback()` to support:
1. `web_fetch_fallback_agent_id`: Switch to dedicated summarizer agent (requires app context)
2. `web_fetch_fallback_model`: Override model for fallback (uses current agent if no agent_id)

Pattern follows `gemini-compaction-feature` agent switching via `app.update_agent()`.

#### Task 5: Implement LRU Cache for Rate Limiting

**File**: `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

Replace class-level dict with bounded LRU cache:

```python
class LRUCache:
    def __init__(self, max_size: int = 1000):
        self._max_size = max_size
        self._cache: OrderedDict[str, List[float]] = OrderedDict()
    
    def get(self, key: str) -> List[float]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return []
    
    def set(self, key: str, value: List[float]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

class GeminiWebFetchTool(ToolPlugin):
    _rate_limit_cache = LRUCache(max_size=1000)
```

Configuration: `web_fetch_rate_limit_requests` and `web_fetch_rate_limit_window`.

#### Task 6: Implement Direct Mode Execution

**File**: `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py`

Add execution path for direct mode (always uses fallback path - local fetch):

```python
async def _execute_async(self, arguments, state, context):
    config = state.get("config", {})
    direct_mode = config.get("web_fetch_direct_mode", False)
    
    if direct_mode:
        return await self._execute_direct_mode(arguments, state, context)
    else:
        return await self._execute_prompt_mode(arguments, state, context)
```

Direct mode:
- Validates single `url` parameter
- Always fetches locally (no Gemini API call)
- Uses fallback summarization if LLM available

#### Task 7: Update Tests

**File**: `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py`

Add tests for:
1. Config schema returns expected keys
2. UI elements return expected elements
3. Direct mode schema returned when `web_fetch_direct_mode=True`
4. Primary model config used in API call
5. Fallback agent switching works
6. LRU cache evicts at max size
7. Rate limit config customization

#### Task 8: Update Documentation

**File**: `plugins/gemini-tools/README.md`

Update Web Fetch section with configuration options and mode descriptions.

### Implementation Order

| Order | Task | Effort |
|-------|------|--------|
| 1 | Task 1: Config schema & UI elements | 1h |
| 2 | Task 5: LRU cache for rate limiting | 1h |
| 3 | Task 2: Direct mode schema | 30m |
| 4 | Task 3: Configurable primary model | 30m |
| 5 | Task 4: Configurable fallback agent | 1.5h |
| 6 | Task 6: Direct mode execution | 1h |
| 7 | Task 7: Update tests | 2h |
| 8 | Task 8: Update documentation | 30m |
| **Total** | | **~8h** |

### Files to Modify

| File | Changes |
|------|---------|
| `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py` | Config schema, UI elements, direct mode, LRU cache, configurable models |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py` | New tests for config, modes, LRU cache |
| `plugins/gemini-tools/README.md` | Updated documentation |

---

## Follow-Up Completion Notes

**Implementation completed successfully.**

### Files Modified

| File | Changes |
|------|---------|
| `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py` | Added config schema, UI elements, direct mode, LRU cache, configurable models |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py` | Added tests for config schema, UI elements, direct mode, LRU cache, rate limiting |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool_integration.py` | Fixed rate limit cache reset |
| `plugins/gemini-tools/README.md` | Updated documentation with modes and configuration |

### Implementation Summary

1. **Configuration Schema (Task 1)**: Added `get_config_schema()` and `get_ui_elements()` methods with 9 flat config keys (`web_fetch_enabled`, `web_fetch_direct_mode`, etc.)

2. **Direct Mode Schema (Task 2)**: `get_tool_schemas()` now returns different schemas based on `web_fetch_direct_mode` config flag

3. **Configurable Primary Model (Task 3)**: Primary path uses `web_fetch_primary_model` config (default: "web-fetch")

4. **Configurable Fallback Agent (Task 4)**: Fallback path supports `web_fetch_fallback_agent_id` for agent switching and `web_fetch_fallback_model` for model override

5. **LRU Cache for Rate Limiting (Task 5)**: Replaced unbounded dict with `LRUCache(max_size=1000)` matching Gemini CLI's `mnemonist` implementation

6. **Direct Mode Execution (Task 6)**: Added `_execute_direct_mode()` for single URL fetch without Gemini API

7. **Tests (Task 7)**: Added 14 new tests for config schema, UI elements, direct mode, LRU cache, and configurable models

8. **Documentation (Task 8)**: Updated README with modes, configuration table, and call examples

### Configuration Keys

All keys use flat `web_fetch_` prefix following the OpenAI web search extension pattern:

```
web_fetch_enabled           (default: true)
web_fetch_direct_mode       (default: false)
web_fetch_primary_model     (default: "web-fetch")
web_fetch_fallback_agent_id (default: null)
web_fetch_fallback_model    (default: null)
web_fetch_timeout_seconds   (default: 10)
web_fetch_max_content_chars (default: 100000)
web_fetch_rate_limit_requests (default: 10)
web_fetch_rate_limit_window (default: 60)
```

### Test Results

- **Unit tests**: 54 tests passing
- **Integration tests**: External service tests skipped (require API keys)

### Documentation Review

The `plugins/docs/config-schema.md` already documents the flat key convention used. No changes needed to plugin documentation.

---

## Second Follow-Up Completion Notes

**Implementation completed successfully.**

### Additional Changes

| File | Changes |
|------|---------|
| `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py` | Added `web_fetch_use_gemini_api`, `web_fetch_fallback_settings_overrides`; conditional UI visibility; fallback-only path |
| `plugins/gemini-tools/tests/test_gemini_web_fetch_tool.py` | Added 14 new tests for use_gemini_api, settings_overrides, UI conditional visibility |
| `plugins/gemini-tools/README.md` | Updated configuration table with new keys and visibility conditions |

### New Configuration Keys

| Key | Type | Default | UI | Description |
|-----|------|---------|----|----|
| `web_fetch_use_gemini_api` | boolean | true | Yes* | Use Gemini API for primary path |
| `web_fetch_fallback_settings_overrides` | object | {} | No | Settings to override for fallback |

\* Only visible when Gemini API key is available.

### Behavior Changes

1. **`web_fetch_use_gemini_api=false`**: Skips primary path, uses fallback directly
2. **`web_fetch_fallback_settings_overrides`**: Merged into config for fallback path (works with or without `fallback_agent_id`)
3. **UI conditional visibility**: 
   - `use_gemini_api` visible only with API key
   - `primary_model` visible only with API key AND `use_gemini_api=true`
   - `direct_mode` and `timeout` always visible

### Test Results

- **Unit tests**: 68 tests passing
- **New tests added**: 14 tests for new functionality
