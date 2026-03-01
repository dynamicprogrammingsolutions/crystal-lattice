from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from agent_app.plugin_manager import PluginManager
from agent_core import AgentCore


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _policy() -> dict:
    return {
        "allow_bash_tools": True,
        "bash_timeout_seconds": 30,
        "bash_error_timeout_seconds": 5,
    }


@pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash executable not available"
)
@pytest.mark.skipif(shutil.which("sed") is None, reason="sed executable not available")
@pytest.mark.skipif(shutil.which("nl") is None, reason="nl executable not available")
def test_read_line_range_default_no_line_numbers(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy=_policy())

    res = mgr.resolve_all([{"bash_tool": {"path": str(_plugin_dir())}}])
    assert res.errors == []
    assert len(res.classes) == 1
    tool_cls = res.classes[0]
    assert getattr(tool_cls, "name", None) == "read_line_range"

    sample = tmp_path / "sample.txt"
    sample.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")

    tool = tool_cls()
    state = tool.init({})
    preview = tool.format_tool_call_preview(
        "read_line_range",
        {"path": str(sample), "start_line": 2, "end_line": 3},
        state,
    )
    assert preview.startswith("read_line_range")
    assert "show_line_numbers=false" in preview

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "read_line_range",
            "arguments": {"path": str(sample), "start_line": 2, "end_line": 3},
        },
    }

    items = list(core.iter_tool_messages([tool_call], config={}))
    partials = [it for it in items if isinstance(it, dict) and "part" in it]
    finals = [it for it in items if isinstance(it, dict) and it.get("role") == "tool"]

    assert partials
    assert len(finals) == 1

    content = finals[0].get("content", "")
    assert content == "two\nthree"
    assert not re.search(r"^\s*2\s+two$", content, re.MULTILINE)


@pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash executable not available"
)
@pytest.mark.skipif(shutil.which("sed") is None, reason="sed executable not available")
@pytest.mark.skipif(shutil.which("nl") is None, reason="nl executable not available")
def test_read_line_range_with_line_numbers(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    mgr = PluginManager(cache_dir=cache_dir, policy=_policy())

    res = mgr.resolve_all([{"bash_tool": {"path": str(_plugin_dir())}}])
    assert res.errors == []
    tool_cls = res.classes[0]

    sample = tmp_path / "sample.txt"
    sample.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")

    core = AgentCore()
    core.register_tool(tool_cls)

    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "read_line_range",
            "arguments": {
                "path": str(sample),
                "start_line": 2,
                "end_line": 3,
                "show_line_numbers": True,
            },
        },
    }

    items = list(core.iter_tool_messages([tool_call], config={}))
    finals = [it for it in items if isinstance(it, dict) and it.get("role") == "tool"]
    assert len(finals) == 1

    content = finals[0].get("content", "")
    assert re.search(r"^\s*2\s+two$", content, re.MULTILINE)
    assert re.search(r"^\s*3\s+three$", content, re.MULTILINE)
