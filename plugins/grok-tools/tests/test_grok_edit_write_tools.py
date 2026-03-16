from __future__ import annotations

from pathlib import Path

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from grok_tools import GrokCreateFileTool, GrokStrReplaceEditorTool


def _create_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GrokCreateFileTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        }
    )
    return wrapper, state


def _edit_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GrokStrReplaceEditorTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        }
    )
    return wrapper, state


def test_create_schema_matches_grok_surface(tmp_path: Path) -> None:
    wrapper, state = _create_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "create_file"
    assert schema["parameters"]["required"] == ["path", "content"]


def test_str_replace_schema_matches_grok_surface(tmp_path: Path) -> None:
    wrapper, state = _edit_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "str_replace_editor"
    assert schema["parameters"]["required"] == ["path", "old_str", "new_str"]
    assert list(schema["parameters"]["properties"].keys()) == ["path", "old_str", "new_str", "replace_all"]


def test_create_file_is_creation_only(tmp_path: Path) -> None:
    wrapper, state = _create_wrapper(tmp_path)
    created = wrapper.execute_tool("create_file", {"path": "note.txt", "content": "alpha\n"}, state)
    assert created["success"] is True
    assert created["result"] == f"Created new file: {(tmp_path / 'note.txt').resolve()}"

    duplicate = wrapper.execute_tool("create_file", {"path": "note.txt", "content": "beta\n"}, state)
    assert duplicate == {"success": False, "error": f"File already exists, cannot create: {(tmp_path / 'note.txt').resolve()}"}


def test_str_replace_editor_handles_multiple_matches(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("one\ntwo\none\n", encoding="utf-8")
    wrapper, state = _edit_wrapper(tmp_path)

    multiple = wrapper.execute_tool(
        "str_replace_editor",
        {"path": "sample.txt", "old_str": "one", "new_str": "ONE"},
        state,
    )
    assert multiple["success"] is False
    assert "Set replace_all to true" in multiple["error"]

    replaced = wrapper.execute_tool(
        "str_replace_editor",
        {"path": "sample.txt", "old_str": "one", "new_str": "ONE", "replace_all": True},
        state,
    )
    assert replaced["success"] is True
    assert replaced["result"] == f"Updated file: {target.resolve()}"
    assert target.read_text(encoding="utf-8") == "ONE\ntwo\nONE\n"


def test_pipeline_returns_final_tool_message_for_create_file(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    core = AgentCore()
    core.register_tool(GrokCreateFileTool)
    messages = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "create_file", "arguments": {"path": "note.txt", "content": "hello from grok\n"}},
            }
        ],
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        },
    )
    assert messages[0]["content"] == f"Created new file: {target.resolve()}"
    assert messages[0]["metadata"]["tool_name"] == "create_file"