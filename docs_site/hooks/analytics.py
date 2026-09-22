"""Validate privacy-safe Umami configuration before MkDocs renders pages."""

from __future__ import annotations

import re
from typing import Any

APPROVED_SCRIPT_URL = "https://stats.dynamicprogrammingsolutions.com/insight.js"
APPROVED_DOMAIN = "docs.crystallattice.dev"
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def on_config(config: Any) -> Any:
    extra = config.setdefault("extra", {})
    crystal_lattice = extra.setdefault("crystal_lattice", {})
    analytics = crystal_lattice.setdefault("analytics", {})
    script_url = str(analytics.get("script_url") or "").strip()
    website_id = str(analytics.get("website_id") or "").strip()

    analytics.update(
        {
            "enabled": (
                script_url == APPROVED_SCRIPT_URL
                and UUID_PATTERN.fullmatch(website_id) is not None
            ),
            "script_url": script_url,
            "website_id": website_id,
            "domain": APPROVED_DOMAIN,
        }
    )
    return config
