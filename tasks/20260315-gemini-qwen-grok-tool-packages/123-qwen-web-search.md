# 123 - Qwen Web Search Tool

Short description: Add `web_search` tool to `qwen-tools` with multi-provider support (Dashscope, Tavily, Google). Dashscope provider lives in vendor plugin (Qwen OAuth coupling). Tavily/Google providers from shared package. Returns top 5 results with optional answer. Disabled by default; errors if enabled without configured provider.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/121-web-search-shared.md`

## Goal

Implement `QwenWebSearchTool` that matches Qwen CLI's `web_search` tool exactly:

1. **Tool schema**: name `web_search`, params `query` (required), `provider` (optional)
2. **Multi-provider support**: Dashscope (OAuth), Tavily (API key), Google Custom Search (API key + CX)
3. **Result format**: Answer (if available) + Sources footer, or top 5 summary
4. **Conditional**: Disabled by default via config; if enabled without provider, returns error

## Source of Truth

### Qwen CLI Implementation

File: `../qwen-code/packages/core/src/tools/web-search/index.ts`

Key behaviors:
1. Creates providers based on configuration
2. Selects provider: requested > default > first available
3. Formats results: answer + sources, or top 5 summary with notes

### Tool Schema

File: `../qwen-code/packages/core/src/tools/tool-names.ts`

```typescript
WEB_SEARCH: 'web_search'
```

From `index.ts`:
```json
{
  "name": "web_search",
  "description": "Allows searching the web and using results to inform responses. Provides up-to-date information for current events and recent data beyond the training data cutoff. Returns search results formatted with concise answers and source links. Use this tool when accessing information that may be outdated or beyond the knowledge cutoff.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query to find information on the web."
      },
      "provider": {
        "type": "string",
        "description": "Optional provider to use for the search (e.g., \"tavily\", \"google\", \"dashscope\"). IMPORTANT: Only specify this parameter if you explicitly know which provider to use. Otherwise, omit this parameter entirely and let the system automatically select the appropriate provider based on availability and configuration."
      }
    },
    "required": ["query"]
  }
}
```

### Provider Implementations

**DashscopeProvider** (lives in vendor plugin):
- File: `../qwen-code/packages/core/src/tools/web-search/providers/dashscope-provider.ts`
- Only available when `auth_type === 'qwen-oauth'`
- Reads credentials from `~/.qwen/oauth_creds.json`
- Uses `resource_url` from credentials

**TavilyProvider** (from shared package):
- Requires `tavily_api_key` config
- Returns `answer` + `results`

**GoogleProvider** (from shared package):
- Requires `google_api_key` + `google_search_engine_id`

### Result Formatting

From `index.ts` `formatSearchResults()`:

**With answer:**
```
<<answer text>>

Sources:
[1] Title (url)
[2] Title (url)
```

**Without answer (top 5):**
```
1. **Title**
   Snippet content...
   Source: https://url
   Relevance: 85%
   Published: 2024-01-15

2. **Another Title**
   ...

*Note: For detailed content from any source above, use the web_fetch tool with the URL.*
```

## Implementation

### File: `plugins/qwen-tools/src/qwen_tools/qwen_web_search_tool.py`

```python
"""Qwen-style web_search tool implementation.

Supports multiple search providers: Dashscope (Qwen OAuth), Tavily, Google.
Dashscope provider is implemented here due to Qwen OAuth coupling.
Tavily and Google providers from tool-compat-shared.

Configuration keys (all flat):
- web_search_enabled: Enable the tool (default: False)
- web_search_default_provider: Default provider name (default: first available)
- dashscope_*: Dashscope-specific settings (inherited from auth)
- tavily_api_key: Tavily API key
- google_api_key: Google Custom Search API key
- google_search_engine_id: Google Custom Search Engine ID
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    SearchResult,
    SearchProvider,
    SearchProviderError,
    TavilyProvider,
    GoogleProvider,
)


# Qwen OAuth credential file path
QWEN_CREDENTIALS_PATH = Path.home() / ".qwen" / "oauth_creds.json"


class DashscopeProvider:
    """Dashscope search provider (Qwen OAuth only).
    
    This provider lives in the vendor plugin because it's tightly
    coupled to Qwen's OAuth authentication flow.
    """
    name = "DashScope"
    
    def __init__(self, config: Dict[str, Any]):
        self._config = config
    
    def is_available(self) -> bool:
        """Only available when auth type is qwen-oauth."""
        return self._config.get("auth_type") == "qwen-oauth"
    
    async def search(
        self, 
        query: str, 
        *, 
        limit: int = 10,
        signal: Any = None
    ) -> List[SearchResult]:
        """Execute search via Dashscope API."""
        credentials = self._load_credentials()
        if not credentials:
            raise SearchProviderError(self.name, "No OAuth credentials found")
        
        access_token = credentials.get("access_token")
        resource_url = credentials.get("resource_url")
        
        if not access_token or not resource_url:
            raise SearchProviderError(self.name, "Invalid credentials")
        
        # Check token expiry
        expiry = credentials.get("expiry_date")
        if expiry and expiry < self._get_time_ms():
            raise SearchProviderError(self.name, "OAuth token expired")
        
        # Construct API URL
        base_url = resource_url if resource_url.startswith("http") else f"https://{resource_url}"
        api_url = f"{base_url.rstrip('/')}/api/v1/indices/plugin/web_search"
        
        # Make request
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}",
                },
                json={"uq": query, "page": 1, "rows": limit},
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise SearchProviderError(self.name, f"API error: {response.status} - {text}")
                
                data = await response.json()
        
        # Parse response
        results = []
        for item in data.get("data", {}).get("docs", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                score=item.get("_score", 0.0),
                date=item.get("timestamp_format", ""),
            ))
        
        return results
    
    def _load_credentials(self) -> Optional[Dict[str, Any]]:
        """Load Qwen OAuth credentials from disk."""
        try:
            if QWEN_CREDENTIALS_PATH.exists():
                return json.loads(QWEN_CREDENTIALS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
        return None
    
    def _get_time_ms(self) -> int:
        import time
        return int(time.time() * 1000)


class QwenWebSearchTool(ToolPlugin):
    """Qwen-style web_search tool.
    
    Multi-provider support with automatic selection.
    """
    
    name = "qwen_web_search_tool"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema for web_search tool settings."""
        return {
            "web_search_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable the web_search tool",
            },
            "web_search_default_provider": {
                "type": "string",
                "default": None,
                "description": "Default provider (dashscope, tavily, google). Auto-selected if not set.",
            },
            "tavily_api_key": {
                "type": "string",
                "default": None,
                "description": "Tavily API key for web search",
            },
            "google_api_key": {
                "type": "string",
                "default": None,
                "description": "Google Custom Search API key",
            },
            "google_search_engine_id": {
                "type": "string",
                "default": None,
                "description": "Google Custom Search Engine ID",
            },
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI schema elements for web_search tool settings."""
        # Build available provider list
        available = self._get_available_providers(config)
        provider_names = list(available.keys()) if available else []
        
        elements = [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable web search",
                "description": f"Available providers: {', '.join(provider_names) or 'none configured'}",
            }
        ]
        
        if len(provider_names) > 1:
            elements.append({
                "type": "select",
                "key": "web_search_default_provider",
                "label": "Default provider",
                "options": [{"value": p.lower(), "label": p} for p in provider_names],
            })
        
        if "Tavily" not in provider_names:
            elements.append({
                "type": "text",
                "key": "tavily_api_key",
                "label": "Tavily API key",
                "description": "Add Tavily search capability",
            })
        
        if "Google" not in provider_names:
            elements.extend([
                {
                    "type": "text",
                    "key": "google_api_key",
                    "label": "Google API key",
                },
                {
                    "type": "text",
                    "key": "google_search_engine_id",
                    "label": "Google Search Engine ID",
                },
            ])
        
        return elements

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with providers."""
        providers = self._create_providers(config)
        return {
            "config": config,
            "enabled": config.get("web_search_enabled", False),
            "providers": providers,
            "default_provider": config.get("web_search_default_provider"),
        }

    def _create_providers(self, config: Dict[str, Any]) -> Dict[str, SearchProvider]:
        """Create available providers based on configuration."""
        providers = {}
        
        # Dashscope (Qwen OAuth)
        dashscope = DashscopeProvider(config)
        if dashscope.is_available():
            providers["dashscope"] = dashscope
        
        # Tavily
        tavily_key = config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            providers["tavily"] = TavilyProvider(tavily_key, config)
        
        # Google Custom Search
        google_key = config.get("google_api_key") or os.environ.get("GOOGLE_API_KEY")
        google_cx = config.get("google_search_engine_id") or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        if google_key and google_cx:
            providers["google"] = GoogleProvider(google_key, google_cx, config)
        
        return providers

    def _get_available_providers(self, config: Dict[str, Any]) -> Dict[str, SearchProvider]:
        """Get dict of available providers for UI display."""
        return self._create_providers(config)

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
        
        # Check if any provider is available
        providers = self._create_providers(config)
        if not providers:
            return False  # No providers configured
        
        return None  # Fall through to tag checks

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the web_search tool schema matching Qwen CLI."""
        return [{
            "type": "function",
            "function": {
                "name": "web_search",
                "description": (
                    "Allows searching the web and using results to inform responses. "
                    "Provides up-to-date information for current events and recent data "
                    "beyond the training data cutoff. Returns search results formatted "
                    "with concise answers and source links. Use this tool when accessing "
                    "information that may be outdated or beyond the knowledge cutoff."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find information on the web.",
                        },
                        "provider": {
                            "type": "string",
                            "description": (
                                'Optional provider to use for the search (e.g., "tavily", '
                                '"google", "dashscope"). IMPORTANT: Only specify this '
                                "parameter if you explicitly know which provider to use. "
                                "Otherwise, omit this parameter entirely and let the system "
                                "automatically select the appropriate provider based on "
                                "availability and configuration."
                            ),
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
        """Execute the web_search tool."""
        if tool_name != "web_search":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        # Check if enabled
        if not state.get("enabled", False):
            return {
                "success": False,
                "error": "Web search is disabled. Enable it via web_search_enabled configuration.",
            }
        
        # Check for providers
        providers = state.get("providers", {})
        if not providers:
            return {
                "success": False,
                "error": "Web search is disabled. Please configure a web search provider in your settings.",
            }
        
        # Validate query
        query = arguments.get("query", "").strip()
        if not query:
            return {
                "success": False,
                "error": "The 'query' parameter cannot be empty.",
            }
        
        # Select provider
        requested = arguments.get("provider", "").lower() if arguments.get("provider") else None
        default = state.get("default_provider")
        
        provider = self._select_provider(providers, requested, default)
        if not provider:
            available = ", ".join(providers.keys())
            return {
                "success": False,
                "error": f'The specified provider "{requested}" is not available. Available: {available}',
            }
        
        return self._execute_search(query, provider)

    def _select_provider(
        self,
        providers: Dict[str, SearchProvider],
        requested: Optional[str],
        default: Optional[str]
    ) -> Optional[SearchProvider]:
        """Select provider based on request and defaults."""
        # Use requested if valid
        if requested and requested in providers:
            return providers[requested]
        
        # Use default if valid
        if default and default in providers:
            return providers[default]
        
        # Fall back to first available
        if providers:
            return next(iter(providers.values()))
        
        return None

    def _execute_search(self, query: str, provider: SearchProvider) -> Dict[str, Any]:
        """Execute search via selected provider."""
        import asyncio
        
        try:
            # Run async search
            results = asyncio.run(provider.search(query, limit=5))
            
            # Format results
            formatted = self._format_results(results, getattr(provider, 'name', 'Unknown'))
            
            return {
                "success": True,
                "result": f'Web search results for "{query}" (via {provider.name}):\n\n{formatted}',
            }
            
        except SearchProviderError as e:
            return {
                "success": False,
                "error": f"Error during web search: {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error during web search: {e}",
            }

    def _format_results(
        self, 
        results: List[SearchResult],
        provider_name: str
    ) -> str:
        """Format results in Qwen-specific style.
        
        - If answer available: answer + Sources footer
        - Otherwise: top 5 results with title, snippet, URL, optional score/date
        """
        if not results:
            return f'No search results found for query.'
        
        # Build top 5 summary
        lines = []
        for i, r in enumerate(results[:5]):
            lines.append(f"{i + 1}. **{r.title}**")
            if r.snippet:
                lines.append(f"   {r.snippet.strip()}")
            lines.append(f"   Source: {r.url}")
            if r.score > 0:
                lines.append(f"   Relevance: {int(r.score * 100)}%")
            if r.date:
                lines.append(f"   Published: {r.date}")
        
        content = "\n\n".join(lines)
        content += "\n\n*Note: For detailed content from any source above, use the web_fetch tool with the URL.*"
        
        return content

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

1. **`__init__.py`**: Add `QwenWebSearchTool` export
2. **`agent_plugin.json`**: Add entry for tool class
3. **`setup.py`**: Already has dependencies

## Test Plan

### Schema Tests

| Test | Expected |
|------|----------|
| Tool name | `web_search` |
| Required params | `["query"]` |
| Optional params | `provider` (string) |

### Provider Selection Tests

| Test | Config | Requested | Expected Provider |
|------|--------|-----------|-------------------|
| Only one available | tavily only | None | Tavily |
| Requested available | tavily + google | "google" | Google |
| Requested unavailable | tavily only | "google" | Error |
| Default used | tavily + google | None, default=tavily | Tavily |
| Fallback | tavily + google | None, no default | First in dict |

### Result Format Tests

| Test | Expected Format |
|------|-----------------|
| Top 5 summary | `1. **Title**\n   Snippet...\n   Source: url` |
| With score | `   Relevance: 85%` |
| With date | `   Published: 2024-01-15` |
| Note footer | `*Note: For detailed content...*` |

### Conditional Tests

| Test | Config | Expected |
|------|--------|----------|
| Disabled by default | `{}` | `is_enabled()` returns False |
| Enabled with provider | `{web_search_enabled: True, tavily_api_key: "key"}` | `is_enabled()` returns None |
| Enabled without provider | `{web_search_enabled: True}` | `is_enabled()` returns False |

## Deliverables

1. `plugins/qwen-tools/src/qwen_tools/qwen_web_search_tool.py`
2. Updated `plugins/qwen-tools/src/qwen_tools/__init__.py`
3. Updated `plugins/qwen-tools/agent_plugin.json`
4. Tests in `plugins/qwen-tools/tests/test_qwen_web_search_tool.py`

## Status: TODO
