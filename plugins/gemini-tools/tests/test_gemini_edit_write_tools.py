from __future__ import annotations

from pathlib import Path

from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from gemini_tools import GeminiReplaceTool, GeminiWriteFileTool


def _write_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GeminiWriteFileTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        }
    )
    return wrapper, state


def _replace_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GeminiReplaceTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        }
    )
    return wrapper, state


def test_write_schema_matches_gemini_surface(tmp_path: Path) -> None:
    wrapper, state = _write_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "write_file"
    assert schema["parameters"]["required"] == ["file_path", "content"]
    assert list(schema["parameters"]["properties"].keys()) == ["file_path", "content"]


def test_replace_schema_matches_gemini_surface(tmp_path: Path) -> None:
    wrapper, state = _replace_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]["function"]
    assert schema["name"] == "replace"
    assert schema["parameters"]["required"] == ["file_path", "instruction", "old_string", "new_string"]
    assert list(schema["parameters"]["properties"].keys()) == [
        "file_path",
        "instruction",
        "old_string",
        "new_string",
        "allow_multiple",
    ]


def test_write_creates_and_overwrites_file(tmp_path: Path) -> None:
    wrapper, state = _write_wrapper(tmp_path)
    created = wrapper.execute_tool("write_file", {"file_path": "note.txt", "content": "alpha\n"}, state)
    assert created["success"] is True
    assert created["result"] == f"Successfully created and wrote to new file: {(tmp_path / 'note.txt').resolve()}."

    overwritten = wrapper.execute_tool("write_file", {"file_path": "note.txt", "content": "beta\n"}, state)
    assert overwritten["success"] is True
    assert overwritten["result"] == f"Successfully overwrote file: {(tmp_path / 'note.txt').resolve()}."
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "beta\n"


def test_replace_reports_missing_zero_match_and_multiple_match_cases(tmp_path: Path) -> None:
    wrapper, state = _replace_wrapper(tmp_path)
    missing = wrapper.execute_tool(
        "replace",
        {"file_path": "missing.txt", "instruction": "create", "old_string": "needle", "new_string": "value"},
        state,
    )
    assert missing == {"success": False, "error": f"File not found: {(tmp_path / 'missing.txt').resolve()}"}

    target = tmp_path / "sample.txt"
    target.write_text("one\ntwo\none\n", encoding="utf-8")
    zero = wrapper.execute_tool(
        "replace",
        {"file_path": "sample.txt", "instruction": "swap", "old_string": "missing", "new_string": "new"},
        state,
    )
    assert "0 occurrences found for old_string" in zero["error"]

    multiple = wrapper.execute_tool(
        "replace",
        {"file_path": "sample.txt", "instruction": "swap", "old_string": "one", "new_string": "ONE"},
        state,
    )
    assert "Expected 1 occurrence but found 2" in multiple["error"]


def test_replace_allow_multiple_updates_all_matches(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("one\ntwo\none\n", encoding="utf-8")
    wrapper, state = _replace_wrapper(tmp_path)
    result = wrapper.execute_tool(
        "replace",
        {
            "file_path": "sample.txt",
            "instruction": "replace the repeated token",
            "old_string": "one",
            "new_string": "ONE",
            "allow_multiple": True,
        },
        state,
    )
    assert result["success"] is True
    assert result["result"] == f"Successfully modified file: {target.resolve()} (2 replacements)."
    assert target.read_text(encoding="utf-8") == "ONE\ntwo\nONE\n"


def test_replace_allows_empty_or_missing_instruction(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("alpha\n", encoding="utf-8")
    wrapper, state = _replace_wrapper(tmp_path)

    empty_instruction = wrapper.execute_tool(
        "replace",
        {
            "file_path": "note.txt",
            "instruction": "",
            "old_string": "alpha",
            "new_string": "beta",
        },
        state,
    )
    assert empty_instruction["success"] is True
    assert target.read_text(encoding="utf-8") == "beta\n"

    target.write_text("alpha\n", encoding="utf-8")
    missing_instruction = wrapper.execute_tool(
        "replace",
        {
            "file_path": "note.txt",
            "old_string": "alpha",
            "new_string": "beta",
        },
        state,
    )
    assert missing_instruction["success"] is True
    assert target.read_text(encoding="utf-8") == "beta\n"


def test_pipeline_returns_final_tool_message_for_replace(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("alpha\n", encoding="utf-8")
    core = AgentCore()
    core.register_tool(GeminiReplaceTool)
    messages = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "replace",
                    "arguments": {
                        "file_path": "note.txt",
                        "instruction": "Rename alpha to beta",
                        "old_string": "alpha",
                        "new_string": "beta",
                    },
                },
            }
        ],
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        },
    )
    assert messages[0]["content"] == f"Successfully modified file: {target.resolve()} (1 replacements)."
    assert messages[0]["metadata"]["tool_name"] == "replace"