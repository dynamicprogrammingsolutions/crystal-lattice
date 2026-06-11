# Licensing note:
# This file may contain both original code authored for this repository and
# material derived from or adapted from Claude Code or other
# Anthropic-authored materials.
#
# Original code in this file authored for this repository is licensed under
# the Apache License, Version 2.0.
#
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
#
# Anthropic-derived material in this file is not licensed by us under
# Apache-2.0, and are instead subject to Anthropic's terms:
#
# © Anthropic PBC. All rights reserved. Use is subject to Anthropic's
# Commercial Terms of Service:
# https://www.anthropic.com/legal/commercial-terms

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from web_fetch_shared import (
    BROWSER_USER_AGENT,
    DEFAULT_MAX_CHARS,
    LRUCache,
    check_rate_limit,
    extract_text,
    fetch_url,
    is_private_url,
    normalize_github_url,
    run_prompted_summary_request,
    truncate_content,
)

from .interop import claude_tool_interop_contribution


WEB_FETCH_DESCRIPTION = (
    "IMPORTANT: WebFetch WILL FAIL for authenticated or private URLs. Before using this tool, check if the URL points to an authenticated service (e.g. Google Docs, Confluence, Jira, GitHub). If so, look for a specialized MCP tool that provides authenticated access.\n\n"
    "- Fetches content from a specified URL and processes it using an AI model\n"
    "- Takes a URL and a prompt as input\n"
    "- Fetches the URL content, converts HTML to markdown\n"
    "- Processes the content with the prompt using a small, fast model\n"
    "- Returns the model's response about the content\n"
    "- Use this tool when you need to retrieve and analyze web content\n\n"
    "Usage notes:\n"
    "  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool instead of this one, as it may have fewer restrictions.\n"
    "  - The URL must be a fully-formed valid URL\n"
    "  - HTTP URLs will be automatically upgraded to HTTPS\n"
    "  - The prompt should describe what information you want to extract from the page\n"
    "  - This tool is read-only and does not modify any files\n"
    "  - Results may be summarized if the content is very large\n"
    "  - Includes a self-cleaning 15-minute cache for faster responses when repeatedly accessing the same URL\n"
    "  - When a URL redirects to a different host, the tool will inform you and provide the redirect URL in a special format. You should then make a new WebFetch request with the redirect URL to fetch the content.\n"
    "  - For GitHub URLs, prefer using the gh CLI via Bash instead (e.g., gh pr view, gh issue view, gh api).\n"
)

WEB_FETCH_SCHEMA: Dict[str, Any] = {
    "name": "WebFetch",
    "description": WEB_FETCH_DESCRIPTION,
    "input_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "prompt": {
                "description": "The prompt to run on the fetched content",
                "type": "string",
            },
            "url": {
                "description": "The URL to fetch content from",
                "format": "uri",
                "type": "string",
            },
        },
        "required": ["url", "prompt"],
        "type": "object",
    },
}

DEFAULT_TIMEOUT_MS = 60_000
DEFAULT_CACHE_TTL_SECONDS = 15 * 60

_rate_limit_cache = LRUCache(max_size=1000)
_result_cache: Dict[Tuple[str, str], Tuple[float, bool, str]] = {}


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


def _normalize_url(raw_url: Any) -> str | None:
    if not isinstance(raw_url, str) or not raw_url.strip():
        return None
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None
    candidate = raw_url.strip()
    if is_private_url(candidate):
        return None
    if parsed.scheme == "http":
        candidate = urlunparse(parsed._replace(scheme="https"))
    return normalize_github_url(candidate)


def _cache_get(url: str, prompt: str) -> Tuple[bool, str] | None:
    now = time.time()
    expired = [
        key for key, (expires_at, _is_error, _content) in _result_cache.items()
        if expires_at <= now
    ]
    for key in expired:
        _result_cache.pop(key, None)
    cached = _result_cache.get((url, prompt))
    if cached is None:
        return None
    _expires_at, is_error, content = cached
    return is_error, content


def _cache_set(url: str, prompt: str, *, is_error: bool, content: str) -> None:
    _result_cache[(url, prompt)] = (
        time.time() + DEFAULT_CACHE_TTL_SECONDS,
        is_error,
        content,
    )


async def _probe_cross_host_redirect(
    url: str,
    *,
    prompt: str,
    timeout_seconds: float,
) -> Tuple[bool, str]:
    import aiohttp

    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            url,
            allow_redirects=False,
            headers={"User-Agent": BROWSER_USER_AGENT},
        ) as response:
            if response.status not in {301, 302, 303, 307, 308}:
                return False, ""
            location = response.headers.get("Location")
            if not isinstance(location, str) or not location.strip():
                return False, ""
            redirect_url = urljoin(url, location)
            original_host = urlparse(url).hostname or ""
            redirect_host = urlparse(redirect_url).hostname or ""
            if not original_host or not redirect_host or redirect_host == original_host:
                return False, ""
            return True, (
                "REDIRECT DETECTED: The URL redirects to a different host.\n\n"
                f"Original URL: {url}\n"
                f"Redirect URL: {redirect_url}\n"
                f"Status: {response.status} {response.reason}\n\n"
                "To complete your request, I need to fetch content from the redirected URL. "
                "Please use WebFetch again with these parameters:\n"
                f'- url: "{redirect_url}"\n'
                f'- prompt: "{prompt}"'
            )


def _run_async(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, awaitable)
        return future.result()


class ClaudeWebFetchTool(ToolPlugin):
    name = "claude_web_fetch_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "config": config,
            "working_directory": str(
                Path(str(config.get("working_directory") or os.getcwd())).resolve()
            ),
            "enabled": config.get("web_fetch_enabled", True),
            "timeout_ms": int(config.get("web_fetch_timeout_ms", DEFAULT_TIMEOUT_MS)),
            "max_content_chars": int(
                config.get("web_fetch_max_content_chars", DEFAULT_MAX_CHARS)
            ),
            "rate_limit_requests": int(
                config.get("web_fetch_rate_limit_requests", 10)
            ),
            "rate_limit_window": int(config.get("web_fetch_rate_limit_window", 60)),
            "summarization_agent_id": config.get("web_fetch_summarization_agent_id"),
            "summarization_model": config.get("web_fetch_summarization_model"),
        }

    def get_tool_interop_contribution(self, state: Dict[str, Any]):
        return claude_tool_interop_contribution()

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        if state.get("enabled", True) is False:
            return []
        return [WEB_FETCH_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        **_: Any,
    ) -> Optional[bool]:
        return tool_name == "WebFetch"

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

    async def _execute_async(
        self,
        payload: Dict[str, Any],
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Tuple[bool, str]:
        if state.get("enabled", True) is False:
            return False, "WebFetch is disabled."

        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            return False, "Invalid prompt"

        raw_url = payload.get("url")
        url = _normalize_url(raw_url)
        if url is None:
            return False, "Invalid URL"

        cached = _cache_get(url, prompt.strip())
        if cached is not None:
            is_error, content = cached
            return not is_error, content

        allowed, wait_seconds = check_rate_limit(
            url,
            _rate_limit_cache,
            max_requests=int(state.get("rate_limit_requests", 10)),
            window_seconds=float(state.get("rate_limit_window", 60)),
        )
        if not allowed:
            return False, f"Rate limited. Try again in {wait_seconds} seconds."

        timeout_ms = max(1, int(state.get("timeout_ms", DEFAULT_TIMEOUT_MS)))
        timeout_seconds = timeout_ms / 1000.0

        try:
            redirected, redirect_message = await _probe_cross_host_redirect(
                url,
                prompt=prompt.strip(),
                timeout_seconds=timeout_seconds,
            )
        except TimeoutError:
            return False, f"timeout of {timeout_ms}ms exceeded"
        except Exception:
            redirected = False
            redirect_message = ""

        if redirected:
            _cache_set(url, prompt.strip(), is_error=False, content=redirect_message)
            return True, redirect_message

        fetch_result = await fetch_url(
            url,
            timeout_seconds=timeout_seconds,
            user_agent=BROWSER_USER_AGENT,
        )
        if fetch_result.is_error:
            if fetch_result.error_message and "timed out" in fetch_result.error_message.lower():
                return False, f"timeout of {timeout_ms}ms exceeded"
            return False, fetch_result.error_message or "Fetch failed"

        content = extract_text(
            fetch_result.content,
            fetch_result.content_type,
            output_format="markdown",
        )
        if not content.strip():
            return False, f"No text content extracted from {url}"

        content = truncate_content(
            content,
            max_chars=int(state.get("max_content_chars", DEFAULT_MAX_CHARS)),
        )
        summary_prompt = (
            f'The user requested: "{prompt.strip()}"\n\n'
            f"I fetched content from {url}. "
            "Please answer the user's request using only the fetched content. "
            "Return only the answer content, with no preamble.\n\n"
            f"---\n{content}\n---"
        )
        success, summary = run_prompted_summary_request(
            summary_prompt,
            content,
            context,
            fallback_agent_id=state.get("summarization_agent_id"),
            fallback_model=state.get("summarization_model"),
        )
        result_text = summary.strip() if success and isinstance(summary, str) else content
        _cache_set(url, prompt.strip(), is_error=False, content=result_text)
        return True, result_text

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
        if tool_name != "WebFetch":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "WebFetch input must be an object"}

        tool_use_id = "call_WebFetch"
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                tool_use_id = raw_id

        success, text = _run_async(self._execute_async(payload, state, context))
        return self._result(tool_use_id=tool_use_id, text=text, success=success)

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        content = result.get("anthropic_content")
        if isinstance(content, list) and all(isinstance(item, dict) for item in content):
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
            "single_line": "Web fetch",
        }


__all__ = ["ClaudeWebFetchTool", "WEB_FETCH_SCHEMA"]