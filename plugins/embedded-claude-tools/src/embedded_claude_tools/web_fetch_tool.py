from __future__ import annotations

from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import FetchError, FetchPolicy, fetch_public_url


WEB_FETCH_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "WebFetch",
        "description": (
            "Fetch a public HTTP(S) page and return bounded extracted text for "
            "analysis. Private, local, authenticated, and non-HTTP URLs are rejected."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Public HTTP(S) URL",
                },
                "prompt": {
                    "type": "string",
                    "description": "What information to look for in the fetched page",
                },
            },
            "required": ["url", "prompt"],
        },
    },
}


class ClaudeLikeWebFetchTool(ToolPlugin):
    name = "embedded_claude_web_fetch"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {
            "policy": FetchPolicy(
                timeout_seconds=float(config.get("web_fetch_timeout_seconds", 20)),
                max_bytes=int(config.get("web_fetch_max_bytes", 1024 * 1024)),
                max_redirects=int(config.get("web_fetch_max_redirects", 5)),
                max_text_chars=int(config.get("web_fetch_max_chars", 100_000)),
            ).bounded()
        }

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [WEB_FETCH_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "WebFetch"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "WebFetch" or not isinstance(payload, dict):
            return {"success": False, "error": "WebFetch input must be an object"}
        url = payload.get("url")
        prompt = payload.get("prompt")
        if not isinstance(url, str) or not url:
            return {"success": False, "error": "url must be a non-empty string"}
        if not isinstance(prompt, str) or not prompt:
            return {"success": False, "error": "prompt must be a non-empty string"}
        try:
            page = fetch_public_url(url, policy=state["policy"])
            if page.status_code >= 400:
                raise FetchError(
                    f"HTTP {page.status_code} {page.reason}".strip()
                )
            lines = [
                f"URL: {page.final_url}",
                f"Status: {page.status_code}",
            ]
            if page.title:
                lines.append(f"Title: {page.title}")
            lines.extend(
                [
                    f"Requested focus: {prompt}",
                    "",
                    page.extracted_text,
                ]
            )
            if page.truncated_bytes or page.truncated_text:
                lines.append("\n[Content truncated by app limits]")
            return {
                "success": True,
                "result": "\n".join(lines),
                "url": page.final_url,
                "title": page.title,
            }
        except (FetchError, OSError, ValueError) as error:
            return {"success": False, "error": str(error)}

    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        _ = state
        if result.get("success"):
            return str(result.get("result") or "")
        return f"Error: {result.get('error')}"

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = state
        return {
            "type": "text",
            "content": text,
            "single_line": (
                f"WebFetch: {result.get('title') or result.get('url') or 'page'}"
            ),
        }