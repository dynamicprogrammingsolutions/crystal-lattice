from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from agent_app.session_assets import FilesystemSessionAssetStore


def _base64_bytes(payload: bytes) -> str:
    return base64.b64encode(payload).decode("ascii")


def test_session_asset_store_round_trip_and_manifest(tmp_path: Path) -> None:
    store = FilesystemSessionAssetStore(tmp_path / "session_assets")

    record = store.store_base64(
        session_id="sess_123",
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=_base64_bytes(b"png-bytes"),
        provider_refs={"openai_responses": {"status": "not_uploaded"}},
        metadata={"origin": "unit-test"},
    )

    assert record.asset_ref() == {
        "kind": "session_asset",
        "session_id": "sess_123",
        "asset_id": record.asset_id,
        "attachment_type": "image",
    }
    assert store.load_bytes("sess_123", record.asset_id) == b"png-bytes"

    loaded = store.load("sess_123", record.asset_id)
    assert loaded.filename == "square.png"
    assert loaded.mime_type == "image/png"
    assert loaded.provider_refs == {"openai_responses": {"status": "not_uploaded"}}
    assert loaded.metadata == {"origin": "unit-test"}

    manifest = json.loads(loaded.manifest_path.read_text(encoding="utf-8"))
    assert manifest["session_id"] == "sess_123"
    assert manifest["asset_id"] == record.asset_id
    assert manifest["size_bytes"] == len(b"png-bytes")
    assert manifest["provider_refs"] == {"openai_responses": {"status": "not_uploaded"}}


def test_session_asset_store_delete_cleans_asset(tmp_path: Path) -> None:
    store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    record = store.store_base64(
        session_id="sess_123",
        attachment_type="pdf",
        filename="note.pdf",
        mime_type="application/pdf",
        data_base64=_base64_bytes(b"pdf-bytes"),
    )

    assert store.delete("sess_123", record.asset_id) is True
    assert store.delete("sess_123", record.asset_id) is False
    with pytest.raises(FileNotFoundError):
        store.load("sess_123", record.asset_id)


def test_session_asset_store_rejects_invalid_base64(tmp_path: Path) -> None:
    store = FilesystemSessionAssetStore(tmp_path / "session_assets")

    with pytest.raises(ValueError, match="valid base64"):
        store.store_base64(
            session_id="sess_123",
            attachment_type="image",
            filename="broken.png",
            mime_type="image/png",
            data_base64="%%%not-base64%%%",
        )