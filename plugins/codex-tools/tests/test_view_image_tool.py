from __future__ import annotations

import base64
import json
from pathlib import Path

from agent_core.plugin import ToolWrapper
from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    OpenAIChatToolSchemaAccessor,
)

from codex_tools.view_image_tool import ViewImageTool


PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB"
    "/6X7bAAAAABJRU5ErkJggg=="
)


def _png_bytes() -> bytes:
    return base64.b64decode(PNG_BASE64)


def _wrapper(tmp_path: Path, extra_config: dict | None = None):
    wrapper = ToolWrapper(ViewImageTool)
    config = {
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
    }
    if extra_config:
        config.update(extra_config)
    state = wrapper.init(config)
    return wrapper, state


def test_view_image_schema_is_responses_native_by_default(tmp_path: Path) -> None:
    wrapper, state = _wrapper(tmp_path)

    schemas = wrapper.get_tool_schemas(state)

    assert len(schemas) == 1
    schema = schemas[0]
    assert schema["type"] == "function"
    assert schema["name"] == "view_image"
    assert schema["strict"] is False
    assert schema["output_schema"]["required"] == ["image_url", "detail"]
    params = schema["parameters"]
    assert params["required"] == ["path"]
    assert params["additionalProperties"] is False
    assert list(params["properties"].keys()) == ["path"]


def test_view_image_schema_detail_is_opt_in(tmp_path: Path) -> None:
    wrapper, state = _wrapper(
        tmp_path,
        {"enable_view_image_detail_original": True},
    )

    params = wrapper.get_tool_schemas(state)[0]["parameters"]

    assert list(params["properties"].keys()) == ["path", "detail"]


def test_view_image_responses_schema_converts_to_chat_schema(tmp_path: Path) -> None:
    wrapper, state = _wrapper(
        tmp_path,
        {"enable_view_image_detail_original": True},
    )
    schema = wrapper.get_tool_schemas(state)[0]

    converted = DEFAULT_TOOL_INTEROP_REGISTRY.convert_schemas(
        [schema],
        target_formats=[OpenAIChatToolSchemaAccessor.format_id],
    )[0]

    assert converted["type"] == "function"
    assert converted["function"]["name"] == "view_image"
    assert converted["function"]["strict"] is False
    params = converted["function"]["parameters"]
    assert params["required"] == ["path"]
    assert "detail" in params["properties"]
    assert "output_schema" not in converted["function"]


def test_view_image_loads_png_and_returns_native_output_content(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    image.write_bytes(_png_bytes())
    wrapper, state = _wrapper(tmp_path)

    result = wrapper.execute_tool("view_image", {"path": "tiny.png"}, state)

    assert result["success"] is True
    assert result["mime_type"] == "image/png"
    assert result["image_url"].startswith("data:image/png;base64,")
    assert result["detail"] == "high"
    output_content = result["tool_output_content"]
    assert output_content == [
        {
            "type": "input_image",
            "image_url": result["image_url"],
            "detail": "high",
        }
    ]
    assert result["multipartContent"] == [
        {
            "type": "image",
            "content": {"url": result["image_url"]},
            "metadata": {"detail": "high", "path": result["path"]},
        }
    ]

    formatted = wrapper.format_tool_result(result, state)
    payload = json.loads(formatted)
    assert payload["image_url"] == result["image_url"]
    assert payload["detail"] == "high"
    assert payload["mime_type"] == "image/png"

    display = wrapper.to_display_format(formatted, result, state)
    assert display["type"] == "image"
    assert display["single_line"] == "view_image: tiny.png"
    assert result["image_url"] not in display["single_line"]


def test_view_image_rejects_invalid_detail(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    image.write_bytes(_png_bytes())
    wrapper, state = _wrapper(
        tmp_path,
        {"enable_view_image_detail_original": True},
    )

    result = wrapper.execute_tool(
        "view_image", {"path": "tiny.png", "detail": "low"}, state
    )

    assert result["success"] is False
    assert "only supports `original`" in result["error"]


def test_view_image_rejects_original_when_not_enabled(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    image.write_bytes(_png_bytes())
    wrapper, state = _wrapper(tmp_path)

    result = wrapper.execute_tool(
        "view_image", {"path": "tiny.png", "detail": "original"}, state
    )

    assert result["success"] is False
    assert "unavailable" in result["error"]


def test_view_image_rejects_missing_directory_non_image_and_outside_paths(
    tmp_path: Path,
) -> None:
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(_png_bytes())
    text_file = safe_dir / "note.txt"
    text_file.write_text("not an image", encoding="utf-8")

    wrapper, state = _wrapper(
        safe_dir,
        {
            "working_directory": str(safe_dir),
            "allowed_paths": [str(safe_dir)],
        },
    )

    missing = wrapper.execute_tool("view_image", {"path": "missing.png"}, state)
    directory = wrapper.execute_tool("view_image", {"path": "."}, state)
    non_image = wrapper.execute_tool("view_image", {"path": "note.txt"}, state)
    denied = wrapper.execute_tool("view_image", {"path": str(outside)}, state)

    assert missing["success"] is False
    assert "unable to locate" in missing["error"]
    assert directory["success"] is False
    assert "not a file" in directory["error"]
    assert non_image["success"] is False
    assert "unsupported image format" in non_image["error"]
    assert denied["success"] is False
    assert "Access denied" in denied["error"]
