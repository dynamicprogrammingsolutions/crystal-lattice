"""Provider-defined cost buckets for the OpenAI Responses plugin.

Cost buckets attribute usage records in the generic cost tracking store. The
bucket base can be altered by config (``cost_bucket``), but the final bucket
is always defined by this provider: the active endpoint appends a suffix
(``-chatgpt`` for the ChatGPT backend, ``-api`` for the OpenAI API).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


DEFAULT_OPENAI_RESPONSES_COST_BUCKET = "openai-responses"

_COST_BUCKET_AUTH_MODE_SUFFIXES = {
    "chatgpt": "-chatgpt",
    "api": "-api",
}


def cost_bucket_base(config: Optional[Dict[str, Any]]) -> str:
    """Return the configured bucket base, falling back to the default."""

    raw = config.get("cost_bucket") if isinstance(config, dict) else None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return DEFAULT_OPENAI_RESPONSES_COST_BUCKET


def resolve_cost_bucket(
    config: Optional[Dict[str, Any]], effective_auth_mode: Optional[str]
) -> str:
    """Return the final provider-defined bucket for a request.

    The suffix is chosen by the active endpoint: the ChatGPT backend maps to
    ``-chatgpt`` and everything else (the OpenAI API) maps to ``-api``.
    """

    base = cost_bucket_base(config)
    suffix = _COST_BUCKET_AUTH_MODE_SUFFIXES.get(
        (effective_auth_mode or "").strip().lower(), "-api"
    )
    return f"{base}{suffix}"
