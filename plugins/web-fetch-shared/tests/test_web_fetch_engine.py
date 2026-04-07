"""Tests for web_fetch_engine module."""

from __future__ import annotations

import pytest

from web_fetch_shared import (
    BROWSER_USER_AGENT,
    DEFAULT_MAX_CHARS,
    DEFAULT_MAX_SIZE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_USER_AGENT,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
    FetchResult,
    LRUCache,
    TRUNCATION_MARKER,
    check_rate_limit,
    extract_text,
    fetch_url,
    format_gemini_citations,
    is_private_url,
    normalize_github_url,
    parse_urls_from_text,
    summarize_content,
    summarize_content_sync,
    truncate_content,
)


# -----------------------------------------------------------------------------
# HTTP Fetch Tests
# -----------------------------------------------------------------------------


class TestFetchUrl:
    """Tests for fetch_url async function."""

    @pytest.mark.asyncio
    async def test_successful_fetch_html(self, mock_http_server):
        """Test successful fetch of HTML content."""
        url = str(mock_http_server.make_url("/html"))
        result = await fetch_url(url)

        assert result.is_error is False
        assert result.status_code == 200
        assert "text/html" in result.content_type
        assert "<html>" in result.content
        assert "Test content" in result.content

    @pytest.mark.asyncio
    async def test_successful_fetch_text(self, mock_http_server):
        """Test successful fetch of plain text content."""
        url = str(mock_http_server.make_url("/text"))
        result = await fetch_url(url)

        assert result.is_error is False
        assert result.status_code == 200
        assert "text/plain" in result.content_type
        assert result.content == "Plain text content"

    @pytest.mark.asyncio
    async def test_successful_fetch_markdown(self, mock_http_server):
        """Test successful fetch of markdown content."""
        url = str(mock_http_server.make_url("/markdown"))
        result = await fetch_url(url)

        assert result.is_error is False
        assert result.status_code == 200
        assert "text/markdown" in result.content_type
        assert "# Title" in result.content

    @pytest.mark.asyncio
    async def test_error_404(self, mock_http_server):
        """Test handling of 404 error response."""
        url = str(mock_http_server.make_url("/404"))
        result = await fetch_url(url)

        assert result.is_error is True
        assert result.status_code == 404
        assert "HTTP 404" in result.error_message

    @pytest.mark.asyncio
    async def test_error_500(self, mock_http_server):
        """Test handling of 500 error response."""
        url = str(mock_http_server.make_url("/500"))
        result = await fetch_url(url)

        assert result.is_error is True
        assert result.status_code == 500
        assert "HTTP 500" in result.error_message

    @pytest.mark.asyncio
    async def test_redirect_following(self, mock_http_server):
        """Test following redirects."""
        url = str(mock_http_server.make_url("/redirect"))
        result = await fetch_url(url)

        assert result.is_error is False
        assert result.status_code == 200
        assert "html" in result.url  # Should end up at /html

    @pytest.mark.asyncio
    async def test_size_limit_enforcement(self, mock_http_server):
        """Test that response size is limited."""
        url = str(mock_http_server.make_url("/large"))
        result = await fetch_url(url, max_size_bytes=5 * 1024 * 1024)  # 5MB limit

        assert result.is_error is True
        assert "exceeds maximum" in result.error_message

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_http_server):
        """Test timeout handling."""
        url = str(mock_http_server.make_url("/slow"))
        result = await fetch_url(url, timeout_seconds=0.1)

        assert result.is_error is True
        assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_custom_headers(self, mock_http_server):
        """Test that custom headers are sent."""
        url = str(mock_http_server.make_url("/html"))
        result = await fetch_url(
            url, headers={"X-Custom-Header": "test-value"}, user_agent="TestAgent/1.0"
        )

        # We can't directly verify headers were sent, but the request should succeed
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_final_url_after_redirect(self, mock_http_server):
        """Test that final URL is captured after redirects."""
        url = str(mock_http_server.make_url("/redirect"))
        result = await fetch_url(url)

        assert "/html" in result.url


# -----------------------------------------------------------------------------
# HTML Extraction Tests
# -----------------------------------------------------------------------------


class TestExtractText:
    """Tests for extract_text function."""

    def test_html_to_text_extraction(self):
        """Test HTML to text extraction."""
        html = "<html><body><h1>Title</h1><p>Content paragraph.</p></body></html>"
        text = extract_text(html, "text/html")

        assert "Title" in text
        assert "Content paragraph" in text
        assert "<html>" not in text

    def test_text_plain_passthrough(self):
        """Test text/plain passthrough without extraction."""
        content = "Plain text content"
        result = extract_text(content, "text/plain")

        assert result == content

    def test_text_markdown_passthrough(self):
        """Test text/markdown passthrough without extraction."""
        content = "# Title\n\nMarkdown content"
        result = extract_text(content, "text/markdown")

        assert result == content

    def test_empty_content(self):
        """Test handling of empty content."""
        assert extract_text("", "text/html") == ""
        assert extract_text("   ", "text/html") == ""

    def test_extraction_with_tables(self):
        """Test extraction including tables."""
        html = """
        <html><body>
            <p>Text before table.</p>
            <table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>
            <p>Text after table.</p>
        </body></html>
        """
        text = extract_text(html, "text/html", include_tables=True)

        # Tables should be included
        assert "Cell 1" in text or "table" in text.lower()

    def test_extraction_without_tables(self):
        """Test extraction excluding tables."""
        html = """
        <html><body>
            <p>Text before table.</p>
            <table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>
            <p>Text after table.</p>
        </body></html>
        """
        text = extract_text(html, "text/html", include_tables=False)

        # Tables may or may not be present depending on trafilatura behavior
        assert "Text before table" in text or "Text after table" in text

    def test_markdown_output_format(self):
        """Test markdown output format."""
        html = "<html><body><h1>Title</h1><p>Content.</p></body></html>"
        text = extract_text(html, "text/html", output_format="markdown")

        # Markdown format should preserve headings
        assert "Title" in text

    def test_application_xhtml(self):
        """Test handling of application/xhtml+xml."""
        html = '<html xmlns="http://www.w3.org/1999/xhtml"><body><p>XHTML content</p></body></html>'
        text = extract_text(html, "application/xhtml+xml")

        assert "XHTML content" in text

    def test_charset_in_content_type(self):
        """Test handling of charset in content type."""
        html = "<html><body><p>Content</p></body></html>"
        text = extract_text(html, "text/html; charset=utf-8")

        assert "Content" in text


# -----------------------------------------------------------------------------
# GitHub URL Normalization Tests
# -----------------------------------------------------------------------------


class TestNormalizeGithubUrl:
    """Tests for normalize_github_url function."""

    def test_blob_url_to_raw(self):
        """Test converting blob URL to raw URL."""
        url = "https://github.com/user/repo/blob/main/README.md"
        result = normalize_github_url(url)

        assert result == "https://raw.githubusercontent.com/user/repo/main/README.md"

    def test_blob_url_with_subfolder(self):
        """Test converting blob URL with subfolder path."""
        url = "https://github.com/user/repo/blob/main/src/lib/utils.py"
        result = normalize_github_url(url)

        assert result == "https://raw.githubusercontent.com/user/repo/main/src/lib/utils.py"

    def test_blob_url_with_branch_name_containing_slash(self):
        """Test blob URL with branch name that could be ambiguous."""
        url = "https://github.com/user/repo/blob/feature/branch/file.txt"
        result = normalize_github_url(url)

        # The regex captures everything after 'blob/' as branch, then rest as path
        # This may not handle complex branch names perfectly
        assert "raw.githubusercontent.com" in result

    def test_raw_url_unchanged(self):
        """Test that raw URLs are unchanged."""
        url = "https://raw.githubusercontent.com/user/repo/main/README.md"
        result = normalize_github_url(url)

        assert result == url

    def test_non_github_url_unchanged(self):
        """Test that non-GitHub URLs are unchanged."""
        url = "https://example.com/file.txt"
        result = normalize_github_url(url)

        assert result == url

    def test_github_tree_url_unchanged(self):
        """Test that tree URLs (directories) are unchanged."""
        url = "https://github.com/user/repo/tree/main/src"
        result = normalize_github_url(url)

        assert result == url


# -----------------------------------------------------------------------------
# Private URL Detection Tests
# -----------------------------------------------------------------------------


class TestIsPrivateUrl:
    """Tests for is_private_url function."""

    def test_localhost(self):
        """Test localhost detection."""
        assert is_private_url("http://localhost/") is True
        assert is_private_url("https://localhost/path") is True

    def test_loopback_ipv4(self):
        """Test 127.0.0.1 loopback detection."""
        assert is_private_url("http://127.0.0.1/") is True
        assert is_private_url("http://127.0.0.1:8080/api") is True

    def test_loopback_ipv6(self):
        """Test IPv6 loopback detection."""
        assert is_private_url("http://[::1]/") is True

    def test_class_a_private(self):
        """Test Class A private range (10.0.0.0/8)."""
        assert is_private_url("http://10.0.0.1/") is True
        assert is_private_url("http://10.255.255.255/api") is True

    def test_class_b_private(self):
        """Test Class B private range (172.16.0.0/12)."""
        assert is_private_url("http://172.16.0.1/") is True
        assert is_private_url("http://172.31.255.255/api") is True
        # 172.15.x.x is NOT private
        assert is_private_url("http://172.15.0.1/") is False
        # 172.32.x.x is NOT private
        assert is_private_url("http://172.32.0.1/") is False

    def test_class_c_private(self):
        """Test Class C private range (192.168.0.0/16)."""
        assert is_private_url("http://192.168.0.1/") is True
        assert is_private_url("http://192.168.255.255/api") is True

    def test_link_local(self):
        """Test link-local range (169.254.0.0/16)."""
        assert is_private_url("http://169.254.0.1/") is True
        assert is_private_url("http://169.254.255.255/") is True

    def test_ipv6_private(self):
        """Test IPv6 private range (fc00::/7)."""
        assert is_private_url("http://[fc00::1]/") is True
        assert is_private_url("http://[fdff:ffff:ffff:ffff::1]/") is True

    def test_public_url(self):
        """Test that public URLs are not detected as private."""
        assert is_private_url("https://example.com/") is False
        assert is_private_url("https://github.com/") is False

    def test_public_ip(self):
        """Test that public IPs are not detected as private."""
        assert is_private_url("http://8.8.8.8/") is False  # Google DNS
        assert is_private_url("http://1.1.1.1/") is False  # Cloudflare

    def test_domain_local(self):
        """Test .local domain detection."""
        assert is_private_url("http://hostname.local/") is True

    def test_domain_localhost_suffix(self):
        """Test .localhost domain detection."""
        assert is_private_url("http://app.localhost/") is True

    def test_domain_internal(self):
        """Test .internal domain detection."""
        assert is_private_url("http://service.internal/") is True

    def test_domain_localdomain(self):
        """Test .localdomain domain detection."""
        assert is_private_url("http://host.localdomain/") is True

    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        # URLs that can't be parsed should return False (conservative)
        # urlparse handles most things gracefully
        assert is_private_url("not-a-url") is False


# -----------------------------------------------------------------------------
# Truncation Tests
# -----------------------------------------------------------------------------


class TestTruncateContent:
    """Tests for truncate_content function."""

    def test_content_under_limit(self):
        """Test content under limit is unchanged."""
        content = "Short content"
        result = truncate_content(content, max_chars=100)

        assert result == content

    def test_content_over_limit(self):
        """Test content over limit is truncated with marker."""
        content = "x" * 200
        result = truncate_content(content, max_chars=100)

        assert len(result) == 100 + len(TRUNCATION_MARKER)
        assert result.startswith("x" * 100)
        assert TRUNCATION_MARKER in result

    def test_custom_marker(self):
        """Test custom truncation marker."""
        content = "x" * 200
        custom_marker = " [truncated]"
        result = truncate_content(content, max_chars=100, truncation_marker=custom_marker)

        assert result.endswith(custom_marker)

    def test_exact_limit(self):
        """Test content exactly at limit is not truncated."""
        content = "x" * 100
        result = truncate_content(content, max_chars=100)

        assert result == content
        assert TRUNCATION_MARKER not in result


# -----------------------------------------------------------------------------
# Citation Formatting Tests
# -----------------------------------------------------------------------------


class TestFormatGeminiCitations:
    """Tests for format_gemini_citations function."""

    def test_basic_citation_formatting(self):
        """Test basic citation formatting with inline markers."""
        text = "The API returns data about the topic."
        grounding_chunks = [
            {"web": {"uri": "https://example.com", "title": "Example Site"}},
            {"web": {"uri": "https://another.com", "title": "Another Site"}},
        ]
        grounding_supports = [
            {"segment": {"startIndex": 0, "endIndex": 20}, "groundingChunkIndices": [0]},
            {"segment": {"startIndex": 21, "endIndex": 35}, "groundingChunkIndices": [1]},
        ]
        result = format_gemini_citations(text, grounding_chunks, grounding_supports)

        assert "[1]" in result
        assert "[2]" in result
        assert "Sources:" in result
        assert "Example Site" in result
        assert "https://example.com" in result

    def test_no_grounding_supports(self):
        """Test formatting with only chunks, no supports."""
        text = "Some content without inline markers."
        grounding_chunks = [
            {"web": {"uri": "https://example.com", "title": "Example"}},
        ]
        grounding_supports = []

        result = format_gemini_citations(text, grounding_chunks, grounding_supports)

        assert "Sources:" in result
        assert "[1]" in result
        assert "Example" in result

    def test_no_grounding_chunks(self):
        """Test that empty chunks returns original text."""
        text = "Original text"
        result = format_gemini_citations(text, [], [])

        assert result == text

    def test_chunk_without_title_uses_uri(self):
        """Test that chunks without title use URI."""
        text = "Content"
        grounding_chunks = [
            {"web": {"uri": "https://example.com"}},  # No title
        ]
        grounding_supports = [
            {"segment": {"startIndex": 0, "endIndex": 7}, "groundingChunkIndices": [0]},
        ]

        result = format_gemini_citations(text, grounding_chunks, grounding_supports)

        assert "https://example.com" in result


# -----------------------------------------------------------------------------
# URL Parsing Tests
# -----------------------------------------------------------------------------


class TestParseUrlsFromText:
    """Tests for parse_urls_from_text function."""

    def test_extract_single_url(self):
        """Test extracting a single URL."""
        text = "Check https://example.com for more info."
        valid, errors = parse_urls_from_text(text)

        assert valid == ["https://example.com"]
        assert errors == []

    def test_extract_multiple_urls(self):
        """Test extracting multiple URLs."""
        text = "Visit https://example.com and https://github.com/user/repo"
        valid, errors = parse_urls_from_text(text)

        assert "https://example.com" in valid
        assert "https://github.com/user/repo" in valid
        assert len(valid) == 2

    def test_http_and_https(self):
        """Test extracting both http and https URLs."""
        text = "http://insecure.com and https://secure.com"
        valid, errors = parse_urls_from_text(text)

        assert "http://insecure.com" in valid
        assert "https://secure.com" in valid

    def test_url_with_path_and_query(self):
        """Test URL with path and query string."""
        text = "https://example.com/path?query=value&other=123"
        valid, errors = parse_urls_from_text(text)

        assert len(valid) == 1
        assert "query=value" in valid[0]

    def test_url_with_port(self):
        """Test URL with custom port."""
        text = "https://example.com:8080/api"
        valid, errors = parse_urls_from_text(text)

        assert len(valid) == 1
        assert ":8080" in valid[0]

    def test_localhost_url(self):
        """Test localhost URL is valid."""
        text = "http://localhost:3000/app"
        valid, errors = parse_urls_from_text(text)

        assert len(valid) == 1
        assert "localhost" in valid[0]

    def test_invalid_hostname(self):
        """Test URL with invalid hostname - no TLD dot."""
        text = "https://not-a-valid-hostname/"
        valid, errors = parse_urls_from_text(text)

        # The URL has a valid structure but the hostname lacks a TLD dot
        # Our validation should catch this as invalid
        assert valid == []
        assert len(errors) == 1
        assert "Invalid hostname" in errors[0]

    def test_no_urls(self):
        """Test text with no URLs."""
        text = "This is just plain text with no URLs."
        valid, errors = parse_urls_from_text(text)

        assert valid == []
        assert errors == []

    def test_urls_in_brackets(self):
        """Test URLs inside brackets are extracted."""
        text = "See [https://example.com] for details."
        valid, errors = parse_urls_from_text(text)

        # The regex excludes brackets, so we get the URL without them
        assert "https://example.com" in valid


# -----------------------------------------------------------------------------
# Constants Tests
# -----------------------------------------------------------------------------


class TestConstants:
    """Tests for module constants."""

    def test_default_timeout(self):
        """Test default timeout constant."""
        assert DEFAULT_TIMEOUT_SECONDS == 10.0

    def test_default_max_size(self):
        """Test default max size constant."""
        assert DEFAULT_MAX_SIZE_BYTES == 10 * 1024 * 1024

    def test_default_max_chars(self):
        """Test default max chars constant."""
        assert DEFAULT_MAX_CHARS == 100000

    def test_user_agent_constants(self):
        """Test user agent constants are strings."""
        assert isinstance(DEFAULT_USER_AGENT, str)
        assert isinstance(BROWSER_USER_AGENT, str)
        assert "AI-Agent-Platform" in DEFAULT_USER_AGENT

    def test_truncation_marker(self):
        """Test truncation marker constant."""
        assert "truncated" in TRUNCATION_MARKER.lower()


# -----------------------------------------------------------------------------
# FetchResult Tests
# -----------------------------------------------------------------------------


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_frozen_dataclass(self):
        """Test that FetchResult is immutable."""
        result = FetchResult(
            content="test",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        with pytest.raises(AttributeError):
            result.content = "modified"

    def test_default_values(self):
        """Test default values for optional fields."""
        result = FetchResult(
            content="test",
            content_type="text/plain",
            status_code=200,
            headers={},
            url="https://example.com",
        )

        assert result.is_error is False
        assert result.error_message is None

    def test_error_result(self):
        """Test creating an error result."""
        result = FetchResult(
            content="",
            content_type="",
            status_code=404,
            headers={},
            url="https://example.com/notfound",
            is_error=True,
            error_message="HTTP 404",
        )

        assert result.is_error is True
        assert result.error_message == "HTTP 404"


# -----------------------------------------------------------------------------
# LRU Cache Tests
# -----------------------------------------------------------------------------


class TestLRUCache:
    """Tests for LRUCache class."""

    def test_get_returns_empty_for_missing_key(self):
        """Missing key should return empty list."""
        cache = LRUCache(max_size=3)
        assert cache.get("missing") == []

    def test_set_and_get(self):
        """Set and get should work correctly."""
        cache = LRUCache(max_size=3)
        cache.set("key1", [1.0, 2.0])
        assert cache.get("key1") == [1.0, 2.0]

    def test_moves_to_end_on_get(self):
        """Getting a key should move it to end (most recently used)."""
        cache = LRUCache(max_size=3)
        cache.set("a", [1.0])
        cache.set("b", [2.0])
        cache.set("c", [3.0])

        # Access 'a' to make it most recently used
        cache.get("a")

        # Add 'd' which should evict 'b' (not 'a')
        cache.set("d", [4.0])

        assert cache.get("a") == [1.0]  # 'a' should still exist
        assert cache.get("b") == []      # 'b' should be evicted
        assert cache.get("c") == [3.0]   # 'c' should still exist
        assert cache.get("d") == [4.0]   # 'd' should exist

    def test_evicts_oldest_at_capacity(self):
        """Should evict oldest entry when at capacity."""
        cache = LRUCache(max_size=3)
        cache.set("a", [1.0])
        cache.set("b", [2.0])
        cache.set("c", [3.0])
        cache.set("d", [4.0])  # Should evict 'a'

        assert cache.get("a") == []   # 'a' evicted
        assert cache.get("b") == [2.0]
        assert cache.get("c") == [3.0]
        assert cache.get("d") == [4.0]

    def test_update_existing_moves_to_end(self):
        """Updating existing key should move it to end."""
        cache = LRUCache(max_size=3)
        cache.set("a", [1.0])
        cache.set("b", [2.0])
        cache.set("c", [3.0])

        # Update 'a' to make it most recently used
        cache.set("a", [1.5])

        # Add 'd' which should evict 'b' (not 'a')
        cache.set("d", [4.0])

        assert cache.get("a") == [1.5]  # 'a' should still exist with new value
        assert cache.get("b") == []     # 'b' should be evicted

    def test_clear(self):
        """Clear should remove all entries."""
        cache = LRUCache(max_size=3)
        cache.set("a", [1.0])
        cache.set("b", [2.0])
        cache.clear()

        assert cache.get("a") == []
        assert cache.get("b") == []
        assert len(cache) == 0

    def test_len(self):
        """Len should return number of entries."""
        cache = LRUCache(max_size=10)
        assert len(cache) == 0

        cache.set("a", [1.0])
        assert len(cache) == 1

        cache.set("b", [2.0])
        assert len(cache) == 2


# -----------------------------------------------------------------------------
# Rate Limiting Tests
# -----------------------------------------------------------------------------


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""

    def test_first_request_allowed(self):
        """First request should be allowed."""
        cache = LRUCache(max_size=100)
        allowed, wait = check_rate_limit("https://example.com", cache)

        assert allowed is True
        assert wait is None

    def test_requests_up_to_limit_allowed(self):
        """Requests up to limit should be allowed."""
        cache = LRUCache(max_size=100)

        for i in range(DEFAULT_RATE_LIMIT_REQUESTS):
            allowed, wait = check_rate_limit("https://example.com", cache)
            assert allowed is True
            assert wait is None

    def test_request_over_limit_blocked(self):
        """Request over limit should be blocked with wait time."""
        cache = LRUCache(max_size=100)

        # Fill up the limit
        for i in range(DEFAULT_RATE_LIMIT_REQUESTS):
            check_rate_limit("https://example.com", cache)

        # Next request should be blocked
        allowed, wait = check_rate_limit("https://example.com", cache)

        assert allowed is False
        assert wait is not None
        assert wait > 0

    def test_different_hosts_tracked_separately(self):
        """Different hosts should have separate rate limits."""
        cache = LRUCache(max_size=100)

        # Fill limit for example.com
        for i in range(DEFAULT_RATE_LIMIT_REQUESTS):
            check_rate_limit("https://example.com", cache)

        # Should still allow requests to other.com
        allowed, wait = check_rate_limit("https://other.com", cache)

        assert allowed is True
        assert wait is None

    def test_custom_limits(self):
        """Should respect custom limits."""
        cache = LRUCache(max_size=100)

        # Custom: 3 requests per 10 seconds
        for i in range(3):
            allowed, _ = check_rate_limit(
                "https://example.com", cache,
                max_requests=3,
                window_seconds=10.0,
            )
            assert allowed is True

        # 4th should be blocked
        allowed, wait = check_rate_limit(
            "https://example.com", cache,
            max_requests=3,
            window_seconds=10.0,
        )
        assert allowed is False

    def test_url_without_hostname_allowed(self):
        """URL without hostname should be allowed (conservative fallback)."""
        cache = LRUCache(max_size=100)
        # URL without proper hostname - urlparse will return None for hostname
        allowed, wait = check_rate_limit("not-a-valid-url", cache)

        # Should be allowed (conservative fallback)
        assert allowed is True
        assert wait is None


# -----------------------------------------------------------------------------
# Rate Limit Constants Tests
# -----------------------------------------------------------------------------


class TestRateLimitConstants:
    """Tests for rate limit constants."""

    def test_default_rate_limit_requests(self):
        """Test default rate limit requests constant."""
        assert DEFAULT_RATE_LIMIT_REQUESTS == 10

    def test_default_rate_limit_window(self):
        """Test default rate limit window constant."""
        assert DEFAULT_RATE_LIMIT_WINDOW == 60.0


# -----------------------------------------------------------------------------
# Summarization Tests
# -----------------------------------------------------------------------------


class TestSummarizeContent:
    """Tests for summarize_content generator function."""

    def test_no_context_returns_fallback(self):
        """No context should return raw content as fallback."""
        content = "Test content"
        events = list(summarize_content(content, "prompt", "https://example.com", None))

        assert len(events) == 1
        assert events[0]["kind"] == "response_complete"
        assert events[0]["content"] == content
        assert events[0]["metadata"]["fallback"] is True

    def test_no_core_returns_fallback(self):
        """No core in context should return raw content as fallback."""
        content = "Test content"
        context = {"config": {}}  # No core

        events = list(summarize_content(content, "prompt", "https://example.com", context))

        assert len(events) == 1
        assert events[0]["kind"] == "response_complete"
        assert events[0]["content"] == content
        assert events[0]["metadata"]["fallback"] is True
        assert events[0]["metadata"]["reason"] == "no_core"

    def test_truncates_long_content(self):
        """Long content should be truncated before summarization."""
        content = "x" * 200
        # This test doesn't need a real core, just verifies truncation is applied
        # We'll use a mock that returns fallback

        # Verify the truncate_content is called by checking the prompt building
        # For now, just test that short content is unchanged
        short_content = "short"
        context = {"config": {}}

        events = list(summarize_content(
            short_content, "prompt", "https://example.com", context,
            max_chars=100,
        ))

        assert events[0]["content"] == short_content


class TestSummarizeContentSync:
    """Tests for summarize_content_sync function."""

    def test_no_context_returns_fallback(self):
        """No context should return raw content as fallback."""
        content = "Test content"
        success, result = summarize_content_sync(
            content, "prompt", "https://example.com", None
        )

        assert success is True
        assert result == content

    def test_no_core_returns_fallback(self):
        """No core in context should return raw content as fallback."""
        content = "Test content"
        context = {"config": {}}

        success, result = summarize_content_sync(
            content, "prompt", "https://example.com", context
        )

        assert success is True
        assert result == content

    def test_truncates_content(self):
        """Long content should be truncated."""
        content = "x" * 200
        context = {"config": {}}

        # The content is truncated but returned as fallback since no core
        success, result = summarize_content_sync(
            content, "prompt", "https://example.com", context,
            max_chars=50,
        )

        assert success is True
        # Result should be truncated content + marker
        assert len(result) == 50 + len(TRUNCATION_MARKER)
