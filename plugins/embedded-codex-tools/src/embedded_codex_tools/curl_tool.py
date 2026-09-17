from __future__ import annotations

import shlex
import time
from typing import Any

from agent_core.types import ToolPlugin
from embedded_tools_shared import FetchError, FetchPolicy, fetch_public_url

from .command_result import CommandResultMixin, command_error, command_result


CURL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "curl",
        "description": (
            "Fetch one public HTTP(S) URL with curl-like behavior. Equivalent to "
            "`curl -L --fail --silent --show-error <url>`. This is a bounded "
            "GET-only fetch tool, not a general shell command."
        ),
        "strict": False,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Public HTTP(S) URL",
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Follow redirects, equivalent to `curl -L`",
                },
                "fail_on_http_error": {
                    "type": "boolean",
                    "description": "Return exit 22 for HTTP 4xx/5xx, like `--fail`",
                },
                "timeout_seconds": {
                    "type": "number",
                    "minimum": 1,
                    "description": "Requested total timeout; app limits remain authoritative",
                },
                "max_bytes": {
                    "type": "integer",
                    "minimum": 1024,
                    "description": "Requested response cap; app limits remain authoritative",
                },
                "include_headers": {
                    "type": "boolean",
                    "description": "Include response headers before the body",
                },
            },
            "required": ["url"],
        },
    },
}


class CodexLikeCurlTool(CommandResultMixin, ToolPlugin):
    name = "embedded_codex_curl"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {
            "default_timeout_seconds": float(
                config.get("web_fetch_timeout_seconds", 20)
            ),
            "default_max_bytes": int(
                config.get("web_fetch_max_bytes", 1024 * 1024)
            ),
            "max_text_chars": int(config.get("web_fetch_max_chars", 100_000)),
        }

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [CURL_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool:
        _ = payload, state
        return tool_name == "curl"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        started = time.monotonic()
        if tool_name != "curl" or not isinstance(payload, dict):
            return command_error(
                "curl",
                "curl: input must be an object",
                started=started,
            )
        url = payload.get("url")
        if not isinstance(url, str) or not url:
            return command_error(
                "curl",
                "curl: url must be a non-empty string",
                started=started,
            )
        follow_redirects = bool(payload.get("follow_redirects", True))
        fail_on_http_error = bool(payload.get("fail_on_http_error", True))
        command_parts = ["curl"]
        if follow_redirects:
            command_parts.append("-L")
        if fail_on_http_error:
            command_parts.append("--fail")
        command_parts.extend(["--silent", "--show-error", shlex.quote(url)])
        command = " ".join(command_parts)
        timeout = payload.get("timeout_seconds")
        timeout = (
            float(timeout)
            if isinstance(timeout, (int, float))
            else state["default_timeout_seconds"]
        )
        max_bytes = payload.get("max_bytes")
        max_bytes = (
            int(max_bytes)
            if isinstance(max_bytes, int)
            else state["default_max_bytes"]
        )
        try:
            page = fetch_public_url(
                url,
                policy=FetchPolicy(
                    timeout_seconds=timeout,
                    max_bytes=max_bytes,
                    max_redirects=5 if follow_redirects else 0,
                    max_text_chars=state["max_text_chars"],
                ),
            )
            if fail_on_http_error and page.status_code >= 400:
                return command_error(
                    command,
                    (
                        f"curl: ({page.status_code}) "
                        f"HTTP {page.status_code} {page.reason}"
                    ),
                    exit_code=22,
                    started=started,
                )
            body = page.body_text[: state["max_text_chars"]]
            output_parts: list[str] = []
            if bool(payload.get("include_headers", False)):
                output_parts.append(f"HTTP {page.status_code} {page.reason}".strip())
                output_parts.extend(
                    f"{name}: {value}" for name, value in page.headers
                )
                output_parts.append("")
            output_parts.append(body)
            return command_result(
                command,
                "\n".join(output_parts),
                started=started,
                truncated=(
                    page.truncated_bytes
                    or len(page.body_text) > state["max_text_chars"]
                ),
            )
        except (FetchError, OSError, ValueError) as error:
            return command_error(command, f"curl: {error}", exit_code=7, started=started)