from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


_SESSION_ASSET_KIND = "session_asset"
_OPENAI_PROVIDER_REF_KEY = "openai_responses"


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
    if not all(isinstance(value, str) and value for value in (session_id, asset_id, attachment_type)):
        return None

    return {
        "kind": _SESSION_ASSET_KIND,
        "session_id": session_id,
        "asset_id": asset_id,
        "attachment_type": attachment_type,
    }


def openai_provider_ref(provider_refs: Any) -> Dict[str, Any]:
    if not isinstance(provider_refs, dict):
        return {}
    value = provider_refs.get(_OPENAI_PROVIDER_REF_KEY)
    return dict(value) if isinstance(value, dict) else {}


def merge_openai_provider_ref(provider_refs: Any, provider_ref: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(provider_refs) if isinstance(provider_refs, dict) else {}
    merged[_OPENAI_PROVIDER_REF_KEY] = dict(provider_ref)
    return merged


def build_openai_provider_ref(
    *,
    file_id: str,
    purpose: str,
    filename: str,
    mime_type: str,
    expires_at: Any = None,
) -> Dict[str, Any]:
    ref: Dict[str, Any] = {
        "status": "uploaded",
        "file_id": file_id,
        "purpose": purpose,
        "filename": filename,
        "mime_type": mime_type,
    }
    if isinstance(expires_at, (int, float)):
        ref["expires_at"] = int(expires_at)
    elif isinstance(expires_at, str) and expires_at:
        ref["expires_at"] = expires_at
    return ref


def openai_provider_ref_is_usable(provider_ref: Any, *, now: Optional[datetime] = None) -> bool:
    if not isinstance(provider_ref, dict):
        return False
    file_id = provider_ref.get("file_id")
    if not isinstance(file_id, str) or not file_id:
        return False

    expires_at = provider_ref.get("expires_at")
    if expires_at is None:
        return True

    current = now or datetime.now(timezone.utc)
    if isinstance(expires_at, (int, float)):
        return float(expires_at) > current.timestamp()

    if isinstance(expires_at, str) and expires_at:
        try:
            parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        return parsed > current

    return True