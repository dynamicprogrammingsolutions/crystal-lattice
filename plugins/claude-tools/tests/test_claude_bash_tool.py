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
import threading
import time
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
from claude_tools.claude_bash_tool import (
    BASH_DESCRIPTION,
    _apply_cwd_lines,
    _bash_description_for_options,
    _cwd_for_storage,
    _last_bash_end_cwd_from_context,
    _resolve_stored_cwd,
    _UPSTREAM_CD_GUIDANCE,
    _UPSTREAM_OPENING,
)


class _TestCancellation:
    def __init__(self) -> None:
        self._callback = None

    def add_callback(self, callback):
        self._callback = callback
        return 1

    def remove_callback(self, token: int) -> None:
        self._callback = None

    def cancel(self) -> None:
        if self._callback is not None:
            self._callback()


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


def test_success_no_output_matches_fixture(tmp_path: Path) -> None:
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
                            "command": "true",
                            "description": "Run true command",
                        }
                    ),
                },
            }
        ],
    )

    expected = _fixture("success-no-output")["tool_result_message"]["content"][0]
    assert messages[0]["content"] == expected["content"]
    assert messages[0][TOOL_RESULT_FIELD]["content"][0]["is_error"] is False


def test_error_no_output_matches_fixture(tmp_path: Path) -> None:
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
                            "command": 'sh -c "exit 7"',
                            "description": "Exit with code 7",
                        }
                    ),
                },
            }
        ],
    )

    expected = _fixture("error-no-output")["tool_result_message"]["content"][0]
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


def test_hard_cancellation_stops_foreground_bash(tmp_path: Path) -> None:
    tool, state = _wrapper(tmp_path)
    cancellation = _TestCancellation()
    result: dict = {}

    worker = threading.Thread(
        target=lambda: result.update(
            tool.execute_tool(
                "Bash",
                {"command": "sleep 60"},
                state,
                cancellation=cancellation,
            )
        )
    )
    worker.start()
    time.sleep(0.2)
    cancellation.cancel()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert result["success"] is False
    assert result["cancelled"] is True


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


# ---------------------------------------------------------------------------
# Cwd persistence tests
# ---------------------------------------------------------------------------


def test_cwd_for_storage_relative_within_tree(tmp_path: Path) -> None:
    assert _cwd_for_storage(str(tmp_path), str(tmp_path)) == "."
    sub = tmp_path / "subdir"
    sub.mkdir()
    assert _cwd_for_storage(str(sub), str(tmp_path)) == "subdir"
    nested = tmp_path / "subdir" / "nested"
    nested.mkdir()
    assert _cwd_for_storage(str(nested), str(tmp_path)) == "subdir/nested"


def test_cwd_for_storage_outside_tree_returns_absolute(tmp_path: Path) -> None:
    outside = tmp_path.parent / "other-dir"
    outside.mkdir(exist_ok=True)
    try:
        result = _cwd_for_storage(str(outside), str(tmp_path))
        assert os.path.isabs(result)
        assert result == str(outside.resolve())
    finally:
        outside.rmdir()


def test_resolve_stored_cwd_fallbacks(tmp_path: Path) -> None:
    configured = str(tmp_path.resolve())
    # Empty/None/dot → configured working directory
    assert _resolve_stored_cwd("", configured) == configured
    assert _resolve_stored_cwd(None, configured) == configured  # type: ignore[arg-type]
    assert _resolve_stored_cwd(".", configured) == configured
    # Relative → resolved against configured
    sub = tmp_path / "subdir"
    sub.mkdir()
    assert _resolve_stored_cwd("subdir", configured) == str(sub.resolve())
    # Absolute existing → used as-is
    assert _resolve_stored_cwd(str(sub.resolve()), configured) == str(sub.resolve())
    # Nonexistent path → fall back to configured
    assert _resolve_stored_cwd("nonexistent", configured) == configured
    assert _resolve_stored_cwd(str(tmp_path / "no-such-dir"), configured) == configured


def test_resolve_stored_cwd_simulated_sandbox_move(tmp_path: Path) -> None:
    """A stored relative path resolves against a different configured working
    directory, simulating a session moved to a sandbox where the project root
    changed."""
    sub = tmp_path / "subdir"
    sub.mkdir()
    stored = _cwd_for_storage(str(sub), str(tmp_path))
    assert stored == "subdir"
    # Simulate a sandbox move: project root is now under a different path
    sandbox = tmp_path.parent / "sandbox-project"
    sandbox.mkdir(exist_ok=True)
    try:
        sandbox_sub = sandbox / "subdir"
        sandbox_sub.mkdir(exist_ok=True)
        resolved = _resolve_stored_cwd(stored, str(sandbox.resolve()))
        assert resolved == str(sandbox_sub.resolve())
    finally:
        import shutil

        shutil.rmtree(sandbox, ignore_errors=True)


def test_last_bash_end_cwd_from_context_finds_most_recent() -> None:
    context = {
        "session": {
            "messages": [
                {
                    "role": "tool",
                    "content": "old output",
                    "metadata": {
                        "tool_name": "Bash",
                        "tool_plugin": "claude_bash_tool",
                        "bash": {"end_cwd": "old-subdir"},
                    },
                },
                {
                    "role": "tool",
                    "content": "new output",
                    "metadata": {
                        "tool_name": "Bash",
                        "tool_plugin": "claude_bash_tool",
                        "bash": {"end_cwd": "new-subdir"},
                    },
                },
            ]
        }
    }
    assert _last_bash_end_cwd_from_context(context) == "new-subdir"


def test_last_bash_end_cwd_from_context_ignores_other_tools() -> None:
    context = {
        "session": {
            "messages": [
                {
                    "role": "tool",
                    "content": "read output",
                    "metadata": {
                        "tool_name": "Read",
                        "tool_plugin": "claude_read_tool",
                    },
                },
                {
                    "role": "tool",
                    "content": "bash output",
                    "metadata": {
                        "tool_name": "Bash",
                        "tool_plugin": "claude_bash_tool",
                        "bash": {"end_cwd": "subdir"},
                    },
                },
            ]
        }
    }
    assert _last_bash_end_cwd_from_context(context) == "subdir"


def test_last_bash_end_cwd_from_context_returns_none_when_no_bash_results() -> None:
    assert _last_bash_end_cwd_from_context(None) is None
    assert _last_bash_end_cwd_from_context({}) is None
    assert _last_bash_end_cwd_from_context({"session": {}}) is None
    assert _last_bash_end_cwd_from_context({"session": {"messages": []}}) is None
    assert (
        _last_bash_end_cwd_from_context(
            {
                "session": {
                    "messages": [
                        {
                            "role": "tool",
                            "content": "read output",
                            "metadata": {
                                "tool_name": "Read",
                                "tool_plugin": "claude_read_tool",
                            },
                        }
                    ]
                }
            }
        )
        is None
    )


def test_bash_command_stores_end_cwd_in_result_metadata(tmp_path: Path) -> None:
    """A foreground Bash command must return ``metadata.bash.end_cwd`` in its
    result dict so the core can attach it to the tool-result message."""
    tool, state = _wrapper(tmp_path)
    result = tool.execute_tool(
        "Bash",
        {"command": "pwd", "description": "Print working directory"},
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is True
    metadata = result.get("metadata")
    assert isinstance(metadata, dict)
    assert metadata["bash"]["end_cwd"] == "."


def test_bash_command_stores_subdir_in_result_metadata(tmp_path: Path) -> None:
    """After ``cd <subdir> && pwd``, the stored ``end_cwd`` is the relative
    path to the subdir."""
    (tmp_path / "subdir").mkdir()
    tool, state = _wrapper(tmp_path)
    result = tool.execute_tool(
        "Bash",
        {
            "command": f'cd "{tmp_path / "subdir"}" && pwd',
            "description": "Change to subdir and print working directory",
        },
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is True
    assert result["metadata"]["bash"]["end_cwd"] == "subdir"


def test_bash_background_command_does_not_set_cwd_metadata(tmp_path: Path) -> None:
    """Background commands must not update the cwd chain."""
    tool, state = _wrapper(tmp_path)
    result = tool.execute_tool(
        "Bash",
        {
            "command": "sleep 0.1",
            "description": "Brief sleep in background",
            "run_in_background": True,
        },
        state,
        tool_call={"id": "call_bash_1"},
    )
    # Background result should not carry cwd metadata
    assert "metadata" not in result or not result.get("metadata")


def test_bash_cwd_persists_across_two_commands(tmp_path: Path) -> None:
    """Two sequential Bash commands in the same session: the first ``cd``s into
    a subdir, the second ``pwd`` must show the subdir because the cwd persists
    via the tool-result message metadata."""
    (tmp_path / "subdir").mkdir()
    tool, state = _wrapper(tmp_path)

    # First command: cd into subdir and print pwd
    first = tool.execute_tool(
        "Bash",
        {
            "command": f'cd "{tmp_path / "subdir"}" && pwd',
            "description": "Change to subdir and print working directory",
        },
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert first["success"] is True
    assert first["text"].strip() == str(tmp_path / "subdir")
    stored_cwd = first["metadata"]["bash"]["end_cwd"]
    assert stored_cwd == "subdir"

    # Simulate the second command running in the same session: the context
    # carries the session with the first tool-result message.
    context = {
        "session": {
            "messages": [
                {
                    "role": "user",
                    "content": "do the thing",
                },
                {
                    "role": "assistant",
                    "content": "",
                    "metadata": {
                        "tool_calls": [
                            {
                                "id": "call_bash_1",
                                "type": "function",
                                "function": {
                                    "name": "Bash",
                                    "arguments": json.dumps(
                                        {
                                            "command": f'cd "{tmp_path / "subdir"}" && pwd',
                                            "description": "Change to subdir",
                                        }
                                    ),
                                },
                            }
                        ]
                    },
                },
                {
                    "role": "tool",
                    "content": first["text"],
                    "metadata": {
                        "tool_call_id": "call_bash_1",
                        "tool_name": "Bash",
                        "tool_plugin": "claude_bash_tool",
                        "bash": {"end_cwd": stored_cwd},
                    },
                },
            ]
        }
    }

    # Second command: just pwd — should run in the subdir, not the configured wd
    second = tool.execute_tool(
        "Bash",
        {"command": "pwd", "description": "Print working directory"},
        state,
        tool_call={"id": "call_bash_2"},
        context=context,
    )
    assert second["success"] is True
    assert second["text"].strip() == str(tmp_path / "subdir")
    assert second["metadata"]["bash"]["end_cwd"] == "subdir"


def test_bash_cwd_resets_when_no_prior_result(tmp_path: Path) -> None:
    """First Bash command in a session (no prior tool results) runs in the
    configured working directory."""
    tool, state = _wrapper(tmp_path)
    result = tool.execute_tool(
        "Bash",
        {"command": "pwd", "description": "Print working directory"},
        state,
        tool_call={"id": "call_bash_1"},
        context={"session": {"messages": []}},
    )
    assert result["success"] is True
    assert result["text"].strip() == str(tmp_path.resolve())
    assert result["metadata"]["bash"]["end_cwd"] == "."


def test_bash_cwd_falls_back_when_stored_path_does_not_exist(tmp_path: Path) -> None:
    """If the stored ``end_cwd`` points at a nonexistent path (e.g. the subdir
    was deleted, or the session moved to a sandbox where the absolute path is
    wrong), the command falls back to the configured working directory."""
    tool, state = _wrapper(tmp_path)
    context = {
        "session": {
            "messages": [
                {
                    "role": "tool",
                    "content": "old output",
                    "metadata": {
                        "tool_call_id": "call_bash_1",
                        "tool_name": "Bash",
                        "tool_plugin": "claude_bash_tool",
                        "bash": {"end_cwd": "deleted-subdir"},
                    },
                }
            ]
        }
    }
    result = tool.execute_tool(
        "Bash",
        {"command": "pwd", "description": "Print working directory"},
        state,
        tool_call={"id": "call_bash_2"},
        context=context,
    )
    assert result["success"] is True
    # Should fall back to the configured working directory
    assert result["text"].strip() == str(tmp_path.resolve())
    assert result["metadata"]["bash"]["end_cwd"] == "."


def test_upstream_description_segments_present() -> None:
    """The exact-string replacements rely on the upstream segments being present
    verbatim in ``BASH_DESCRIPTION``; drift in the upstream text must be caught
    by this test rather than silently producing an unmodified description."""
    assert _UPSTREAM_OPENING in BASH_DESCRIPTION
    assert _UPSTREAM_CD_GUIDANCE in BASH_DESCRIPTION


def test_init_reads_cwd_config_options_with_defaults() -> None:
    tool = ClaudeBashTool()
    state = tool.init({"working_directory": os.getcwd()})
    assert state["cwd_persistence"] is True
    assert state["include_cwd_in_result"] is False
    assert state["permissive_cd_guidance"] is False


def test_init_reads_cwd_config_options_overrides() -> None:
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": os.getcwd(),
            "bash_cwd_persistence": False,
            "bash_include_cwd_in_result": True,
            "bash_permissive_cd_guidance": True,
        }
    )
    assert state["cwd_persistence"] is False
    assert state["include_cwd_in_result"] is True
    assert state["permissive_cd_guidance"] is True


def test_bash_description_defaults_match_upstream() -> None:
    """With both options at their defaults the description must be byte-identical
    to the upstream Claude Code Bash description (persistence on)."""
    description = _bash_description_for_options(
        cwd_persistence=True,
        permissive_cd_guidance=False,
    )
    assert description == BASH_DESCRIPTION


def test_bash_description_persistence_off_restrictive_guidance() -> None:
    description = _bash_description_for_options(
        cwd_persistence=False,
        permissive_cd_guidance=False,
    )
    assert description != BASH_DESCRIPTION
    assert (
        "The working directory does not persist between commands; each command "
        "starts in the configured working directory."
    ) in description
    # Upstream restrictive sentence stays, with the chaining note appended.
    assert "Try to maintain your current working directory" in description
    assert (
        "When you do use `cd`, chain it with the command in a single Bash call "
        "(`cd dir && cmd`) because the working directory does not persist "
        "between commands."
    ) in description


def test_bash_description_persistence_off_permissive_guidance() -> None:
    description = _bash_description_for_options(
        cwd_persistence=False,
        permissive_cd_guidance=True,
    )
    assert "The working directory does not persist between commands" in description
    assert "You may use `cd` when a command must run from a specific directory" in (
        description
    )
    assert "chain `cd dir && cmd` in a single Bash call" in description
    assert "Try to maintain your current working directory" not in description


def test_bash_description_persistence_on_permissive_guidance() -> None:
    description = _bash_description_for_options(
        cwd_persistence=True,
        permissive_cd_guidance=True,
    )
    assert (
        "The working directory persists between commands, but shell state does " "not."
    ) in description
    assert "You may use `cd` when a command must run from a specific directory" in (
        description
    )
    assert "so `cd` alone is sufficient" in description
    assert "Try to maintain your current working directory" not in description


def test_get_tool_schemas_description_follows_state() -> None:
    tool = ClaudeBashTool()
    state = tool.init({"working_directory": os.getcwd()})
    schemas = tool.get_tool_schemas(state)
    assert len(schemas) == 1
    assert schemas[0]["name"] == "Bash"
    assert schemas[0]["description"] == BASH_DESCRIPTION

    state_off = tool.init(
        {
            "working_directory": os.getcwd(),
            "bash_cwd_persistence": False,
            "bash_permissive_cd_guidance": True,
        }
    )
    schemas_off = tool.get_tool_schemas(state_off)
    assert schemas_off[0]["description"] != BASH_DESCRIPTION
    assert "The working directory does not persist between commands" in (
        schemas_off[0]["description"]
    )


def test_apply_cwd_lines_formats() -> None:
    assert (
        _apply_cwd_lines(
            "output",
            start_cwd="/a",
            end_cwd="/a",
            cwd_persistence=True,
        )
        == "[cwd: /a]\noutput"
    )
    assert (
        _apply_cwd_lines(
            "output",
            start_cwd="/a",
            end_cwd="/b",
            cwd_persistence=True,
        )
        == "[cwd: /a]\noutput\n[cwd: /b]"
    )
    # A changed cwd is not noted when persistence is disabled.
    assert (
        _apply_cwd_lines(
            "output",
            start_cwd="/a",
            end_cwd="/b",
            cwd_persistence=False,
        )
        == "[cwd: /a]\noutput"
    )


def test_bash_cwd_persistence_disabled_ignores_stored_cwd(
    tmp_path: Path,
) -> None:
    """With ``bash_cwd_persistence`` disabled, a stored ``end_cwd`` in the
    session is ignored: the command runs in the configured working directory
    and no ``bash.end_cwd`` metadata is emitted."""
    (tmp_path / "subdir").mkdir()
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
            "bash_cwd_persistence": False,
        }
    )
    context = {
        "session": {
            "messages": [
                {
                    "role": "tool",
                    "content": "old output",
                    "metadata": {
                        "tool_call_id": "call_bash_1",
                        "tool_name": "Bash",
                        "tool_plugin": "claude_bash_tool",
                        "bash": {"end_cwd": "subdir"},
                    },
                }
            ]
        }
    }
    result = tool.execute_tool(
        "Bash",
        {"command": "pwd", "description": "Print working directory"},
        state,
        tool_call={"id": "call_bash_2"},
        context=context,
    )
    assert result["success"] is True
    assert result["text"].strip() == str(tmp_path.resolve())
    assert not result.get("metadata")


def test_bash_include_cwd_in_result_success(tmp_path: Path) -> None:
    """With ``bash_include_cwd_in_result`` enabled, the initial cwd appears as
    the first line of the result; no end line when the cwd did not change."""
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
            "bash_include_cwd_in_result": True,
        }
    )
    result = tool.execute_tool(
        "Bash",
        {"command": "printf hello", "description": "Print hello"},
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is True
    assert result["text"] == f"[cwd: {tmp_path.resolve()}]\nhello"
    # The cwd chain still works with cwd lines enabled.
    assert result["metadata"]["bash"]["end_cwd"] == "."


def test_bash_include_cwd_in_result_changed_cwd_notes_end(tmp_path: Path) -> None:
    """When the command changes the cwd and persistence is on, the end cwd is
    noted as the last line."""
    (tmp_path / "subdir").mkdir()
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
            "bash_include_cwd_in_result": True,
        }
    )
    result = tool.execute_tool(
        "Bash",
        {
            "command": f'cd "{tmp_path / "subdir"}" && pwd',
            "description": "Change to subdir and print working directory",
        },
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is True
    assert result["text"] == (
        f"[cwd: {tmp_path.resolve()}]\n"
        f"{tmp_path.resolve() / 'subdir'}\n"
        f"[cwd: {tmp_path.resolve() / 'subdir'}]"
    )
    assert result["metadata"]["bash"]["end_cwd"] == "subdir"


def test_bash_include_cwd_in_result_changed_cwd_no_end_note_when_persistence_off(
    tmp_path: Path,
) -> None:
    """With persistence disabled, a changed cwd is not noted at the end because
    it does not persist."""
    (tmp_path / "subdir").mkdir()
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
            "bash_include_cwd_in_result": True,
            "bash_cwd_persistence": False,
        }
    )
    result = tool.execute_tool(
        "Bash",
        {
            "command": f'cd "{tmp_path / "subdir"}" && pwd',
            "description": "Change to subdir and print working directory",
        },
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is True
    assert result["text"] == (
        f"[cwd: {tmp_path.resolve()}]\n{tmp_path.resolve() / 'subdir'}"
    )


def test_bash_include_cwd_in_result_failure(tmp_path: Path) -> None:
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
            "bash_include_cwd_in_result": True,
        }
    )
    result = tool.execute_tool(
        "Bash",
        {
            "command": 'sh -c "echo problem 1>&2; exit 7"',
            "description": "Fail with output",
        },
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is False
    assert result["text"] == (f"[cwd: {tmp_path.resolve()}]\nExit code 7\nproblem")


def test_bash_include_cwd_in_result_no_output_placeholder(
    tmp_path: Path,
) -> None:
    tool = ClaudeBashTool()
    state = tool.init(
        {
            "working_directory": str(tmp_path),
            "bash_include_cwd_in_result": True,
        }
    )
    result = tool.execute_tool(
        "Bash",
        {"command": "true", "description": "No-op command"},
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is True
    assert result["text"] == (
        f"[cwd: {tmp_path.resolve()}]\n(Bash completed with no output)"
    )


def test_bash_cwd_lines_disabled_by_default(tmp_path: Path) -> None:
    """Without ``bash_include_cwd_in_result`` the result content is unchanged
    (no cwd lines), matching the upstream result format."""
    tool = ClaudeBashTool()
    state = tool.init({"working_directory": str(tmp_path)})
    result = tool.execute_tool(
        "Bash",
        {"command": "printf hello", "description": "Print hello"},
        state,
        tool_call={"id": "call_bash_1"},
    )
    assert result["success"] is True
    assert result["text"] == "hello"
