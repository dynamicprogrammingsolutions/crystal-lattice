# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

# ruff: noqa: E402

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE_PY = ROOT / "core/python"
PLUGIN_SRC = ROOT / "plugins/claude-tools/src"
SHARED_SRC = ROOT / "plugins/tool-compat-shared/src"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
if str(PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SRC))
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))

from agent_core import AgentCore
from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    compose_tool_interop_registry,
)
from agent_core.tool_result_payloads import (  # noqa: E402
    FORMAT_ANTHROPIC_MESSAGES,
    TOOL_RESULT_FIELD,
    openai_chat_tool_result_content,
)
from claude_tools import ClaudeReadTool  # noqa: E402


PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"


def _png_bytes() -> bytes:
    return base64.b64decode(PNG_BASE64)


def _wrapper(tmp_path: Path):
    tool = ClaudeReadTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
            "allowed_paths": [str(tmp_path)],
        }
    )
    return tool, state


def _fixture(name: str) -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "investigation"
        / "fixtures"
        / "read"
        / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _execute_with_core(tmp_path: Path, arguments: dict) -> dict:
    core = AgentCore()
    core.register_tool(ClaudeReadTool)
    messages = list(
        core.iter_tool_messages(
            [
                {
                    "id": "call_read_1",
                    "type": "function",
                    "function": {
                        "name": "Read",
                        "arguments": json.dumps(arguments),
                    },
                }
            ],
            {
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
            },
        )
    )
    assert len(messages) == 1
    return messages[0]


def test_schema_matches_observed_fixture(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)

    assert (
        tool.get_tool_schemas(state)[0] == _fixture("success-small-file")["tool_schema"]
    )


def test_anthropic_schema_converts_to_openai_chat_schema(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)
    schema = tool.get_tool_schemas(state)[0]
    registry = compose_tool_interop_registry(
        contributed=[tool.get_tool_interop_contribution(state)],
        defaults=DEFAULT_TOOL_INTEROP_REGISTRY,
    )

    converted = registry.convert_schemas(
        [schema],
        target_formats=["openai.chat_completions.function.tool_schema"],
    )[0]

    assert converted["type"] == "function"
    assert converted["function"]["name"] == "Read"
    assert converted["function"]["parameters"] == schema["input_schema"]


def test_core_text_read_returns_anthropic_native_tool_result(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("alpha\nbeta\n", encoding="utf-8")

    message = _execute_with_core(tmp_path, {"file_path": str(path)})

    assert message["role"] == "tool"
    assert message["content"] == "1\talpha\n2\tbeta\n3\t"
    tool_result = message[TOOL_RESULT_FIELD]
    assert tool_result["format"] == FORMAT_ANTHROPIC_MESSAGES
    assert tool_result["content"] == [
        {
            "type": "tool_result",
            "tool_use_id": "call_read_1",
            "content": "1\talpha\n2\tbeta\n3\t",
            "cache_control": {"type": "ephemeral"},
        }
    ]


def test_core_offset_limit_read_uses_one_based_line_numbers(tmp_path: Path) -> None:
    path = tmp_path / "range.txt"
    path.write_text(
        "\n".join(f"line-{index}" for index in range(1, 6)), encoding="utf-8"
    )

    message = _execute_with_core(
        tmp_path, {"file_path": str(path), "offset": 3, "limit": 2}
    )

    assert message["content"] == "3\tline-3\n4\tline-4"


def test_missing_file_error_matches_observed_shape(tmp_path: Path) -> None:
    path = tmp_path / "missing.txt"

    message = _execute_with_core(tmp_path, {"file_path": str(path)})

    block = message[TOOL_RESULT_FIELD]["content"][0]
    assert block["is_error"] is True
    assert block["cache_control"] == {"type": "ephemeral"}
    assert block["content"] == (
        f"File does not exist. Note: your current working directory is {tmp_path}."
    )


def test_image_read_returns_anthropic_image_and_openai_chat_conversion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "tiny.png"
    path.write_bytes(_png_bytes())

    message = _execute_with_core(tmp_path, {"file_path": str(path)})

    tool_result = message[TOOL_RESULT_FIELD]
    block = tool_result["content"][0]
    assert block["type"] == "tool_result"
    assert block["content"][0]["type"] == "image"
    assert block["content"][0]["source"]["media_type"] == "image/png"

    chat_content = openai_chat_tool_result_content(tool_result)
    assert chat_content is not None
    assert chat_content[0]["type"] == "image_url"
    assert chat_content[0]["image_url"]["url"].startswith("data:image/png;base64,")


def test_notebook_read_returns_text_block_array(tmp_path: Path) -> None:
    path = tmp_path / "simple.ipynb"
    path.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": ["# CLAUDE_NOTEBOOK_SENTINEL\n"],
                    },
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "execution_count": 1,
                        "outputs": [
                            {
                                "name": "stdout",
                                "output_type": "stream",
                                "text": ["CLAUDE_NOTEBOOK_OUTPUT\n"],
                            }
                        ],
                        "source": ["print('CLAUDE_NOTEBOOK_OUTPUT')\n"],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )

    message = _execute_with_core(tmp_path, {"file_path": str(path)})

    block = message[TOOL_RESULT_FIELD]["content"][0]
    assert isinstance(block["content"], list)
    assert block["content"][0]["type"] == "text"
    assert "CLAUDE_NOTEBOOK_SENTINEL" in block["content"][0]["text"]
    assert "CLAUDE_NOTEBOOK_OUTPUT" in block["content"][0]["text"]


def test_small_pdf_read_returns_status_tool_result(tmp_path: Path) -> None:
    path = tmp_path / "small.pdf"
    path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"
    )

    message = _execute_with_core(tmp_path, {"file_path": str(path)})

    block = message[TOOL_RESULT_FIELD]["content"][0]
    assert block == {
        "type": "tool_result",
        "tool_use_id": "call_read_1",
        "content": f"PDF file read: {path} ({path.stat().st_size} bytes)",
    }
