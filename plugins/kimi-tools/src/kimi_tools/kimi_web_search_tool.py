"""Kimi-style SearchWeb tool implementation."""

from __future__ import annotations

import asyncio
import concurrent.futures
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


DEFAULT_PROVIDER = "moonshot"
KIMI_SEARCH_DESCRIPTION = (
    "WebSearch tool allows you to search on the internet to get latest "
    "information, including news, documents, release notes, blog posts, "
    "papers, etc."
)
KIMI_USER_AGENT = "Kimi-CLI/1.0"
MOONSHOT_TIMEOUT_SECONDS = 30


class KimiWebSearchTool(ToolPlugin):
    """Kimi-compatible SearchWeb tool with configurable search backend."""

    name = "kimi_web_search_tool"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
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
                    'Search backend: "moonshot" (requires services.moonshot_search), '
                    '"tavily" (requires tavily_api_key), '
                    '"gemini_api" (requires gemini_api_key)'
                ),
            },
            "tavily_api_key": {
                "type": "string",
                "default": None,
                "description": "Tavily API key for Tavily web search",
            },
            "gemini_api_key": {
                "type": "string",
                "default": None,
                "description": "Gemini API key for Google Search grounding",
            },
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        provider_options = self._provider_options(config)
        elements: List[Dict[str, Any]] = [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable web search",
                "description": (
                    "Enable SearchWeb. Requires GEMINI_API_KEY, TAVILY_API_KEY, "
                    "or services.moonshot_search."
                ),
                "disabled": not bool(provider_options),
                "rich_ui": {
                    "kind": "toggle",
                    "label": "Web search",
                    "show_label": False,
                    "icon": "globe",
                    "placements": ["composer"],
                    "default_pinned": True,
                    "options": [
                        {
                            "value": False,
                            "label": "Off",
                            "icon": "globe",
                            "tone": "primary",
                        },
                        {
                            "value": True,
                            "label": "On",
                            "icon": "globe",
                            "tone": "success",
                        },
                    ],
                },
            }
        ]
        if not provider_options:
            return elements
        if len(provider_options) > 0:
            elements.append(
                {
                    "type": "select",
                    "key": "web_search_provider",
                    "label": "Search provider",
                    "description": "Search backend for SearchWeb",
                    "options": provider_options,
                }
            )
        return elements

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        providers = self._create_providers(config)
        provider_name = self._select_provider(config, providers)
        return {
            "config": config,
            "enabled": config.get("web_search_enabled", False),
            "provider_name": provider_name,
            "providers": providers,
        }

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]],
        models: Optional[List[str]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[bool]:
        return None

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not state.get("enabled", False) or not state.get("providers"):
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": "SearchWeb",
                    "description": KIMI_SEARCH_DESCRIPTION,
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
                                    "Whether to include the content of the web pages in the "
                                    "results. It can consume a large amount of tokens when "
                                    "this is set to True. You should avoid enabling this when "
                                    "`limit` is set to a large value."
                                ),
                                "default": False,
                            },
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
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any = None,
        context: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if tool_name != "SearchWeb":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        async def _run() -> Dict[str, Any]:
            return await self._execute_async(arguments, state, tool_call=tool_call)

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, _run())
            return future.result()

    def stream_tool(
        self,
        tool_name: str,
        payload: Dict[str, Any],
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any = None,
        context: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        yield self.execute_tool(
            tool_name,
            payload,
            state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
            prepared=prepared,
        )

    async def _execute_async(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        tool_call: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not state.get("enabled", False):
            return {
                "success": False,
                "error": (
                    "Web search is disabled. Enable it via web_search_enabled "
                    "configuration."
                ),
            }

        query = str(arguments.get("query", "")).strip()
        if not query:
            return {"success": False, "error": "The 'query' parameter cannot be empty."}

        limit = arguments.get("limit", 5)
        if not isinstance(limit, int) or limit < 1 or limit > 20:
            return {
                "success": False,
                "error": "The 'limit' parameter must be an integer between 1 and 20.",
            }

        include_content = arguments.get("include_content", False)
        if not isinstance(include_content, bool):
            include_content = bool(include_content)

        provider_name = state.get("provider_name", DEFAULT_PROVIDER)
        provider = state.get("providers", {}).get(provider_name)
        if not provider:
            if not state.get("providers"):
                return {
                    "success": False,
                    "error": (
                        "Search service is not configured. You may want to try "
                        "other methods to search."
                    ),
                }
            available = ", ".join(state.get("providers", {}).keys())
            return {
                "success": False,
                "error": (
                    f"Web search provider '{provider_name}' is not configured. "
                    f"Available providers: {available}."
                ),
            }

        if provider_name == "moonshot":
            return await self._execute_moonshot(
                query,
                limit,
                include_content,
                provider,
                tool_call=tool_call,
            )

        return await self._execute_shared_provider(query, limit, provider)

    async def _execute_moonshot(
        self,
        query: str,
        limit: int,
        include_content: bool,
        moonshot: Dict[str, Any],
        *,
        tool_call: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        base_url = moonshot.get("base_url")
        api_key = self._resolve_config_value(moonshot.get("api_key", ""))
        if not base_url or not api_key:
            return {
                "success": False,
                "error": (
                    "Search service is not configured. You may want to try "
                    "other methods to search."
                ),
            }

        try:
            results = await self._moonshot_request(
                base_url,
                api_key,
                query,
                limit,
                include_content,
                moonshot.get("custom_headers") or {},
                self._tool_call_id(tool_call),
            )
        except SearchProviderError as err:
            error = str(err)
            prefix = "[Moonshot Search] "
            if error.startswith(prefix):
                error = error[len(prefix) :]
            return {"success": False, "error": error}
        except Exception as err:
            return {"success": False, "error": f"Failed to search: {err}"}

        if not results:
            return {"success": True, "result": "No matches found"}
        return {"success": True, "result": self._format_kimi_results(results)}

    async def _moonshot_request(
        self,
        base_url: str,
        api_key: str,
        query: str,
        limit: int,
        include_content: bool,
        custom_headers: Dict[str, str],
        tool_call_id: Optional[str],
    ) -> List[SearchResult]:
        import aiohttp

        headers = {
            "User-Agent": KIMI_USER_AGENT,
            "Authorization": f"Bearer {api_key}",
            **custom_headers,
        }
        if tool_call_id:
            headers["X-Msh-Tool-Call-Id"] = tool_call_id

        body = {
            "text_query": query,
            "limit": limit,
            "enable_page_crawling": include_content,
            "timeout_seconds": MOONSHOT_TIMEOUT_SECONDS,
        }

        timeout = aiohttp.ClientTimeout(total=MOONSHOT_TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(base_url, headers=headers, json=body) as response:
                if response.status != 200:
                    raise SearchProviderError(
                        "Moonshot Search",
                        (
                            f"Failed to search. Status: {response.status}. "
                            "This may indicates that the search service is currently "
                            "unavailable."
                        ),
                    )
                try:
                    data = await response.json()
                except Exception as err:
                    raise SearchProviderError(
                        "Moonshot Search",
                        (
                            f"Failed to parse search results. Error: {err}. "
                            "This may indicates that the search service is currently "
                            "unavailable."
                        ),
                        original_error=err,
                    )

        return [
            SearchResult(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                snippet=str(item.get("snippet", "")),
                content=str(item.get("content", "")),
                date=str(item.get("date", "")),
                site_name=str(item.get("site_name", "")),
            )
            for item in data.get("search_results", [])
        ]

    async def _execute_shared_provider(
        self,
        query: str,
        limit: int,
        provider: Any,
    ) -> Dict[str, Any]:
        try:
            response: SearchResponse = await provider.search(query, limit=limit)
        except SearchProviderError as err:
            return {"success": False, "error": f"Failed to search: {err}"}
        except Exception as err:
            return {"success": False, "error": f"Failed to search: {err}"}

        if not response.results:
            return {"success": True, "result": "No matches found"}
        return {"success": True, "result": self._format_kimi_results(response.results)}

    def _create_providers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        providers: Dict[str, Any] = {}

        moonshot = self._moonshot_config(config)
        if moonshot:
            providers["moonshot"] = moonshot

        tavily_key = self._resolve_config_value(
            config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY", "")
        )
        if tavily_key:
            providers["tavily"] = TavilyProvider(api_key=tavily_key)

        gemini_key = self._resolve_config_value(
            config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        )
        if gemini_key:
            providers["gemini_api"] = GeminiApiProvider(api_key=gemini_key)

        return providers

    def _provider_options(self, config: Dict[str, Any]) -> List[Dict[str, str]]:
        providers = self._create_providers(config)
        labels = {
            "moonshot": "Moonshot Search",
            "tavily": "Tavily",
            "gemini_api": "Gemini API (Google Search grounding)",
        }
        return [
            {"value": name, "label": labels[name]}
            for name in ("moonshot", "tavily", "gemini_api")
            if name in providers
        ]

    def _select_provider(
        self, config: Dict[str, Any], providers: Dict[str, Any]
    ) -> str:
        explicit = config.get("web_search_provider")
        if explicit:
            return str(explicit)
        for name in ("moonshot", "tavily", "gemini_api"):
            if name in providers:
                return name
        return DEFAULT_PROVIDER

    def _moonshot_config(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        services = config.get("services") or {}
        moonshot = services.get("moonshot_search")
        if isinstance(moonshot, dict):
            return moonshot
        return None

    def _resolve_config_value(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        if value.startswith("${") and value.endswith("}"):
            return os.environ.get(value[2:-1], "")
        return value

    def _tool_call_id(self, tool_call: Optional[Dict[str, Any]]) -> Optional[str]:
        if not isinstance(tool_call, dict):
            return None
        value = tool_call.get("id")
        return str(value) if value else None

    def _format_kimi_results(self, results: List[SearchResult]) -> str:
        parts = []
        for result in results:
            text = (
                f"Title: {result.title}\n"
                f"Date: {result.date}\n"
                f"URL: {result.url}\n"
                f"Summary: {result.snippet}\n\n"
            )
            if result.content:
                text += f"{result.content}\n\n"
            parts.append(text)
        return "---\n\n".join(parts)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success"):
            return result.get("result", "")
        return f"Error: {result.get('error', 'Unknown error')}"

    def to_display_format(
        self, text: str, result: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"type": "text", "content": text}
