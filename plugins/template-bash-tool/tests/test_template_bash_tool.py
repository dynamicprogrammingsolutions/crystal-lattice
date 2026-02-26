from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash executable not available"
)
def test_template_bash_echo_runs(tmp_path: Path) -> None:
    mgr = PluginManager(
        cache_dir=tmp_path / "cache",
        policy={"allow_bash_tools": True},
    )

    res = mgr.resolve_all([{"bash_tool": {"path": str(_plugin_dir())}}])
    assert res.errors == []
    assert len(res.classes) == 1
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "template_bash_echo", "arguments": {"value": "hi"}},
    }
    items = list(core.iter_tool_messages([tool_call], config={}))
    finals = [it for it in items if isinstance(it, dict) and it.get("role") == "tool"]
    assert len(finals) == 1
    assert finals[0].get("content") == "hi"


@pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash executable not available"
)
def test_template_bash_echo_uppercase(tmp_path: Path) -> None:
    mgr = PluginManager(
        cache_dir=tmp_path / "cache",
        policy={"allow_bash_tools": True},
    )

    res = mgr.resolve_all([{"bash_tool": {"path": str(_plugin_dir())}}])
    assert res.errors == []
    tool_cls = res.classes[0]

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "template_bash_echo",
            "arguments": {"value": "hi", "uppercase": True},
        },
    }
    items = list(core.iter_tool_messages([tool_call], config={}))
    finals = [it for it in items if isinstance(it, dict) and it.get("role") == "tool"]
    assert len(finals) == 1
    assert finals[0].get("content") == "HI"
