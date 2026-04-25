"""Gemini-style web_fetch tool implementation.

This tool uses the Gemini API's server-side URL grounding capability
as the primary path, falling back to local HTTP fetch + LLM summarization
when the primary fails or for private IP URLs.

Configuration keys (all flat, prefixed with web_fetch_):
- web_fetch_enabled: Enable the tool (default: True)
- web_fetch_use_gemini_api: Use Gemini API for primary path (default: True, requires API key)
- web_fetch_direct_mode: Use direct URL mode instead of prompt mode (default: False)
- web_fetch_primary_model: Gemini model for primary path (default: "web-fetch")
- web_fetch_fallback_agent_id: Optional dedicated agent for fallback summarization
- web_fetch_fallback_settings_overrides: Settings to override for fallback path
- web_fetch_timeout_seconds: Fetch timeout in seconds (default: 10)
- web_fetch_max_content_chars: Max content length in chars (default: 100000)
- web_fetch_rate_limit_requests: Max requests per window per host (default: 10)
- web_fetch_rate_limit_window: Rate limit window in seconds (default: 60)
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Iterator, List, Optional

from agent_core.types import ToolPlugin
from web_fetch_shared import (
    DEFAULT_MAX_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    LRUCache,
    check_rate_limit,
    extract_text,
    fetch_url,
    format_gemini_citations,
    is_private_url,
    normalize_github_url,
    parse_urls_from_text,
    run_prompted_summary_request,
    truncate_content,
)

# Lazy import for google-genai
genai = None


# Constants
MAX_URLS = 20
DEFAULT_PRIMARY_MODEL = "web-fetch"

# Module-level LRU cache for rate limiting (shared across instances)
_rate_limit_cache = LRUCache(max_size=1000)


class GeminiWebFetchTool(ToolPlugin):
    """Gemini-style web_fetch tool.

    Uses Gemini API server-side URL grounding as primary path,
    with fallback to local fetch + LLM summarization.

    Supports two modes:
    - Prompt mode (default): URLs embedded in prompt, processed via Gemini API
    - Direct mode: Single URL per call, fetched directly without Gemini API
    """

    name = "gemini_web_fetch_tool"
    version = "0.4.0"

    def _get_web_fetch_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract web_fetch settings from config with defaults.

        All config keys are flat with 'web_fetch_' prefix.
        """
        return {
            "enabled": config.get("web_fetch_enabled", True),
            "use_gemini_api": config.get("web_fetch_use_gemini_api", True),
            "direct_mode": config.get("web_fetch_direct_mode", False),
            "primary_model": config.get(
                "web_fetch_primary_model", DEFAULT_PRIMARY_MODEL
            ),
            "fallback_agent_id": config.get("web_fetch_fallback_agent_id"),
            "fallback_settings_overrides": config.get(
                "web_fetch_fallback_settings_overrides", {}
            ),
            "timeout_seconds": config.get(
                "web_fetch_timeout_seconds", DEFAULT_TIMEOUT_SECONDS
            ),
            "max_content_chars": config.get(
                "web_fetch_max_content_chars", DEFAULT_MAX_CHARS
            ),
            "rate_limit_requests": config.get("web_fetch_rate_limit_requests", 10),
            "rate_limit_window": config.get("web_fetch_rate_limit_window", 60),
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
            "web_fetch_use_gemini_api": {
                "type": "boolean",
                "default": True,
                "description": "Use Gemini API for server-side URL grounding (requires API key)",
            },
            "web_fetch_direct_mode": {
                "type": "boolean",
                "default": False,
                "description": "Use direct URL fetch mode instead of prompt mode",
            },
            "web_fetch_primary_model": {
                "type": "string",
                "default": DEFAULT_PRIMARY_MODEL,
                "description": "Gemini model for primary path (server-side URL grounding)",
            },
            "web_fetch_fallback_agent_id": {
                "type": "string",
                "default": None,
                "description": "Optional dedicated agent for fallback summarization",
            },
            "web_fetch_fallback_settings_overrides": {
                "type": "object",
                "default": {},
                "description": "Settings to override for fallback path (e.g., model, temperature)",
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
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI schema elements for web_fetch tool settings.

        Elements are conditionally visible based on API key availability
        and use_gemini_api setting.
        """
        api_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        use_gemini = config.get("web_fetch_use_gemini_api", True)

        elements = [
            {
                "type": "checkbox",
                "key": "web_fetch_enabled",
                "label": "Enable web fetch",
            },
            {
                "type": "checkbox",
                "key": "web_fetch_direct_mode",
                "label": "Direct URL mode",
                "description": "Fetch single URLs directly without prompt processing",
            },
        ]

        # Only show Gemini API option when API key is available
        if api_key:
            elements.append(
                {
                    "type": "checkbox",
                    "key": "web_fetch_use_gemini_api",
                    "label": "Use Gemini API",
                    "description": "Server-side URL grounding via Gemini (requires API key)",
                }
            )

            # Only show primary model when using Gemini API
            if use_gemini:
                elements.append(
                    {
                        "type": "text",
                        "key": "web_fetch_primary_model",
                        "label": "Primary model",
                        "description": "Gemini model for URL grounding",
                        "placeholder": "web-fetch",
                    }
                )

        elements.append(
            {
                "type": "number",
                "key": "web_fetch_timeout_seconds",
                "label": "URL fetch timeout",
                "description": "Seconds to wait for URL response",
            }
        )

        return elements

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with API key and configuration.

        Checks for Gemini API key in config or environment.
        Tool behavior depends on use_gemini_api setting.
        """
        api_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        web_fetch_cfg = self._get_web_fetch_config(config)

        return {
            "config": config,
            "api_key": api_key,
            "web_fetch_config": web_fetch_cfg,
        }

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]],
        models: Optional[List[str]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[bool]:
        """Check if tool is enabled based on API key availability.

        Note: The web_fetch_enabled config is handled at execution time, not here.
        This ensures the "Enable web fetch" UI toggle is always visible.

        Returns False only when there's a hard requirement not met (missing API key).
        Returns None to fall back to tag checks otherwise.
        """
        web_fetch_cfg = self._get_web_fetch_config(config)

        # In direct mode, we don't need a Gemini API key
        if web_fetch_cfg.get("direct_mode"):
            return None

        # Check if using Gemini API
        use_gemini = web_fetch_cfg.get("use_gemini_api", True)

        # If not using Gemini API, we don't need an API key (fallback only)
        if not use_gemini:
            return None

        # In prompt mode with Gemini, we need a Gemini API key
        api_key = config.get("gemini_api_key") if config else None
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return False

        return None

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the web_fetch tool schema based on mode.

        In direct mode, returns a schema with 'url' parameter.
        In prompt mode (default), returns a schema with 'prompt' parameter.
        """
        config = state.get("config", {})
        web_fetch_cfg = self._get_web_fetch_config(config)
        direct_mode = web_fetch_cfg.get("direct_mode", False)

        if direct_mode:
            return [self._get_direct_mode_schema()]
        return [self._get_prompt_mode_schema()]

    def _get_prompt_mode_schema(self) -> Dict[str, Any]:
        """Return the prompt mode schema (default)."""
        return {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": (
                    "Processes content from URL(s), including local and private network addresses "
                    "(e.g., localhost), embedded in a prompt. Include up to 20 URLs and instructions "
                    "(e.g., summarize, extract specific data) directly in the 'prompt' parameter."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": (
                                "A comprehensive prompt that includes the URL(s) (up to 20) to fetch "
                                "and specific instructions on how to process their content "
                                '(e.g., "Summarize https://example.com/article and extract key points '
                                'from https://another.com/data"). All URLs to be fetched must be valid '
                                'and complete, starting with "http://" or "https://", and be fully-formed '
                                'with a valid hostname (e.g., a domain name like "example.com" or an IP '
                                'address). For example, "https://example.com" is valid, but "example.com" is not.'
                            ),
                        }
                    },
                    "required": ["prompt"],
                },
            },
        }

    def _get_direct_mode_schema(self) -> Dict[str, Any]:
        """Return the direct mode schema (experimental)."""
        return {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": (
                    "Fetch content from a URL directly. Send multiple requests "
                    "for this tool if multiple URL fetches are needed."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to fetch. Must be a valid http or https URL.",
                        }
                    },
                    "required": ["url"],
                },
            },
        }

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

    async def _execute_async(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Main async execution logic.

        Dispatches to prompt mode or direct mode based on configuration.
        """
        config = state.get("config", {})
        web_fetch_cfg = self._get_web_fetch_config(config)

        # Check if explicitly disabled
        if not web_fetch_cfg.get("enabled", True):
            return {
                "success": False,
                "error": "Web fetch is disabled. Enable it via web_fetch_enabled configuration.",
            }

        direct_mode = web_fetch_cfg.get("direct_mode", False)

        if direct_mode:
            return await self._execute_direct_mode(arguments, state, context)
        return await self._execute_prompt_mode(arguments, state, context)

    async def _execute_direct_mode(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute in direct URL mode.

        Always uses fallback path (local fetch + optional LLM summarization).
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

        # Normalize GitHub URL
        url = normalize_github_url(url)

        # Check rate limit
        allowed, wait_seconds = self._check_rate_limit(url, state)
        if not allowed:
            return {
                "success": False,
                "error": f"Rate limit exceeded. Please wait {wait_seconds} seconds.",
            }

        # Build a simple prompt for summarization context
        prompt = f"Fetch content from {url}"

        # Always use fallback path in direct mode
        return await self._execute_fallback(prompt, url, state, context)

    def _check_rate_limit(
        self, url: str, state: Dict[str, Any]
    ) -> tuple[bool, Optional[int]]:
        """Check rate limit for a URL using shared utility.

        Wrapper around web_fetch_shared.check_rate_limit for test compatibility.

        Returns (allowed, wait_seconds) tuple.
        """
        web_fetch_cfg = state.get("web_fetch_config", {})
        return check_rate_limit(
            url,
            _rate_limit_cache,
            max_requests=web_fetch_cfg.get("rate_limit_requests", 10),
            window_seconds=web_fetch_cfg.get("rate_limit_window", 60),
        )

    async def _execute_prompt_mode(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute in prompt mode.

        Uses Gemini API for primary path when enabled and API key available,
        otherwise uses fallback path directly.
        """
        # Validate prompt parameter
        prompt = arguments.get("prompt")
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            return {
                "success": False,
                "error": "The 'prompt' parameter cannot be empty and must contain URL(s) and instructions.",
            }

        # Parse URLs from prompt
        valid_urls, url_errors = parse_urls_from_text(prompt)

        if url_errors:
            return {
                "success": False,
                "error": "Error(s) in prompt URLs:\n- " + "\n- ".join(url_errors),
            }

        if not valid_urls:
            return {
                "success": False,
                "error": "The 'prompt' must contain at least one valid URL (starting with http:// or https://).",
            }

        if len(valid_urls) > MAX_URLS:
            return {
                "success": False,
                "error": f"Too many URLs in prompt. Maximum is {MAX_URLS}, found {len(valid_urls)}.",
            }

        # Normalize GitHub URLs
        normalized_urls = [normalize_github_url(url) for url in valid_urls]

        # Check rate limiting for first URL
        first_url = normalized_urls[0]
        allowed, wait_seconds = self._check_rate_limit(first_url, state)
        if not allowed:
            return {
                "success": False,
                "error": f"Rate limit exceeded for host. Please wait {wait_seconds} seconds before trying again.",
            }

        # Check if URL is private (always triggers fallback)
        if is_private_url(first_url):
            return await self._execute_fallback(prompt, first_url, state, context)

        # Determine execution path based on use_gemini_api and API key availability
        web_fetch_cfg = state.get("web_fetch_config", {})
        use_gemini = web_fetch_cfg.get("use_gemini_api", True)
        api_key = state.get("api_key")

        # Skip primary path if: use_gemini_api is False OR no API key
        if not use_gemini or not api_key:
            return await self._execute_fallback(prompt, first_url, state, context)

        # Try primary path (Gemini API)
        result = await self._execute_primary(prompt, state)

        # If primary failed or returned no usable content, try fallback
        if not result.get("success") or result.get("_needs_fallback"):
            # Clean up internal flag
            result.pop("_needs_fallback", None)
            return await self._execute_fallback(prompt, first_url, state, context)

        return result

    async def _execute_primary(
        self,
        prompt: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute primary path using Gemini API server-side fetch.

        Uses the google-genai SDK to call Gemini with URL grounding.
        """
        api_key = state.get("api_key")
        if not api_key:
            return {
                "success": False,
                "error": "No Gemini API key available for primary fetch.",
                "_needs_fallback": True,
            }

        # Get configurable model
        web_fetch_cfg = state.get("web_fetch_config", {})
        primary_model = web_fetch_cfg.get("primary_model", DEFAULT_PRIMARY_MODEL)

        try:
            # Lazy import google-genai
            from google import genai

            # Create client
            client = genai.Client(api_key=api_key)

            # Call Gemini API with the prompt using configurable model
            response = client.models.generate_content(
                model=primary_model,
                contents=prompt,
            )

            # Extract response text
            response_text = ""
            if response.candidates and response.candidates[0].content:
                parts = response.candidates[0].content.parts
                for part in parts:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text

            # Extract grounding metadata
            grounding_chunks = []
            grounding_supports = []

            if response.candidates:
                candidate = response.candidates[0]

                # Check for grounding metadata
                if (
                    hasattr(candidate, "grounding_metadata")
                    and candidate.grounding_metadata
                ):
                    gm = candidate.grounding_metadata
                    if hasattr(gm, "grounding_chunks"):
                        grounding_chunks = [
                            {"web": {"uri": chunk.web.uri, "title": chunk.web.title}}
                            for chunk in gm.grounding_chunks
                            if hasattr(chunk, "web") and chunk.web
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

                # Check for URL context metadata (indicates fetch status)
                url_context_meta = getattr(candidate, "url_context_metadata", None)
                if url_context_meta and hasattr(url_context_meta, "url_metadata"):
                    all_statuses = [
                        m.url_retrieval_status for m in url_context_meta.url_metadata
                    ]
                    if all(s != "URL_RETRIEVAL_STATUS_SUCCESS" for s in all_statuses):
                        return {
                            "success": False,
                            "error": "Primary fetch failed: URLs could not be retrieved.",
                            "_needs_fallback": True,
                        }

            # Check if we got usable content
            if not response_text.strip() and not grounding_chunks:
                return {
                    "success": False,
                    "error": "No usable content from Gemini API.",
                    "_needs_fallback": True,
                }

            # Format response with citations
            if grounding_chunks:
                formatted_text = format_gemini_citations(
                    response_text, grounding_chunks, grounding_supports
                )
            else:
                formatted_text = response_text

            return {
                "success": True,
                "result": formatted_text,
            }

        except ImportError as e:
            return {
                "success": False,
                "error": f"google-genai SDK not installed: {e}",
                "_needs_fallback": True,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Gemini API error: {e}",
                "_needs_fallback": True,
            }

    async def _execute_fallback(
        self,
        prompt: str,
        url: str,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute fallback path: local fetch + LLM summarization.

        Uses web_fetch_shared for fetching and summarize_content_sync for LLM calls.
        Supports optional fallback agent and settings overrides.
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
                    "error": f"Failed to fetch {url}: {fetch_result.error_message}",
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

            # Truncate content before building the Gemini-owned fallback prompt.
            max_chars = web_fetch_cfg.get("max_content_chars", DEFAULT_MAX_CHARS)
            content = truncate_content(content, max_chars=max_chars)

            summarization_prompt = (
                f'The user requested: "{prompt}"\n\n'
                f"I was unable to access the URL directly via the Gemini API. "
                f"Instead, I have fetched the raw content. Please use the following content "
                f"to answer the request. Do not attempt to access the URL again.\n\n"
                f"---\n{content}\n---"
            )

            # Build context with settings overrides for summarization
            fallback_settings_overrides = web_fetch_cfg.get(
                "fallback_settings_overrides", {}
            )
            summarization_context = context
            if fallback_settings_overrides and context:
                config = context.get("config", {})
                summarization_context = {
                    **context,
                    "config": {**config, **fallback_settings_overrides},
                }

            # Use shared summarization utility
            success, result = run_prompted_summary_request(
                summarization_prompt,
                content,
                summarization_context,
                fallback_agent_id=web_fetch_cfg.get("fallback_agent_id"),
                fallback_model=fallback_settings_overrides.get("model"),
            )

            return {
                "success": success,
                "result": result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback fetch error: {e}",
            }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format the tool result for LLM consumption."""
        if result.get("success"):
            return result.get("result", "")
        return f"Error: {result.get('error', 'Unknown error')}"

    def to_display_format(
        self, text: str, result: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format for display in UI."""
        return {"type": "text", "content": text}
