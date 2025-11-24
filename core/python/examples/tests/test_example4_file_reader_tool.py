"""
Tests for examples/file_reader_tool.py
"""

import os
import sys
import tempfile



def test_file_reader_tool_reads_file():
    from examples.example4_file_reader_tool import FileReaderTool

    cfg = {"allowed_paths": ["."], "max_file_size": 1024 * 1024}
    state = FileReaderTool().init(cfg)

    with tempfile.NamedTemporaryFile("w+", delete=False, dir=".") as tf:
        tf.write("hello world")
        tf.flush()
        path = tf.name

    try:
        result = FileReaderTool().execute_tool("read_file", {"file_path": path}, state)
        assert result.get("success") is True
        formatted = FileReaderTool().format_tool_result(result, state)
        assert "hello world" in formatted
    finally:
        os.unlink(path)
