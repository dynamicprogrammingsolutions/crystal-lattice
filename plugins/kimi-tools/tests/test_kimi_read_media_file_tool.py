from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.session_assets import FilesystemSessionAssetStore  # noqa: E402
from agent_core.tool_result_payloads import FORMAT_OPENAI_CHAT_COMPLETIONS  # noqa: E402
from kimi_tools.kimi_read_media_file_tool import KimiReadMediaFileTool  # noqa: E402


PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB"
    "/6X7bAAAAABJRU5ErkJggg=="
)


def _png_bytes() -> bytes:
    return base64.b64decode(PNG_BASE64)


def _make_tool(tmp_path: Path, extra_config: dict | None = None):
    tool = KimiReadMediaFileTool()
    config = {
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
    }
    if extra_config:
        config.update(extra_config)
    state = tool.init(config)
    return tool, state


def test_schema_tool_name_is_pascal_case(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)

    schemas = tool.get_tool_schemas(state)

    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "ReadMediaFile"


def test_schema_required_params(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)

    params = tool.get_tool_schemas(state)[0]["function"]["parameters"]

    assert params["required"] == ["path"]
    assert list(params["properties"].keys()) == ["path"]


def test_schema_hidden_without_media_capability(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path, {"kimi_read_media_capabilities": []})

    assert tool.get_tool_schemas(state) == []


def test_read_png_returns_image_payloads(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    image.write_bytes(_png_bytes())
    tool, state = _make_tool(tmp_path)

    result = tool.execute_tool("ReadMediaFile", {"path": "tiny.png"}, state)

    assert result["success"] is True
    assert result["kind"] == "image"
    assert result["mime_type"] == "image/png"
    assert result["image_url"].startswith("data:image/png;base64,")
    assert result["bytes"] == len(_png_bytes())
    assert result["display_content"] == {
        "url": result["image_url"],
        "filename": "tiny.png",
        "mime_type": "image/png",
    }
    assert "Loaded image file" in result["message"]
    if result["width"] is not None:
        assert "original size 1x1px" in result["message"]

    formatted = tool.format_tool_result(result, state)
    assert formatted["type"] == "provider_native_tool_result"
    assert formatted["format"] == FORMAT_OPENAI_CHAT_COMPLETIONS
    content = formatted["content"]
    assert [part["type"] for part in content] == ["text", "image_url", "text"]
    assert "<system>" in content[0]["text"]
    assert f'<image path="{result["path"]}">' in content[0]["text"]
    assert content[1]["image_url"] == {"url": result["image_url"]}
    assert content[2]["text"] == "</image>"
    assert result["image_url"] not in content[0]["text"]
    assert result["image_url"] not in content[2]["text"]
    display = tool.to_display_format("", result, state)
    assert display["type"] == "image"
    assert display["single_line"] == "ReadMediaFile: tiny.png"
    assert display["content"] == result["display_content"]
    assert display["content_text"] == result["message"]


def test_read_png_stores_asset_backed_multipart_with_context(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    image.write_bytes(_png_bytes())
    tool, state = _make_tool(tmp_path)
    asset_store = FilesystemSessionAssetStore(tmp_path / "assets")

    result = tool.execute_tool(
        "ReadMediaFile",
        {"path": "tiny.png"},
        state,
        context={"session_id": "sess_1", "session_asset_store": asset_store},
    )

    assert result["success"] is True
    content = result["display_content"]
    assert content["asset_ref"]["kind"] == "session_asset"
    assert content["asset_ref"]["session_id"] == "sess_1"
    assert content["filename"] == "tiny.png"
    assert content["mime_type"] == "image/png"
    assert content["preview_data_base64"] == result["image_url"].split(",", 1)[1]
    assert content["preview_mime_type"] == "image/png"
    formatted = tool.format_tool_result(result, state)
    assert formatted["content"][1]["image_url"] == {
        "asset_ref": content["asset_ref"],
        "filename": "tiny.png",
        "mime_type": "image/png",
    }
    stored = asset_store.load_bytes("sess_1", content["asset_ref"]["asset_id"])
    assert stored == _png_bytes()


def test_read_extensionless_png(tmp_path: Path) -> None:
    image = tmp_path / "sample"
    image.write_bytes(_png_bytes())
    tool, state = _make_tool(tmp_path)

    result = tool.execute_tool("ReadMediaFile", {"path": "sample"}, state)

    assert result["success"] is True
    assert result["mime_type"] == "image/png"


def test_rejects_missing_directory_text_unknown_empty_and_too_large(
    tmp_path: Path,
) -> None:
    (tmp_path / "subdir").mkdir()
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02\x03\x04\x05")
    (tmp_path / "empty.png").write_bytes(b"")
    large = tmp_path / "large.png"
    large.write_bytes(_png_bytes())
    tool, state = _make_tool(tmp_path)
    small_tool, small_state = _make_tool(tmp_path, {"kimi_read_media_max_bytes": 4})

    missing = tool.execute_tool("ReadMediaFile", {"path": "missing.png"}, state)
    directory = tool.execute_tool("ReadMediaFile", {"path": "subdir"}, state)
    text = tool.execute_tool("ReadMediaFile", {"path": "note.txt"}, state)
    unknown = tool.execute_tool("ReadMediaFile", {"path": "blob.bin"}, state)
    empty = tool.execute_tool("ReadMediaFile", {"path": "empty.png"}, state)
    too_large = small_tool.execute_tool(
        "ReadMediaFile", {"path": "large.png"}, small_state
    )

    assert missing["brief"] == "File not found"
    assert directory["brief"] == "Invalid path"
    assert text["brief"] == "Unsupported file type"
    assert "Use ReadFile" in text["error"]
    assert unknown["brief"] == "File not readable"
    assert empty["brief"] == "Empty file"
    assert too_large["brief"] == "File too large"


def test_rejects_relative_path_outside_workspace(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(_png_bytes())
    tool, state = _make_tool(work)

    result = tool.execute_tool("ReadMediaFile", {"path": "../outside.png"}, state)

    assert result["success"] is False
    assert result["brief"] == "Invalid path"
    assert "not an absolute path" in result["error"]


def test_rejects_image_when_capability_missing(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    image.write_bytes(_png_bytes())
    tool, state = _make_tool(tmp_path, {"kimi_read_media_capabilities": ["video_in"]})

    result = tool.execute_tool("ReadMediaFile", {"path": "tiny.png"}, state)

    assert result["success"] is False
    assert result["brief"] == "Unsupported media type"
    assert "does not support image input" in result["error"]
