# 124 - Kimi Web Search Tool

Short description: Add `SearchWeb` tool to `kimi-tools` with configurable search backend. Primary backend uses Moonshot Search API with optional page crawling. Alternative backends: Tavily, Google Custom Search (from shared providers). Tool shape (name, params, result format) stays Kimi-specific regardless of backend. Disabled by default; errors if enabled without any configured provider.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/121-web-search-shared.md`

## Goal

Implement `KimiWebSearchTool` that matches Kimi CLI's `SearchWeb` tool exactly in shape, with configurable backend:

1. **Tool schema**: name `SearchWeb`, params `query`, `limit` (1-20), `include_content` (bool) — matches CLI exactly
2. **Primary backend**: Moonshot Search API with server-side page crawling
3. **Alternative backends**: Tavily, Google Custom Search (from shared `tool-compat-shared`)
4. **Result format**: Always Kimi-specific Title/Date/URL/Summary format regardless of backend
5. **Backend selection**: Config-driven (`web_search_provider`), no provider param in schema
6. **Conditional**: Disabled by default; if enabled without any configured backend, returns error

## Source of Truth

### Kimi CLI Implementation

File: `../kimi-cli/src/kimi_cli/tools/web/search.py`

Key behaviors:
1. Checks `config.services.moonshot_search` - raises `SkipThisTool` if None
2. POST to `moonshot_search.base_url` with JSON body
3. Request body: `{"text_query": query, "limit": limit, "enable_page_crawling": include_content, "timeout_seconds": 30}`
4. Headers: `Authorization: Bearer {api_key}`, `X-Msh-Tool-Call-Id: {tool_call_id}`
5. Response parsed into `SearchResult` model with fields: `site_name`, `title`, `url`, `snippet`, `content`, `date`, `icon`, `mime`

### Tool Schema

File: `../kimi-cli/src/kimi_cli/tools/web/search.py`

```python
class Params(BaseModel):
    query: str = Field(description="The query text to search for.")
    limit: int = Field(
        description=(
            "The number of results to return. "
            "Typically you do not need to set this value. "
            "When the results do not contain what you need, "
            "you probably want to give a more concrete query."
        ),
        default=5,
        ge=1,
        le=20,
    )
    include_content: bool = Field(
        description=(
            "Whether to include the content of the web pages in the results. "
            "It can consume a large amount of tokens when this is set to True. "
            "You should avoid enabling this when `limit` is set to a large value."
        ),
        default=False,
    )

class SearchWeb(CallableTool2[Params]):
    name: str = "SearchWeb"
    description: str = load_desc(Path(__file__).parent / "search.md", {})
```

Description from `search.md`:
```
WebSearch tool allows you to search on the internet to get latest information, including news, documents, release notes, blog posts, papers, etc.
```

### Result Formatting

From `search.py`:

```python
for i, result in enumerate(results):
    if i > 0:
        builder.write("---\n\n")
    builder.write(
        f"Title: {result.title}\nDate: {result.date}\n"
        f"URL: {result.url}\nSummary: {result.snippet}\n\n"
    )
    if result.content:
        builder.write(f"{result.content}\n\n")
```

### Error Messages

- Not configured: `"Search service is not configured. You may want to try other methods to search."`
- API failure: `"Failed to search. Status: N. This may indicates that the search service is currently unavailable."`

## Design: Shape vs Backend

The tool has a fixed **shape** (Kimi CLI-compatible) but configurable **backend**:

| Aspect | Shape (fixed) | Backend (configurable) |
|--------|---------------|----------------------|
| Tool name | `SearchWeb` | - |
| Parameters | `query`, `limit`, `include_content` | - |
| Description | Kimi CLI description | - |
| Result format | Title/Date/URL/Summary + `---\n\n` separator | - |
| Page crawling | `include_content` param | Only with `moonshot` backend |
| Search execution | - | `moonshot` (default), `tavily`, `google` |

When using a non-Moonshot backend, the result format stays Kimi-style (Title/Date/URL/Summary). The `include_content` parameter is only meaningful for the Moonshot backend (server-side crawling); for other backends, it's accepted but has no effect (no server-side crawling available).

## Implementation

### File: `plugins/kimi-tools/src/kimi_tools/kimi_web_search_tool.py`

```python
"""Kimi-style SearchWeb tool implementation.

Primary backend: Moonshot Search API with optional server-side page crawling.
Alternative backends: Tavily, Google Custom Search (from shared providers).
Result format is always Kimi-specific regardless of backend.

Configuration keys:
- web_search_enabled: Enable the tool (default: False)
- web_search_provider: Search backend: "moonshot" (default), "tavily", "google"
- services.moonshot_search.base_url: Moonshot Search API URL
- services.moonshot_search.api_key: Moonshot API key
- services.moonshot_search.oauth: OAuth reference for key resolution
- services.moonshot_search.custom_headers: Additional headers
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


# Default backend
DEFAULT_PROVIDER = "moonshot"


class KimiWebSearchTool(ToolPlugin):
    """Kimi-style SearchWeb tool.
    
    Primary: Moonshot Search API with optional page content crawling.
    Alternatives: Tavily, Google Custom Search (from shared).
    Result format is always Kimi-specific regardless of backend.
    """
    
    name = "kimi_web_search_tool"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema for web_search tool settings."""
        return {
            "web_search_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable the SearchWeb tool",
            },
            "web_search_provider": {
                "type": "string",
                "default": DEFAULT_PROVIDER,
                "description": (
                    'Search backend: "moonshot" (default, requires Moonshot config), '
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
        moonshot = config.get("services", {}).get("moonshot_search")
        tavily_key = config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY")
        google_key = config.get("google_api_key") or os.environ.get("GOOGLE_API_KEY")
        google_cx = config.get("google_search_engine_id") or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        
        # Build available provider options
        provider_options = []
        if moonshot:
            provider_options.append({"value": "moonshot", "label": "Moonshot Search"})
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
                    "description": "Configure Moonshot search, Tavily, or Google credentials to enable",
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
        moonshot = config.get("services", {}).get("moonshot_search")
        
        return {
            "config": config,
            "enabled": config.get("web_search_enabled", False),
            "provider_name": provider_name,
            "providers": providers,
            "moonshot_config": moonshot,
        }

    def _create_providers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create available providers based on configuration.
        
        Returns dict mapping provider name to provider instance or config.
        The moonshot provider is special (handled inline with Moonshot API).
        """
        providers = {}
        
        # Moonshot (handled inline)
        moonshot = config.get("services", {}).get("moonshot_search")
        if moonshot:
            providers["moonshot"] = moonshot
        
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
        """Check if tool is enabled based on configuration."""
        enabled = config.get("web_search_enabled", False)
        if not enabled:
            return False
        
        providers = self._create_providers(config)
        if not providers:
            return False  # No provider configured
        
        return None  # Fall through to tag checks

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the SearchWeb tool schema matching Kimi CLI."""
        return [{
            "type": "function",
            "function": {
                "name": "SearchWeb",
                "description": (
                    "WebSearch tool allows you to search on the internet to get latest "
                    "information, including news, documents, release notes, blog posts, "
                    "papers, etc."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query text to search for.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": (
                                "The number of results to return. "
                                "Typically you do not need to set this value. "
                                "When the results do not contain what you need, "
                                "you probably want to give a more concrete query."
                            ),
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                        },
                        "include_content": {
                            "type": "boolean",
                            "description": (
                                "Whether to include the content of the web pages in the results. "
                                "It can consume a large amount of tokens when this is set to True. "
                                "You should avoid enabling this when `limit` is set to a large value."
                            ),
                            "default": False,
                        },
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
        """Execute the SearchWeb tool."""
        if tool_name != "SearchWeb":
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
        
        # Validate limit
        limit = arguments.get("limit", 5)
        if not isinstance(limit, int) or limit < 1 or limit > 20:
            return {
                "success": False,
                "error": "The 'limit' parameter must be an integer between 1 and 20.",
            }
        
        include_content = arguments.get("include_content", False)
        
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
                    f"Available providers: {available}."
                ),
            }
        
        # Dispatch to appropriate backend
        if provider_name == "moonshot":
            return self._execute_moonshot(query, limit, include_content, provider, context)
        else:
            return self._execute_shared_provider(query, limit, provider, provider_name)

    def _execute_moonshot(
        self,
        query: str,
        limit: int,
        include_content: bool,
        moonshot: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute search via Moonshot Search API."""
        import asyncio
        
        base_url = moonshot.get("base_url")
        api_key = moonshot.get("api_key")
        oauth_ref = moonshot.get("oauth")
        custom_headers = moonshot.get("custom_headers", {})
        
        # Resolve API key via OAuth if needed
        if oauth_ref and context:
            app = context.get("app")
            if app and hasattr(app, "resolve_oauth_key"):
                api_key = app.resolve_oauth_key(api_key, oauth_ref)
        
        if not base_url or not api_key:
            return {
                "success": False,
                "error": "Search service is not configured. You may want to try other methods to search.",
            }
        
        try:
            results = asyncio.run(self._moonshot_request(
                base_url, api_key, query, limit, include_content, custom_headers
            ))
            
            if not results:
                return {
                    "success": True,
                    "result": "No matches found",
                }
            
            formatted = self._format_kimi_results(results, include_content)
            return {
                "success": True,
                "result": formatted,
            }
            
        except Exception as e:
            error_msg = str(e)
            if "Status:" in error_msg:
                return {
                    "success": False,
                    "error": error_msg,
                }
            return {
                "success": False,
                "error": f"Failed to search: {error_msg}",
            }

    async def _moonshot_request(
        self,
        base_url: str,
        api_key: str,
        query: str,
        limit: int,
        include_content: bool,
        custom_headers: Dict[str, str],
    ) -> List[SearchResult]:
        """Make async HTTP request to Moonshot Search API."""
        import aiohttp
        
        headers = {
            "User-Agent": "Kimi-CLI/1.0",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **custom_headers,
        }
        
        body = {
            "text_query": query,
            "limit": limit,
            "enable_page_crawling": include_content,
            "timeout_seconds": 30,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(base_url, headers=headers, json=body) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to search. Status: {response.status}. "
                        "This may indicates that the search service is currently unavailable."
                    )
                
                data = await response.json()
        
        # Parse response
        results = []
        for item in data.get("search_results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                content=item.get("content", ""),
                date=item.get("date", ""),
                site_name=item.get("site_name", ""),
            ))
        
        return results

    def _execute_shared_provider(
        self,
        query: str,
        limit: int,
        provider: Any,
        provider_name: str,
    ) -> Dict[str, Any]:
        """Execute search using a shared provider (Tavily/Google).
        
        Results are formatted in Kimi-specific style.
        include_content is not supported for shared providers (no server-side crawling).
        """
        import asyncio
        
        try:
            results = asyncio.run(provider.search(query, limit=limit))
            
            if not results:
                return {
                    "success": True,
                    "result": "No matches found",
                }
            
            # Format in Kimi style (include_content=False for shared providers)
            formatted = self._format_kimi_results(results, include_content=False)
            return {
                "success": True,
                "result": formatted,
            }
            
        except SearchProviderError as e:
            return {
                "success": False,
                "error": f"Failed to search: {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to search: {e}",
            }

    def _format_kimi_results(
        self, 
        results: List[SearchResult],
        include_content: bool
    ) -> str:
        """Format results in Kimi-specific style.
        
        Per-result format:
            Title: X
            Date: Y
            URL: Z
            Summary: W
            
            Content: ... (optional, raw content)
        
        Separator: "---\n\n"
        """
        output_parts = []
        
        for result in results:
            lines = [
                f"Title: {result.title}",
                f"Date: {result.date}",
                f"URL: {result.url}",
                f"Summary: {result.snippet}",
                "",
            ]
            if include_content and result.content:
                lines.append(f"{result.content}")
                lines.append("")
            
            output_parts.append("\n".join(lines))
        
        return "---\n\n".join(output_parts)

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

1. **`__init__.py`**: Add `KimiWebSearchTool` export
2. **`agent_plugin.json`**: Add entry for tool class
3. **`pyproject.toml`**: Add `aiohttp` dependency (for async HTTP)

## Test Plan

### Schema Tests

| Test | Expected |
|------|----------|
| Tool name | `SearchWeb` (PascalCase) |
| Required params | `["query"]` |
| Optional params | `limit` (1-20), `include_content` (bool) |
| Default values | `limit=5`, `include_content=False` |
| No `provider` param | Schema has query/limit/include_content only |

### Result Format Tests (all backends)

| Test | Backend | Expected Format |
|------|---------|-----------------|
| Moonshot result | moonshot | `Title: X\nDate: Y\nURL: Z\nSummary: W\n\n` |
| Moonshot with content | moonshot | `Title...\n\nContent text...\n\n` |
| Shared provider result | tavily/google | Same Kimi format (Title/Date/URL/Summary) |
| Multiple results | any | Separated by `---\n\n` |
| No results | any | `"No matches found"` |

### Provider Selection Tests

| Test | Config | Expected Backend |
|------|--------|------------------|
| Default with Moonshot | `{services: {moonshot_search: {...}}}` | moonshot |
| Explicit tavily | `{web_search_provider: "tavily", tavily_api_key: "key"}` | tavily |
| Explicit google | `{web_search_provider: "google", google_api_key+cx: ...}` | google |
| Fallback: no Moonshot but Tavily | `{tavily_api_key: "key"}` | tavily |
| Unavailable provider | `{web_search_provider: "tavily"}` (no key) | Error |

### Conditional Tests

| Test | Config | Expected |
|------|--------|----------|
| Disabled by default | `{}` | Plugin remains visible for UI; no tool schema is exposed |
| Enabled with Moonshot | `{web_search_enabled: True, services: {moonshot_search: {...}}}` | `is_enabled()` returns None |
| Enabled with Tavily | `{web_search_enabled: True, tavily_api_key: "key"}` | `is_enabled()` returns None |
| Enabled without any provider | `{web_search_enabled: True}` | Plugin remains visible for UI; no tool schema is exposed |

### Error Message Tests

| Test | Expected Message |
|------|------------------|
| No provider configured | `"Search service is not configured..."` or provider unavailable error |
| Moonshot API failure | `"Failed to search. Status: N. This may indicates..."` |
| Invalid limit | `"The 'limit' parameter must be an integer between 1 and 20."` |

## Deliverables

1. `plugins/kimi-tools/src/kimi_tools/kimi_web_search_tool.py`
2. Updated `plugins/kimi-tools/src/kimi_tools/__init__.py`
3. Updated `plugins/kimi-tools/agent_plugin.json`
4. Updated `plugins/kimi-tools/pyproject.toml` (add aiohttp dependency)
5. Tests in `plugins/kimi-tools/tests/test_kimi_web_search_tool.py`

## Status: DONE

## Execution plan

Added during completion after checking the Kimi CLI source of truth and the existing real API test patterns.

1. Implement `KimiWebSearchTool` in `plugins/kimi-tools/src/kimi_tools/kimi_web_search_tool.py`.
   - Match Kimi CLI shape exactly: tool name `SearchWeb`, params `query`, `limit`, `include_content`, Kimi CLI descriptions, no provider parameter.
   - Keep `web_search_enabled` disabled by default.
   - Use `moonshot` as the source-of-truth backend shape, with mocked HTTP tests only because `MOONSHOT_API_KEY` is not available.
   - Use shared `TavilyProvider` and `GeminiApiProvider` as real alternate providers. Do not use `GoogleProvider`; dependency task 121 replaced it with `GeminiApiProvider`.
   - Keep all LLM-visible formatting in the Kimi plugin: `Title`, `Date`, `URL`, `Summary`, optional raw content, separated by `---\n\n`.

2. Wire package discovery.
   - Export `KimiWebSearchTool` from `plugins/kimi-tools/src/kimi_tools/__init__.py`.
   - Add it to `plugins/kimi-tools/agent_plugin.json`.
   - Keep packaging dependencies consistent with `plugins/kimi-tools/setup.py`; add a direct `aiohttp` dependency if the Moonshot implementation imports `aiohttp` directly.

3. Add unit and mocked integration tests in `plugins/kimi-tools/tests/test_kimi_web_search_tool.py`.
   - Schema parity, config schema, visibility, disabled/default behavior.
   - Provider selection for `moonshot`, `tavily`, and `gemini_api`.
   - Moonshot request body/header behavior using mocked `aiohttp`.
   - Moonshot status and parse errors.
   - Kimi-format output for single result, multiple results, empty results, and content.
   - Tavily/Gemini provider execution using mocked providers returning `SearchResponse`.

4. Add real backend API integration tests.
   - Load `.env` using the existing Kimi test pattern.
   - Mark tests with `@pytest.mark.integration`.
   - Add real Tavily backend test gated by `TAVILY_API_KEY`.
   - Add real Gemini backend test gated by `GEMINI_API_KEY`.
   - Do not add a real Moonshot test because the Moonshot API key is not available.

5. Add OpenRouter LLM/tool-call integration test in `plugins/kimi-tools/tests/test_kimi_web_search_tool_openrouter_integration.py`.
   - Mark with `@pytest.mark.integration` and `@pytest.mark.openrouter`.
   - Use `OPENROUTER_MODEL_KIMI_TOOLS`, defaulting to `moonshotai/kimi-k2.5`.
   - Register `OpenRouterProvider`, `OpenRouterToolsExtension`, `RequestOptionsFeature`, and `KimiWebSearchTool`.
   - Use `web_search_provider="tavily"` because `TAVILY_API_KEY` is available.
   - Assert the model calls `SearchWeb`, the real search tool execution succeeds, and the final response contains `OK`.

6. Verification.
   - `pytest plugins/kimi-tools/tests/test_kimi_web_search_tool.py -q`
   - `pytest plugins/kimi-tools/tests/test_kimi_web_search_tool.py -m integration -q`
   - `pytest plugins/kimi-tools/tests/test_kimi_web_search_tool_openrouter_integration.py -m "integration and openrouter" -q`
   - `pytest plugins/kimi-tools/tests -q`

## Completion Notes

Added during completion.

Implemented `KimiWebSearchTool` in `plugins/kimi-tools/src/kimi_tools/kimi_web_search_tool.py`.

Key implementation details:
- Tool schema matches Kimi CLI shape: `SearchWeb` with `query`, `limit`, and `include_content`.
- Moonshot backend mirrors the Kimi CLI request shape: `text_query`, `limit`, `enable_page_crawling`, `timeout_seconds: 30`, `Authorization`, and `X-Msh-Tool-Call-Id` when the core provides a tool call id.
- Real alternate backends use shared `TavilyProvider` and `GeminiApiProvider`; stale `GoogleProvider` references from the original task text were not used because task 121 replaced Google Custom Search with Gemini API Google Search grounding.
- All result formatting stays in the Kimi tool and uses Kimi's `Title`/`Date`/`URL`/`Summary` format with `---\n\n` separators.
- `web_search_enabled` controls model-facing schema exposure and execution, not plugin visibility. The plugin remains visible so the UI can explain missing providers; `SearchWeb` is exposed only when enabled and at least one provider is configured.

Files changed:
- `plugins/kimi-tools/src/kimi_tools/kimi_web_search_tool.py`
- `plugins/kimi-tools/src/kimi_tools/__init__.py`
- `plugins/kimi-tools/agent_plugin.json`
- `plugins/kimi-tools/setup.py`
- `plugins/kimi-tools/tests/test_kimi_web_search_tool.py`
- `plugins/kimi-tools/tests/test_kimi_web_search_tool_openrouter_integration.py`
- `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`
- `application/python/agent_terminal_app/default_config/config.json`
- `application/python/tests/test_kimi_web_search_integration.py`

Verification:
- Passed: `pytest plugins/kimi-tools/tests/test_kimi_web_search_tool.py -q` (`27 passed`)
- Passed: `pytest plugins/kimi-tools/tests/test_kimi_web_search_tool.py -m integration -q` (`2 passed, 25 deselected`)
- Passed: `pytest plugins/kimi-tools/tests/test_kimi_web_search_tool_openrouter_integration.py -m "integration and openrouter" -q` (`1 passed`)
- Partial: `pytest plugins/kimi-tools/tests -q` produced `160 passed, 1 skipped, 11 failed`. The failures are all pre-existing/unrelated `KimiShellTool` async-wrapper compatibility failures: `KimiShellTool.execute_tool()` does not accept newer wrapper kwargs such as `payload_kind`.
