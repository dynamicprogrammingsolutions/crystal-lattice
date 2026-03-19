from __future__ import annotations

from pathlib import Path

from kimi_tools.kimi_read_file_tool import KimiReadFileTool


FIXTURES = Path(__file__).parent / "fixtures"


def _make_tool(tmp_path: Path) -> KimiReadFileTool:
    tool = KimiReadFileTool()
    state = tool.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)]})
    return tool, state


def test_schema_tool_name_is_pascal_case() -> None:
    tool = KimiReadFileTool()
    _, state = tool.init({"working_directory": "/tmp"})
    schemas = tool.get_tool_schemas(state)
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "ReadFile"


def test_schema_required_params() -> None:
    tool = KimiReadFileTool()
    _, state = tool.init({"working_directory": "/tmp"})
    schemas = tool.get_tool_schemas(state)
    props = schemas[0]["function"]["parameters"]["properties"]
    assert "path" in props
    assert "line_offset" in props
    assert "n_lines" in props
    assert schemas[0]["function"]["parameters"]["required"] == ["path"]


def test_read_simple_file(tmp_path: Path) -> None:
    f = tmp_path / "hello.txt"
    f.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "hello.txt"}, state)
    assert result["success"] is True
    assert "     1\talpha" in result["result"]
    assert "     2\tbeta" in result["result"]
    assert "     3\tgamma" in result["result"]
    assert "End of file reached." in result["message"]


def test_read_missing_file(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "nonexistent.txt"}, state)
    assert result["success"] is False
    assert "does not exist" in result["error"]


def test_read_directory_returns_error(tmp_path: Path) -> None:
    d = tmp_path / "subdir"
    d.mkdir()
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "subdir"}, state)
    assert result["success"] is False
    assert "not a file" in result["error"]


def test_read_with_line_offset(tmp_path: Path) -> None:
    f = tmp_path / "lines.txt"
    f.write_text("line1\nline2\nline3\nline4\nline5\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "lines.txt", "line_offset": 3}, state)
    assert result["success"] is True
    assert "     3\tline3" in result["result"]
    assert "     1\tline1" not in result["result"]


def test_read_with_n_lines(tmp_path: Path) -> None:
    f = tmp_path / "lines.txt"
    f.write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "lines.txt", "n_lines": 2}, state)
    assert result["success"] is True
    assert "     1\ta" in result["result"]
    assert "     2\tb" in result["result"]
    assert "     3\tc" not in result["result"]


def test_read_truncates_long_lines(tmp_path: Path) -> None:
    f = tmp_path / "long.txt"
    f.write_text("x" * 3000 + "\nshort\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "long.txt"}, state)
    assert result["success"] is True
    assert "..." in result["result"]
    assert "were truncated" in result["message"]


def test_read_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "empty.txt"}, state)
    assert result["success"] is True
    assert result["result"] == ""


def test_read_format_tool_result_wraps_with_system_tag(tmp_path: Path) -> None:
    f = tmp_path / "hello.txt"
    f.write_text("hi\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool("ReadFile", {"path": "hello.txt"}, state)
    formatted = tool.format_tool_result(result, state)
    assert "<system>" in formatted
    assert "</system>" in formatted
    assert "     1\thi" in formatted


def test_format_tool_result_error(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": False, "error": "File not found."}
    formatted = tool.format_tool_result(result, state)
    assert formatted == "Error: File not found."
