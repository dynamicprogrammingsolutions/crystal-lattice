from __future__ import annotations

from pathlib import Path

from kimi_tools.kimi_glob_tool import KimiGlobTool


def _make_tool(tmp_path: Path) -> KimiGlobTool:
    tool = KimiGlobTool()
    state = tool.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)]})
    return tool, state


def test_schema_tool_name() -> None:
    tool = KimiGlobTool()
    _, state = tool.init({"working_directory": "/tmp"})
    schemas = tool.get_tool_schemas(state)
    assert schemas[0]["function"]["name"] == "Glob"
    assert schemas[0]["function"]["parameters"]["required"] == ["pattern"]


def test_simple_pattern(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "c.py").write_text("c", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("Glob", {"pattern": "*.txt"}, state)
    assert result["success"] is True
    lines = result["result"].strip().split("\n")
    assert "a.txt" in lines
    assert "b.txt" in lines
    assert "c.py" not in lines


def test_double_star_prefix_rejected(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("Glob", {"pattern": "**/*.py"}, state)
    assert result["success"] is False
    assert "starts with '**'" in result["error"]
    # Should include directory listing in result
    assert isinstance(result.get("result"), str)


def test_include_dirs_false(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")
    (tmp_path / "subdir").mkdir()
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("Glob", {"pattern": "*", "include_dirs": False}, state)
    assert result["success"] is True
    lines = result["result"].strip().split("\n")
    assert "file.txt" in lines
    # Note: include_dirs filter is applied by glob_search, but * matches files
    # and directories both. With include_dirs=False, only files remain.
    assert "subdir" not in lines


def test_directory_param_outside_workspace(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Glob", {"pattern": "*", "directory": "/etc"}, state
    )
    assert result["success"] is False
    assert "outside the workspace" in result["error"]


def test_directory_param_non_absolute(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Glob", {"pattern": "*", "directory": "relative/path"}, state
    )
    assert result["success"] is False
    assert "not an absolute path" in result["error"]


def test_no_matches(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("Glob", {"pattern": "*.nonexistent"}, state)
    assert result["success"] is True
    assert result["result"].strip() == ""
    assert "No matches found" in result["message"]


def test_alphabetical_sort(tmp_path: Path) -> None:
    (tmp_path / "c.txt").write_text("", encoding="utf-8")
    (tmp_path / "a.txt").write_text("", encoding="utf-8")
    (tmp_path / "b.txt").write_text("", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("Glob", {"pattern": "*.txt"}, state)
    assert result["success"] is True
    lines = result["result"].strip().split("\n")
    assert lines == ["a.txt", "b.txt", "c.txt"]


def test_format_tool_result_error_with_listing(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {
        "success": False,
        "error": "Pattern `**` starts with '**'",
        "result": "a.txt\nb.txt",
    }
    formatted = tool.format_tool_result(result, state)
    assert "starts with '**'" in formatted
    assert "a.txt" in formatted


def test_format_tool_result_success(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": True, "result": "a.txt\nb.txt"}
    formatted = tool.format_tool_result(result, state)
    assert formatted == "a.txt\nb.txt"
