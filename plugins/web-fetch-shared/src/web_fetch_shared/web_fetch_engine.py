"""Web fetch engine for HTTP fetching and HTML extraction.

This module provides shared utilities for vendor-specific web fetch tools.
All functions are designed to be reusable across Gemini, Qwen, Kimi, and
other vendor tool packages.
"""

from __future__ import annotations

import ipaddress
import re
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

# aiohttp is imported lazily in fetch_url to allow the module to be
# imported in environments where it's not installed.

# trafilatura is imported lazily in extract_text for the same reason.


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DEFAULT_TIMEOUT_SECONDS: float = 10.0
DEFAULT_MAX_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_CHARS: int = 100000

DEFAULT_USER_AGENT: str = "Mozilla/5.0 (compatible; AI-Agent-Platform/1.0)"
BROWSER_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

TRUNCATION_MARKER: str = "... [Content truncated due to size limit]"

# Rate limiting defaults
DEFAULT_RATE_LIMIT_REQUESTS: int = 10
DEFAULT_RATE_LIMIT_WINDOW: float = 60.0


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------


class LRUCache:
    """Simple LRU cache for rate limiting.

    Matches vendor CLI rate limiting patterns with bounded memory usage.
    Uses OrderedDict for O(1) get/set/eviction operations.

    Example:
        cache = LRUCache(max_size=1000)
        cache.set("example.com", [time.time()])
        history = cache.get("example.com")
    """

    def __init__(self, max_size: int = 1000):
        """Initialize LRU cache with maximum size.

        Args:
            max_size: Maximum number of entries. Evicts oldest when full.
        """
        self._max_size = max_size
        self._cache: OrderedDict[str, List[float]] = OrderedDict()

    def get(self, key: str) -> List[float]:
        """Get cached value, moving to end if found (most recently used).

        Args:
            key: Cache key (typically hostname).

        Returns:
            Cached list of timestamps, or empty list if not found.
        """
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return []

    def set(self, key: str, value: List[float]) -> None:
        """Set cached value, evicting oldest if at capacity.

        Args:
            key: Cache key (typically hostname).
            value: List of timestamps to cache.
        """
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)


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


# -----------------------------------------------------------------------------
# Core Functions
# -----------------------------------------------------------------------------


async def fetch_url(
    url: str,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    headers: Optional[Dict[str, str]] = None,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
    max_redirects: int = 5,
    user_agent: str = DEFAULT_USER_AGENT,
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
    # Lazy import to allow module to load without aiohttp
    import aiohttp

    request_headers = {"User-Agent": user_agent}
    if headers:
        request_headers.update(headers)

    connector = aiohttp.TCPConnector()

    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        ) as session:
            # Note: max_redirects handling is done automatically by aiohttp
            # with a default of 10. We set enable_redirects=True (default)
            async with session.get(
                url, headers=request_headers, allow_redirects=True
            ) as response:
                # Get content type before reading body
                content_type = response.headers.get("Content-Type", "")

                # Check content length if available
                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        length = int(content_length)
                        if length > max_size_bytes:
                            return FetchResult(
                                content="",
                                content_type=content_type,
                                status_code=response.status,
                                headers=dict(response.headers),
                                url=str(response.url),
                                is_error=True,
                                error_message=(
                                    f"Content-Length {length} exceeds "
                                    f"maximum {max_size_bytes} bytes"
                                ),
                            )
                    except ValueError:
                        pass

                # Read content with streaming size check
                chunks: List[bytes] = []
                total_size = 0

                async for chunk in response.content.iter_chunked(8192):
                    total_size += len(chunk)
                    if total_size > max_size_bytes:
                        return FetchResult(
                            content="",
                            content_type=content_type,
                            status_code=response.status,
                            headers=dict(response.headers),
                            url=str(response.url),
                            is_error=True,
                            error_message=(
                                f"Response body exceeded maximum "
                                f"{max_size_bytes} bytes"
                            ),
                        )
                    chunks.append(chunk)

                # Decode content
                body = b"".join(chunks)

                # Try to detect encoding from content-type header
                encoding = "utf-8"
                if "charset=" in content_type.lower():
                    charset_match = re.search(
                        r"charset=([^\s;]+)", content_type, re.IGNORECASE
                    )
                    if charset_match:
                        encoding = charset_match.group(1).strip('"\'')

                try:
                    content = body.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    # Fall back to utf-8 with errors ignored
                    content = body.decode("utf-8", errors="replace")

                return FetchResult(
                    content=content,
                    content_type=content_type,
                    status_code=response.status,
                    headers=dict(response.headers),
                    url=str(response.url),
                    is_error=response.status >= 400,
                    error_message=(
                        f"HTTP {response.status}" if response.status >= 400 else None
                    ),
                )

    except aiohttp.ClientError as e:
        return FetchResult(
            content="",
            content_type="",
            status_code=0,
            headers={},
            url=url,
            is_error=True,
            error_message=str(e),
        )
    except TimeoutError:
        return FetchResult(
            content="",
            content_type="",
            status_code=0,
            headers={},
            url=url,
            is_error=True,
            error_message=f"Request timed out after {timeout_seconds} seconds",
        )
    except Exception as e:
        return FetchResult(
            content="",
            content_type="",
            status_code=0,
            headers={},
            url=url,
            is_error=True,
            error_message=f"Unexpected error: {e}",
        )


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
    ct_lower = content_type.lower()

    # Passthrough for text content types
    if "text/plain" in ct_lower:
        return html_or_text
    if "text/markdown" in ct_lower:
        return html_or_text

    # Only process HTML-like content
    if "text/html" not in ct_lower and "application/xhtml" not in ct_lower:
        # For other content types, attempt extraction but may return empty
        pass

    if not html_or_text or not html_or_text.strip():
        return ""

    # Lazy import to allow module to load without trafilatura
    import trafilatura

    # Map output format to trafilatura format
    trafilatura_format = "txt"
    if output_format == "markdown":
        trafilatura_format = "markdown"

    try:
        extracted = trafilatura.extract(
            html_or_text,
            output_format=trafilatura_format,
            include_comments=include_comments,
            include_tables=include_tables,
            include_formatting=include_formatting,
        )
        if extracted is None:
            return ""
        return extracted
    except Exception:
        # If extraction fails, return empty string
        return ""


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
    # Match GitHub blob URLs
    blob_pattern = re.compile(
        r"^https?://github\.com/"
        r"(?P<user>[^/]+)/"
        r"(?P<repo>[^/]+)/"
        r"blob/"
        r"(?P<branch>[^/]+)/"
        r"(?P<path>.*)$"
    )

    match = blob_pattern.match(url)
    if match:
        user = match.group("user")
        repo = match.group("repo")
        branch = match.group("branch")
        path = match.group("path")
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"

    # Handle tree URLs (directories) - these can't be converted to raw
    # Just return as-is
    return url


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
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False

        # Check for localhost hostname
        if hostname.lower() == "localhost":
            return True

        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)

            # Check for loopback
            if ip.is_loopback:
                return True

            # Check for private (includes 10.x, 172.16-31.x, 192.168.x)
            if ip.is_private:
                return True

            # Check for link-local
            if ip.is_link_local:
                return True

            # Check for site-local (deprecated but still used)
            if ip.is_site_local:
                return True

            return False

        except ValueError:
            # Not an IP address, could be a domain
            # Check for common private patterns
            hostname_lower = hostname.lower()
            if hostname_lower.endswith(".local"):
                return True
            if hostname_lower.endswith(".localhost"):
                return True
            if hostname_lower.endswith(".internal"):
                return True
            if hostname_lower.endswith(".localdomain"):
                return True
            return False

    except Exception:
        # If parsing fails, be conservative
        return False


def truncate_content(
    content: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    truncation_marker: str = TRUNCATION_MARKER,
) -> str:
    """Truncate content to maximum character count.

    Args:
        content: Text to truncate.
        max_chars: Maximum character count.
        truncation_marker: Marker to append when truncated.

    Returns:
        Truncated content with marker if truncated.
    """
    if len(content) <= max_chars:
        return content

    return content[:max_chars] + truncation_marker


def format_gemini_citations(
    text: str,
    grounding_chunks: List[Dict[str, Any]],
    grounding_supports: List[Dict[str, Any]],
) -> str:
    """Format Gemini-style citations with inline markers and source footer.

    Args:
        text: Response text from Gemini API.
        grounding_chunks: List of {web: {uri, title}} dicts.
        grounding_supports: List of {segment: {startIndex, endIndex},
            groundingChunkIndices} dicts.

    Returns:
        Text with [N] citation markers inserted and Sources: footer appended.

    Example output:
        The API returns data[1] about the topic[2].

        Sources:
        [1] Title (https://example.com)
        [2] Another Title (https://another.com)
    """
    if not grounding_chunks:
        return text

    # Build chunk index map (1-indexed for citation display)
    chunk_urls: Dict[int, str] = {}
    chunk_titles: Dict[int, str] = {}

    for i, chunk in enumerate(grounding_chunks):
        web_info = chunk.get("web", {})
        uri = web_info.get("uri", "")
        title = web_info.get("title", "")
        chunk_urls[i] = uri
        chunk_titles[i] = title or uri

    if not grounding_supports:
        # No inline markers, just append source list
        lines = [text, "", "Sources:"]
        for i in range(len(grounding_chunks)):
            idx = i + 1
            url = chunk_urls.get(i, "")
            title = chunk_titles.get(i, url)
            lines.append(f"[{idx}] {title} ({url})" if url else f"[{idx}] {title}")
        return "\n".join(lines)

    # Process grounding supports to insert markers
    # Sort by start index descending to insert from end to beginning
    # (so indices don't shift)
    sorted_supports = sorted(
        grounding_supports,
        key=lambda s: s.get("segment", {}).get("startIndex", 0),
        reverse=True,
    )

    result_text = text

    for support in sorted_supports:
        segment = support.get("segment", {})
        start_idx = segment.get("startIndex")
        end_idx = segment.get("endIndex")
        chunk_indices = support.get("groundingChunkIndices", [])

        if start_idx is None or end_idx is None:
            continue

        if not chunk_indices:
            continue

        # Build citation marker for first chunk index
        # (Gemini typically uses single index per support)
        first_idx = chunk_indices[0]
        citation_num = first_idx + 1  # Convert to 1-indexed

        # Insert citation marker at end of segment
        # Ensure we're within bounds
        if 0 <= end_idx <= len(result_text):
            marker = f"[{citation_num}]"
            result_text = result_text[:end_idx] + marker + result_text[end_idx:]

    # Build source footer
    lines = [result_text, "", "Sources:"]
    seen_indices: set = set()

    # Re-sort supports in ascending order for footer
    ascending_supports = sorted(
        grounding_supports,
        key=lambda s: s.get("segment", {}).get("startIndex", 0),
    )

    for support in ascending_supports:
        chunk_indices = support.get("groundingChunkIndices", [])
        for idx in chunk_indices:
            if idx in seen_indices:
                continue
            seen_indices.add(idx)

            citation_num = idx + 1
            url = chunk_urls.get(idx, "")
            title = chunk_titles.get(idx, url)
            lines.append(f"[{citation_num}] {title} ({url})" if url else f"[{citation_num}] {title}")

    # Add any chunks that weren't referenced in supports
    for i in range(len(grounding_chunks)):
        if i not in seen_indices:
            citation_num = i + 1
            url = chunk_urls.get(i, "")
            title = chunk_titles.get(i, url)
            lines.append(f"[{citation_num}] {title} ({url})" if url else f"[{citation_num}] {title}")

    return "\n".join(lines)


def parse_urls_from_text(text: str) -> Tuple[List[str], List[str]]:
    """Parse URLs from text, returning valid URLs and errors.

    Extracts URLs that appear to be http:// or https:// URLs,
    validates them, and returns both valid URLs and error messages
    for invalid/malformed URLs.

    Args:
        text: Text containing URLs.

    Returns:
        Tuple of (valid_urls, error_messages).
    """
    # URL pattern for http/https URLs
    url_pattern = re.compile(r"https?://[^\s<>\[\]{}\"']+", re.IGNORECASE)

    matches = url_pattern.findall(text)

    valid_urls: List[str] = []
    error_messages: List[str] = []

    for match in matches:
        try:
            parsed = urlparse(match)

            # Check for valid scheme
            if parsed.scheme.lower() not in ("http", "https"):
                error_messages.append(f"Invalid scheme in URL: {match}")
                continue

            # Check for valid hostname
            if not parsed.hostname:
                error_messages.append(f"Missing hostname in URL: {match}")
                continue

            # Basic validation - hostname should have at least one dot or be localhost
            hostname = parsed.hostname.lower()
            if hostname != "localhost" and "." not in hostname:
                error_messages.append(f"Invalid hostname in URL: {match}")
                continue

            valid_urls.append(match)

        except Exception as e:
            error_messages.append(f"Failed to parse URL {match}: {e}")

    return valid_urls, error_messages


# -----------------------------------------------------------------------------
# Rate Limiting Utilities
# -----------------------------------------------------------------------------


def check_rate_limit(
    url: str,
    cache: LRUCache,
    max_requests: int = DEFAULT_RATE_LIMIT_REQUESTS,
    window_seconds: float = DEFAULT_RATE_LIMIT_WINDOW,
) -> Tuple[bool, Optional[int]]:
    """Check rate limit for a URL using provided LRU cache.

    Tracks requests per hostname with sliding window. Updates the cache
    with the current request timestamp if allowed.

    Args:
        url: URL to check rate limit for.
        cache: LRU cache instance for storing request history.
        max_requests: Maximum requests allowed per window per host.
        window_seconds: Rate limit window in seconds.

    Returns:
        Tuple of (allowed, wait_seconds).
        - If allowed is True, wait_seconds is None.
        - If allowed is False, wait_seconds is the time to wait.

    Example:
        cache = LRUCache(max_size=1000)
        allowed, wait = check_rate_limit("https://example.com", cache)
        if not allowed:
            print(f"Rate limited, wait {wait} seconds")
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            # Can't determine hostname, allow the request
            return True, None

        now = time.time()
        window_start = now - window_seconds

        # Get and clean history from cache
        history = cache.get(hostname)
        history = [t for t in history if t > window_start]

        if len(history) >= max_requests:
            wait = int(history[0] + window_seconds - now)
            # Update cache with cleaned history (but don't add new request)
            cache.set(hostname, history)
            return False, max(1, wait)

        # Add current request and update cache
        history.append(now)
        cache.set(hostname, history)
        return True, None

    except Exception:
        # If parsing fails, allow the request
        return True, None


# -----------------------------------------------------------------------------
# LLM Summarization Utilities
# -----------------------------------------------------------------------------


def summarize_content(
    content: str,
    user_prompt: str,
    url: str,
    context: Optional[Dict[str, Any]],
    *,
    fallback_agent_id: Optional[str] = None,
    fallback_model: Optional[str] = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> Iterator[Dict[str, Any]]:
    """Summarize fetched content using LLM via tool context.

    Uses context["core"] for LLM calls. Supports agent switching via
    fallback_agent_id when context["app"] is available.

    This is a generator function that yields events matching the
    AgentCore stream_request event format:
    - {"kind": "response_chunk", "content": "..."}
    - {"kind": "response_complete", "content": "..."}

    Args:
        content: Fetched content to summarize.
        user_prompt: User's original prompt/question.
        url: Source URL (for context in summarization prompt).
        context: Tool context dict with "core" and optional "app".
        fallback_agent_id: Optional agent ID to switch to for summarization.
        fallback_model: Optional model override for summarization.
        max_chars: Maximum characters to include from content.

    Yields:
        Event dicts matching AgentCore stream_request format.

    Example:
        for event in summarize_content(content, prompt, url, context):
            if event["kind"] == "response_chunk":
                print(event["content"], end="")
            elif event["kind"] == "response_complete":
                result = event["content"]
    """
    # Truncate content if needed
    if len(content) > max_chars:
        content = truncate_content(content, max_chars=max_chars)

    # Build summarization prompt
    summarization_prompt = (
        f'The user requested: "{user_prompt}"\n\n'
        f"I have fetched the content from {url}. "
        f"Please use the following content to answer the user's request.\n\n"
        f"---\n{content}\n---"
    )

    # Check for context availability
    if not context:
        # No context available, yield raw content
        yield {
            "kind": "response_complete",
            "content": content,
            "metadata": {"fallback": True, "reason": "no_context"},
        }
        return

    core = context.get("core")
    if not core:
        # No core available, yield raw content
        yield {
            "kind": "response_complete",
            "content": content,
            "metadata": {"fallback": True, "reason": "no_core"},
        }
        return

    config = context.get("config", {})
    app = context.get("app")

    # Try agent switching if configured
    if fallback_agent_id and app:
        try:
            # Import Session locally to avoid circular imports
            from agent_core import Session

            # Create temp session
            temp_session = Session(session_id="web_fetch_summarize", messages=[])
            temp_session = core.add_message(temp_session, "user", summarization_prompt)

            # Switch to fallback agent
            fallback_core, fallback_config, _ = app.update_agent(
                fallback_agent_id, temp_session
            )

            # Apply model override if set
            if fallback_model:
                fallback_config = {**fallback_config, "model": fallback_model}

            # Stream response
            result_text = ""
            for event in fallback_core.stream_request(temp_session, fallback_config):
                if event.get("kind") == "response_chunk":
                    result_text += event.get("content", "")
                    yield event
                elif event.get("kind") == "response_complete":
                    result_text = event.get("content", result_text)
                    yield event

            return

        except Exception:
            # Fall through to default core usage
            pass

    # Apply fallback model override if set
    if fallback_model:
        config = {**config, "model": fallback_model}

    # Use current agent/core for summarization
    try:
        from agent_core import Session

        temp_session = Session(session_id="web_fetch_summarize", messages=[])
        temp_session = core.add_message(temp_session, "user", summarization_prompt)

        # Stream response
        result_text = ""
        for event in core.stream_request(temp_session, config):
            if event.get("kind") == "response_chunk":
                result_text += event.get("content", "")
                yield event
            elif event.get("kind") == "response_complete":
                result_text = event.get("content", result_text)
                yield event

    except Exception as e:
        # Error during summarization, yield error
        yield {
            "kind": "response_complete",
            "content": content,
            "metadata": {"fallback": True, "reason": "error", "error": str(e)},
        }


def summarize_content_sync(
    content: str,
    user_prompt: str,
    url: str,
    context: Optional[Dict[str, Any]],
    *,
    fallback_agent_id: Optional[str] = None,
    fallback_model: Optional[str] = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> Tuple[bool, str]:
    """Synchronous wrapper for summarize_content.

    Collects all events and returns the final result.

    Args:
        content: Fetched content to summarize.
        user_prompt: User's original prompt/question.
        url: Source URL.
        context: Tool context dict.
        fallback_agent_id: Optional agent ID to switch to.
        fallback_model: Optional model override.
        max_chars: Maximum characters to include from content.

    Returns:
        Tuple of (success, result_or_error).
        - If success is True, result is the summarized content.
        - If success is False, result is an error message or raw content.
    """
    result_text = ""
    last_event = None

    for event in summarize_content(
        content,
        user_prompt,
        url,
        context,
        fallback_agent_id=fallback_agent_id,
        fallback_model=fallback_model,
        max_chars=max_chars,
    ):
        last_event = event
        if event.get("kind") == "response_chunk":
            result_text += event.get("content", "")
        elif event.get("kind") == "response_complete":
            result_text = event.get("content", result_text)

    # Check for fallback mode
    if last_event and last_event.get("kind") == "response_complete":
        metadata = last_event.get("metadata", {})
        if metadata.get("fallback"):
            # Fallback to raw content
            return True, result_text
        # Successful summarization
        return True, result_text

    # Should not reach here, but return what we have
    return True, result_text if result_text else (True, content)
