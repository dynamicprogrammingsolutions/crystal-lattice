from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
SRC = ROOT / "plugins/session-asset-attachments/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent_app.session_assets import FilesystemSessionAssetStore  # noqa: E402
from session_asset_attachments import SessionAssetAttachmentsAppPlugin  # noqa: E402


class _App:
    def __init__(self, store: FilesystemSessionAssetStore) -> None:
        self._store = store

    def get_session_asset_store(self) -> FilesystemSessionAssetStore:
        return self._store


def test_download_attachment_action_returns_session_asset_payload(tmp_path: Path) -> None:
    store = FilesystemSessionAssetStore(tmp_path / "assets")
    record = store.store_base64(
        session_id="sess_1",
        attachment_type="image",
        filename="sample.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
    )
    plugin = SessionAssetAttachmentsAppPlugin()
    state: Dict[str, Any] = plugin.init({})

    result = plugin.execute_action(
        _App(store),  # type: ignore[arg-type]
        "download_attachment",
        {"session_id": "sess_1", "asset_id": record.asset_id},
        None,
        state,
    )

    assert result["attachment_asset"]["asset_ref"] == record.asset_ref()
    assert result["attachment_asset"]["filename"] == "sample.png"
    assert result["attachment_asset"]["mime_type"] == "image/png"
    assert base64.b64decode(result["data_base64"]) == b"image-bytes"