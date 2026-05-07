from __future__ import annotations

from pathlib import Path
import tempfile

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper
from agent_app.plugin_manager import PluginManager

from qwen_tools import QwenGlobTool, QwenGrepSearchTool, QwenListDirectoryTool


def _base_config(tmp_path: Path) -> dict:
    return {
        "working_directory": str(tmp_path),
        "workspace_dirs": [str(tmp_path)],
        "project_temp_dir": str(tmp_path / ".temp"),
        "global_temp_dir": tempfile.gettempdir(),
        "user_skills_dir": str(tmp_path / ".skills"),
    }


def _list_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(QwenListDirectoryTool)
    return wrapper, wrapper.init(_base_config(tmp_path))


def _glob_wrapper(tmp_path: Path, *, line_limit: int = 2) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(QwenGlobTool)
    config = _base_config(tmp_path)
    config["truncate_tool_output_lines"] = line_limit
    return wrapper, wrapper.init(config)


def _grep_wrapper(tmp_path: Path, *, line_limit: int = 10, char_limit: int = 500) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(QwenGrepSearchTool)
    config = _base_config(tmp_path)
    config["truncate_tool_output_lines"] = line_limit
    config["truncate_tool_output_threshold"] = char_limit
    return wrapper, wrapper.init(config)


def test_search_schemas_match_qwen_surface(tmp_path: Path) -> None:
    list_wrapper, list_state = _list_wrapper(tmp_path)
    list_schema = list_wrapper.get_tool_schemas(list_state)[0]["function"]
    assert list_schema["name"] == "list_directory"
    assert list_schema["parameters"]["required"] == ["path"]

    glob_wrapper, glob_state = _glob_wrapper(tmp_path)
    glob_schema = glob_wrapper.get_tool_schemas(glob_state)[0]["function"]
    assert glob_schema["name"] == "glob"
    assert list(glob_schema["parameters"]["properties"].keys()) == ["pattern", "path"]

    grep_wrapper, grep_state = _grep_wrapper(tmp_path)
    grep_schema = grep_wrapper.get_tool_schemas(grep_state)[0]["function"]
    assert grep_schema["name"] == "grep_search"
    assert list(grep_schema["parameters"]["properties"].keys()) == ["pattern", "glob", "path", "limit"]


def test_list_directory_requires_absolute_path(tmp_path: Path) -> None:
    wrapper, state = _list_wrapper(tmp_path)
    result = wrapper.execute_tool("list_directory", {"path": "relative"}, state)
    assert result == {"success": False, "error": "Path must be absolute: relative"}


def test_glob_truncates_output_based_on_config(tmp_path: Path) -> None:
    for name in ["a.txt", "b.txt", "c.txt"]:
        (tmp_path / name).write_text(name, encoding="utf-8")
    wrapper, state = _glob_wrapper(tmp_path, line_limit=2)

    result = wrapper.execute_tool("glob", {"pattern": "*.txt"}, state)
    text = wrapper.format_tool_result(result, state)
    assert result["success"] is True
    assert result["return_display"].endswith("(truncated)")
    assert "[1 file truncated] ..." in text


def test_grep_respects_glob_filter_and_limit(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("Foo\nfoo\n", encoding="utf-8")
    (tmp_path / "beta.md").write_text("foo\n", encoding="utf-8")
    wrapper, state = _grep_wrapper(tmp_path)

    result = wrapper.execute_tool("grep_search", {"pattern": "foo", "glob": "*.txt", "limit": 1}, state)
    text = wrapper.format_tool_result(result, state)
    assert result["success"] is True
    assert "alpha.txt" in text
    assert "beta.md" not in text
    assert "Found 1 match" in text

    core = AgentCore()
    core.register_tool(QwenGrepSearchTool)
    messages = core.execute_tool_calls(
        [{"id": "call_1", "type": "function", "function": {"name": "grep_search", "arguments": {"pattern": "foo", "glob": "*.txt", "limit": 1}}}],
        {**_base_config(tmp_path), "truncate_tool_output_lines": 10, "truncate_tool_output_threshold": 500},
    )
    assert messages[0]["metadata"]["tool_name"] == "grep_search"


def test_plugin_manager_loads_all_qwen_tools(tmp_path: Path) -> None:
    mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
    repo = Path(__file__).resolve().parents[1]
    resolution = mgr.resolve_all([{"path": str(repo)}])
    assert resolution.errors == []
    assert [cls.__name__ for cls in resolution.classes] == [
        "QwenReadFileTool",
        "QwenListDirectoryTool",
        "QwenGrepSearchTool",
        "QwenGlobTool",
        "QwenWriteFileTool",
        "QwenEditTool",
        "QwenShellTool",
        "QwenWebFetchTool",
    ]
