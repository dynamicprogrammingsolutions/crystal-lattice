from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys
import threading
import time

import pytest

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore


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


def _pid_is_live(pid: int) -> bool:
    completed = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    status = completed.stdout.strip()
    return bool(status) and not status.startswith("Z")


def _core_python_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _bash_tool_policy(base_dir: Path) -> dict:
    return {
        "base_dir": str(base_dir),
        "allow_bash_tools": True,
        "bash_timeout_seconds": 30,
        "bash_error_timeout_seconds": 5,
    }


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_plugin_manager_resolves_bash_tool_file(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    base_dir = _core_python_dir()
    mgr = PluginManager(cache_dir=cache_dir, policy=_bash_tool_policy(base_dir))

    res = mgr.resolve_all(
        [
            {"bash_tool": {"file": "tests/fixtures/bash_tools/read_line_range.bash"}},
        ]
    )
    assert res.errors == []
    assert len(res.classes) == 1
    assert getattr(res.classes[0], "name", None) == "read_line_range"

    core = AgentCore()
    core.register_tool(res.classes[0])
    schemas = core.get_tool_schemas({})
    assert any((s.get("function") or {}).get("name") == "read_line_range" for s in schemas)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_plugin_manager_resolves_bash_shorthand_path(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    base_dir = _core_python_dir()
    mgr = PluginManager(cache_dir=cache_dir, policy=_bash_tool_policy(base_dir))

    res = mgr.resolve_all(
        [
            "bash:tests/fixtures/bash_tools/read_line_range.bash",
        ]
    )
    assert res.errors == []
    assert len(res.classes) == 1
    assert getattr(res.classes[0], "name", None) == "read_line_range"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_bash_tool_host_exposes_agent_tool_python(tmp_path: Path) -> None:
    tool_file = tmp_path / "python_env_tool.bash"
    tool_file.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

sub="${1-}"
shift || true

case "$sub" in
  schema)
    cat <<'JSON'
{"id":"python_env_tool","version":"0.1.0","args_mode":"flags","tools":[{"type":"function","function":{"name":"python_env_tool","description":"Reports AGENT_TOOL_PYTHON","parameters":{"type":"object","properties":{},"required":[]}}}]}
JSON
    ;;
  run)
    printf '%s' "${AGENT_TOOL_PYTHON:-}"
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    policy = _bash_tool_policy(_core_python_dir())
    policy["base_dir"] = str(tmp_path)
    mgr = PluginManager(cache_dir=cache_dir, policy=policy)

    res = mgr.resolve_all(
        [
            {"bash_tool": {"file": str(tool_file.name)}},
        ]
    )
    assert res.errors == []
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    items = list(
        core.iter_tool_messages(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "python_env_tool", "arguments": {}},
                }
            ],
            config={},
        )
    )
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 1
    assert finals[0].get("content", "") == sys.executable


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_bash_tool_host_exposes_selected_config_keys(tmp_path: Path) -> None:
    tool_file = tmp_path / "config_env_tool.bash"
    tool_file.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

sub="${1-}"
shift || true

case "$sub" in
  schema)
    cat <<'JSON'
{"id":"config_env_tool","version":"0.1.0","args_mode":"flags","config_keys":["sample_config_value"],"tools":[{"type":"function","function":{"name":"config_env_tool","description":"Reports selected config env","parameters":{"type":"object","properties":{},"required":[]}}}]}
JSON
    ;;
  run)
    printf '%s' "${AGENT_TOOL_CONFIG_SAMPLE_CONFIG_VALUE:-}"
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    policy = _bash_tool_policy(_core_python_dir())
    policy["base_dir"] = str(tmp_path)
    mgr = PluginManager(cache_dir=cache_dir, policy=policy)

    res = mgr.resolve_all(
        [
            {"bash_tool": {"file": str(tool_file.name)}},
        ]
    )
    assert res.errors == []
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    items = list(
        core.iter_tool_messages(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "config_env_tool", "arguments": {}},
                }
            ],
            config={"sample_config_value": "hello-config"},
        )
    )
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 1
    assert finals[0].get("content", "") == "hello-config"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_bash_tool_preview_and_streaming_execution(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    base_dir = _core_python_dir()
    mgr = PluginManager(cache_dir=cache_dir, policy=_bash_tool_policy(base_dir))

    res = mgr.resolve_all(
        [
            {"bash_tool": {"file": "tests/fixtures/bash_tools/read_line_range.bash"}},
        ]
    )
    assert res.errors == []
    tool_cls = res.classes[0]

    test_file = tmp_path / "sample.txt"
    test_file.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")

    tool = tool_cls()
    state = tool.init({})
    preview = tool.format_tool_call_preview(
        "read_line_range",
        {
            "path": str(test_file),
            "start_line": 2,
            "end_line": 3,
            "show_line_numbers": False,
        },
        state,
    )
    assert preview.startswith("read_line_range")

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "read_line_range",
                "arguments": {
                    "path": str(test_file),
                    "start_line": 2,
                    "end_line": 3,
                    "show_line_numbers": False,
                },
            },
        }
    ]

    items = list(core.iter_tool_messages(tool_calls, config={}))
    partials = [it for it in items if isinstance(it, dict) and "part" in it]
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]

    assert partials, "expected streamed tool partials"
    assert len(finals) == 1
    assert "two" in finals[0].get("content", "")
    assert "three" in finals[0].get("content", "")


@pytest.mark.skipif(sys.platform == "win32", reason="uses POSIX process groups")
def test_bash_tool_hard_cancel_terminates_process_tree(tmp_path: Path) -> None:
    pid_file = tmp_path / "child.pid"
    tool_file = tmp_path / "cancellable_tool.bash"
    tool_file.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
case "${{1-}}" in
  schema)
    cat <<'JSON'
{{"id":"cancellable_tool","version":"0.1.0","args_mode":"flags","tools":[{{"type":"function","function":{{"name":"cancellable_tool","description":"Blocks","parameters":{{"type":"object","properties":{{}},"required":[]}}}}}}]}}
JSON
    ;;
  run)
    sleep 60 &
    child=$!
    printf '%s' "$child" > {str(pid_file)!r}
    wait "$child"
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )
    policy = _bash_tool_policy(tmp_path)
    manager = PluginManager(cache_dir=tmp_path / "cache", policy=policy)
    resolved = manager.resolve_all(
        [{"bash_tool": {"file": str(tool_file.name)}}]
    )
    assert resolved.errors == []
    core = AgentCore()
    core.register_tool(resolved.classes[0])
    cancellation = _TestCancellation()
    items: list[dict] = []
    call = {
        "id": "call_cancel",
        "type": "function",
        "function": {"name": "cancellable_tool", "arguments": {}},
    }
    worker = threading.Thread(
        target=lambda: items.extend(
            core.iter_tool_messages(
                [call],
                config={},
                cancellation=cancellation,
            )
        )
    )
    worker.start()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not pid_file.exists():
        time.sleep(0.02)
    assert pid_file.exists()

    cancellation.cancel()
    worker.join(timeout=5)

    assert not worker.is_alive()
    child_pid = int(pid_file.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and _pid_is_live(child_pid):
        time.sleep(0.05)
    assert not _pid_is_live(child_pid)
    finals = [item for item in items if "part" not in item]
    assert finals
    assert "cancel" in str(finals[-1].get("content", "")).lower()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_bash_tool_error_subcommand_formats_tool_message(tmp_path: Path) -> None:
    tool_file = tmp_path / "fail_tool.bash"
    tool_file.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

sub="${1-}"
shift || true

case "$sub" in
  schema)
    cat <<'JSON'
{
  "id": "fail_tool",
  "version": "0.1.0",
  "args_mode": "flags",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "fail_tool",
        "description": "Always fails.",
        "parameters": {
          "type": "object",
          "properties": {"value": {"type": "string"}},
          "required": ["value"]
        }
      }
    }
  ]
}
JSON
    ;;
  run)
    echo "oops" >&2
    exit 2
    ;;
  error)
    code="${1-}"
    shift || true
    echo "CUSTOM ERROR exit_code=$code"
    exit 0
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    policy = _bash_tool_policy(_core_python_dir())
    policy["base_dir"] = str(tmp_path)
    mgr = PluginManager(cache_dir=cache_dir, policy=policy)

    res = mgr.resolve_all(
        [
            {"bash_tool": {"file": str(tool_file.name)}},
        ]
    )
    assert res.errors == []
    assert len(res.classes) == 1
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    items = list(
        core.iter_tool_messages(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "fail_tool", "arguments": {"value": "x"}},
                }
            ],
            config={},
        )
    )
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 1
    assert "CUSTOM ERROR" in finals[0].get("content", "")


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_bash_tool_error_falls_back_when_unhandled(tmp_path: Path) -> None:
    tool_file = tmp_path / "no_error_tool.bash"
    tool_file.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

sub="${1-}"
shift || true

case "$sub" in
  schema)
    cat <<'JSON'
{"id":"no_error_tool","version":"0.1.0","args_mode":"flags","tools":[{"type":"function","function":{"name":"no_error_tool","description":"Fails","parameters":{"type":"object","properties":{},"required":[]}}}]}
JSON
    ;;
  run)
    echo "boom" >&2
    exit 3
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    policy = _bash_tool_policy(_core_python_dir())
    policy["base_dir"] = str(tmp_path)
    mgr = PluginManager(cache_dir=cache_dir, policy=policy)

    res = mgr.resolve_all(
        [
            {"bash_tool": {"file": str(tool_file.name)}},
        ]
    )
    assert res.errors == []
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    items = list(
        core.iter_tool_messages(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "no_error_tool", "arguments": {}},
                }
            ],
            config={},
        )
    )
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 1
    content = finals[0].get("content", "")
    assert "exited with code 3" in content
    assert "STDERR" in content


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
def test_bash_tool_directory_manifest_resolves(tmp_path: Path) -> None:
    repo = tmp_path / "bash_repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "tools" / "echo.bash").write_text(
        """#!/usr/bin/env bash
set -euo pipefail

sub="${1-}"
shift || true

case "$sub" in
  schema)
    cat <<'JSON'
{"id":"bash_echo","version":"0.1.0","args_mode":"flags","tools":[{"type":"function","function":{"name":"bash_echo","description":"Echo","parameters":{"type":"object","properties":{"value":{"type":"string"}},"required":["value"]}}}]}
JSON
    ;;
  preview)
    echo "bash_echo"
    ;;
  run)
    echo "${2-}"
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )
    (repo / "agent_plugin.json").write_text(
        json.dumps({"bash_tools": [{"file": "tools/echo.bash"}]}),
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy=_bash_tool_policy(_core_python_dir()))

    res = mgr.resolve_all(
        [
            {"bash_tool": {"path": str(repo)}},
        ]
    )
    assert res.errors == []
    assert len(res.classes) == 1
    assert getattr(res.classes[0], "name", None) == "bash_echo"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash executable not available")
@pytest.mark.skipif(shutil.which("jq") is None, reason="jq executable not available")
def test_bash_tool_json_args_mode_executes(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    base_dir = _core_python_dir()
    mgr = PluginManager(cache_dir=cache_dir, policy=_bash_tool_policy(base_dir))

    res = mgr.resolve_all(
        [
            {"bash_tool": {"file": "tests/fixtures/bash_tools/json_example.bash"}},
        ]
    )
    assert res.errors == []
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "json_example",
                "arguments": {"items": ["a", "b"], "uppercase": True},
            },
        }
    ]

    items = list(core.iter_tool_messages(tool_calls, config={}))
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]
    assert len(finals) == 1
    assert "A" in finals[0].get("content", "")
