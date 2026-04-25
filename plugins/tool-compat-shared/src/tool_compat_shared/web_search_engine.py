"""Web search engine for shared search provider infrastructure.

This module provides reusable search data models, provider protocol,
and concrete provider implementations (Tavily, Gemini API) for
vendor-specific web search tool plugins.

Engine vs Shape principle:
    This module is the ENGINE — it returns structured data (SearchResponse,
    SearchResult). It does NOT format results for LLM consumption.
    All formatting (citation markers, source footers, truncation banners,
    result numbering) belongs in vendor tool plugins.

Known precedent violations:
    The existing reader_engine.py and search_engine.py in this package
    export vendor-specific formatting functions (format_gemini_*,
    format_qwen_*, build_qwen_truncation_wrapper). This module does NOT
    follow that pattern. It returns raw structured data only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class SearchResult:
    """Common search result data model across vendors.

    Vendors use different subsets of fields:
    - Gemini: title, url (from grounding_chunks)
    - Qwen: title, url, snippet (as content), score, date
    - Kimi: title, url, snippet, content, date, site_name
    - Tavily: title, url, content, score, date

    Future configurable tools can use whatever subset they need.
    All fields have defaults so vendors only set what they need.
    """

    title: str
    url: str
    snippet: str = ""
    content: str = ""  # Full page content (Kimi include_content, Tavily content)
    date: str = ""  # Published/fetched date (Kimi date, Qwen publishedDate, Tavily published_date)
    site_name: str = ""  # Source site name (Kimi)
    score: float = 0.0  # Relevance score 0.0-1.0 (Qwen, Tavily)


@dataclass(frozen=True)
class SearchResponse:
    """Wrapper for search provider responses.

    Contains the list of results plus optional metadata
    that applies to the entire response (not individual results).
    Vendor plugins decide how to present each field.
    """

    results: List[SearchResult]
    answer: str = ""  # AI-generated answer (Tavily include_answer, Gemini API)
    query: str = ""  # Original query (for reference)
    grounding_chunks: List[Dict[str, Any]] = field(default_factory=list)
    grounding_supports: List[Dict[str, Any]] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


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
        original_error: Optional[Exception] = None,
    ):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"[{provider_name}] {message}")


# -----------------------------------------------------------------------------
# Provider Protocol
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Tavily Provider
# -----------------------------------------------------------------------------


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
    _API_URL = "https://api.tavily.com/search"

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
        """Check if Tavily API key is configured."""
        return bool(self._api_key)

    async def search(self, query: str, *, limit: int = 5) -> SearchResponse:
        """Execute search via Tavily API.

        Args:
            query: Search query string.
            limit: Maximum results to return (mapped to max_results).

        Returns:
            SearchResponse with results and optional AI answer.

        Raises:
            SearchProviderError: On API failure or missing key.
        """
        if not self.is_available():
            raise SearchProviderError(
                self.name, "API key is not configured"
            )

        # Lazy import aiohttp
        import aiohttp

        request_body = {
            "api_key": self._api_key,
            "query": query,
            "search_depth": self._search_depth,
            "max_results": limit,
            "include_answer": self._include_answer,
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self._API_URL,
                    json=request_body,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        text = await response.text(errors="replace")
                        raise SearchProviderError(
                            self.name,
                            f"API error: {response.status} {response.reason}"
                            + (f" - {text}" if text else ""),
                        )

                    try:
                        data = await response.json()
                    except Exception as parse_err:
                        raise SearchProviderError(
                            self.name,
                            f"Failed to parse API response: {parse_err}",
                            original_error=parse_err,
                        )

        except SearchProviderError:
            raise
        except Exception as err:
            raise SearchProviderError(
                self.name,
                f"Request failed: {err}",
                original_error=err,
            )

        # Parse results
        raw_results = data.get("results", [])
        results: List[SearchResult] = []
        for item in raw_results:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=float(item.get("score", 0.0)),
                    date=item.get("published_date", ""),
                )
            )

        answer = data.get("answer", "") or ""
        if isinstance(answer, str):
            answer = answer.strip()

        return SearchResponse(
            results=results,
            answer=answer,
            query=query,
        )


# -----------------------------------------------------------------------------
# Gemini API Provider
# -----------------------------------------------------------------------------


class GeminiApiProvider:
    """Gemini API search provider using server-side Google Search grounding.

    Uses the google-genai SDK to perform searches via Gemini's built-in
    Google Search grounding tool. The provider calls a Gemini model with
    the ``googleSearch`` tool enabled, which returns grounded content
    with source metadata (grounding chunks) and citation positions
    (grounding supports with UTF-8 byte offsets).

    Returns the response text, grounding chunks (source metadata), and
    grounding supports (citation byte-offset positions) as structured
    data. Vendor plugins handle citation marker insertion and formatting.

    Configuration via constructor:
        api_key: Gemini API key (required)
        model: Gemini model name (default: "gemini-2.5-flash")

    The ``googleSearch`` tool is automatically included in the API call
    to enable grounding. The API returns:
    - Response text with grounded content
    - grounding_chunks: source metadata [{web: {uri, title}}]
    - grounding_supports: citation positions [{segment: {startIndex, endIndex},
      groundingChunkIndices}] where indices are UTF-8 byte offsets

    Response mapping:
        response text                    → SearchResponse.answer
        grounding_chunks[].web.title     → SearchResult.title
        grounding_chunks[].web.uri       → SearchResult.url
        grounding_supports               → SearchResponse.grounding_supports
        grounding_chunks                 → SearchResponse.grounding_chunks
    """

    name: str = "Gemini API"
    _DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(
        self,
        api_key: str,
        *,
        model: Optional[str] = None,
    ):
        self._api_key = api_key
        self._model = model or self._DEFAULT_MODEL

    def is_available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self._api_key)

    async def search(self, query: str, *, limit: int = 5) -> SearchResponse:
        """Execute search via Gemini API with Google Search grounding.

        Args:
            query: Search query string.
            limit: Ignored — Gemini API controls result count internally.

        Returns:
            SearchResponse with answer text, grounding chunks as results,
            and raw grounding metadata for vendor-side citation formatting.

        Raises:
            SearchProviderError: On API failure or missing key.
        """
        if not self.is_available():
            raise SearchProviderError(
                self.name, "API key is not configured"
            )

        try:
            # Lazy import google-genai
            from google import genai

            client = genai.Client(api_key=self._api_key)
            response = client.models.generate_content(
                model=self._model,
                contents=query,
                config=genai.types.GenerateContentConfig(
                    tools=[genai.types.Tool(google_search=genai.types.GoogleSearch())],
                ),
            )

        except ImportError as err:
            raise SearchProviderError(
                self.name,
                "google-genai SDK not installed",
                original_error=err,
            )
        except Exception as err:
            raise SearchProviderError(
                self.name,
                f"API request failed: {err}",
                original_error=err,
            )

        # Extract response text
        response_text = ""
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    response_text += part.text

        # Extract grounding metadata
        grounding_chunks: List[Dict[str, Any]] = []
        grounding_supports: List[Dict[str, Any]] = []

        if response.candidates:
            candidate = response.candidates[0]
            if (
                hasattr(candidate, "grounding_metadata")
                and candidate.grounding_metadata
            ):
                gm = candidate.grounding_metadata
                if hasattr(gm, "grounding_chunks"):
                    grounding_chunks = [
                        {"web": {"uri": c.web.uri, "title": c.web.title}}
                        for c in gm.grounding_chunks
                        if hasattr(c, "web") and c.web
                    ]
                if hasattr(gm, "grounding_supports"):
                    grounding_supports = [
                        {
                            "segment": {
                                "startIndex": s.segment.start_index,
                                "endIndex": s.segment.end_index,
                            },
                            "groundingChunkIndices": list(
                                s.grounding_chunk_indices
                            ),
                        }
                        for s in gm.grounding_supports
                        if hasattr(s, "segment")
                        and hasattr(s, "grounding_chunk_indices")
                    ]

        # Build SearchResult list from grounding chunks
        results: List[SearchResult] = []
        for chunk in grounding_chunks:
            web_info = chunk.get("web", {})
            results.append(
                SearchResult(
                    title=web_info.get("title", ""),
                    url=web_info.get("uri", ""),
                )
            )

        return SearchResponse(
            results=results,
            answer=response_text.strip(),
            query=query,
            grounding_chunks=grounding_chunks,
            grounding_supports=grounding_supports,
        )
