"""Kimi-style FetchURL tool implementation.

This tool fetches web content with optional Moonshot fetch service support.
Unlike Gemini and Qwen, Kimi returns raw extracted text without LLM summarization.

Configuration keys:
- moonshot_enabled: Enable Moonshot fetch service (default: false)
- moonshot_base_url: Moonshot fetch service URL (default: https://api.kimi.com/coding/v1/fetch)
- moonshot_api_key: API key, can use ${ENV_VAR} placeholder (required when enabled)
- moonshot_custom_headers: Additional headers for service requests (optional)
- web_fetch_timeout_seconds: Fetch timeout in seconds (default: 10)
- web_fetch_max_chars: Max content length in chars (default: 50000)
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Iterator, List, Optional

from agent_core.types import ToolPlugin
from web_fetch_shared import (
    BROWSER_USER_AGENT,
    DEFAULT_MAX_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    FetchResult,
    fetch_url,
    truncate_content,
)


# Kimi-specific content limits
KIMI_MAX_CHARS = 50000

# Default Moonshot fetch service URL
DEFAULT_MOONSHOT_BASE_URL = "https://api.kimi.com/coding/v1/fetch"


class KimiFetchURLTool(ToolPlugin):
    """Kimi-style FetchURL tool.

    Fetches web content using:
    1. Primary path: Moonshot fetch service (when enabled and configured)
    2. Fallback path: Local HTTP fetch + trafilatura extraction

    Unlike Gemini and Qwen, Kimi returns raw extracted text without LLM summarization.
    """

    name = "kimi_fetch_url_tool"
    version = "0.2.0"

    def _get_fetch_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fetch settings from config with defaults."""
        return {
            "timeout_seconds": config.get(
                "web_fetch_timeout_seconds", DEFAULT_TIMEOUT_SECONDS
            ),
            "max_chars": config.get("web_fetch_max_chars", KIMI_MAX_CHARS),
        }

    def _get_moonshot_service_config(
        self, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get Moonshot fetch service configuration if enabled and available.

        Requires:
        - moonshot_enabled: True (opt-in)
        - moonshot_api_key: Valid API key

        Uses flattened config keys:
        - moonshot_enabled: Enable the service (default: false)
        - moonshot_base_url: Service endpoint URL (default: https://api.kimi.com/coding/v1/fetch)
        - moonshot_api_key: API key (can use ${ENV_VAR} placeholder)
        - moonshot_custom_headers: Additional headers (optional)
        """
        # Must be explicitly enabled
        if not config.get("moonshot_enabled", False):
            return None

        # Get API key and resolve env var placeholder
        api_key = config.get("moonshot_api_key", "")
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.environ.get(env_var, "")

        # Must have a valid API key after resolution
        if not api_key:
            return None

        # Use default URL if not specified
        base_url = config.get("moonshot_base_url", DEFAULT_MOONSHOT_BASE_URL)

        return {
            "base_url": base_url,
            "api_key": api_key,
            "custom_headers": config.get("moonshot_custom_headers"),
        }

    # ------------------------------------------------------------------
    # ToolPlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema for FetchURL tool settings."""
        return {
            "moonshot_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable Moonshot fetch service for web content fetching",
            },
            "moonshot_base_url": {
                "type": "string",
                "default": DEFAULT_MOONSHOT_BASE_URL,
                "description": "Moonshot fetch service endpoint URL",
            },
            "moonshot_api_key": {
                "type": "string",
                "default": "",
                "description": "API key for Moonshot fetch service (can use ${ENV_VAR} placeholder)",
            },
            "moonshot_custom_headers": {
                "type": "object",
                "default": {},
                "description": "Additional headers for Moonshot service requests",
            },
            "web_fetch_timeout_seconds": {
                "type": "integer",
                "default": DEFAULT_TIMEOUT_SECONDS,
                "description": "HTTP fetch timeout in seconds",
            },
            "web_fetch_max_chars": {
                "type": "integer",
                "default": KIMI_MAX_CHARS,
                "description": "Maximum content length in characters",
            },
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI schema elements for FetchURL tool settings."""
        elements = [
            {
                "type": "checkbox",
                "key": "moonshot_enabled",
                "label": "Enable Moonshot fetch service",
                "description": "Use Kimi's fetch service for web content (requires API key)",
            },
        ]

        # Only show API key and URL when enabled
        if config.get("moonshot_enabled", False):
            elements.extend([
                {
                    "type": "text",
                    "key": "moonshot_api_key",
                    "label": "Moonshot API key",
                    "description": "API key for Moonshot fetch service",
                    "placeholder": "sk-... or ${MOONSHOT_API_KEY}",
                },
                {
                    "type": "text",
                    "key": "moonshot_base_url",
                    "label": "Moonshot service URL",
                    "description": "Fetch service endpoint",
                    "placeholder": DEFAULT_MOONSHOT_BASE_URL,
                },
            ])

        elements.extend([
            {
                "type": "number",
                "key": "web_fetch_timeout_seconds",
                "label": "Fetch timeout (seconds)",
                "description": "Time to wait for URL response",
            },
            {
                "type": "number",
                "key": "web_fetch_max_chars",
                "label": "Max content chars",
                "description": "Maximum content length to return",
            },
        ])

        return elements

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with configuration."""
        fetch_config = self._get_fetch_config(config)
        moonshot_config = self._get_moonshot_service_config(config)

        return {
            "config": config,
            "fetch_config": fetch_config,
            "moonshot_config": moonshot_config,
        }

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the FetchURL tool schema (PascalCase name matching Kimi CLI)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "FetchURL",
                    "description": (
                        "Fetch a web page from a URL and extract main text content from it."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch content from.",
                            }
                        },
                        "required": ["url"],
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
        """Execute the FetchURL tool synchronously.

        This wraps the async implementation for sync callers.
        """
        if tool_name != "FetchURL":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # Run async implementation
        return asyncio.run(self._execute_async(arguments, state, context))

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
    ) -> Iterator[Dict[str, Any]]:
        """Execute the FetchURL tool asynchronously.

        Yields a single result dict with the response.
        """
        if tool_name != "FetchURL":
            yield {"success": False, "error": f"Unknown tool: {tool_name}"}
            return

        # Run async implementation synchronously
        result = asyncio.run(self._execute_async(payload, state, context))
        yield result

    async def _execute_async(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Main async execution logic.

        Tries Moonshot service first (if enabled and configured), then falls back to local fetch.
        """
        url = arguments.get("url")
        if not url or not isinstance(url, str):
            return {"success": False, "error": "The 'url' parameter is required."}

        # Validate URL
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return {
                    "success": False,
                    "error": f"Unsupported protocol: {parsed.scheme}",
                }
            if not parsed.hostname:
                return {"success": False, "error": "URL must have a valid hostname."}
        except Exception as e:
            return {"success": False, "error": f"Invalid URL: {e}"}

        # Try Moonshot service first if configured
        moonshot_config = state.get("moonshot_config")
        if moonshot_config:
            result = await self._fetch_with_service(url, moonshot_config, state)
            if result.get("success"):
                return result
            # Service failed, fall back to local fetch

        # Use local fetch
        return await self._fetch_with_http_get(url, state)

    async def _fetch_with_service(
        self,
        url: str,
        service_config: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fetch URL content via Moonshot fetch service.

        POSTs to the Moonshot fetch service with the URL.
        Returns markdown content on success.
        """
        import aiohttp

        base_url = service_config.get("base_url")
        api_key = service_config.get("api_key", "")

        if not api_key:
            return {
                "success": False,
                "error": "Moonshot fetch service is enabled but no API key is configured.",
            }

        # Build headers
        headers = {
            "User-Agent": BROWSER_USER_AGENT,
            "Authorization": f"Bearer {api_key}",
            "Accept": "text/markdown",
        }

        # Add custom headers if present
        custom_headers = service_config.get("custom_headers")
        if custom_headers:
            headers.update(custom_headers)

        fetch_config = state.get("fetch_config", {})

        try:
            timeout = aiohttp.ClientTimeout(total=fetch_config.get("timeout_seconds", 10))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    base_url,
                    headers=headers,
                    json={"url": url},
                ) as response:
                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"Failed to fetch URL via service. Status: {response.status}.",
                        }

                    content = await response.text()

                    # Truncate if needed
                    max_chars = fetch_config.get("max_chars", KIMI_MAX_CHARS)
                    if len(content) > max_chars:
                        content = truncate_content(content, max_chars=max_chars)

                    return {
                        "success": True,
                        "result": content,
                        "message": "The returned content is the main content extracted from the page.",
                    }

        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": (
                    f"Failed to fetch URL via service due to network error: {str(e)}. "
                    "This may indicate the service is unreachable."
                ),
            }
        except TimeoutError:
            return {
                "success": False,
                "error": "Request to fetch service timed out.",
            }

    async def _fetch_with_http_get(
        self,
        url: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fetch URL content via local HTTP GET with trafilatura extraction.

        Uses web_fetch_shared.fetch_url for HTTP fetching.
        Applies trafilatura extraction for HTML content.
        Passthrough for text/plain and text/markdown.
        """
        fetch_config = state.get("fetch_config", {})

        # Fetch URL content using shared utility
        fetch_result = await fetch_url(
            url,
            timeout_seconds=fetch_config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
            user_agent=BROWSER_USER_AGENT,
        )

        # Handle fetch errors
        if fetch_result.is_error:
            if fetch_result.status_code >= 400:
                return {
                    "success": False,
                    "error": (
                        f"Failed to fetch URL. Status: {fetch_result.status_code}. "
                        "This may indicate the page is not accessible or the server is down."
                    ),
                }
            return {
                "success": False,
                "error": (
                    f"Failed to fetch URL due to network error: {fetch_result.error_message}. "
                    "This may indicate the URL is invalid or the server is unreachable."
                ),
            }

        content_type = fetch_result.content_type.lower()
        content = fetch_result.content

        # Check for empty response
        if not content:
            return {
                "success": True,
                "result": "",
                "message": "The response body is empty.",
            }

        # Passthrough for text/plain and text/markdown
        if "text/plain" in content_type or "text/markdown" in content_type:
            # Truncate if needed
            max_chars = fetch_config.get("max_chars", KIMI_MAX_CHARS)
            if len(content) > max_chars:
                content = truncate_content(content, max_chars=max_chars)

            return {
                "success": True,
                "result": content,
                "message": "The returned content is the full content of the page.",
            }

        # Use trafilatura extraction for HTML content
        # Kimi-specific options: include_comments=True, include_tables=True,
        # include_formatting=False, output_format="txt", with_metadata=True
        extracted_text = self._extract_with_trafilatura(content)

        if not extracted_text:
            return {
                "success": False,
                "error": (
                    "Failed to extract meaningful content from the page. "
                    "This may indicate the page content is not suitable for text extraction, "
                    "or the page requires JavaScript to render its content."
                ),
            }

        # Truncate if needed
        max_chars = fetch_config.get("max_chars", KIMI_MAX_CHARS)
        if len(extracted_text) > max_chars:
            extracted_text = truncate_content(extracted_text, max_chars=max_chars)

        return {
            "success": True,
            "result": extracted_text,
            "message": "The returned content is the main text content extracted from the page.",
        }

    def _extract_with_trafilatura(self, html_content: str) -> str:
        """Extract text from HTML using trafilatura with Kimi-specific options.

        Kimi uses:
        - include_comments=True
        - include_tables=True
        - include_formatting=False
        - output_format="txt"
        - with_metadata=True
        """
        # Lazy import to allow module to load without trafilatura
        import trafilatura

        try:
            extracted = trafilatura.extract(
                html_content,
                include_comments=True,
                include_tables=True,
                include_formatting=False,
                output_format="txt",
                with_metadata=True,
            )
            if extracted is None:
                return ""
            return extracted
        except Exception:
            return ""

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format the tool result for LLM consumption."""
        if result.get("success"):
            content = result.get("result", "")
            message = result.get("message", "")
            if message:
                return f"{message}\n\n{content}" if content else message
            return content
        return f"Error: {result.get('error', 'Unknown error')}"

    def to_display_format(
        self, text: str, result: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format for display in UI."""
        return {"type": "text", "content": text}
