"""Gemini-style web_fetch tool implementation.

This tool uses the Gemini API's server-side URL grounding capability
as the primary path, falling back to local HTTP fetch + LLM summarization
when the primary fails or for private IP URLs.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core.types import ToolPlugin
from web_fetch_shared import (
    DEFAULT_MAX_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    extract_text,
    fetch_url,
    format_gemini_citations,
    is_private_url,
    normalize_github_url,
    parse_urls_from_text,
    truncate_content,
)

# Lazy import for google-genai
genai = None


# Constants
MAX_URLS = 20
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 10


class GeminiWebFetchTool(ToolPlugin):
    """Gemini-style web_fetch tool.

    Uses Gemini API server-side URL grounding as primary path,
    with fallback to local fetch + LLM summarization.
    """

    name = "gemini_web_fetch_tool"
    version = "0.1.0"

    # Module-level rate limit state (shared across instances)
    _host_history: Dict[str, List[float]] = {}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with API key and configuration.

        Checks for Gemini API key in config or environment.
        Tool is disabled if no key is available.
        """
        api_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        return {
            "config": config,
            "api_key": api_key,
            "disabled": api_key is None,
            "timeout_seconds": config.get("web_fetch_timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
            "max_content_chars": config.get("web_fetch_max_content_chars", DEFAULT_MAX_CHARS),
        }

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]],
        models: Optional[List[str]],
        context: Optional[Dict[str, Any]],
    ) -> Optional[bool]:
        """Check if tool is enabled based on API key availability.

        Returns False if disabled (no API key), None to fall back to tag checks.
        """
        # Check config parameter for API key (passed from wrapper)
        api_key = config.get("gemini_api_key") if config else None
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return False
        return None

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the web_fetch tool schema matching Gemini CLI."""
        return [
            {
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

    async def _execute_async(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Main async execution logic."""
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
                "error": f"Error(s) in prompt URLs:\n- " + "\n- ".join(url_errors),
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

        # Check rate limiting for first URL (primary rate limit target)
        first_url = normalized_urls[0]
        allowed, wait_seconds = self._check_rate_limit(first_url)
        if not allowed:
            return {
                "success": False,
                "error": f"Rate limit exceeded for host. Please wait {wait_seconds} seconds before trying again.",
            }

        # Check if URL is private (triggers fallback)
        if is_private_url(first_url):
            return await self._execute_fallback(prompt, normalized_urls[0], state, context)

        # Try primary path (Gemini API)
        result = await self._execute_primary(prompt, state)

        # If primary failed or returned no usable content, try fallback
        if not result.get("success") or result.get("_needs_fallback"):
            # Clean up internal flag
            result.pop("_needs_fallback", None)
            return await self._execute_fallback(prompt, normalized_urls[0], state, context)

        return result

    def _check_rate_limit(self, url: str) -> Tuple[bool, Optional[int]]:
        """Check rate limit for a URL.

        Returns (allowed, wait_seconds) tuple.
        """
        try:
            from urllib.parse import urlparse

            hostname = urlparse(url).hostname
            if not hostname:
                return True, None

            now = time.time()
            window_start = now - RATE_LIMIT_WINDOW_SECONDS

            # Get and clean history
            history = GeminiWebFetchTool._host_history.get(hostname, [])
            history = [t for t in history if t > window_start]

            if len(history) >= MAX_REQUESTS_PER_WINDOW:
                wait = int(history[0] + RATE_LIMIT_WINDOW_SECONDS - now)
                GeminiWebFetchTool._host_history[hostname] = history
                return False, max(1, wait)

            history.append(now)
            GeminiWebFetchTool._host_history[hostname] = history
            return True, None

        except Exception:
            # If parsing fails, allow the request
            return True, None

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

        try:
            # Lazy import google-genai
            from google import genai

            # Create client
            client = genai.Client(api_key=api_key)

            # Call Gemini API with the prompt
            # The Gemini API will process URLs in the prompt using server-side grounding
            response = client.models.generate_content(
                model="gemini-2.5-flash",
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
                if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
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
                                "groundingChunkIndices": list(s.grounding_chunk_indices),
                            }
                            for s in gm.grounding_supports
                            if hasattr(s, "segment") and hasattr(s, "grounding_chunk_indices")
                        ]

                # Check for URL context metadata (indicates fetch status)
                url_context_meta = getattr(candidate, "url_context_metadata", None)
                if url_context_meta and hasattr(url_context_meta, "url_metadata"):
                    all_statuses = [m.url_retrieval_status for m in url_context_meta.url_metadata]
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

        Uses web_fetch_shared for fetching and context["core"] for LLM calls.
        """
        try:
            # Fetch URL content
            fetch_result = await fetch_url(
                url,
                timeout_seconds=state.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
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

            # Truncate content
            max_chars = state.get("max_content_chars", DEFAULT_MAX_CHARS)
            content = truncate_content(content, max_chars=max_chars)

            # Use LLM for summarization if context provides core
            if context and context.get("core"):
                core = context["core"]
                config = context.get("config", {})

                # Build summarization prompt
                summarization_prompt = (
                    f'The user requested: "{prompt}"\n\n'
                    f"I was unable to access the URL directly via the Gemini API. "
                    f"Instead, I have fetched the raw content. Please use the following content "
                    f"to answer the request. Do not attempt to access the URL again.\n\n"
                    f"---\n{content}\n---"
                )

                # Create temporary session and call LLM
                from agent_core import Session

                temp_session = Session(session_id="web_fetch_fallback", messages=[])
                temp_session = core.add_message(temp_session, "user", summarization_prompt)

                # Stream response and collect
                result_text = ""
                for event in core.stream_request(temp_session, config):
                    if event.get("kind") == "response_chunk":
                        result_text += event.get("content", "")
                    elif event.get("kind") == "response_complete":
                        result_text = event.get("content", result_text)

                return {
                    "success": True,
                    "result": result_text.strip() or content,
                }

            # No LLM available, return raw content
            return {
                "success": True,
                "result": content,
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
