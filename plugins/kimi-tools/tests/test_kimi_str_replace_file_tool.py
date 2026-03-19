from __future__ import annotations

from pathlib import Path

from kimi_tools.kimi_str_replace_file_tool import KimiStrReplaceFileTool


def _make_tool(tmp_path: Path) -> KimiStrReplaceFileTool:
    tool = KimiStrReplaceFileTool()
    state = tool.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)]})
    return tool, state


def test_schema_tool_name() -> None:
    tool = KimiStrReplaceFileTool()
    _, state = tool.init({"working_directory": "/tmp"})
    schemas = tool.get_tool_schemas(state)
    assert schemas[0]["function"]["name"] == "StrReplaceFile"
    assert set(schemas[0]["function"]["parameters"]["required"]) == {"path", "edit"}


def test_single_edit_one_match(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("hello world\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "StrReplaceFile",
        {"path": "test.txt", "edit": {"old": "world", "new": "earth"}},
        state,
    )
    assert result["success"] is True
    assert f.read_text(encoding="utf-8") == "hello earth\n"
    assert "1 edit(s) with 1 total replacement(s)" in result["message"]


def test_single_edit_replace_all(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("aaa aaa aaa\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "StrReplaceFile",
        {"path": "test.txt", "edit": {"old": "aaa", "new": "bbb", "replace_all": True}},
        state,
    )
    assert result["success"] is True
    assert f.read_text(encoding="utf-8") == "bbb bbb bbb\n"
    assert "3 total replacement(s)" in result["message"]


def test_multiple_edits_list(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("alpha beta gamma\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "StrReplaceFile",
        {
            "path": "test.txt",
            "edit": [
                {"old": "alpha", "new": "one"},
                {"old": "gamma", "new": "three"},
            ],
        },
        state,
    )
    assert result["success"] is True
    assert f.read_text(encoding="utf-8") == "one beta three\n"
    assert "2 edit(s) with 2 total replacement(s)" in result["message"]


def test_zero_matches_returns_error(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("hello world\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "StrReplaceFile",
        {"path": "test.txt", "edit": {"old": "xyz", "new": "abc"}},
        state,
    )
    assert result["success"] is False
    assert "No replacements were made" in result["error"]
    assert "not found" in result["error"]
    # File should be unchanged
    assert f.read_text(encoding="utf-8") == "hello world\n"


def test_missing_file_returns_error(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "StrReplaceFile",
        {"path": "nonexistent.txt", "edit": {"old": "a", "new": "b"}},
        state,
    )
    assert result["success"] is False
    assert "does not exist" in result["error"]


def test_directory_path_returns_error(tmp_path: Path) -> None:
    d = tmp_path / "subdir"
    d.mkdir()
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "StrReplaceFile",
        {"path": "subdir", "edit": {"old": "a", "new": "b"}},
        state,
    )
    assert result["success"] is False
    assert "not a file" in result["error"]


def test_multiline_edit(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("line1\nline2\nline3\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "StrReplaceFile",
        {"path": "test.txt", "edit": {"old": "line1\nline2", "new": "replaced"}},
        state,
    )
    assert result["success"] is True
    assert f.read_text(encoding="utf-8") == "replaced\nline3\n"


def test_format_tool_result_success(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": True, "message": "File successfully edited. Applied 1 edit(s) with 1 total replacement(s)."}
    formatted = tool.format_tool_result(result, state)
    assert "1 edit(s)" in formatted


def test_format_tool_result_error(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": False, "error": "No replacements were made."}
    formatted = tool.format_tool_result(result, state)
    assert formatted == "Error: No replacements were made."
