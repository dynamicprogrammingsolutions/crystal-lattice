"""Tests for the unified exec tools (exec_command + write_stdin).

Covers schema parity with the current upstream Codex CLI contract, session
lifecycle (finish path, session path, PTY interaction, polling), yield-time
clamping, truncation, error paths, apply_patch interception, streaming, and
shell_tool_mode selection.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Tuple

import pytest

from codex_tools.unified_exec_tool import (
    ExecCommandTool,
    WriteStdinTool,
    _manager_store_key,
    clamp_exec_yield_time_ms,
    resolve_write_stdin_yield_time_ms,
)
from tool_compat_shared.interactive_process_engine import (
    InteractiveProcessManager,
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _isolated_managers(monkeypatch):
    """Give each test fresh fallback managers so sessions never leak."""

    managers: Dict[Tuple[int, float], InteractiveProcessManager] = {}
    monkeypatch.setattr(
        "codex_tools.unified_exec_tool._module_managers", managers
    )
    yield managers
    for manager in managers.values():
        manager.terminate_all()


def _terminate_all(managers) -> None:
    for manager in managers.values():
        manager.terminate_all()


class _FakeStore:
    """Minimal runtime store matching the MCP precedent interface."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._data.get(key)

    def get_or_create(self, key: str, factory: Any) -> Any:
        if key not in self._data:
            self._data[key] = factory()
        return self._data[key]


class TestExecCommandSchemaParity:
    """Served schema must match current upstream Codex CLI texts exactly."""

    def _schema(self) -> Dict[str, Any]:
        tool = ExecCommandTool()
        state = {"config": {}}
        schemas = tool.get_tool_schemas(state)
        assert len(schemas) == 1
        return schemas[0]["function"]

    def test_description_matches_upstream(self):
        assert self._schema()["description"] == (
            "Runs a command in a PTY, returning output or a session ID for "
            "ongoing interaction."
        )

    def test_parameter_texts_match_upstream(self):
        props = self._schema()["parameters"]["properties"]
        assert props["cmd"] == {
            "type": "string",
            "description": "Shell command to execute.",
        }
        assert props["workdir"] == {
            "type": "string",
            "description": (
                "Working directory for the command. Defaults to the turn cwd."
            ),
        }
        assert props["tty"] == {
            "type": "boolean",
            "description": (
                "True allocates a PTY for the command; false or omitted uses "
                "plain pipes."
            ),
        }
        assert props["yield_time_ms"] == {
            "type": "number",
            "description": (
                "Wait before yielding output. Defaults to 10000 ms; "
                "effective range is 250-30000 ms."
            ),
        }
        assert props["max_output_tokens"] == {
            "type": "number",
            "description": (
                "Output token budget. Defaults to 10000 tokens; larger "
                "requests may be capped by policy."
            ),
        }
        assert props["shell"] == {
            "type": "string",
            "description": (
                "Shell binary to launch. Defaults to the user's default shell."
            ),
        }
        assert props["login"] == {
            "type": "boolean",
            "description": (
                "True runs the shell with -l/-i semantics; false disables "
                "them. Defaults to true."
            ),
        }

    def test_parameter_surface_matches_platform_decision(self):
        """Approval params and environment_id are omitted (documented
        platform divergence); timeout_ms is not in the upstream schema."""

        props = self._schema()["parameters"]["properties"]
        assert set(props) == {
            "cmd",
            "workdir",
            "tty",
            "yield_time_ms",
            "max_output_tokens",
            "shell",
            "login",
        }
        assert self._schema()["parameters"]["required"] == ["cmd"]
        assert self._schema()["parameters"]["additionalProperties"] is False

    def test_served_schema_matches_reference_snapshot_texts(self):
        """Every served parameter text appears verbatim in the refreshed
        reference snapshot (upstream truth)."""

        import json
        from pathlib import Path

        reference = (
            Path(__file__).resolve().parents[1]
            / "reference/codex-cli-tools/exec_command/"
            / "schema.without_request_permissions.json"
        )
        upstream = json.loads(reference.read_text(encoding="utf-8"))
        served_props = self._schema()["parameters"]["properties"]
        upstream_props = upstream["parameters"]["properties"]
        for name, served in served_props.items():
            assert served["description"] == upstream_props[name]["description"], (
                f"param {name} diverges from the reference snapshot"
            )
        assert self._schema()["description"] == upstream["description"]


class TestWriteStdinSchemaParity:
    def _schema(self) -> Dict[str, Any]:
        tool = WriteStdinTool()
        schemas = tool.get_tool_schemas({"config": {}})
        assert len(schemas) == 1
        return schemas[0]["function"]

    def test_description_matches_upstream(self):
        assert self._schema()["description"] == (
            "Writes characters to an existing unified exec session and "
            "returns recent output."
        )

    def test_parameter_texts_match_upstream(self):
        props = self._schema()["parameters"]["properties"]
        assert props["session_id"] == {
            "type": "number",
            "description": "Identifier of the running unified exec session.",
        }
        assert props["chars"] == {
            "type": "string",
            "description": (
                "Bytes to write to stdin. Defaults to empty, which polls "
                "without writing."
            ),
        }
        assert props["yield_time_ms"] == {
            "type": "number",
            "description": (
                "Wait before yielding output. Non-empty writes default to "
                "250 ms and cap at 30000 ms; empty polls wait 5000-300000 ms "
                "by default."
            ),
        }
        assert props["max_output_tokens"] == {
            "type": "number",
            "description": (
                "Output token budget. Defaults to 10000 tokens; larger "
                "requests may be capped by policy."
            ),
        }
        assert set(props) == {
            "session_id",
            "chars",
            "yield_time_ms",
            "max_output_tokens",
        }
        assert self._schema()["parameters"]["required"] == ["session_id"]

    def test_served_schema_matches_reference_snapshot_texts(self):
        import json
        from pathlib import Path

        reference = (
            Path(__file__).resolve().parents[1]
            / "reference/codex-cli-tools/write_stdin/schema.json"
        )
        upstream = json.loads(reference.read_text(encoding="utf-8"))
        served_props = self._schema()["parameters"]["properties"]
        upstream_props = upstream["parameters"]["properties"]
        assert set(served_props) == set(upstream_props)
        for name, served in served_props.items():
            assert served == upstream_props[name], (
                f"param {name} diverges from the reference snapshot"
            )
        assert self._schema()["description"] == upstream["description"]


class TestYieldTimeClamping:
    def test_exec_defaults_and_bounds(self):
        assert clamp_exec_yield_time_ms(None) == 10000
        assert clamp_exec_yield_time_ms(100) == 250
        assert clamp_exec_yield_time_ms(5000) == 5000
        assert clamp_exec_yield_time_ms(100000) == 30000

    def test_write_stdin_non_empty_write_bounds(self):
        assert resolve_write_stdin_yield_time_ms(None, has_input=True) == 250
        assert resolve_write_stdin_yield_time_ms(100, has_input=True) == 250
        assert resolve_write_stdin_yield_time_ms(2000, has_input=True) == 2000
        assert resolve_write_stdin_yield_time_ms(60000, has_input=True) == 30000

    def test_write_stdin_empty_poll_bounds(self):
        assert resolve_write_stdin_yield_time_ms(None, has_input=False) == 5000
        assert resolve_write_stdin_yield_time_ms(250, has_input=False) == 5000
        assert resolve_write_stdin_yield_time_ms(10000, has_input=False) == 10000
        assert (
            resolve_write_stdin_yield_time_ms(500000, has_input=False) == 300000
        )


class TestExecCommandLifecycle:
    def test_finished_command_returns_exit_code_and_output(self):
        tool = ExecCommandTool()
        state = {"config": {}}
        result = _run(
            tool.execute_tool(
                "exec_command", {"cmd": "echo lifecycle-finish"}, state
            )
        )
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["session_id"] is None
        assert "lifecycle-finish" in result["output"]
        assert "Process exited with code 0" in result["output"]
        assert result["output"].startswith("Wall time: ")
        assert "Output:" in result["output"]

    def test_nonzero_exit_code_marks_failure(self):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command", {"cmd": "echo err >&2; exit 7"}, {"config": {}}
            )
        )
        assert result["success"] is False
        assert result["exit_code"] == 7
        assert "Process exited with code 7" in result["output"]

    def test_long_command_returns_session_id(self, _isolated_managers):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "sleep 30", "yield_time_ms": 300},
                {"config": {}},
            )
        )
        assert result["success"] is True
        assert result["exit_code"] is None
        assert isinstance(result["session_id"], int)
        assert (
            f"Process running with session ID {result['session_id']}"
            in result["output"]
        )
        # cleanup
        _terminate_all(_isolated_managers)

    def test_finished_session_removed_from_registry(self, _isolated_managers):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command", {"cmd": "echo gone"}, {"config": {}}
            )
        )
        assert result["session_id"] is None
        assert all(
            manager.session_count() == 0
            for manager in _isolated_managers.values()
        )

    def test_workdir_is_resolved(self, tmp_path):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "pwd", "workdir": str(tmp_path)},
                {"config": {}},
            )
        )
        assert str(tmp_path) in result["output"]

    def test_invalid_cmd_rejected(self):
        tool = ExecCommandTool()
        for bad in ("", "   ", None, 5):
            result = _run(
                tool.execute_tool("exec_command", {"cmd": bad}, {"config": {}})
            )
            assert result["success"] is False
            assert "cmd must be a non-empty string" in result["error"]

    def test_unknown_tool_name_rejected(self):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool("other_tool", {"cmd": "x"}, {"config": {}})
        )
        assert result["success"] is False

    def test_truncation_applies_warning_header(self):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "seq 1 60000", "max_output_tokens": 100},
                {"config": {}},
            )
        )
        assert result["truncated"] is True
        assert "Warning: truncated output (original token count:" in result["output"]
        assert "Total output lines:" in result["output"]
        assert "tokens truncated" in result["output"]
        assert isinstance(result["original_token_count"], int)
        assert result["original_token_count"] > 100

    def test_spawn_error_reported(self):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "echo x", "shell": "/nonexistent/shell-binary"},
                {"config": {}},
            )
        )
        assert result["success"] is False
        assert "failed to spawn command" in result["output"]

    def test_session_limit_error(self, _isolated_managers):
        tool = ExecCommandTool()
        state = {"config": {"unified_exec_max_sessions": 1}}
        first = _run(
            tool.execute_tool(
                "exec_command", {"cmd": "sleep 30", "yield_time_ms": 300}, state
            )
        )
        assert first["session_id"] is not None
        second = _run(
            tool.execute_tool(
                "exec_command", {"cmd": "echo x", "yield_time_ms": 300}, state
            )
        )
        assert second["success"] is False
        assert "session limit reached" in second["error"]
        _terminate_all(_isolated_managers)


class TestWriteStdinLifecycle:
    def _start_session(
        self, cmd: str, tty: bool = False, yield_ms: int = 300
    ) -> "Dict[str, Any]":
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": cmd, "tty": tty, "yield_time_ms": yield_ms},
                {"config": {}},
            )
        )
        assert result["session_id"] is not None, (
            f"command finished before yielding a session: {result}"
        )
        return result

    def test_poll_collects_new_output_and_exit(self, _isolated_managers):
        # The echo output arrives during the exec window, so it belongs to
        # the exec_command response; the poll observes the exit and any
        # output produced after the exec call's last drain.
        started = self._start_session("echo poll-me; sleep 0.6")
        assert "poll-me" in started["output"]

        tool = WriteStdinTool()
        result = _run(
            tool.execute_tool(
                "write_stdin",
                {"session_id": started["session_id"], "yield_time_ms": 5000},
                {"config": {}},
            )
        )
        assert result["exit_code"] == 0
        assert result["session_id"] is None
        assert "Process exited with code 0" in result["output"]

    def test_poll_after_finish_reports_unknown_session(self, _isolated_managers):
        started = self._start_session("sleep 0.6; echo quick")
        session_id = started["session_id"]
        tool = WriteStdinTool()
        first = _run(
            tool.execute_tool(
                "write_stdin",
                {"session_id": session_id, "yield_time_ms": 5000},
                {"config": {}},
            )
        )
        assert first["exit_code"] == 0
        assert "quick" in first["output"]
        second = _run(
            tool.execute_tool(
                "write_stdin",
                {"session_id": session_id, "yield_time_ms": 250},
                {"config": {}},
            )
        )
        assert second["success"] is False
        assert f"Unknown process id {session_id}" in second["error"]

    def test_unknown_session_id(self):
        tool = WriteStdinTool()
        result = _run(
            tool.execute_tool(
                "write_stdin", {"session_id": 424242}, {"config": {}}
            )
        )
        assert result["success"] is False
        assert "Unknown process id 424242" in result["error"]

    def test_invalid_session_id_rejected(self):
        tool = WriteStdinTool()
        for bad in ("abc", None, True, [1]):
            result = _run(
                tool.execute_tool(
                    "write_stdin", {"session_id": bad}, {"config": {}}
                )
            )
            assert result["success"] is False
            assert "session_id must be a number" in result["error"]

    def test_write_to_pipe_session_rejected_with_upstream_message(
        self, _isolated_managers
    ):
        started = self._start_session("sleep 30")
        tool = WriteStdinTool()
        result = _run(
            tool.execute_tool(
                "write_stdin",
                {"session_id": started["session_id"], "chars": "hello"},
                {"config": {}},
            )
        )
        assert result["success"] is False
        assert result["error"] == (
            "stdin is closed for this session; rerun exec_command with "
            "tty=true to keep stdin open"
        )
        _terminate_all(_isolated_managers)

    def test_interrupt_pipe_session(self):
        started = self._start_session("sleep 30")
        tool = WriteStdinTool()
        result = _run(
            tool.execute_tool(
                "write_stdin",
                {"session_id": started["session_id"], "chars": "\x03"},
                {"config": {}},
            )
        )
        assert result["exit_code"] is not None
        assert result["exit_code"] != 0

    def test_tty_session_write_and_interact(self, _isolated_managers):
        started = self._start_session("cat", tty=True)
        tool = WriteStdinTool()
        result = _run(
            tool.execute_tool(
                "write_stdin",
                {
                    "session_id": started["session_id"],
                    "chars": "interact-line\n",
                    "yield_time_ms": 1000,
                },
                {"config": {}},
            )
        )
        assert result["success"] is True
        assert result["session_id"] is not None
        assert "interact-line" in result["output"]
        _terminate_all(_isolated_managers)

    def test_empty_poll_writes_nothing(self):
        started = self._start_session("sleep 2; echo after-poll", tty=False)
        tool = WriteStdinTool()
        result = _run(
            tool.execute_tool(
                "write_stdin",
                {"session_id": started["session_id"], "yield_time_ms": 6000},
                {"config": {}},
            )
        )
        assert result["exit_code"] == 0
        assert "after-poll" in result["output"]


class TestCrossRequestSessions:
    def test_session_survives_via_runtime_store(self):
        store = _FakeStore()
        context = {"runtime_store": store}
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "sleep 2; echo cross-request", "yield_time_ms": 300},
                {"config": {}},
                context=context,
            )
        )
        session_id = result["session_id"]
        assert session_id is not None

        # A brand-new tool instance and state (i.e. a new request) can still
        # reach the session through the same runtime store.
        fresh_tool = WriteStdinTool()
        fresh_state = {"config": {}}
        polled = _run(
            fresh_tool.execute_tool(
                "write_stdin",
                {"session_id": session_id, "yield_time_ms": 6000},
                fresh_state,
                context=context,
            )
        )
        assert polled["exit_code"] == 0
        assert "cross-request" in polled["output"]

    def test_manager_config_from_config_keys(self):
        store = _FakeStore()
        context = {"runtime_store": store}
        tool = ExecCommandTool()
        state = {
            "config": {
                "unified_exec_max_sessions": 3,
                "unified_exec_session_ttl_seconds": 60,
            }
        }
        _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "true"},
                state,
                context=context,
            )
        )
        manager = store.get(_manager_store_key(state["config"]))
        assert isinstance(manager, InteractiveProcessManager)
        assert manager.max_sessions == 3
        assert manager.session_ttl_seconds == 60.0


class TestStreaming:
    def test_exec_command_stream_emits_parts_and_result(self):
        tool = ExecCommandTool()
        chunks: List[Dict[str, Any]] = list(
            tool.stream_tool(
                "exec_command", {"cmd": "echo stream-me"}, {"config": {}}
            )
        )
        parts = [c for c in chunks if "part" in c]
        finals = [c for c in chunks if "success" in c]
        assert len(finals) == 1
        assert finals[0]["exit_code"] == 0
        assert "stream-me" in finals[0]["output"]
        joined = "".join(p["part"]["content"] for p in parts)
        assert "stream-me" in joined

    def test_exec_command_stream_running_session(self, _isolated_managers):
        tool = ExecCommandTool()
        chunks = list(
            tool.stream_tool(
                "exec_command",
                {"cmd": "sleep 30", "yield_time_ms": 300},
                {"config": {}},
            )
        )
        finals = [c for c in chunks if "success" in c]
        assert len(finals) == 1
        assert finals[0]["session_id"] is not None
        _terminate_all(_isolated_managers)

    def test_write_stdin_stream(self):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "echo tail-output; sleep 0.4", "yield_time_ms": 300},
                {"config": {}},
            )
        )
        assert result["session_id"] is not None
        ws = WriteStdinTool()
        chunks = list(
            ws.stream_tool(
                "write_stdin",
                {"session_id": result["session_id"], "yield_time_ms": 5000},
                {"config": {}},
            )
        )
        finals = [c for c in chunks if "success" in c]
        assert len(finals) == 1
        assert finals[0]["exit_code"] == 0


class TestApplyPatchInterception:
    def test_intercepted_patch_routed_to_patch_runtime(self, tmp_path):
        tool = ExecCommandTool()
        target = tmp_path / "intercept.txt"
        target.write_text("old\n", encoding="utf-8")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {target.name}\n"
            "@@\n"
            "-old\n"
            "+new\n"
            "*** End Patch\n"
        )
        state = {
            "config": {
                "intercept_apply_patch": True,
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
            }
        }
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": f"apply_patch <<'EOF'\n{patch}EOF"},
                state,
            )
        )
        assert result.get("intercepted_tool") == "apply_patch"
        assert result["success"] is True
        assert target.read_text(encoding="utf-8") == "new\n"

    def test_interception_disabled_runs_shell(self, tmp_path):
        tool = ExecCommandTool()
        state = {"config": {"working_directory": str(tmp_path)}}
        result = _run(
            tool.execute_tool("exec_command", {"cmd": "echo plain"}, state)
        )
        assert result.get("intercepted_tool") is None
        assert result["exit_code"] == 0


class TestSelection:
    """Mode matrix for the unified exec tools (direct is_enabled checks)."""

    def test_explicit_exec_command_mode_enabled(self):
        tool = ExecCommandTool()
        assert (
            tool.is_enabled({"shell_tool_mode": "exec_command"}, [], [], {})
            is True
        )
        ws = WriteStdinTool()
        assert (
            ws.is_enabled({"shell_tool_mode": "exec_command"}, [], [], {})
            is True
        )

    def test_auto_mode_enabled_with_codex_variant_tag(self):
        tool = ExecCommandTool()
        assert (
            tool.is_enabled(
                {"shell_tool_mode": "auto"}, ["codex-variant"], [], {}
            )
            is True
        )
        assert tool.is_enabled({}, ["codex-variant"], [], {}) is True

    def test_auto_mode_enabled_without_tag(self):
        """Unified exec is the model-agnostic default: ``auto`` enables it
        regardless of tags (no model-based selection)."""
        tool = ExecCommandTool()
        assert tool.is_enabled({"shell_tool_mode": "auto"}, [], [], {}) is True
        assert tool.is_enabled({}, [], [], {}) is True

    def test_shell_and_shell_command_modes_disable_unified_exec(self):
        tool = ExecCommandTool()
        for mode in ("shell", "shell_command"):
            assert (
                tool.is_enabled(
                    {"shell_tool_mode": mode}, ["codex-variant"], [], {}
                )
                is False
            )

    def test_tags_advertised(self):
        assert ExecCommandTool().get_tags({}, []) == ["shell:exec"]
        assert WriteStdinTool().get_tags({}, []) == ["shell:exec"]

    def test_shell_command_tool_is_explicit_mode_only(self):
        from codex_tools.shell_command_tool import ShellCommandTool

        tool = ShellCommandTool()
        # auto mode (with or without the codex-variant tag) never enables it
        assert (
            tool.is_enabled(
                {"shell_tool_mode": "auto"}, ["codex-variant"], [], {}
            )
            is False
        )
        assert tool.is_enabled({}, ["codex-variant"], [], {}) is False
        assert tool.is_enabled({}, [], [], {}) is False
        # explicit mode still forces it on
        assert (
            tool.is_enabled({"shell_tool_mode": "shell_command"}, [], [], {})
            is True
        )

    def test_shell_array_tool_is_explicit_mode_only(self):
        from codex_tools.shell_tool import ShellArrayTool

        tool = ShellArrayTool()
        assert tool.is_enabled({"shell_tool_mode": "shell"}, [], [], {}) is True
        # auto never enables the array tool any more, tagged or not
        assert tool.is_enabled({}, [], [], {}) is False
        assert tool.is_enabled({}, ["codex-variant"], [], {}) is False
        assert (
            tool.is_enabled({"shell_tool_mode": "shell_command"}, [], [], {})
            is False
        )
        assert (
            tool.is_enabled({"shell_tool_mode": "exec_command"}, [], [], {})
            is False
        )


class TestResultFormatting:
    def test_output_layout_matches_upstream(self):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command", {"cmd": "echo layout"}, {"config": {}}
            )
        )
        lines = result["output"].splitlines()
        assert lines[0].startswith("Wall time: ")
        assert lines[0].endswith(" seconds")
        assert lines[1] == "Process exited with code 0"
        assert lines[2] == "Output:"
        assert "layout" in result["output"]
        assert isinstance(result["wall_time_seconds"], float)

    def test_running_layout_reports_session(self, _isolated_managers):
        tool = ExecCommandTool()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "sleep 30", "yield_time_ms": 250},
                {"config": {}},
            )
        )
        lines = result["output"].splitlines()
        assert lines[1] == f"Process running with session ID {result['session_id']}"
        _terminate_all(_isolated_managers)

    def test_wall_time_reasonable(self):
        tool = ExecCommandTool()
        start = time.monotonic()
        result = _run(
            tool.execute_tool(
                "exec_command",
                {"cmd": "sleep 0.5", "yield_time_ms": 5000},
                {"config": {}},
            )
        )
        elapsed = time.monotonic() - start
        assert 0.4 <= result["wall_time_seconds"] <= elapsed + 0.5


class TestPublicCoreExecution:
    """Drives the unified exec tools through the public AgentCore tool-call
    execution path (the same boundary the hosted-API tests use after the
    model responds), with a shell-command-family model under auto mode."""

    def test_exec_command_then_write_stdin_via_execute_tool_calls(
        self, _isolated_managers
    ):
        import json as _json

        from agent_core import AgentCore
        from codex_tools.codex_variant_feature import CodexVariantFeature

        class _MinimalProvider:
            name = "minimal_provider"
            version = "1.0.0"

            def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
                return {"config": config}

            def get_tags(
                self, config: Dict[str, Any], models: List[Dict[str, Any]]
            ) -> List[str]:
                return []

        core = AgentCore()
        core.register_provider(_MinimalProvider)
        core.register_feature(CodexVariantFeature)
        core.register_tool(ExecCommandTool)
        core.register_tool(WriteStdinTool)

        config = {
            "model": "gpt-6.1-sol",  # shell-command family
            "shell_tool_mode": "auto",
        }

        # Real config -> plugin wiring path selects the unified exec tools.
        _, _, _, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]
        assert "codex-variant" in tags
        assert "exec_command" in tool_names
        assert "write_stdin" in tool_names
        assert "shell" not in tool_names
        assert "shell_command" not in tool_names

        def _tool_messages(tool_calls):
            messages = list(core.execute_tool_calls(tool_calls, config))
            return [m for m in messages if m.get("role") == "tool"]

        # Simulated model tool call in the format the core produces.
        exec_call = [
            {
                "id": "call_exec_1",
                "type": "function",
                "function": {
                    "name": "exec_command",
                    "arguments": _json.dumps(
                        {
                            "cmd": "sleep 1; echo core-e2e-output",
                            "yield_time_ms": 300,
                        }
                    ),
                },
            }
        ]
        tool_messages = _tool_messages(exec_call)
        assert tool_messages, "expected a tool message from exec_command"
        content = tool_messages[0]["content"]
        assert "Process running with session ID" in content
        session_id = int(
            content.split("Process running with session ID", 1)[1].split()[0]
        )

        poll_call = [
            {
                "id": "call_poll_1",
                "type": "function",
                "function": {
                    "name": "write_stdin",
                    "arguments": _json.dumps(
                        {"session_id": session_id, "yield_time_ms": 5000}
                    ),
                },
            }
        ]
        poll_messages = _tool_messages(poll_call)
        assert poll_messages, "expected a tool message from write_stdin"
        poll_content = poll_messages[0]["content"]
        assert "Process exited with code 0" in poll_content
        assert "core-e2e-output" in poll_content

