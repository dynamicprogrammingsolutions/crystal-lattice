from __future__ import annotations

from pathlib import Path

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore
from agent_core.plugin import ToolWrapper

from gemini_tools import GeminiReadFileTool


def _make_wrapper(tmp_path: Path) -> tuple[ToolWrapper, dict]:
    wrapper = ToolWrapper(GeminiReadFileTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        }
    )
    return wrapper, state


def test_schema_matches_gemini_surface(tmp_path: Path) -> None:
    wrapper, state = _make_wrapper(tmp_path)
    schema = wrapper.get_tool_schemas(state)[0]
    function = schema["function"]
    assert function["name"] == "read_file"
    assert function["parameters"]["required"] == ["file_path"]
    assert list(function["parameters"]["properties"].keys()) == [
        "file_path",
        "start_line",
        "end_line",
    ]
    assert "Handles text, images" in function["description"]


def test_reads_text_and_formats_truncation_banner(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("Line 1\n" + ("a" * 2200) + "\nLine 3\n", encoding="utf-8")
    wrapper, state = _make_wrapper(tmp_path)
    result = wrapper.execute_tool("read_file", {"file_path": "sample.txt"}, state)
    text = wrapper.format_tool_result(result, state)
    assert result["success"] is True
    assert "IMPORTANT: The file content has been truncated." in text
    assert "--- FILE CONTENT (truncated) ---" in text
    assert "... [truncated]" in text


def test_reports_missing_file_directory_and_ignore(tmp_path: Path) -> None:
    wrapper, state = _make_wrapper(tmp_path)
    missing = wrapper.execute_tool("read_file", {"file_path": "missing.txt"}, state)
    assert missing["success"] is False
    assert missing["error"] == f"File not found: {(tmp_path / 'missing.txt').resolve()}"

    directory = tmp_path / "folder"
    directory.mkdir()
    result = wrapper.execute_tool("read_file", {"file_path": "folder"}, state)
    assert result["success"] is False
    assert result["error"] == f"Path is a directory, not a file: {directory.resolve()}"

    (tmp_path / ".geminiignore").write_text("secret.txt\n", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("hidden", encoding="utf-8")
    ignored = wrapper.execute_tool("read_file", {"file_path": "secret.txt"}, state)
    assert ignored == {
        "success": False,
        "error": f"File path '{(tmp_path / 'secret.txt').resolve()}' is ignored by configured ignore patterns.",
    }


def test_handles_binary_svg_and_inline_image_payloads(tmp_path: Path) -> None:
    wrapper, state = _make_wrapper(tmp_path)

    binary = tmp_path / "binary.bin"
    binary.write_bytes(b"\x00\xff\x00\xff")
    binary_result = wrapper.execute_tool("read_file", {"file_path": "binary.bin"}, state)
    assert binary_result["success"] is True
    assert binary_result["result"] == "Cannot display content of binary file: binary.bin"

    svg = tmp_path / "large.svg"
    svg.write_text("<svg>" + ("x" * ((1024 * 1024) + 1)) + "</svg>", encoding="utf-8")
    svg_result = wrapper.execute_tool("read_file", {"file_path": "large.svg"}, state)
    assert svg_result["success"] is True
    assert svg_result["result"] == "Cannot display content of SVG file larger than 1MB: large.svg"

    image = tmp_path / "image.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    image_result = wrapper.execute_tool("read_file", {"file_path": "image.png"}, state)
    assert image_result["success"] is True
    assert image_result["kind"] == "inline"
    assert image_result["result"]["inlineData"]["mimeType"] == "image/png"


def test_pipeline_returns_final_tool_message(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("hello from gemini\n", encoding="utf-8")
    core = AgentCore()
    core.register_tool(GeminiReadFileTool)
    messages = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "read_file", "arguments": {"file_path": "note.txt"}},
            }
        ],
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
            "project_temp_dir": str(tmp_path / ".temp"),
        },
    )
    assert messages[0]["role"] == "tool"
    assert messages[0]["content"] == "hello from gemini\n"
    assert messages[0]["metadata"]["tool_name"] == "read_file"


def test_plugin_manager_loads_package_with_sibling_dependency(tmp_path: Path) -> None:
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
        "GeminiShellTool",
        "GeminiWebFetchTool",
    ]