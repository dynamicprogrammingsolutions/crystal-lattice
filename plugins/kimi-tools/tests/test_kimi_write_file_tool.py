from __future__ import annotations

from pathlib import Path

from kimi_tools.kimi_write_file_tool import KimiWriteFileTool


def _make_tool(tmp_path: Path) -> KimiWriteFileTool:
    tool = KimiWriteFileTool()
    state = tool.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)]})
    return tool, state


def test_schema_tool_name() -> None:
    tool = KimiWriteFileTool()
    _, state = tool.init({"working_directory": "/tmp"})
    schemas = tool.get_tool_schemas(state)
    assert schemas[0]["function"]["name"] == "WriteFile"
    props = schemas[0]["function"]["parameters"]["properties"]
    assert "path" in props
    assert "content" in props
    assert "mode" in props
    assert set(schemas[0]["function"]["parameters"]["required"]) == {"path", "content"}


def test_write_create_new_file(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("WriteFile", {"path": "new.txt", "content": "hello"}, state)
    assert result["success"] is True
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "hello"
    assert "overwritten" in result["message"]


def test_write_overwrite_existing_file(tmp_path: Path) -> None:
    f = tmp_path / "existing.txt"
    f.write_text("old content", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("WriteFile", {"path": "existing.txt", "content": "new content"}, state)
    assert result["success"] is True
    assert f.read_text(encoding="utf-8") == "new content"
    assert "overwritten" in result["message"]


def test_write_append_mode(tmp_path: Path) -> None:
    f = tmp_path / "append.txt"
    f.write_text("first\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "WriteFile", {"path": "append.txt", "content": "second\n", "mode": "append"}, state
    )
    assert result["success"] is True
    assert f.read_text(encoding="utf-8") == "first\nsecond\n"
    assert "appended to" in result["message"]


def test_write_missing_parent_directory(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "WriteFile", {"path": "nonexistent/sub/file.txt", "content": "x"}, state
    )
    assert result["success"] is False
    assert "parent directory" in result["error"]


def test_write_invalid_mode(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "WriteFile", {"path": "test.txt", "content": "x", "mode": "invalid"}, state
    )
    assert result["success"] is False
    assert "Invalid write mode" in result["error"]


def test_write_empty_path(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("WriteFile", {"path": "", "content": "x"}, state)
    assert result["success"] is False
    assert "empty" in result["error"]


def test_format_tool_result_success(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": True, "message": "File successfully overwritten. Current size: 5 bytes."}
    formatted = tool.format_tool_result(result, state)
    assert formatted == "File successfully overwritten. Current size: 5 bytes."


def test_format_tool_result_error(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": False, "error": "Parent directory not found."}
    formatted = tool.format_tool_result(result, state)
    assert formatted == "Error: Parent directory not found."
