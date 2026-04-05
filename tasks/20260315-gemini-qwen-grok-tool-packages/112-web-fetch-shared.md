# 112 - Web Fetch Shared Package

Short description: Create the `web-fetch-shared` library package for HTTP fetching, HTML extraction, and URL normalization helpers. This package isolates heavy dependencies (`trafilatura`, `aiohttp`) from vendor tool packages.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/111-tool-plugin-context.md`

## Goal

Create a dedicated shared package for HTTP fetching and HTML-to-text extraction used by all vendor web fetch tools. This package is a library dependency, NOT a plugin package (no `agent_plugin.json`).

## Package Structure

```
plugins/web-fetch-shared/
├── pyproject.toml
├── README.md
├── src/
│   └── web_fetch_shared/
│       ├── __init__.py
│       └── web_fetch_engine.py
└── tests/
    ├── __init__.py
    └── test_web_fetch_engine.py
```

## Dependencies (pyproject.toml)

```toml
[project]
name = "web-fetch-shared"
version = "0.1.0"
description = "Shared HTTP fetch and HTML extraction helpers for vendor web fetch tools"
requires-python = ">=3.10"
dependencies = [
    "aiohttp>=3.8.0",
    "trafilatura>=1.6.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-aiohttp>=1.0.0"]
```

**Note**: No LLM provider dependencies - LLM calls go through `context["core"]` or `context["app"]` in vendor tools.

## Core Engine Module (`web_fetch_engine.py`)

### Data Structures

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass(frozen=True)
class FetchResult:
    """Result of a URL fetch operation.
    
    Attributes:
        content: The fetched content (raw text/html).
        content_type: Content-Type header value.
        status_code: HTTP status code.
        headers: Response headers dict.
        url: Final URL after redirects.
        is_error: Whether this represents an error.
        error_message: Error message if is_error is True.
    """
    content: str
    content_type: str
    status_code: int
    headers: Dict[str, str]
    url: str
    is_error: bool = False
    error_message: Optional[str] = None
```

### Core Functions

#### 1. `fetch_url`

```python
async def fetch_url(
    url: str,
    *,
    timeout_seconds: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
    max_size_bytes: int = 10 * 1024 * 1024,  # 10MB
    max_redirects: int = 5,
    user_agent: str = "Mozilla/5.0 (compatible; AI-Agent-Platform/1.0)",
) -> FetchResult:
    """Fetch content from a URL with async HTTP GET.
    
    Features:
    - Streaming response with size limit enforcement
    - Follows redirects (up to max_redirects)
    - Timeout handling
    - Returns raw content and content-type header
    
    Args:
        url: URL to fetch.
        timeout_seconds: Request timeout.
        headers: Optional additional headers.
        max_size_bytes: Maximum response size.
        max_redirects: Maximum redirect count.
        user_agent: User-Agent header value.
    
    Returns:
        FetchResult with content and metadata.
    """
```

#### 2. `extract_text`

```python
def extract_text(
    html_or_text: str,
    content_type: str,
    *,
    include_comments: bool = True,
    include_tables: bool = True,
    include_formatting: bool = False,
    output_format: str = "txt",
) -> str:
    """Extract text from HTML or passthrough for text content.
    
    Uses trafilatura for HTML extraction with configurable options.
    
    Args:
        html_or_text: Raw content (HTML or text).
        content_type: Content-Type header value.
        include_comments: Include comments in extraction.
        include_tables: Include tables in extraction.
        include_formatting: Preserve formatting in extraction.
        output_format: Output format ("txt", "markdown").
    
    Returns:
        Extracted text content.
        
    Behavior:
        - text/plain, text/markdown: passthrough (no extraction)
        - text/html, application/xhtml+xml: trafilatura extraction
        - Other types: attempt text extraction, may return empty
    """
```

#### 3. `normalize_github_url`

```python
def normalize_github_url(url: str) -> str:
    """Convert GitHub blob URL to raw content URL.
    
    Converts:
        https://github.com/user/repo/blob/branch/path
    To:
        https://raw.githubusercontent.com/user/repo/branch/path
    
    Args:
        url: GitHub URL (may be blob or raw).
    
    Returns:
        Raw content URL (unchanged if not a GitHub blob URL).
    """
```

#### 4. `is_private_url`

```python
def is_private_url(url: str) -> bool:
    """Detect if URL points to a private/internal IP address.
    
    Detects:
    - localhost, 127.0.0.1, ::1
    - 10.0.0.0/8 (Class A private)
    - 172.16.0.0/12 (Class B private)
    - 192.168.0.0/16 (Class C private)
    - 169.254.0.0/16 (Link-local)
    - ::/128 (IPv6 loopback)
    - fc00::/7 (IPv6 private)
    
    Args:
        url: URL to check.
    
    Returns:
        True if URL points to private/internal address.
    """
```

#### 5. `truncate_content`

```python
def truncate_content(
    content: str,
    max_chars: int = 100000,
    truncation_marker: str = "... [Content truncated due to size limit]",
) -> str:
    """Truncate content to maximum character count.
    
    Args:
        content: Text to truncate.
        max_chars: Maximum character count.
        truncation_marker: Marker to append when truncated.
    
    Returns:
        Truncated content with marker if truncated.
    """
```

#### 6. `format_gemini_citations`

```python
def format_gemini_citations(
    text: str,
    grounding_chunks: list[dict[str, Any]],
    grounding_supports: list[dict[str, Any]],
) -> str:
    """Format Gemini-style citations with inline markers and source footer.
    
    Args:
        text: Response text from Gemini API.
        grounding_chunks: List of {web: {uri, title}} dicts.
        grounding_supports: List of {segment: {startIndex, endIndex}, groundingChunkIndices} dicts.
    
    Returns:
        Text with [N] citation markers inserted and Sources: footer appended.
        
    Example output:
        The API returns data[1] about the topic[2].
        
        Sources:
        [1] Title (https://example.com)
        [2] Another Title (https://another.com)
    """
```

#### 7. `parse_urls_from_text`

```python
def parse_urls_from_text(text: str) -> tuple[list[str], list[str]]:
    """Parse URLs from text, returning valid URLs and errors.
    
    Extracts URLs that appear to be http:// or https:// URLs,
    validates them, and returns both valid URLs and error messages
    for invalid/malformed URLs.
    
    Args:
        text: Text containing URLs.
    
    Returns:
        Tuple of (valid_urls, error_messages).
    """
```

## Constants

```python
# Default timeouts and limits
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_CHARS = 100000

# User agents
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; AI-Agent-Platform/1.0)"
BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Truncation
TRUNCATION_MARKER = "... [Content truncated due to size limit]"
```

## Tests

### HTTP Fetch Tests

1. Successful fetch (200 status)
2. Error responses (404, 500)
3. Redirect following
4. Timeout handling
5. Size limit enforcement
6. Network error handling

### HTML Extraction Tests

1. HTML to text extraction
2. text/plain passthrough
3. text/markdown passthrough
4. Empty content handling
5. Extraction options (comments, tables, formatting)

### URL Helper Tests

1. GitHub URL normalization
2. Private IP detection
3. URL parsing from text

### Truncation Tests

1. Content under limit (no truncation)
2. Content over limit (truncation with marker)

## Mock HTTP Server

Create a test fixture with aiohttp test server:

```python
# tests/conftest.py
import pytest
from aiohttp import web

@pytest.fixture
async def mock_http_server(aiohttp_server):
    """Mock HTTP server for testing fetch operations."""
    app = web.Application()
    
    async def html_handler(request):
        return web.Response(
            text="<html><body><p>Test content</p></body></html>",
            content_type="text/html",
        )
    
    async def text_handler(request):
        return web.Response(
            text="Plain text content",
            content_type="text/plain",
        )
    
    async def markdown_handler(request):
        return web.Response(
            text="# Title\n\nMarkdown content",
            content_type="text/markdown",
        )
    
    async def error_404_handler(request):
        return web.Response(status=404, text="Not found")
    
    async def error_500_handler(request):
        return web.Response(status=500, text="Internal error")
    
    async def large_handler(request):
        # Returns content larger than default max_size
        return web.Response(text="x" * (20 * 1024 * 1024))
    
    async def redirect_handler(request):
        # Redirect to /html
        raise web.HTTPFound("/html")
    
    app.router.add_get("/html", html_handler)
    app.router.add_get("/text", text_handler)
    app.router.add_get("/markdown", markdown_handler)
    app.router.add_get("/404", error_404_handler)
    app.router.add_get("/500", error_500_handler)
    app.router.add_get("/large", large_handler)
    app.router.add_get("/redirect", redirect_handler)
    
    return await aiohttp_server(app)
```

## Requirements Checklist

- [ ] Create package structure with pyproject.toml
- [ ] Implement `fetch_url` async function
- [ ] Implement `extract_text` function with trafilatura
- [ ] Implement `normalize_github_url` function
- [ ] Implement `is_private_url` function
- [ ] Implement `truncate_content` function
- [ ] Implement `format_gemini_citations` function
- [ ] Implement `parse_urls_from_text` function
- [ ] Create mock HTTP server fixture
- [ ] Add tests for all functions
- [ ] Create README.md with usage documentation

## Key Files

| File | Purpose |
|------|---------|
| `plugins/web-fetch-shared/pyproject.toml` | Package definition |
| `plugins/web-fetch-shared/src/web_fetch_shared/__init__.py` | Public exports |
| `plugins/web-fetch-shared/src/web_fetch_shared/web_fetch_engine.py` | Core implementation |
| `plugins/web-fetch-shared/tests/test_web_fetch_engine.py` | Unit tests |
| `plugins/web-fetch-shared/tests/conftest.py` | Test fixtures |

## Notes

- This package is a library dependency, NOT a plugin package
- No `agent_plugin.json` file
- No LLM-related code - all LLM calls happen in vendor tools via context
- Async-first design for HTTP operations
- Trafilatura is the primary extraction engine (used by Kimi and feature-web-context)
