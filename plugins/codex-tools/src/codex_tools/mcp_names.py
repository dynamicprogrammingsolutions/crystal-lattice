from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable


MCP_PREFIX = "mcp__"
MCP_DELIMITER = "__"
MAX_TOOL_NAME_LENGTH = 64
HASH_LEN = 12


@dataclass(frozen=True)
class QualifiedMCPToolName:
    server_name: str
    raw_tool_name: str
    model_tool_name: str


def sanitize_responses_api_tool_name(value: str) -> str:
    out = []
    for char in value:
        if char.isascii() and (char.isalnum() or char == "_"):
            out.append(char)
        else:
            out.append("_")
    sanitized = "".join(out)
    return sanitized or "_"


def qualify_codex_mcp_names(
    server_name: str,
    tool_names: Iterable[str],
) -> list[QualifiedMCPToolName]:
    seen: set[str] = set()
    qualified: list[QualifiedMCPToolName] = []
    namespace = sanitize_responses_api_tool_name(f"{MCP_PREFIX}{server_name}{MCP_DELIMITER}")
    for raw_tool_name in tool_names:
        base_name = sanitize_responses_api_tool_name(raw_tool_name)
        model_tool_name = _unique_name(namespace, base_name, f"{server_name}\0{raw_tool_name}", seen)
        qualified.append(
            QualifiedMCPToolName(
                server_name=server_name,
                raw_tool_name=raw_tool_name,
                model_tool_name=model_tool_name,
            )
        )
    return qualified


def _unique_name(namespace: str, tool_name: str, identity: str, seen: set[str]) -> str:
    candidate = f"{namespace}{tool_name}"
    if len(candidate) <= MAX_TOOL_NAME_LENGTH and candidate not in seen:
        seen.add(candidate)
        return candidate

    attempt = 0
    while True:
        suffix = "_" + hashlib.sha1(f"{identity}\0{attempt}".encode("utf-8")).hexdigest()[:HASH_LEN]
        max_tool_len = max(1, MAX_TOOL_NAME_LENGTH - len(namespace) - len(suffix))
        truncated = tool_name[:max_tool_len]
        candidate = f"{namespace}{truncated}{suffix}"
        if len(candidate) > MAX_TOOL_NAME_LENGTH:
            overflow = len(candidate) - MAX_TOOL_NAME_LENGTH
            if overflow > 0:
                namespace_part = namespace[:-overflow] if overflow < len(namespace) else ""
                candidate = f"{namespace_part}{truncated}{suffix}"
        if candidate not in seen:
            seen.add(candidate)
            return candidate
        attempt += 1