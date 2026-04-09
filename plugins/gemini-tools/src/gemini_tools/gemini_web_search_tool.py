"""Gemini-style google_web_search tool implementation.

Primary backend: Gemini API server-side Google Search grounding with
citation insertion at UTF-8 byte offsets (matching Gemini CLI behavior).

Alternative backend: Tavily (from shared tool-compat-shared).
Result format is always Gemini-style regardless of backend.

Configuration keys (all flat, prefixed with web_search_):
- web_search_enabled: Enable the tool (default: False)
- web_search_provider: Search backend: "gemini_api" (default), "tavily"
- tavily_api_key: Tavily API key (for tavily backend)
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Iterator, List, Optional

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    GeminiApiProvider,
    SearchProviderError,
    SearchResponse,
    SearchResult,
    TavilyProvider,
)


# Default backend
DEFAULT_PROVIDER = "gemini_api"


# ---------------------------------------------------------------------------
# UTF-8 byte-offset citation formatting
# ---------------------------------------------------------------------------


def format_gemini_citations_utf8(
    text: str,
    grounding_chunks: List[Dict[str, Any]],
    grounding_supports: List[Dict[str, Any]],
) -> str:
    """Format Gemini-style citations using UTF-8 byte offsets.

    This matches the Gemini CLI's web-search.ts behavior exactly:
    segment indices in groundingSupports are UTF-8 byte positions,
    not character positions. We encode the text to bytes, insert
    citation markers at byte offsets, then decode back.

    Args:
        text: Response text from Gemini API.
        grounding_chunks: List of {web: {uri, title}} dicts.
        grounding_supports: List of {segment: {startIndex, endIndex},
            groundingChunkIndices} dicts with byte-offset positions.

    Returns:
        Text with [N] citation markers inserted and Sources: footer appended.
    """
    if not grounding_chunks:
        return text

    # Build chunk index maps (1-indexed for citation display)
    chunk_urls: Dict[int, str] = {}
    chunk_titles: Dict[int, str] = {}

    for i, chunk in enumerate(grounding_chunks):
        web_info = chunk.get("web", {})
        uri = web_info.get("uri", "")
        title = web_info.get("title", "")
        chunk_urls[i] = uri
        chunk_titles[i] = title or uri

    # No inline markers if no supports — just append source list
    if not grounding_supports:
        lines = [text, "", "Sources:"]
        for i in range(len(grounding_chunks)):
            idx = i + 1
            url = chunk_urls.get(i, "")
            title = chunk_titles.get(i, url)
            lines.append(f"[{idx}] {title} ({url})" if url else f"[{idx}] {title}")
        return "\n".join(lines)

    # Build insertions from grounding supports
    insertions: List[Dict[str, Any]] = []
    for support in grounding_supports:
        segment = support.get("segment", {})
        start_idx = segment.get("startIndex")
        end_idx = segment.get("endIndex")
        chunk_indices = support.get("groundingChunkIndices", [])

        if start_idx is None or end_idx is None or not chunk_indices:
            continue

        # Build citation marker from all chunk indices
        # (Gemini CLI joins multiple indices: [1][2])
        marker = "".join(f"[{idx + 1}]" for idx in chunk_indices)
        insertions.append({"index": end_idx, "marker": marker})

    # Sort insertions by byte index descending (insert from end to start)
    # so earlier byte positions don't shift
    insertions.sort(key=lambda ins: ins["index"], reverse=True)

    # Encode text to UTF-8 bytes and insert markers at byte positions
    # This matches the Gemini CLI's TextEncoder/TextDecoder approach
    response_bytes = text.encode("utf-8")
    parts: List[bytes] = []
    last_index = len(response_bytes)

    for ins in insertions:
        pos = min(ins["index"], last_index)
        # Append the text segment after this insertion point
        parts.insert(0, response_bytes[pos:last_index])
        # Prepend the marker
        parts.insert(0, ins["marker"].encode("utf-8"))
        last_index = pos

    # Prepend remaining text before the first insertion
    parts.insert(0, response_bytes[:last_index])

    # Concatenate all parts
    modified_text = b"".join(parts).decode("utf-8")

    # Build Sources footer
    lines = [modified_text, "", "Sources:"]
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
            lines.append(
                f"[{citation_num}] {title} ({url})"
                if url
                else f"[{citation_num}] {title}"
            )

    # Add any chunks not referenced in supports
    for i in range(len(grounding_chunks)):
        if i not in seen_indices:
            citation_num = i + 1
            url = chunk_urls.get(i, "")
            title = chunk_titles.get(i, url)
            lines.append(
                f"[{citation_num}] {title} ({url})"
                if url
                else f"[{citation_num}] {title}"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------


class GeminiWebSearchTool(ToolPlugin):
    """Gemini-style google_web_search tool.

    Primary: Gemini API server-side Google Search grounding
    with UTF-8 byte-offset citation insertion.
    Alternative: Tavily (from shared providers).
    Result format is always Gemini-style regardless of backend.
    """

    name = "gemini_web_search_tool"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema for web_search tool settings."""
        return {
            "web_search_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable the google_web_search tool",
            },
            "web_search_provider": {
                "type": "string",
                "default": DEFAULT_PROVIDER,
                "description": (
                    'Search backend: "gemini_api" (default, requires Gemini API key), '
                    '"tavily" (requires tavily_api_key)'
                ),
            },
            "tavily_api_key": {
                "type": "string",
                "default": None,
                "description": "Tavily API key (for tavily backend)",
            },
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI schema elements for web_search tool settings."""
        gemini_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        tavily_key = config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY")

        # Build available provider options
        provider_options = []
        if gemini_key:
            provider_options.append(
                {
                    "value": "gemini_api",
                    "label": "Gemini API (Google Search grounding)",
                }
            )
        if tavily_key:
            provider_options.append({"value": "tavily", "label": "Tavily"})

        if not provider_options:
            return [
                {
                    "type": "text",
                    "key": "web_search_enabled",
                    "label": "Web Search (no search provider configured)",
                    "description": (
                        "Set GEMINI_API_KEY or TAVILY_API_KEY to enable"
                    ),
                }
            ]

        elements = [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable web search",
                "description": "Enable the google_web_search tool",
            },
        ]

        if len(provider_options) > 1:
            elements.append(
                {
                    "type": "select",
                    "key": "web_search_provider",
                    "label": "Search provider",
                    "description": "Search backend for web search queries",
                    "options": provider_options,
                }
            )

        return elements

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with configuration."""
        provider_name = config.get("web_search_provider", DEFAULT_PROVIDER)
        providers = self._create_providers(config)

        return {
            "config": config,
            "enabled": config.get("web_search_enabled", False),
            "provider_name": provider_name,
            "providers": providers,
        }

    def _create_providers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create available providers based on configuration.

        Returns dict mapping provider name to provider instance.
        The gemini_api provider uses GeminiApiProvider from shared.
        """
        providers: Dict[str, Any] = {}

        # Gemini API
        gemini_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            providers["gemini_api"] = GeminiApiProvider(api_key=gemini_key)

        # Tavily
        tavily_key = config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            providers["tavily"] = TavilyProvider(api_key=tavily_key)

        return providers

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]],
        models: Optional[List[str]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[bool]:
        """Check if tool should be visible in the tool catalog.

        Returns False only when no provider is configured (no API keys).
        Returns None to fall through to tag checks when at least one
        provider is available — this ensures the UI checkbox is always
        visible so users can toggle web_search_enabled.

        The web_search_enabled flag controls execution, not visibility.
        """
        providers = self._create_providers(config)
        if not providers:
            return False  # No provider configured — hide entirely

        return None  # Fall through to tag checks (tool visible in UI)

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the google_web_search tool schema matching Gemini CLI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "google_web_search",
                    "description": (
                        "Performs a web search using Google Search (via the Gemini API) "
                        "and returns the results. This tool is useful for finding information "
                        "on the internet based on a query."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "The search query to find information on the web."
                                ),
                            }
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the google_web_search tool."""
        if tool_name != "google_web_search":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # Check if enabled
        if not state.get("enabled", False):
            return {
                "success": False,
                "error": (
                    "Web search is disabled. Enable it via web_search_enabled "
                    "configuration."
                ),
            }

        # Validate query
        query = arguments.get("query", "").strip()
        if not query:
            return {
                "success": False,
                "error": "The 'query' parameter cannot be empty.",
            }

        # Select provider
        provider_name = state.get("provider_name", DEFAULT_PROVIDER)
        providers = state.get("providers", {})
        provider = providers.get(provider_name)

        if not provider:
            available = ", ".join(providers.keys()) or "none"
            return {
                "success": False,
                "error": (
                    f"Web search provider '{provider_name}' is not configured. "
                    f"Available providers: {available}. "
                    "Set an API key for at least one provider."
                ),
            }

        # Dispatch to appropriate backend
        async def _run() -> Dict[str, Any]:
            if provider_name == "gemini_api":
                return await self._execute_gemini_api(query, provider)
            else:
                return await self._execute_shared_provider(
                    query, provider, provider_name
                )

        # Handle async execution in both sync and async contexts
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run())
                return future.result()
        except RuntimeError:
            return asyncio.run(_run())

    async def _execute_gemini_api(
        self, query: str, provider: GeminiApiProvider
    ) -> Dict[str, Any]:
        """Execute search using Gemini API with Google Search grounding.

        This is the primary path with grounding metadata and
        UTF-8 byte-offset citation insertion.
        """
        try:
            response: SearchResponse = await provider.search(query)

            # Handle no results
            answer = response.answer.strip() if response.answer else ""
            if not answer and not response.results:
                return {
                    "success": True,
                    "result": (
                        f'No search results or information found for query: '
                        f'"{query}"'
                    ),
                }

            # Format with UTF-8 byte-offset citations
            if response.grounding_chunks:
                formatted = format_gemini_citations_utf8(
                    answer,
                    response.grounding_chunks,
                    response.grounding_supports,
                )
            else:
                formatted = answer

            return {
                "success": True,
                "result": f'Web search results for "{query}":\n\n{formatted}',
            }

        except SearchProviderError as e:
            return {
                "success": False,
                "error": (
                    f'Error during web search for query "{query}": {e}'
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": (
                    f'Error during web search for query "{query}": {e}'
                ),
            }

    async def _execute_shared_provider(
        self,
        query: str,
        provider: Any,
        provider_name: str,
    ) -> Dict[str, Any]:
        """Execute search using a shared provider (Tavily).

        Results are formatted in Gemini-style wrapper with Sources footer.
        No inline citation markers (only Gemini API provides grounding).
        """
        try:
            response: SearchResponse = await provider.search(query, limit=5)

            if not response.results:
                return {
                    "success": True,
                    "result": (
                        f'No search results or information found for query: '
                        f'"{query}"'
                    ),
                }

            # Format in Gemini style: content + Sources footer
            formatted = self._format_shared_results(response.results)

            # Include Tavily's AI answer if present
            if response.answer:
                formatted = f"{response.answer}\n\n{formatted}"

            return {
                "success": True,
                "result": f'Web search results for "{query}":\n\n{formatted}',
            }

        except SearchProviderError as e:
            return {
                "success": False,
                "error": (
                    f'Error during web search for query "{query}": {e}'
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "error": (
                    f'Error during web search for query "{query}": {e}'
                ),
            }

    def _format_shared_results(self, results: List[SearchResult]) -> str:
        """Format shared provider results in Gemini style.

        Gemini-style: content summary + Sources footer.
        No inline citation markers (only Gemini API grounding provides those).
        """
        # Build content summary from top results
        content_parts = []
        for i, r in enumerate(results[:5]):
            content_parts.append(f"{i + 1}. {r.title}")
            if r.snippet:
                content_parts.append(f"   {r.snippet.strip()}")

        content = "\n".join(content_parts)

        # Build Sources footer (Gemini-style)
        sources = []
        for i, r in enumerate(results):
            title = r.title or "Untitled"
            url = r.url
            sources.append(f"[{i + 1}] {title} ({url})")

        return f"{content}\n\nSources:\n" + "\n".join(sources)

    def format_tool_result(
        self, result: Dict[str, Any], state: Dict[str, Any]
    ) -> str:
        """Format the tool result for LLM consumption."""
        if result.get("success"):
            return result.get("result", "")
        return f"Error: {result.get('error', 'Unknown error')}"

    def to_display_format(
        self, text: str, result: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format for display in UI."""
        return {"type": "text", "content": text}
