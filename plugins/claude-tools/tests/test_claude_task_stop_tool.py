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

from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    compose_tool_interop_registry,
)
from claude_tools import ClaudeTaskStopTool
from tool_compat_shared import ensure_background_process_registry


def _wrapper(tmp_path: Path):
    tool = ClaudeTaskStopTool()
    state = tool.init({"working_directory": str(tmp_path)})
    context = {"runtime_state_root": tmp_path / ".crystal" / "runtime"}
    return tool, state, context


def _fixture(name: str) -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "investigation"
        / "fixtures"
        / "task-stop"
        / f"{name}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _materialize_fixture(
    value,
    *,
    tool_call_id: str | None = None,
    background_id: str | None = None,
):
    if isinstance(value, str):
        rendered = value
        if tool_call_id is not None:
            rendered = rendered.replace("<TOOL_CALL_ID>", tool_call_id)
        if background_id is not None:
            rendered = rendered.replace("<BACKGROUND_ID>", background_id)
        return rendered
    if isinstance(value, list):
        return [
            _materialize_fixture(
                item,
                tool_call_id=tool_call_id,
                background_id=background_id,
            )
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _materialize_fixture(
                item,
                tool_call_id=tool_call_id,
                background_id=background_id,
            )
            for key, item in value.items()
        }
    return value


def test_schema_matches_observed_fixture(tmp_path: Path) -> None:
    tool, state, _context = _wrapper(tmp_path)

    assert (
        tool.get_tool_schemas(state)[0]
        == _fixture("success-stop-background-task")["tool_schema"]
    )


def test_anthropic_schema_converts_to_openai_chat_schema(tmp_path: Path) -> None:
    tool, state, _context = _wrapper(tmp_path)
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
    assert converted["function"]["name"] == "TaskStop"
    assert converted["function"]["parameters"] == schema["input_schema"]


def test_success_stop_matches_fixture(tmp_path: Path) -> None:
    tool, state, context = _wrapper(tmp_path)
    registry = ensure_background_process_registry(
        runtime_state_root=context["runtime_state_root"]
    )
    record = registry.start_background_command(
        "while true; do sleep 60; done",
        working_directory=str(tmp_path),
        ownership_mode="tracked",
        shutdown_policy="leave_running",
    )
    try:
        result = tool.execute_tool(
            "TaskStop",
            {"task_id": record.process_id},
            state,
            tool_call={"id": "call_taskstop_1"},
            context=context,
        )

        expected = _materialize_fixture(
            _fixture("success-stop-background-task")["tool_result_message"],
            tool_call_id="call_taskstop_1",
            background_id=record.process_id,
        )
        assert result["text"] == expected["content"][0]["content"]
        assert result["success"] is True
        assert result["anthropic_content"][0].get("is_error") is None
    finally:
        refreshed = registry.get_process(record.process_id)
        if refreshed.status == "running":
            if os.name != "nt":
                os.killpg(os.getpgid(record.pid), signal.SIGTERM)
            else:
                os.kill(record.pid, signal.SIGTERM)


def test_shell_id_alias_stops_task(tmp_path: Path) -> None:
    tool, state, context = _wrapper(tmp_path)
    registry = ensure_background_process_registry(
        runtime_state_root=context["runtime_state_root"]
    )
    record = registry.start_background_command(
        "while true; do sleep 60; done",
        working_directory=str(tmp_path),
        ownership_mode="tracked",
        shutdown_policy="leave_running",
    )

    result = tool.execute_tool(
        "TaskStop",
        {"shell_id": record.process_id},
        state,
        tool_call={"id": "call_taskstop_1"},
        context=context,
    )

    assert result["success"] is True
    assert record.process_id in result["text"]


def test_error_task_not_found_matches_fixture(tmp_path: Path) -> None:
    tool, state, context = _wrapper(tmp_path)
    result = tool.execute_tool(
        "TaskStop",
        {"task_id": "does-not-exist"},
        state,
        tool_call={"id": "call_taskstop_1"},
        context=context,
    )

    expected = _materialize_fixture(
        _fixture("error-task-not-found")["tool_result_message"],
        tool_call_id="call_taskstop_1",
    )
    assert result["text"] == expected["content"][0]["content"]
    assert result["success"] is False
    assert result["anthropic_content"][0]["is_error"] is True


def test_error_invalid_parameters_matches_fixture(tmp_path: Path) -> None:
    tool, state, context = _wrapper(tmp_path)
    result = tool.execute_tool(
        "TaskStop",
        {"task_id": "does-not-exist", "block": "true", "timeout": "10000"},
        state,
        tool_call={"id": "call_taskstop_1"},
        context=context,
    )

    expected = _materialize_fixture(
        _fixture("error-invalid-parameters")["tool_result_message"],
        tool_call_id="call_taskstop_1",
    )
    assert result["text"] == expected["content"][0]["content"]
    assert result["success"] is False
    assert result["anthropic_content"][0]["is_error"] is True