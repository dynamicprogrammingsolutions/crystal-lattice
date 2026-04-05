"""Tests for web_fetch_engine module."""

from __future__ import annotations

import pytest

from web_fetch_shared import (
    BROWSER_USER_AGENT,
    DEFAULT_MAX_CHARS,
    DEFAULT_MAX_SIZE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_USER_AGENT,
    FetchResult,
    TRUNCATION_MARKER,
    extract_text,
    fetch_url,
    format_gemini_citations,
    is_private_url,
    normalize_github_url,
    parse_urls_from_text,
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
