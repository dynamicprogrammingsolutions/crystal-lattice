"""Provider-defined cost buckets for the reference OpenAI-compatible provider.

Cost buckets attribute usage records in the generic cost tracking store. The
bucket base can be altered by config (``cost_bucket``), but the final bucket
is always defined by this provider: the endpoint URL host is slugged and
appended, so different endpoints land in different buckets.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional
from urllib.parse import urlsplit


DEFAULT_OPENAI_COMPATIBLE_COST_BUCKET = "openai-compatible"

_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def cost_bucket_base(config: Optional[Dict[str, Any]]) -> str:
    """Return the configured bucket base, falling back to the default."""

    raw = config.get("cost_bucket") if isinstance(config, dict) else None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return DEFAULT_OPENAI_COMPATIBLE_COST_BUCKET


def endpoint_host_slug(base_url: Optional[str]) -> str:
    """Return a slug of the endpoint URL host (e.g. ``api-fireworks-ai``)."""

    if not isinstance(base_url, str) or not base_url.strip():
        return ""
    try:
        host = urlsplit(base_url.strip()).netloc.rpartition("@")[2]
    except ValueError:
        return ""
    host = host.split(":", 1)[0].strip().lower()
    slug = _SLUG_NON_ALNUM.sub("-", host).strip("-")
    return slug


def resolve_cost_bucket(config: Optional[Dict[str, Any]]) -> str:
    """Return the final provider-defined bucket for a request.

    The bucket is the configured base plus a slug of the endpoint URL host so
    requests against different endpoints are attributed separately.
    """

    base = cost_bucket_base(config)
    base_url = config.get("base_url") if isinstance(config, dict) else None
    slug = endpoint_host_slug(base_url if isinstance(base_url, str) else None)
    if not slug:
        return base
    return f"{base}-{slug}"
