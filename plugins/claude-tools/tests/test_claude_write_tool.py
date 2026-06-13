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
from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
    TOOL_RESULT_FIELD,
    openai_chat_tool_result_content,
)
from claude_tools import ClaudeReadTool, ClaudeWriteTool


def _wrapper(tmp_path: Path):
    tool = ClaudeWriteTool()
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
        / "write"
        / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _materialize_fixture(
    value,
    tmp_path: Path,
    *,
    tool_call_id: str | None = None,
):
    if isinstance(value, str):
        rendered = value.replace("<WORKSPACE>", str(tmp_path))
        if tool_call_id is not None:
            rendered = rendered.replace("<TOOL_CALL_ID>", tool_call_id)
        return rendered
    if isinstance(value, list):
        return [
            _materialize_fixture(item, tmp_path, tool_call_id=tool_call_id)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _materialize_fixture(item, tmp_path, tool_call_id=tool_call_id)
            for key, item in value.items()
        }
    return value


def _execute_messages(tmp_path: Path, calls: list[dict]) -> list[dict]:
    core = AgentCore()
    core.register_tool(ClaudeReadTool)
    core.register_tool(ClaudeWriteTool)
    return list(
        core.iter_tool_messages(
            calls,
            {
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
            },
        )
    )


def test_schema_matches_observed_fixture(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)

    assert (
        tool.get_tool_schemas(state)[0]
        == _fixture("success-create-file")["tool_schema"]
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
    assert converted["function"]["name"] == "Write"
    assert converted["function"]["parameters"] == schema["input_schema"]


def test_create_file_returns_native_tool_result_and_writes_content(
    tmp_path: Path,
) -> None:
    target = tmp_path / "note.txt"

    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_write_1",
                "type": "function",
                "function": {
                    "name": "Write",
                    "arguments": json.dumps(
                        {
                            "file_path": str(target),
                            "content": "WRITE_SENTINEL one two three",
                        }
                    ),
                },
            }
        ],
    )

    assert target.read_text(encoding="utf-8") == "WRITE_SENTINEL one two three"
    assert len(messages) == 1
    expected_message = _materialize_fixture(
        _fixture("success-create-file")["tool_result_message"],
        tmp_path,
        tool_call_id="call_write_1",
    )
    assert messages[0]["content"] == expected_message["content"][0]["content"]
    tool_result = messages[0][TOOL_RESULT_FIELD]
    assert tool_result["format"] == FORMAT_ANTHROPIC_MESSAGES
    assert tool_result["content"] == expected_message["content"]

    chat_content = openai_chat_tool_result_content(tool_result)
    assert chat_content == [
        {
            "type": "text",
            "text": "File created successfully at: " + str(target),
        }
    ]


def test_existing_file_requires_prior_read(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("OLD_CONTENT\n", encoding="utf-8")

    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_write_1",
                "type": "function",
                "function": {
                    "name": "Write",
                    "arguments": json.dumps(
                        {"file_path": str(target), "content": "NEW_CONTENT"}
                    ),
                },
            }
        ],
    )

    assert len(messages) == 1
    expected_message = _fixture("error-overwrite-without-read")["tool_result_message"]
    assert messages[0]["content"] == expected_message["content"][0]["content"]
    block = messages[0][TOOL_RESULT_FIELD]["content"][0]
    assert block["is_error"] is True


def test_existing_file_can_be_overwritten_after_read(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("OLD_CONTENT\n", encoding="utf-8")

    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_read_1",
                "type": "function",
                "function": {
                    "name": "Read",
                    "arguments": json.dumps({"file_path": str(target)}),
                },
            },
            {
                "id": "call_write_1",
                "type": "function",
                "function": {
                    "name": "Write",
                    "arguments": json.dumps(
                        {"file_path": str(target), "content": "NEW_CONTENT"}
                    ),
                },
            },
        ],
    )

    assert len(messages) == 2
    assert target.read_text(encoding="utf-8") == "NEW_CONTENT"
    expected_message = _materialize_fixture(
        _fixture("success-overwrite-after-read")["tool_result_message"],
        tmp_path,
        tool_call_id="call_write_1",
    )
    assert messages[1]["content"] == expected_message["content"][0]["content"]


def test_create_missing_parent_directories(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "dir" / "note.txt"

    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_write_1",
                "type": "function",
                "function": {
                    "name": "Write",
                    "arguments": json.dumps(
                        {
                            "file_path": str(target),
                            "content": "WRITE_SENTINEL nested",
                        }
                    ),
                },
            }
        ],
    )

    assert target.read_text(encoding="utf-8") == "WRITE_SENTINEL nested"
    expected_message = _materialize_fixture(
        _fixture("success-create-missing-parent")["tool_result_message"],
        tmp_path,
        tool_call_id="call_write_1",
    )
    assert messages[0]["content"] == expected_message["content"][0]["content"]