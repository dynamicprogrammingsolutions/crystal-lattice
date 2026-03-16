from __future__ import annotations

import os
import time
from pathlib import Path

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper
from agent_app.plugin_manager import PluginManager

from gemini_tools import GeminiGlobTool, GeminiGrepSearchTool, GeminiListDirectoryTool


def _list_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GeminiListDirectoryTool)
    state = wrapper.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)], "project_temp_dir": str(tmp_path / ".temp")})
    return wrapper, state


def _glob_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GeminiGlobTool)
    state = wrapper.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)], "project_temp_dir": str(tmp_path / ".temp")})
    return wrapper, state


def _grep_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GeminiGrepSearchTool)
    state = wrapper.init({"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)], "project_temp_dir": str(tmp_path / ".temp")})
    return wrapper, state


def test_search_schemas_match_gemini_surface(tmp_path: Path) -> None:
    list_wrapper, list_state = _list_wrapper(tmp_path)
    list_schema = list_wrapper.get_tool_schemas(list_state)[0]["function"]
    assert list_schema["name"] == "list_directory"
    assert list_schema["parameters"]["required"] == ["dir_path"]

    glob_wrapper, glob_state = _glob_wrapper(tmp_path)
    glob_schema = glob_wrapper.get_tool_schemas(glob_state)[0]["function"]
    assert glob_schema["name"] == "glob"
    assert list(glob_schema["parameters"]["properties"].keys()) == [
        "pattern",
        "dir_path",
        "case_sensitive",
        "respect_git_ignore",
        "respect_gemini_ignore",
    ]

    grep_wrapper, grep_state = _grep_wrapper(tmp_path)
    grep_schema = grep_wrapper.get_tool_schemas(grep_state)[0]["function"]
    assert grep_schema["name"] == "grep_search"
    assert list(grep_schema["parameters"]["properties"].keys()) == [
        "pattern",
        "dir_path",
        "include_pattern",
        "exclude_pattern",
        "names_only",
        "max_matches_per_file",
        "total_max_matches",
    ]


def test_list_directory_formats_entries_and_ignore_count(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored-git.txt\n", encoding="utf-8")
    (tmp_path / ".geminiignore").write_text("ignored-vendor.txt\n", encoding="utf-8")
    (tmp_path / "alpha.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "ignored-git.txt").write_text("git\n", encoding="utf-8")
    (tmp_path / "ignored-vendor.txt").write_text("vendor\n", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    wrapper, state = _list_wrapper(tmp_path)

    result = wrapper.execute_tool("list_directory", {"dir_path": "."}, state)
    text = wrapper.format_tool_result(result, state)
    assert result["success"] is True
    assert "Directory listing for" in text
    assert "[DIR] nested" in text
    assert "alpha.txt (6 bytes)" in text
    assert "(2 ignored)" in text


def test_glob_returns_sorted_paths(tmp_path: Path) -> None:
    newer = tmp_path / "newer.py"
    older = tmp_path / "older.py"
    newer.write_text("print('new')\n", encoding="utf-8")
    older.write_text("print('old')\n", encoding="utf-8")
    now = time.time()
    os.utime(newer, (now, now))
    old = now - (3 * 24 * 60 * 60)
    os.utime(older, (old, old))
    wrapper, state = _glob_wrapper(tmp_path)

    result = wrapper.execute_tool("glob", {"pattern": "*.py"}, state)
    text = wrapper.format_tool_result(result, state)
    assert result["success"] is True
    lines = text.splitlines()
    assert str(newer.resolve()) in lines[-2]
    assert str(older.resolve()) in lines[-1]


def test_grep_names_only_and_pipeline_output(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("token\n", encoding="utf-8")
    (tmp_path / "two.txt").write_text("missing\n", encoding="utf-8")
    wrapper, state = _grep_wrapper(tmp_path)
    result = wrapper.execute_tool(
        "grep_search",
        {"pattern": "token", "include_pattern": "*.txt", "names_only": True},
        state,
    )
    text = wrapper.format_tool_result(result, state)
    assert result["success"] is True
    assert str((tmp_path / "one.txt").resolve()) in text
    assert "L1:" not in text

    core = AgentCore()
    core.register_tool(GeminiGrepSearchTool)
    messages = core.execute_tool_calls(
        [{"id": "call_1", "type": "function", "function": {"name": "grep_search", "arguments": {"pattern": "token", "include_pattern": "*.txt"}}}],
        {"working_directory": str(tmp_path), "allowed_paths": [str(tmp_path)], "project_temp_dir": str(tmp_path / ".temp")},
    )
    assert messages[0]["metadata"]["tool_name"] == "grep_search"
    assert "Found 1 match" in messages[0]["content"]


def test_plugin_manager_loads_all_gemini_tools(tmp_path: Path) -> None:
    mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
    repo = Path(__file__).resolve().parents[1]
    resolution = mgr.resolve_all([{"path": str(repo)}])
    assert resolution.errors == []
    assert [cls.__name__ for cls in resolution.classes] == [
        "GeminiReadFileTool",
        "GeminiListDirectoryTool",
        "GeminiGrepSearchTool",
        "GeminiGlobTool",
        "GeminiWriteFileTool",
        "GeminiReplaceTool",
    ]
