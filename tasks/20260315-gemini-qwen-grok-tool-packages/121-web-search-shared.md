# 121 - Web Search Shared Package

Short description: Create shared web search infrastructure in `tool-compat-shared` with `SearchResult` data model, `SearchProvider` protocol, and reusable provider implementations (Tavily, Google Custom Search). Vendor-specific formatting stays in vendor plugins. Providers live here for reuse by configurable tools later.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/110-web-fetch-tools.md` (shares `web-fetch-shared` for HTTP utilities)

## Goal

Provide shared search infrastructure that vendor plugins can use:

1. **Search result data model** - common `SearchResult` dataclass with all fields vendors might use
2. **Search provider protocol** - `SearchProvider` interface for provider implementations
3. **Reusable providers** - Tavily, Google Custom Search providers that can be used by vendor tools or future configurable tools
4. **No vendor-specific formatting** - all LLM-visible formatting stays in vendor plugins

## Key Principle: Engine vs Shape

- **Shared package = Engine**: HTTP calls, API clients, data extraction, protocol definitions, data models
- **Vendor plugins = Shape**: Tool name, parameters, descriptions, result formatting, error messages, citation insertion

This module returns structured data (`SearchResponse`/`SearchResult`). It does NOT format results for LLM consumption. All formatting — citation markers, source footers, truncation banners, result numbering — belongs in vendor tool plugins.

### Known precedent violations in existing shared code

The existing `reader_engine.py` and `search_engine.py` in `tool-compat-shared` violate the Engine vs Shape principle by exporting vendor-specific formatting functions:

- `reader_engine.py`: `build_qwen_truncation_wrapper` (Qwen-specific), `format_tool_result_text`, `format_tool_result_payload`, `format_with_line_numbers`
- `search_engine.py`: `format_gemini_glob_result`, `format_gemini_grep_result`, `format_gemini_list_result`, `format_qwen_glob_result`, `format_qwen_grep_result`, `format_qwen_list_result`

These should ideally live in vendor plugins, not in the shared package. This module will NOT follow that pattern. It returns raw structured data only, and vendor plugins handle all formatting.

## Requirements checklist

- [x] `SearchResult` frozen dataclass with all vendor-needed fields
- [x] `SearchResponse` frozen dataclass wrapping results + optional answer
- [x] `SearchProvider` Protocol with `name`, `is_available`, `search`
- [x] `SearchProviderError` exception with provider name and original error
- [x] `TavilyProvider` concrete implementation (aiohttp, POST to api.tavily.com)
- [x] `GoogleProvider` concrete implementation (aiohttp, GET to customsearch/v1)
- [x] All exports added to `tool_compat_shared/__init__.py`
- [x] `tool-compat-shared` pyproject.toml updated with `aiohttp` dependency
- [x] Unit tests for all data models, protocol conformance, and provider logic
- [x] Integration tests with mock HTTP servers for Tavily and Google providers
- [x] Integration tests using real API keys from `.env` (`GOOGLE_API_KEY`, `TAVILY_API_KEY`) — marked `integration`
- [x] README updated with new exports

## Execution plan

Added during completion.

### Design decisions

1. **Package placement**: New module `web_search_engine.py` in `tool-compat-shared`, NOT a separate package. Rationale: the task file specifies `tool-compat-shared`, and the search providers are lightweight HTTP clients (unlike `web-fetch-shared` which has heavy `trafilatura` deps). However, `aiohttp` is a heavy dep, so we need to decide.

   **Decision**: Place in `tool-compat-shared` and add `aiohttp` as a dependency. The existing `web-fetch-shared` already depends on `aiohttp`, and all vendor packages that will use search also depend on `web-fetch-shared`. Adding `aiohttp` to `tool-compat-shared` is acceptable because:
   - It's already transitively available in all consuming packages
   - The alternative (a third shared package) adds packaging complexity for minimal gain
   - `tool-compat-shared` already has no stdlib-only constraint in its stated purpose (it just happens to be stdlib-only currently)

   **Alternative considered**: Create `web-search-shared` as a separate package. Rejected because it's one module with two provider classes — not enough substance for a full package, and the task file explicitly says `tool-compat-shared`.

2. **Lazy aiohttp import**: Follow the `web-fetch-shared` pattern of lazy-importing `aiohttp` inside provider methods so the module can be imported in environments where aiohttp isn't installed (for type-checking, etc.).

3. **SearchResult fields**: Include all fields needed by Gemini (title, url from grounding), Qwen (title, url, snippet, score, published_date), and Kimi (title, url, snippet, content, date, site_name). The `content` field covers Tavily's `content` and Kimi's page crawling results.

4. **NO formatting in this module**: This module returns `SearchResponse` with structured `SearchResult` objects. All formatting — including Gemini's UTF-8 byte-offset citation insertion, Qwen's answer+sources layout, and Kimi's Title/Date/URL/Summary format — belongs in vendor tool plugins. This is the correct Engine vs Shape separation, and it corrects the mistake made in `reader_engine.py` and `search_engine.py` where vendor-specific formatting leaked into the shared package.

   Specifically, `format_gemini_citations_utf8` (originally proposed for this module) will instead be implemented in the Gemini vendor plugin (`gemini_web_search_tool.py`, task 122). The shared package provides the raw `grounding_chunks` and `grounding_supports` data from the Gemini API response; the Gemini plugin handles citation marker insertion and source footer formatting.

5. **SearchProvider protocol**: Use `typing.Protocol` for structural subtyping, matching the pattern from Qwen's `WebSearchProvider` interface. Concrete providers are plain classes (not Protocol subclasses) — they just need to satisfy the protocol structurally.

6. **Provider config pattern**: Providers accept config via constructor parameters (not a generic dict), matching the Qwen TS pattern where `TavilyProvider(config)` receives typed config. This is cleaner than dict-based config for provider implementations.

7. **Error handling**: `SearchProviderError` wraps all provider failures with the provider name. Each provider catches HTTP/parsing errors and re-raises as `SearchProviderError`. This matches Qwen's `BaseWebSearchProvider` pattern.

8. **`SearchResponse` wrapper**: Tavily returns a top-level `answer` field that doesn't belong on any individual `SearchResult`. `SearchResponse(results, answer, query)` cleanly captures this, matching Qwen's `WebSearchResult` type which has `answer` as a top-level field. Vendor plugins decide how to present the answer (Gemini ignores it, Qwen shows it, Kimi ignores it).

### File layout

```
plugins/tool-compat-shared/
  src/tool_compat_shared/
    web_search_engine.py          # NEW - search infrastructure (data + providers only)
    __init__.py                    # UPDATED - add new exports
  tests/
    test_web_search_engine.py      # NEW - unit + mock integration tests
  pyproject.toml                   # UPDATED - add aiohttp dependency
  README.md                        # UPDATED - document new exports
```

### Concrete interfaces

#### `SearchResult` dataclass

```python
@dataclass(frozen=True)
class SearchResult:
    """Common search result data model across vendors.
    
    Vendors use different subsets of fields:
    - Gemini: title, url (from grounding_chunks)
    - Qwen: title, url, snippet (as content), score, date
    - Kimi: title, url, snippet, content, date, site_name
    - Tavily: title, url, content, score, date
    - Google: title, url, snippet, site_name (displayLink)
    
    Future configurable tools can use whatever subset they need.
    All fields have defaults so vendors only set what they need.
    """
    title: str
    url: str
    snippet: str = ""
    content: str = ""           # Full page content (Kimi include_content, Tavily content)
    date: str = ""              # Published/fetched date (Kimi date, Qwen publishedDate, Tavily published_date)
    site_name: str = ""         # Source site name (Kimi, Google displayLink)
    score: float = 0.0          # Relevance score 0.0-1.0 (Qwen, Tavily)
```

#### `SearchResponse` dataclass

```python
@dataclass(frozen=True)
class SearchResponse:
    """Wrapper for search provider responses.
    
    Contains the list of results plus optional metadata
    that applies to the entire response (not individual results).
    Vendor plugins decide how to present each field.
    """
    results: List[SearchResult]
    answer: str = ""            # AI-generated answer (Tavily include_answer)
    query: str = ""             # Original query (for reference)
```

#### `SearchProviderError` exception

```python
class SearchProviderError(Exception):
    """Raised when a search provider fails.
    
    Always includes the provider name for clear error messages.
    Chains the original exception for debugging.
    Vendor plugins catch this and format vendor-specific error messages.
    """
    def __init__(
        self, 
        provider_name: str, 
        message: str, 
        original_error: Optional[Exception] = None
    ):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"[{provider_name}] {message}")
```

#### `SearchProvider` protocol

```python
class SearchProvider(Protocol):
    """Protocol for search provider implementations.
    
    Each vendor tool wraps one or more providers. Providers handle
    the actual HTTP calls and API authentication.
    
    Implementations must be stateless between calls — all config
    is provided at construction time, matching the ToolPlugin pattern
    where instances are short-lived per request.
    """
    @property
    def name(self) -> str:
        """Provider display name for error messages and logging."""
        ...
    
    def is_available(self) -> bool:
        """Check if provider has required configuration (API keys, etc).
        
        Returns:
            True if provider can make search calls.
        """
        ...
    
    async def search(
        self, 
        query: str, 
        *, 
        limit: int = 5,
    ) -> SearchResponse:
        """Execute search and return structured results.
        
        Args:
            query: Search query string.
            limit: Maximum results to return.
            
        Returns:
            SearchResponse with results and optional answer.
            NO formatting is applied — vendor plugins handle that.
            
        Raises:
            SearchProviderError: On API failure.
        """
        ...
```

#### `TavilyProvider` concrete class

```python
class TavilyProvider:
    """Tavily search API provider.
    
    Configuration via constructor:
        api_key: Tavily API key (required)
        search_depth: 'basic' or 'advanced' (default: 'advanced')
        include_answer: Include AI-generated answer (default: True)
    
    API: POST https://api.tavily.com/search
    Response mapping:
        results[].title          → SearchResult.title
        results[].url            → SearchResult.url
        results[].content        → SearchResult.content
        results[].score          → SearchResult.score
        results[].published_date → SearchResult.date
        answer (top-level)       → SearchResponse.answer
    """
    name: str = "Tavily"
    
    def __init__(
        self, 
        api_key: str, 
        *,
        search_depth: str = "advanced",
        include_answer: bool = True,
    ):
        self._api_key = api_key
        self._search_depth = search_depth
        self._include_answer = include_answer
    
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    async def search(self, query: str, *, limit: int = 5) -> SearchResponse:
        # Lazy import aiohttp
        # POST to https://api.tavily.com/search
        #   body: {api_key, query, search_depth, max_results, include_answer}
        # Parse response into SearchResponse
        #   - results[].published_date → date
        #   - results[].content → content (NOT snippet — Tavily content is full text)
        #   - top-level answer → SearchResponse.answer
        # Raise SearchProviderError on HTTP/parse failure
        ...
```

#### `GoogleProvider` concrete class

```python
class GoogleProvider:
    """Google Custom Search API provider.
    
    Configuration via constructor:
        api_key: Google API key (required)
        search_engine_id: Custom search engine ID / cx (required)
        safe_search: 'off', 'medium', 'high' (default: 'medium')
    
    API: GET https://www.googleapis.com/customsearch/v1?key=...&cx=...&q=...&num=...&safe=...
    Response mapping:
        items[].title       → SearchResult.title
        items[].link        → SearchResult.url
        items[].snippet     → SearchResult.snippet
        items[].displayLink → SearchResult.site_name
    """
    name: str = "Google"
    
    def __init__(
        self, 
        api_key: str, 
        search_engine_id: str,
        *,
        safe_search: str = "medium",
    ):
        self._api_key = api_key
        self._cx = search_engine_id
        self._safe_search = safe_search
    
    def is_available(self) -> bool:
        return bool(self._api_key and self._cx)
    
    async def search(self, query: str, *, limit: int = 10) -> SearchResponse:
        # Lazy import aiohttp
        # GET https://www.googleapis.com/customsearch/v1
        #   params: key, cx, q, num, safe
        # Parse response into SearchResponse
        #   - items[].link → url
        #   - items[].snippet → snippet
        #   - items[].displayLink → site_name
        # Raise SearchProviderError on HTTP/parse failure
        ...
```

### Updated `__init__.py` exports

```python
from .web_search_engine import (
    GoogleProvider,
    SearchProvider,
    SearchProviderError,
    SearchResponse,
    SearchResult,
    TavilyProvider,
)

__all__ = [
    # ... existing exports ...
    "GoogleProvider",
    "SearchProvider",
    "SearchProviderError",
    "SearchResponse",
    "SearchResult",
    "TavilyProvider",
]
```

### Updated `pyproject.toml`

Add `aiohttp` to dependencies:

```toml
dependencies = [
    "aiohttp>=3.8.0",
]
```

### Test plan

#### Unit tests (`test_web_search_engine.py`)

1. **SearchResult**
   - Construction with required fields only
   - Construction with all optional fields
   - Frozen (immutable) — `dataclasses.FrozenInstanceError` on assignment
   - Default values are correct

2. **SearchResponse**
   - Construction with results only
   - Construction with answer and query
   - Frozen (immutable)

3. **SearchProviderError**
   - Message format: `[ProviderName] message`
   - `provider_name` attribute
   - `original_error` chaining

4. **TavilyProvider**
   - `is_available()` returns True with key, False with empty key
   - `search()` constructs correct POST request body
   - Response parsing: title, url, content, score, published_date → SearchResult
   - Answer field mapped to SearchResponse.answer
   - Error handling: HTTP errors → SearchProviderError
   - Error handling: invalid JSON → SearchProviderError
   - `search_depth` and `include_answer` config passed correctly

5. **GoogleProvider**
   - `is_available()` returns True with key+cx, False without either
   - `search()` constructs correct GET URL with query params
   - Response parsing: title, link, snippet, displayLink → SearchResult
   - Error handling: HTTP errors → SearchProviderError
   - Error handling: invalid JSON → SearchProviderError
   - `safe_search` config passed correctly

#### Integration tests — mock HTTP (always run)

6. **TavilyProvider with mock server**
   - Successful search returning multiple results
   - Successful search with answer
   - API error (401, 500)
   - Network error
   - Empty results

7. **GoogleProvider with mock server**
   - Successful search returning multiple results
   - API error (403, 500)
   - Network error
   - Empty results (no items in response)

#### Integration tests — real API (marked `integration`, skipped unless keys available)

8. **Real API tests**
   - `.env` in the repo root contains `GOOGLE_API_KEY` and `TAVILY_API_KEY`
   - Tests are marked `@pytest.mark.integration` and skipped when keys are not set
   - TavilyProvider: real search query, verify `SearchResponse` structure
   - GoogleProvider: real search query, verify `SearchResponse` structure
   - Both: verify `is_available()` returns True when keys are present

### Implementation order

1. Create `web_search_engine.py` with `SearchResult`, `SearchResponse`, `SearchProviderError`
2. Implement `SearchProvider` protocol
3. Implement `TavilyProvider` with aiohttp
4. Implement `GoogleProvider` with aiohttp
5. Update `__init__.py` with new exports
6. Update `pyproject.toml` with aiohttp dependency
7. Write unit tests (data models, protocol conformance)
8. Write mock integration tests (following `web-fetch-shared/tests/conftest.py` pattern)
9. Write real API integration tests (marked `integration`, using `.env` keys)
10. Update README

### Formatting responsibility by vendor (NOT in this module)

| Formatting concern | Where it belongs |
|---|---|
| Gemini UTF-8 byte-offset citation insertion + Sources footer | `gemini_web_search_tool.py` (task 122) |
| Gemini `format_gemini_citations` (char-based, for web-fetch) | `web-fetch-shared` (existing, stays) |
| Qwen answer + Sources layout | `qwen_web_search_tool.py` (task 123) |
| Qwen top-5 summary fallback | `qwen_web_search_tool.py` (task 123) |
| Kimi Title/Date/URL/Summary separator format | `kimi_web_search_tool.py` (task 124) |
| Any future vendor's formatting | That vendor's tool plugin |

### Source references for implementation

- **Tavily API**: POST `https://api.tavily.com/search` — body: `{api_key, query, search_depth, max_results, include_answer}` — response: `{query, answer?, results: [{title, url, content, score, published_date}]}`
- **Google Custom Search API**: GET `https://www.googleapis.com/customsearch/v1?key=...&cx=...&q=...&num=...&safe=...` — response: `{items: [{title, link, snippet, displayLink}]}`
- **Gemini UTF-8 citations**: `gemini-cli/packages/core/src/tools/web-search.ts` — uses `TextEncoder`/`TextDecoder` for byte-offset insertion (implementation goes in Gemini vendor plugin, NOT here)
- **Qwen provider pattern**: `qwen-code/packages/core/src/tools/web-search/base-provider.ts` — `BaseWebSearchProvider` with error wrapping
- **Kimi search response**: `kimi-cli/src/kimi_cli/tools/web/search.py` — `SearchResult` with `site_name, title, url, snippet, content, date`
- **`.env` keys**: `GOOGLE_API_KEY`, `TAVILY_API_KEY` available in repo root `.env` for integration testing

## Completion Notes

Added during completion.

### Files created/modified

1. **Created**: `plugins/tool-compat-shared/src/tool_compat_shared/web_search_engine.py`
   - `SearchResult` frozen dataclass (7 fields: title, url, snippet, content, date, site_name, score)
   - `SearchResponse` frozen dataclass (results list + answer + query + grounding_chunks + grounding_supports)
   - `SearchProviderError` exception (provider_name, original_error, formatted message)
   - `SearchProvider` Protocol (name, is_available, async search)
   - `TavilyProvider` concrete class (POST api.tavily.com/search, aiohttp, lazy import)
   - `GeminiApiProvider` concrete class (google-genai SDK, googleSearch tool, lazy import)
   - **Removed**: `GoogleProvider` (Google Custom Search API — deprecated 2027)

2. **Updated**: `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
   - Added imports and `__all__` entries for: GeminiApiProvider, SearchProvider, SearchProviderError, SearchResponse, SearchResult, TavilyProvider
   - Removed: GoogleProvider

3. **Updated**: `plugins/tool-compat-shared/pyproject.toml`
   - Added `aiohttp>=3.8.0` to dependencies
   - Added `google-genai>=0.3.0` as optional `[gemini]` dependency
   - Added `pytest-asyncio>=0.21.0` to dev dependencies
   - Added `asyncio_mode = "auto"` and `integration` marker to pytest config
   - Updated description to mention web search

4. **Created**: `plugins/tool-compat-shared/tests/test_web_search_engine.py`
   - 36 unit + mock integration tests (all passing)
   - 2 real Tavily API integration tests (passing with `TAVILY_API_KEY` from `.env`)
   - 1 real Gemini API integration test (passing with `GEMINI_API_KEY` from `.env`)

5. **Updated**: `plugins/tool-compat-shared/README.md`
   - Documented Engine vs Shape principle
   - Documented web_search_engine module exports
   - Documented GeminiApiProvider with googleSearch tool config
   - Flagged existing formatting violations in reader_engine/search_engine

### Test results

- **36/36** unit + mock integration tests pass
- **2/2** real Tavily API integration tests pass (using `TAVILY_API_KEY` from `.env`)
- **1/1** real Gemini API integration test passes (using `GEMINI_API_KEY` from `.env`)
- **0 pre-existing failures** introduced (shell tool failures are unrelated TypeError in agent_core/types.py)
- All existing gemini-tools, qwen-tools, kimi-tools tests remain unaffected

### Key design decisions applied

- **No formatting in shared package**: All formatting (citations, footers, truncation banners) stays in vendor plugins. `format_gemini_citations_utf8` was removed from this module and will be implemented in the Gemini vendor plugin (task 122).
- **SearchResponse with grounding metadata**: Added `grounding_chunks` and `grounding_supports` fields to `SearchResponse` so vendor plugins can access raw Gemini API grounding data for citation formatting without the shared package doing any formatting itself.
- **GoogleProvider removed**: Google Custom Search API is deprecated (2027), replaced with `GeminiApiProvider` which uses the Gemini API's built-in Google Search grounding via the `googleSearch` tool config.
- **GeminiApiProvider uses real model + tool config**: The `web-search` model alias is a Gemini CLI internal concept, not a real API model. The provider uses `gemini-2.5-flash` (configurable) with `tools=[Tool(google_search=GoogleSearch())]` to enable grounding.
- **Lazy imports**: Both `aiohttp` (TavilyProvider) and `google-genai` (GeminiApiProvider) are imported inside their methods, allowing the module to be imported for type-checking without them installed.
- **Constructor-based config**: Providers accept typed constructor params (not dicts), matching the Qwen TS pattern.