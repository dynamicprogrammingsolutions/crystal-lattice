"""Web fetch shared utilities for vendor tool packages.

This package provides reusable HTTP fetching and HTML extraction helpers
for implementing vendor-specific web fetch tools (Gemini, Qwen, Kimi, etc.).

This is a library package, NOT a plugin package.
"""

from .web_fetch_engine import (
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

__all__ = [
    "BROWSER_USER_AGENT",
    "DEFAULT_MAX_CHARS",
    "DEFAULT_MAX_SIZE_BYTES",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_USER_AGENT",
    "FetchResult",
    "TRUNCATION_MARKER",
    "extract_text",
    "fetch_url",
    "format_gemini_citations",
    "is_private_url",
    "normalize_github_url",
    "parse_urls_from_text",
    "truncate_content",
]
