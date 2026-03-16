from __future__ import annotations

import tempfile
from pathlib import Path

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from qwen_tools import QwenReadFileTool


def _make_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(QwenReadFileTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "workspace_dirs": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
            "global_temp_dir": tempfile.gettempdir(),
            "user_skills_dir": str(tmp_path / ".skills"),
            "truncate_tool_output_lines": 4,
            "truncate_tool_output_threshold": 24,
        }
    )
    return wrapper, state


def test_schema_matches_qwen_surface(tmp_path: Path) -> None:
    wrapper, state = _make_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "read_file"
    assert schema["parameters"]["required"] == ["absolute_path"]
    assert list(schema["parameters"]["properties"].keys()) == [
        "absolute_path",
        "offset",
        "limit",
    ]
    assert "Relative paths are not supported" in schema["parameters"]["properties"]["absolute_path"]["description"]


def test_requires_absolute_path_and_respects_qwenignore(tmp_path: Path) -> None:
    wrapper, state = _make_wrapper(tmp_path)
    relative = wrapper.execute_tool("read_file", {"absolute_path": "notes.txt"}, state)
    assert relative == {
        "success": False,
        "error": "File path must be absolute, but was relative: notes.txt. You must provide an absolute path.",
    }

    (tmp_path / ".qwenignore").write_text("hidden.txt\n", encoding="utf-8")
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("secret", encoding="utf-8")
    ignored = wrapper.execute_tool("read_file", {"absolute_path": str(hidden)}, state)
    assert ignored == {
        "success": False,
        "error": f"File path '{hidden.resolve()}' is ignored by .qwenignore pattern(s).",
    }


def test_formats_offset_limit_truncation_and_trimmed_lines(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("one   \ntwo   \nthree   \nfour   \nfive", encoding="utf-8")
    wrapper, state = _make_wrapper(tmp_path)
    result = wrapper.execute_tool(
        "read_file",
        {"absolute_path": str(path), "offset": 1, "limit": 3},
        state,
    )
    text = wrapper.format_tool_result(result, state)
    assert result["success"] is True
    assert text.startswith("Showing lines 2-4 of 5 total lines.")
    assert "two\nthree\nfour" in text
    assert "two   " not in text


def test_char_limit_truncates_and_temp_dir_is_allowed(tmp_path: Path) -> None:
    wrapper, state = _make_wrapper(tmp_path)
    path = tmp_path / "long.txt"
    path.write_text("abcdefghijklmnopqrstuvwxyz\nsecond\n", encoding="utf-8")
    result = wrapper.execute_tool("read_file", {"absolute_path": str(path)}, state)
    assert result["success"] is True
    assert "... [truncated]" in wrapper.format_tool_result(result, state)

    temp_file = tmp_path / ".temp" / "tool-output.txt"
    temp_file.parent.mkdir(parents=True)
    temp_file.write_text("ok\n", encoding="utf-8")
    allowed = wrapper.execute_tool("read_file", {"absolute_path": str(temp_file)}, state)
    assert allowed["success"] is True
    assert allowed["result"] == "ok\n"


def test_pipeline_returns_final_tool_message(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("hello from qwen\n", encoding="utf-8")
    core = AgentCore()
    core.register_tool(QwenReadFileTool)
    messages = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "read_file", "arguments": {"absolute_path": str(target)}},
            }
        ],
        {
            "working_directory": str(tmp_path),
            "workspace_dirs": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
            "global_temp_dir": tempfile.gettempdir(),
            "user_skills_dir": str(tmp_path / ".skills"),
        },
    )
    assert messages[0]["content"] == "hello from qwen\n"
    assert messages[0]["metadata"]["tool_name"] == "read_file"


def test_plugin_manager_loads_package_with_sibling_dependency(tmp_path: Path) -> None:
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
    ]