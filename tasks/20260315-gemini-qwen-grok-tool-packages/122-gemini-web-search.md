# 122 - Gemini Web Search Tool

Short description: Add `google_web_search` tool to `gemini-tools` with configurable search backend. Primary backend uses Gemini API's server-side Google Search grounding with citation formatting. Alternative backends: Tavily, Google Custom Search (from shared providers). Tool shape (name, params, result format) stays Gemini-specific regardless of backend. Disabled by default; errors if enabled without any configured provider.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/121-web-search-shared.md`

## Goal

Implement `GeminiWebSearchTool` that matches Gemini CLI's `google_web_search` tool exactly in shape, with configurable backend:

1. **Tool schema**: name `google_web_search`, single `query` parameter — matches CLI exactly
2. **Primary backend**: Gemini API with `web-search` model alias (citations with UTF-8 byte offsets)
3. **Alternative backends**: Tavily, Google Custom Search (from shared `tool-compat-shared`)
4. **Result format**: Always Gemini-style regardless of backend — `"Web search results for \"query\":\n\n<<content>>\n\nSources:\n[1] Title (url)"`
5. **Backend selection**: Config-driven (`web_search_provider`), no `provider` param in schema
6. **Conditional**: Disabled by default; if enabled without any configured backend, returns error

## Source of Truth

### Gemini CLI Implementation

File: `../gemini-cli/packages/core/src/tools/web-search.ts`

Key behaviors:
1. Calls `geminiClient.generate_content(model='web-search', contents=[{role: 'user', parts: [{text: query}]}])`
2. Extracts `groundingMetadata.groundingChunks` for sources: `{web: {title, uri}}`
3. Extracts `groundingMetadata.groundingSupports` for citation positions: `{segment: {startIndex, endIndex}, groundingChunkIndices}`
4. **Critical**: Citation markers inserted at **UTF-8 byte offsets** (not character offsets)
5. Uses `TextEncoder`/`TextDecoder` to handle multi-byte characters correctly

### Tool Schema

File: `../gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts`

```json
{
  "name": "google_web_search",
  "description": "Performs a web search using Google Search (via the Gemini API) and returns the results. This tool is useful for finding information on the internet based on a query.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query to find information on the web."
      }
    },
    "required": ["query"]
  }
}
```

### Result Formatting

From source tests (`web-search.test.ts`):

**Success with citations:**
```
Web search results for "grounding query":

This is a test[1] response.[1][2]

Sources:
[1] Example Site (https://example.com)
[2] Google (https://google.com)
```

**No results:**
```
No search results or information found for query: "no results query"
```

**Error:**
```
Error during web search for query "error query": <<error message>>
```

## Design: Shape vs Backend

The tool has a fixed **shape** (Gemini CLI-compatible) but configurable **backend**:

| Aspect | Shape (fixed) | Backend (configurable) |
|--------|---------------|----------------------|
| Tool name | `google_web_search` | - |
| Parameters | `query` only | - |
| Description | Gemini CLI description | - |
| Result format | `Web search results for "query":\n\n...` + Sources footer | - |
| Citation markers | `[N]` inline + footer | Only with `gemini_api` backend |
| Search execution | - | `gemini_api` (default), `tavily`, `google` |

When using a non-Gemini backend, the result format still uses the Gemini-style wrapper and Sources footer, but without inline citation markers (since only the Gemini API returns grounding metadata). The Sources footer is built from the provider's result URLs.

## Implementation

### File: `plugins/gemini-tools/src/gemini_tools/gemini_web_search_tool.py`

```python
"""Gemini-style google_web_search tool implementation.

Primary backend: Gemini API server-side Google Search grounding with
automatic citation insertion (UTF-8 byte offsets).

Alternative backends: Tavily, Google Custom Search (from shared providers).
Result format is always Gemini-style regardless of backend.

Configuration keys (all flat, prefixed with web_search_):
- web_search_enabled: Enable the tool (default: False)
- web_search_provider: Search backend: "gemini_api" (default), "tavily", "google"
- tavily_api_key: Tavily API key (for tavily backend)
- google_api_key: Google Custom Search API key (for google backend)
- google_search_engine_id: Google Custom Search Engine ID (for google backend)
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterator, List, Optional

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    SearchResult,
    SearchProviderError,
    TavilyProvider,
    GoogleProvider,
)
from web_fetch_shared import format_gemini_citations  # Already exists


# Default backend
DEFAULT_PROVIDER = "gemini_api"


class GeminiWebSearchTool(ToolPlugin):
    """Gemini-style google_web_search tool.
    
    Primary: Gemini API server-side Google Search grounding.
    Alternatives: Tavily, Google Custom Search (from shared).
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
                    '"tavily" (requires tavily_api_key), '
                    '"google" (requires google_api_key + google_search_engine_id)'
                ),
            },
            "tavily_api_key": {
                "type": "string",
                "default": None,
                "description": "Tavily API key (for tavily backend)",
            },
            "google_api_key": {
                "type": "string",
                "default": None,
                "description": "Google Custom Search API key (for google backend)",
            },
            "google_search_engine_id": {
                "type": "string",
                "default": None,
                "description": "Google Custom Search Engine ID (for google backend)",
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
        google_key = config.get("google_api_key") or os.environ.get("GOOGLE_API_KEY")
        google_cx = config.get("google_search_engine_id") or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        
        # Build available provider options
        provider_options = []
        if gemini_key:
            provider_options.append({"value": "gemini_api", "label": "Gemini API (Google Search grounding)"})
        if tavily_key:
            provider_options.append({"value": "tavily", "label": "Tavily"})
        if google_key and google_cx:
            provider_options.append({"value": "google", "label": "Google Custom Search"})
        
        if not provider_options:
            return [
                {
                    "type": "text",
                    "key": "web_search_enabled",
                    "label": "Web Search (no search provider configured)",
                    "description": "Set GEMINI_API_KEY, TAVILY_API_KEY, or Google API credentials to enable",
                    "disabled": True,
                }
            ]
        
        elements = [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable web search",
            },
        ]
        
        if len(provider_options) > 1:
            elements.append({
                "type": "select",
                "key": "web_search_provider",
                "label": "Search provider",
                "options": provider_options,
            })
        
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
            "gemini_api_key": config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY"),
        }

    def _create_providers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create available providers based on configuration.
        
        Returns dict mapping provider name to provider instance or config.
        The gemini_api provider is special (handled inline, not a SearchProvider).
        """
        providers = {}
        
        # Gemini API (always "available" if key exists, handled inline)
        gemini_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            providers["gemini_api"] = {"type": "gemini_api", "api_key": gemini_key}
        
        # Tavily (from shared)
        tavily_key = config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            providers["tavily"] = TavilyProvider(tavily_key, config)
        
        # Google Custom Search (from shared)
        google_key = config.get("google_api_key") or os.environ.get("GOOGLE_API_KEY")
        google_cx = config.get("google_search_engine_id") or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        if google_key and google_cx:
            providers["google"] = GoogleProvider(google_key, google_cx, config)
        
        return providers

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]],
        models: Optional[List[str]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[bool]:
        """Check if tool is enabled based on configuration.
        
        Returns False if disabled or no provider configured.
        Returns None to fall back to tag checks if enabled with provider.
        """
        enabled = config.get("web_search_enabled", False)
        if not enabled:
            return False
        
        providers = self._create_providers(config)
        if not providers:
            return False  # No provider configured
        
        return None  # Fall through to tag checks

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the google_web_search tool schema matching Gemini CLI."""
        return [{
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
                            "description": "The search query to find information on the web.",
                        }
                    },
                    "required": ["query"],
                },
            }
        }]

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
                "error": "Web search is disabled. Enable it via web_search_enabled configuration.",
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
        if provider_name == "gemini_api" or (isinstance(provider, dict) and provider.get("type") == "gemini_api"):
            return self._execute_gemini_api(query, provider["api_key"])
        else:
            return self._execute_shared_provider(query, provider, provider_name)

    def _execute_gemini_api(self, query: str, api_key: str) -> Dict[str, Any]:
        """Execute search using Gemini API with web-search model.
        
        This is the primary path with grounding metadata and citations.
        """
        try:
            from google import genai
            
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="web-search",
                contents=query,
            )
            
            # Extract response text
            response_text = self._extract_text(response)
            
            # Extract grounding metadata
            grounding_chunks, grounding_supports = self._extract_grounding(response)
            
            # Handle no results
            if not response_text or not response_text.strip():
                return {
                    "success": True,
                    "result": f'No search results or information found for query: "{query}"',
                }
            
            # Format with citations using shared helper
            if grounding_chunks:
                formatted = format_gemini_citations(
                    response_text, grounding_chunks, grounding_supports
                )
            else:
                formatted = response_text
            
            return {
                "success": True,
                "result": f'Web search results for "{query}":\n\n{formatted}',
            }
            
        except ImportError as e:
            return {
                "success": False,
                "error": f"google-genai SDK not installed: {e}",
            }
        except Exception as e:
            error_msg = str(e)
            return {
                "success": False,
                "error": f'Error during web search for query "{query}": {error_msg}',
            }

    def _execute_shared_provider(
        self, 
        query: str, 
        provider: Any, 
        provider_name: str
    ) -> Dict[str, Any]:
        """Execute search using a shared provider (Tavily/Google).
        
        Results are formatted in Gemini-style wrapper with Sources footer.
        No inline citation markers (only Gemini API provides grounding).
        """
        import asyncio
        
        try:
            results = asyncio.run(provider.search(query, limit=5))
            
            if not results:
                return {
                    "success": True,
                    "result": f'No search results or information found for query: "{query}"',
                }
            
            # Format in Gemini style: content + Sources footer
            formatted = self._format_shared_results(results)
            
            return {
                "success": True,
                "result": f'Web search results for "{query}":\n\n{formatted}',
            }
            
        except SearchProviderError as e:
            return {
                "success": False,
                "error": f'Error during web search for query "{query}": {e}',
            }
        except Exception as e:
            return {
                "success": False,
                "error": f'Error during web search for query "{query}": {e}',
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

    def _extract_text(self, response) -> str:
        """Extract text from Gemini response."""
        text = ""
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
        return text

    def _extract_grounding(self, response) -> tuple[list, list]:
        """Extract grounding metadata from response."""
        chunks = []
        supports = []
        
        if response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, "grounding_chunks"):
                    chunks = [
                        {"web": {"uri": c.web.uri, "title": c.web.title}}
                        for c in gm.grounding_chunks
                        if hasattr(c, "web") and c.web
                    ]
                if hasattr(gm, "grounding_supports"):
                    supports = [
                        {
                            "segment": {
                                "startIndex": s.segment.start_index,
                                "endIndex": s.segment.end_index,
                            },
                            "groundingChunkIndices": list(s.grounding_chunk_indices),
                        }
                        for s in gm.grounding_supports
                        if hasattr(s, "segment") and hasattr(s, "grounding_chunk_indices")
                    ]
        
        return chunks, supports

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format the tool result for LLM consumption."""
        if result.get("success"):
            return result.get("result", "")
        return f"Error: {result.get('error', 'Unknown error')}"

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Format for display in UI."""
        return {"type": "text", "content": text}
```

### Package Updates

1. **`__init__.py`**: Add `GeminiWebSearchTool` export
2. **`agent_plugin.json`**: Add entry for tool class
3. **`setup.py`**: Already has `google-genai` and `web-fetch-shared` dependencies

## Test Plan

### Schema Tests

| Test | Expected |
|------|----------|
| Tool name | `google_web_search` |
| Required params | `["query"]` |
| Param type | `query`: string |
| Description matches CLI | Exact match |
| No `provider` param | Schema has only `query` |

### Citation Tests (Gemini API backend only)

| Test | Input | Expected |
|------|-------|----------|
| Basic citation | Single chunk, single support | `[1]` at correct position |
| Multiple citations | Multiple chunks/supports | `[1]`, `[2]`, etc. |
| UTF-8 byte offsets | Multi-byte chars (日本語, emoji) | Markers at byte positions, not char positions |
| No grounding | Empty chunks | Plain text, no Sources footer |

### Result Format Tests (all backends)

| Test | Backend | Expected Format |
|------|---------|-----------------|
| Success with citations | gemini_api | `Web search results for "query":\n\n<<content with [N]>>\n\nSources:\n[1] Title (url)` |
| Success without citations | tavily/google | `Web search results for "query":\n\n1. Title\n   Snippet\n\nSources:\n[1] Title (url)` |
| No results | any | `No search results or information found for query: "query"` |
| Error | any | `Error during web search for query "query": <<error>>` |

### Provider Selection Tests

| Test | Config | Expected Backend |
|------|--------|------------------|
| Default with Gemini key | `{gemini_api_key: "key"}` | gemini_api |
| Explicit tavily | `{web_search_provider: "tavily", tavily_api_key: "key"}` | tavily |
| Explicit google | `{web_search_provider: "google", google_api_key+cx: ...}` | google |
| Fallback: no Gemini key but Tavily | `{tavily_api_key: "key"}` | tavily |
| Unavailable provider | `{web_search_provider: "tavily"}` (no key) | Error |

### Conditional Tests

| Test | Config | Expected |
|------|--------|----------|
| Disabled by default | `{}` | `is_enabled()` returns False |
| Enabled with Gemini key | `{web_search_enabled: True, gemini_api_key: "key"}` | `is_enabled()` returns None |
| Enabled with Tavily key | `{web_search_enabled: True, tavily_api_key: "key"}` | `is_enabled()` returns None |
| Enabled without any key | `{web_search_enabled: True}` | `is_enabled()` returns False |

## Deliverables

1. `plugins/gemini-tools/src/gemini_tools/gemini_web_search_tool.py`
2. Updated `plugins/gemini-tools/src/gemini_tools/__init__.py`
3. Updated `plugins/gemini-tools/agent_plugin.json`
4. Tests in `plugins/gemini-tools/tests/test_gemini_web_search_tool.py`

## Status: TODO
