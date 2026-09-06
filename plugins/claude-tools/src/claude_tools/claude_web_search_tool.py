# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from tool_compat_shared import (
    GeminiApiProvider,
    SearchProviderError,
    SearchResponse,
    SearchResult,
    TavilyProvider,
)
from web_fetch_shared import run_prompted_summary_request

from .interop import claude_tool_interop_contribution


WEB_SEARCH_DESCRIPTION = (
    "\n"
    "- Allows Claude to search the web and use the results to inform responses\n"
    "- Provides up-to-date information for current events and recent data\n"
    "- Returns search result information formatted as search result blocks, including links as markdown hyperlinks\n"
    "- Use this tool for accessing information beyond Claude's knowledge cutoff\n"
    "- Searches are performed automatically within a single API call\n\n"
    "CRITICAL REQUIREMENT - You MUST follow this:\n"
    '  - After answering the user\'s question, you MUST include a "Sources:" section at the end of your response\n'
    "  - In the Sources section, list all relevant URLs from the search results as markdown hyperlinks: [Title](URL)\n"
    "  - This is MANDATORY - never skip including sources in your response\n"
    "  - Example format:\n\n"
    "    [Your answer here]\n\n"
    "    Sources:\n"
    "    - [Source Title 1](https://example.com/1)\n"
    "    - [Source Title 2](https://example.com/2)\n\n"
    "Usage notes:\n"
    "  - Domain filtering is supported to include or block specific websites\n"
    "  - Web search is only available in the US\n\n"
    "IMPORTANT - Use the correct year in search queries:\n"
    "  - The current month is May 2026. You MUST use this year when searching for recent information, documentation, or current events.\n"
    '  - Example: If the user asks for "latest React docs", search for "React documentation" with the current year, NOT last year\n'
)

WEB_SEARCH_SCHEMA: Dict[str, Any] = {
    "name": "WebSearch",
    "description": WEB_SEARCH_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "allowed_domains": {
                "description": "Only include search results from these domains",
                "items": {"type": "string"},
                "type": "array",
            },
            "blocked_domains": {
                "description": "Never include search results from these domains",
                "items": {"type": "string"},
                "type": "array",
            },
            "query": {
                "description": "The search query to use",
                "minLength": 2,
                "type": "string",
            },
        },
        "required": ["query"],
        "type": "object",
    },
}

DEFAULT_PROVIDER = "gemini_api"
DEFAULT_MAX_RESULTS = 5


def _tool_result_block(
    tool_use_id: str,
    content: str,
    *,
    is_error: bool,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "cache_control": {"type": "ephemeral"},
    }
    if is_error:
        block["is_error"] = True
    return block


def _domains_from_value(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    domains: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            domains.append(item.strip().lower())
    return domains


def _host_matches_domain(hostname: str, domain: str) -> bool:
    return hostname == domain or hostname.endswith(f".{domain}")


def _filter_results(
    results: List[SearchResult],
    *,
    allowed_domains: List[str],
    blocked_domains: List[str],
) -> List[SearchResult]:
    filtered: List[SearchResult] = []
    for result in results:
        hostname = (urlparse(result.url).hostname or "").lower()
        if allowed_domains and not any(
            _host_matches_domain(hostname, domain) for domain in allowed_domains
        ):
            continue
        if blocked_domains and any(
            _host_matches_domain(hostname, domain) for domain in blocked_domains
        ):
            continue
        filtered.append(result)
    return filtered


def _fallback_summary(query: str, results: List[SearchResult]) -> str:
    if not results:
        return "No search results matched the requested filters."
    lines = [f"I found {len(results)} relevant web results for {query!r}:"]
    for result in results[:5]:
        title = result.title or result.url
        detail = result.snippet or result.content or result.url
        lines.append(f"- {title}: {detail}".strip())
    return "\n".join(lines)


def _run_async(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, awaitable)
        return future.result()


class ClaudeWebSearchTool(ToolPlugin):
    name = "claude_web_search_tool"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "web_search_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable the Claude-compatible WebSearch tool.",
            }
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = tags, models
        gemini_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        tavily_key = config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY")
        return [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable web search",
                "description": (
                    "Enable WebSearch. Requires GEMINI_API_KEY or TAVILY_API_KEY."
                ),
                "disabled": not bool(gemini_key or tavily_key),
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

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        gemini_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        tavily_key = config.get("tavily_api_key") or os.environ.get("TAVILY_API_KEY")
        providers: Dict[str, Any] = {}
        if gemini_key:
            providers["gemini_api"] = GeminiApiProvider(api_key=gemini_key)
        if tavily_key:
            providers["tavily"] = TavilyProvider(api_key=tavily_key)
        provider_name = str(config.get("web_search_provider") or DEFAULT_PROVIDER)
        return {
            "config": config,
            "enabled": config.get("web_search_enabled", True),
            "providers": providers,
            "provider_name": provider_name,
            "max_results": int(
                config.get("web_search_max_results", DEFAULT_MAX_RESULTS)
            ),
        }

    def get_tool_interop_contribution(self, state: Dict[str, Any]):
        return claude_tool_interop_contribution()

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        if state.get("enabled", True) is False:
            return []
        return [WEB_SEARCH_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "WebSearch"

    def _provider(self, state: Dict[str, Any]) -> Any | None:
        providers = state.get("providers") or {}
        provider_name = state.get("provider_name") or DEFAULT_PROVIDER
        provider = providers.get(provider_name)
        if provider is not None:
            return provider
        if provider_name != DEFAULT_PROVIDER and provider_name in {
            "gemini_api",
            "tavily",
        }:
            return None
        if providers.get("gemini_api") is not None:
            return providers["gemini_api"]
        if providers.get("tavily") is not None:
            return providers["tavily"]
        return None

    def _result(
        self,
        *,
        tool_use_id: str,
        text: str,
        success: bool,
    ) -> Dict[str, Any]:
        return {
            "success": success,
            "anthropic_content": [
                _tool_result_block(tool_use_id, text, is_error=not success)
            ],
            "text": text,
        }

    def _validation_error_text(self) -> str:
        return (
            "<tool_use_error>InputValidationError: [\n"
            "  {\n"
            '    "origin": "string",\n'
            '    "code": "too_small",\n'
            '    "minimum": 2,\n'
            '    "inclusive": true,\n'
            '    "path": [\n'
            '      "query"\n'
            "    ],\n"
            '    "message": "Too small: expected string to have >=2 characters"\n'
            "  }\n"
            "]</tool_use_error>"
        )

    def _format_content(
        self,
        *,
        query: str,
        summary: str,
        results: List[SearchResult],
    ) -> str:
        links = json.dumps(
            [{"title": result.title, "url": result.url} for result in results],
            separators=(",", ":"),
        )
        return (
            f'Web search results for query: "{query}"\n\n'
            f"Links: {links}\n\n"
            f'Here\'s a summary of the search results for "{query}":\n\n'
            f"{summary.strip()}\n\n"
            "REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks."
        )

    def _summarize_results(
        self,
        *,
        query: str,
        provider_response: SearchResponse,
        filtered_results: List[SearchResult],
        used_filters: bool,
        context: Optional[Dict[str, Any]],
    ) -> str:
        answer = (provider_response.answer or "").strip()
        if answer and not used_filters:
            return answer
        structured = json.dumps(
            [
                {
                    "title": item.title,
                    "url": item.url,
                    "snippet": item.snippet,
                    "content": item.content[:1000],
                    "date": item.date,
                }
                for item in filtered_results[:10]
            ],
            indent=2,
            ensure_ascii=False,
        )
        prompt_text = (
            f'Please summarize these web search results for the query "{query}". '
            "Use only the provided results. Return only the answer content, with no preamble.\n\n"
            f"{structured}"
        )
        success, summary = run_prompted_summary_request(
            prompt_text,
            answer or _fallback_summary(query, filtered_results),
            context,
        )
        if success and isinstance(summary, str) and summary.strip():
            return summary.strip()
        return answer or _fallback_summary(query, filtered_results)

    async def _execute_async(
        self,
        payload: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> tuple[bool, str]:
        if state.get("enabled", True) is False:
            return False, "WebSearch is disabled."

        query = payload.get("query")
        if not isinstance(query, str) or len(query) < 2:
            return False, self._validation_error_text()

        provider = self._provider(state)
        if provider is None:
            return (
                False,
                "<tool_use_error>Search service is not configured. Configure GEMINI_API_KEY or TAVILY_API_KEY.</tool_use_error>",
            )

        allowed_domains = _domains_from_value(payload.get("allowed_domains"))
        blocked_domains = _domains_from_value(payload.get("blocked_domains"))
        try:
            response = await provider.search(
                query,
                limit=max(
                    1, min(20, int(state.get("max_results", DEFAULT_MAX_RESULTS)))
                ),
            )
        except SearchProviderError as exc:
            return False, f"<tool_use_error>{exc}</tool_use_error>"

        filtered_results = _filter_results(
            response.results,
            allowed_domains=allowed_domains,
            blocked_domains=blocked_domains,
        )
        summary = self._summarize_results(
            query=query,
            provider_response=response,
            filtered_results=filtered_results,
            used_filters=bool(allowed_domains or blocked_domains),
            context=context,
        )
        return True, self._format_content(
            query=query,
            summary=summary,
            results=filtered_results,
        )

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        tool_call: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "WebSearch":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "WebSearch input must be an object"}

        tool_use_id = "call_WebSearch"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        success, text = _run_async(self._execute_async(payload, state, context))
        return self._result(tool_use_id=tool_use_id, text=text, success=success)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        content = result.get("anthropic_content")
        if isinstance(content, list) and all(
            isinstance(item, dict) for item in content
        ):
            return make_provider_native_tool_result(
                format=FORMAT_ANTHROPIC_MESSAGES,
                content=content,
                text=str(result.get("text") or ""),
            )
        if result.get("success"):
            return str(result.get("text") or "")
        return f"Error: {result.get('text') or result.get('error') or ''}"

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "type": "text",
            "content": text,
            "single_line": "Web search",
        }


__all__ = ["ClaudeWebSearchTool", "WEB_SEARCH_SCHEMA"]
