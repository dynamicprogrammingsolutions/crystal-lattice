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

- **Shared package = Engine**: HTTP calls, API clients, data extraction, protocol definitions
- **Vendor plugins = Shape**: Tool name, parameters, descriptions, result formatting, error messages

## Package: `tool-compat-shared`

### 1. SearchResult Data Model

```python
# tool_compat_shared/web_search_engine.py

@dataclass(frozen=True)
class SearchResult:
    """Common search result data model across vendors.
    
    Vendors use different subsets of fields:
    - Gemini: title, url (from grounding_chunks)
    - Qwen: title, url, snippet (as content), score, published_date
    - Kimi: title, url, snippet, content, date, site_name
    
    Future configurable tools can use whatever subset they need.
    """
    title: str
    url: str
    snippet: str = ""
    content: str = ""        # Full page content (Kimi include_content)
    date: str = ""           # Published/fetched date
    site_name: str = ""      # Source site name (Kimi)
    score: float = 0.0       # Relevance score 0.0-1.0 (Qwen/Tavily)
```

### 2. SearchProvider Protocol

```python
class SearchProvider(Protocol):
    """Protocol for search provider implementations.
    
    Each vendor tool wraps one or more providers. Providers handle
    the actual HTTP calls and API authentication.
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
        signal: Any = None
    ) -> List[SearchResult]:
        """Execute search and return results.
        
        Args:
            query: Search query string.
            limit: Maximum results to return.
            signal: Optional abort signal for cancellation.
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            SearchProviderError: On API failure.
        """
        ...


class SearchProviderError(Exception):
    """Raised when a search provider fails."""
    def __init__(self, provider_name: str, message: str, original_error: Optional[Exception] = None):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"[{provider_name}] {message}")
```

### 3. Reusable Provider Implementations

#### TavilyProvider

```python
class TavilyProvider:
    """Tavily search API provider.
    
    Configuration:
        - tavily_api_key: API key (required)
        - tavily_search_depth: 'basic' or 'advanced' (default: 'advanced')
        - tavily_max_results: max results (default: 5)
        - tavily_include_answer: include AI answer (default: True)
    """
    name = "Tavily"
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        self._api_key = api_key
        self._config = config or {}
    
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    async def search(self, query: str, *, limit: int = 5, signal=None) -> List[SearchResult]:
        # POST to https://api.tavily.com/search
        # Returns results with optional 'answer' field (handled by caller)
```

#### GoogleProvider

```python
class GoogleProvider:
    """Google Custom Search API provider.
    
    Configuration:
        - google_api_key: API key (required)
           - google_search_engine_id: Custom search engine ID (required)
        - google_max_results: max results (default: 10)
        - google_safe_search: 'off', 'medium', 'high' (default: 'medium')
    """
    name = "Google"
    
    def __init__(self, api_key: str, search_engine_id: str, config: Optional[Dict[str, Any]] = None):
        self._api_key = api_key
        self._cx = search_engine_id
        self._config = config or {}
    
    def is_available(self) -> bool:
        return bool(self._api_key and self._cx)
    
    async def search(self, query: str, *, limit: int = 10, signal=None) -> List[SearchResult]:
        # GET https://www.googleapis.com/customsearch/v1
```

### 4. NOT in Shared Package

The following stay in vendor plugins:

- **Gemini grounding logic** - Uses Gemini SDK, not a generic HTTP provider
- **Dashscope provider** - Tightly coupled to Qwen OAuth, lives in qwen-tools
- **Moonshot search provider** - Tightly coupled to Kimi, lives in kimi-tools
- **Vendor-specific formatting** - All result formatting stays in vendor tools
- **Tool schemas** - Tool names, parameters, descriptions stay in vendor tools

### 5. Dependencies

| Package | Dependencies |
|---------|-------------|
| `tool-compat-shared` | `aiohttp` (for async HTTP) |

## Exports

Update `tool_compat_shared/__init__.py`:

```python
from .web_search_engine import (
    SearchResult,
    SearchProvider,
    SearchProviderError,
    TavilyProvider,
    GoogleProvider,
)

__all__ = [
    # ... existing exports ...
    "SearchResult",
    "SearchProvider",
    "SearchProviderError",
    "TavilyProvider",
    "GoogleProvider",
]
```

## Test Plan

### Unit Tests

1. **SearchResult dataclass**
   - Field defaults are correct
   - Frozen (immutable)
   - All optional fields work

2. **TavilyProvider**
   - `is_available()` returns True with key, False without
   - `search()` constructs correct API request
   - Error handling for API failures
   - Response parsing into SearchResult objects

3. **GoogleProvider**
   - `is_available()` returns True with key+cx, False without either
   - `search()` constructs correct API URL
   - Error handling for API failures
   - Response parsing into SearchResult objects

### Integration Tests

1. Mock Tavily API responses
2. Mock Google Custom Search API responses

## Deliverables

1. `plugins/tool-compat-shared/src/tool_compat_shared/web_search_engine.py`
2. Updated `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
3. Tests in `plugins/tool-compat-shared/tests/test_web_search_engine.py`
4. Updated README documenting new exports

## Status: TODO
