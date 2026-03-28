"""Unit tests for ShellTool plugin."""

from agent_core.plugin import ToolWrapper
from codex_tools.shell_tool import ShellTool


def test_shell_tool_runs_basic_command(tmp_path):
    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    schemas = wrapper.get_tool_schemas(state)
    assert schemas and schemas[0]["function"]["name"] == "shell_legacy"

    # Run a very simple, fast command
    result = wrapper.execute_tool(
        "shell_legacy",
        {"command": "echo 'hello from shell'", "workdir": str(tmp_path)},
        state,
    )

    assert result["success"] is True
    assert "hello from shell" in result.get("stdout", "")

    formatted = wrapper.format_tool_result(result, state)
    # For a clean success with no stderr and no truncation,
    # format_tool_result should return just the raw stdout.
    assert "hello from shell" in formatted
    assert "Command succeeded" not in formatted
    assert "STDOUT" not in formatted

    display = wrapper.to_display_format(formatted, result, state)
    assert display.get("type") == "text"
    assert display.get("single_line") == "echo 'hello from shell'"


def test_shell_tool_includes_headers_on_failure(tmp_path):
    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    # Command that writes to both stdout and stderr and exits non-zero.
    result = wrapper.execute_tool(
        "shell_legacy",
        {
            "command": "echo 'out'; echo 'err' 1>&2; exit 1",
            "workdir": str(tmp_path),
        },
        state,
    )

    assert result["success"] is False

    formatted = wrapper.format_tool_result(result, state)
    assert "Command failed" in formatted or "Command exited with code" in formatted
    assert "STDOUT:" in formatted
    assert "STDERR:" in formatted


def test_shell_tool_streams_stdout(tmp_path):
    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    chunks = list(
        wrapper.stream_tool(
            "shell_legacy",
            {"command": "printf 'a\\n'", "workdir": str(tmp_path)},
            state,
        )
    )

    assert chunks, "expected at least one streamed chunk"
    partials = [
        p
        for c in chunks
        if isinstance(c, dict)
        for p in [c.get("part")]
        if isinstance(p, dict)
    ]
    assert partials, "expected at least one streamed partial payload"
    assert any(p.get("type") == "text" for p in partials)
    assert any("a" in str(p.get("content", "")) for p in partials)
    # Final RESULT dict should also be present
    assert any(isinstance(c, dict) and "success" in c for c in chunks)


def test_shell_tool_streams_exit_code_and_stderr_at_end(tmp_path):
    """Streaming output should end with exit code and stderr summary."""

    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    command = "echo 'out'; echo 'err' 1>&2; exit 1"

    chunks = list(
        wrapper.stream_tool(
            "shell_legacy",
            {"command": command, "workdir": str(tmp_path)},
            state,
        )
    )

    parts = [c.get("part") for c in chunks if isinstance(c, dict) and "part" in c]
    texts = [str(p.get("content", "")) for p in parts if isinstance(p, dict)]

    # There should be at least one partial containing the stderr and
    # exit-code summary near the end of the stream.
    combined = "\n".join(texts)
    assert "Command exited with code 1" in combined or "Command failed" in combined
    assert "STDERR:" in combined
    assert "err" in combined


def _get_final_stream_result(events):
    results = [e for e in events if isinstance(e, dict) and "success" in e]
    assert results, "expected a final result payload from stream_tool"
    return results[-1]


def test_shell_tool_stream_respects_max_output_lines_at_limit(tmp_path):
    """Exactly max_output_lines lines should be preserved without truncation."""

    wrapper = ToolWrapper(ShellTool)
    # Configure a large line limit and a generous character cap so that
    # truncation is governed by lines, not characters.
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "max_output_lines": 8000,
        }
    )

    command = "for i in {1..8000}; do echo \"LINE $i\"; done"

    events = list(
        wrapper.stream_tool(
            "shell_legacy",
            {"command": command, "workdir": str(tmp_path)},
            state,
        )
    )

    final = _get_final_stream_result(events)
    stdout_text = str(final.get("stdout") or "")
    lines = stdout_text.splitlines()

    # All 8000 lines from the command output should be present and
    # there should be no truncation marker.
    assert final.get("stdout_truncated") is False
    assert len(lines) == 8000
    assert lines[0] == "LINE 1"
    assert lines[-1] == "LINE 8000"
    assert "... (truncated," not in stdout_text


def test_shell_tool_stream_truncates_above_max_output_lines(tmp_path):
    """More than max_output_lines lines should trigger truncation."""

    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "max_output_lines": 8000,
        }
    )

    command = "for i in {1..8001}; do echo \"LINE $i\"; done"

    events = list(
        wrapper.stream_tool(
            "shell_legacy",
            {"command": command, "workdir": str(tmp_path)},
            state,
        )
    )

    final = _get_final_stream_result(events)
    stdout_text = str(final.get("stdout") or "")
    lines = stdout_text.splitlines()

    # The stored stdout should be truncated: only the first 8000
    # command-output lines are kept, followed by the truncation note.
    assert final.get("stdout_truncated") is True
    assert "LINE 8001" not in stdout_text
    assert "LINE 1" == lines[0]
    assert "LINE 8000" == lines[7999]
    assert any("truncated" in line for line in lines[-2:])
    assert "... (truncated," in stdout_text

    # Streaming mode should also emit a summary part indicating that
    # stdout was truncated.
    summary_parts = [
        e.get("part")
        for e in events
        if isinstance(e, dict) and e.get("part", {}).get("type") == "summary"
    ]
    combined_summary = "".join(
        str(p.get("content", "")) for p in summary_parts if isinstance(p, dict)
    )
    assert "STDOUT was truncated" in combined_summary


def test_shell_tool_respects_timeout_execute(tmp_path):
    """Non-streaming execute_tool should enforce the per-call timeout."""

    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    # This command would normally sleep for 5 seconds; the timeout of 1 second
    # should cause it to be terminated early.
    result = wrapper.execute_tool(
        "shell_legacy",
        {"command": "sleep 5", "timeout_seconds": 1, "workdir": str(tmp_path)},
        state,
    )

    assert result["success"] is False
    assert result.get("returncode") is None
    assert "timed out" in (result.get("error") or "")
    assert result.get("timeout_seconds") == 1


def test_shell_tool_respects_timeout_streaming(tmp_path):
    """Streaming mode should stop emitting once the timeout is reached."""

    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    # This would print 10 lines over ~10 seconds. A timeout of 2 seconds
    # should stop the command early, so we never see the later lines.
    command = "for i in {1..10}; do echo \"Hello $i\"; sleep 1; done"

    events = list(
        wrapper.stream_tool(
            "shell_legacy",
            {"command": command, "timeout_seconds": 2, "workdir": str(tmp_path)},
            state,
        )
    )

    # Extract the final RESULT dict and the aggregated stdout it reports.
    results = [e for e in events if isinstance(e, dict) and "success" in e]
    assert results, "expected a final result payload from stream_tool"
    final = results[-1]

    assert final["success"] is False
    assert final.get("returncode") is None
    assert "timed out" in (final.get("error") or "")

    stdout_text = str(final.get("stdout") or "")
    assert "Hello 1" in stdout_text
    # We should have timed out well before the final iteration.
    assert "Hello 10" not in stdout_text


def test_shell_tool_marks_truncated_output_in_format(tmp_path):
    """When stdout is truncated, format_tool_result marks it explicitly."""

    wrapper = ToolWrapper(ShellTool)
    # Force a very small character limit so truncation is guaranteed.
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "max_output_chars": 16,
            "max_output_lines": 10,
        }
    )

    result = wrapper.execute_tool(
        "shell_legacy",
        {"command": "printf 'abcdefghijklmnopqrstuvwxyz'", "workdir": str(tmp_path)},
        state,
    )

    assert result["success"] is True
    # Confirm that truncation metadata is present.
    assert result.get("stdout_truncated") is True

    formatted = wrapper.format_tool_result(result, state)
    assert "STDOUT (truncated):" in formatted
    assert "... (truncated," in formatted


def test_shell_tool_stream_truncates_long_single_line_by_char_limit(tmp_path):
    """Streaming mode should truncate a very long single-line stdout payload."""

    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init(
        {
            "working_directory": str(tmp_path),
            "max_output_chars": 16,
            "max_output_lines": 10,
        }
    )

    events = list(
        wrapper.stream_tool(
            "shell_legacy",
            {"command": "printf 'abcdefghijklmnopqrstuvwxyz'", "workdir": str(tmp_path)},
            state,
        )
    )

    final = _get_final_stream_result(events)

    assert final["success"] is True
    assert final.get("stdout_truncated") is True
    assert final.get("stdout", "").startswith("abcdefghijklmnop")
    assert "... (truncated," in str(final.get("stdout") or "")

    summary_parts = [
        e.get("part")
        for e in events
        if isinstance(e, dict) and e.get("part", {}).get("type") == "summary"
    ]
    combined_summary = "".join(
        str(p.get("content", "")) for p in summary_parts if isinstance(p, dict)
    )
    assert "STDOUT was truncated" in combined_summary
