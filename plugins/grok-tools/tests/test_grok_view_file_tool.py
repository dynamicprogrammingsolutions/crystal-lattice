from __future__ import annotations

from pathlib import Path

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from grok_tools import GrokViewFileTool


def _make_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GrokViewFileTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        }
    )
    return wrapper, state


def test_schema_matches_grok_surface(tmp_path: Path) -> None:
    wrapper, state = _make_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "view_file"
    assert schema["description"] == "View contents of a file or list directory contents"
    assert schema["parameters"]["required"] == ["path"]


def test_directory_listing_mode_and_partial_file_view(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    folder = tmp_path / "dir"
    folder.mkdir()
    (folder / "nested.txt").write_text("nested\n", encoding="utf-8")
    wrapper, state = _make_wrapper(tmp_path)

    listing = wrapper.execute_tool("view_file", {"path": "."}, state)
    text = wrapper.format_tool_result(listing, state)
    assert listing["success"] is True
    assert "alpha.txt" in text
    assert "dir/" in text

    partial = wrapper.execute_tool(
        "view_file",
        {"path": "alpha.txt", "start_line": 2, "end_line": 3},
        state,
    )
    partial_text = wrapper.format_tool_result(partial, state)
    assert "Showing lines 2-3 of 4 total lines" in partial_text
    assert "two" in partial_text
    assert "three" in partial_text


def test_pipeline_returns_directory_tool_message(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("hello\n", encoding="utf-8")
    core = AgentCore()
    core.register_tool(GrokViewFileTool)
    messages = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "view_file", "arguments": {"path": "."}},
            }
        ],
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        },
    )
    assert messages[0]["role"] == "tool"
    assert "alpha.txt" in messages[0]["content"]
    assert messages[0]["metadata"]["tool_name"] == "view_file"


def test_plugin_manager_loads_package_with_sibling_dependency(tmp_path: Path) -> None:
    mgr = PluginManager(cache_dir=tmp_path / "cache", policy={"install_deps": True})
    repo = Path(__file__).resolve().parents[1]
    resolution = mgr.resolve_all([{"path": str(repo)}])
    assert resolution.errors == []
    assert [cls.__name__ for cls in resolution.classes] == [
        "GrokViewFileTool",
        "GrokCreateFileTool",
        "GrokStrReplaceEditorTool",
    ]