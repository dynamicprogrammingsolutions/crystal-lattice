"""Qwen-style web_fetch tool implementation.

This tool fetches URLs directly and summarizes content using the
configured provider. Simpler than Gemini with explicit url and prompt
parameters.

Configuration keys (all flat, prefixed with web_fetch_):
- web_fetch_enabled: Enable the tool (default: True)
- web_fetch_timeout_seconds: Fetch timeout in seconds (default: 10)
- web_fetch_max_content_chars: Max content length in chars (default: 100000)
- web_fetch_rate_limit_requests: Max requests per window per host (default: 10)
- web_fetch_rate_limit_window: Rate limit window in seconds (default: 60)
- web_fetch_summarization_agent_id: Optional dedicated agent for summarization
- web_fetch_summarization_model: Optional model override for summarization
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterator, List, Optional

from agent_core.types import ToolPlugin
from web_fetch_shared import (
    DEFAULT_MAX_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    LRUCache,
    check_rate_limit,
    extract_text,
    fetch_url,
    normalize_github_url,
    run_prompted_summary_request,
    truncate_content,
)


# Module-level LRU cache for rate limiting (shared across instances)
_rate_limit_cache = LRUCache(max_size=1000)


class QwenWebFetchTool(ToolPlugin):
    """Qwen-style web_fetch tool.

    Single execution path: local fetch + LLM summarization.
    Simpler than Gemini with explicit url and prompt parameters.
    """

    name = "qwen_web_fetch_tool"
    version = "0.1.0"

    def _get_web_fetch_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract web_fetch settings from config with defaults.

        All config keys are flat with 'web_fetch_' prefix.
        """
        return {
            "enabled": config.get("web_fetch_enabled", True),
            "timeout_seconds": config.get(
                "web_fetch_timeout_seconds", DEFAULT_TIMEOUT_SECONDS
            ),
            "max_content_chars": config.get(
                "web_fetch_max_content_chars", DEFAULT_MAX_CHARS
            ),
            "rate_limit_requests": config.get("web_fetch_rate_limit_requests", 10),
            "rate_limit_window": config.get("web_fetch_rate_limit_window", 60),
            "summarization_agent_id": config.get("web_fetch_summarization_agent_id"),
            "summarization_model": config.get("web_fetch_summarization_model"),
        }

    # ------------------------------------------------------------------
    # ToolPlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema for web_fetch tool settings."""
        return {
            "web_fetch_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable the web_fetch tool",
            },
            "web_fetch_timeout_seconds": {
                "type": "integer",
                "default": DEFAULT_TIMEOUT_SECONDS,
                "description": "Fetch timeout in seconds",
            },
            "web_fetch_max_content_chars": {
                "type": "integer",
                "default": DEFAULT_MAX_CHARS,
                "description": "Maximum content length in characters",
            },
            "web_fetch_rate_limit_requests": {
                "type": "integer",
                "default": 10,
                "description": "Max requests per rate limit window per host",
            },
            "web_fetch_rate_limit_window": {
                "type": "integer",
                "default": 60,
                "description": "Rate limit window in seconds",
            },
            "web_fetch_summarization_agent_id": {
                "type": "string",
                "default": None,
                "description": "Optional dedicated agent for summarization",
            },
            "web_fetch_summarization_model": {
                "type": "string",
                "default": None,
                "description": "Optional model override for summarization",
            },
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI schema elements for web_fetch tool settings."""
        return [
            {
                "type": "checkbox",
                "key": "web_fetch_enabled",
                "label": "Enable web fetch",
            },
            {
                "type": "number",
                "key": "web_fetch_timeout_seconds",
                "label": "Timeout (seconds)",
                "description": "Seconds to wait for URL response",
            },
            {
                "type": "number",
                "key": "web_fetch_max_content_chars",
                "label": "Max content chars",
            },
            {
                "type": "text",
                "key": "web_fetch_summarization_agent_id",
                "label": "Summarization agent",
                "description": "Optional dedicated agent for summarization",
                "placeholder": "e.g., summarizer",
            },
            {
                "type": "text",
                "key": "web_fetch_summarization_model",
                "label": "Summarization model",
                "description": "Optional model override for summarization",
            },
        ]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with configuration."""
        web_fetch_cfg = self._get_web_fetch_config(config)

        return {
            "config": config,
            "web_fetch_config": web_fetch_cfg,
        }

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]],
        models: Optional[List[str]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[bool]:
        """Check if tool is enabled based on configuration.

        Returns False if explicitly disabled, None to fall back to tag checks.
        """
        web_fetch_cfg = self._get_web_fetch_config(config)

        if not web_fetch_cfg.get("enabled", True):
            return False

        return None

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the web_fetch tool schema with url and prompt parameters."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_fetch",
                    "description": (
                        "Fetches content from a specified URL and processes it using an AI model.\n"
                        "- Takes a URL and a prompt as input\n"
                        "- Fetches the URL content, converts HTML to markdown\n"
                        "- Processes the content with the prompt using a small, fast model\n"
                        "- Returns the model's response about the content\n"
                        "- Use this tool when you need to retrieve and analyze web content\n\n"
                        "Usage notes:\n"
                        "  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that "
                        "tool instead of this one, as it may have fewer restrictions. All MCP-provided "
                        'tools start with "mcp__".\n'
                        "  - The URL must be a fully-formed valid URL\n"
                        "  - The prompt should describe what information you want to extract from the page\n"
                        "  - This tool is read-only and does not modify any files\n"
                        "  - Results may be summarized if the content is very large\n"
                        "  - Supports both public and private/localhost URLs using direct fetch"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch content from",
                            },
                            "prompt": {
                                "type": "string",
                                "description": "The prompt to run on the fetched content",
                            },
                        },
                        "required": ["url", "prompt"],
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
        """Execute the web_fetch tool synchronously.

        This wraps the async implementation for sync callers.
        """
        if tool_name != "web_fetch":
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
        """Execute the web_fetch tool asynchronously.

        Yields a single result dict with the response.
        """
        if tool_name != "web_fetch":
            yield {"success": False, "error": f"Unknown tool: {tool_name}"}
            return

        # Run async implementation synchronously
        result = asyncio.run(self._execute_async(payload, state, context))
        yield result

    def _check_rate_limit(
        self, url: str, state: Dict[str, Any]
    ) -> tuple[bool, Optional[int]]:
        """Check rate limit for a URL using shared utility.

        Returns (allowed, wait_seconds) tuple.
        """
        web_fetch_cfg = state.get("web_fetch_config", {})
        return check_rate_limit(
            url,
            _rate_limit_cache,
            max_requests=web_fetch_cfg.get("rate_limit_requests", 10),
            window_seconds=web_fetch_cfg.get("rate_limit_window", 60),
        )

    async def _execute_async(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Main async execution logic.

        Single execution path: fetch + summarize.
        """
        config = state.get("config", {})
        web_fetch_cfg = self._get_web_fetch_config(config)

        # Check if explicitly disabled
        if not web_fetch_cfg.get("enabled", True):
            return {
                "success": False,
                "error": "Web fetch is disabled. Enable it via web_fetch_enabled configuration.",
            }

        # Validate URL parameter
        url = arguments.get("url")
        if not url or not isinstance(url, str) or not url.strip():
            return {"success": False, "error": "The 'url' parameter is required."}

        # Validate prompt parameter
        prompt = arguments.get("prompt")
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            return {
                "success": False,
                "error": "The 'prompt' parameter is required.",
            }

        # Validate URL format
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return {
                    "success": False,
                    "error": f"Unsupported protocol: {parsed.scheme}. URL must start with http:// or https://.",
                }
            if not parsed.hostname:
                return {"success": False, "error": "URL must have a valid hostname."}
        except Exception as e:
            return {"success": False, "error": f"Invalid URL: {e}"}

        # Normalize GitHub URL
        url = normalize_github_url(url)

        # Check rate limit
        allowed, wait_seconds = self._check_rate_limit(url, state)
        if not allowed:
            return {
                "success": False,
                "error": f"Rate limit exceeded. Please wait {wait_seconds} seconds.",
            }

        # Execute fetch + summarize
        return await self._execute_fetch_summarize(prompt, url, state, context)

    async def _execute_fetch_summarize(
        self,
        prompt: str,
        url: str,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute fetch + LLM summarization.

        Uses web_fetch_shared for fetching and summarize_content_sync for LLM calls.
        """
        web_fetch_cfg = state.get("web_fetch_config", {})

        try:
            # Fetch URL content
            fetch_result = await fetch_url(
                url,
                timeout_seconds=web_fetch_cfg.get(
                    "timeout_seconds", DEFAULT_TIMEOUT_SECONDS
                ),
            )

            if fetch_result.is_error:
                return {
                    "success": False,
                    "error": f"Error during fetch for {url}: {fetch_result.error_message}",
                }

            # Extract text from HTML
            content = extract_text(
                fetch_result.content,
                fetch_result.content_type,
            )

            if not content.strip():
                return {
                    "success": False,
                    "error": f"No text content extracted from {url}",
                }

            max_chars = web_fetch_cfg.get("max_content_chars", DEFAULT_MAX_CHARS)
            content = truncate_content(content, max_chars=max_chars)

            summarization_prompt = (
                f'The user requested: "{prompt}"\n\n'
                f"I have fetched the content from {url}. "
                f"Please use the following content to answer the user's request.\n\n"
                f"---\n{content}\n---"
            )

            # Use shared summarization utility
            success, result = run_prompted_summary_request(
                summarization_prompt,
                content,
                context,
                fallback_agent_id=web_fetch_cfg.get("summarization_agent_id"),
                fallback_model=web_fetch_cfg.get("summarization_model"),
            )

            if success:
                return {
                    "success": True,
                    "result": result,
                }
            else:
                return {
                    "success": False,
                    "error": result,
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Fetch error: {e}",
            }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format the tool result for LLM consumption."""
        if result.get("success"):
            content = result.get("result", "")
            # Add success message for display
            return content
        return f"Error: {result.get('error', 'Unknown error')}"

    def to_display_format(
        self, text: str, result: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format for display in UI."""
        return {
            "type": "text",
            "content": text,
            "metadata": {
                "success": result.get("success", False),
            },
        }
