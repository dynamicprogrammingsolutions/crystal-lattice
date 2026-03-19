from __future__ import annotations

from pathlib import Path

from kimi_tools.kimi_grep_tool import KimiGrepTool


def _make_tool(tmp_path: Path) -> KimiGrepTool:
    tool = KimiGrepTool()
    state = tool.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)]})
    return tool, state


def test_schema_tool_name() -> None:
    tool = KimiGrepTool()
    _, state = tool.init({"working_directory": "/tmp"})
    schemas = tool.get_tool_schemas(state)
    assert schemas[0]["function"]["name"] == "Grep"
    assert schemas[0]["function"]["parameters"]["required"] == ["pattern"]


def test_schema_output_modes() -> None:
    tool = KimiGrepTool()
    _, state = tool.init({"working_directory": "/tmp"})
    schemas = tool.get_tool_schemas(state)
    output_mode = schemas[0]["function"]["parameters"]["properties"]["output_mode"]
    assert set(output_mode["enum"]) == {"content", "files_with_matches", "count_matches"}


def test_schema_flag_aliases() -> None:
    tool = KimiGrepTool()
    _, state = tool.init({"working_directory": "/tmp"})
    props = tool.get_tool_schemas(state)[0]["function"]["parameters"]["properties"]
    assert "-B" in props
    assert "-A" in props
    assert "-C" in props
    assert "-n" in props
    assert "-i" in props
    assert "type" in props
    assert "head_limit" in props
    assert "multiline" in props


def test_files_with_matches_mode(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("token here\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("no match\n", encoding="utf-8")
    (tmp_path / "c.txt").write_text("token too\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "token", "output_mode": "files_with_matches"}, state
    )
    assert result["success"] is True
    lines = result["result"].strip().split("\n")
    assert any("a.txt" in l for l in lines)
    assert any("c.txt" in l for l in lines)
    assert not any("b.txt" in l for l in lines)


def test_count_matches_mode(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("aaa bbb aaa\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("aaa\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "aaa", "output_mode": "count_matches"}, state
    )
    assert result["success"] is True
    # rg --count counts matching lines, not individual occurrences
    assert "a.txt:1" in result["result"]
    assert "b.txt:1" in result["result"]


def test_content_mode_with_line_numbers(tmp_path: Path) -> None:
    (tmp_path / "test.txt").write_text("line1 token\nline2 other\nline3 token\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "token", "output_mode": "content", "-n": True}, state
    )
    assert result["success"] is True
    assert "1:" in result["result"] or "line1" in result["result"]
    assert "3:" in result["result"] or "line3" in result["result"]


def test_ignore_case(tmp_path: Path) -> None:
    (tmp_path / "test.txt").write_text("Hello WORLD\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "hello", "output_mode": "content", "-i": True}, state
    )
    assert result["success"] is True
    assert "Hello WORLD" in result["result"]


def test_head_limit_truncation(tmp_path: Path) -> None:
    for i in range(20):
        (tmp_path / f"file{i}.txt").write_text("match\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "match", "output_mode": "files_with_matches", "head_limit": 5}, state
    )
    assert result["success"] is True
    assert "truncated" in result["message"]
    # The result text includes the head_limit truncation suffix
    assert "results truncated to 5 lines" in result["result"]


def test_no_matches(tmp_path: Path) -> None:
    (tmp_path / "test.txt").write_text("nothing here\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "nonexistent", "output_mode": "content"}, state
    )
    assert result["success"] is True
    assert result["result"] == ""
    assert "No matches found" in result["message"]


def test_invalid_output_mode(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "test", "output_mode": "invalid"}, state
    )
    assert result["success"] is False
    assert "Invalid output_mode" in result["error"]


def test_context_c_parameter(tmp_path: Path) -> None:
    (tmp_path / "test.txt").write_text(
        "line1\nline2 TARGET\nline3\nline4\n", encoding="utf-8"
    )
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "TARGET", "output_mode": "content", "-C": 1}, state
    )
    assert result["success"] is True
    assert "line2" in result["result"]  # match line
    # Context lines should appear
    assert "line1" in result["result"] or "line3" in result["result"]


def test_glob_filter(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("match\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("match\n", encoding="utf-8")
    tool, state = _make_tool(tmp_path)
    result = tool.execute_tool(
        "Grep", {"pattern": "match", "glob": "*.txt", "output_mode": "files_with_matches"}, state
    )
    assert result["success"] is True
    assert "a.txt" in result["result"]
    assert "b.py" not in result["result"]


def test_format_tool_result_success(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": True, "result": "a.txt:5", "message": ""}
    formatted = tool.format_tool_result(result, state)
    assert formatted == "a.txt:5"


def test_format_tool_result_with_truncation_message(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": True, "result": "a.txt\nb.txt", "message": "Results truncated to first 5 lines"}
    formatted = tool.format_tool_result(result, state)
    assert "a.txt" in formatted
    assert "truncated" in formatted


def test_format_tool_result_error(tmp_path: Path) -> None:
    tool, state = _make_tool(tmp_path)
    result = {"success": False, "error": "pattern is required."}
    formatted = tool.format_tool_result(result, state)
    assert formatted == "Error: pattern is required."
