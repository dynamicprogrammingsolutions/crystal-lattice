from __future__ import annotations

import tempfile
from pathlib import Path

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from qwen_tools import QwenEditTool, QwenWriteFileTool


def _write_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(QwenWriteFileTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "workspace_dirs": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
            "global_temp_dir": tempfile.gettempdir(),
            "user_skills_dir": str(tmp_path / ".skills"),
        }
    )
    return wrapper, state


def _edit_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(QwenEditTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "workspace_dirs": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
            "global_temp_dir": tempfile.gettempdir(),
            "user_skills_dir": str(tmp_path / ".skills"),
        }
    )
    return wrapper, state


def test_write_schema_matches_qwen_surface(tmp_path: Path) -> None:
    wrapper, state = _write_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "write_file"
    assert schema["parameters"]["required"] == ["file_path", "content"]
    assert "Relative paths are not supported" in schema["parameters"]["properties"]["file_path"]["description"]


def test_edit_schema_matches_qwen_surface(tmp_path: Path) -> None:
    wrapper, state = _edit_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "edit"
    assert schema["parameters"]["required"] == ["file_path", "old_string", "new_string"]
    assert list(schema["parameters"]["properties"].keys()) == ["file_path", "old_string", "new_string", "replace_all"]


def test_write_requires_absolute_path(tmp_path: Path) -> None:
    wrapper, state = _write_wrapper(tmp_path)
    result = wrapper.execute_tool("write_file", {"file_path": "note.txt", "content": "alpha\n"}, state)
    assert result == {"success": False, "error": "File path must be absolute: note.txt"}


def test_edit_reports_zero_match_and_multiple_match_cases(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("one\ntwo\none\n", encoding="utf-8")
    wrapper, state = _edit_wrapper(tmp_path)

    zero = wrapper.execute_tool(
        "edit",
        {"file_path": str(target), "old_string": "missing", "new_string": "new"},
        state,
    )
    assert "0 occurrences found for old_string" in zero["error"]

    multiple = wrapper.execute_tool(
        "edit",
        {"file_path": str(target), "old_string": "one", "new_string": "ONE"},
        state,
    )
    assert "replace_all was not enabled" in multiple["error"]


def test_edit_replace_all_and_empty_old_string_create_file(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("one\ntwo\none\n", encoding="utf-8")
    wrapper, state = _edit_wrapper(tmp_path)

    replaced = wrapper.execute_tool(
        "edit",
        {"file_path": str(target), "old_string": "one", "new_string": "ONE", "replace_all": True},
        state,
    )
    assert replaced["success"] is True
    assert replaced["result"] == f"The file: {target.resolve()} has been updated."
    assert target.read_text(encoding="utf-8") == "ONE\ntwo\nONE\n"

    created = tmp_path / "created.txt"
    create_result = wrapper.execute_tool(
        "edit",
        {"file_path": str(created), "old_string": "", "new_string": "hello\n"},
        state,
    )
    assert create_result["success"] is True
    assert create_result["result"] == f"Created new file: {created.resolve()} with provided content."
    assert created.read_text(encoding="utf-8") == "hello\n"


def test_pipeline_returns_final_tool_message_for_write(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    core = AgentCore()
    core.register_tool(QwenWriteFileTool)
    messages = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "write_file", "arguments": {"file_path": str(target), "content": "hello from qwen\n"}},
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
    assert messages[0]["content"] == f"Successfully created and wrote to new file: {target.resolve()}."
    assert messages[0]["metadata"]["tool_name"] == "write_file"