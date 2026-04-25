from __future__ import annotations

from typing import Any, Dict, Optional


_SESSION_ASSET_KIND = "session_asset"


def session_asset_ref_from_content(content: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(content, dict):
        return None
    asset_ref = content.get("asset_ref")
    if not isinstance(asset_ref, dict):
        return None
    if asset_ref.get("kind") != _SESSION_ASSET_KIND:
        return None

    session_id = asset_ref.get("session_id")
    asset_id = asset_ref.get("asset_id")
    attachment_type = asset_ref.get("attachment_type")
    if not all(
        isinstance(value, str) and value
        for value in (session_id, asset_id, attachment_type)
    ):
        return None

    return {
        "kind": _SESSION_ASSET_KIND,
        "session_id": session_id,
        "asset_id": asset_id,
        "attachment_type": attachment_type,
    }