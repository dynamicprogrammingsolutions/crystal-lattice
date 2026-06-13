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
import os
import signal
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
from agent_core.tool_result_payloads import FORMAT_ANTHROPIC_MESSAGES, TOOL_RESULT_FIELD
from claude_tools import ClaudeBashTool


def _wrapper(tmp_path: Path):
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
        }
    )
    return tool, state


def _fixture(name: str) -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "investigation"
        / "fixtures"
        / "bash"
        / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _materialize_fixture(
    value,
    tmp_path: Path,
    *,
    tool_call_id: str | None = None,
    background_id: str | None = None,
    background_output_path: str | None = None,
):
    if isinstance(value, str):
        rendered = value.replace("<WORKING_DIRECTORY>", str(tmp_path))
        if tool_call_id is not None:
            rendered = rendered.replace("<TOOL_CALL_ID>", tool_call_id)
        if background_id is not None:
            rendered = rendered.replace("<BACKGROUND_ID>", background_id)
        if background_output_path is not None:
            rendered = rendered.replace(
                "<BACKGROUND_OUTPUT_PATH>", background_output_path
            )
        return rendered
    if isinstance(value, list):
        return [
            _materialize_fixture(
                item,
                tmp_path,
                tool_call_id=tool_call_id,
                background_id=background_id,
                background_output_path=background_output_path,
            )
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _materialize_fixture(
                item,
                tmp_path,
                tool_call_id=tool_call_id,
                background_id=background_id,
                background_output_path=background_output_path,
            )
            for key, item in value.items()
        }
    return value


def _execute_messages(tmp_path: Path, calls: list[dict]) -> list[dict]:
    core = AgentCore()
    core.register_tool(ClaudeBashTool)
    return list(
        core.iter_tool_messages(
            calls,
            {
                "working_directory": str(tmp_path),
            },
        )
    )


def test_schema_matches_observed_fixture(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)

    assert tool.get_tool_schemas(state)[0] == _fixture("success-pwd")["tool_schema"]


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
    assert converted["function"]["name"] == "Bash"
    assert converted["function"]["parameters"] == schema["input_schema"]


def test_success_pwd_matches_fixture(tmp_path: Path) -> None:
    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_bash_1",
                "type": "function",
                "function": {
                    "name": "Bash",
                    "arguments": json.dumps(
                        {
                            "command": "pwd",
                            "description": "Print working directory",
                        }
                    ),
                },
            }
        ],
    )

    expected = _materialize_fixture(
        _fixture("success-pwd")["tool_result_message"],
        tmp_path,
        tool_call_id="call_bash_1",
    )
    assert messages[0]["content"] == expected["content"][0]["content"]
    assert messages[0][TOOL_RESULT_FIELD]["format"] == FORMAT_ANTHROPIC_MESSAGES


def test_success_stderr_zero_matches_fixture(tmp_path: Path) -> None:
    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_bash_1",
                "type": "function",
                "function": {
                    "name": "Bash",
                    "arguments": json.dumps(
                        {
                            "command": 'sh -c "echo problem 1>&2; exit 0"',
                            "description": "Run shell command echoing problem to stderr",
                        }
                    ),
                },
            }
        ],
    )

    expected = _fixture("success-stderr-zero")["tool_result_message"]["content"][0]
    assert messages[0]["content"] == expected["content"]


def test_error_nonzero_matches_fixture(tmp_path: Path) -> None:
    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_bash_1",
                "type": "function",
                "function": {
                    "name": "Bash",
                    "arguments": json.dumps(
                        {
                            "command": 'sh -c "echo problem 1>&2; exit 7"',
                            "description": "Run shell command with stderr output and exit code 7",
                        }
                    ),
                },
            }
        ],
    )

    expected = _fixture("error-nonzero")["tool_result_message"]["content"][0]
    assert messages[0]["content"] == expected["content"]
    assert messages[0][TOOL_RESULT_FIELD]["content"][0]["is_error"] is True


def test_timeout_matches_fixture(tmp_path: Path) -> None:
    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_bash_1",
                "type": "function",
                "function": {
                    "name": "Bash",
                    "arguments": json.dumps(
                        {
                            "command": "sleep 2",
                            "description": "Sleep for 2 seconds",
                            "timeout": 200,
                        }
                    ),
                },
            }
        ],
    )

    expected = _fixture("error-timeout")["tool_result_message"]["content"][0]
    assert messages[0]["content"] == expected["content"]
    assert messages[0][TOOL_RESULT_FIELD]["content"][0]["is_error"] is True


def test_cwd_reset_matches_fixture(tmp_path: Path) -> None:
    (tmp_path / "subdir").mkdir()
    messages = _execute_messages(
        tmp_path,
        [
            {
                "id": "call_bash_1",
                "type": "function",
                "function": {
                    "name": "Bash",
                    "arguments": json.dumps(
                        {
                            "command": f'cd "{tmp_path / "subdir"}" && pwd',
                            "description": "Change to subdir and print working directory",
                        }
                    ),
                },
            }
        ],
    )

    expected = _materialize_fixture(
        _fixture("success-cwd-reset")["tool_result_message"],
        tmp_path,
        tool_call_id="call_bash_1",
    )
    assert messages[0]["content"] == expected["content"][0]["content"]


def test_background_matches_fixture_and_creates_output_file(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)
    result = tool.execute_tool(
        "Bash",
        {
            "command": "sleep 5",
            "description": "Sleep for 5 seconds in background",
            "run_in_background": True,
        },
        state,
        tool_call={"id": "call_bash_1"},
    )
    pid = int(result["pid"])
    try:
        expected = _materialize_fixture(
            _fixture("success-background")["tool_result_message"],
            tmp_path,
            tool_call_id="call_bash_1",
            background_id=str(result["background_id"]),
            background_output_path=str(result["output_path"]),
        )
        assert result["text"] == expected["content"][0]["content"]
        assert Path(str(result["output_path"])).exists()
    finally:
        if os.name != "nt":
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)