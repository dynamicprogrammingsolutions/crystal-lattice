from __future__ import annotations

import base64
import binascii
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class SessionAssetRecord:
    session_id: str
    asset_id: str
    attachment_type: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: str
    provider_refs: Dict[str, Any]
    metadata: Dict[str, Any]
    blob_path: Path
    manifest_path: Path

    def asset_ref(self) -> Dict[str, Any]:
        return {
            "kind": "session_asset",
            "session_id": self.session_id,
            "asset_id": self.asset_id,
            "attachment_type": self.attachment_type,
        }

    def public_descriptor(self) -> Dict[str, Any]:
        descriptor: Dict[str, Any] = {
            "asset_ref": self.asset_ref(),
            "filename": self.filename,
            "mime_type": self.mime_type,
            "provider_refs": dict(self.provider_refs),
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "created_at": self.created_at,
        }
        if self.metadata:
            descriptor["metadata"] = dict(self.metadata)
        return descriptor

    def manifest_payload(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "asset_id": self.asset_id,
            "attachment_type": self.attachment_type,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "provider_refs": dict(self.provider_refs),
            "metadata": dict(self.metadata),
        }


class FilesystemSessionAssetStore:
    """Filesystem-backed asset store for per-session attachments."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = Path(root_dir)
        self._root_dir.mkdir(parents=True, exist_ok=True)

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    def _validate_component(self, value: str, *, field_name: str) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} must be a non-empty string")
        if value in {".", ".."} or "/" in value or "\\" in value:
            raise ValueError(f"{field_name} must be an opaque path-safe identifier")
        return value

    def _session_dir(self, session_id: str) -> Path:
        return self._root_dir / self._validate_component(session_id, field_name="session_id")

    def _asset_dir(self, session_id: str, asset_id: str) -> Path:
        return self._session_dir(session_id) / self._validate_component(asset_id, field_name="asset_id")

    def _blob_path(self, session_id: str, asset_id: str) -> Path:
        return self._asset_dir(session_id, asset_id) / "blob"

    def _manifest_path(self, session_id: str, asset_id: str) -> Path:
        return self._asset_dir(session_id, asset_id) / "manifest.json"

    def _write_json_atomic(self, path: Path, payload: Dict[str, Any]) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(path)

    def _record_from_manifest(self, path: Path, payload: Dict[str, Any]) -> SessionAssetRecord:
        if not isinstance(payload, dict):
            raise ValueError("asset manifest must be a dict")

        session_id = self._validate_component(str(payload.get("session_id") or ""), field_name="session_id")
        asset_id = self._validate_component(str(payload.get("asset_id") or ""), field_name="asset_id")
        attachment_type = str(payload.get("attachment_type") or "")
        filename = str(payload.get("filename") or "")
        mime_type = str(payload.get("mime_type") or "")
        size_bytes = payload.get("size_bytes")
        sha256 = str(payload.get("sha256") or "")
        created_at = str(payload.get("created_at") or "")
        provider_refs = payload.get("provider_refs") if isinstance(payload.get("provider_refs"), dict) else {}
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

        if not attachment_type or not filename or not mime_type or not sha256 or not created_at:
            raise ValueError("asset manifest missing required fields")
        if not isinstance(size_bytes, int) or size_bytes < 0:
            raise ValueError("asset manifest has invalid size_bytes")

        return SessionAssetRecord(
            session_id=session_id,
            asset_id=asset_id,
            attachment_type=attachment_type,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            sha256=sha256,
            created_at=created_at,
            provider_refs=dict(provider_refs),
            metadata=dict(metadata),
            blob_path=self._blob_path(session_id, asset_id),
            manifest_path=path,
        )

    def store_base64(
        self,
        *,
        session_id: str,
        attachment_type: str,
        filename: str,
        mime_type: str,
        data_base64: str,
        asset_id: Optional[str] = None,
        provider_refs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionAssetRecord:
        session_id = self._validate_component(session_id, field_name="session_id")
        if not isinstance(attachment_type, str) or not attachment_type:
            raise ValueError("attachment_type must be a non-empty string")
        if not isinstance(filename, str) or not filename:
            raise ValueError("filename must be a non-empty string")
        if not isinstance(mime_type, str) or not mime_type:
            raise ValueError("mime_type must be a non-empty string")
        if not isinstance(data_base64, str) or not data_base64:
            raise ValueError("data_base64 must be a non-empty string")

        try:
            payload_bytes = base64.b64decode(data_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("data_base64 must contain valid base64") from exc

        normalized_asset_id = (
            self._validate_component(asset_id, field_name="asset_id")
            if isinstance(asset_id, str) and asset_id
            else uuid.uuid4().hex
        )
        asset_dir = self._asset_dir(session_id, normalized_asset_id)
        asset_dir.mkdir(parents=True, exist_ok=False)

        blob_path = self._blob_path(session_id, normalized_asset_id)
        blob_path.write_bytes(payload_bytes)

        record = SessionAssetRecord(
            session_id=session_id,
            asset_id=normalized_asset_id,
            attachment_type=attachment_type,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(payload_bytes),
            sha256=hashlib.sha256(payload_bytes).hexdigest(),
            created_at=_utc_now_iso(),
            provider_refs=dict(provider_refs) if isinstance(provider_refs, dict) else {},
            metadata=dict(metadata) if isinstance(metadata, dict) else {},
            blob_path=blob_path,
            manifest_path=self._manifest_path(session_id, normalized_asset_id),
        )
        self._write_json_atomic(record.manifest_path, record.manifest_payload())
        return record

    def load(self, session_id: str, asset_id: str) -> SessionAssetRecord:
        manifest_path = self._manifest_path(session_id, asset_id)
        if not manifest_path.exists():
            raise FileNotFoundError(f"Asset {asset_id!r} not found for session {session_id!r}")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return self._record_from_manifest(manifest_path, payload)

    def load_bytes(self, session_id: str, asset_id: str) -> bytes:
        record = self.load(session_id, asset_id)
        if not record.blob_path.exists():
            raise FileNotFoundError(f"Asset blob missing for {asset_id!r}")
        return record.blob_path.read_bytes()

    def update_manifest(
        self,
        session_id: str,
        asset_id: str,
        *,
        provider_refs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionAssetRecord:
        record = self.load(session_id, asset_id)
        next_record = SessionAssetRecord(
            session_id=record.session_id,
            asset_id=record.asset_id,
            attachment_type=record.attachment_type,
            filename=record.filename,
            mime_type=record.mime_type,
            size_bytes=record.size_bytes,
            sha256=record.sha256,
            created_at=record.created_at,
            provider_refs=(
                dict(provider_refs) if isinstance(provider_refs, dict) else dict(record.provider_refs)
            ),
            metadata=dict(metadata) if isinstance(metadata, dict) else dict(record.metadata),
            blob_path=record.blob_path,
            manifest_path=record.manifest_path,
        )
        self._write_json_atomic(next_record.manifest_path, next_record.manifest_payload())
        return next_record

    def delete(self, session_id: str, asset_id: str) -> bool:
        asset_dir = self._asset_dir(session_id, asset_id)
        if not asset_dir.exists():
            return False

        for child in asset_dir.iterdir():
            child.unlink()
        asset_dir.rmdir()

        session_dir = self._session_dir(session_id)
        try:
            next(session_dir.iterdir())
        except StopIteration:
            session_dir.rmdir()
        except FileNotFoundError:
            pass
        return True