# web-fetch-shared

Shared HTTP fetch and HTML extraction helpers for vendor web fetch tools.

This is a **library package**, not a plugin package. It provides reusable components for implementing vendor-specific web fetch tools (Gemini, Qwen, Kimi, etc.).

## Installation

```bash
pip install -e .
```

## Dependencies

- `aiohttp>=3.8.0` - Async HTTP client
- `trafilatura>=1.6.0` - HTML-to-text extraction

## Usage

### Fetch URL

```python
from web_fetch_shared import fetch_url, FetchResult

result = await fetch_url("https://example.com")
if not result.is_error:
    print(result.content)
```

### Extract Text from HTML

```python
from web_fetch_shared import extract_text

html = "<html><body><p>Hello world</p></body></html>"
text = extract_text(html, "text/html")
print(text)  # "Hello world"
```

### URL Helpers

```python
from web_fetch_shared import normalize_github_url, is_private_url, parse_urls_from_text

# Convert GitHub blob URL to raw content URL
raw_url = normalize_github_url("https://github.com/user/repo/blob/main/README.md")
# Returns: https://raw.githubusercontent.com/user/repo/main/README.md

# Check if URL points to private IP
is_private = is_private_url("http://192.168.1.1/internal")
# Returns: True

# Parse URLs from text
valid, errors = parse_urls_from_text("Check https://example.com and http://[invalid")
```

### Content Utilities

```python
from web_fetch_shared import truncate_content, format_gemini_citations

# Truncate long content
truncated = truncate_content(long_text, max_chars=1000)

# Format Gemini grounding citations
formatted = format_gemini_citations(text, grounding_chunks, grounding_supports)
```

## API Reference

### `FetchResult`

Dataclass representing a URL fetch result.

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | Fetched content |
| `content_type` | `str` | Content-Type header |
| `status_code` | `int` | HTTP status code |
| `headers` | `Dict[str, str]` | Response headers |
| `url` | `str` | Final URL after redirects |
| `is_error` | `bool` | Whether this is an error |
| `error_message` | `Optional[str]` | Error message if `is_error` |

### `fetch_url()`

```python
async def fetch_url(
    url: str,
    *,
    timeout_seconds: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
    max_size_bytes: int = 10 * 1024 * 1024,
    max_redirects: int = 5,
    user_agent: str = "Mozilla/5.0 (compatible; AI-Agent-Platform/1.0)",
) -> FetchResult
```

### `extract_text()`

```python
def extract_text(
    html_or_text: str,
    content_type: str,
    *,
    include_comments: bool = True,
    include_tables: bool = True,
    include_formatting: bool = False,
    output_format: str = "txt",
) -> str
```

### `normalize_github_url()`

```python
def normalize_github_url(url: str) -> str
```

### `is_private_url()`

```python
def is_private_url(url: str) -> bool
```

### `truncate_content()`

```python
def truncate_content(
    content: str,
    max_chars: int = 100000,
    truncation_marker: str = "... [Content truncated due to size limit]",
) -> str
```

### `format_gemini_citations()`

```python
def format_gemini_citations(
    text: str,
    grounding_chunks: list[dict[str, Any]],
    grounding_supports: list[dict[str, Any]],
) -> str
```

### `parse_urls_from_text()`

```python
def parse_urls_from_text(text: str) -> tuple[list[str], list[str]]
```

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_TIMEOUT_SECONDS` | `10.0` | Default fetch timeout |
| `DEFAULT_MAX_SIZE_BYTES` | `10 * 1024 * 1024` | Default max response size (10MB) |
| `DEFAULT_MAX_CHARS` | `100000` | Default truncation limit |
| `TRUNCATION_MARKER` | `"... [Content truncated due to size limit]"` | Default truncation marker |

## License

This directory is available under the [Apache License 2.0](../../LICENSE).
